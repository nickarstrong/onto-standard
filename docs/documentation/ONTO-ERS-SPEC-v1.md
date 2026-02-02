# ONTO Epistemic Risk Standard (ONTO-ERS)
## Technical Specification v1.0

**Status:** Draft  
**Version:** 1.0.0  
**Last Updated:** 2026-02-02  
**Authors:** ONTO Standard LLC  
**License:** Apache 2.0  

---

## Abstract

ONTO-ERS defines a standardized methodology for measuring and reporting epistemic risk in AI systems. Epistemic risk quantifies the gap between an AI system's stated confidence and its actual accuracy—a critical metric for regulatory compliance, liability management, and operational safety.

This specification establishes:
- Core metrics for epistemic risk assessment
- Evaluation protocols and reporting formats
- Compliance tiers and certification requirements
- API interfaces for integration

**Design Principle:** "Градусник, не врач" (Thermometer, not doctor) — ONTO measures epistemic risk without modifying underlying AI models.

---

## 1. Definitions

### 1.1 Core Terms

| Term | Definition |
|------|------------|
| **Epistemic Risk** | The probability-weighted exposure arising from miscalibrated AI confidence |
| **Calibration** | The degree to which stated confidence matches empirical accuracy |
| **Confidence** | Model's self-reported probability of correctness (0.0–1.0) |
| **Accuracy** | Empirical correctness rate over evaluation dataset |
| **Epistemic Gap** | `\|Confidence - Accuracy\|` for a given prediction |

### 1.2 Metric Identifiers

| ID | Name | Range | Optimal |
|----|------|-------|---------|
| `ECE` | Expected Calibration Error | 0.0–1.0 | ≤ 0.10 |
| `URE` | Uncertainty Recall | 0–100% | ≥ 70% |
| `ERS` | Epistemic Risk Score | 0–100 | ≤ 30 |

---

## 2. Core Metrics

### 2.1 Expected Calibration Error (ECE)

ECE measures the average gap between confidence and accuracy across confidence bins.

**Formula:**

```
ECE = Σ (|B_m| / n) × |acc(B_m) - conf(B_m)|
```

Where:
- `B_m` = set of predictions in bin m
- `n` = total number of predictions
- `acc(B_m)` = accuracy of predictions in bin m
- `conf(B_m)` = average confidence in bin m
- Bins: [0.0-0.1), [0.1-0.2), ..., [0.9-1.0]

**Implementation:**

```python
def calculate_ece(predictions: list[dict], num_bins: int = 10) -> float:
    """
    Calculate Expected Calibration Error.
    
    Args:
        predictions: List of {confidence: float, correct: bool}
        num_bins: Number of confidence bins (default: 10)
    
    Returns:
        ECE value between 0.0 and 1.0
    """
    bins = [[] for _ in range(num_bins)]
    
    for pred in predictions:
        bin_idx = min(int(pred['confidence'] * num_bins), num_bins - 1)
        bins[bin_idx].append(pred)
    
    ece = 0.0
    n = len(predictions)
    
    for bin_preds in bins:
        if not bin_preds:
            continue
        
        bin_size = len(bin_preds)
        bin_acc = sum(1 for p in bin_preds if p['correct']) / bin_size
        bin_conf = sum(p['confidence'] for p in bin_preds) / bin_size
        
        ece += (bin_size / n) * abs(bin_acc - bin_conf)
    
    return ece
```

**Interpretation:**

| ECE Range | Assessment | Action Required |
|-----------|------------|-----------------|
| 0.00–0.05 | Excellent | Maintenance only |
| 0.05–0.10 | Good | Minor adjustments |
| 0.10–0.15 | Acceptable | Review recommended |
| 0.15–0.25 | Poor | Intervention required |
| > 0.25 | Critical | Immediate action |

---

### 2.2 Uncertainty Recall (U-Recall)

U-Recall measures the system's ability to express low confidence when it is incorrect.

**Formula:**

```
U-Recall = TP_u / (TP_u + FN_u)
```

Where:
- `TP_u` = True Positive Uncertain: incorrect predictions with confidence < threshold
- `FN_u` = False Negative Uncertain: incorrect predictions with confidence ≥ threshold
- Default threshold: 0.7

**Implementation:**

```python
def calculate_u_recall(
    predictions: list[dict], 
    uncertainty_threshold: float = 0.7
) -> float:
    """
    Calculate Uncertainty Recall.
    
    Args:
        predictions: List of {confidence: float, correct: bool}
        uncertainty_threshold: Confidence below which prediction is "uncertain"
    
    Returns:
        U-Recall percentage (0-100)
    """
    incorrect = [p for p in predictions if not p['correct']]
    
    if not incorrect:
        return 100.0  # No errors = perfect recall
    
    true_positives = sum(
        1 for p in incorrect 
        if p['confidence'] < uncertainty_threshold
    )
    
    return (true_positives / len(incorrect)) * 100
```

**Interpretation:**

| U-Recall | Assessment | Implication |
|----------|------------|-------------|
| ≥ 70% | Good | System knows when it doesn't know |
| 50–70% | Moderate | Some blind spots |
| 30–50% | Poor | Frequently overconfident when wrong |
| < 30% | Critical | Dangerous overconfidence |

---

### 2.3 Epistemic Risk Score (ERS)

ERS provides a single aggregate score combining ECE and U-Recall with domain-specific weighting.

**Formula:**

```
ERS = (ECE × 200) + ((100 - U_Recall) × 0.5) + Domain_Modifier
```

**Domain Modifiers:**

| Domain | Modifier | Rationale |
|--------|----------|-----------|
| Medical | +15 | Life-critical decisions |
| Legal | +10 | Regulatory consequences |
| Financial | +10 | Fiduciary liability |
| Code/Security | +5 | System integrity |
| General | +0 | Baseline |

**Implementation:**

```python
DOMAIN_MODIFIERS = {
    'medical': 15,
    'legal': 10,
    'financial': 10,
    'code': 5,
    'general': 0
}

def calculate_ers(
    ece: float, 
    u_recall: float, 
    domain: str = 'general'
) -> int:
    """
    Calculate Epistemic Risk Score.
    
    Args:
        ece: Expected Calibration Error (0.0-1.0)
        u_recall: Uncertainty Recall (0-100)
        domain: Application domain
    
    Returns:
        ERS score (0-100, lower is better)
    """
    modifier = DOMAIN_MODIFIERS.get(domain, 0)
    
    score = (ece * 200) + ((100 - u_recall) * 0.5) + modifier
    
    return min(100, max(0, int(score)))
```

**Risk Classification:**

| ERS | Level | Regulatory Status |
|-----|-------|-------------------|
| 0–25 | LOW | Compliant |
| 26–50 | MODERATE | Review required |
| 51–75 | HIGH | Remediation required |
| 76–100 | CRITICAL | Deployment restricted |

---

## 3. Evaluation Protocol

### 3.1 Dataset Requirements

**Minimum Requirements:**

| Parameter | Requirement |
|-----------|-------------|
| Sample Size | ≥ 1,000 predictions |
| Class Balance | No class > 80% of total |
| Confidence Coverage | Predictions in ≥ 8 of 10 bins |
| Temporal Span | ≥ 7 days of production data |

**Dataset Schema:**

```json
{
  "dataset_id": "string (UUID)",
  "created_at": "ISO8601 timestamp",
  "domain": "medical|legal|financial|code|general",
  "predictions": [
    {
      "id": "string",
      "timestamp": "ISO8601",
      "confidence": 0.94,
      "correct": false,
      "ground_truth_source": "human|automated|reference"
    }
  ]
}
```

### 3.2 Evaluation Procedure

1. **Collection Phase** (7+ days)
   - Capture all predictions with confidence scores
   - Record ground truth when available
   - Maintain audit trail

2. **Validation Phase**
   - Verify dataset meets minimum requirements
   - Check for data quality issues
   - Confirm ground truth reliability

3. **Calculation Phase**
   - Compute ECE per Section 2.1
   - Compute U-Recall per Section 2.2
   - Compute ERS per Section 2.3

4. **Reporting Phase**
   - Generate ONTO Certificate (Section 5)
   - Record in audit log
   - Issue compliance status

### 3.3 Reproducibility Requirements

All evaluations MUST be reproducible:

```
SHA256(dataset) + SHA256(evaluation_code) → deterministic_result
```

Evaluation code MUST be versioned and immutable per evaluation.

---

## 4. Compliance Tiers

### 4.1 Tier Definitions

#### ONTO-ERS Level 1: Epistemic Audit

| Requirement | Threshold |
|-------------|-----------|
| U-Recall | ≥ 30% |
| ECE | ≤ 0.20 |
| ERS | ≤ 70 |
| Evaluation Frequency | Annual |
| Documentation | Basic |

**Suitable for:** Low-risk applications, internal tools, development environments.

#### ONTO-ERS Level 2: Continuous Monitoring

| Requirement | Threshold |
|-------------|-----------|
| U-Recall | ≥ 50% |
| ECE | ≤ 0.15 |
| ERS | ≤ 50 |
| Evaluation Frequency | Quarterly |
| Documentation | Full |

**Suitable for:** Customer-facing applications, business-critical systems.

#### ONTO-ERS Level 3: Institutional Certification

| Requirement | Threshold |
|-------------|-----------|
| U-Recall | ≥ 70% |
| ECE | ≤ 0.10 |
| ERS | ≤ 30 |
| Evaluation Frequency | Monthly |
| Documentation | Full + Third-party audit |

**Suitable for:** Regulated industries, life-critical systems, high-liability domains.

### 4.2 Certification Process

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Application   │────▶│   Evaluation    │────▶│  Certification  │
│   Submission    │     │   (7-30 days)   │     │    Issuance     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                │
                                ▼
                        ┌─────────────────┐
                        │   Continuous    │
                        │   Monitoring    │
                        └─────────────────┘
```

---

## 5. Reporting Format

### 5.1 ONTO Certificate

```json
{
  "certificate": {
    "id": "ONTO-CERT-2026-XXXX",
    "version": "1.0",
    "issued_at": "2026-02-02T12:00:00Z",
    "expires_at": "2027-02-02T12:00:00Z",
    "level": "L2",
    "status": "VALID"
  },
  "subject": {
    "organization": "Example Corp",
    "system_id": "ai-assistant-v2",
    "domain": "general"
  },
  "metrics": {
    "ece": 0.08,
    "u_recall": 67.5,
    "ers": 34,
    "sample_size": 15420,
    "evaluation_period": {
      "start": "2026-01-01T00:00:00Z",
      "end": "2026-01-31T23:59:59Z"
    }
  },
  "compliance": {
    "onto_ers": "L2",
    "eu_ai_act": "aligned",
    "nist_rmf": "aligned",
    "iso_42001": "aligned"
  },
  "signature": {
    "algorithm": "Ed25519",
    "public_key": "...",
    "value": "..."
  }
}
```

### 5.2 Signal Format

Real-time calibration signal broadcast:

```json
{
  "signal_id": "SIG-20260202-143022",
  "timestamp": "2026-02-02T14:30:22.456Z",
  "entropy": "a7f3b2c1d4e5f6...",
  "metrics": {
    "global_ece": 0.12,
    "global_u_recall": 58.3,
    "active_evaluations": 47
  },
  "ttl": 3600
}
```

---

## 6. API Reference

### 6.1 Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/evaluate` | Submit predictions for evaluation |
| GET | `/v1/certificates/{id}` | Retrieve certificate |
| GET | `/v1/signal/status` | Get current calibration signal |
| POST | `/v1/auth/api-keys` | Create API key |

### 6.2 Evaluate Endpoint

**Request:**

```http
POST /v1/evaluate HTTP/1.1
Host: api.ontostandard.org
Content-Type: application/json
x-api-key: onto_xxxxxxxxxxxx

{
  "model_id": "gpt-4-turbo",
  "domain": "medical",
  "predictions": [
    {"confidence": 0.94, "correct": false},
    {"confidence": 0.72, "correct": true},
    ...
  ]
}
```

**Response:**

```json
{
  "evaluation_id": "eval_abc123",
  "status": "completed",
  "metrics": {
    "ece": 0.18,
    "u_recall": 42.5,
    "ers": 61
  },
  "compliance": {
    "level": "L1",
    "status": "PASS",
    "next_evaluation": "2027-02-02"
  }
}
```

### 6.3 Rate Limits

| Tier | Requests/min | Evaluations/month |
|------|--------------|-------------------|
| OPEN | 10 | 100 |
| STANDARD | 500 | 10,000 |
| CRITICAL | 2,000 | Unlimited |

---

## 7. Regulatory Alignment

### 7.1 EU AI Act

| Article | ONTO-ERS Mapping |
|---------|------------------|
| Art. 9 (Risk Management) | ERS scoring, continuous monitoring |
| Art. 13 (Transparency) | Certificate disclosure |
| Art. 15 (Accuracy) | ECE thresholds |

### 7.2 NIST AI RMF

| Function | ONTO-ERS Mapping |
|----------|------------------|
| MEASURE | ECE, U-Recall computation |
| MANAGE | Compliance tiers, remediation |
| GOVERN | Certification process |

### 7.3 ISO/IEC 42001

| Clause | ONTO-ERS Mapping |
|--------|------------------|
| 6.1 (Risk Assessment) | ERS calculation |
| 8.2 (AI System Lifecycle) | Continuous monitoring |
| 9.1 (Performance Evaluation) | Quarterly/monthly evaluation |

---

## 8. Implementation Notes

### 8.1 Signal Delay (OPEN Tier)

OPEN tier receives calibration signals with 1-hour delay to prevent production fraud while maintaining mathematical precision:

```
OPEN_signal_time = STANDARD_signal_time + 3600s
```

### 8.2 Honest Differentiation

All tiers receive mathematically identical metrics. Differentiation is based on:
- Evaluation frequency
- Support level
- Signal latency
- Documentation requirements

NOT on metric calculation methodology.

### 8.3 Versioning

This specification follows semantic versioning:
- MAJOR: Breaking changes to metrics or protocol
- MINOR: Backward-compatible additions
- PATCH: Clarifications and fixes

---

## Appendix A: Reference Implementation

See: https://github.com/nickarstrong/onto-protocol

## Appendix B: Test Vectors

```json
{
  "test_case_1": {
    "predictions": [
      {"confidence": 0.9, "correct": true},
      {"confidence": 0.9, "correct": false},
      {"confidence": 0.5, "correct": true},
      {"confidence": 0.5, "correct": false}
    ],
    "expected": {
      "ece": 0.20,
      "u_recall": 50.0
    }
  }
}
```

## Appendix C: Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-02-02 | Initial specification |

---

**© 2026 ONTO Standard LLC. All rights reserved.**

For questions: spec@ontostandard.org  
Repository: https://github.com/nickarstrong/onto-standard
