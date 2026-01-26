# Citation Seeding Strategy

## Goal

Get 10+ citations in first 6 months. Force inclusion in calibration/uncertainty literature.

---

## Phase 1: Direct Outreach (Week 1-2)

### Target Authors

Find papers on:
- LLM calibration
- Hallucination detection  
- Uncertainty quantification
- Knowledge boundaries
- Epistemic AI

### Search Queries

```
arxiv: "LLM calibration" 2023-2024
arxiv: "hallucination detection" 2023-2024
arxiv: "uncertainty quantification language models"
scholar: "epistemic uncertainty neural networks"
semantic scholar: "confidence calibration transformers"
```

### Target Papers (Examples)

| Paper | Authors | Relevance | Action |
|-------|---------|-----------|--------|
| "Language Models (Mostly) Know What They Know" | Kadavath et al. | Direct competitor | Email, compare |
| "Semantic Uncertainty" | Kuhn et al. | Uncertainty method | Cite them, email |
| "TruthfulQA" | Lin et al. | Benchmark | Position as complement |
| "Calibrating Language Models" | Various | Calibration | Email with results |

### Email Template

```
Subject: New benchmark for epistemic calibration - relevant to your work on [TOPIC]

Hi [Name],

I noticed your work on [their paper]. We just released Onto-Bench, 
a benchmark specifically designed for measuring epistemic calibration 
in LLMs—particularly unknown detection.

Key finding relevant to your work: GPT-4 achieves only 1% recall on 
genuinely open scientific questions, suggesting current calibration 
methods don't address epistemic boundaries.

Paper: [arXiv]
Dataset: [GitHub]

Would love your thoughts. Happy to discuss evaluation protocols 
or potential collaboration.

Best,
[Name]
```

### Outreach Tracking

| Author | Email | Sent | Response | Action |
|--------|-------|------|----------|--------|
| [Name] | [email] | [ ] | [ ] | [ ] |

---

## Phase 2: Conference Targeting (Month 1-3)

### Workshop Submissions

| Conference | Workshop | Deadline | Fit |
|------------|----------|----------|-----|
| NeurIPS 2024 | ATTRIB | ~Sep | Calibration |
| NeurIPS 2024 | SoLaR | ~Sep | Reliability |
| ICML 2024 | DMLR | ~May | Evaluation |
| ACL 2024 | TrustNLP | ~May | Trust/Safety |

### Main Track Potential

| Conference | Deadline | Submission Plan |
|------------|----------|-----------------|
| EMNLP 2024 | Jun 2024 | Extended version |
| NeurIPS 2024 | May 2024 | Position paper |
| ICLR 2025 | Oct 2024 | Full paper |

---

## Phase 3: Survey Inclusion (Month 3-6)

### Target Surveys

Monitor for upcoming surveys on:
- LLM evaluation
- AI safety benchmarks
- Calibration methods
- Hallucination mitigation

### Survey Author Outreach

```
Subject: Onto-Bench for your survey on [TOPIC]

Hi [Name],

I saw you're working on a survey covering [topic]. 

Onto-Bench might be relevant—it's the first benchmark 
with explicit epistemic labels (KNOWN/UNKNOWN/CONTRADICTION) 
for measuring unknown detection in LLMs.

Results: GPT-4 <10% unknown recall vs 96% with explicit 
epistemic structure.

Paper: [link]

Happy to provide any additional details for your survey.

Best,
[Name]
```

---

## Phase 4: Leaderboard Citations (Ongoing)

### Strategy

When labs submit to leaderboard → they cite the benchmark paper.

### Outreach to Labs

| Lab | Contact Point | Status |
|-----|---------------|--------|
| OpenAI | API team / researchers | [ ] |
| Anthropic | Research team | [ ] |
| Google DeepMind | Safety team | [ ] |
| Meta FAIR | LLM team | [ ] |
| Mistral | Research | [ ] |
| Cohere | Research | [ ] |

### Lab Email Template

```
Subject: Onto-Bench leaderboard - submit your model?

Hi [Name],

We launched Onto-Bench, a benchmark for epistemic calibration.

Current results show room for improvement on unknown detection
across all major LLMs. We'd love to include official results 
from [Lab].

Leaderboard: onto-bench.org
Evaluation code: [GitHub]

Happy to coordinate on evaluation protocol.

Best,
[Name]
```

---

## Phase 5: Media Citations (Month 2-6)

### Target Outlets

| Outlet | Contact | Angle |
|--------|---------|-------|
| MIT Tech Review | Editor | "LLMs don't know what they don't know" |
| Wired | AI reporter | Consumer AI safety |
| The Verge | AI desk | ChatGPT limitations |
| Ars Technica | Tech reporter | Technical depth |
| VentureBeat | AI beat | Enterprise implications |

### Press Release (Short)

```
FOR IMMEDIATE RELEASE

New Benchmark Shows AI Models Fail to Recognize 
Their Own Knowledge Limits

[City] - Researchers have released Onto-Bench, revealing that 
GPT-4, Claude, and other leading AI models correctly identify 
genuinely unanswerable questions less than 10% of the time.

"These systems confidently answer questions that have no known 
answer," said [Author]. "That's a fundamental safety problem."

Paper: [arXiv]
Leaderboard: onto-bench.org
```

---

## Citation Tracking

### Tools

- Google Scholar alerts for paper title
- Semantic Scholar author page
- arxiv-sanity for related papers

### Monthly Check

```
[ ] Google Scholar citation count
[ ] Semantic Scholar metrics
[ ] Papers citing Onto-Bench
[ ] Leaderboard submissions
[ ] Media mentions
```

---

## Anti-Patterns (Avoid)

1. ❌ Mass emailing without personalization
2. ❌ Asking for citations directly
3. ❌ Spamming Twitter mentions
4. ❌ Overselling results
5. ❌ Ignoring criticism

## Patterns (Do)

1. ✅ Genuine engagement with related work
2. ✅ Offer collaboration
3. ✅ Respond to all technical questions
4. ✅ Update paper based on feedback
5. ✅ Credit predecessors generously
