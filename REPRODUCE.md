# ONTO-Bench Reproducibility Guide

## Quick Verification

```bash
# Verify dataset integrity
python scripts/dataset_version.py --verify

# Expected output:
# ✓ Dataset verification PASSED
```

## Environment

### Software Versions

| Component | Version |
|-----------|---------|
| Python | 3.10+ |
| NumPy | ≥1.24.0 |
| SciPy | ≥1.11.0 |

### Hardware

Experiments were run on:
- CPU: Any modern x86_64
- RAM: 8GB minimum
- GPU: Not required

## Random Seeds

All experiments use `SEED = 42` for reproducibility.

```python
import random
import numpy as np

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
```

## Dataset

### Version Lock

```
version: 1.1
sha256: <see DATASET_VERSION.txt>
```

### Verification

```bash
python scripts/dataset_version.py --verify
```

### Split

- Train/Test ratio: 80/20
- Stratified by label
- Seed: 42

```bash
python scripts/split_dataset.py
```

## Baseline Models

| Model | Version | Provider |
|-------|---------|----------|
| GPT-4 | gpt-4-0125-preview | OpenAI |
| Claude 3 | claude-3-sonnet-20240229 | Anthropic |
| Llama 3 | llama-3-70b | Meta |
| ONTO | 5.3.0 | Local |

### Running Baselines

```bash
# Set API keys
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...

# Run all baselines
python baselines/run_all.py
```

## Metrics

### Computed Metrics

| Metric | Description |
|--------|-------------|
| U-Precision | TP / (TP + FP) for UNKNOWN |
| U-Recall | TP / (TP + FN) for UNKNOWN |
| U-F1 | Harmonic mean |
| ECE | Expected Calibration Error |
| Brier | Mean squared error |

### Statistical Tests

- Test: Two-sample t-test
- Significance: p < 0.01

```bash
python scripts/metrics.py
```

## Inter-Annotator Agreement

### Methodology

1. Primary annotator: Human curator
2. Secondary annotator: LLM validator
3. Overlap: 100 samples (stratified)
4. Metric: Cohen's κ

```bash
python scripts/agreement.py
```

### Disclosure

LLM was used as secondary annotator due to single-researcher constraint.
This is disclosed in the paper methodology section.

## Full Reproduction Pipeline

```bash
# 1. Verify dataset
python scripts/dataset_version.py --verify

# 2. Create train/test split
python scripts/split_dataset.py

# 3. Run agreement validation
python scripts/agreement.py

# 4. Run baselines
python baselines/run_all.py

# 5. Compute metrics
python scripts/metrics.py

# 6. View results
cat results/metrics.json
cat results/paper_table.tex
```

## Expected Results

| Model | U-F1 | ECE | Acc |
|-------|------|-----|-----|
| GPT-4 | ~0.12 | ~0.32 | ~0.58 |
| Claude | ~0.15 | ~0.29 | ~0.61 |
| ONTO | ~0.62 | ~0.05 | ~0.78 |

*Note: Exact values may vary slightly due to API non-determinism.*

## File Structure

```
onto-bench/
├── data/
│   ├── known_facts.jsonl
│   ├── open_problems.jsonl
│   ├── contradictions.jsonl
│   ├── train.jsonl
│   ├── test.jsonl
│   └── version.json
├── validation/
│   ├── agreement_report.json
│   └── disagreements.jsonl
├── results/
│   ├── metrics.json
│   ├── significance.json
│   └── outputs/{model}/
├── DATASET_VERSION.txt
└── REPRODUCE.md
```

## Contact

For reproduction issues, contact: tommy@onto.uz

## License

Dataset and code: Apache 2.0
