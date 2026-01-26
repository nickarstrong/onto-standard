# ONTO Release Protocol

## PyPI + GitHub Release Execution Guide

---

## PRE-FLIGHT CHECKLIST

```bash
# Verify everything is ready
cd onto-bench

# 1. Tests pass
python -m pytest tests/ -v
# Expected: 28 passed

# 2. Package builds
python -m build
# Expected: dist/onto_standard-1.0.0-py3-none-any.whl

# 3. Local install works
pip install dist/onto_standard-1.0.0-py3-none-any.whl
python -c "from onto_standard import evaluate; print('OK')"

# 4. CLI works
onto-standard --help
```

---

## STEP 1: CREATE GITHUB REPO

### 1.1 Create Repository

```
Repository name: onto-standard
Description: Reference implementation of ONTO Epistemic Risk Standard v1.0
Visibility: Public
License: Apache 2.0
```

### 1.2 Push Code

```bash
cd onto-bench
git init
git add .
git commit -m "Initial release: onto-standard v1.0.0"
git branch -M main
git remote add origin https://github.com/onto-project/onto-standard.git
git push -u origin main
```

### 1.3 Create GitHub Release

```
Tag: v1.0.0
Title: ONTO Standard v1.0.0 - Initial Release
Description: [See RELEASE_NOTES below]
Assets: Upload dist/*.whl and dist/*.tar.gz
```

---

## STEP 2: PYPI PUBLISH

### 2.1 Create PyPI Account

1. Go to https://pypi.org/account/register/
2. Verify email
3. Enable 2FA (required for new packages)

### 2.2 Create API Token

1. Go to https://pypi.org/manage/account/token/
2. Create token with scope: "Entire account" (first time)
3. Save token securely

### 2.3 Configure twine

```bash
# Create ~/.pypirc
cat > ~/.pypirc << 'EOF'
[pypi]
username = __token__
password = pypi-YOUR-TOKEN-HERE
EOF

chmod 600 ~/.pypirc
```

### 2.4 Upload to PyPI

```bash
# Install tools
pip install twine

# Upload
twine upload dist/*

# Verify
pip install onto-standard
python -c "from onto_standard import __version__; print(__version__)"
# Expected: 1.0.0
```

### 2.5 Verify PyPI Page

Check: https://pypi.org/project/onto-standard/

Should show:
- Package name
- Description
- Installation instructions
- Links to documentation

---

## STEP 3: POST-PUBLISH VERIFICATION

```bash
# Fresh environment test
python -m venv test_env
source test_env/bin/activate
pip install onto-standard
python -c "
from onto_standard import evaluate, Prediction, GroundTruth, Label
print('Import: OK')
p = [Prediction('1', Label.KNOWN, 0.9)]
g = [GroundTruth('1', Label.KNOWN)]
r = evaluate(p, g)
print(f'Evaluate: OK, compliance={r.compliance_level}')
"
deactivate
rm -rf test_env
```

---

## RELEASE NOTES (v1.0.0)

```markdown
# onto-standard v1.0.0

Reference implementation of **ONTO Epistemic Risk Standard v1.0** (ONTO-ERS-1.0).

## Installation

```bash
pip install onto-standard
```

## What's Included

### Metrics (ONTO-ERS §3.1)
- Unknown Detection (U-Recall, Precision, F1)
- Calibration Error (ECE, Brier Score)
- Risk Score (0-100)

### Compliance Levels (ONTO-ERS §4)
- Basic: U-Recall ≥30%, ECE ≤0.20
- Standard: U-Recall ≥50%, ECE ≤0.15
- Advanced: U-Recall ≥70%, ECE ≤0.10

### Regulatory Alignment (ONTO-ERS §10)
- EU AI Act mapping
- NIST AI RMF alignment
- ISO/IEC 23894 compatibility

## Quick Start

```python
from onto_standard import evaluate, Prediction, GroundTruth, Label

predictions = [Prediction("q1", Label.KNOWN, 0.9)]
ground_truth = [GroundTruth("q1", Label.KNOWN)]

result = evaluate(predictions, ground_truth)
print(result.compliance_level)  # ComplianceLevel.BASIC
print(result.citation())        # Legal citation string
```

## CLI

```bash
onto-standard predictions.jsonl ground_truth.jsonl
```

## Links

- Standard: https://onto-bench.org/standard
- Documentation: https://onto-bench.org/standard/api
- Certification: https://onto-bench.org/certified

## License

Apache 2.0
```

---

## GITHUB SECRETS (for CI/CD)

Add to repository settings → Secrets:

```
PYPI_API_TOKEN: pypi-YOUR-TOKEN-HERE
```

This enables automatic publishing on new releases.

---

## VERIFICATION CHECKLIST

After publish, verify:

- [ ] `pip install onto-standard` works
- [ ] PyPI page shows correct metadata
- [ ] GitHub release has assets
- [ ] README renders correctly on PyPI
- [ ] CLI command `onto-standard` works
- [ ] Import `from onto_standard import evaluate` works

---

## ROLLBACK PROTOCOL

If something goes wrong:

```bash
# PyPI allows yanking (hiding) releases
# Go to: https://pypi.org/manage/project/onto-standard/releases/
# Click on version → Yank this release

# Then fix and re-release with new version
# (Cannot reuse same version number)
```

---

*ONTO Release Protocol v1.0*
*Execute in order. Verify each step.*
