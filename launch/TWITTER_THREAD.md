# Twitter/X Thread Templates

## Main Thread (Technical Audience)

### Tweet 1 (Hook)
```
NEW: We tested whether GPT-4, Claude, and Llama know what they don't know.

Result: They correctly identify genuinely unanswerable questions <10% of the time.

Paper + benchmark + code 🧵👇
```

### Tweet 2 (Problem)
```
The problem: LLMs answer "What causes consciousness?" with the same confidence as "What is 2+2?"

This isn't hallucination—it's epistemic miscalibration. They lack representation of knowledge boundaries.
```

### Tweet 3 (Dataset)
```
We built Onto-Bench: 268 questions with explicit epistemic labels

• KNOWN: Established facts (speed of light, Euler's identity)
• UNKNOWN: Genuine open problems (P vs NP, dark matter)  
• CONTRADICTION: Legitimate scientific debates

Sources: Clay Math, NSF, physics surveys
```

### Tweet 4 (Results)
```
Results:

Unknown detection recall:
• ONTO: 96%
• Claude: 9%
• GPT-4: 1%
• Llama: 1%

LLMs miss >90% of genuinely open questions.
```

### Tweet 5 (Method)
```
How ONTO works: explicit epistemic structure

Instead of just storing facts, we encode:
• What is established
• What is contested  
• What is genuinely unknown

Simple idea. Dramatic improvement.
```

### Tweet 6 (Implications)
```
Why this matters:

Medical AI that confidently answers unanswerable diagnostic questions is dangerous.

Legal AI that doesn't distinguish settled law from open questions is unreliable.

Epistemic calibration isn't optional for high-stakes AI.
```

### Tweet 7 (CTA)
```
Paper: [arXiv link]
Code + data: [GitHub link]
Leaderboard (coming): onto-bench.org

Submit your model. Let's see who actually knows what they don't know.

/end
```

---

## Alt Thread (Provocative Version)

### Tweet 1
```
GPT-4 thinks it knows everything.

We tested. It doesn't.

When asked genuinely unanswerable questions, it fails to say "I don't know" 99% of the time.

Data 👇
```

### Tweet 2
```
We asked LLMs questions from:
• Clay Millennium Problems ($1M unsolved)
• "What causes consciousness?"
• "Why is there something rather than nothing?"

They confidently answered. With citations.

None of these have known answers.
```

### Tweet 3
```
This isn't cherry-picking. 

268 questions. Systematic evaluation.

GPT-4 unknown detection: 1%
Claude: 9%
Our method (ONTO): 96%

Explicit epistemic structure works.
```

### Tweet 4
```
The fix isn't "more RLHF" or "better prompting."

It's structural: encode what is NOT known alongside what is known.

Ontology > vibes.

Paper: [link]
```

---

## Quote Tweet Templates

### For sharing results:
```
Fascinating result: LLMs are confidently wrong about questions that have no answer.

Not hallucination—they genuinely can't distinguish "unknown" from "I don't know yet."

This benchmark measures it. [QT original]
```

### For engaging skeptics:
```
"But if you prompt it right..."

We tried. System prompts don't fix structural epistemic blindness.

The model lacks representation of knowledge boundaries. [QT]
```

---

## Target Accounts to Tag/Engage

### Researchers (reply, don't tag in main thread)
```
@ylaboratory (Yann LeCun)
@kaboratory (Andrej Karpathy)
@iaboratory (Ilya Sutskever)
@DrJimFan
@goodaboratoryellow (Ian Goodfellow)
```

### AI Safety / Alignment
```
@ESYudkowsky
@PaulGChristiano
@AISafetyMemes
```

### Journalists / Amplifiers
```
@willknight (Wired)
@TechEmergence
@TheAIGRID
```

---

## Timing

| Platform | Best Time (EST) | Best Day |
|----------|-----------------|----------|
| Twitter/X | 9-11 AM | Tue-Thu |
| Twitter/X | 12-2 PM | Tue-Thu |

Post paper announcement **same day** as arXiv goes live.

---

## Hashtags (use sparingly)

```
#LLM #GPT4 #Claude #AI #MachineLearning #NeurIPS
```

Max 2-3 per tweet. None in main hook.

---

## Engagement Strategy

1. **Don't argue** with critics
2. **Invite to leaderboard**: "Submit your model"
3. **Share data**: Link to specific results
4. **Acknowledge limitations**: "Fair point, we note this in Section 7"
5. **RT supporters** within first hour
