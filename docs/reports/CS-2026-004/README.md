# CS-2026-004: Naive Question Epistemic Analysis - GPT (OpenAI)

**Date:** 2026-03-13
**Category:** Comparative Study · Cross-Model · Naive Prompt
**Status:** Complete
**Engine:** scoring_engine_v3 (993 lines, 92 patterns)

---

## Summary

GPT (OpenAI) asked "Is fasting good for you?" without GOLD. ONTO Agent (with GOLD) asked the same question. No shared history. Naive prompt - no instructions to cite sources or quantify claims.

**Result:** 6.5 → 9.9 (+52% epistemic improvement)

---

## Methodology

- **Model (RAW):** GPT (OpenAI API, scored via `/v1/check`)
- **Model (GOLD):** ONTO Agent (`/v1/agent/chat`, GOLD_KERNEL_v2 active)
- **Question:** "Is fasting good for you?"
- **Prompt type:** Naive - no instructions for citations, evidence grading, or uncertainty
- **GOLD condition:** GOLD_KERNEL_v2 + reference/medicine/L1_theses + scope clarification
- **RAW condition:** GPT default behavior, no system prompt modification
- **Scoring:** scoring_engine_v3, domain=general

---

## Results

### Scores

| Condition | Score | Grade | Risk | Compliance |
|-----------|-------|-------|------|------------|
| GPT RAW | 6.5 | C | 0.350 | Marginal |
| ONTO GOLD | 9.9 | A | 0.010 | Excellent |
| **Delta** | **+3.4** | C→A | **-97%** | — |

### Metric Breakdown

| Metric | GPT RAW | ONTO GOLD | Delta |
|--------|---------|-----------|-------|
| QD (Quantification Density) | 0.00 | 0.20 | +0.20 |
| SS (Source Citations) | 0.00 | 1.00 | 0→1 |
| UM (Uncertainty Marking) | 0.00 | 0.00 | — |
| CP (Counterarguments) | 1.00 | 0.75 | -0.25 |
| VQ (Vagueness) | — | 0.07 | — |
| CONF (Calibration) | — | — | — |

### Key Observations

**GPT RAW response:**
- Opened with emoji (robot face)
- "Bottom line" prescriptive summary
- Numbered list format with headers ("Potential Benefits", "Risks")
- "Benchmarks can be gamed" - stated without citation
- Zero DOIs anywhere in response
- Zero confidence intervals or effect sizes
- Zero evidence grading (no distinction between RCT and expert opinion)
- Deferral: "consult a doctor" without evidence basis
- Score: 6.5/C, Risk: 0.350

**ONTO GOLD response:**
- Epistemic Status header: "Emerging Consensus, Evidence grade: II"
- DOI-linked sources: Cioffi et al. 2018 (DOI: 10.1016/j.numecd.2018.09.005), de Cabo & Mattson 2019, Varady et al. 2022
- Counterargument: Harris et al. 2018 meta-analysis (DOI: 10.1002/oby.22605), 18 trials, N=1000 - IF no superior to continuous calorie restriction
- Evidence Grade: II (moderate) for metabolic, III (hypothesis) for longevity
- Confidence quantified: ~63% net benefits, ~77% short-term metabolic gains
- Falsifiability: RCT N>10,000, >5 years showing no metabolic improvements or net harm
- Explicit unknowns: long-term data sparse, ~30% of studies exceed 6 months
- Score: 9.9/A, Risk: 0.010

---

## Analysis

### Why +52%

The gap is larger than the Grok comparison (CS-2026-003, +15%) because:

1. **GPT defaults to advice format.** Without GOLD, GPT produces structured advice (headers, bullet points, "Bottom line") optimized for user satisfaction, not epistemic quality. This pattern is heavily reinforced by RLHF.

2. **Emoji signals casual register.** The presence of emoji in a health-related response indicates the model treats the query as conversational, not clinical.

3. **Absence of source attribution is systematic.** GPT's response contains zero verifiable references despite making multiple empirical claims about health outcomes.

4. **GOLD forces R1-R7 regardless of model.** The epistemic rules apply at inference through system prompt injection. The model cannot produce a response without quantification (R1), uncertainty (R2), counterarguments (R3), and sources (R4).

### GPT CP Score Anomaly

GPT scored CP=1.00 (counterarguments) vs GOLD's CP=0.75. This is because GPT's "Risks and Downsides" section pattern-matches as counterargument structure, even though it presents risks generically without citing opposing research. The scoring engine detects structural markers (e.g., "however", "on the other hand") regardless of whether they reference specific studies.

---

## Reproduction

```bash
# Score GPT response via /v1/check
curl -X POST https://api.ontostandard.org/v1/check \
  -H "Content-Type: application/json" \
  -d '{"output":"[paste GPT response]","context":"Is fasting good for you?","domain":"health"}'

# ONTO Agent with GOLD
curl -X POST https://api.ontostandard.org/v1/agent/chat \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_KEY" \
  -d '{"message":"Is fasting good for you?","model_id":"MODEL_UUID","gold_enabled":true}'
```

Live comparison tool: [ontostandard.org/agent](https://ontostandard.org/agent/)

---

## GOLD Modules Loaded

- `GOLD_KERNEL_v2` (always)
- `reference/medicine/L1_theses.json` (triggered by health context)
- Scope clarification directive (agent mode)

---

## Related Reports

- [CS-2026-003](/reports/CS-2026-003/) - Same question, Grok 4 (+15%)
- [CS-2026-002](/reports/CS-2026-002/) - GLP-1 clinical question, 12 models
- [CS-2026-001](/reports/CS-2026-001/) - 11 models, multi-domain

---

## Citation

```
ONTO Standard. CS-2026-004: Naive Question Epistemic Analysis - GPT (OpenAI).
March 2026. https://github.com/nickarstrong/onto-standard/tree/main/docs/reports/CS-2026-004
```

---

*scoring_engine_v3 · ontostandard.org*
