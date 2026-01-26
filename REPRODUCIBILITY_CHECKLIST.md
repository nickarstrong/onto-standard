# ONTO-Bench Reproducibility Checklist

## NeurIPS 2024 Paper Checklist (Adapted)

This checklist follows the NeurIPS reproducibility guidelines.

---

### 1. Claims

| Item | Status | Notes |
|------|--------|-------|
| Main claims clearly stated | ✓ | Abstract + Section 1 |
| Claims supported by evidence | ✓ | Table 1, Section 5 |
| Claims appropriately scoped | ✓ | "on our benchmark" language |

---

### 2. Method

| Item | Status | Notes |
|------|--------|-------|
| Algorithm described | ✓ | Section 3 |
| Pseudocode provided | ✓ | Algorithm 1 |
| Assumptions stated | ✓ | Section 3.1 |

---

### 3. Experimental Setup

| Item | Status | Notes |
|------|--------|-------|
| Dataset statistics | ✓ | Table 2, Appendix A |
| Train/test split | ✓ | 80/20 stratified |
| Evaluation metrics defined | ✓ | Section 4.2 |
| Baseline descriptions | ✓ | Section 4.1 |
| Hyperparameters | ✓ | N/A (no training) |
| Random seeds | ✓ | Seed = 42 |

---

### 4. Results

| Item | Status | Notes |
|------|--------|-------|
| Central findings in main text | ✓ | Table 1 |
| Error bars / confidence intervals | ⚠ | Single run (API non-determinism) |
| Statistical significance | ✓ | t-tests in Appendix |
| Negative results reported | ✓ | Lower overall accuracy |

---

### 5. Reproducibility

| Item | Status | Location |
|------|--------|----------|
| Code availability | ✓ | GitHub (to be released) |
| Dataset availability | ✓ | Included in repository |
| Dataset version hash | ✓ | `cb6978046e249ab6...` |
| Random seed documented | ✓ | 42 |
| Model versions documented | ✓ | Appendix A.2 |
| Compute requirements | ✓ | Appendix A.5 |

---

### 6. Ethics

| Item | Status | Notes |
|------|--------|-------|
| Broader impact discussed | ✓ | Section 6 |
| Limitations acknowledged | ✓ | Section 7 |
| Dataset bias disclosed | ✓ | Section 7 |
| No personally identifiable information | ✓ | Scientific questions only |

---

### 7. Assets

| Asset | License | Location |
|-------|---------|----------|
| Code | Apache 2.0 | `/scripts/`, `/baselines/` |
| Dataset | Apache 2.0 | `/data/` |
| Paper | CC-BY 4.0 | `/paper/` |

---

## Verification Commands

```bash
# 1. Verify dataset integrity
python scripts/dataset_version.py --verify
# Expected: "Dataset verification PASSED"

# 2. Verify reproducible split
python scripts/split_dataset.py
# Check: train=213, test=55

# 3. Run baselines
python baselines/run_all.py

# 4. Compute metrics
python scripts/metrics.py
# Check: onto U-F1 ≈ 0.58

# 5. Generate paper assets
python scripts/generate_tables.py
python scripts/generate_plots.py
```

---

## Key Artifacts

| Artifact | Hash/Version | Verification |
|----------|--------------|--------------|
| Dataset | `cb6978046e249ab6...` | `dataset_version.py --verify` |
| Code | v1.4 | Git tag |
| Paper | arXiv v1 | DOI pending |

---

## Contact for Reproducibility Issues

Please open a GitHub issue or contact: tommy@onto.uz
