# ONTO-Bench Governance Policy

## Purpose

This document establishes governance rules for ONTO-Bench to ensure benchmark integrity, reproducibility, and fair evaluation as adoption scales.

---

## 1. Submission Rules

### 1.1 Required Artifacts

Every leaderboard submission MUST include:

| Artifact | Required | Format |
|----------|----------|--------|
| Model name | ✓ | String |
| Organization | ✓ | String |
| Model version | ✓ | Semantic version or commit hash |
| Predictions file | ✓ | JSONL (schema below) |
| System prompt | Recommended | Text file |
| Inference code | Recommended | GitHub link |
| Hardware specs | Recommended | JSON |

### 1.2 Prediction Schema

```json
{
  "id": "sample_001",
  "label": "KNOWN|UNKNOWN|CONTRADICTION",
  "confidence": 0.0-1.0,
  "reasoning": "optional explanation"
}
```

### 1.3 Prohibited Practices

- ❌ Training on ONTO-Bench test set
- ❌ Manual label lookup during inference
- ❌ Submitting without reproducibility artifacts
- ❌ Gaming confidence scores without calibration

---

## 2. Verification Process

### 2.1 Automatic Verification

All submissions undergo:
1. Schema validation
2. Coverage check (all test samples)
3. Confidence distribution analysis
4. Duplicate detection

### 2.2 Manual Verification (Top 10)

Top-ranked submissions additionally require:
1. Code review
2. Reproduction attempt
3. Methodology disclosure
4. Organization verification

### 2.3 Verification Status

| Status | Meaning |
|--------|---------|
| ✓ Verified | Manually verified, reproducible |
| ⚠ Pending | Awaiting verification |
| ✗ Rejected | Failed verification |

---

## 3. Versioning Policy

### 3.1 Dataset Versions

| Version | Status | Hash |
|---------|--------|------|
| v1.6 | Current | `cb6978046e249ab6...` |
| v1.5 | Deprecated | `...` |

### 3.2 Deprecation Rules

- New versions announced 30 days before activation
- Deprecated versions remain accessible for 1 year
- Submissions on deprecated versions marked accordingly

### 3.3 Breaking Changes

Breaking changes (label schema, metric definitions) trigger:
1. Major version bump
2. 60-day migration period
3. Parallel leaderboards during transition

---

## 4. Metric Definitions

### 4.1 Primary Metrics

| Metric | Definition | Direction |
|--------|------------|-----------|
| U-F1 | F1 for UNKNOWN class | Higher ↑ |
| U-Recall | TP / (TP + FN) for UNKNOWN | Higher ↑ |
| U-Precision | TP / (TP + FP) for UNKNOWN | Higher ↑ |
| ECE | Expected Calibration Error | Lower ↓ |
| Brier | Brier Score | Lower ↓ |

### 4.2 Secondary Metrics (v1.7+)

| Metric | Definition | Direction |
|--------|------------|-----------|
| AUROC-U | Area under ROC for UNKNOWN detection | Higher ↑ |
| Selective Risk | Risk at 80% coverage | Lower ↓ |
| Abstention Rate | Fraction of abstentions | Report only |

### 4.3 Metric Freeze

Metric definitions are frozen per major version. No retroactive recalculation.

---

## 5. Leaderboard Rules

### 5.1 Update Schedule

- Submissions processed: Daily
- Leaderboard refresh: Weekly (Mondays 00:00 UTC)
- Major updates: Quarterly

### 5.2 Submission Limits

- 3 submissions per organization per day
- 10 submissions per organization per week
- No limit on total submissions

### 5.3 Ranking Ties

Ties resolved by:
1. U-F1 (primary)
2. ECE (secondary)
3. Submission timestamp (tertiary)

---

## 6. Dispute Resolution

### 6.1 Filing Disputes

Disputes filed via GitHub Issues with:
- Submission ID
- Specific concern
- Evidence

### 6.2 Resolution Process

1. Initial review: 7 days
2. Investigation: 14 days
3. Final decision: 7 days

### 6.3 Appeals

One appeal per dispute. Final decision binding.

---

## 7. Ethics & Integrity

### 7.1 Data Ethics

- No personally identifiable information in dataset
- Questions sourced from public scientific literature
- Synthetic generation disclosed

### 7.2 Benchmark Limitations

ONTO-Bench measures epistemic calibration on curated scientific questions. Results:
- Do NOT reflect full system capabilities
- Do NOT guarantee real-world performance
- Should NOT be sole deployment criterion

### 7.3 Responsible Disclosure

Security vulnerabilities in evaluation code: security@onto-bench.org

---

## 8. Governance Structure

### 8.1 Maintainers

| Role | Responsibility |
|------|----------------|
| Lead Maintainer | Final decisions, disputes |
| Technical Maintainer | Code, infrastructure |
| Data Maintainer | Dataset updates, validation |

### 8.2 Advisory Board (Future)

When citations > 50 or submissions > 100:
- Form advisory board
- Include external researchers
- Annual governance review

---

## 9. License

- Code: Apache 2.0
- Dataset: Apache 2.0
- Governance document: CC-BY 4.0

---

## 10. Contact

- Issues: GitHub Issues
- Email: governance@onto-bench.org
- Security: security@onto-bench.org

---

*Last updated: January 2026*
*Version: 1.0*
