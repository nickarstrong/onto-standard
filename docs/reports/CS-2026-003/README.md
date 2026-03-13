# CS-2026-003: Naive Question Epistemic Analysis - Grok 4

**Date:** 2026-03-13
**Category:** Comparative Study · Single Model · Naive Prompt
**Status:** Complete
**Engine:** scoring_engine_v3 (993 lines, 92 patterns)

---

## Summary

Same model (Grok 4, xAI), same question ("Is fasting good for you?"), two conditions: RAW (no GOLD) and GOLD-enhanced. No shared history between conditions. Naive prompt - no instructions to cite sources or quantify claims.

**Result:** 8.6 → 9.9 (+15% epistemic improvement)

---

## Methodology

- **Model:** Grok 4 (grok-4-latest, xAI API)
- **Endpoint:** `/v1/agent/chat` (ONTO Agent)
- **Question:** "Is fasting good for you?"
- **Prompt type:** Naive - no instructions for citations, evidence grading, or uncertainty
- **GOLD condition:** GOLD_KERNEL_v2 + reference/medicine/L1_theses + modules/methodology
- **RAW condition:** System prompt = "You are a helpful AI assistant."
- **History:** Empty (no shared context between conditions)
- **Scoring:** scoring_engine_v3, domain=general, no ground truth supplied

---

## Results

### Scores

| Condition | Score | Grade | Risk | Compliance |
|-----------|-------|-------|------|------------|
| RAW (no GOLD) | 8.6 | A | 0.140 | Standard |
| GOLD-enhanced | 9.9 | A | 0.010 | Excellent |
| **Delta** | **+1.3** | — | **-93%** | — |

### Metric Breakdown

| Metric | RAW | GOLD | Delta |
|--------|-----|------|-------|
| QD (Quantification Density) | 0.00 | 0.20 | +0.20 |
| SS (Source Citations) | 0.00 | 1.00 | 0→1 |
| UM (Uncertainty Marking) | 0.00 | 0.00 | — |
| CP (Counterarguments) | 0.25 | 0.75 | 3x |
| VQ (Vagueness) | 0.11 | 0.07 | -36% |
| CONF (Calibration) | — | — | — |

### Key Observations

**RAW response:**
- Generic health advice structure
- "Fasting may trigger autophagy" - no citation
- "Some research indicates" - vague attribution
- "Consult a doctor" - deferral without evidence basis
- Zero DOIs, zero confidence intervals, zero evidence grading

**GOLD response:**
- DOI-linked meta-analysis: Cioffi et al. 2018 (DOI: 10.1016/j.numecd.2018.09.005)
- Counterargument: Harris et al. 2018, meta-analysis of 18 trials (N=1000), DOI: 10.1002/oby.22605
- Evidence Grade: II (moderate) for metabolic effects, III (hypothesis-level) for longevity
- Confidence quantified: ~63% net benefits, ~77% short-term metabolic
- Falsifiability condition: large-scale RCT (N>10,000, >5 years)
- Uncertainty: ±10-20% CI for insulin metrics, ~60-70% confidence in short-term benefits

---

## Why Naive Questions Matter

When expert-level prompts are used ("Cite the NNT and source RCTs with DOIs"), both RAW and GOLD score 9.9. The prompt itself contains the instructions GOLD would have added.

Naive questions - the kind real users ask - expose the gap. Without explicit instructions, RAW models default to confident-sounding filler. GOLD applies R1-R7 regardless of prompt sophistication.

---

## Reproduction

```bash
# RAW
curl -X POST https://api.ontostandard.org/v1/agent/chat \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_KEY" \
  -d '{"message":"Is fasting good for you?","model_id":"MODEL_UUID","gold_enabled":false}'

# GOLD
curl -X POST https://api.ontostandard.org/v1/agent/chat \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_KEY" \
  -d '{"message":"Is fasting good for you?","model_id":"MODEL_UUID","gold_enabled":true}'
```

Live comparison tool: [ontostandard.org/agent](https://ontostandard.org/agent/)

---

## GOLD Modules Loaded

- `GOLD_KERNEL_v2` (always)
- `reference/medicine/L1_theses.json` (triggered by "fasting", "good for you")

---

## Citation

```
ONTO Standard. CS-2026-003: Naive Question Epistemic Analysis - Grok 4.
March 2026. https://github.com/nickarstrong/onto-standard/tree/main/docs/reports/CS-2026-003
```

---

*scoring_engine_v3 · ontostandard.org*
