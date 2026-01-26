# Twitter/X Launch Thread

## Thread (10 tweets)

### Tweet 1 (Hook)
```
GPT-4 correctly identifies "genuinely unanswerable" questions only 9% of the time.

The rest? Confident hallucination.

We built an open standard to measure this. Thread 🧵
```

### Tweet 2 (Problem)
```
The problem isn't accuracy. LLMs are increasingly accurate.

The problem is calibration: when should the model say "I don't know"?

Current LLMs almost never abstain. They guess confidently instead.
```

### Tweet 3 (Stakes)
```
Why this matters:

• Air Canada chatbot case: $800K+
• Lawyer used ChatGPT: Sanctioned
• EU AI Act fines: Up to 6% of revenue

"Confident wrong answer" is now a liability event.
```

### Tweet 4 (Solution intro)
```
Introducing: ONTO Epistemic Risk Standard v1.0

An open standard for measuring whether AI knows what it doesn't know.

Standard: onto-bench.org/standard
Implementation: pip install onto-standard
```

### Tweet 5 (Metrics)
```
Two core metrics:

1. Unknown Detection (U-Recall)
   Does it identify unanswerable questions?

2. Calibration Error (ECE)
   Does confidence match accuracy?

Both matter. Both are measurable.
```

### Tweet 6 (Compliance levels)
```
Three compliance levels:

Basic: U-Recall ≥30%, ECE ≤0.20
Standard: U-Recall ≥50%, ECE ≤0.15
Advanced: U-Recall ≥70%, ECE ≤0.10

Most frontier models fail Basic.
```

### Tweet 7 (Regulatory mapping)
```
Maps to existing frameworks:

• EU AI Act Article 9
• NIST AI RMF MEASURE function
• ISO/IEC 23894

Legal teams can cite ONTO in compliance docs.
```

### Tweet 8 (Code example)
```
Usage:

from onto_standard import evaluate
result = evaluate(predictions, ground_truth)
print(result.compliance_level)

Pure Python. No dependencies. Apache 2.0.
```

### Tweet 9 (Call to action)
```
We're looking for:

• Early adopters for certification
• Academic collaborators
• Feedback on the standard

DMs open. Or: enterprise@onto-bench.org
```

### Tweet 10 (Summary + links)
```
TL;DR:

• LLMs hallucinate 90%+ when they should say "idk"
• We built an open standard to measure this
• Regulatory-aligned, legally citable

Standard: onto-bench.org/standard
PyPI: pip install onto-standard
GitHub: github.com/onto-project/onto-standard
```

---

## Standalone Tweets (for ongoing engagement)

### Stat tweet
```
Tested frontier LLMs on "questions with no known answer."

Results:
• GPT-4: 9% correct abstention
• Claude 3: 8%
• Llama 3: 6%

91%+ of the time, they confidently make something up.

ONTO-Bench: onto-bench.org
```

### Regulatory tweet
```
EU AI Act Article 9 requires "identifying known and foreseeable risks."

If your AI confidently answers questions it can't answer, that's a foreseeable risk.

How are you documenting it?
```

### Enterprise tweet
```
Enterprise AI sales are getting stuck on a new question:

"How do you prevent hallucination?"

"We test internally" isn't cutting it anymore.

Third-party certification is becoming table stakes.
```

### Technical tweet
```
Calibration ≠ Unknown detection

Calibration: Does 90% confidence mean 90% accuracy?

Unknown detection: Does the model recognize "no one knows the answer to this"?

Both matter. Most evals measure neither.
```

---

## Hashtags (use sparingly)

```
#AIEthics #AISafety #LLM #MachineLearning #AI #NLP
#Calibration #ResponsibleAI #EUAIACT
```

---

## Best Times to Post

- Tue-Thu, 8-10am PT
- Avoid weekends
- Space thread tweets 2-3 min apart
- Quote-tweet after 24h to resurface

---

## Engagement Strategy

1. Reply to technical questions with depth
2. Share specific numbers/data
3. Acknowledge competitors fairly
4. Link to standard doc, not just product
5. Don't engage trolls
