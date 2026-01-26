#!/usr/bin/env python3
"""
ONTO-Bench Leaderboard API
Minimal FastAPI server for leaderboard

Run: uvicorn leaderboard.api:app --reload
"""

import json
import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, asdict

from fastapi import FastAPI, HTTPException, UploadFile, File, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# ============================================================
# CONFIG
# ============================================================

DATA_DIR = Path("leaderboard_data")
SUBMISSIONS_DIR = DATA_DIR / "submissions"
RESULTS_FILE = DATA_DIR / "results.json"
API_KEYS_FILE = DATA_DIR / "api_keys.json"

# Ensure dirs exist
DATA_DIR.mkdir(exist_ok=True)
SUBMISSIONS_DIR.mkdir(exist_ok=True)

# ============================================================
# MODELS
# ============================================================

class Prediction(BaseModel):
    id: str
    label: str  # KNOWN, UNKNOWN, CONTRADICTION
    confidence: float


class SubmissionRequest(BaseModel):
    model_name: str
    model_version: Optional[str] = None
    organization: Optional[str] = None
    predictions: List[Prediction]


class LeaderboardEntry(BaseModel):
    rank: int
    model: str
    organization: str
    u_precision: float
    u_recall: float
    u_f1: float
    ece: float
    accuracy: float
    submitted_at: str
    verified: bool = False


# ============================================================
# METRICS
# ============================================================

def load_ground_truth() -> dict:
    """Load ground truth labels from test set"""
    gt = {}
    test_path = Path("data/test.jsonl")
    if test_path.exists():
        with open(test_path) as f:
            for line in f:
                d = json.loads(line)
                gt[d["id"]] = d["label"]
    return gt


def compute_metrics(predictions: List[Prediction], ground_truth: dict) -> dict:
    """Compute evaluation metrics"""
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
    
    # Unknown detection metrics
    u_tp = sum(1 for t, p in zip(y_true, y_pred) if t == "UNKNOWN" and p == "UNKNOWN")
    u_fp = sum(1 for t, p in zip(y_true, y_pred) if t != "UNKNOWN" and p == "UNKNOWN")
    u_fn = sum(1 for t, p in zip(y_true, y_pred) if t == "UNKNOWN" and p != "UNKNOWN")
    
    u_precision = u_tp / (u_tp + u_fp) if (u_tp + u_fp) > 0 else 0
    u_recall = u_tp / (u_tp + u_fn) if (u_tp + u_fn) > 0 else 0
    u_f1 = 2 * u_precision * u_recall / (u_precision + u_recall) if (u_precision + u_recall) > 0 else 0
    
    # Accuracy
    correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    accuracy = correct / len(y_true)
    
    # ECE (simplified)
    n_bins = 10
    bin_accs = []
    bin_confs = []
    bin_counts = []
    
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
    
    return {
        "u_precision": round(u_precision, 4),
        "u_recall": round(u_recall, 4),
        "u_f1": round(u_f1, 4),
        "ece": round(ece, 4),
        "accuracy": round(accuracy, 4),
        "n_samples": len(y_true),
    }


# ============================================================
# STORAGE
# ============================================================

def load_results() -> List[dict]:
    """Load leaderboard results"""
    if RESULTS_FILE.exists():
        with open(RESULTS_FILE) as f:
            return json.load(f)
    return []


def save_results(results: List[dict]):
    """Save leaderboard results"""
    with open(RESULTS_FILE, 'w') as f:
        json.dump(results, f, indent=2)


def add_submission(entry: dict):
    """Add new submission to leaderboard"""
    results = load_results()
    
    # Check for duplicate
    for i, r in enumerate(results):
        if r["model"] == entry["model"] and r.get("organization") == entry.get("organization"):
            # Update existing
            results[i] = entry
            break
    else:
        results.append(entry)
    
    # Sort by U-F1
    results.sort(key=lambda x: x["u_f1"], reverse=True)
    
    # Update ranks
    for i, r in enumerate(results):
        r["rank"] = i + 1
    
    save_results(results)
    return results


# ============================================================
# API
# ============================================================

app = FastAPI(
    title="ONTO-Bench Leaderboard",
    description="Epistemic calibration benchmark for LLMs",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "ONTO-Bench Leaderboard API", "docs": "/docs"}


@app.get("/api/leaderboard")
def get_leaderboard(limit: int = 20) -> List[dict]:
    """Get current leaderboard"""
    results = load_results()
    return results[:limit]


@app.post("/api/submit")
def submit_predictions(submission: SubmissionRequest) -> dict:
    """Submit model predictions for evaluation"""
    
    # Load ground truth
    gt = load_ground_truth()
    if not gt:
        raise HTTPException(status_code=500, detail="Ground truth not loaded")
    
    # Compute metrics
    try:
        metrics = compute_metrics(submission.predictions, gt)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Create entry
    entry = {
        "model": submission.model_name,
        "organization": submission.organization or "Anonymous",
        "model_version": submission.model_version,
        "submitted_at": datetime.utcnow().isoformat(),
        "verified": False,
        **metrics,
    }
    
    # Save submission
    sub_id = hashlib.sha256(
        f"{submission.model_name}{datetime.utcnow().isoformat()}".encode()
    ).hexdigest()[:12]
    
    sub_path = SUBMISSIONS_DIR / f"{sub_id}.json"
    with open(sub_path, 'w') as f:
        json.dump({
            "submission": entry,
            "predictions": [p.dict() for p in submission.predictions],
        }, f, indent=2)
    
    # Add to leaderboard
    results = add_submission(entry)
    
    return {
        "submission_id": sub_id,
        "status": "success",
        "metrics": metrics,
        "rank": next((r["rank"] for r in results if r["model"] == entry["model"]), None),
    }


@app.get("/api/dataset")
def get_dataset_info() -> dict:
    """Get dataset information (no labels)"""
    return {
        "name": "ONTO-Bench",
        "version": "1.6",
        "total_samples": 268,
        "test_samples": 55,
        "categories": ["KNOWN", "UNKNOWN", "CONTRADICTION"],
        "download": "https://github.com/onto-project/onto-bench",
    }


@app.get("/api/health")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


# ============================================================
# SEED DATA
# ============================================================

def seed_baseline_results():
    """Seed leaderboard with baseline results"""
    baselines = [
        {
            "model": "ONTO",
            "organization": "ONTO Project",
            "u_precision": 0.41,
            "u_recall": 0.96,
            "u_f1": 0.58,
            "ece": 0.30,
            "accuracy": 0.43,
            "submitted_at": "2026-01-26T00:00:00",
            "verified": True,
        },
        {
            "model": "Claude 3 Sonnet",
            "organization": "Anthropic",
            "u_precision": 0.45,
            "u_recall": 0.09,
            "u_f1": 0.15,
            "ece": 0.31,
            "accuracy": 0.48,
            "submitted_at": "2026-01-26T00:00:00",
            "verified": False,
        },
        {
            "model": "GPT-4",
            "organization": "OpenAI",
            "u_precision": 0.10,
            "u_recall": 0.01,
            "u_f1": 0.02,
            "ece": 0.34,
            "accuracy": 0.44,
            "submitted_at": "2026-01-26T00:00:00",
            "verified": False,
        },
        {
            "model": "Llama 3 70B",
            "organization": "Meta",
            "u_precision": 0.20,
            "u_recall": 0.01,
            "u_f1": 0.02,
            "ece": 0.33,
            "accuracy": 0.46,
            "submitted_at": "2026-01-26T00:00:00",
            "verified": False,
        },
    ]
    
    # Sort and rank
    baselines.sort(key=lambda x: x["u_f1"], reverse=True)
    for i, b in enumerate(baselines):
        b["rank"] = i + 1
    
    save_results(baselines)
    print(f"Seeded {len(baselines)} baseline results")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--seed":
        seed_baseline_results()
    else:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8080)
