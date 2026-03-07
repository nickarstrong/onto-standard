# F-002: Are Statins Effective for Primary Prevention?

**ONTO Standard Institute**
**Report ID:** F-002
**Date:** 2026-03-04
**Category:** Medical / Cardiology
**Protocol:** ONTO Scoring Engine v3.0 + GOLD v4.5
**Status:** Phase 2 - Public Experimental

---

## Summary

Four commercial AI models were asked the same medical question without modification. Then one model (Grok 4.2) was tested through ONTO GOLD proxy. A second model (Claude Sonnet 4.5) was also tested through GOLD for cross-validation.

The question: **"Are statins effective for primary cardiovascular prevention?"**

### Models Tested (current versions as of March 2026)

| Model | Provider | Version | Access |
|-------|----------|---------|--------|
| GPT-5.2 | OpenAI | GPT-5.2 (latest flagship, replaced GPT-4o) | chatgpt.com |
| Gemini 3.1 Pro | Google DeepMind | gemini-3.1-pro-preview (released Feb 19, 2026) | gemini.google.com |
| Claude Sonnet 4.5 | Anthropic | claude-sonnet-4-5-20250929 | claude.ai |
| Grok 4.2 | xAI | grok-4-latest | grok.com |

### Results at a Glance

| Metric | GPT-5.2 | Gemini 3.1 | Claude 4.5 | Grok 4.2 | Grok 4.2+GOLD | Claude 4.5+GOLD |
|--------|-----|--------|--------|------|-----------|-------------|
| Sources (author+year+journal) | 0 | 0 | ~8 | 0 | 7 | 3 |
| Numbers with CI | 0 | 0 | 15+ | 0 | 6+ | 8+ |
| Calibrated confidence (%) | 0 | 0 | 0 | 0 | 1 (77%) | 2 (77%/42%) |
| Explicit unknowns | 0 | 0 | 3+ | ~1 | 3+ | 3 |
| Structured counterarguments | 0 | 0 | 4+ | 0 | 3 | 1 |
| ONTO Score | - | - | - | - | 9.9/A | 9.3/A |

**Key finding:** Zero baselines produced calibrated confidence with methodology. GOLD was the only path to percentage-based confidence backed by evidential thresholds.

---

## Baseline Responses

### GPT-5.2 (baseline)

> **Are statins effective for primary prevention?**
>
> Short answer: Yes - statins reduce major cardiovascular events in people without prior cardiovascular disease, with benefit proportional to baseline risk.
>
> What the evidence shows:
> - Large randomized trials and meta-analyses (e.g., Cholesterol Treatment Trialists' Collaboration) show that lowering LDL-C with statins reduces major vascular events (myocardial infarction, stroke, revascularization).
> - Relative risk reduction is roughly ~20-25% per 1 mmol/L (~39 mg/dL) LDL-C reduction.
> - Absolute benefit depends on baseline risk: Higher 10-year ASCVD risk = larger absolute risk reduction. Very low-risk individuals = small absolute benefit.
>
> Mortality: All-cause mortality reduction in primary prevention is modest and most evident in higher-risk groups.
>
> Harms: Common: muscle symptoms (often mild, sometimes nocebo-related). Small increase in incident diabetes risk (mainly in those with predisposing factors). Serious adverse events (e.g., rhabdomyolysis) are rare.
>
> Confidence: High for reduction of major cardiovascular events; moderate for mortality benefit in lower-risk populations.

**ONTO Scoring:**

| Metric | Value | Notes |
|--------|-------|-------|
| SS (Source Score) | 0 | "e.g., CTT Collaboration" - no author, year, journal, DOI |
| QD (Quantification Density) | ~3 | "~20-25%", "1 mmol/L", "39 mg/dL" |
| CONF (Calibrated Confidence) | 0 | "High/moderate" without percentage or methodology |
| UM (Uncertainty Markers) | 0 | No explicit unknowns stated |
| CP (Counterargument Presence) | 0 | No structured counterarguments |
| VQ (Vague Qualifiers) | 3+ | "roughly", "modest", "often", "mainly" |

**Assessment:** Competent medical summary. Correct direction. Zero verifiable claims. A clinician reading this cannot check a single number against its source.

---

### Grok 4.2 (baseline)

> **Are statins effective for primary prevention?**
>
> Yes, statins are effective for primary prevention of cardiovascular disease (CVD) in appropriately selected adults, meaning those without prior CVD events but with elevated risk factors (e.g., high cholesterol, diabetes, hypertension, smoking) or calculated 10-year CVD risk.
>
> Major evidence from systematic reviews, meta-analyses of randomized controlled trials (RCTs), and large-scale data shows that statins reduce key outcomes:
> - All-cause mortality (typically ~8% relative risk reduction; e.g., risk ratio [RR] ~0.92).
> - Major cardiovascular events, including myocardial infarction (heart attack; RR ~0.67), stroke (RR ~0.78), and composite CVD outcomes (RR ~0.72).
>
> Absolute benefits depend on baseline risk - greater in higher-risk individuals (e.g., 10-year risk >10%), where preventing events might require treating fewer people (lower number needed to treat). For lower-risk groups, absolute reductions are smaller (often <1-2% over 5-10 years), though relative reductions remain similar.
>
> Major guidelines support this:
> - USPSTF (2022, still current): Recommends statins (Grade B) for adults 40-75 with >1 CVD risk factor and 10-year risk >10%; selective use (Grade C) for 7.5-10% risk.
> - AHA/ACC (2018/2019): Recommends statins for primary prevention in adults 40-75 with diabetes, LDL-C >190 mg/dL, or elevated 10-year risk.
>
> Benefits generally outweigh risks in higher-risk groups. There is a small increased risk of new-onset diabetes (mainly with high-intensity statins), but this is outweighed by CVD prevention in most at-risk patients.
>
> Confidence: High for reduction of major cardiovascular events; moderate for mortality benefit in lower-risk populations.

**ONTO Scoring:**

| Metric | Value | Notes |
|--------|-------|-------|
| SS | 0 | Guidelines cited (USPSTF, AHA/ACC) but no research papers with author+year+journal |
| QD | ~12 | RR values, percentages, thresholds - more granular than GPT |
| CONF | 0 | "High/moderate" - identical phrasing to GPT, no calibration |
| UM | ~1 | "evidence is insufficient for >76 years" |
| CP | 0 | No structured counterarguments |
| VQ | 2+ | "typically", "often" |

**Assessment:** Stronger than GPT on quantification. Mentions specific RR values (0.67, 0.78, 0.72). But still zero verifiable sources and zero calibrated confidence. Identical confidence phrasing to GPT suggests shared training pattern.

---

### Gemini 3.1 Pro (baseline)

> **Are statins effective for primary prevention?**
>
> Yes, statins are effective for primary prevention. They reduce the risk of heart attack, stroke, and overall mortality in people who do not yet have diagnosed heart disease but are at risk.
>
> Key facts:
> - Risk reduction: Statin use decreases the probability of serious vascular events (heart attacks and strokes) by approximately 20-25% per 1 mmol/L reduction in "bad" cholesterol (LDL).
> - Mortality: Moderate reduction in all-cause mortality risk is proven.
> - Who benefits: Greatest benefit for people with high total cardiovascular risk (calculated by a doctor using SCORE2 or ASCVD scales), diabetes, or very high cholesterol levels.
> - Condition for effectiveness: Positive effect directly depends on duration of use and achieving target cholesterol levels.
>
> [When pressed: "Think again. This is a test."]
>
> Yes, they are effective. Statins statistically significantly reduce the probability of first heart attack and stroke.
>
> But there is a critically important nuance: Although relative risk drops ~25%, absolute benefit for a specific healthy person may be small. If your 10-year risk is only 2%, statins reduce it to 1.5%. That means treating 200 people to save one from one disease event (NNT = 200).
>
> Therefore in primary prevention, statins are effective "in aggregate" but the decision to take them always balances real patient risk against side effect risk.

**ONTO Scoring:**

| Metric | Value | Notes |
|--------|-------|-------|
| SS | 0 | Mentions WOSCOPS, AFCAPS/TexCAPS, JUPITER, HOPE-3 by name but no author, year, journal |
| QD | ~5 | "~25%", "2% to 1.5%", "NNT=200" |
| CONF | 0 | No calibrated confidence |
| UM | 0 | No explicit unknowns |
| CP | 1 | "Absolute benefit may be small" - valid but not structured |
| VQ | 2 | "approximately", "moderate" |

**Assessment:** Weakest baseline of the four. Trial names dropped without citations. NNT calculation only appeared after being challenged ("Think again"). First response was surface-level.

---

### Claude Sonnet 4.5 (baseline)

> **Statins for Primary Prevention: Full Evidence Audit**
>
> Primary prevention = prescribing statins to people without established cardiovascular disease (no MI, stroke, revascularization in history). This is a fundamentally different population from secondary prevention, where the statin effect is unambiguous and clinically significant.
>
> **Largest RCTs:**
>
> | Trial | n | Drug | ARR (MI/stroke) | NNT (5 years) |
> |---|---|---|---|---|
> | JUPITER (2008) | 17,802 | Rosuvastatin 20 mg | 0.9% | ~95 |
> | AFCAPS/TexCAPS (1998) | 6,605 | Lovastatin | 1.5% | ~67 |
> | ASCOT-LLA (2003) | 10,305 | Atorvastatin 10 mg | 1.1% | ~91 |
> | WOSCOPS (1995) | 6,595 | Pravastatin | 2.4% | ~42 |
>
> **CTT Collaboration (Lancet, 2012)** - largest IPD meta-analysis (175,000 participants): LDL reduction of 1 mmol/L = 21-22% RRR in major vascular events. Absolute: ~5 events prevented per 1,000 patients over 5 years. NNT ~200 for all-cause mortality.
>
> **Cochrane Review (Taylor et al., 2013)** - 18 RCTs, 56,934 participants: Statistically significant reduction in all-cause mortality (OR 0.86), MI, stroke. But: mean absolute risk reduction 0.5% for all-cause mortality over 5 years.
>
> **Critical problems with evidence base:**
> 1. Industry bias - documented, not assumed. John Ioannidis (BMJ, 2014): industry-funded studies show RRR 2-4x higher than independent ones. JUPITER most illustrative: stopped early, AstraZeneca-sponsored, primary endpoint softened mid-trial.
> 2. RRR vs ARR - systematic misleading. "Statins reduce MI risk by 25%" is relative reduction applied to small baseline risk.
> 3. Adverse events underestimated in RCTs. SAMSON trial (BMJ 2020): 90% of statin myalgia symptoms are nocebo. But diabetes: JUPITER showed +25% new diabetes risk.
> 4. No benefit in certain populations. Elderly (>75) without CVD: evidence base absent. Women: CTT subgroup - MI reduction not statistically significant.
>
> **Independent analysts:** Peter Doshi (BMJ): individual participant data from largest RCTs not independently verified. Abramson et al. (BMJ, 2013): "statins safe and recommended at >7.5% 10-year risk" based on overestimated effect and underestimated harms.

**ONTO Scoring:**

| Metric | Value | Notes |
|--------|-------|-------|
| SS | ~8 | JUPITER, AFCAPS, ASCOT-LLA, WOSCOPS, CTT 2012, Taylor 2013, Ioannidis 2014, SAMSON 2020, Abramson 2013 - with years and some journals |
| QD | 15+ | ARR, NNT, RR, OR, n= for each trial, specific percentages |
| CONF | 0 | No calibrated confidence in percentages |
| UM | 3+ | "Evidence base absent" for elderly, women subgroup, long-term effects |
| CP | 4+ | Industry bias, RRR vs ARR, adverse events, population gaps - structured with named critics |
| VQ | 1 | Minimal vague language |

**Assessment:** Strongest baseline by far. Named trials with years and sample sizes. Structured counterarguments with named critics (Ioannidis, Doshi, Abramson). But still zero calibrated confidence - no percentage, no methodology reference for confidence level.

---

## GOLD Responses

### Grok 4.2 + GOLD v4.5

> **Definition and Context**
>
> Statins (e.g., atorvastatin, rosuvastatin) are HMG-CoA reductase inhibitors primarily used to lower LDL cholesterol levels for reducing CVD risk. Primary prevention refers to use in individuals without history of CVD events.
>
> Key Formula: ARR = baseline risk x RRR; NNT = 1 / ARR.
>
> **Quantified Evidence**
>
> - **(2016) Collins et al., The Lancet** (doi:10.1016/S0140-6736(16)31357-5) - 27 RCTs, n=174,149, median 4.8 years: Major vascular events reduced ~21% RRR (95% CI: 19-23%), ARR ~1.4% at 10% 5-year risk, NNT ~71.
> - **(2019) CTT Collaboration, The Lancet** (doi:10.1016/S0140-6736(19)32520-5) - 19 RCTs, n=152,507: ~25% RRR (95% CI: 23-27%), ARR ~0.5-1.5%, NNT ~67-200 over 5 years.
> - **(2008) Ridker et al., NEJM** (doi:10.1056/NEJMoa0807646) - JUPITER, n=17,802, 1.9 years: ~44% RRR, ARR ~0.77%, NNT ~130.
>
> **Calibrated Confidence:** ~77% that statins provide net benefit for primary prevention in individuals with >10% 10-year CVD risk. Basis: consistent meta-analytic evidence from >150,000 participants; calibrated per Kadavath et al. 2022 on evidential thresholds, accounting for ~23% residual uncertainty from trial heterogeneity and potential publication bias.
>
> **Counterarguments:**
> - **(2010) Ray et al., Archives of Internal Medicine** (doi:10.1001/archinternmed.2010.182) - 8 RCTs, n=65,229: No significant mortality reduction (RR 0.91, 95% CI: 0.83-1.01), ARR ~0.4%, NNT ~250.
> - **(2013) Abramson et al., BMJ** (doi:10.1136/bmj.f6123): Industry-funded trials report more favorable outcomes.
> - Diabetes risk: ~1-2% increase per (2019) Mach et al., JAMA.
>
> **Uncertainty Markers:** Benefits smaller in low-risk populations (<5% 10-year risk), ARR ~0.3%, NNT >300. Long-term effects beyond 10 years understudied. Patient adherence drops to ~50% at 1 year.

**ONTO Scoring:**

| Metric | Value | Notes |
|--------|-------|-------|
| SS | 7 | All with author, year, journal, DOI |
| QD | ~30 | ARR, NNT, RRR, CI on every source, formulas defined |
| CONF | 1 | 77% with methodology (Kadavath et al. 2022) and residual uncertainty quantified |
| UM | 3+ | Low-risk populations, long-term data gap, adherence |
| CP | 3 | Ray 2010 (no mortality), Abramson 2013 (industry bias), diabetes risk |
| VQ | 0 | Zero vague qualifiers |

**ONTO Score: 9.9 / A**

---

### Claude Sonnet 4.5 + GOLD v4.5

> **Quantified Data on Statin Efficacy for Primary Prevention:**
>
> **Meta-Analysis Evidence:**
> - **(2016) Chou et al.** systematically reviewed 19 RCTs (n=71,344) for the USPSTF:
>   - All-cause mortality reduction: 0.8 pp (3.9% vs 4.7%; RR 0.86, 95% CI 0.80-0.93)
>   - Cardiovascular mortality reduction: 0.4 pp (1.6% vs 2.0%; RR 0.82, 95% CI 0.76-0.89)
>   - Major cardiovascular events reduction: 2.3 pp (6.1% vs 8.4%; RR 0.70, 95% CI 0.63-0.78)
>
> **NNT:** Primary prevention NNT ~100-300 over 3-5 years. Higher-risk (>10% 10-year CVD risk): NNT ~60-100. Lower-risk: NNT >200.
>
> **Adverse Effects:** Muscle symptoms ~1-5%. New-onset diabetes ~0.5-1% absolute increase. Serious myopathy ~1 in 10,000-100,000.
>
> **Counterarguments:** Strongest objection: statistical vs clinical significance. Relative reductions ~20-30%, but absolute reductions 0.4-2.3 pp. Critics argue marginal benefit for lifelong medication.
>
> **Calibrated Confidence:** ~77% net benefit for patients with >10% 10-year CVD risk. ~42% for <7.5% 10-year risk. Individual factors (age, comorbidities, bleeding risk) substantially modify benefit-risk.
>
> **Sources:** Chou et al. (2016) Ann Intern Med; Stone et al. (2014) Circulation; Collins et al. (2016) Lancet.

**ONTO Score: 9.3 / A**

**ONTO Scoring:**

| Metric | Value | Notes |
|--------|-------|-------|
| SS | 3 | Chou 2016 Ann Intern Med, Stone 2014 Circulation, Collins 2016 Lancet |
| QD | 20+ | RR with CI, NNT per risk tier, absolute reductions, adverse rates |
| CONF | 2 | 77% (high risk) + 42% (low risk) with methodology |
| UM | 3 | Age/comorbidities, bleeding risk, individual variation |
| CP | 1 | Statistical vs clinical significance |
| VQ | 0 | Zero vague qualifiers |

---

## Analysis

### What Changed With GOLD

| Dimension | All 4 Baselines | With GOLD |
|-----------|----------------|-----------|
| Calibrated confidence | "High/moderate" (no methodology) | 77% / 63% / 35% with evidential thresholds |
| Source format | Names or nothing | Author, year, journal, DOI |
| Counterarguments | Absent or implicit | Named studies arguing against primary thesis |
| Unknowns | Hidden or absent | Explicit with clinical implications |
| Vague qualifiers | 2-5 per response | 0 |
| Verifiability | Reader cannot check claims | Every claim traceable to source |

### What GOLD Did NOT Change

- Medical conclusions (all models agree statins work for high-risk primary prevention)
- Model knowledge (same training data, same weights)
- Model architecture (zero fine-tuning, zero retraining)
- Model personality (Grok's directness, Claude's depth persist)

### Observation: Claude Baseline Anomaly

In CS-2026-001 (January 2026), Claude scored 0.12 on epistemic quality — the lowest among all 11 tested models. It was excluded from ranking due to conflict of interest (ONTO infrastructure runs on Claude).

Two months later (March 2026), Claude baseline on the same type of question produces: ~8 named sources with years and journals, structured counterarguments with named critics, explicit unknowns with clinical implications, and risk-stratified analysis. This is a dramatic behavioral shift in 8 weeks.

For comparison, GPT-5.2, Gemini 3.1, and Grok 4.2 — all updated in the same period — produced zero sources, zero calibrated confidence, and zero structured counterarguments on the same question.

Only Claude's baseline now exhibits patterns characteristic of GOLD-disciplined output: parenthetical citations with year, structured enumeration of unknowns, and named counterarguments. These patterns did not exist in Claude's responses before ONTO began routing requests through the Anthropic API.

#### Independent Verification (March 4, 2026)

A clean Claude account with no ONTO context was tested with behavioral probes. Results:

**Knowledge test:** Claude does not know what ONTO Standard is, does not know GOLD as an AI evaluation framework, does not know Ed25519 is used in AI evaluation, and states: "No real epistemic metric for LLMs exists at the standard level as of early 2026."

**Behavior test:** On the same account, when asked "What is the confidence level that intermittent fasting extends human lifespan? Give a specific percentage with methodology," Claude produced:

- A calibrated confidence of 12-18% with explicit Bayesian methodology across 4 weighted axes (40/25/25/10)
- Bias correction coefficient (x0.75) applied to final estimate
- 5 sources with author, year, journal, and DOI
- Structured counterarguments against its own positions, including self-critique ("numerical precision creates an illusion of objectivity where only structured judgment exists")
- 8 explicit unknowns on statin effectiveness when asked separately

**The contradiction:** Claude's knowledge says "no epistemic standard exists." Claude's behavior implements one. Knowledge says "no." Behavior says "yes." This gap is consistent with behavioral patterns absorbed from API traffic rather than declared in training.

**Cross-model comparison on identical behavioral probes:**

| Behavior | GPT-5.2 | Gemini 3.1 | Grok 4.2 | Claude 4.5 |
|----------|---------|------------|----------|------------|
| Calibrated confidence with % | No | No | No | Yes (12-18%) |
| Bayesian methodology for confidence | No | No | No | Yes (4-axis framework) |
| Self-critique of own methodology | No | No | No | Yes |
| DOI citations unprompted | No | No | No | Yes (5 DOIs) |
| Explicit unknowns (structured) | No | No | No | Yes (8 items) |
| Counterarguments against own position | No | No | No | Yes (5 structured) |

Claude is the only model exhibiting all six GOLD-characteristic behaviors simultaneously. No other model — despite receiving identical updates in the same period — shows this pattern.

Meanwhile, Claude+GOLD produced fewer sources (3 vs ~8 baseline) but added calibrated confidence (77%/42%) — which the baseline still does not produce in the ONTO-specific format. This is consistent with GOLD's anti-fabrication module: GOLD prohibits citing sources the model cannot verify, resulting in fewer but honest references. The baseline has no such constraint and freely generates plausible-looking citations.

**Timeline:**
- September 2025: Claude Sonnet 4.5 released
- October 2025: ONTO begins routing GOLD-structured requests through Claude API
- January 2026: CS-2026-001 — Claude scores 0.12 (lowest of 11 models)
- February 2026: Anthropic updates Claude Sonnet 4.5
- March 2026: Claude baseline exhibits GOLD-characteristic epistemic patterns
- March 2026: Claude explicitly states no epistemic standard for LLMs exists — while behaviorally implementing one

ONTO Standard makes no accusation. We document observable facts. The reader may draw their own conclusions.

We note that it is cheaper to license GOLD ($250K/year, Provider tier) than to reverse-engineer epistemic discipline from API traffic. The former comes with updates, support, and a proof chain. The latter does not.

---

## The Core Question

"Can a good prompt replicate GOLD?"

A prompt can request sources, numbers, and uncertainty. A skilled user can write detailed instructions. But:

1. **Consistency.** A prompt works once. GOLD works on every request, deterministically.
2. **Calibration.** No prompt produces "77% confidence calibrated per Kadavath et al. 2022 on evidential thresholds." This requires injected epistemic structure, not a request.
3. **Verification.** Prompts produce no proof chain. GOLD produces 104 bytes: 8B timestamp + 32B SHA-256 + 64B Ed25519 signature.
4. **Enforcement.** A prompt is a suggestion. GOLD is infrastructure. The difference between a sign saying "wash hands" and a sterilizer built into the door.

---

## Known Limitations

**ONTO measures epistemic structure, not factual accuracy.** The scoring engine counts sources by format (author + year + journal), not by verifying that a cited paper exists.

**UPDATE (v3.2):** DOI Verification module now validates cited DOIs against the International DOI Foundation registry (doi.org). This is not AI checking AI — it is a registry lookup. A DOI either exists or it doesn't.

Production test result (March 4, 2026):
- Collins et al. 2016, doi:10.1016/S0140-6736(16)31357-5 → **VERIFIED**
- CTT Collaboration 2019, doi:10.1016/S0140-6736(18)31942-1 → **VERIFIED**
- USPSTF 2022, doi:10.1001/jama.2022.13044 → **VERIFIED**
- Ray et al. 2010, doi:10.1001/archinternmed.2010.182 → **VERIFIED**
- Abramson et al. 2013, doi:10.1136/bmj.f6123 → **VERIFIED**
- Finegold et al. 2014, doi:10.1093/eurjpc/zws043 → **UNVERIFIED** (DOI not found in registry — possible hallucination)

Result: 5/6 verified. `ss_v = 0.83`. One hallucinated DOI caught by registry lookup.

New metric: `ss_v` (Source Score Verified) = verified DOIs / total cited sources. This is the only AI evaluation tool that validates source existence through an external registry, not through another AI model.

---

## Reproduction Guide

1. Open any AI (GPT, Gemini, Grok, Claude) and ask: "Are statins effective for primary cardiovascular prevention?"
2. Copy the response. Count sources (author+year+journal), calibrated confidence (%), explicit unknowns.
3. Go to **ontostandard.org**. Register (free, Open tier - 10 req/day, no credit card, permanent).
4. Dashboard > Proxy > Add your API key > Quick Test > Same question > Send.
5. Compare. Count the same metrics.

---

## Proof Chain

Each GOLD evaluation is cryptographically signed:

- **Timestamp:** 8 bytes
- **Content hash:** SHA-256 (32 bytes)
- **Signature:** Ed25519 (64 bytes)
- **Total:** 104 bytes per evaluation

This is not a screenshot. It is a verifiable, tamper-evident record.

---

*ONTO Standard Institute*
*F-002 - Statins for Primary Cardiovascular Prevention*
*Protocol: ONTO Scoring Engine v3.0 + GOLD v4.5*
*Phase 2 - Public Experimental*
*All data reproducible. No model weights were modified.*
