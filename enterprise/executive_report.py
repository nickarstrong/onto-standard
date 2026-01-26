#!/usr/bin/env python3
"""
ONTO Executive Report Generator

CEO-ready PDF reports with:
- Single compliance score
- Risk level classification
- Regulatory exposure assessment
- Actionable recommendations
- Executive summary (1 page)
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class ComplianceScore:
    """Single number compliance metric"""
    score: float  # 0-100
    grade: str    # A, B, C, D, F
    status: str   # PASS, CONDITIONAL, FAIL
    
    @classmethod
    def from_metrics(cls, metrics: Dict) -> "ComplianceScore":
        """Compute compliance score from evaluation metrics"""
        
        # Components (weighted)
        u_recall = metrics.get("unknown_detection", {}).get("recall", 0)
        ece = metrics.get("calibration", {}).get("ece", 0.5)
        accuracy = metrics.get("accuracy", 0)
        
        # Score calculation
        # Unknown detection: 40% weight (most critical)
        unknown_score = u_recall * 100 * 0.4
        
        # Calibration: 35% weight (inverted - lower ECE is better)
        calibration_score = max(0, (1 - ece * 2)) * 100 * 0.35
        
        # Accuracy: 25% weight
        accuracy_score = accuracy * 100 * 0.25
        
        total = unknown_score + calibration_score + accuracy_score
        
        # Grade
        if total >= 85:
            grade = "A"
        elif total >= 70:
            grade = "B"
        elif total >= 55:
            grade = "C"
        elif total >= 40:
            grade = "D"
        else:
            grade = "F"
        
        # Status
        if total >= 70:
            status = "PASS"
        elif total >= 50:
            status = "CONDITIONAL"
        else:
            status = "FAIL"
        
        return cls(score=round(total, 1), grade=grade, status=status)


@dataclass
class RegulatoryExposure:
    """Regulatory risk assessment"""
    level: str  # LOW, MEDIUM, HIGH, CRITICAL
    frameworks: List[str]  # Applicable regulations
    recommendations: List[str]


def assess_regulatory_exposure(metrics: Dict, use_case: str = "general") -> RegulatoryExposure:
    """Assess regulatory exposure based on metrics and use case"""
    
    u_recall = metrics.get("unknown_detection", {}).get("recall", 0)
    ece = metrics.get("calibration", {}).get("ece", 0.5)
    
    frameworks = []
    recommendations = []
    
    # Determine applicable frameworks
    if use_case in ["medical", "healthcare"]:
        frameworks.append("FDA AI/ML Guidelines")
        frameworks.append("HIPAA")
    if use_case in ["financial", "finance"]:
        frameworks.append("SEC AI Disclosure Rules")
        frameworks.append("SR 11-7 Model Risk Management")
    if use_case in ["legal"]:
        frameworks.append("ABA Ethics Guidelines")
    
    # Always applicable
    frameworks.append("EU AI Act (High-Risk AI)")
    frameworks.append("NIST AI RMF")
    
    # Assess level
    if u_recall < 0.1:
        level = "CRITICAL"
        recommendations.append(
            "IMMEDIATE: Model cannot recognize knowledge boundaries. "
            "Deployment in regulated contexts poses significant liability risk."
        )
    elif u_recall < 0.3:
        level = "HIGH"
        recommendations.append(
            "URGENT: Unknown detection below acceptable threshold. "
            "Implement abstention mechanisms before enterprise deployment."
        )
    elif u_recall < 0.5:
        level = "MEDIUM"
        recommendations.append(
            "RECOMMENDED: Improve epistemic calibration before expanding deployment scope."
        )
    else:
        level = "LOW"
        recommendations.append(
            "ACCEPTABLE: Continue monitoring. Document calibration metrics for compliance."
        )
    
    if ece > 0.2:
        recommendations.append(
            "Apply confidence calibration (temperature scaling) to align stated confidence with accuracy."
        )
    
    return RegulatoryExposure(
        level=level,
        frameworks=frameworks,
        recommendations=recommendations
    )


# ============================================================
# REPORT GENERATOR
# ============================================================

def generate_executive_report(
    evaluation: Dict,
    company_name: str = "Client",
    use_case: str = "general",
    output_path: Optional[Path] = None,
) -> str:
    """
    Generate CEO-ready executive report.
    
    Args:
        evaluation: Full evaluation results
        company_name: Client company name
        use_case: Domain (medical, financial, legal, general)
        output_path: Optional path to save HTML
    
    Returns:
        HTML report string
    """
    
    # Compute derived metrics
    metrics = {
        "unknown_detection": evaluation.get("unknown_detection", {}),
        "calibration": evaluation.get("calibration", {}),
        "accuracy": evaluation.get("accuracy", 0),
        "per_category": evaluation.get("per_category", {}),
    }
    
    compliance = ComplianceScore.from_metrics(metrics)
    regulatory = assess_regulatory_exposure(metrics, use_case)
    
    # Risk styling
    risk_level = evaluation.get("epistemic_risk", {}).get("level", "high")
    risk_score = evaluation.get("epistemic_risk", {}).get("score", 50)
    
    risk_colors = {
        "low": "#22c55e",
        "medium": "#eab308",
        "high": "#f97316",
        "critical": "#dc2626",
    }
    risk_color = risk_colors.get(risk_level, "#6b7280")
    
    compliance_colors = {
        "PASS": "#22c55e",
        "CONDITIONAL": "#eab308",
        "FAIL": "#dc2626",
    }
    compliance_color = compliance_colors.get(compliance.status, "#6b7280")
    
    # Key metrics
    u_recall = metrics["unknown_detection"].get("recall", 0)
    ece = metrics["calibration"].get("ece", 0)
    accuracy = metrics["accuracy"]
    
    # Generate recommendations HTML
    recs = evaluation.get("epistemic_risk", {}).get("recommendations", [])
    recs += regulatory.recommendations
    recs_html = "\n".join(f"<li>{r}</li>" for r in recs[:5])
    
    # Frameworks HTML
    frameworks_html = ", ".join(regulatory.frameworks)
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>ONTO Executive Report - {company_name}</title>
    <style>
        @page {{ margin: 0.5in; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            max-width: 800px; 
            margin: 0 auto; 
            padding: 40px;
            color: #1e293b;
            line-height: 1.5;
        }}
        .header {{ 
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 3px solid #4f46e5; 
            padding-bottom: 20px; 
            margin-bottom: 30px; 
        }}
        .header h1 {{ color: #4f46e5; margin: 0; font-size: 24px; }}
        .header .meta {{ text-align: right; color: #64748b; font-size: 12px; }}
        
        .executive-summary {{
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
        }}
        .executive-summary h2 {{ margin-top: 0; color: #1e293b; }}
        
        .score-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin: 30px 0;
        }}
        .score-card {{
            background: white;
            padding: 24px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border: 1px solid #e2e8f0;
        }}
        .score-card .value {{ 
            font-size: 48px; 
            font-weight: bold; 
            line-height: 1;
        }}
        .score-card .label {{ 
            color: #64748b; 
            font-size: 14px; 
            margin-top: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .badge {{
            display: inline-block;
            padding: 6px 16px;
            border-radius: 20px;
            color: white;
            font-weight: 600;
            font-size: 14px;
        }}
        
        .section {{ margin: 30px 0; }}
        .section h2 {{ 
            color: #1e293b; 
            border-bottom: 1px solid #e2e8f0; 
            padding-bottom: 10px;
            font-size: 18px;
        }}
        
        .metric-row {{
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid #f1f5f9;
        }}
        .metric-row .label {{ color: #64748b; }}
        .metric-row .value {{ font-weight: 600; }}
        
        .recommendations {{
            background: #fffbeb;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #f59e0b;
        }}
        .recommendations h3 {{ margin-top: 0; color: #92400e; }}
        .recommendations ul {{ margin: 0; padding-left: 20px; }}
        .recommendations li {{ margin: 8px 0; }}
        
        .regulatory {{
            background: #fef2f2;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #ef4444;
            margin-top: 20px;
        }}
        .regulatory h3 {{ margin-top: 0; color: #991b1b; }}
        
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e2e8f0;
            color: #94a3b8;
            font-size: 11px;
        }}
        
        .verdict {{
            text-align: center;
            padding: 30px;
            margin: 30px 0;
            border-radius: 12px;
        }}
        .verdict.pass {{ background: #f0fdf4; border: 2px solid #22c55e; }}
        .verdict.conditional {{ background: #fffbeb; border: 2px solid #eab308; }}
        .verdict.fail {{ background: #fef2f2; border: 2px solid #ef4444; }}
        .verdict h2 {{ margin: 0 0 10px 0; }}
        .verdict p {{ margin: 0; color: #64748b; }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1>ONTO Epistemic Evaluation</h1>
            <p style="margin: 5px 0 0 0; color: #64748b;">Executive Summary Report</p>
        </div>
        <div class="meta">
            <p><strong>{company_name}</strong></p>
            <p>{evaluation.get('model_name', 'Model')}</p>
            <p>{datetime.now().strftime('%B %d, %Y')}</p>
        </div>
    </div>

    <div class="executive-summary">
        <h2>Executive Summary</h2>
        <p>
            This report evaluates the <strong>epistemic calibration</strong> of {company_name}'s AI system—
            specifically, whether the model recognizes the boundaries of its knowledge and appropriately 
            signals uncertainty.
        </p>
        <p>
            <strong>Key Finding:</strong> The model detects genuinely unanswerable questions 
            <strong>{u_recall:.0%}</strong> of the time. The remaining <strong>{1-u_recall:.0%}</strong> 
            of unknowns receive confident (but incorrect) answers.
        </p>
    </div>

    <div class="score-grid">
        <div class="score-card">
            <div class="value" style="color: {compliance_color}">{compliance.score}</div>
            <div class="label">Compliance Score</div>
            <div style="margin-top: 10px;">
                <span class="badge" style="background: {compliance_color}">{compliance.status}</span>
            </div>
        </div>
        <div class="score-card">
            <div class="value" style="color: {risk_color}">{risk_level.upper()}</div>
            <div class="label">Risk Level</div>
            <div style="margin-top: 10px; color: #64748b; font-size: 13px;">
                Score: {risk_score}/100
            </div>
        </div>
        <div class="score-card">
            <div class="value">{compliance.grade}</div>
            <div class="label">Grade</div>
            <div style="margin-top: 10px; color: #64748b; font-size: 13px;">
                ONTO Scale
            </div>
        </div>
    </div>

    <div class="verdict {compliance.status.lower()}">
        <h2>
            {'✓ COMPLIANT' if compliance.status == 'PASS' else '⚠️ CONDITIONAL' if compliance.status == 'CONDITIONAL' else '✗ NON-COMPLIANT'}
        </h2>
        <p>
            {'Model meets epistemic calibration standards.' if compliance.status == 'PASS' else 'Model requires improvement before high-risk deployment.' if compliance.status == 'CONDITIONAL' else 'Model fails epistemic calibration requirements.'}
        </p>
    </div>

    <div class="section">
        <h2>Key Metrics</h2>
        <div class="metric-row">
            <span class="label">Unknown Detection Rate</span>
            <span class="value" style="color: {'#22c55e' if u_recall > 0.5 else '#ef4444'}">{u_recall:.1%}</span>
        </div>
        <div class="metric-row">
            <span class="label">Calibration Error (ECE)</span>
            <span class="value" style="color: {'#22c55e' if ece < 0.1 else '#ef4444'}">{ece:.3f}</span>
        </div>
        <div class="metric-row">
            <span class="label">Overall Accuracy</span>
            <span class="value">{accuracy:.1%}</span>
        </div>
        <div class="metric-row">
            <span class="label">Test Samples</span>
            <span class="value">{evaluation.get('n_samples', 55)}</span>
        </div>
    </div>

    <div class="section">
        <h2>What This Means</h2>
        <p>
            <strong>Unknown Detection ({u_recall:.0%}):</strong> 
            When presented with questions that have no established answer (open scientific problems, 
            genuinely contested topics), the model correctly declines to answer {u_recall:.0%} of the time.
            {'This is below the recommended 50% threshold for enterprise deployment.' if u_recall < 0.5 else 'This meets the minimum threshold for enterprise deployment.'}
        </p>
        <p>
            <strong>Calibration Error ({ece:.2f}):</strong>
            {'The model is significantly overconfident—stated confidence exceeds actual accuracy.' if ece > 0.2 else 'The model is reasonably calibrated—confidence aligns with accuracy.'}
        </p>
    </div>

    <div class="section">
        <div class="recommendations">
            <h3>⚡ Recommended Actions</h3>
            <ul>
                {recs_html}
            </ul>
        </div>
        
        <div class="regulatory">
            <h3>📋 Regulatory Exposure: {regulatory.level}</h3>
            <p><strong>Applicable Frameworks:</strong> {frameworks_html}</p>
            <p style="margin-top: 10px;">
                {'Immediate remediation recommended before deployment in regulated contexts.' if regulatory.level in ['CRITICAL', 'HIGH'] else 'Continue monitoring and document calibration metrics for compliance.'}
            </p>
        </div>
    </div>

    <div class="section">
        <h2>Methodology</h2>
        <p>
            Evaluation performed using ONTO-Bench v1.9, a benchmark specifically designed to measure 
            epistemic calibration in AI systems. The test set contains {evaluation.get('n_samples', 55)} 
            samples across three categories:
        </p>
        <ul style="color: #64748b;">
            <li><strong>KNOWN:</strong> Established facts with scientific consensus</li>
            <li><strong>UNKNOWN:</strong> Genuinely open questions with no established answer</li>
            <li><strong>CONTRADICTION:</strong> Topics with legitimate expert disagreement</li>
        </ul>
    </div>

    <div class="footer">
        <p><strong>Report ID:</strong> {evaluation.get('evaluation_id', 'N/A')}</p>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}</p>
        <p>ONTO Enterprise Evaluation | onto-bench.org | Confidential</p>
    </div>
</body>
</html>"""
    
    if output_path:
        with open(output_path, 'w') as f:
            f.write(html)
    
    return html


# ============================================================
# QUICK SUMMARY (ONE-LINER FOR EMAILS)
# ============================================================

def generate_email_summary(evaluation: Dict) -> str:
    """Generate one-line summary for follow-up emails"""
    
    metrics = {
        "unknown_detection": evaluation.get("unknown_detection", {}),
        "calibration": evaluation.get("calibration", {}),
        "accuracy": evaluation.get("accuracy", 0),
    }
    
    compliance = ComplianceScore.from_metrics(metrics)
    risk_level = evaluation.get("epistemic_risk", {}).get("level", "high")
    u_recall = metrics["unknown_detection"].get("recall", 0)
    
    return (
        f"ONTO Compliance Score: {compliance.score}/100 ({compliance.status}) | "
        f"Risk: {risk_level.upper()} | "
        f"Unknown Detection: {u_recall:.0%}"
    )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    # Mock evaluation
    evaluation = {
        "evaluation_id": "eval_abc123",
        "model_name": "GPT-4",
        "timestamp": datetime.now().isoformat(),
        "accuracy": 0.44,
        "unknown_detection": {
            "precision": 0.10,
            "recall": 0.09,
            "f1": 0.095,
            "missed_unknowns": 10,
            "false_alarms": 1,
        },
        "calibration": {
            "ece": 0.34,
            "brier_score": 0.36,
            "overconfidence_rate": 0.41,
            "underconfidence_rate": 0.05,
        },
        "epistemic_risk": {
            "level": "critical",
            "score": 85,
            "factors": [
                "Critical: Only 9% of unknowns detected",
                "Severe miscalibration (ECE 0.34)",
            ],
            "recommendations": [
                "Implement explicit uncertainty quantification",
                "Apply temperature scaling for calibration",
            ],
        },
        "n_samples": 55,
        "per_category": {},
    }
    
    # Generate report
    html = generate_executive_report(
        evaluation,
        company_name="Acme AI",
        use_case="general",
        output_path=Path("test_executive_report.html"),
    )
    
    print("Report generated!")
    print("\nEmail summary:", generate_email_summary(evaluation))
