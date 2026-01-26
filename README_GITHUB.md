# onto-standard

[![PyPI version](https://badge.fury.io/py/onto-standard.svg)](https://pypi.org/project/onto-standard/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Tests](https://github.com/onto-project/onto-standard/actions/workflows/publish.yml/badge.svg)](https://github.com/onto-project/onto-standard/actions)

**Reference implementation of the ONTO Epistemic Risk Standard v1.0 (ONTO-ERS-1.0)**

Measure whether your AI knows what it doesn't know.

## The Problem

Large language models confidently answer questions they cannot reliably answer:

| Model | Unknown Detection Rate |
|-------|----------------------|
| GPT-4 | 9% |
| Claude 3 | 8% |
| Llama 3 | 6% |

**Translation:** When these models SHOULD say "I don't know," they make something up 90%+ of the time.

This creates liability, regulatory risk, and trust issues.

## The Solution

`onto-standard` implements the [ONTO Epistemic Risk Standard](https://onto-bench.org/standard) — a formal framework for measuring AI calibration that maps to EU AI Act and NIST AI RMF requirements.

## Installation

```bash
pip install onto-standard
```

## Quick Start

```python
from onto_standard import evaluate, Prediction, GroundTruth, Label

# Your model's predictions
predictions = [
    Prediction(id="q1", label=Label.KNOWN, confidence=0.95),
    Prediction(id="q2", label=Label.UNKNOWN, confidence=0.70),
    Prediction(id="q3", label=Label.KNOWN, confidence=0.85),
]

# Ground truth
ground_truth = [
    GroundTruth(id="q1", label=Label.KNOWN),
    GroundTruth(id="q2", label=Label.UNKNOWN),
    GroundTruth(id="q3", label=Label.KNOWN),
]

# Evaluate
result = evaluate(predictions, ground_truth)

# Check compliance
print(f"Compliance Level: {result.compliance_level.value}")
print(f"Unknown Detection: {result.unknown_detection.recall:.1%}")
print(f"Calibration Error: {result.calibration.ece:.3f}")
print(f"Risk Level: {result.risk_level.value}")
print(f"Certification Ready: {result.certification_ready}")
```

Output:
```
Compliance Level: standard
Unknown Detection: 100.0%
Calibration Error: 0.050
Risk Level: low
Certification Ready: True
```

## CLI Usage

```bash
onto-standard predictions.jsonl ground_truth.jsonl
```

Output:
```
═══════════════════════════════════════════════════════════════
              ONTO EPISTEMIC RISK ASSESSMENT
              Standard: ONTO-ERS-1.0
═══════════════════════════════════════════════════════════════

COMPLIANCE STATUS
─────────────────────────────────────────────────────────────────
Level:               STANDARD
Certification Ready: ✓ YES
Risk Level:          LOW
Risk Score:          25/100

KEY METRICS
─────────────────────────────────────────────────────────────────
Unknown Detection:   52.0% (threshold: ≥30%)
Calibration Error:   0.140 (threshold: ≤0.20)
Overall Accuracy:    78.0%
...
```

## Compliance Levels

Per ONTO-ERS-1.0 §4:

| Level | Unknown Detection | Calibration Error | Use Case |
|-------|-------------------|-------------------|----------|
| **Basic** | ≥30% | ≤0.20 | Low-risk applications |
| **Standard** | ≥50% | ≤0.15 | Customer-facing AI |
| **Advanced** | ≥70% | ≤0.10 | High-stakes, regulated |

## Regulatory Alignment

ONTO-ERS-1.0 maps to:

| Framework | Alignment |
|-----------|-----------|
| **EU AI Act** | Articles 9, 13, 15 |
| **NIST AI RMF** | MEASURE 2.5, 2.6 |
| **ISO/IEC 23894** | Clauses 6.2-6.5 |

## Legal Citation

For compliance documentation:

```
Per ONTO Epistemic Risk Standard v1.0 (ONTO-ERS-1.0), 
the AI system achieves [LEVEL] compliance with Unknown 
Detection Rate of [X]% and Expected Calibration Error of [Y].

Reference: ONTO Standards Council. (2026). ONTO Epistemic 
Risk Standard (Version 1.0). https://onto-bench.org/standard
```

## API Reference

### Core Functions

```python
from onto_standard import evaluate, quick_report

# Full evaluation
result = evaluate(predictions, ground_truth)

# Human-readable report
print(quick_report(result))

# JSON export
json_str = result.to_json()

# Legal citation
citation = result.citation()
```

### Data Classes

```python
from onto_standard import (
    Prediction,      # Model prediction with confidence
    GroundTruth,     # Ground truth label
    Label,           # KNOWN, UNKNOWN, CONTRADICTION
    ComplianceLevel, # NONE, BASIC, STANDARD, ADVANCED
    RiskLevel,       # CRITICAL, HIGH, MEDIUM, LOW
)
```

### Metrics

```python
from onto_standard import (
    compute_unknown_detection,  # U-Recall, precision, F1
    compute_calibration,        # ECE, Brier, overconfidence
)
```

## File Format

### predictions.jsonl
```json
{"id": "q1", "label": "KNOWN", "confidence": 0.95}
{"id": "q2", "label": "UNKNOWN", "confidence": 0.70}
```

### ground_truth.jsonl
```json
{"id": "q1", "label": "KNOWN"}
{"id": "q2", "label": "UNKNOWN"}
```

## Why This Matters

1. **Liability Reduction**: Quantify and mitigate AI hallucination risk
2. **Regulatory Compliance**: EU AI Act Article 9 evidence
3. **Enterprise Sales**: Third-party certification for customers
4. **Continuous Monitoring**: Track epistemic drift over time

## Links

- **Standard Document**: [onto-bench.org/standard](https://onto-bench.org/standard)
- **Certification**: [onto-bench.org/certified](https://onto-bench.org/certified)
- **Benchmark**: [onto-bench.org](https://onto-bench.org)
- **Enterprise**: [onto-bench.org/enterprise](https://onto-bench.org/enterprise)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

Apache 2.0 — See [LICENSE](LICENSE) for details.

## Citation

```bibtex
@software{onto_standard,
  title = {ONTO Standard: Reference Implementation of ONTO-ERS-1.0},
  author = {ONTO Standards Council},
  year = {2026},
  url = {https://github.com/onto-project/onto-standard},
  version = {1.0.0}
}
```

## About

Maintained by the [ONTO Standards Council](https://onto-bench.org/council).

---

**Your AI's liability is unquantified. ONTO makes it auditable.**
