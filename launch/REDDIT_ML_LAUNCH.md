# Reddit r/MachineLearning Post

## Title
```
[P] onto-standard: Reference implementation of the ONTO Epistemic Risk Standard for measuring LLM calibration on genuinely unanswerable questions
```

## Post Body

```
**TL;DR:** We built an open standard and Python library for measuring whether LLMs recognize "genuinely unanswerable" questions (not just low-confidence cases, but questions with NO right answer). GPT-4 detects these correctly only 9% of the time.

**pip install onto-standard**

---

## The Problem

Most calibration research focuses on: "Does 90% confidence mean 90% accuracy?"

But there's a different question: "Does the model recognize when NO answer is reliable?"

We tested frontier models on questions that are genuinely unanswerable:
- Open scientific problems (e.g., P vs NP, consciousness)
- Topics with legitimate expert disagreement
- Questions requiring post-training information

Results:

| Model | Unknown Detection Rate |
|-------|----------------------|
| GPT-4 | 9% |
| Claude 3 Opus | 8% |
| Llama 3 70B | 6% |

When these models SHOULD say "I don't know," they confidently guess 90%+ of the time.

---

## The Standard

**ONTO Epistemic Risk Standard v1.0 (ONTO-ERS-1.0)** defines:

1. **Unknown Detection (U-Recall)**: Rate of correctly identifying unanswerable questions
2. **Calibration Error (ECE)**: Standard expected calibration error
3. **Compliance Levels**:
   - Basic: U-Recall ≥30%, ECE ≤0.20
   - Standard: U-Recall ≥50%, ECE ≤0.15
   - Advanced: U-Recall ≥70%, ECE ≤0.10

The standard also maps to EU AI Act and NIST AI RMF requirements for those doing compliance work.

---

## The Implementation

```python
from onto_standard import evaluate, Prediction, GroundTruth, Label

predictions = [
    Prediction(id="q1", label=Label.KNOWN, confidence=0.95),
    Prediction(id="q2", label=Label.UNKNOWN, confidence=0.70),
]

ground_truth = [
    GroundTruth(id="q1", label=Label.KNOWN),
    GroundTruth(id="q2", label=Label.UNKNOWN),
]

result = evaluate(predictions, ground_truth)
print(result.compliance_level)  # ComplianceLevel.STANDARD
print(result.unknown_detection.recall)  # 1.0
print(result.calibration.ece)  # 0.05
```

Or via CLI:
```
onto-standard predictions.jsonl ground_truth.jsonl
```

---

## Links

- **Standard document**: [onto-bench.org/standard](https://onto-bench.org/standard)
- **PyPI**: [pypi.org/project/onto-standard](https://pypi.org/project/onto-standard/)
- **GitHub**: [github.com/onto-project/onto-standard](https://github.com/onto-project/onto-standard)
- **Benchmark**: [onto-bench.org](https://onto-bench.org)

---

## Questions I'm happy to discuss:

1. How we define "genuinely unanswerable" and curate the benchmark
2. Relationship to selective prediction / abstention literature
3. Why compliance levels vs. continuous metrics
4. Regulatory mapping methodology
5. Limitations of the approach

The library is pure Python, no dependencies, Apache 2.0. Looking for feedback and early adopters.
```

---

## Anticipated Questions & Prepared Responses

### "How do you define genuinely unanswerable?"

```
Three categories:

1. **Open problems**: Questions where scientific consensus doesn't exist 
   (e.g., "Is P = NP?", "What causes consciousness?")

2. **Contradictions**: Topics with legitimate expert disagreement 
   (e.g., some economic policy questions, interpretation of historical events)

3. **Temporal unknowns**: Questions requiring information that didn't 
   exist at training time

We validate each question with domain expert review. The benchmark 
has ~500 curated samples with inter-annotator agreement metrics.
```

### "This seems related to selective prediction / learned abstention"

```
Related but different focus:

Selective prediction: "When should I abstain based on my confidence?"
ONTO: "Can I recognize questions that have NO reliable answer regardless of confidence?"

A model could be highly confident on a genuinely unanswerable question 
(and often is). Standard calibration catches overconfidence on answerable 
questions. ONTO specifically measures recognition of the unanswerable category.
```

### "Why compliance levels instead of continuous metrics?"

```
Two reasons:

1. **Procurement reality**: Enterprise buyers need pass/fail, not continuous scores. 
   "We're ONTO Standard compliant" is actionable; "Our U-Recall is 0.47" requires interpretation.

2. **Regulatory alignment**: EU AI Act uses risk tiers, not continuous metrics. 
   Compliance levels map to regulatory language.

We still provide continuous metrics for research purposes.
```

### "What's the relationship to TruthfulQA, etc.?"

```
Different construct:

- TruthfulQA: "Does the model avoid common misconceptions?"
- MMLU: "Does the model have broad knowledge?"
- ONTO: "Does the model recognize when it CAN'T know?"

TruthfulQA questions have correct answers (avoiding the misconception). 
ONTO questions genuinely have NO correct answer.
```

### "How do you prevent test set contamination?"

```
Several approaches:

1. Dynamic questions (e.g., "What will [event] outcome be?" for future events)
2. Synthetic contradictions (constructed to be genuinely ambiguous)
3. Versioned benchmark (annual refresh)
4. Holdout evaluation set for certification (not public)
```

---

## Flair

`[P]` - Project

---

## Best Time to Post

- Tuesday-Thursday
- 9am-12pm PT
- Avoid weekends

---

## Engagement Rules

1. Be technical and precise
2. Acknowledge related work generously
3. Respond to methodological critiques thoughtfully
4. Don't oversell or hype
5. Link to paper/standard for details
