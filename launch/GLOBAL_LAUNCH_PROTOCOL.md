# ONTO Global Launch Protocol

## Complete Institutional Launch Execution

---

## PHASE 0: PRE-LAUNCH VERIFICATION (Day -1)

### Code Ready
```bash
# Tests pass
pytest tests/ -v  # 28/28 ✓

# Package builds
python -m build   # ✓

# Local install works
pip install dist/onto_standard-1.0.0-py3-none-any.whl
python -c "from onto_standard import evaluate; print('OK')"
```

### Documents Ready
- [ ] ONTO_STANDARD_v1.0.md finalized
- [ ] README_GITHUB.md polished
- [ ] CHANGELOG.md complete
- [ ] All launch posts drafted

---

## PHASE 1: INFRASTRUCTURE (Day 1, Morning)

### 1.1 Domain Setup (if not done)
```
onto-bench.org configured
SSL active
DNS propagated
```

### 1.2 GPG Key
```bash
# Generate if needed
gpg --full-generate-key

# Export public key
gpg --armor --export standards@onto-bench.org > ONTO_SIGNING_KEY.asc

# Note fingerprint
gpg --fingerprint standards@onto-bench.org
```

### 1.3 Git Signing
```bash
git config --global user.signingkey [KEY_ID]
git config --global commit.gpgsign true
```

---

## PHASE 2: PUBLISH ARTIFACTS (Day 1, 08:00-09:00)

### 2.1 GitHub Repository

```bash
# Initialize
cd onto-bench
git init
git add .
git commit -S -m "Initial release: onto-standard v1.0.0"

# Push
git remote add origin https://github.com/onto-project/onto-standard.git
git push -u origin main

# Create signed tag
git tag -s v1.0.0 -m "ONTO Standard v1.0.0"
git push origin v1.0.0
```

### 2.2 PyPI Upload

```bash
# Upload
twine upload dist/*

# Verify
pip install onto-standard
python -c "from onto_standard import __version__; print(__version__)"
# Expected: 1.0.0
```

### 2.3 GitHub Release

1. Go to github.com/onto-project/onto-standard/releases
2. Click "Create new release"
3. Select tag: v1.0.0
4. Title: "ONTO Standard v1.0.0 - Initial Release"
5. Upload assets:
   - onto_standard-1.0.0-py3-none-any.whl
   - onto_standard-1.0.0.tar.gz
   - CHECKSUMS.txt
6. Publish

---

## PHASE 3: PERMANENT ARCHIVE (Day 1, 09:00-10:00)

### 3.1 Zenodo Upload

1. Go to zenodo.org/deposit/new
2. Upload:
   - ONTO-ERS-1.0.pdf (generate from markdown)
   - ONTO-ERS-1.0.pdf.asc (signature)
3. Fill metadata (see ZENODO_DOI_PIPELINE.md)
4. Publish
5. Note DOI: 10.5281/zenodo.XXXXXXX

### 3.2 Update Documentation with DOI

```bash
# Add DOI badge to README
echo "[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)]..." >> README.md
git add . && git commit -S -m "Add Zenodo DOI" && git push
```

### 3.3 Internet Archive

```bash
# Archive main pages
curl "https://web.archive.org/save/https://onto-bench.org/standard/v1"
curl "https://web.archive.org/save/https://pypi.org/project/onto-standard/"
curl "https://web.archive.org/save/https://github.com/onto-project/onto-standard"
```

---

## PHASE 4: WEBSITE LIVE (Day 1, 10:00-11:00)

### Deploy Pages

```
onto-bench.org/standard/v1          ← Standard document
onto-bench.org/reference            ← pip install guide
onto-bench.org/standard/v1/integrity ← Hashes and verification
onto-bench.org/council              ← Standards Council
onto-bench.org/gpg-key              ← Public key download
```

### Verify All Links

```bash
# Check all URLs respond
curl -I https://onto-bench.org/standard/v1
curl -I https://onto-bench.org/reference
curl -I https://pypi.org/project/onto-standard/
```

---

## PHASE 5: DEV ANNOUNCEMENT (Day 1, 11:00-12:00)

### 5.1 Hacker News (11:00 AM ET)

**Title:**
```
Show HN: onto-standard – Measure if your LLM knows what it doesn't know
```

**Body:** (See HN_LAUNCH.md)

### 5.2 Twitter Thread (11:30 AM ET)

Post 10-tweet thread (See TWITTER_LAUNCH.md)

### 5.3 LinkedIn (12:00 PM ET)

Post announcement with:
- Problem statement
- pip install command
- Link to standard

---

## PHASE 6: COMMUNITY OUTREACH (Day 2)

### Reddit
- r/MachineLearning (morning)
- r/LocalLLaMA (afternoon)

### Developer Communities
- Python Discord
- MLOps Slack
- Hugging Face forums

### Follow-up
- Respond to all HN comments
- Engage Twitter replies
- Answer Reddit questions

---

## PHASE 7: ENTERPRISE SIGNAL (Day 3-5)

### Update Cold Emails

Add to email templates:
```
PS: Test your own models: pip install onto-standard
```

### Send First Batch

50 emails from OUTBOUND_50.md:
- Batch 1: Legal AI (10)
- Batch 2: Healthcare (10)
- Batch 3: Enterprise AI (15)
- Batch 4: Fintech (10)
- Batch 5: Infrastructure (5)

---

## PHASE 8: METRICS (Day 7)

### Check Numbers

```bash
# PyPI
pypistats recent onto-standard

# GitHub (API)
curl -s https://api.github.com/repos/onto-project/onto-standard | jq '.stargazers_count'
```

### Week 1 Targets

| Metric | Target | Result |
|--------|--------|--------|
| PyPI downloads | 500 | |
| GitHub stars | 100 | |
| HN points | 50 | |
| Enterprise inquiries | 2 | |

---

## CRITICAL PATH (DEPENDENCIES)

```
GPG Key
   ↓
Signed Commit
   ↓
GitHub Push
   ↓
PyPI Upload ──→ Verify pip install
   ↓
GitHub Release
   ↓
Zenodo DOI
   ↓
Website with DOI
   ↓
HN/Twitter Launch
   ↓
Community Engagement
   ↓
Enterprise Outreach
```

---

## ROLLBACK PROCEDURES

### If PyPI Upload Fails

```bash
# Check error message
# Common issues: twine version, token, metadata

# Retry with verbose
twine upload dist/* --verbose
```

### If Critical Bug Found

```bash
# Yank PyPI version
# Go to pypi.org/manage/project/onto-standard/releases/
# Yank v1.0.0

# Fix, bump to v1.0.1
# Edit pyproject.toml
python -m build
twine upload dist/onto_standard-1.0.1*
```

### If HN Post Fails to Gain Traction

- Post at different time next day
- Try different title angle
- Cross-post to Twitter for initial momentum

---

## SUCCESS CRITERIA

### Launch Day (Day 1)
- [ ] PyPI package live
- [ ] GitHub repo public
- [ ] Zenodo DOI assigned
- [ ] HN post submitted
- [ ] Twitter thread posted

### Week 1
- [ ] 500+ PyPI downloads
- [ ] 100+ GitHub stars
- [ ] 50+ HN points
- [ ] 3+ blog mentions
- [ ] 2+ enterprise inquiries

### Month 1
- [ ] 5,000+ PyPI downloads
- [ ] 500+ GitHub stars
- [ ] First enterprise pilot
- [ ] First academic citation

---

## EMERGENCY CONTACTS

If something breaks:
- PyPI support: admin@pypi.org
- GitHub support: support.github.com
- Zenodo support: info@zenodo.org
- Domain registrar support: [your registrar]

---

## FINAL CHECKLIST

### Pre-Launch (Day -1)
- [ ] All code tested
- [ ] All docs reviewed
- [ ] GPG key ready
- [ ] Launch posts drafted
- [ ] Calendar blocked for Day 1

### Launch Day (Day 1)
- [ ] Infrastructure (08:00-09:00)
- [ ] Publish artifacts (09:00-10:00)
- [ ] Permanent archive (10:00-11:00)
- [ ] Website live (10:30)
- [ ] HN post (11:00)
- [ ] Twitter thread (11:30)
- [ ] LinkedIn (12:00)
- [ ] Monitor & respond (all day)

### Post-Launch (Day 2-7)
- [ ] Reddit posts
- [ ] Dev community engagement
- [ ] Cold emails sent
- [ ] Metrics tracked
- [ ] Week 2 planned

---

**Execute in order. Verify each step. Ship it.**

🚀
