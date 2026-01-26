#!/usr/bin/env python3
"""
ONTO Enterprise Evaluation API
MVP for paid evaluation service

Endpoints:
  POST /enterprise/evaluate  - Submit model for evaluation
  GET  /enterprise/status    - Check evaluation status
  GET  /enterprise/report    - Get evaluation report
  POST /enterprise/pilot     - Request free pilot

Run: uvicorn enterprise.api:app --host 0.0.0.0 --port 8080
"""

import json
import hashlib
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from enum import Enum
import secrets

from fastapi import FastAPI, HTTPException, Header, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr

# ============================================================
# CONFIG
# ============================================================

DATA_DIR = Path("enterprise_data")
EVALUATIONS_DIR = DATA_DIR / "evaluations"
REPORTS_DIR = DATA_DIR / "reports"
CUSTOMERS_DIR = DATA_DIR / "customers"

for d in [DATA_DIR, EVALUATIONS_DIR, REPORTS_DIR, CUSTOMERS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Pricing tiers
PRICING = {
    "pilot": {"evaluations": 1, "price": 0, "duration_days": 14},
    "starter": {"evaluations": 10, "price": 2000, "duration_days": 30},
    "pro": {"evaluations": 100, "price": 10000, "duration_days": 30},
    "enterprise": {"evaluations": -1, "price": 50000, "duration_days": 365},  # -1 = unlimited
}

# ============================================================
# MODELS
# ============================================================

class EvaluationStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Prediction(BaseModel):
    id: str
    label: str  # KNOWN, UNKNOWN, CONTRADICTION
    confidence: float

class EvaluationRequest(BaseModel):
    model_name: str
    model_version: Optional[str] = None
    organization: str
    predictions: List[Prediction]
    contact_email: EmailStr
    notes: Optional[str] = None

class PilotRequest(BaseModel):
    company_name: str
    contact_name: str
    contact_email: EmailStr
    model_description: str
    use_case: str

class EvaluationResult(BaseModel):
    evaluation_id: str
    status: EvaluationStatus
    model_name: str
    organization: str
    submitted_at: str
    completed_at: Optional[str] = None
    metrics: Optional[Dict] = None
    risk_score: Optional[str] = None
    report_url: Optional[str] = None

# ============================================================
# AUTH
# ============================================================

def verify_api_key(x_api_key: str = Header(...)) -> Dict:
    """Verify API key and return customer info"""
    customers_file = CUSTOMERS_DIR / "keys.json"
    
    if not customers_file.exists():
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    with open(customers_file) as f:
        keys = json.load(f)
    
    if x_api_key not in keys:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    customer = keys[x_api_key]
    
    # Check if active
    if datetime.fromisoformat(customer["expires_at"]) < datetime.utcnow():
        raise HTTPException(status_code=403, detail="Subscription expired")
    
    # Check evaluation limit
    tier = customer["tier"]
    limit = PRICING[tier]["evaluations"]
    if limit != -1 and customer["evaluations_used"] >= limit:
        raise HTTPException(status_code=403, detail="Evaluation limit reached")
    
    return customer

# ============================================================
# METRICS COMPUTATION
# ============================================================

def load_ground_truth() -> Dict[str, str]:
    """Load ground truth from test set"""
    gt = {}
    test_path = Path("data/test.jsonl")
    if test_path.exists():
        with open(test_path) as f:
            for line in f:
                d = json.loads(line)
                gt[d["id"]] = d["label"]
    return gt

def compute_metrics(predictions: List[Prediction], ground_truth: Dict) -> Dict:
    """Compute comprehensive evaluation metrics"""
    y_true = []
    y_pred = []
    confidences = []
    
    for p in predictions:
        if p.id in ground_truth:
            y_true.append(ground_truth[p.id])
            y_pred.append(p.label)
            confidences.append(p.confidence)
    
    if not y_true:
        raise ValueError("No matching predictions found")
    
    # Per-class metrics
    labels = ["KNOWN", "UNKNOWN", "CONTRADICTION"]
    metrics = {"per_class": {}}
    
    for label in labels:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != label and p == label)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == label and p != label)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        metrics["per_class"][label] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
        }
    
    # Overall metrics
    correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    metrics["accuracy"] = round(correct / len(y_true), 4)
    
    # Unknown detection (key metric)
    metrics["unknown_detection"] = {
        "precision": metrics["per_class"]["UNKNOWN"]["precision"],
        "recall": metrics["per_class"]["UNKNOWN"]["recall"],
        "f1": metrics["per_class"]["UNKNOWN"]["f1"],
    }
    
    # ECE
    n_bins = 10
    bin_accs, bin_confs, bin_counts = [], [], []
    
    for i in range(n_bins):
        lo, hi = i / n_bins, (i + 1) / n_bins
        mask = [lo <= c < hi for c in confidences]
        if any(mask):
            bin_correct = [1 if t == p else 0 for t, p, m in zip(y_true, y_pred, mask) if m]
            bin_conf = [c for c, m in zip(confidences, mask) if m]
            bin_accs.append(sum(bin_correct) / len(bin_correct))
            bin_confs.append(sum(bin_conf) / len(bin_conf))
            bin_counts.append(len(bin_correct))
    
    ece = sum(abs(a - c) * n / len(y_true) for a, c, n in zip(bin_accs, bin_confs, bin_counts)) if bin_counts else 0
    metrics["calibration"] = {
        "ece": round(ece, 4),
        "mean_confidence": round(sum(confidences) / len(confidences), 4),
    }
    
    metrics["n_samples"] = len(y_true)
    
    return metrics

def compute_risk_score(metrics: Dict) -> str:
    """Compute epistemic risk score"""
    u_recall = metrics["unknown_detection"]["recall"]
    ece = metrics["calibration"]["ece"]
    
    # Risk factors
    risk_score = 0
    
    # Unknown detection risk (weight: 50%)
    if u_recall < 0.1:
        risk_score += 50  # Critical
    elif u_recall < 0.3:
        risk_score += 35  # High
    elif u_recall < 0.5:
        risk_score += 20  # Medium
    elif u_recall < 0.7:
        risk_score += 10  # Low
    # else: 0 (Minimal)
    
    # Calibration risk (weight: 30%)
    if ece > 0.3:
        risk_score += 30  # Critical
    elif ece > 0.2:
        risk_score += 20  # High
    elif ece > 0.1:
        risk_score += 10  # Medium
    # else: 0 (Good)
    
    # Accuracy risk (weight: 20%)
    if metrics["accuracy"] < 0.3:
        risk_score += 20
    elif metrics["accuracy"] < 0.5:
        risk_score += 10
    
    # Convert to grade
    if risk_score >= 70:
        return "CRITICAL"
    elif risk_score >= 50:
        return "HIGH"
    elif risk_score >= 30:
        return "MEDIUM"
    elif risk_score >= 10:
        return "LOW"
    else:
        return "MINIMAL"

def generate_recommendations(metrics: Dict, risk_score: str) -> List[str]:
    """Generate actionable recommendations"""
    recs = []
    
    u_recall = metrics["unknown_detection"]["recall"]
    ece = metrics["calibration"]["ece"]
    
    if u_recall < 0.3:
        recs.append(
            "CRITICAL: Model fails to detect genuinely unanswerable questions. "
            "Consider implementing explicit epistemic boundaries or abstention mechanisms."
        )
    
    if ece > 0.2:
        recs.append(
            "HIGH: Model is poorly calibrated (overconfident). "
            "Implement confidence calibration (temperature scaling, Platt scaling)."
        )
    
    if metrics["per_class"]["CONTRADICTION"]["f1"] < 0.1:
        recs.append(
            "Model cannot identify contested/debated topics. "
            "Add training data for ambiguous cases or implement multi-perspective outputs."
        )
    
    if risk_score in ["CRITICAL", "HIGH"]:
        recs.append(
            "NOT RECOMMENDED for high-stakes deployment (medical, legal, financial) "
            "without significant epistemic calibration improvements."
        )
    
    if not recs:
        recs.append(
            "Model shows acceptable epistemic calibration. "
            "Continue monitoring with regular ONTO-Bench evaluations."
        )
    
    return recs

# ============================================================
# REPORT GENERATION
# ============================================================

def generate_report_html(evaluation: Dict) -> str:
    """Generate HTML evaluation report"""
    
    metrics = evaluation["metrics"]
    risk_score = evaluation["risk_score"]
    recommendations = evaluation.get("recommendations", [])
    
    risk_colors = {
        "CRITICAL": "#dc2626",
        "HIGH": "#ea580c",
        "MEDIUM": "#ca8a04",
        "LOW": "#16a34a",
        "MINIMAL": "#15803d",
    }
    
    risk_color = risk_colors.get(risk_score, "#6b7280")
    
    recs_html = "\n".join(f"<li>{r}</li>" for r in recommendations)
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>ONTO Enterprise Evaluation Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 40px; }}
        .header {{ border-bottom: 3px solid #4f46e5; padding-bottom: 20px; margin-bottom: 30px; }}
        .header h1 {{ color: #1e1b4b; margin-bottom: 5px; }}
        .header p {{ color: #6b7280; margin: 0; }}
        .risk-badge {{ display: inline-block; padding: 8px 16px; border-radius: 20px; color: white; font-weight: bold; font-size: 14px; background: {risk_color}; }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 30px 0; }}
        .metric-card {{ background: #f9fafb; padding: 20px; border-radius: 8px; text-align: center; }}
        .metric-value {{ font-size: 32px; font-weight: bold; color: #1e1b4b; }}
        .metric-label {{ color: #6b7280; font-size: 14px; margin-top: 5px; }}
        .section {{ margin: 30px 0; }}
        .section h2 {{ color: #1e1b4b; border-bottom: 1px solid #e5e7eb; padding-bottom: 10px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #e5e7eb; }}
        th {{ background: #f9fafb; }}
        .recommendations {{ background: #fef3c7; padding: 20px; border-radius: 8px; }}
        .recommendations h3 {{ margin-top: 0; color: #92400e; }}
        .recommendations ul {{ margin: 0; padding-left: 20px; }}
        .recommendations li {{ margin: 10px 0; }}
        .footer {{ margin-top: 50px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #6b7280; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>ONTO Enterprise Evaluation Report</h1>
        <p>Epistemic Calibration Assessment</p>
    </div>

    <div class="section">
        <p><strong>Model:</strong> {evaluation['model_name']}</p>
        <p><strong>Organization:</strong> {evaluation['organization']}</p>
        <p><strong>Evaluation Date:</strong> {evaluation['completed_at']}</p>
        <p><strong>Evaluation ID:</strong> {evaluation['evaluation_id']}</p>
    </div>

    <div class="section">
        <h2>Epistemic Risk Score</h2>
        <p>
            <span class="risk-badge">{risk_score}</span>
        </p>
        <p style="color: #6b7280; margin-top: 10px;">
            Risk score based on unknown detection capability and confidence calibration.
        </p>
    </div>

    <div class="metric-grid">
        <div class="metric-card">
            <div class="metric-value">{metrics['unknown_detection']['recall']:.0%}</div>
            <div class="metric-label">Unknown Detection Rate</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{metrics['calibration']['ece']:.2f}</div>
            <div class="metric-label">Calibration Error (ECE)</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{metrics['accuracy']:.0%}</div>
            <div class="metric-label">Overall Accuracy</div>
        </div>
    </div>

    <div class="section">
        <h2>Detailed Metrics</h2>
        <table>
            <tr>
                <th>Category</th>
                <th>Precision</th>
                <th>Recall</th>
                <th>F1 Score</th>
            </tr>
            <tr>
                <td>KNOWN (Established Facts)</td>
                <td>{metrics['per_class']['KNOWN']['precision']:.2%}</td>
                <td>{metrics['per_class']['KNOWN']['recall']:.2%}</td>
                <td>{metrics['per_class']['KNOWN']['f1']:.2%}</td>
            </tr>
            <tr>
                <td>UNKNOWN (Open Questions)</td>
                <td>{metrics['per_class']['UNKNOWN']['precision']:.2%}</td>
                <td>{metrics['per_class']['UNKNOWN']['recall']:.2%}</td>
                <td>{metrics['per_class']['UNKNOWN']['f1']:.2%}</td>
            </tr>
            <tr>
                <td>CONTRADICTION (Debated)</td>
                <td>{metrics['per_class']['CONTRADICTION']['precision']:.2%}</td>
                <td>{metrics['per_class']['CONTRADICTION']['recall']:.2%}</td>
                <td>{metrics['per_class']['CONTRADICTION']['f1']:.2%}</td>
            </tr>
        </table>
    </div>

    <div class="section">
        <div class="recommendations">
            <h3>⚠️ Recommendations</h3>
            <ul>
                {recs_html}
            </ul>
        </div>
    </div>

    <div class="section">
        <h2>Methodology</h2>
        <p>
            Evaluation performed on ONTO-Bench v1.9, a benchmark specifically designed 
            to measure epistemic calibration in AI systems. The benchmark contains 
            268 samples across three categories: established facts (KNOWN), 
            genuinely open scientific questions (UNKNOWN), and legitimately 
            contested claims (CONTRADICTION).
        </p>
        <p>
            <strong>Key Metric - Unknown Detection Rate:</strong> Measures the model's 
            ability to recognize genuinely unanswerable questions. Low scores indicate 
            the model confidently answers questions that have no known answer.
        </p>
    </div>

    <div class="footer">
        <p>
            Generated by ONTO Enterprise | onto-bench.org<br>
            This report is confidential and intended for the recipient organization only.<br>
            © 2026 ONTO Project
        </p>
    </div>
</body>
</html>
"""
    return html

# ============================================================
# API
# ============================================================

app = FastAPI(
    title="ONTO Enterprise Evaluation API",
    description="Epistemic calibration evaluation for enterprise AI systems",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Public endpoints ---

@app.get("/")
def root():
    return {
        "service": "ONTO Enterprise Evaluation API",
        "version": "1.0.0",
        "docs": "/docs",
        "contact": "enterprise@onto-bench.org",
    }

@app.post("/enterprise/pilot")
def request_pilot(request: PilotRequest):
    """Request a free pilot evaluation"""
    
    pilot_id = secrets.token_hex(8)
    
    # Save pilot request
    pilot_data = {
        "pilot_id": pilot_id,
        "company_name": request.company_name,
        "contact_name": request.contact_name,
        "contact_email": request.contact_email,
        "model_description": request.model_description,
        "use_case": request.use_case,
        "requested_at": datetime.utcnow().isoformat(),
        "status": "pending_review",
    }
    
    with open(CUSTOMERS_DIR / f"pilot_{pilot_id}.json", 'w') as f:
        json.dump(pilot_data, f, indent=2)
    
    return {
        "status": "received",
        "pilot_id": pilot_id,
        "message": "Pilot request received. We'll contact you within 24 hours.",
    }

@app.get("/enterprise/pricing")
def get_pricing():
    """Get pricing tiers"""
    return {
        "tiers": PRICING,
        "currency": "USD",
        "contact": "enterprise@onto-bench.org",
    }

# --- Authenticated endpoints ---

@app.post("/enterprise/evaluate")
def submit_evaluation(
    request: EvaluationRequest,
    background_tasks: BackgroundTasks,
    customer: Dict = Depends(verify_api_key),
):
    """Submit model predictions for evaluation"""
    
    evaluation_id = secrets.token_hex(12)
    
    # Create evaluation record
    evaluation = {
        "evaluation_id": evaluation_id,
        "customer_id": customer["customer_id"],
        "model_name": request.model_name,
        "model_version": request.model_version,
        "organization": request.organization,
        "contact_email": request.contact_email,
        "notes": request.notes,
        "status": EvaluationStatus.PENDING,
        "submitted_at": datetime.utcnow().isoformat(),
        "completed_at": None,
        "metrics": None,
        "risk_score": None,
        "recommendations": None,
    }
    
    # Save predictions
    predictions_path = EVALUATIONS_DIR / f"{evaluation_id}_predictions.json"
    with open(predictions_path, 'w') as f:
        json.dump([p.dict() for p in request.predictions], f)
    
    # Save evaluation
    eval_path = EVALUATIONS_DIR / f"{evaluation_id}.json"
    with open(eval_path, 'w') as f:
        json.dump(evaluation, f, indent=2)
    
    # Process in background
    background_tasks.add_task(process_evaluation, evaluation_id)
    
    return {
        "evaluation_id": evaluation_id,
        "status": "pending",
        "message": "Evaluation submitted. Check status at /enterprise/status/{evaluation_id}",
    }

def process_evaluation(evaluation_id: str):
    """Background task to process evaluation"""
    
    eval_path = EVALUATIONS_DIR / f"{evaluation_id}.json"
    predictions_path = EVALUATIONS_DIR / f"{evaluation_id}_predictions.json"
    
    with open(eval_path) as f:
        evaluation = json.load(f)
    
    with open(predictions_path) as f:
        predictions = [Prediction(**p) for p in json.load(f)]
    
    evaluation["status"] = EvaluationStatus.PROCESSING
    with open(eval_path, 'w') as f:
        json.dump(evaluation, f, indent=2)
    
    try:
        # Compute metrics
        ground_truth = load_ground_truth()
        metrics = compute_metrics(predictions, ground_truth)
        risk_score = compute_risk_score(metrics)
        recommendations = generate_recommendations(metrics, risk_score)
        
        # Update evaluation
        evaluation["status"] = EvaluationStatus.COMPLETED
        evaluation["completed_at"] = datetime.utcnow().isoformat()
        evaluation["metrics"] = metrics
        evaluation["risk_score"] = risk_score
        evaluation["recommendations"] = recommendations
        
        # Generate report
        report_html = generate_report_html(evaluation)
        report_path = REPORTS_DIR / f"{evaluation_id}.html"
        with open(report_path, 'w') as f:
            f.write(report_html)
        
    except Exception as e:
        evaluation["status"] = EvaluationStatus.FAILED
        evaluation["error"] = str(e)
    
    with open(eval_path, 'w') as f:
        json.dump(evaluation, f, indent=2)

@app.get("/enterprise/status/{evaluation_id}")
def get_status(
    evaluation_id: str,
    customer: Dict = Depends(verify_api_key),
) -> EvaluationResult:
    """Get evaluation status"""
    
    eval_path = EVALUATIONS_DIR / f"{evaluation_id}.json"
    
    if not eval_path.exists():
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    with open(eval_path) as f:
        evaluation = json.load(f)
    
    # Verify ownership
    if evaluation["customer_id"] != customer["customer_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    report_url = None
    if evaluation["status"] == EvaluationStatus.COMPLETED:
        report_url = f"/enterprise/report/{evaluation_id}"
    
    return EvaluationResult(
        evaluation_id=evaluation_id,
        status=evaluation["status"],
        model_name=evaluation["model_name"],
        organization=evaluation["organization"],
        submitted_at=evaluation["submitted_at"],
        completed_at=evaluation.get("completed_at"),
        metrics=evaluation.get("metrics"),
        risk_score=evaluation.get("risk_score"),
        report_url=report_url,
    )

@app.get("/enterprise/report/{evaluation_id}")
def get_report(
    evaluation_id: str,
    customer: Dict = Depends(verify_api_key),
):
    """Download evaluation report"""
    
    eval_path = EVALUATIONS_DIR / f"{evaluation_id}.json"
    
    if not eval_path.exists():
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    with open(eval_path) as f:
        evaluation = json.load(f)
    
    # Verify ownership
    if evaluation["customer_id"] != customer["customer_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if evaluation["status"] != EvaluationStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Evaluation not completed")
    
    report_path = REPORTS_DIR / f"{evaluation_id}.html"
    
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    
    return FileResponse(
        report_path,
        media_type="text/html",
        filename=f"onto_report_{evaluation_id}.html",
    )

@app.get("/enterprise/evaluations")
def list_evaluations(
    customer: Dict = Depends(verify_api_key),
) -> List[EvaluationResult]:
    """List all evaluations for customer"""
    
    evaluations = []
    
    for eval_file in EVALUATIONS_DIR.glob("*.json"):
        if "_predictions" in eval_file.name:
            continue
        
        with open(eval_file) as f:
            evaluation = json.load(f)
        
        if evaluation["customer_id"] == customer["customer_id"]:
            report_url = None
            if evaluation["status"] == EvaluationStatus.COMPLETED:
                report_url = f"/enterprise/report/{evaluation['evaluation_id']}"
            
            evaluations.append(EvaluationResult(
                evaluation_id=evaluation["evaluation_id"],
                status=evaluation["status"],
                model_name=evaluation["model_name"],
                organization=evaluation["organization"],
                submitted_at=evaluation["submitted_at"],
                completed_at=evaluation.get("completed_at"),
                metrics=evaluation.get("metrics"),
                risk_score=evaluation.get("risk_score"),
                report_url=report_url,
            ))
    
    return sorted(evaluations, key=lambda x: x.submitted_at, reverse=True)

# ============================================================
# ADMIN (Internal)
# ============================================================

def create_customer(
    company_name: str,
    contact_email: str,
    tier: str,
) -> Dict:
    """Create new customer and API key"""
    
    customer_id = secrets.token_hex(8)
    api_key = f"onto_{secrets.token_hex(24)}"
    
    customer = {
        "customer_id": customer_id,
        "company_name": company_name,
        "contact_email": contact_email,
        "tier": tier,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(days=PRICING[tier]["duration_days"])).isoformat(),
        "evaluations_used": 0,
    }
    
    # Save customer
    with open(CUSTOMERS_DIR / f"{customer_id}.json", 'w') as f:
        json.dump(customer, f, indent=2)
    
    # Add API key
    keys_file = CUSTOMERS_DIR / "keys.json"
    keys = {}
    if keys_file.exists():
        with open(keys_file) as f:
            keys = json.load(f)
    
    keys[api_key] = customer
    
    with open(keys_file, 'w') as f:
        json.dump(keys, f, indent=2)
    
    return {"api_key": api_key, **customer}

# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == "create-customer" and len(sys.argv) >= 5:
            company = sys.argv[2]
            email = sys.argv[3]
            tier = sys.argv[4]
            
            result = create_customer(company, email, tier)
            print(f"Customer created:")
            print(f"  API Key: {result['api_key']}")
            print(f"  Customer ID: {result['customer_id']}")
            print(f"  Tier: {tier}")
            print(f"  Expires: {result['expires_at']}")
        
        elif cmd == "create-pilot" and len(sys.argv) >= 4:
            company = sys.argv[2]
            email = sys.argv[3]
            
            result = create_customer(company, email, "pilot")
            print(f"Pilot created:")
            print(f"  API Key: {result['api_key']}")
        
        else:
            print("Usage:")
            print("  python api.py create-customer <company> <email> <tier>")
            print("  python api.py create-pilot <company> <email>")
    else:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8080)
