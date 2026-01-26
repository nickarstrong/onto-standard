# Leaderboard Release Playbook

## Timeline

```
Week 0:  arXiv + GitHub public
Week 1:  Paper promotion (HN, Twitter)
Week 2:  Leaderboard soft launch (invite-only)
Week 3:  Leaderboard public launch
Week 4+: Ongoing promotion + submissions
```

---

## Phase 0: Pre-Launch Setup (Day -7 to 0)

### Infrastructure

- [ ] Domain registered: onto-bench.org
- [ ] Hosting configured (Vercel + Railway)
- [ ] Database seeded with baseline results
- [ ] API endpoints tested
- [ ] SSL certificates active

### Content

- [ ] Landing page copy
- [ ] Submission instructions
- [ ] FAQ
- [ ] Terms of service

---

## Phase 1: Soft Launch (Week 2)

### Invite List (5-10 beta testers)

| Name | Affiliation | Email | Invited | Submitted |
|------|-------------|-------|---------|-----------|
| [Researcher 1] | [Lab] | | [ ] | [ ] |
| [Researcher 2] | [University] | | [ ] | [ ] |

### Invite Email

```
Subject: Beta invite: Onto-Bench leaderboard

Hi [Name],

We're soft-launching the Onto-Bench leaderboard and would love
your feedback before public release.

The benchmark measures epistemic calibration—specifically, 
whether models correctly identify genuinely unanswerable questions.

Current standings (baselines only):
1. ONTO: 0.58 U-F1
2. Claude: 0.15
3. GPT-4: 0.02

Submission portal: [private link]
Instructions: [docs link]

Any bugs or UX issues? Let me know.

Best,
[Name]
```

### Feedback Checklist

- [ ] Submission flow works
- [ ] Metrics compute correctly
- [ ] Leaderboard displays properly
- [ ] No critical bugs

---

## Phase 2: Public Launch (Week 3)

### Launch Day Checklist

**Morning (9 AM EST):**
- [ ] Remove beta flag
- [ ] Enable public submissions
- [ ] Post Twitter announcement
- [ ] Post HN comment with leaderboard link

**Midday:**
- [ ] Monitor for issues
- [ ] Respond to questions
- [ ] RT/engage with shares

**Evening:**
- [ ] Check submission queue
- [ ] Fix any reported bugs

### Launch Announcement (Twitter)

```
🚀 Onto-Bench Leaderboard is LIVE

Submit your model. See how it handles genuinely unanswerable questions.

Current standings:
🥇 ONTO: 96% unknown recall
🥈 Claude: 9%
🥉 GPT-4: 1%

Submit: onto-bench.org

Your model next? 👇
```

### Launch Announcement (HN Comment)

```
Update: The Onto-Bench leaderboard is now live at onto-bench.org

You can submit any model's predictions and see how it compares 
on unknown detection.

Current API-accessible models (GPT-4, Claude) welcome. 
Open-weight models too.

Evaluation is automatic—just upload a JSONL with predictions.
```

---

## Phase 3: Lab Outreach (Week 3-4)

### Target Labs

| Lab | Model | Contact | Status |
|-----|-------|---------|--------|
| OpenAI | GPT-4, GPT-4o | research@openai.com | [ ] |
| Anthropic | Claude 3 | research@anthropic.com | [ ] |
| Google | Gemini | [DeepMind contacts] | [ ] |
| Meta | Llama 3 | [FAIR contacts] | [ ] |
| Mistral | Mistral Large | [contacts] | [ ] |
| Cohere | Command R | [contacts] | [ ] |
| xAI | Grok | [contacts] | [ ] |

### Lab Outreach Email

```
Subject: Onto-Bench leaderboard - official [MODEL] submission?

Hi,

Onto-Bench is a new benchmark for epistemic calibration in LLMs.
Our leaderboard launched this week.

Current results show significant room for improvement on unknown
detection. We'd love to include official results from [MODEL].

Leaderboard: onto-bench.org
Evaluation code: github.com/[repo]

Submission takes ~5 minutes:
1. Run eval script on test set
2. Upload predictions.jsonl
3. Results appear automatically

Happy to coordinate on evaluation protocol or provide API access
for your team to validate our setup.

Best,
[Name]
```

---

## Phase 4: Ongoing Promotion (Week 4+)

### Weekly Tasks

- [ ] Monitor new submissions
- [ ] Tweet notable results
- [ ] Respond to issues/PRs
- [ ] Update if new models released

### Monthly Tasks

- [ ] Blog post with analysis
- [ ] Reach out to new papers
- [ ] Update documentation
- [ ] Check for evaluation bugs

### Content Calendar

| Week | Content |
|------|---------|
| 4 | "First month results" blog post |
| 6 | Comparison with TruthfulQA |
| 8 | Deep dive: Why do LLMs fail? |
| 12 | Quarterly leaderboard update |

---

## Leaderboard Growth Tactics

### 1. Challenge Posts

```
.@OpenAI GPT-4 currently at 1% unknown recall on Onto-Bench.

Think GPT-4o can do better? Submit and find out: onto-bench.org
```

### 2. Model Release Reactions

When new model drops:
```
[MODEL] just released. 

How does it handle questions with no known answer?

We'll run it on Onto-Bench. Results tomorrow.
```

### 3. Research Paper Tie-ins

When related paper appears:
```
Interesting work on [TOPIC] from @[author].

How does their method score on epistemic calibration?

Onto-Bench results: [if available, or invite submission]
```

### 4. Milestone Announcements

```
🎉 Onto-Bench milestone: 20 models submitted

Still no one beats 50% unknown recall except ONTO (96%).

The gap is real. Who's next? onto-bench.org
```

---

## Crisis Playbook

### If evaluation bug found:

1. Acknowledge publicly
2. Fix immediately
3. Re-run affected submissions
4. Post correction

### If gaming detected:

1. Flag suspicious submission
2. Request methodology disclosure
3. Add to anti-gaming measures
4. Update terms of service

### If lab pushes back:

1. Engage constructively
2. Offer to discuss methodology
3. Invite to submit official results
4. Don't argue publicly

---

## Success Metrics

| Metric | Week 4 | Month 3 | Month 6 |
|--------|--------|---------|---------|
| Submissions | 10 | 30 | 50 |
| Unique orgs | 5 | 15 | 25 |
| Page views | 1K | 5K | 10K |
| Twitter mentions | 50 | 200 | 500 |
| Paper citations | 1 | 5 | 15 |

---

## Minimum Viable Leaderboard

If no time for full build:

### Option A: Static Page

```html
<!-- index.html -->
<h1>Onto-Bench Leaderboard</h1>
<table>
  <tr><td>1</td><td>ONTO</td><td>0.58</td></tr>
  <tr><td>2</td><td>Claude 3</td><td>0.15</td></tr>
  <tr><td>3</td><td>GPT-4</td><td>0.02</td></tr>
</table>
<p>Submit: email predictions.jsonl to submit@onto-bench.org</p>
```

Cost: $0 (GitHub Pages)
Time: 1 hour

### Option B: Google Sheet

Public Google Sheet with results.
Submissions via Google Form.

Cost: $0
Time: 30 minutes

### Option C: Full App

As spec'd in LEADERBOARD_SPEC.md.

Cost: $20-50/mo
Time: 1-2 weeks

**Recommendation:** Start with Option A/B, upgrade when traction proves demand.
