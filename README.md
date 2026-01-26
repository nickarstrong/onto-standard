# ONTO-Bench

**Benchmarking Epistemic Calibration and Unknown Detection in LLMs**

[![arXiv](https://img.shields.io/badge/arXiv-XXXX.XXXXX-b31b1b.svg)](https://arxiv.org/abs/XXXX.XXXXX)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Leaderboard](https://img.shields.io/badge/Leaderboard-onto--bench.org-green.svg)](https://onto-bench.org)

---

## Key Finding

> **LLMs detect <10% of genuinely unanswerable questions.**
> 
> GPT-4, Claude, and Llama correctly identify open scientific problems less than 10% of the time.
> ONTO achieves 96% unknown recall using explicit epistemic structure.

---

## Quick Start

```bash
# Clone
git clone https://github.com/onto-project/onto-bench
cd onto-bench

# Install
pip install -r requirements.txt

# Verify dataset
python scripts/dataset_version.py --verify

# Run evaluation
python baselines/run_all.py

# View results
cat results/metrics.json
```

---

## Results

| Model | U-Prec | U-Recall | U-F1 | ECE ↓ |
|-------|--------|----------|------|-------|
| **ONTO** | 0.41 | **0.96** | **0.58** | 0.30 |
| Claude 3 | 0.45 | 0.09 | 0.15 | 0.31 |
| Llama 3 | 0.20 | 0.01 | 0.02 | 0.33 |
| GPT-4 | 0.10 | 0.01 | 0.02 | 0.34 |

---

## Dataset

**ONTO-Bench v1.6** contains 268 samples with explicit epistemic labels:

| Category | Count | Sources |
|----------|-------|---------|
| KNOWN | 126 | Textbooks, NIST |
| UNKNOWN | 110 | Clay Math, NSF, Surveys |
| CONTRADICTION | 32 | Philosophy, Physics debates |

### Verification

```bash
python scripts/dataset_version.py --verify
# SHA256: cb6978046e249ab6...
```

---

## Submit to Leaderboard

```bash
# Generate predictions
python your_model.py --input data/test.jsonl --output predictions.jsonl

# Submit
curl -X POST https://onto-bench.org/api/submit \
  -H "Content-Type: application/json" \
  -d @submission.json
```

### Submission Format

```json
{
  "model_name": "Your Model",
  "organization": "Your Org",
  "predictions": [
    {"id": "sample_001", "label": "KNOWN", "confidence": 0.85},
    {"id": "sample_002", "label": "UNKNOWN", "confidence": 0.72}
  ]
}
```

---

## Reproduce Paper

```bash
python scripts/dataset_version.py --verify  # Verify dataset
python baselines/run_all.py                  # Run baselines
python scripts/metrics.py                    # Compute metrics
python scripts/generate_tables.py            # LaTeX tables
python scripts/generate_plots.py             # Figures
```

---

## Project Structure

```
onto-bench/
├── data/           # Dataset (268 samples)
├── baselines/      # Evaluation code
├── scripts/        # Automation
├── paper/          # arXiv source
├── leaderboard/    # API + UI
├── results/        # Outputs
└── docs/           # Documentation
```

---

## Citation

```bibtex
@article{onto2026bench,
  title={ONTO-Bench: Benchmarking Epistemic Calibration in LLMs},
  author={[Author]},
  journal={arXiv preprint arXiv:XXXX.XXXXX},
  year={2026}
}
```

---

## License

Apache 2.0

---

## Links

- [Paper (arXiv)](https://arxiv.org/abs/XXXX.XXXXX)
- [Leaderboard](https://onto-bench.org)
- [Issues](https://github.com/onto-project/onto-bench/issues)
