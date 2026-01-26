# Hacker News Post

## Title Options (pick one)

**Option A (Technical):**
```
Show HN: onto-standard – Measure if your LLM knows what it doesn't know
```

**Option B (Problem-focused):**
```
Show HN: Reference implementation of the ONTO Epistemic Risk Standard
```

**Option C (Provocative):**
```
Show HN: GPT-4 detects genuinely unanswerable questions only 9% of the time
```

---

## Post Body

```
We built an open standard for measuring whether AI systems recognize the boundaries of their knowledge.

The problem: LLMs confidently answer questions they can't reliably answer. GPT-4 correctly identifies genuinely unanswerable questions only 9% of the time. The rest? Confident hallucination.

This matters because:
- EU AI Act requires documented AI risk management
- Enterprise customers want safety evidence
- One hallucination incident can cost $5M+ in lawsuits

ONTO Epistemic Risk Standard (ONTO-ERS-1.0) provides:
- Formal metrics for "unknown detection" and calibration
- Compliance levels (Basic/Standard/Advanced)
- Regulatory mapping (EU AI Act, NIST AI RMF, ISO 23894)

The reference implementation:

    pip install onto-standard

Usage:

    from onto_standard import evaluate
    result = evaluate(predictions, ground_truth)
    print(result.compliance_level)  # ComplianceLevel.STANDARD

Or CLI:

    onto-standard predictions.jsonl ground_truth.jsonl

It's pure Python, no dependencies, Apache 2.0 licensed.

Standard document: https://onto-bench.org/standard
GitHub: https://github.com/onto-project/onto-standard
PyPI: https://pypi.org/project/onto-standard/

We're looking for feedback on the standard and early adopters for certification.
```

---

## Anticipated Questions & Answers

### "How is this different from existing calibration metrics?"

```
Existing calibration metrics (ECE, Brier score) measure whether 
confidence matches accuracy. ONTO adds "unknown detection" — 
whether the model correctly identifies questions with NO right answer.

Most calibration work assumes all questions have answers. 
ONTO specifically measures the "I don't know" capability.
```

### "Why should I trust your standard?"

```
We're building institutional legitimacy:
- Standards Council with academic/industry advisors
- Open standard document (publicly citable)
- Reference implementation (Apache 2.0)
- Mapping to existing frameworks (EU AI Act, NIST)

The goal is to become a de-facto reference, like SOC2 for AI epistemic risk.
```

### "How do you define 'genuinely unanswerable'?"

```
Three categories:
1. Open problems (no scientific consensus)
2. Contradictions (legitimate expert disagreement)
3. Beyond knowledge cutoff (events after training)

We curate questions with domain expert review. 
The benchmark (ONTO-Bench) has 500+ validated samples.
```

### "What about selective prediction / abstention?"

```
Related but different. Selective prediction focuses on 
"when to abstain based on confidence."

ONTO focuses on "does the model recognize fundamentally 
unanswerable questions" — not just low-confidence cases, 
but cases where NO amount of data would give a reliable answer.
```

### "Is this just another AI safety benchmark?"

```
It's a standard, not just a benchmark. The difference:
- Benchmark: "Here's how models rank"
- Standard: "Here's what compliance means"

We provide certification levels, regulatory mapping, 
and legal citation format. Designed for procurement 
and compliance, not just research.
```

---

## Best Time to Post

- Tuesday-Thursday
- 8-10 AM ET (when US tech workers check HN)
- Avoid weekends and Mondays

---

## Engagement Strategy

1. **First hour**: Reply to every comment
2. **Be technical**: HN values depth
3. **Acknowledge limitations**: Shows intellectual honesty
4. **Link to standard doc**: For credibility
5. **Don't oversell**: Let the work speak

---

## Backup Title (if first doesn't land)

```
Ask HN: How do you measure if your LLM knows what it doesn't know?
```

(Then link to solution in comments)
