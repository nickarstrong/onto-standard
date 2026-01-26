# ONTO-Bench PR & Launch Strategy

## Objectives

1. **Awareness**: AI researchers know ONTO-Bench exists
2. **Adoption**: Labs submit to leaderboard
3. **Citations**: Paper gets cited in calibration/uncertainty work
4. **Pressure**: Public comparison forces improvement

---

## Phase 1: arXiv Launch (Day 0)

### Pre-Launch Checklist

- [ ] Paper finalized and proofread
- [ ] GitHub repo public with clean README
- [ ] All code tested and documented
- [ ] Dataset download working
- [ ] arXiv account ready

### Launch Day Actions

1. **arXiv submission** (morning)
   - Category: cs.CL (primary), cs.AI, cs.LG (cross-list)
   - Title: "ONTO: Epistemically-Calibrated Reasoning for Large Language Models"

2. **Twitter/X thread** (after arXiv confirmation)
   ```
   🧵 New paper: ONTO-Bench - A benchmark for epistemic calibration in LLMs
   
   Key finding: GPT-4 and Claude detect <10% of genuinely unknown questions. ONTO achieves 96%.
   
   Paper: [arXiv link]
   Code: [GitHub link]
   
   1/7 Thread 👇
   ```

3. **Hacker News post** (evening, ~6pm EST)
   - Title: "ONTO-Bench: A benchmark showing LLMs fail at knowing what they don't know"
   - Post to Show HN

4. **Reddit posts**
   - r/MachineLearning: Paper announcement
   - r/LocalLLaMA: Results on open models
   - r/artificial: General AI audience

---

## Phase 2: Community Engagement (Week 1)

### Target Communities

| Community | Platform | Approach |
|-----------|----------|----------|
| ML researchers | Twitter, arXiv | Technical discussion |
| AI safety | LessWrong, EA Forum | Epistemic uncertainty framing |
| Practitioners | Reddit, HN | Practical implications |
| Journalists | Direct outreach | Press release |

### Content Calendar

| Day | Action |
|-----|--------|
| Day 1 | arXiv, Twitter thread, HN |
| Day 2 | Reddit posts, respond to comments |
| Day 3 | Blog post with examples |
| Day 4 | Demo video (2 min) |
| Day 5 | Email newsletter mentions |
| Day 7 | Weekly roundup inclusion |

### Key Messages

1. **Hook**: "LLMs confidently answer unanswerable questions"
2. **Finding**: "96% vs 10% unknown detection"
3. **Implication**: "Epistemic structure improves calibration"
4. **CTA**: "Submit your model to the leaderboard"

---

## Phase 3: Leaderboard Launch (Week 2-3)

### Soft Launch

1. Invite 5-10 researchers to beta test
2. Seed with baseline results
3. Fix bugs, improve UX

### Public Launch

1. **Announcement**: "ONTO-Bench Leaderboard is live"
2. **Challenge**: Tag AI labs publicly
   ```
   .@OpenAI @AnthropicAI @GoogleAI @xaboratory
   
   ONTO-Bench leaderboard is live. Current standings:
   
   1. ONTO: 0.58 U-F1
   2. Claude: 0.15
   3. GPT-4: 0.02
   
   Submit your model: onto-bench.org
   ```

3. **Tracking**: Monitor submissions, update leaderboard

---

## Phase 4: Citation Building (Month 1-3)

### Target Papers

Find papers on:
- LLM calibration
- Hallucination detection
- Uncertainty quantification
- Knowledge boundaries

### Outreach Template

```
Subject: ONTO-Bench - New benchmark for your calibration work

Hi [Name],

I noticed your recent work on [topic]. We just released ONTO-Bench, 
a benchmark specifically designed for evaluating epistemic calibration 
in LLMs.

Key finding: GPT-4 achieves only 2% recall on unknown detection, 
while explicit epistemic structure achieves 96%.

Paper: [link]
Dataset: [link]

Would love your feedback. Happy to discuss evaluation protocols.

Best,
[Name]
```

### Conference Targeting

| Conference | Deadline | Fit |
|------------|----------|-----|
| NeurIPS 2024 | May 2024 | Workshop or main |
| ICML 2024 | Feb 2024 | Main track |
| ACL 2024 | Feb 2024 | Main track |
| EMNLP 2024 | June 2024 | Main track |

---

## Phase 5: Media & Press (Month 2-6)

### Press Release

```
FOR IMMEDIATE RELEASE

New Benchmark Reveals AI Models Fail at Recognizing 
Their Own Knowledge Limits

[City, Date] - Researchers have released ONTO-Bench, a new 
benchmark showing that leading AI models like GPT-4 and Claude 
correctly identify genuinely unanswered scientific questions 
less than 10% of the time.

"AI systems confidently answer questions that have no known answer,"
said [Author]. "This is a fundamental calibration problem."

The benchmark includes questions from authoritative sources including
Clay Mathematics Institute millennium problems.

Full paper: [arXiv link]
Leaderboard: onto-bench.org
```

### Media Targets

| Outlet | Contact Type | Angle |
|--------|--------------|-------|
| MIT Tech Review | Editor email | AI limitations |
| Wired | Science desk | Hallucination angle |
| The Verge | AI reporter | Consumer impact |
| Ars Technica | Tech reporter | Technical depth |
| VentureBeat | AI beat | Industry implications |

---

## Metrics & Tracking

### Success Metrics

| Metric | Week 1 | Month 1 | Month 3 |
|--------|--------|---------|---------|
| arXiv downloads | 500 | 2000 | 5000 |
| GitHub stars | 100 | 500 | 1000 |
| Twitter impressions | 50K | 200K | 500K |
| Leaderboard submissions | 5 | 20 | 50 |
| Citations | 0 | 2 | 10 |

### Tracking Tools

- arXiv: daily download stats
- GitHub: stars, forks, issues
- Twitter: Analytics dashboard
- Google Scholar: citation alerts
- Leaderboard: submission logs

---

## Risk Mitigation

### Potential Criticisms

| Criticism | Response |
|-----------|----------|
| "Dataset too small" | "Quality over quantity; authoritative sources" |
| "Heuristic detection" | "Proof of concept; future work on learning" |
| "Unfair baseline comparison" | "Matched settings; no tool augmentation" |
| "Not generalizable" | "Demonstrates principle; domain-specific extension needed" |

### Crisis Scenarios

1. **Paper rejected by arXiv**: Resubmit with minor edits, post to OpenReview
2. **Major bug found**: Issue patch, update paper, be transparent
3. **Lab pushback**: Engage constructively, invite collaboration

---

## Budget

| Item | Cost | Priority |
|------|------|----------|
| Domain (onto-bench.org) | $12/year | P0 |
| Hosting (Vercel + Railway) | $0-20/mo | P0 |
| arXiv (free) | $0 | P0 |
| Twitter Blue (optional) | $8/mo | P2 |
| PR service (optional) | $500-2000 | P3 |

**Minimum viable launch: $12**

---

## Timeline Summary

```
Week 0:  Paper finalization, repo cleanup
Day 0:   arXiv submission
Day 1:   Social media launch
Week 1:  Community engagement
Week 2:  Leaderboard beta
Week 3:  Leaderboard public launch
Month 1: Citation outreach
Month 2: Press outreach
Month 3: Conference submission
```

---

## Key Assets Needed

- [ ] Paper PDF (final)
- [ ] GitHub repo (public)
- [ ] Twitter thread draft
- [ ] HN post draft
- [ ] Blog post
- [ ] Demo video script
- [ ] Press release
- [ ] Leaderboard website
