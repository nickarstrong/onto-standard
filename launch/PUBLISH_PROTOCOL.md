# ONTO PyPI & GitHub Publish Protocol

## Complete Execution Checklist

---

## PHASE 1: PRE-PUBLISH VERIFICATION (30 min)

### 1.1 Version Check
```bash
# Verify version is 1.0.0
grep version pyproject.toml
# Should show: version = "1.0.0"
```

### 1.2 Run Tests
```bash
pip install pytest
pytest tests/ -v
# All 28 tests should pass
```

### 1.3 Build Package
```bash
pip install build twine
python -m build
ls dist/
# Should show:
#   onto_standard-1.0.0-py3-none-any.whl
#   onto_standard-1.0.0.tar.gz
```

### 1.4 Test Install Locally
```bash
pip install dist/onto_standard-1.0.0-py3-none-any.whl
python -c "from onto_standard import evaluate; print('OK')"
onto-standard --help
```

---

## PHASE 2: GITHUB SETUP (20 min)

### 2.1 Create Repository
1. Go to github.com/new
2. Name: `onto-standard`
3. Description: "Reference implementation of ONTO Epistemic Risk Standard v1.0"
4. Public
5. Add LICENSE (Apache 2.0)
6. Don't add README (we have one)

### 2.2 Initial Push
```bash
cd onto-bench
git init
git add .
git commit -m "Initial release: onto-standard v1.0.0

Reference implementation of ONTO Epistemic Risk Standard v1.0 (ONTO-ERS-1.0)

Features:
- Unknown detection metrics (U-Recall, precision, F1)
- Calibration metrics (ECE, Brier, overconfidence)
- Compliance level determination (Basic/Standard/Advanced)
- Risk assessment
- CLI tool
- Regulatory mapping (EU AI Act, NIST AI RMF)"

git branch -M main
git remote add origin https://github.com/onto-project/onto-standard.git
git push -u origin main
```

### 2.3 Add Secrets for CI/CD
1. Go to repo Settings → Secrets → Actions
2. Add: `PYPI_API_TOKEN` (from PyPI, see below)

### 2.4 Create Release
1. Go to Releases → "Create new release"
2. Tag: `v1.0.0`
3. Title: "v1.0.0 - Initial Release"
4. Description:
```
## ONTO Standard v1.0.0

Reference implementation of ONTO Epistemic Risk Standard v1.0 (ONTO-ERS-1.0)

### Installation
pip install onto-standard

### Features
- Unknown detection metrics per ONTO-ERS §3.1.1
- Calibration metrics per ONTO-ERS §3.1.2
- Three compliance levels (Basic/Standard/Advanced)
- CLI tool for evaluation
- JSON/dict export
- Legal citation generation

### Links
- Standard: https://onto-bench.org/standard
- Documentation: https://onto-bench.org/standard/api
```

---

## PHASE 3: PYPI PUBLISH (15 min)

### 3.1 Create PyPI Account
1. Go to https://pypi.org/account/register/
2. Verify email
3. Enable 2FA (required for publishing)

### 3.2 Create API Token
1. Go to https://pypi.org/manage/account/token/
2. Token name: "onto-standard-publish"
3. Scope: "Entire account" (first time) or project-specific after
4. Copy token (starts with `pypi-`)

### 3.3 Upload to PyPI
```bash
# First time: manual upload
twine upload dist/*

# Enter credentials:
# Username: __token__
# Password: pypi-YOUR_API_TOKEN
```

### 3.4 Verify
```bash
# Wait 1-2 minutes, then:
pip install onto-standard
python -c "from onto_standard import evaluate; print('PyPI install works!')"
```

### 3.5 Check PyPI Page
- Go to https://pypi.org/project/onto-standard/
- Verify description renders correctly
- Check classifiers and links

---

## PHASE 4: DOCUMENTATION (20 min)

### 4.1 Update onto-bench.org/standard
Add to standard page:
```html
<h2>Reference Implementation</h2>
<pre>pip install onto-standard</pre>
<p>GitHub: <a href="https://github.com/onto-project/onto-standard">onto-project/onto-standard</a></p>
<p>PyPI: <a href="https://pypi.org/project/onto-standard/">onto-standard</a></p>
```

### 4.2 Create API Documentation Page
At onto-bench.org/standard/api:
- List all functions
- Show examples
- Link to GitHub for full docs

---

## PHASE 5: DEV ADOPTION CAMPAIGN (Day 1-3)

### 5.1 Hacker News (Day 1, 8-10am ET)
1. Post using HN_LAUNCH.md
2. Monitor for first hour
3. Reply to all comments

### 5.2 Twitter/X (Day 1, after HN)
1. Post thread from TWITTER_LAUNCH.md
2. Space tweets 2-3 min apart
3. Pin thread

### 5.3 Reddit r/MachineLearning (Day 2)
1. Post using REDDIT_ML_LAUNCH.md
2. Use [P] flair
3. Respond to technical questions

### 5.4 LinkedIn (Day 2)
```
Excited to release onto-standard v1.0.0 — the reference 
implementation of the ONTO Epistemic Risk Standard.

It measures whether AI systems recognize the boundaries 
of their knowledge. pip install onto-standard

Most frontier LLMs confidently answer questions they 
can't answer 90%+ of the time. This matters for liability, 
compliance, and trust.

Standard: onto-bench.org/standard
GitHub: [link]

#AI #MachineLearning #AISafety #Compliance
```

### 5.5 Dev Communities (Day 3)
- Lobste.rs (if you have invite)
- Python Discord
- ML Discord servers
- Hugging Face community

---

## PHASE 6: TRACKING (Ongoing)

### Metrics to Monitor

| Metric | Source | Target (Week 1) |
|--------|--------|-----------------|
| PyPI downloads | pypistats.org | 500+ |
| GitHub stars | GitHub | 100+ |
| HN points | HN | 50+ |
| Twitter impressions | Analytics | 10K+ |

### Daily Check
```bash
# PyPI downloads
pip install pypistats
pypistats overall onto-standard

# GitHub
curl -s https://api.github.com/repos/onto-project/onto-standard | jq '.stargazers_count'
```

---

## PHASE 7: FOLLOW-UP (Week 2+)

### 7.1 Respond to Issues
- Triage within 24h
- Fix bugs within 48h
- Thank contributors

### 7.2 Write Blog Post
- "Why we built ONTO"
- Technical deep-dive
- Post on Medium/Dev.to

### 7.3 Academic Outreach
- Email researchers in calibration/uncertainty
- Offer collaboration
- Ask for citation

### 7.4 Enterprise Follow-up
- Cold emails reference pip package
- "You can try it yourself: pip install onto-standard"

---

## ROLLBACK PLAN (If Critical Bug)

```bash
# Yank bad version
twine yank onto-standard 1.0.0

# Fix, bump version
# Edit pyproject.toml: version = "1.0.1"

# Rebuild and publish
python -m build
twine upload dist/onto_standard-1.0.1*
```

---

## SUCCESS CRITERIA

### Week 1
- [ ] PyPI package live
- [ ] GitHub repo public
- [ ] 500+ PyPI downloads
- [ ] 100+ GitHub stars
- [ ] 10+ HN comments

### Month 1
- [ ] 5,000+ PyPI downloads
- [ ] 500+ GitHub stars
- [ ] 3+ blog posts/mentions
- [ ] 1+ academic citation

### Month 3
- [ ] 20,000+ PyPI downloads
- [ ] First enterprise customer used pip package
- [ ] Contributor community forming

---

## IMMEDIATE NEXT STEP

```bash
# Right now:
twine upload dist/*

# Then:
# Verify at pypi.org/project/onto-standard/
```

---

**Ship it.**
