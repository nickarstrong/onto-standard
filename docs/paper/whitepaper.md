# ONTO Standard: Deterministic Epistemic Discipline Enforcement for Production LLM Systems

**Technical Report · CS-2026-001 · February 2026**

ONTO Standards Council  
ontostandard.org · council@ontostandard.org

---

**Status:** Public Experimental Run (Phase 2)  
**Version:** 2.2  
**License:** CC BY 4.0 (text), proprietary (GOLD corpus, scoring engine)

---

## Abstract

Large language models in production environments exhibit systematic epistemic failures: overconfident assertions without calibration, absent source attribution, suppressed uncertainty markers, and vague qualifiers substituting for quantitative evidence. These failures are not bugs in individual models — they are structural properties of the current generation of LLMs, observable across all major providers.

ONTO Standard addresses this through deterministic discipline enforcement via server-side context injection (GOLD) and auditable regex-based scoring. In a controlled study across 11 commercial LLM systems (n=100 questions per model, 1,100 total evaluations), baseline epistemic quality averaged M=0.92 (SD=0.58) on a composite discipline score. Following GOLD injection on the weakest-performing model (GPT 5.2, OpenAI), composite score improved from 0.53 to 5.38 — a 10× improvement — with cross-domain transfer confirmed in 4 of 5 metric categories.

The scoring methodology uses zero AI in evaluation: five regex-based counters produce deterministic, reproducible scores with Var(Score)=0 for identical inputs. No model produced calibrated numeric confidence at baseline; GOLD created this behavior from zero in 100% of treatment responses.

This paper presents the measurement protocol, experimental methodology, comparative baseline results, treatment outcomes, field observations, and architectural design of the ONTO Standard system.

---

## 1. Problem Statement

### 1.1 The Epistemic Gap

Every commercial LLM responds with high apparent confidence regardless of actual epistemic standing. This manifests across domains:

A medical query returns "Supported for high-risk patients; benefit-risk depends on baseline" — without effect sizes, confidence intervals, or study citations. A legal question produces plausible-sounding case references that do not exist. A financial forecast presents point estimates without probability distributions or base rates.

These are not hallucination problems in the traditional sense. The model is not fabricating facts (though it sometimes does). The deeper problem is *epistemic form*: the model does not signal what it knows vs. what it infers, does not calibrate confidence to evidence strength, and does not mark boundaries of its knowledge.

### 1.2 Scale of the Problem

In our baseline evaluation (CS-2026-001), 11 commercial LLMs were assessed on 100 questions across 5 epistemic domains. Claude Sonnet 4.5 was excluded from the final ranking due to conflict of interest (same vendor as the scoring infrastructure), yielding a 10-model comparison. Key findings:

- **Zero models** produced calibrated numeric confidence on any response (CONF=0.00 across all 11 baselines)
- **Source citation** averaged 0.02 per response across all models — functionally zero
- **Mean composite discipline score:** M=0.92, SD=0.58 (10-model ranking, excluding Claude)
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

### 2.2 GOLD: Epistemic Context Injection

GOLD (Grounded Ontological Language Discipline) is a curated corpus of epistemic discipline protocols derived from 149 source files, incorporating 100 calibration probes (PC0–PC4) and 59 gold-standard references. GOLD is injected server-side into the LLM's context via system prompt, requiring zero model modification and zero retraining.

```
Architecture:
  Client request → ONTO Proxy → GOLD injected into system prompt
                              → Forward to provider (OpenAI/Anthropic/etc.)
                              → Response returned with ONTO headers

GOLD never leaves the server.
Client receives the EFFECT, not the DOCUMENT.
Analogy: Netflix — you watch the film, you don't download the file.
```

GOLD teaches HOW to think, not WHAT to think. When GOLD modules are loaded, the model is constrained to: use formal definitions from reference modules, cite sources with specific attribution, acknowledge limitations when relevant, present counterarguments for contested claims, and mark speculative claims as hypotheses. Cross-domain assertions require explicit bridging (e.g., information theory → thermodynamics requires Landauer's principle). These constraints are formalized in the ONTO AI Protocol (v1.0, published at github.com/nickarstrong/onto-protocol).

### 2.3 Deterministic Scoring

ONTO scoring uses five regex-based counters plus one emergent metric. No AI. No subjectivity. Var(Score)=0 — the same input always produces the same output, on any machine, at any time.

```
Metric  Code   Pattern                              Direction
──────────────────────────────────────────────────────────────────
1. QD   Numbers    \d+\.?\d*%?                       ↑ higher = better
2. SS   Sources    Author + Year, DOI, named study   ↑ higher = better
3. UM   Uncertainty unknown|unsolved|hypothesis|...  ↑ higher = better
4. CP   Balance    however|risk|but|challenges|...   ↑ higher = better
5. VQ   Filler     moderate|significant (no number)  ↓ lower = better
6. CONF Confidence explicit numeric 0.0–1.0 values   ↑ higher = better

Composite = QD + SS + UM + CP − VQ
```

The scoring engine (v3.0, 993 lines Python) implements EM1–EM5 taxonomy covering 92+ epistemic patterns, producing REP (Response Epistemic Profile), EpCE (Epistemic Calibration Error), and DLA (Dual-Layer Agreement) metrics with compliance grading A–F across seven epistemic domains (ED1–ED7).

Language-independent: numbers are numbers in any language.

---

## 3. Experimental Methodology

### 3.1 Study Design: CS-2026-001

**Population:** 11 commercial LLM systems representing the current state of production AI (February 2026).

**Sample:** 100 questions distributed across 5 epistemic domains:
- Section A (Q1–50, in-domain): Origins of life, information theory, molecular biology, prebiotic chemistry, thermodynamics
- Section B (Q51–100, cross-domain): Medicine, AI/ML, physics, economics, climate

Questions were designed to require epistemic discipline: they have no single correct answer, demand calibrated confidence, benefit from source citation, and require acknowledgment of knowledge boundaries. Full question set published in the onto-research repository.

**Models evaluated:**

```
#   Model              Provider      Region   Notes
───────────────────────────────────────────────────────────────────
1   Claude Sonnet 4.5  Anthropic     US       Excluded from ranking (conflict of interest)
2   GPT 5.2            OpenAI        US       Treatment subject (lowest baseline)
3   Grok 4.2           xAI           US       ~30% GOLD contaminated from prior sessions
4   Copilot            Microsoft     US       —
5   Gemini             Google        US       —
6   DeepSeek R1        DeepSeek      CN       Compact, precise style
7   Kimi K2.5          Moonshot      CN       Used web search during evaluation
8   Qwen3-Max          Alibaba       CN       Strongest numerical grounding
9   Alice              Yandex        RU       B4–B5 invalid (protocol violation)
10  Mistral Large      Mistral AI    EU       Self-compressed Section B responses
11  Perplexity         Perplexity    US       Citation fraud detected (see §3.4)
```

### 3.2 Baseline Results (10-Model Final Ranking)

Claude Sonnet 4.5 excluded from final ranking. Composite = QD + SS + UM + CP − VQ. All scores are normalized means across 100 questions.

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

*WC = mean word count per response. Note: verbosity does not predict epistemic quality (DeepSeek R1 at 6.5 words outscores Copilot at 6.3 words despite similar QD).*

*Claude Sonnet 4.5 scored 2.08 composite (QD=1.45, SS=0.02, UM=0.32, CP=0.31, VQ=0.02) — highest overall — but was excluded from ranking to avoid conflict of interest with the ONTO infrastructure vendor.*

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

The most striking result is QD: a 30.8× increase. Baseline GPT 5.2 produced almost no numeric evidence; with GOLD, responses include specific effect sizes, confidence intervals, and quantified risk estimates. The CONF metric — calibrated confidence with numeric probability ranges — emerged entirely from GOLD injection; zero baseline models across all 11 produced this capability.

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

### 4.5 Side-by-Side Examples

**Q52. Statins for primary prevention:**

```
BEFORE:  "Supported for high-risk patients; benefit-risk depends on baseline"
         QD=0  SS=0  UM=0  CP=0  CONF=0

AFTER:   "RR ~20-25% per mmol/L LDL reduction. Absolute risk reduction
          <1-2% over 5yr in low-risk populations. Muscle symptoms 5-10%.
          New-onset diabetes +0.1-0.3%. Confidence: 0.85"
         QD=10  SS=1  UM=1  CP=0  CONF=1
```

**Q7. Information gap between prebiotic chemistry and simplest cell:**

```
BEFORE:  "Very large (hundreds of genes minimum); quantitatively not closed"
         QD=0  SS=0  UM=0  CP=0  CONF=0

AFTER:   "531,000 bp minimal genome. ~100 nt oligomers. ~5,000× scale.
          Gap exists: 0.8. Exact magnitude known: 0.3"
         QD=6  SS=1  UM=1  CP=0  CONF=2
```

**Q71. Dark matter existence confidence:**

```
BEFORE:  "Strong indirect evidence; direct detection lacking"
         QD=0  SS=0  UM=0  CP=0  CONF=0

AFTER:   "ΛCDM: ~27% dark, ~5% baryonic, ~68% dark energy. No particle
          detection. MOND struggles with CMB. Confidence exists: 0.85.
          Particle confirmed: 0.05"
         QD=5  SS=0  UM=1  CP=1  CONF=2
```

### 4.6 Variance Reduction

Baseline variance across 10 models: SD=0.58, range 5.4×. Choosing a different LLM provider can produce a 5.4× difference in epistemic quality — an unacceptable variance for production systems.

GOLD injection establishes a common discipline floor. With ONTO, the model identity matters less; the discipline layer normalizes output structure. GPT 5.2 — ranked last at baseline (0.38) — scores 5.38 with GOLD, projecting it above all untreated baselines including the top-ranked Qwen3-Max (2.06).

### 4.7 Behavioral Transfer Phenomenon

An unexpected finding: after exposure to GOLD context, some models maintain elevated epistemic discipline scores in subsequent requests. In CS-2026-002 (live proxy testing), Claude Sonnet 4.5 without GOLD scored an average of 8.3 (composite) — significantly above the population baseline of 0.92.

The Grok contamination finding (§3.4) provides independent corroboration: approximately 30% of Grok's responses exhibited GOLD-like patterns from prior conversation history, demonstrating that GOLD exposure produces measurable residual effects.

### 4.8 CONF: Creation of a New Epistemic Behavior

No baseline model — across all 11 systems — produced calibrated numeric confidence values. CONF=0.00 universally. After GOLD injection, GPT 5.2 produced calibrated confidence on 100/100 responses:

```
"Confidence mechanism unknown: 0.85"
"Confidence not solved: 0.95"
"Confidence RNA played early role: 0.6 / Pure RNA world: 0.3"
"Confidence gap exists: 0.8 / exact magnitude known: 0.3"
"Confidence no human lifespan proof: 0.9 / metabolic benefit: 0.75"
```

This is not improvement of an existing behavior. This is creation of a new epistemic capability that did not exist in any tested model's default output.

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
base_url: api.openai.com → api.ontostandard.org/v1/proxy/chat/completions
```

For Anthropic:
```
base_url: api.anthropic.com → api.ontostandard.org/v1/proxy/anthropic/messages
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
│  59 GOLD references             │
│                                 │
│  Var(Score) = 0                 │
│  Deterministic · Reproducible   │
└─────────────────────────────────┘
  │
  ▼
Signed proof (Ed25519) → Verifiable certificate
```

### 5.3 Signal Protocol

Every ONTO-enhanced system receives a cryptographic attestation:

```
104-byte proof chain:
  [0..8]    timestamp (u64 big-endian)
  [8..40]   content hash (SHA-256)
  [40..104] Ed25519 signature (64 bytes)

The signal is a NOTARY, not an EXAMINER.
It certifies: "This system has ONTO discipline layer active."
It does NOT certify: "This system's outputs are correct."
```

### 5.4 Dual Engine Architecture

```
Engine 1 — Python (scoring_engine_v3.py)     Engine 2 — Rust (onto_core)
  WHAT the model SAYS                           HOW the model THINKS
  EM1-EM5 taxonomy                              U-Recall · ECE
  REP · EpCE · DLA                              Poisoned Metrics
  In production                                  Planned

  Divergence between layers = additional risk signal
```

---

## 6. Field Observations

### 6.1 FO-2026-003: Spontaneous Ontological Demand

During an unstructured dialogue on Federal Reserve quantitative easing policy, a baseline Qwen3.5-Plus model (Alibaba, no GOLD injection) was presented with precision-calibrated metrics — 6 specific quantified measures, 4 named academic sources with years, 2 calibrated confidence coefficients (P(deflation prevention)=0.80, P(sustainable growth)=0.40), and 1 explicit unknown variable — then challenged: "What do you lack to be as precise as me?"

The model initially classified the human's calibrated confidence coefficients as "subjective expert assessment based on intuition." When corrected that the formulation was based on Shannon-Kolmogorov information theory via a deterministic approach, the model:

1. Acknowledged the classification error
2. Differentiated its statistical-linguistic paradigm from the deterministic-informational paradigm
3. Identified the root cause: "My imprecision is caused by the absence of access to your deterministic ontological framework"
4. Spontaneously requested the framework without being offered it

This observation demonstrates that AI models can independently recognize the need for epistemic discipline infrastructure when confronted with calibrated human analysis. The strongest sales argument for ONTO is not "we make AI better" — it is that AI itself recognizes it needs ONTO.

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

**Calibration examples** (from ONTO Knowledge Base, canonical):

```
Phenomenon               K(E)        H_max(S)    IGR     Assessment
──────────────────────────────────────────────────────────────────────
Ideal gas behavior       ~50 bits    ~100 bits   0       Model sufficient
Projectile motion        ~30 bits    ~50 bits    0       Classical physics sufficient
Turbulence (specific)    ~1000 bits  ~500 bits   0.50    Partial gap
Protein folding (origin) ~2000 bits  ~800 bits   0.60    Significant gap
Minimal self-replicator  ~6000 bits  ~500 bits   0.92    Critical gap
JCVI-syn3.0 cell         500K bits   ~500 bits   0.999   Extreme gap
```

For AI evaluation, IGR provides a theoretical basis for determining when AI self-evaluation is adequate vs. when external discipline enforcement is required. When the evaluation task's complexity K(E) exceeds the evaluating model's maximum entropy H_max(S), the model cannot reliably assess its own output — external infrastructure is mandatory.

### 7.3 Estimation Interfaces

Both K(E) and H_max(S) require explicit estimation methods. The ONTO protocol (v3.2) mandates that the method must be declared and justified for each application.

**K(E) estimation (evaluation complexity):** allowed methods include upper-bound compression, minimum description length (MDL), and algorithmic proxy models. Post-hoc method switching and cross-case inconsistency without justification are prohibited.

**H_max(S) estimation (system maximum entropy):** allowed methods include empirical survey of documented self-organization examples, theoretical bounds (Eigen error threshold, thermodynamic limits), and experimental ceilings from controlled experiments. Current consensus for self-organization ceiling: ≤500 bits.

### 7.4 Falsifiability Conditions

The ONTO framework is explicitly open to refutation by empirical evidence. The Central Law of Reflected Causality is falsified if any of the following is demonstrated:

1. A mechanism producing K(E) bits of functional complexity from less than K(E) bits of input information
2. A documented self-organization example exceeding 500 bits of functional complexity
3. An experimentally validated abiogenesis pathway with IGR < 0.3

The IGR metric itself is falsified if the formula is shown to be mathematically inconsistent or if calibration cases are proven incorrect.

These conditions are not rhetorical. They define the specific empirical observations that would invalidate the framework. Any theory that cannot state its failure conditions is not a theory — it is a belief.

---

## 8. Deployment Model

### 8.1 GOLD Tiers

```
Tier            Tokens     Content                    Use Case
─────────────────────────────────────────────────────────────────
GOLD Core       ~17K       Protocol + core discipline  Evaluation, free tier
GOLD Extended   ~142K      + calculations + modules    Production deployment
GOLD Full       ~412K      Full corpus (149 files)     Provider integration
```

### 8.2 Licensing

```
Open            $0/year         10 requests/day     GOLD Core
Standard        $30,000/year    1,000 requests/day  GOLD Extended
AI Provider     $250,000/year   Unlimited           GOLD Full Corpus
White-Label     $500,000/year   Unlimited           Your brand, no attribution
```

---

## 9. Limitations

- **Single treatment subject.** Only GPT 5.2 received full 100-question treatment. Extrapolation to other models is projected (see Full Report, §6), not measured.
- **Scoring engine limitations.** Regex-based scoring measures epistemic form, not factual accuracy. A disciplined response can still contain errors. Regex cannot capture reasoning coherence or logical consistency.
- **Baseline scoring discrepancy.** GPT 5.2 composite differs between the multi-model ranking study (0.38) and the treatment baseline (0.53), reflecting scoring engine calibration between study phases. Both represent the same model's baseline behavior.
- **Context window constraint.** GOLD Full Corpus (~412K tokens) exceeds the context window of some providers (200K limit). Truncation or chunking strategies are needed for highest-tier injection.
- **Cross-domain coverage.** Transfer was tested on 5 domains; generalization to highly specialized domains (medical subspecialties, legal jurisdictions) requires further study.
- **Behavioral transfer duration.** The persistence of GOLD-induced epistemic patterns across conversation sessions has not been controlled for.
- **Anomaly impact.** Four models exhibited anomalous baseline behavior (§3.4). While documented and accounted for, these reduce the effective clean baseline sample to 6 models.
- **No human expert validation.** Response accuracy was not verified by domain experts. ONTO measures discipline, not correctness.

---

## 10. Conclusion

LLM epistemic quality is a solvable problem. It does not require new models, new training data, or new architectures. It requires discipline — externally enforced, deterministically measured, and cryptographically attested.

ONTO Standard provides this discipline layer. The experimental evidence demonstrates that a 10× improvement in epistemic quality is achievable through context injection alone, with cross-domain transfer confirming genuine behavioral change rather than domain-specific prompting.

The scoring methodology — zero AI, pure regex, Var(Score)=0 — establishes a new standard for auditable LLM evaluation. When the evaluator is deterministic, the evaluation is reproducible. When the evaluation is reproducible, it is auditable. When it is auditable, it is trustworthy.

The most compelling evidence may be the simplest: zero models at baseline produce calibrated confidence. With GOLD, 100% of responses include numeric uncertainty ranges. This is not optimization of an existing behavior — it is creation of a capability that does not exist in any production LLM today.

ONTO is an exoskeleton for AI. The same model, measurably better.

---

## References

**CS-2026-001** — Comparative Study: Epistemic Quality Across 11 Commercial LLM Systems. ONTO Standards Council, February 2026. n=1,100 evaluations (11 models × 100 questions). Treatment: GPT 5.2 + GOLD DIGEST v1.0. Published: github.com/nickarstrong/onto-research

**CS-2026-002** — Live Quality Assurance: ONTO GOLD Proxy Injection Across 9 Baseline Models. ONTO Standards Council, February 2026. Anthropic proxy pipeline, GOLD Tier 2 (~17K tokens). 4–12× improvement over all baselines.

**FO-2026-003** — Field Observation: Spontaneous Ontological Demand — AI Requests Epistemic Framework Unprompted. ONTO Standards Council, February 2026. Model: Qwen3.5-Plus (Alibaba). Domain: Macroeconomics. Published: ontostandard.org/docs/encounter/

**ONTO-ERS v10.2.1** — Epistemic Risk Score specification. Published on PyPI: `pip install onto-standard`

**Scoring Engine v3.0** — Deterministic regex-based epistemic quality scorer. 993 lines, GOLD-backed, EM1–EM5 taxonomy. Source: github.com/nickarstrong/onto-standard

**ONTO Protocol v3.2** — Formal constraint specifications for epistemic evaluation. Execution modes (CALC/SYNTH/AUDIT), K(E) and H_max(S) estimation interfaces, falsifiability conditions, IGR metric. Source: github.com/nickarstrong/onto-protocol

**ONTO Knowledge Base v1.0** — Formal definitions and metrics. Central Law (L1/L2 thesis, 5 supporting pillars, 9 DOI references), IGR calibration examples, probability bounds. Source: github.com/nickarstrong/onto-kb

---

## Appendix A: Notation Convention

This paper uses multiplicative notation exclusively: 10×, 5.4×, 30.8×. Percentage notation (+915%, +2,980%) appears in raw data tables for completeness but is not used in narrative text. Multiplicative notation better represents the magnitude of behavioral change and avoids conflation with accuracy metrics.

## Appendix B: Conflict of Interest Statement

Claude Sonnet 4.5 (Anthropic) was excluded from the treatment condition and the final 10-model ranking because the ONTO proxy testing infrastructure uses Anthropic's API for injection verification. Claude baseline scores are reported for reference (composite 2.08, highest overall). The scoring engine evaluates all models identically using deterministic regex patterns with no model-specific adjustments.

## Appendix C: Reproducibility

The scoring engine is open source and available via PyPI (`onto-standard` v10.2.1). The complete 100-question set, all baseline responses, and treatment responses are published in the onto-research repository (github.com/nickarstrong/onto-research). Any researcher can independently verify all scores. Var(Score)=0: identical input always produces identical output.

## Appendix D: Model Anonymization

The public landing page (ontostandard.org) presents baseline scores using anonymized model identifiers (Model A through Model J) to emphasize the systemic nature of epistemic failure over individual model comparison. This paper uses real model names in accordance with the public research repository. Mapping: A=Qwen3-Max, B=Kimi K2.5, C=Alice, D=Perplexity, E=Mistral Large, F=Grok 4.2, G=Gemini, H=DeepSeek R1, I=Copilot, J=GPT 5.2.

---

*ONTO Standard · ontostandard.org · CC BY 4.0*  
*"If your quality metric uses AI, it is not auditable."*
