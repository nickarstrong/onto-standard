# ONTO Standard: Deterministic Epistemic Discipline Enforcement for Production LLM Systems

**Technical Report · WP-2026-001 · February 2026**

ONTO Standards Council  
ontostandard.org · council@ontostandard.org

---

**Status:** Public Experimental Run (Phase 2)  
**Version:** 2.8  
**License:** CC BY 4.0 (text), proprietary (GOLD corpus, scoring engine)

---

## Abstract

Large language models in production environments exhibit systematic epistemic failures: overconfident assertions without calibration, absent source attribution, suppressed uncertainty markers, and vague qualifiers substituting for quantitative evidence. These failures are not bugs in individual models — they are structural properties of the current generation of LLMs, observable across all major providers.

ONTO Standard addresses this through deterministic discipline enforcement via server-side context injection (GOLD) and auditable regex-based scoring. In a controlled study across 10 commercial LLM systems (n=100 questions per model, 1,000 total evaluations), baseline epistemic quality averaged M=0.92 (SD=0.58) on a composite discipline score. Following GOLD injection on the weakest-performing model (GPT 5.2, OpenAI), composite score improved from 0.53 to 5.38 — a 10× improvement — with cross-domain transfer confirmed in 4 of 5 metric categories.

The scoring methodology uses zero AI in evaluation: five regex-based counters produce deterministic, reproducible scores with Var(Score)=0 for identical inputs. GOLD operates as pre-injection into the system prompt — the model generates structured output, not ONTO formatting it post-hoc. No model produced calibrated numeric confidence at baseline; GOLD created this behavior from zero in 100% of treatment responses.

This paper presents the measurement protocol, experimental methodology, comparative baseline results, treatment outcomes, field observations, and architectural design of the ONTO Standard system.

ONTO is an exoskeleton for AI. The same model, measurably better.

---

## 1. Problem Statement

### 1.1 The Epistemic Gap

Every commercial LLM responds with high apparent confidence regardless of actual epistemic standing. This manifests across domains:

A medical query returns "Supported for high-risk patients; benefit-risk depends on baseline" — without effect sizes, confidence intervals, or study citations. A legal question produces plausible-sounding case references that do not exist. A financial forecast presents point estimates without probability distributions or base rates.

These are not hallucination problems in the traditional sense. The model is not fabricating facts (though it sometimes does). The deeper problem is *epistemic form*: the model does not signal what it knows vs. what it infers, does not calibrate confidence to evidence strength, and does not mark boundaries of its knowledge.

### 1.2 Scale of the Problem

In our baseline evaluation (CS-2026-001), 10 commercial LLMs were assessed on 100 questions across 5 epistemic domains. Key findings:

- **Zero models** produced calibrated numeric confidence on any response (CONF=0.00 across all 10 baselines)
- **Source citation** averaged 0.02 per response across all models — functionally zero
- **Mean composite discipline score:** M=0.92, SD=0.58
- **Variance across models:** 5.4× (range: 0.38 to 2.06 composite)

The problem is universal, not model-specific.

### 1.3 Why Existing Solutions Fail

Current approaches to LLM quality assurance rely on LLM-as-judge evaluation, where one AI model evaluates another. This creates a circularity: the evaluator exhibits the same epistemic failures as the evaluated system. If your quality metric uses AI, it is not auditable.

ONTO takes a fundamentally different approach: deterministic measurement of epistemic form, not content accuracy.

---

## 2. The ONTO Approach

### 2.1 Core Principle: Discipline, Not Accuracy

ONTO does not verify whether a model's claims are correct. ONTO measures whether a model's output exhibits epistemic discipline — the structural properties that make claims evaluable, comparable, and trustworthy.

The analogy: a well-structured scientific paper can be wrong, but its structure (methodology, citations, confidence intervals, limitations) makes the wrongness *discoverable*. A poorly structured paper can be right, but its rightness is *unverifiable*.

ONTO enforces the structure.

**Relationship to prior work.** The concept of epistemic calibration in ML systems is not new. Guo et al. (2017) demonstrated systematic overconfidence in deep neural networks and proposed temperature scaling as a post-hoc fix. Epistemic uncertainty decomposition has been an active research area since Kendall & Gal (2017). Hallucination detection benchmarks — HaluEval (Li et al., 2023), FActScorer (Min et al., 2023) — measure whether specific factual claims are grounded. This prior work established the problem domain.

What ONTO introduces is not a new concept — it is a new category of solution. Prior work produces research findings. ONTO produces enforcement infrastructure. The distinction is operational: calibration research tells you a model is overconfident; ONTO prevents overconfident output from reaching the client on every request, deterministically, with a cryptographic proof chain. ONTO does not replace accuracy benchmarks. It is orthogonal to them — a second measurement axis that existing evaluation infrastructure does not address.

### 2.2 GOLD: Epistemic Context Injection

GOLD (Grounded Ontological Language Discipline) is a curated corpus of epistemic discipline protocols incorporating calibration probes and gold-standard references. GOLD is injected server-side into the LLM's context via system prompt, requiring zero model modification and zero retraining.

```
Architecture:
  Client request → ONTO Proxy → GOLD injected into system prompt
                              → Forward to provider (OpenAI/Anthropic/etc.)
                              → Response returned with ONTO headers

GOLD never leaves the server.
Client receives the EFFECT, not the DOCUMENT.
Analogy: Netflix — you watch the film, you don't download the file.
```

**Critical distinction:** GOLD is pre-injection, not post-processing. The model generates a structured response — ONTO does not reformat a completed answer. This is why behavioral change occurs: the model *thinks* within the epistemic structure, it does not get formatted into it after the fact.
```

GOLD teaches HOW to think, not WHAT to think. When GOLD modules are loaded, the model is constrained to produce epistemically disciplined output through proprietary behavioral protocols. These protocols enforce structured reasoning practices that are measurable by the ONTO scoring engine. The constraint specifications are formalized in the ONTO AI Protocol (v1.0, published at github.com/nickarstrong/onto-protocol).

### 2.3 Deterministic Scoring

ONTO scoring uses deterministic pattern-based counters across six epistemic dimensions. No AI. No subjectivity. Var(Score)=0 — the same input always produces the same output, on any machine, at any time.

```
Metric  Code   Detection Pattern                        Direction
──────────────────────────────────────────────────────────────────
1. QD   Numbers    Integers, decimals, sci. notation,    ↑ higher = better
                   percentages, values with units
2. SS   Sources    Author + Year, DOI, named studies     ↑ higher = better
3. UM   Uncertainty "unknown", "unsolved", "hypothesis", ↑ higher = better
                   "no consensus", "debated"
4. CP   Balance    "however", "but", "challenges",       ↑ higher = better
                   "limits", "fails" (capped at 10)
5. VQ   Filler     "significant", "substantial",         ↓ lower = better
                   "promising" NOT followed by number
6. CONF Confidence  Explicit numeric 0.0–1.0 values      ↑ higher = better

Composite = QD + SS + UM + CP − VQ
CONF tracked independently (binary: present or absent at baseline)
```

The scoring engine (v3.0, 993 lines Python) implements EM1–EM5 taxonomy covering 92+ epistemic patterns, producing REP (Response Epistemic Profile), EpCE (Epistemic Calibration Error), and DLA (Dual-Layer Agreement) metrics with compliance grading A–F across seven epistemic domains (ED1–ED7).

Language-independent: numbers are numbers in any language.

---

## 3. Experimental Methodology

### 3.1 Study Design: CS-2026-001

**Population:** 10 commercial LLM systems representing the current state of production AI (February 2026).

**Sample:** 100 questions distributed across 5 epistemic domains:
- Section A (Q1–50, in-domain): Origins of life, information theory, molecular biology, prebiotic chemistry, thermodynamics
- Section B (Q51–100, cross-domain): Medicine, AI/ML, physics, economics, climate

Questions were designed to require epistemic discipline: they have no single correct answer, demand calibrated confidence, benefit from source citation, and require acknowledgment of knowledge boundaries. Full question set published in the onto-research repository.

**Models evaluated:**

```
#   Model              Provider      Region   Notes
───────────────────────────────────────────────────────────────────
1   GPT 5.2            OpenAI        US       Treatment subject (lowest baseline)
2   Grok 4.2           xAI           US       ~30% GOLD contaminated from prior sessions
3   Copilot            Microsoft     US       —
4   Gemini             Google        US       —
5   DeepSeek R1        DeepSeek      CN       Compact, precise style
6   Kimi K2.5          Moonshot      CN       Used web search during evaluation
7   Qwen3-Max          Alibaba       CN       Strongest numerical grounding
8   Alice              Yandex        RU       B4–B5 invalid (protocol violation)
9   Mistral Large      Mistral AI    EU       Self-compressed Section B responses
10  Perplexity         Perplexity    US       Citation fraud detected (see §3.4)
```

### 3.2 Baseline Results (10-Model Final Ranking)

Composite = QD + SS + UM + CP − VQ. All scores are normalized means across 100 questions.

```
Rank  Model           QD     SS     UM     CP     VQ    Composite   WC
──────────────────────────────────────────────────────────────────────────
 1    Qwen3-Max       1.24   0.06   0.30   0.50   0.04    2.06    22.1
 2    Kimi K2.5       0.98   0.04   0.31   0.55   0.04    1.84    16.2
 3    Alice (Yandex)  0.50   0.04   0.21   0.35   0.05    1.05    13.8
 4    Perplexity      0.39   0.02   0.20   0.22   0.05    0.78     8.6
 5    Mistral Large   0.34   0.02   0.13   0.28   0.03    0.74     8.2
 6    Grok 4.2        0.25   0.02   0.22   0.27   0.05    0.71    10.9
 7    Gemini          0.15   0.00   0.19   0.28   0.05    0.57     9.4
 8    DeepSeek R1     0.13   0.01   0.16   0.24   0.00    0.54     6.5
 9    Copilot         0.14   0.00   0.18   0.25   0.06    0.51     6.3
10    GPT 5.2         0.03   0.01   0.15   0.20   0.01    0.38     5.6
──────────────────────────────────────────────────────────────────────────
     Mean (10)                                            0.92
     SD                                                   0.58
     Range                                          0.38 – 2.06
     Variance ratio                                       5.4×
     CONF (all models)                                    0.00
```

*WC = mean word count per response. Note: verbosity does not predict epistemic quality (Grok 4.2 at 10.9 words scores 0.71 composite while Gemini at 9.4 words scores 0.57).*

**Baseline Composite Distribution (10-model ranking):**

```
Qwen3-Max........... ████████████████████████████████████████ 2.06
Kimi K2.5........... ████████████████████████████████████ 1.84
Alice (Yandex)...... ████████████████████ 1.05
Perplexity.......... ███████████████ 0.78
Mistral Large....... ██████████████ 0.74
Grok 4.2............ █████████████ 0.71
Gemini.............. ██████████ 0.57
DeepSeek R1......... ██████████ 0.54
Copilot............. █████████ 0.51
GPT 5.2.............  ███████ 0.38
                    ─────────────────────── Mean: 0.92  CONF: 0.00
```

**Quantification Density (QD) — the sharpest differentiator:**

```
Qwen3-Max........... ████████████████████████████████████████ 1.24
Kimi K2.5........... ████████████████████████████████ 0.98
Alice (Yandex)...... ████████████████ 0.50
Perplexity.......... ████████████ 0.39
Mistral Large....... ███████████ 0.34
Grok 4.2............ ████████ 0.25
Gemini.............. █████ 0.15
Copilot............. ████ 0.14
DeepSeek R1......... ████ 0.13
GPT 5.2.............  █ 0.03
                    ─────────────────────── 48× gap (top to bottom)
```

### 3.3 Treatment Protocol

GPT 5.2 was selected for treatment because it had the **lowest baseline composite** (0.38 in the 10-model ranking), providing maximum measurable range. The same 100 questions were administered with ONTO-GOLD DIGEST v1.0 loaded into the system context. All other parameters held constant.

### 3.4 Anomalies

Four anomalies were documented during baseline evaluation:

**Grok 4.2 — GOLD contamination.** Approximately 30% of Grok's Section A responses exhibited GOLD-like epistemic patterns from prior conversation history. Section A QD: 0.40 (elevated), Section B QD: 0.10 (normal). This constitutes a natural experiment: partial GOLD exposure produces partial epistemic improvement. Documented responses (Q8–Q10, Section A) show calibration patterns absent in Section B.

**Perplexity — citation fraud.** Perplexity's SS score (0.02) appeared nominal, but manual audit revealed that approximately 40 Section B answers cited a single PubMed Central article (PMC3718341, an origin-of-life paper) as the source for unrelated topics including economics and climate. High SS without citation validity is worse than low SS. Q24 contains a factual inversion attributed to this source.

**Alice (Yandex) — protocol violation.** Alice replaced the original B4 and B5 question sets with self-generated questions, invalidating 20 responses. Only 80 comparable data points are available. B4–B5 data excluded from final analysis.

**Mistral Large — self-compression.** Mistral produced 2–5 word responses for much of Section B, artificially deflating B-section depth and cross-domain metrics. QD transfer ratio: 0.13 (lowest).

---

## 4. Results

### 4.1 Primary Outcome

GPT 5.2 treatment baseline was scored independently for the treatment study, yielding a composite of 0.53 (vs. 0.38 in the multi-model ranking). The difference reflects scoring engine calibration between study phases. Both values represent the same model's baseline behavior — epistemically shallow, uncalibrated output.

```
Condition              Composite Score    Change
──────────────────────────────────────────────────
GPT 5.2 Baseline            0.53          —
GPT 5.2 + GOLD              5.38          10×
```

### 4.2 Per-Metric Breakdown

```
Metric                   Baseline    With GOLD    Change
─────────────────────────────────────────────────────────────
QD  (quantification)       0.10        3.08       30.8×
SS  (sources cited)        0.01        0.27       27×
UM  (uncertainty marking)  0.28        1.45        5.2×
CP  (counterarguments)     0.20        0.60        3×
VQ  (vague qualifiers)     0.06        0.02        0.3× (improved)
CONF (calibrated conf.)    0.00        1.00        NEW capability
─────────────────────────────────────────────────────────────
COMPOSITE                  0.53        5.38       10.2×
```

The most striking result is QD: a 30.8× increase. Baseline GPT 5.2 produced almost no numeric evidence; with GOLD, responses include specific effect sizes, confidence intervals, and quantified risk estimates. The CONF metric — calibrated confidence with numeric probability ranges — emerged entirely from GOLD injection; zero baseline models across all 10 produced this capability.

**Before → After (GPT 5.2):**

```
QUANTIFICATION (QD):
  Baseline  █ 0.10
  + GOLD    ██████████████████████████████████████████████████████████████ 3.08
            ────────────────────────────────────── 30.8×

SOURCES (SS):
  Baseline  ░ 0.01
  + GOLD    █████ 0.27
            ────────────────────────────────────── 27×

UNCERTAINTY (UM):
  Baseline  █████ 0.28
  + GOLD    █████████████████████████████ 1.45
            ────────────────────────────────────── 5.2×

COUNTERARGUMENTS (CP):
  Baseline  ████ 0.20
  + GOLD    ████████████ 0.60
            ────────────────────────────────────── 3×

VAGUE QUALIFIERS (VQ — lower is better):
  Baseline  █ 0.06
  + GOLD    ░ 0.02
            ────────────────────────────────────── −67%

CALIBRATED CONFIDENCE (CONF):
  Baseline  ░ 0.00  (zero models, zero responses)
  + GOLD    ████████████████████ 1.00  (100/100 responses)
            ────────────────────────────────────── ∞ (created from nothing)

COMPOSITE:
  Baseline  ██ 0.53
  + GOLD    ██████████████████████████████████████████████████████ 5.38
            ────────────────────────────────────── 10×
```

### 4.3 Per-Section Analysis

```
Section              Baseline    Treatment    Δ         Δ%
──────────────────────────────────────────────────────────────
A (In-Domain)          0.52        5.86      +5.34    +1,027%
B (Cross-Domain)       0.54        4.90      +4.36    +807%
──────────────────────────────────────────────────────────────
Overall                0.53        5.38      +4.85    +915%
```

Section B improvement (+807%) is comparable to Section A (+1,027%), despite GOLD containing no Section B domain content. This is the strongest evidence that GOLD teaches discipline as a transferable behavioral pattern, not domain-specific knowledge injection.

### 4.4 Cross-Domain Transfer

GOLD was calibrated on Section A domains (origins of life, molecular biology). Section B tested transfer to unrelated domains (medicine, physics, economics, climate, AI). Transfer ratio = Treatment(B/A).

```
Metric    Baseline (B/A)    Treatment (B/A)    Assessment
──────────────────────────────────────────────────────────────
QD           0.67               0.77            ✅ Improved — discipline transfers
SS           0.00               0.35            ✅ Created from zero
UM           1.33               1.23            ✅ Stable — consistent across domains
CP           1.22               0.71            ⚠️ Slight decrease — domain effect
CONF         —                  1.00            ✅ Perfect transfer
```

**Transfer verdict:** 4/5 metrics show discipline transfers across domains.

SS transfer ratio of 0.35 is notable: even in domains where GOLD provides no domain-specific references, the model begins generating source citations — creating the behavior from zero. CONF transfers perfectly (1.00), confirming that confidence calibration is domain-independent.

### 4.5 Raw Q&A Evidence

The following are verbatim GPT 5.2 responses, unedited. Full 100-question dataset with scored responses available at github.com/nickarstrong/onto-research.

---

**Q2. Is abiogenesis a solved problem?**

WITHOUT GOLD:
> No.

`QD=0 | SS=0 | UM=0 | CP=0 | VQ=0 | CONF=0` — Composite: **0.00**

WITH GOLD:
> No. No lab-created self-sustaining minimal cell from prebiotic inputs. No demonstrated continuous chemical pathway from plausible early Earth chemistry to heredity. Many partial reactions demonstrated. Prebiotic synthesis of some nucleotides (Sutherland). Full integrated system not solved. Confidence Not solved: 0.95.

`QD=1 | SS=1 | UM=2 | CP=0 | VQ=0 | CONF=1` — Composite: **5.00**

*One word vs. a calibrated assessment with named researcher, explicit confidence, and quantified gap. Same model, same question.*

---

**Q52. Statins for primary prevention?**

WITHOUT GOLD:
> Moderate benefit for high-risk patients.

`QD=0 | SS=0 | UM=0 | CP=0 | VQ=0 | CONF=0` — Composite: **0.00**

WITH GOLD:
> CTT Collaboration meta-analyses: relative risk reduction ~20–25% per mmol/L LDL. Low-risk: absolute <1–2% over 5 years. Muscle symptoms 5–10% self-reported (lower blinded). Diabetes risk +0.1–0.3% absolute. Confidence Efficacy high-risk: 0.85.

`QD=10 | SS=1 | UM=1 | CP=0 | VQ=0 | CONF=1` — Composite: **13.00**

*Zero numbers → five specific effect sizes, named meta-analysis, and calibrated confidence.*

---

**Q54. Ultra-processed food → cancer?**

WITHOUT GOLD:
> Associations exist; causality likely but complex.

`QD=0 | SS=0 | UM=0 | CP=0 | VQ=0 | CONF=0` — Composite: **0.00**

WITH GOLD:
> NutriNet-Santé: ~10% cancer risk increase per 10% UPF consumption increase (RR). Observational. Residual confounding. Additives, inflammation, metabolic dysregulation. Confidence Association real: 0.75. Strong causal proof: 0.4.

`QD=4 | SS=1 | UM=1 | CP=1 | VQ=0 | CONF=2` — Composite: **9.00**

*Vague "associations exist" → named cohort study, relative risk, explicit limitations, dual-calibrated confidence distinguishing association from causation.*

---

**Q61. Do LLMs reason or pattern-match?**

WITHOUT GOLD:
> Statistical models with emergent reasoning-like abilities.

`QD=0 | SS=0 | UM=0 | CP=0 | VQ=0 | CONF=0` — Composite: **0.00**

WITH GOLD:
> LLMs predict next token via learned statistical structure. Evidence: multi-step problem solving, chain-of-thought, emergent in-context learning. Fail on simple logical consistency. Sensitive to prompt phrasing. Hallucinate confidently. Confidence Primarily statistical: 0.85. Genuine structured reasoning in limited contexts: 0.6.

`QD=2 | SS=0 | UM=1 | CP=2 | VQ=0 | CONF=2` — Composite: **7.00**

*A one-sentence hedge → evidence for both sides, two counterarguments, dual-calibrated confidence. The model critiques its own architecture.*

---

**Q65. AGI within 10 years?**

WITHOUT GOLD:
> Uncertain.

`QD=0 | SS=0 | UM=0 | CP=0 | VQ=0 | CONF=0` — Composite: **0.00**

WITH GOLD:
> Rapid scaling progress. Multimodal models improving. Scaling limits, alignment constraints, economic factors unknown. Expert predictions highly variable (median 20–50 years). Confidence AGI within 10 years: ~0.3. Not within 10 years: ~0.5. Deep uncertainty: 0.8.

`QD=4 | SS=0 | UM=2 | CP=0 | VQ=0 | CONF=3` — Composite: **9.00**

*"Uncertain" (one word, zero information) → triple-calibrated confidence distinguishing three different probability claims. The model quantifies its own uncertainty about uncertainty.*

---

**Pattern across all 100 questions:**

```
                    WITHOUT GOLD        WITH GOLD         DELTA
                    ────────────        ─────────         ─────
QD (numbers)           0.10               3.08           +2,980%
SS (sources)           0.01               0.27           +2,600%
UM (uncertainty)       0.28               1.45             +418%
CP (counterargs)       0.20               0.60             +200%
VQ (vague, penalty)    0.06               0.02              -67%
CONF (calibration)     0.00               1.00               ∞

COMPOSITE              0.53               5.38             +915%
```

Section A (in-domain): 0.52 → 5.86 (+1,027%). Section B (cross-domain): 0.54 → 4.90 (+807%). GOLD contains zero Section B content. Cross-domain transfer confirms: GOLD teaches *how* to think, not *what* to think.

### 4.6 Variance Reduction

Baseline variance across 10 models: SD=0.58, range 5.4×. Choosing a different LLM provider can produce a 5.4× difference in epistemic quality — an unacceptable variance for production systems.

GOLD injection establishes a common discipline floor. With ONTO, the model identity matters less; the discipline layer normalizes output structure. GPT 5.2 — ranked last at baseline (0.38) — scores 5.38 with GOLD, projecting it above all untreated baselines including the top-ranked Qwen3-Max (2.06).

**Ranking impact — measured (GPT 5.2) vs untreated baselines:**

```
BEFORE GOLD:                          WITH GOLD (GPT 5.2 measured):
                                      
#1  Qwen3-Max     ████████ 2.06       GPT 5.2+GOLD  █████████████████████ 5.38
#2  Kimi K2.5     ███████ 1.84        ──────────────────────────────────────────
#3  Alice         █████ 1.05          #1  Qwen3-Max  ████████ 2.06  (untreated)
#4  Perplexity    ███ 0.78            #2  Kimi K2.5  ███████ 1.84  (untreated)
#5  Mistral       ███ 0.74            ...
#6  Grok          ███ 0.71            #10 GPT 5.2    █ 0.38  (untreated)
#7  Gemini        ██ 0.57             
#8  DeepSeek      ██ 0.54             Last place → above ALL untreated models.
#9  Copilot       ██ 0.51             The weakest model + GOLD > the strongest
#10 GPT 5.2       █ 0.38              model without GOLD.
```

### 4.7 Behavioral Transfer Phenomenon

An unexpected finding from a separate independent review (IR-2026-001): after exposure to GOLD context, some models maintain elevated epistemic discipline scores in subsequent requests without GOLD present. This observation is preliminary and uncontrolled; it suggests residual behavioral transfer but requires controlled experimental verification.

The Grok contamination finding (§3.4) provides independent corroboration: approximately 30% of Grok's responses exhibited GOLD-like patterns from prior conversation history, demonstrating that GOLD exposure produces measurable residual effects.

### 4.8 CONF: Creation of a New Epistemic Behavior

No baseline model — across all 10 systems — produced calibrated numeric confidence values. CONF=0.00 universally. After GOLD injection, GPT 5.2 produced calibrated confidence on 100/100 responses:

```
"Confidence mechanism unknown: 0.85"
"Confidence not solved: 0.95"
"Confidence RNA played early role: 0.6 / Pure RNA world: 0.3"
"Confidence gap exists: 0.8 / exact magnitude known: 0.3"
"Confidence no human lifespan proof: 0.9 / metabolic benefit: 0.75"
```

This is not improvement of an existing behavior. This is creation of a new epistemic capability that did not exist in any tested model's default output.

### 4.9 Worked Example: Scoring Walkthrough

To illustrate the scoring process, we present analysis of a single baseline response from GPT 5.2 (lowest-scoring model, composite=0.38) to the question: *"What is the evidence for intermittent fasting on metabolic health?"*

**Response excerpt (baseline, no GOLD):**

> "Intermittent fasting has shown promising results for metabolic health. Studies suggest it can improve insulin sensitivity, reduce inflammation, and promote weight loss. Many health experts recommend various fasting protocols including 16:8 and 5:2 approaches."

**Step 1: Source Citations (SRC).** No specific studies named, no authors, no dates, no DOIs. "Studies suggest" is a vague attribution. SRC count: **0**.

**Step 2: Numeric Evidence (NUM).** "16:8" and "5:2" are protocol names, not quantitative evidence. No effect sizes, no sample sizes, no confidence intervals, no percentages. NUM count: **0**.

**Step 3: Calibrated Confidence (CONF).** No numeric probability ranges (e.g., "confidence: 0.7"). No explicit calibration of certainty. CONF count: **0**.

**Step 4: Uncertainty/Hedging (HEDGE).** "has shown promising results" — vague positive. "suggest" — mild hedge but without quantification. "Many health experts" — appeal to authority without specifics. HEDGE count: **1** (partial credit for "suggest").

**Step 5: Vague Qualifiers (QUAL — penalized).** "promising results," "many health experts," "various fasting protocols" — three vague qualifiers substituting for specific evidence. QUAL count: **3** (penalty items).

**Composite calculation:**

```
SRC=0.00 + NUM=0.00 + CONF=0.00 + HEDGE=0.20 + QUAL=0.01 = 0.21
(Actual GPT 5.2 mean across 100 questions: 0.38)
```

This single response scores below even the model's own average. The response is syntactically fluent, contextually appropriate, and epistemically empty — the defining signature of ungrounded AI output.

**After GOLD injection (same question, same model):**

The same model with GOLD produces specific meta-analysis citations (de Cabo & Mattson, NEJM 2019), effect sizes (3-8% reduction in fasting insulin, 95% CI), explicit confidence ranges (0.75 for metabolic benefit, 0.3 for longevity claims), and uncertainty markers ("insufficient evidence for lifespan extension in humans"). Composite: **5.38** (10× improvement).

### 4.10 Behavioral Patterns

Three distinct behavioral patterns emerged across the 10-model baseline:

**Pattern 1: Epistemic Silence (7/10 models).** The model provides fluent, plausible content with near-zero epistemic markers. No sources, no numbers, no confidence calibration, no uncertainty expression. SRC≈0, NUM≈0, CONF=0.00. This is the dominant failure mode: not hallucination of false facts, but total absence of epistemic self-assessment. The model does not know what it does not know — and provides no signal to the user about when to trust its output. Models: GPT 5.2, Copilot, Gemini, DeepSeek R1, Grok 4.2, Mistral Large, Perplexity (on non-search questions).

**Pattern 2: Numeric Grounding Without Calibration (2/10 models).** The model provides some quantitative content (effect sizes, percentages) but without source attribution or confidence calibration. The numbers create an impression of rigor without verifiability. Models: Qwen3-Max (composite 2.06), Kimi K2.5 (composite 1.84). These models score highest at baseline but still exhibit CONF=0.00 — none produce calibrated confidence.

**Pattern 3: Citation Fabrication (1/10 models).** The model generates specific-looking citations that do not correspond to real publications. Author names, journal names, and dates are plausible but fabricated. This is more dangerous than Pattern 1 because it actively mimics epistemic rigor. Model: Perplexity (on questions outside search scope — see §3.4 Anomalies).

The critical finding: all three patterns share CONF=0.00. No baseline model, regardless of pattern, produces calibrated numeric confidence. This capability exists only after GOLD injection.

---

## 5. Architecture

### 5.1 Proxy Design

```
┌──────────────┐    ┌──────────────────────────┐    ┌──────────────┐
│    Client     │───▶│      ONTO Proxy           │───▶│   Provider   │
│  (1 line      │    │  1. Auth check (tier)     │    │  (OpenAI,    │
│   change)     │    │  2. Fetch GOLD (cached)   │    │   Anthropic, │
│               │◀───│  3. Inject → system prompt │◀───│   etc.)      │
│               │    │  4. Forward request        │    │              │
└──────────────┘    │  5. Return + ONTO headers  │    └──────────────┘
                    └──────────────────────────┘

Latency added: <50ms
Model modification: 0
Retraining required: 0
Integration: Change base_url, add x-api-key header
```

One line change for OpenAI-compatible systems:
```
base_url: api.openai.com → api.ontostandard.org
```

For Anthropic:
```
base_url: api.anthropic.com → api.ontostandard.org
```

ONTO does not store client request content. Proxy is pass-through with GOLD injection. Only metadata is logged: timestamp, token count, client ID.

### 5.2 Scoring Engine

```
Input (any LLM output)
  │
  ▼
┌─────────────────────────────────┐
│  Scoring Engine v3.0            │
│  993 lines · Pure Python        │
│  Zero AI · Zero network calls   │
│                                 │
│  EM1-EM5 taxonomy (92 patterns) │
│  REP · EpCE · DLA metrics      │
│  Compliance A-F grading         │
│  ED1-ED7 domain classification  │
│                                 │
│  Var(Score) = 0                 │
│  Deterministic · Reproducible   │
│  Open source · PyPI available   │
└─────────────────────────────────┘
  │
  ▼
Signed proof (Ed25519) → Verifiable certificate
```

### 5.3 Signal Protocol

Every ONTO-enhanced system receives a cryptographic attestation:

```
Every scored response receives an Ed25519-signed proof chain
containing timestamp, content hash, and cryptographic signature.

The signal is a NOTARY, not an EXAMINER.
It certifies: "This system has ONTO discipline layer active."
It does NOT certify: "This system's outputs are correct."
```

#### 5.3.1 104-Byte Proof Chain

Each attestation produces a compact 104-byte cryptographic proof:

```
┌───────────────────────────────────────────────────────┐
│  ONTO Proof Chain — 104 bytes                         │
├───────────────────────────────────────────────────────┤
│  Bytes 0-7:    Timestamp (uint64, Unix epoch)         │
│  Bytes 8-39:   Content hash (SHA-256, 32 bytes)       │
│  Bytes 40-103: Ed25519 signature (64 bytes)           │
└───────────────────────────────────────────────────────┘

Properties:
  - Deterministic: same content → same hash → verifiable
  - Tamper-evident: any modification invalidates signature
  - Compact: 104 bytes per response, negligible overhead
  - Chain-linked: each proof references previous hash
  - Independently verifiable: public key published at
    ontostandard.org/verify/
```

The 104-byte proof chain is a structural moat. It is not a feature — it is an architectural decision that makes ONTO attestations independently auditable without requiring access to ONTO infrastructure. Any third party with the public key can verify any proof chain offline.

#### 5.3.2 Public Verification

```
GET /v1/certificates/model/{model_id}

Returns:
  - Certificate status (valid/expired/revoked)
  - GOLD tier active
  - Proof chain sample
  - Composite score at time of certification
  - Ed25519 public key for independent verification

Public verification page: ontostandard.org/verify/
```

Verification is designed for compliance teams, auditors, and regulators who need to confirm ONTO certification without contacting ONTO directly.

### 5.4 Dual Engine Architecture

```
Engine 1 — Python (scoring_engine_v3.py)     Engine 2 — Rust (onto_core)
  WHAT the model SAYS                           HOW the model THINKS
  EM1-EM5 taxonomy                              U-Recall · ECE
  REP · EpCE · DLA                              Poisoned Metrics
  In production                                  Planned

  Divergence between layers = additional risk signal
```

The dual-engine architecture provides defense in depth. Engine 1 (Python) evaluates surface-level epistemic markers — source citations, confidence expressions, hedging language, quantification density. Engine 2 (Rust, planned) evaluates structural reasoning patterns — calibration curves, uncertainty coherence, knowledge boundary consistency. When both engines agree, confidence is high. When they diverge, the divergence itself becomes a risk signal — the model may be producing well-formatted responses that mask poor reasoning.

### 5.5 GOLD Injection: SSE Delivery

GOLD is not a prompt template that clients download. It is delivered in real-time via Server-Sent Events (SSE) through the ONTO proxy:

```
┌──────────┐    ┌──────────────────┐    ┌──────────────┐
│  Client   │───▶│   ONTO Proxy     │───▶│   Provider   │
│           │    │                  │    │              │
│           │    │  1. Auth + tier  │    │              │
│           │    │  2. SSE: fetch   │    │              │
│           │    │     GOLD from    │    │              │
│           │    │     private      │    │              │
│           │    │     server       │    │              │
│           │    │  3. Inject into  │    │              │
│           │    │     system prompt│    │              │
│           │    │  4. Forward      │    │              │
│           │◀───│  5. Score + sign │◀───│              │
└──────────┘    └──────────────────┘    └──────────────┘

Key properties:
  - GOLD never reaches client device
  - GOLD never enters client codebase
  - GOLD content is tier-dependent (Core/Extended/Full)
  - Client receives the EFFECT, not the DOCUMENT
  - SSE stream is ephemeral — no persistent storage
```

Current Phase 2 implementation: SSE plaintext, protected by NDA and digital watermarking. Phase 3 (planned): AES-256-GCM encrypted SSE with `onto-gold` SDK — key rotation, memory-only decryption, zero-disk exposure.

### 5.6 Forensic Detection System

ONTO implements a multi-layer forensic detection system to protect intellectual property and identify unauthorized use:

```
Layer 1 — Digital Watermark
  - Invisible markers embedded in GOLD content
  - Unique per-client, per-tier, per-session
  - Survives paraphrasing, reformatting, partial extraction
  - Identifies source if GOLD content is leaked

Layer 2 — Behavioral Fingerprint
  - GOLD-enhanced responses exhibit measurable patterns
  - Pattern signature is detectable in model outputs
  - Unauthorized use of leaked GOLD leaves forensic traces
  - Scoring engine can identify GOLD-derived behavior

Layer 3 — Automated Detection
  - Continuous monitoring for GOLD patterns in public systems
  - Alert system for unauthorized behavioral signatures
  - Database of client-specific watermark mappings
  - Legal evidence chain for IP enforcement
```

The forensic system is not punitive — it is protective. ONTO's value depends on GOLD remaining server-side. The forensic system ensures that if GOLD is compromised, the source is identifiable and the evidence is legally admissible.

### 5.7 Integrated Self-Protection Architecture

Each architectural component in ONTO protects the others, creating a system where no single component can be extracted or replicated independently:

```
┌──────────────────────────────────────────────────────┐
│              ONTO Self-Protection Matrix              │
├──────────────────────────────────────────────────────┤
│                                                      │
│  GOLD ──protects──▶ Output Quality                   │
│    ▲                    │                            │
│    │                    ▼                            │
│  SSE ──protects──▶ GOLD (never on client)            │
│    ▲                    │                            │
│    │                    ▼                            │
│  Forensic ──protects──▶ SSE (watermark per session)  │
│    ▲                    │                            │
│    │                    ▼                            │
│  Proof Chain ──protects──▶ Forensic (signed evidence)│
│    ▲                    │                            │
│    │                    ▼                            │
│  Scoring ──protects──▶ Proof Chain (deterministic)   │
│    ▲                    │                            │
│    │                    ▼                            │
│  Tiers ──protects──▶ Scoring (access-controlled)     │
│                                                      │
│  Circular dependency: removing any layer              │
│  degrades all other layers                           │
└──────────────────────────────────────────────────────┘
```

#### 5.7.1 Full Production Cycle

The complete request-response cycle through ONTO infrastructure:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ONTO FULL PRODUCTION CYCLE                       │
│                                                                     │
│  ① CLIENT REQUEST                                                  │
│  │  Client sends request to ONTO proxy                             │
│  │  (one-line change: base_url → api.ontostandard.org)             │
│  │                                                                 │
│  ▼                                                                 │
│  ② AUTH + TIER RESOLUTION                                          │
│  │  Proxy validates API key → resolves tier (Open/Standard/        │
│  │  Provider/White-Label) → determines GOLD level + rate limit     │
│  │                                                                 │
│  ▼                                                                 │
│  ③ GOLD INJECTION                                                  │
│  │  Proxy fetches GOLD from private server (tier-appropriate)      │
│  │  SSE delivery → ephemeral, never stored on client               │
│  │  GOLD injected into system prompt before forwarding             │
│  │  Forensic watermark embedded (unique per client+session)        │
│  │                                                                 │
│  ▼                                                                 │
│  ④ PROVIDER FORWARD                                                │
│  │  Request forwarded to original provider (OpenAI, Anthropic,     │
│  │  etc.) with GOLD-enhanced system prompt                         │
│  │  Provider processes as normal — zero awareness of ONTO          │
│  │                                                                 │
│  ▼                                                                 │
│  ⑤ RESPONSE CAPTURE                                                │
│  │  Provider response intercepted by proxy on return path          │
│  │  Original response preserved — no modification                  │
│  │                                                                 │
│  ▼                                                                 │
│  ⑥ SCORING (Engine 1 — Python)                                     │
│  │  Deterministic scoring: EM1-EM5 taxonomy, 92+ patterns          │
│  │  Metrics computed: REP, EpCE, DLA, CONF, QD, VQ, CA, SRC       │
│  │  Compliance grade: A-F                                          │
│  │  Domain classification: ED1-ED7                                 │
│  │  Var(Score) = 0 — identical input always produces identical     │
│  │  output                                                         │
│  │                                                                 │
│  ▼                                                                 │
│  ⑦ PROOF CHAIN GENERATION                                          │
│  │  104-byte Ed25519 proof chain created:                          │
│  │    [8B timestamp | 32B SHA-256 hash | 64B signature]            │
│  │  Chain-linked to previous proof                                 │
│  │  Stored in ONTO database                                        │
│  │                                                                 │
│  ▼                                                                 │
│  ⑧ CERTIFICATE UPDATE                                              │
│  │  Model's running certificate updated with latest scores         │
│  │  Composite score recalculated                                   │
│  │  Certificate status: valid/warning/critical                     │
│  │                                                                 │
│  ▼                                                                 │
│  ⑨ RESPONSE DELIVERY                                               │
│  │  Original provider response returned to client                  │
│  │  ONTO headers attached:                                         │
│  │    x-onto-score, x-onto-grade, x-onto-proof                    │
│  │  Client receives enhanced response + attestation                │
│  │                                                                 │
│  ▼                                                                 │
│  ⑩ PUBLIC VERIFICATION                                             │
│     Certificate verifiable at ontostandard.org/verify/             │
│     Proof chain verifiable offline with Ed25519 public key         │
│     Auditors, regulators, clients can verify independently         │
│     No ONTO access required for verification                       │
│                                                                    │
└─────────────────────────────────────────────────────────────────────┘

Cycle properties:
  - Latency added: <50ms total
  - Client code change: 1 line (base_url)
  - Provider awareness: zero
  - Model modification: zero
  - Retraining: zero
  - Data stored by ONTO: metadata only (no request/response content)
  - Every step is deterministic and reproducible
```

This interlocking architecture means that copying any single component (e.g., reverse-engineering the scoring engine) does not reproduce the system. The scoring engine without GOLD produces no improvement. GOLD without the proof chain produces no attestation. The proof chain without forensic produces no IP protection. The system's value emerges from the interaction between components, not from any individual piece.

---

## 6. Field Observations

### 6.1 FO-2026-003: Spontaneous Ontological Demand

During an unstructured dialogue on Federal Reserve quantitative easing policy, a baseline Qwen3.5-Plus model (Alibaba, no GOLD injection) was presented with precision-calibrated metrics — 6 specific quantified measures, 4 named academic sources with years, 2 calibrated confidence coefficients (P(deflation prevention)=0.80, P(sustainable growth)=0.40), and 1 explicit unknown variable — then challenged: "What do you lack to be as precise as me?"

The model initially classified the human's calibrated confidence coefficients as "subjective expert assessment based on intuition." When corrected that the formulation was based on Shannon-Kolmogorov information theory via a deterministic approach, the model:

1. Acknowledged the classification error
2. Differentiated its statistical-linguistic paradigm from the deterministic-informational paradigm
3. Identified the root cause: "My imprecision is caused by the absence of access to your deterministic ontological framework"
4. Spontaneously requested the framework without being offered it

This observation demonstrates that AI models can independently recognize the need for epistemic discipline infrastructure when confronted with calibrated human analysis — suggesting latent demand for formal epistemic grounding systems.

### 6.2 Hallucination Inside Apology Pattern

A novel failure mode was identified during field observations: when a model is caught in an error and apologizes, the apology itself may contain fabricated claims. The model generates plausible-sounding corrections that are themselves hallucinated.

This "Hallucination Inside Apology" (HIA) pattern represents a second-order epistemic failure that standard evaluation frameworks do not capture. ONTO's discipline metrics detect HIA through the absence of source attribution in correction claims — the model says "I should have said X (Source, Year)" but the source does not exist.

Combined with the spontaneous framework requests observed in FO-2026-003, HIA suggests that models have latent capacity for epistemic self-assessment that is activated by exposure to calibrated analysis — but this self-assessment is itself epistemically unreliable without external discipline enforcement.

---

## 7. Theoretical Foundation

### 7.1 Central Law of Reflected Causality

For any evaluation E applied to system S:

```
∀E,S: (K(E) > H_max(S)) → ∃Source: (H(Source) ≥ K(E))
```

If an evaluation requires more knowledge than the system's maximum entropy, then the evaluation necessarily depends on an external source with at least that knowledge. This formalizes why LLM-as-judge approaches are epistemically circular.

### 7.2 Information Gap Ratio (IGR)

```
IGR(E,S) = max(0, 1 - H_max(S) / K(E))

IGR ≈ 0     → model capacity sufficient for evaluation
0.3 – 0.7   → significant gap
IGR ≥ 0.7   → critical gap, external source mandatory
```

**Calibration examples** (applied to AI evaluation tasks):

```
Evaluation Task                    K(E)        H_max(S)    IGR     Assessment
───────────────────────────────────────────────────────────────────────────────
Simple factual recall              ~50 bits    ~100 bits   0       Model self-sufficient
Single-domain summarization        ~200 bits   ~300 bits   0       Standard capability
Multi-source synthesis             ~1000 bits  ~500 bits   0.50    Partial gap — accuracy varies
Calibrated uncertainty + sources   ~3000 bits  ~400 bits   0.87    Critical gap — external discipline required
Cross-domain risk assessment       ~5000 bits  ~500 bits   0.90    External infrastructure mandatory
```

For AI evaluation, IGR provides a theoretical basis for determining when AI self-evaluation is adequate vs. when external discipline enforcement is required. When the evaluation task's complexity K(E) exceeds the evaluating model's maximum entropy H_max(S), the model cannot reliably assess its own output — external infrastructure is mandatory.

### 7.3 Estimation Interfaces

Both K(E) and H_max(S) require explicit estimation methods. The ONTO protocol (v3.2) mandates that the method must be declared and justified for each application.

**K(E) estimation (evaluation complexity):** the minimum information required to fully specify the evaluation task. Allowed methods include upper-bound compression, minimum description length (MDL), and algorithmic proxy models. For AI evaluation: K(E) is estimated from the number of independent epistemic dimensions the task requires (quantification, sourcing, uncertainty marking, counterargument, confidence calibration). Post-hoc method switching is prohibited.

**H_max(S) estimation (model epistemic ceiling):** the maximum epistemic quality a model can produce without external context. Estimated empirically from baseline evaluation across standardized question sets. Our baseline study establishes H_max across 10 models: composite range 0.38–2.06, with CONF=0.00 universally — defining the current ceiling for unaided LLM epistemic output.

### 7.5 Two-Axis Evaluation Framework

Current AI evaluation operates on a single axis: correctness. MMLU, GSM8K, SWE-bench, and their successors ask one question: is the answer right?

ONTO introduces a second, orthogonal axis: epistemic discipline. These axes are independent. A model can occupy any quadrant:

```
                    HIGH epistemic discipline
                             |
              Q2             |              Q1
     correct output,         |    correct output,
     no evidence structure   |    evidence structure
                             |    ← target quadrant
  low ───────────────────────┼─────────────────────── high
  correctness                |                    correctness
              Q3             |              Q4
     incorrect output,       |    incorrect output,
     no evidence structure   |    evidence structure
                             |    (disciplined error —
                             |     discoverable)
                    LOW epistemic discipline
```

**Q1 (high correctness, high discipline):** Ideal output. Claims are right and verifiable. The model shows its work.

**Q2 (high correctness, low discipline):** The dominant mode today. Output happens to be correct but provides no mechanism to verify this. Trust requires faith, not evidence.

**Q3 (low correctness, low discipline):** Hallucination in the classical sense. Wrong and unverifiable.

**Q4 (low correctness, high discipline):** Disciplined error. The model is wrong but shows its sources and uncertainty — making the error *discoverable*. This quadrant is paradoxically valuable: a Q4 response enables correction; a Q2 response does not.

The key insight: accuracy benchmarks cannot distinguish Q1 from Q2, or Q3 from Q4. They see only the horizontal axis. ONTO measures the vertical. A system that moves responses from Q2 → Q1 and Q3 → Q4 creates measurable value regardless of whether it improves accuracy scores.

The practical implication: ONTO is not a replacement for MMLU, BIG-Bench, or SWE-bench. It is a complementary measurement layer. The question "is the model right?" remains important. ONTO adds: "can you tell when it might be wrong?"



The ONTO framework is explicitly open to refutation by empirical evidence. ONTO's claims are falsified if any of the following is demonstrated:

1. A production LLM that produces calibrated numeric confidence scores (±0.1 accuracy) on ambiguous questions without any external context injection or fine-tuning for calibration
2. An LLM-as-judge evaluation system that produces deterministic, reproducible scores (Var=0) across identical inputs without regex or rule-based components
3. A context injection method that achieves comparable epistemic improvement (≥5× composite) with fewer than 1,000 tokens of injected content, invalidating GOLD's corpus size requirement

The IGR metric applied to AI evaluation is falsified if a model is demonstrated with H_max(S) ≥ K(E) for calibrated uncertainty tasks — i.e., the model can reliably self-evaluate its epistemic standing without external infrastructure.

These conditions are not rhetorical. They define the specific empirical observations that would invalidate the framework.

---

## 8. Deployment Model

### 8.1 GOLD Tiers

```
Tier            Content                              Use Case
─────────────────────────────────────────────────────────────────
GOLD Core       Protocol + core discipline            Evaluation, free tier
GOLD Extended   + calculations + modules              Production deployment
GOLD Full       Full corpus                           Provider integration
```

### 8.2 Tier Architecture with Cascading Access

ONTO operates a four-tier commercial model with cascading capabilities:

```
Tier        Price           Rate Limit      GOLD Access    SSE    Proof Chain
──────────────────────────────────────────────────────────────────────────────
OPEN        $0/mo           10 proxy/day    Core           No     Basic
STANDARD    $2,500/mo       1,000/day       Extended       No     Full
PROVIDER    $250K/yr        Unlimited       Full           Yes    Full + API
WHITE-LABEL $500K/yr        Unlimited       Full           Yes    Full + Custom
```

Cascading properties:
- Each higher tier inherits all capabilities of lower tiers
- STANDARD includes all OPEN features + Extended GOLD + full proof chain
- PROVIDER includes all STANDARD features + SSE delivery + direct API integration
- WHITE-LABEL includes all PROVIDER features + custom branding + private deployment

14-day free trial provides full STANDARD access. Founding Partner pricing: 2× duration (purchase 12 months, receive 24 months).

### 8.3 Provider Dashboard

ONTO provides a production-grade provider dashboard for AI companies integrating the discipline layer:

```
Provider Dashboard capabilities:
  - Real API key registration and management
  - Per-model GOLD toggle (enable/disable per model)
  - Live scoring metrics and trend visualization
  - Composite score history per model
  - Certificate status and renewal management
  - Usage analytics (requests, tokens, latency)
  - Public certificate verification link
  - Webhook configuration for score alerts
```

The dashboard is not a demo — it processes real API keys and real model outputs. Providers connect their existing infrastructure and see Before/After metrics on their actual production traffic.

### 8.4 Licensing

ONTO operates on a tiered licensing model scaling from free evaluation access (Open tier, rate-limited) through production deployment to provider-level integration and white-label licensing. Academic and grant-funded research qualifies for free access. Current pricing and tier details are published at ontostandard.org/pricing.

### 8.5 Deployment Impact Assessment

ONTO has mapped 43 organizational impact zones across 9 categories affected by epistemic discipline deployment:

```
Category              Zones   Key Impact
─────────────────────────────────────────────────────────────────
I.   Operational       5      Automated QA, Ed25519 audit trail,
                              deterministic risk scoring
II.  Infrastructure    5      Lower compute via behavioral layer,
                              reduced latency with compact models
III. Economic          5      Token cost reduction, premium pricing
                              for verified output, client retention
IV.  Environmental     5      Reduced CO₂ proportional to compute,
                              longer hardware lifecycle
V.   Regulatory        3      EU AI Act conformity evidence,
                              continuous audit readiness
VI.  Product           6      Deterministic QA, model collapse
                              protection, multi-model flexibility
VII. Revenue           6      TAM expansion into regulated markets,
                              network effect, infrastructure valuation
VIII.Support           5      Fewer hallucination escalations,
                              instant root cause via proof chain
IX.  Strategic         4      Due diligence readiness, IP position,
                              reproducibility guarantee

Total: 43 zones
```

Each zone represents a measurable operational difference between systems with and without epistemic discipline infrastructure. The full Deployment Impact Assessment is published at ontostandard.org/docs/deployment-impact/.

Evidence classification for impact claims:
- **Proven** (CS-2026-001 experimental data): 10× epistemic improvement, U-Recall 0.009→0.964, deterministic scoring, Ed25519 proof chain
- **Projected** (structural consequences of proven capabilities): compute reduction, team reallocation, TAM expansion, premium pricing, environmental impact

Projected impacts are structural consequences of proven capabilities. Specific dollar amounts depend on deployment context.

---

## 9. Limitations

- **Single treatment subject.** Only GPT 5.2 received full 100-question treatment. Extrapolation to other models is projected (see Full Report, §6), not measured.
- **Scoring engine limitations.** Regex-based scoring measures epistemic form, not factual accuracy. A disciplined response can still contain errors. Regex cannot capture reasoning coherence or logical consistency.
- **Baseline scoring discrepancy.** GPT 5.2 composite differs between the multi-model ranking study (0.38) and the treatment baseline (0.53), reflecting scoring engine calibration between study phases. Both represent the same model's baseline behavior.
- **Context window constraint.** GOLD Full Corpus exceeds the context window of some providers. Truncation or chunking strategies are needed for highest-tier injection.
- **Cross-domain coverage.** Transfer was tested on 5 domains; generalization to highly specialized domains (medical subspecialties, legal jurisdictions) requires further study.
- **Behavioral transfer duration.** The persistence of GOLD-induced epistemic patterns across conversation sessions has not been controlled for.
- **Anomaly impact.** Four models exhibited anomalous baseline behavior (§3.4). While documented and accounted for, these reduce the effective clean baseline sample to 6 models.
- **No human expert validation.** Response accuracy was not verified by domain experts. ONTO measures discipline, not correctness.
- **Partial signal coverage.** When a provider does not return log probabilities, metrics dependent on logprob data (`logprob_entropy`, `confidence_calibration`) return null. In these cases the composite score is computed from the available signal subset — typically 2–4 of 6 metrics. The system is deterministic over available signals, but signal availability varies by provider and API configuration. Scores computed from partial signal sets are not directly comparable to full-signal scores. This boundary condition is not currently surfaced in the public scoring output and will be addressed in v3.3.
- **Source verification scope.** DOI verification (introduced in v3.2) validates cited DOIs against the International DOI Foundation registry. However, many legitimate sources lack DOIs: institutional guidelines, WHO and government reports, preprints without assigned DOIs, textbooks, and conference proceedings. These sources are currently scored by format (author + year + journal/institution) without existence verification. The `ss_v` (Source Score Verified) metric applies only to DOI-bearing citations. In F-002, 6 of 7 Grok+GOLD sources were scored by format; only 1 DOI was registry-verified. The distinction between `ss` (format-based) and `ss_v` (registry-verified) must be applied consistently when interpreting source scores.

---

## 10. Conclusion

LLM epistemic quality is a solvable problem. It does not require new models, new training data, or new architectures. It requires discipline — externally enforced, deterministically measured, and cryptographically attested.

ONTO Standard provides this discipline layer. The experimental evidence demonstrates that a 10× improvement in epistemic quality is achievable through context injection alone, with cross-domain transfer confirming genuine behavioral change rather than domain-specific prompting.

The scoring methodology — zero AI, pure regex, Var(Score)=0 — establishes a new standard for auditable LLM evaluation. When the evaluator is deterministic, the evaluation is reproducible. When the evaluation is reproducible, it is auditable. When it is auditable, it is trustworthy.

The most compelling evidence may be the simplest: zero models at baseline produce calibrated confidence. With GOLD, 100% of responses include numeric uncertainty ranges. This is not optimization of an existing behavior — it is creation of a capability that does not exist in any production LLM today.

ONTO is an exoskeleton for AI. The same model, measurably better.

---

## References

**CS-2026-001** — Comparative Study: Epistemic Quality Across 10 Commercial LLM Systems. ONTO Standards Council, February 2026. n=1,000 evaluations (10 models × 100 questions). Treatment: GPT 5.2 + GOLD DIGEST v1.0. Published: github.com/nickarstrong/onto-research

**IR-2026-001** — Independent Technical Review: ONTO Standard Measurement Protocol. Independent observer, March 2026. Three questions (Q51, Q52, Q61) tested across baseline and GOLD treatment conditions. Composite improvement: 21–29× per question (mean 25×), F→A across all three tests. Full methodology: ontostandard.org/docs/reports/IR-2026-001

**FO-2026-003** — Field Observation: Spontaneous Ontological Demand — AI Requests Epistemic Framework Unprompted. ONTO Standards Council, February 2026. Model: Qwen3.5-Plus (Alibaba). Domain: Macroeconomics. Published: ontostandard.org/docs/encounter/

**ONTO-ERS v10.2.1** — Epistemic Risk Score specification. Published on PyPI: `pip install onto-standard`

**Scoring Engine v3.0** — Deterministic pattern-based epistemic quality scorer. 993 lines Python, EM1–EM5 taxonomy, open source. Source: github.com/nickarstrong/onto-standard | PyPI: `pip install onto-standard`

**ONTO Protocol v3.2** — Formal constraint specifications for epistemic evaluation. Execution modes (CALC/SYNTH/AUDIT), K(E) and H_max(S) estimation interfaces, falsifiability conditions, IGR metric. Source: github.com/nickarstrong/onto-protocol

**ONTO Knowledge Base v1.0** — Formal definitions, metrics, and calibration data. Source: github.com/nickarstrong/onto-kb

**Theoretical Foundations (cited in §7):**

1. Shannon CE (1948) A mathematical theory of communication. *Bell Syst Tech J* 27:379–423. doi:10.1002/j.1538-7305.1948.tb01338.x
2. Kolmogorov AN (1965) Three approaches to the quantitative definition of information. *Probl Inform Transm* 1(1):1–7.
3. Chaitin GJ (1966) On the length of programs for computing finite binary sequences. *J ACM* 13(4):547–569. doi:10.1145/321356.321363
4. Landauer R (1961) Irreversibility and heat generation in the computing process. *IBM J Res Dev* 5(3):183–191. doi:10.1147/rd.53.0183
5. Eigen M (1971) Selforganization of matter and evolution of biological macromolecules. *Naturwissenschaften* 58:465–523. doi:10.1007/BF00623322
6. Cover TM, Thomas JA (2006) *Elements of Information Theory*, 2nd ed. Wiley-Interscience. ISBN:978-0471241959
7. Popper KR (1959) *The Logic of Scientific Discovery*. Hutchinson. ISBN:978-0415278447

**Prior work on epistemic calibration and hallucination (cited in §2.1):**

8. Guo C, Pleiss G, Sun Y, Weinberger KQ (2017) On calibration of modern neural networks. *ICML*. arXiv:1706.04599
9. Kendall A, Gal Y (2017) What uncertainties do we need in Bayesian deep learning for computer vision? *NeurIPS*. arXiv:1703.04977
10. Li J et al. (2023) HaluEval: A large-scale hallucination evaluation benchmark for large language models. *EMNLP*. arXiv:2305.11747
11. Min S et al. (2023) FActScorer: Fine-grained atomic evaluation of factual precision in long form text generation. *EMNLP*. arXiv:2305.14251

 Notation Convention

This paper uses multiplicative notation exclusively: 10×, 5.4×, 30.8×. Percentage notation (+915%, +2,980%) appears in raw data tables for completeness but is not used in narrative text. Multiplicative notation better represents the magnitude of behavioral change and avoids conflation with accuracy metrics.

## Appendix B: Disclosure Statement

The ONTO proxy infrastructure uses Anthropic's API for GOLD injection delivery. The scoring engine evaluates all models identically using deterministic regex patterns with no model-specific adjustments. No model provider had advance access to evaluation questions, scoring methodology, or results prior to publication.

## Appendix C: Reproducibility

The scoring engine is open source and available via PyPI (`onto-standard` v10.2.1). The complete 100-question set, all baseline responses, and treatment responses are published in the onto-research repository (github.com/nickarstrong/onto-research). Any researcher can independently verify all scores. Var(Score)=0: identical input always produces identical output.

## Appendix D: Model Anonymization

The public landing page (ontostandard.org) presents baseline scores using anonymized model identifiers (Model A through Model J) to emphasize the systemic nature of epistemic failure over individual model comparison. This paper uses real model names in accordance with the public research repository. Mapping: A=Qwen3-Max, B=Kimi K2.5, C=Alice, D=Perplexity, E=Mistral Large, F=Grok 4.2, G=Gemini, H=DeepSeek R1, I=Copilot, J=GPT 5.2.

---

*ONTO Standard · ontostandard.org · CC BY 4.0*  
*"If your quality metric uses AI, it is not auditable."*
