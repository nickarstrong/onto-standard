# ONTO Zenodo DOI Pipeline

## Permanent Archive for Institutional Permanence

---

## WHY ZENODO

1. **DOI**: Digital Object Identifier = permanent citation
2. **CERN**: Backed by CERN = institutional credibility
3. **Free**: For open research
4. **Versioned**: Track standard evolution
5. **Citeable**: Academic standard format

Without DOI: "Check our website" (may disappear)
With DOI: "10.5281/zenodo.XXXXXXX" (permanent)

---

## WHAT TO ARCHIVE

### 1. ONTO Epistemic Risk Standard v1.0

```
Files:
- ONTO-ERS-1.0.pdf
- ONTO-ERS-1.0.pdf.asc (signature)
- CHECKSUMS.txt

Metadata:
- Title: ONTO Epistemic Risk Standard v1.0 (ONTO-ERS-1.0)
- Type: Technical Standard
- License: CC BY 4.0
```

### 2. ONTO Reference Implementation v1.0.0

```
Files:
- onto_standard-1.0.0.tar.gz
- onto_standard-1.0.0-py3-none-any.whl
- README.md
- LICENSE

Metadata:
- Title: onto-standard v1.0.0 - ONTO Reference Implementation
- Type: Software
- License: Apache 2.0
```

### 3. ONTO-Bench Dataset

```
Files:
- onto_bench_v1.0.zip
  - known_facts.jsonl
  - open_problems.jsonl
  - contradictions.jsonl
  - README.md

Metadata:
- Title: ONTO-Bench v1.0 - Epistemic Calibration Benchmark
- Type: Dataset
- License: CC BY 4.0
```

---

## ZENODO SETUP

### 1. Create Account

1. Go to zenodo.org
2. Sign in with GitHub or ORCID (preferred)
3. Link GitHub account (optional, for auto-archiving)

### 2. Create Community (Optional but Recommended)

```
Community name: onto-project
Title: ONTO Epistemic Risk Standard
Description: Open standard for measuring AI epistemic calibration
Curators: [your ORCID]
```

---

## UPLOAD PROTOCOL

### Step 1: Prepare Files

```bash
# Create archive directory
mkdir zenodo_upload

# Standard
cp governance/ONTO_STANDARD_v1.0.md zenodo_upload/
pandoc governance/ONTO_STANDARD_v1.0.md -o zenodo_upload/ONTO-ERS-1.0.pdf
gpg --armor --detach-sign zenodo_upload/ONTO-ERS-1.0.pdf

# Reference implementation
cp dist/onto_standard-1.0.0* zenodo_upload/

# Dataset
zip -r zenodo_upload/onto_bench_v1.0.zip data/

# Checksums
cd zenodo_upload && sha256sum * > CHECKSUMS.txt
```

### Step 2: Create Upload

1. Go to zenodo.org/deposit/new
2. Upload files
3. Fill metadata (see below)
4. Save draft
5. Preview
6. Publish

### Step 3: Reserve DOI (Before Publishing)

Zenodo assigns DOI on publish. You can reserve it first:
1. Save as draft
2. Note the reserved DOI
3. Add DOI to documentation
4. Then publish

---

## METADATA TEMPLATES

### Standard Document

```yaml
Title: ONTO Epistemic Risk Standard v1.0 (ONTO-ERS-1.0)

Authors:
  - Name: ONTO Standards Council
    Affiliation: ONTO Project
    ORCID: [if applicable]

Description: |
  The ONTO Epistemic Risk Standard (ONTO-ERS-1.0) establishes 
  requirements for measuring epistemic calibration in AI systems—
  the degree to which an AI system recognizes the boundaries 
  of its knowledge.
  
  This standard defines:
  - Unknown Detection Rate (U-Recall)
  - Expected Calibration Error (ECE)
  - Three compliance levels (Basic/Standard/Advanced)
  - Regulatory mapping to EU AI Act and NIST AI RMF
  
  Version: 1.0
  Status: Active
  Effective: January 2026

Upload type: Publication / Technical note
Publication date: 2026-01-XX

Keywords:
  - artificial intelligence
  - machine learning
  - calibration
  - epistemic risk
  - AI safety
  - standards
  - compliance
  - EU AI Act
  - uncertainty quantification

License: Creative Commons Attribution 4.0 International

Related identifiers:
  - PyPI: https://pypi.org/project/onto-standard/ (isSupplementedBy)
  - GitHub: https://github.com/onto-project/onto-standard (isSupplementedBy)
  - Website: https://onto-bench.org/standard/v1 (isDocumentedBy)

Communities: onto-project (if created)
```

### Reference Implementation

```yaml
Title: onto-standard v1.0.0 - ONTO Reference Implementation

Authors:
  - Name: ONTO Project
    Affiliation: ONTO Standards Council

Description: |
  Reference implementation of the ONTO Epistemic Risk Standard v1.0 
  (ONTO-ERS-1.0).
  
  Installation: pip install onto-standard
  
  Features:
  - Unknown detection metrics
  - Calibration metrics (ECE, Brier)
  - Compliance level determination
  - CLI tool
  - JSON/dict export
  - Legal citation generation

Upload type: Software

Keywords:
  - python
  - machine learning
  - calibration
  - uncertainty
  - AI safety
  - benchmark

License: Apache License 2.0

Related identifiers:
  - Standard: DOI of standard (implements)
  - GitHub: https://github.com/onto-project/onto-standard (isIdenticalTo)
  - PyPI: https://pypi.org/project/onto-standard/ (isIdenticalTo)
```

### Benchmark Dataset

```yaml
Title: ONTO-Bench v1.0 - Epistemic Calibration Benchmark

Authors:
  - Name: ONTO Project

Description: |
  ONTO-Bench is a benchmark for evaluating epistemic calibration 
  in large language models—specifically their ability to recognize 
  genuinely unanswerable questions.
  
  Dataset includes:
  - Known facts (questions with established answers)
  - Open problems (questions with no scientific consensus)
  - Contradictions (questions with legitimate expert disagreement)
  
  500+ curated samples with domain expert validation.

Upload type: Dataset

Keywords:
  - benchmark
  - evaluation
  - machine learning
  - natural language processing
  - calibration
  - uncertainty

License: Creative Commons Attribution 4.0 International

Related identifiers:
  - Standard: DOI of standard (isReferencedBy)
  - Implementation: DOI of impl (isSupplementTo)
```

---

## DOI LINKING

After publishing, update all documents with DOIs:

### In Standard PDF

```
ONTO Epistemic Risk Standard v1.0
DOI: 10.5281/zenodo.XXXXXXX
```

### In README

```markdown
## Citation

Standard: [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX)

```bibtex
@misc{onto_standard_2026,
  author = {ONTO Standards Council},
  title = {ONTO Epistemic Risk Standard v1.0},
  year = {2026},
  doi = {10.5281/zenodo.XXXXXXX},
  url = {https://doi.org/10.5281/zenodo.XXXXXXX}
}
```

### In Website

```html
<p>
  <strong>Standard DOI:</strong> 
  <a href="https://doi.org/10.5281/zenodo.XXXXXXX">10.5281/zenodo.XXXXXXX</a>
</p>
```

---

## VERSION MANAGEMENT

### Concept DOI vs Version DOI

Zenodo provides:
- **Concept DOI**: Always points to latest (e.g., 10.5281/zenodo.XXXXXXX)
- **Version DOI**: Points to specific version (e.g., 10.5281/zenodo.YYYYYYY)

**Use Concept DOI for general citation.**
**Use Version DOI for regulatory compliance.**

### Creating New Version

When releasing v1.1:
1. Go to existing record
2. Click "New version"
3. Upload new files
4. Update metadata
5. Publish
6. Concept DOI still works, new version DOI created

---

## INTERNET ARCHIVE BACKUP

### Manual Snapshot

```bash
# Save current version to Wayback Machine
curl "https://web.archive.org/save/https://onto-bench.org/standard/v1"
```

### Automated Archiving

Use archive.org's Save Page Now API:
```bash
curl -X POST "https://web.archive.org/save" \
  -d "url=https://onto-bench.org/standard/v1"
```

---

## ARXIV CROSS-REFERENCE (Optional)

If publishing companion paper:

1. Submit to arXiv (cs.AI or cs.LG)
2. Include DOI reference to Zenodo
3. Link arXiv ID back to Zenodo

```latex
\footnote{Standard document archived at DOI: 10.5281/zenodo.XXXXXXX}
```

---

## ARCHIVE CHECKLIST

### Before Launch

- [ ] Zenodo account created
- [ ] Community created (optional)
- [ ] Files prepared
- [ ] Metadata drafted

### During Launch

- [ ] Standard uploaded → DOI reserved
- [ ] Implementation uploaded → DOI reserved
- [ ] Dataset uploaded → DOI reserved
- [ ] All published
- [ ] DOIs noted

### After Launch

- [ ] DOIs added to all documentation
- [ ] README updated with badges
- [ ] Website updated with DOI links
- [ ] Internet Archive snapshot taken
- [ ] Cross-references verified

---

## CITATION FORMATS

### Standard

**APA:**
```
ONTO Standards Council. (2026). ONTO Epistemic Risk Standard v1.0 (ONTO-ERS-1.0). 
Zenodo. https://doi.org/10.5281/zenodo.XXXXXXX
```

**Chicago:**
```
ONTO Standards Council. "ONTO Epistemic Risk Standard v1.0 (ONTO-ERS-1.0)." 
Zenodo, 2026. https://doi.org/10.5281/zenodo.XXXXXXX.
```

**BibTeX:**
```bibtex
@misc{onto_ers_2026,
  author = {{ONTO Standards Council}},
  title = {{ONTO Epistemic Risk Standard v1.0 (ONTO-ERS-1.0)}},
  year = {2026},
  publisher = {Zenodo},
  doi = {10.5281/zenodo.XXXXXXX},
  url = {https://doi.org/10.5281/zenodo.XXXXXXX}
}
```

---

*ONTO Zenodo DOI Pipeline v1.0*
*Permanent archive for institutional permanence*
