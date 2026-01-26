# Hacker News Post Templates

## Option A: Show HN (RECOMMENDED)

**Title:**
```
Show HN: Onto-Bench – LLMs detect <10% of genuinely unanswerable questions
```

**Post URL:** `https://arxiv.org/abs/XXXX.XXXXX`

**First comment (post immediately after):**
```
Author here. We built Onto-Bench to measure how well LLMs recognize what they don't know.

Key finding: GPT-4, Claude, and Llama correctly identify genuinely open scientific questions (like "Is P=NP?" or "What causes consciousness?") less than 10% of the time. They confidently answer unanswerable questions.

Our approach (ONTO) uses explicit epistemic structure—essentially encoding "what is not known" alongside facts—and achieves 96% recall on unknown detection.

Dataset: 268 questions from authoritative sources (Clay Math problems, physics surveys, etc.)

Code + data: [GitHub link]
Paper: [arXiv link]

Happy to answer questions about the methodology or results.
```

---

## Option B: Direct Link Post

**Title:**
```
LLMs fail to recognize 90%+ of genuinely unanswerable questions [pdf]
```

**URL:** `https://arxiv.org/pdf/XXXX.XXXXX.pdf`

---

## Option C: Ask HN Style

**Title:**
```
Ask HN: How should AI systems handle questions with no known answer?
```

**Body:**
```
We just released research showing GPT-4/Claude/Llama detect <10% of genuinely open scientific questions. They answer "What causes consciousness?" as confidently as "What is 2+2?"

Paper: [link]

Curious what approaches others have tried for epistemic calibration. RAG helps with factual grounding but doesn't solve the "unknown unknowns" problem.
```

---

## Timing Strategy

| Day | Time (EST) | Rationale |
|-----|------------|-----------|
| Tuesday | 9-10 AM | Peak HN traffic |
| Wednesday | 9-10 AM | Good engagement |
| Thursday | 9-10 AM | Before weekend lull |

**Avoid:** Weekends, Mondays, Fridays

---

## Response Templates

### For "Dataset too small" criticism:
```
Fair point. We prioritized label quality over scale—every "unknown" is from authoritative sources (Clay Math, NSF). Scaling with LLM-generated questions risks label noise. That said, expanding to 1K+ samples is on the roadmap.
```

### For "Just pattern matching" criticism:
```
You're right that current detection is heuristic. The contribution is demonstrating that *any* explicit epistemic structure dramatically outperforms LLMs' implicit uncertainty. Learned detectors are future work.
```

### For "Unfair baseline" criticism:
```
We tested without tools to isolate the epistemic structure contribution. Agree that RAG/tool-augmented baselines would be interesting—happy to accept submissions to the leaderboard.
```

### For "What's the practical use?" question:
```
High-stakes domains: medical diagnosis, legal advice, scientific research. Users need to know when AI is speculating vs. reporting established knowledge. Current LLMs don't distinguish.
```

---

## Engagement Rules

1. **Reply within 1 hour** of posting
2. **Be technical**, not defensive
3. **Acknowledge limitations** proactively
4. **Invite collaboration**: "PRs welcome"
5. **Don't argue**—provide data

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Points | 100+ |
| Comments | 50+ |
| Front page | Yes |
| GitHub stars from HN | 50+ |
