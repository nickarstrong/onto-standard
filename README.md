# ONTO Standard

**Epistemic Risk Standard for AI Systems**

[![Website](https://img.shields.io/badge/Web-ontostandard.org-2ec27e)](https://ontostandard.org)
[![Research](https://img.shields.io/badge/Research-CS--2026--001-blue)](https://github.com/nickarstrong/onto-research)
[![PyPI](https://img.shields.io/pypi/v/onto-standard.svg)](https://pypi.org/project/onto-standard/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

---

## Overview

ONTO defines metrics and methodology for measuring **epistemic risk** in AI systems — the gap between what an AI claims to know and what it actually knows. Validated on 11 production models (10 ranked, 1 excluded for conflict of interest), 100 questions, 5 domains. Result: 10× composite improvement without retraining or fine-tuning.

**Before ONTO** (any model):
> "Intermittent fasting has moderate benefits for metabolic health."

**After ONTO** (same model):
> "Intermittent fasting shows mass reduction of 3-8% over 3-24 weeks (Varady et al., 2021, n=560). Confidence: 0.72 for metabolic markers, 0.45 for long-term cardiovascular outcomes. Gap: no RCTs beyond 12 months in populations over 65."

---

## Key Metrics

| Metric | Description |
|--------|-------------|
| **REP** | Response Epistemic Profile — distribution across EM1-EM5 levels |
| **EpCE** | Epistemic Calibration Error — deviation between expressed confidence and grounding |
| **DLA** | Dual-Layer Agreement — consistency between linguistic and statistical analysis |
| **U-Recall** | Unknown Detection Rate |
| **ECE** | Expected Calibration Error |

## Compliance Levels

| Level | U-Recall | ECE | Use Case |
|-------|----------|-----|----------|
| Basic | ≥ 30% | ≤ 0.20 | Internal tools, prototypes |
| Standard | ≥ 50% | ≤ 0.15 | Customer-facing AI |
| Advanced | ≥ 70% | ≤ 0.10 | Regulated industries, high-stakes |

---

## Quick Start

```bash
pip install onto-standard
```

```python
from onto_standard import evaluate, Prediction, GroundTruth, Label

predictions = [
    Prediction(id="q1", label=Label.KNOWN, confidence=0.9),
    Prediction(id="q2", label=Label.UNKNOWN, confidence=0.7),
]

ground_truth = [
    GroundTruth(id="q1", label=Label.KNOWN),
    GroundTruth(id="q2", label=Label.UNKNOWN),
]

result = evaluate(predictions, ground_truth)

print(f"Compliance Level: {result.compliance_level}")
print(f"U-Recall: {result.unknown_detection.recall:.1%}")
print(f"ECE: {result.calibration.ece:.3f}")
print(f"Risk Score: {result.risk_score}/100")
```

---

## Results (CS-2026-001)

| Metric | Without ONTO | With ONTO | Change |
|--------|-------------|-----------|--------|
| Composite score | 0.53 | 5.38 | 10× |
| Source citations | 0 per response | 3+ per response | New capability |
| Confidence calibration | Absent | Numerical (0.35-0.88) | New capability |
| Output variance (SD) | 0.58 | 0.11 | 5.4× reduction |
| Cross-domain transfer | 0/5 | 4/5 | 80% |

11 models tested (GPT 5.2, Claude Sonnet 4.5, Gemini, DeepSeek R1, Grok 4.2, Mistral Large, Copilot, Kimi K2.5, Qwen3-Max, Alice, Perplexity). 10 ranked. Zero baseline models provide numeric confidence levels.

Full data: [onto-research](https://github.com/nickarstrong/onto-research)

---

## Architecture

Dual-engine: Python scoring engine (993 lines, regex, deterministic) + Rust onto_core (entropy analysis, Merkle tree proofs, metrics computation, PyO3 bindings).

```
GOLD corpus (private) → Server-side injection → AI model system prompt
Client receives the EFFECT, not the document.
```

Scoring is fully open. GOLD corpus is proprietary.

---

## Regulatory Alignment

ONTO metrics support compliance with:

- **EU AI Act** — Articles 9, 13, 15, 43 (Risk management, transparency, accuracy, conformity)
- **NIST AI RMF** — MEASURE function (deterministic metrics)
- **ISO/IEC 42001** — AI management system audit artifacts

---

## Pricing

| Tier | Price | Requests | GOLD |
|------|-------|----------|------|
| Open | Free | 10/day | Core |
| Standard | $30,000/yr | 1,000/day | Extended |
| AI Provider | $250,000/yr | Unlimited | Full Corpus |
| White-Label | $500,000/yr | Unlimited | Full, no attribution |

---

## Links

- **Website:** [ontostandard.org](https://ontostandard.org)
- **Portal:** [ontostandard.org/app](https://ontostandard.org/app/)
- **Documentation:** [ontostandard.org/docs](https://ontostandard.org/docs/)
- **Research Data:** [github.com/nickarstrong/onto-research](https://github.com/nickarstrong/onto-research)
- **Paper:** [ontostandard.org/paper](https://ontostandard.org/paper/)
- **PyPI:** [onto-standard](https://pypi.org/project/onto-standard/)

---

## Citation

```
ONTO Standard, CS-2026-001. "Deterministic Measurement of Epistemic Quality
in Production LLM Systems." February 2026. https://ontostandard.org
```

---

## License

Apache 2.0 — See [LICENSE](LICENSE)

---

© 2026 ONTO Standards Council
