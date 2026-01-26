# arXiv Submission Checklist

## Pre-Submission (Day -1)

### Paper Quality
- [x] Abstract states contribution clearly (no overclaims)
- [x] Claims sanitized (claims_limitations.tex)
- [x] Limitations section complete
- [x] Ethics statement included
- [x] Reproducibility statement included
- [x] All tables auto-generated from data
- [x] All figures publication-ready (PDF)

### Technical Verification
- [x] Dataset hash locked: `cb6978046e249ab6...`
- [x] Seed documented: 42
- [x] Baseline outputs stored
- [x] Metrics reproducible
- [x] Code runs without errors

### Files Ready
- [x] main.tex (renamed from onto_arxiv.tex)
- [x] claims_limitations.tex
- [x] appendix_reproducibility.tex
- [x] tables/*.tex
- [x] figures/*.pdf

---

## Submission Day (Day 0)

### Step 1: Final Compilation
```bash
cd paper
pdflatex main.tex
pdflatex main.tex  # Second pass for refs
```

### Step 2: Verify PDF
- [ ] All figures render correctly
- [ ] All tables render correctly
- [ ] No broken references
- [ ] Page count acceptable
- [ ] Abstract fits on first page

### Step 3: arXiv Account
- [ ] Log in to arxiv.org
- [ ] Verify email confirmed

### Step 4: Submission Form
- [ ] Title: "ONTO: Epistemically-Calibrated Reasoning for Large Language Models"
- [ ] Authors: [Your name]
- [ ] Abstract: Copy from paper (≤1920 chars)
- [ ] Primary category: **cs.CL**
- [ ] Cross-list: cs.AI, cs.LG
- [ ] Comments: "10 pages, 4 figures, 3 tables. Code and data: [GitHub URL]"
- [ ] License: CC-BY 4.0

### Step 5: Upload Files
- [ ] Upload .tex files
- [ ] Upload figures/
- [ ] Upload tables/
- [ ] Process submission
- [ ] Verify PDF preview

### Step 6: Submit
- [ ] Click Submit
- [ ] Save submission ID
- [ ] Note expected announcement date (~24-48 hours)

---

## Post-Submission (Day 1-2)

### Verify Publication
- [ ] Check arXiv for paper
- [ ] Verify PDF renders correctly
- [ ] Test all links

### Announce
- [ ] Twitter thread ready
- [ ] HN post ready
- [ ] Reddit post ready
- [ ] Email collaborators

### GitHub
- [ ] Make repo public
- [ ] Add arXiv badge to README
- [ ] Update citation info

---

## Common arXiv Issues

| Issue | Fix |
|-------|-----|
| "TeX compilation failed" | Remove problematic packages, simplify |
| "File too large" | Compress PDFs, remove unused files |
| "Invalid category" | cs.CL is correct for NLP/LLM work |
| "Duplicate submission" | Contact arXiv support |

---

## File Structure for Upload

```
upload/
├── main.tex                 # Main paper
├── claims_limitations.tex   # Sanitized claims
├── appendix_reproducibility.tex
├── figures/
│   ├── calibration_curve.pdf
│   ├── metric_comparison.pdf
│   ├── label_distribution.pdf
│   └── confusion_onto.pdf
└── tables/
    ├── results_table.tex
    └── dataset_table.tex
```

---

## Quick Reference

- **arXiv URL**: https://arxiv.org/submit
- **Processing time**: 24-48 hours
- **Announcement**: Daily at 20:00 UTC
- **Revision**: Can update within 24h of submission
- **DOI**: Available after announcement

---

## Emergency Contacts

- arXiv support: help@arxiv.org
- GitHub issues: [repo]/issues
