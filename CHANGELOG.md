# Changelog

All notable changes to the `onto-standard` package will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-27

### Added

- Initial release implementing ONTO Epistemic Risk Standard v1.0 (ONTO-ERS-1.0)
- Core evaluation function `evaluate()` for computing compliance
- Unknown detection metrics per ONTO-ERS §3.1.1
  - Unknown Recall (U-Recall)
  - Unknown Precision
  - Unknown F1
- Calibration metrics per ONTO-ERS §3.1.2
  - Expected Calibration Error (ECE)
  - Brier Score
  - Overconfidence Rate
- Compliance level determination per ONTO-ERS §4
  - Level 1: Basic (U-Recall ≥30%, ECE ≤0.20)
  - Level 2: Standard (U-Recall ≥50%, ECE ≤0.15)
  - Level 3: Advanced (U-Recall ≥70%, ECE ≤0.10)
- Risk level assessment (Critical/High/Medium/Low)
- Regulatory alignment indicators
  - EU AI Act compliance
  - NIST AI RMF alignment
- Output formats
  - Dictionary export (`to_dict()`)
  - JSON export (`to_json()`)
  - Legal citation generation (`citation()`)
  - Human-readable report (`quick_report()`)
- CLI tool: `onto-standard <predictions.jsonl> <ground_truth.jsonl>`
- JSONL file evaluation helper (`evaluate_from_jsonl()`)

### Standard Compliance

This release fully implements:
- ONTO-ERS-1.0 §3 (Requirements)
- ONTO-ERS-1.0 §4 (Compliance Levels)
- ONTO-ERS-1.0 §6 (Certification)
- ONTO-ERS-1.0 §10 (Regulatory Traceability)

### Documentation

- Full API documentation at https://onto-bench.org/standard/api
- Standard document at https://onto-bench.org/standard/v1.0

---

## Future Releases

### [1.1.0] - Planned

- Batch evaluation for multiple models
- HTML report generation
- Integration with ONTO-Bench leaderboard

### [2.0.0] - Planned

- ONTO-ERS-2.0 support (when released)
- Domain-specific compliance levels
- Extended calibration metrics

---

[1.0.0]: https://github.com/onto-project/onto-standard/releases/tag/v1.0.0
