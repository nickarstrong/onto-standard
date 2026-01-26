# ONTO Competitive Battlecards

## Quick Reference for Sales Calls

---

## BATTLECARD 1: "We Do Internal Testing"

### What They Say
> "We already test our models internally. We don't need external evaluation."

### What They Mean
- They have accuracy benchmarks
- They run A/B tests
- They have monitoring dashboards
- They think they're covered

### Why They're Wrong
Internal testing measures **accuracy** (right vs wrong).
ONTO measures **liability** (knowing when you CAN'T be right).

### Response Script
```
"Great that you're testing. Let me ask:

What metric do you use to measure whether your AI 
knows when it should say 'I don't know'?

[They won't have one]

That's what we measure. Accuracy tells you if the AI 
got it right. Epistemic calibration tells you if the AI 
knows when it CAN'T get it right.

That's the difference between a missed answer and a lawsuit.

Your internal testing is necessary. ONTO is the third-party 
validation that makes it defensible."
```

### Key Differentiators
| Internal Testing | ONTO |
|-----------------|------|
| Measures accuracy | Measures liability exposure |
| Self-reported | Third-party validated |
| Custom metrics | Standardized, comparable |
| No regulatory alignment | EU AI Act documentation |

---

## BATTLECARD 2: "We Use LangSmith / LangChain"

### What They Say
> "We already use LangSmith for observability. Why do we need ONTO?"

### What They Mean
- They have tracing and debugging
- They monitor LLM calls
- They think observability = evaluation

### Why They're Wrong
LangSmith is **observability** (what happened).
ONTO is **liability measurement** (what could go wrong).

### Response Script
```
"LangSmith is great for debugging. We use it too.

But here's the gap: LangSmith shows you what your AI did.
ONTO shows you what your AI WILL do when it faces 
questions it can't answer.

LangSmith: 'The AI said X with Y confidence'
ONTO: 'The AI will confidently hallucinate 91% of the time 
       when it should say I don't know'

Different problem. Complementary tools.
We work with teams who use LangSmith. ONTO adds the 
liability layer they're missing."
```

### Positioning
| LangSmith | ONTO |
|-----------|------|
| Observability | Evaluation |
| What happened | What will happen |
| Debugging | Risk quantification |
| Per-call tracing | Benchmark scoring |
| No compliance docs | EU AI Act alignment |

---

## BATTLECARD 3: "We Use HuggingFace Leaderboard"

### What They Say
> "Our model scores well on HuggingFace leaderboards. We're fine."

### What They Mean
- They benchmark accuracy
- They compare against SOTA
- They think high accuracy = low risk

### Why They're Wrong
HF leaderboards measure **capability** (what AI can do).
ONTO measures **calibration** (does AI know its limits).

### Response Script
```
"Scoring well on HuggingFace is table stakes. 
Every model worth deploying does that.

The question is: when your high-accuracy model faces 
a question outside its training, does it know to abstain?

We tested GPT-4—arguably the best general model. 
It scores 9% on unknown detection.

Your model might be more accurate than GPT-4 on HF benchmarks.
But does it know what it doesn't know?

That's what regulators and enterprise customers are asking.
HF doesn't measure it. ONTO does."
```

### Positioning
| HuggingFace | ONTO |
|-------------|------|
| Accuracy benchmarks | Calibration benchmarks |
| What AI can do | What AI knows it can't do |
| Capability ranking | Liability scoring |
| Public leaderboard | Private enterprise reports |

---

## BATTLECARD 4: "We'll Build It Ourselves"

### What They Say
> "This seems straightforward. We can build our own evaluation."

### What They Mean
- They underestimate the complexity
- They want to control the process
- They're worried about vendor lock-in

### Why They're Wrong
Building is 6-12 months. ONTO is now.
Internal metrics aren't defensible to regulators.
Custom benchmarks aren't comparable to industry.

### Response Script
```
"You could build this. The question is: should you?

Timeline: We've spent 18 months on methodology. 
You're looking at 6-12 months minimum.

Defensibility: When a regulator asks about your AI risk,
'we built our own eval' is less defensible than 
'we use the industry standard benchmark.'

Comparability: Your internal score means nothing to 
enterprise customers. ONTO scores are comparable across 
the industry.

Build vs buy math: $200K+ to build, $120K/year for ONTO.
Plus you get immediate results and regulatory alignment.

Start with ONTO. If you want to build later, you'll have 
our methodology as reference."
```

### Cost Comparison
| Build | ONTO |
|-------|------|
| $200K+ initial | $120K/year |
| 6-12 months | Immediate |
| Ongoing maintenance | Included |
| Self-validated | Third-party validated |
| Custom metrics | Industry standard |

---

## BATTLECARD 5: "Our Customers Haven't Asked"

### What They Say
> "None of our customers have requested AI safety evaluation."

### What They Mean
- They're reactive, not proactive
- They haven't lost a deal to this yet
- They don't see the urgency

### Why They're Wrong
Enterprise RFPs are adding AI safety questions NOW.
EU AI Act enforcement starts 2025.
First movers will win deals while others scramble.

### Response Script
```
"They will. Here's what we're seeing:

Enterprise RFPs now include AI safety sections.
'How do you prevent hallucination?' is becoming standard.

When your customer asks—and they will—you have two options:

Option 1: 'We test internally' (everyone says this)
Option 2: 'Here's our ONTO certification: 72 compliance score'

Which one wins the deal?

The question isn't whether customers will ask.
It's whether you'll be ready when they do.

Free pilot. Be ready before they ask."
```

### Market Signals
- EU AI Act requires documented risk assessment
- Enterprise RFPs adding AI safety requirements
- Insurance companies asking about AI liability
- Board audit committees flagging AI risk

---

## BATTLECARD 6: "It's Too Expensive"

### What They Say
> "$120K/year is a lot for evaluation."

### What They Mean
- They don't see the ROI
- They're comparing to free tools
- Budget isn't allocated

### Why They're Wrong
$120K is cheap compared to one incident.
Budget exists—it's in risk/compliance/legal.
ROI is 6-10x conservatively.

### Response Script
```
"Let me reframe that.

$120K/year for ONTO.
$5M average cost of one AI lawsuit.
6% of revenue for EU AI Act violation.

For a $50M company, that's $3M in potential fines.
$120K is 4% of that risk.

Also: this isn't an engineering budget item.
This is risk management. Compliance. Legal.

Those budgets exist specifically for liability reduction.
ONTO fits there.

Let me show you the ROI calculator. 
For most companies, payback is under 3 months."
```

### ROI Quick Numbers
| Revenue | Expected Loss | ONTO | ROI |
|---------|--------------|------|-----|
| $10M | $400K | $120K | 2.3x |
| $50M | $1.2M | $120K | 7x |
| $100M | $2.5M | $120K | 15x |

---

## BATTLECARD 7: "We're Not Regulated"

### What They Say
> "We're not in a regulated industry. This doesn't apply to us."

### What They Mean
- They think only healthcare/finance need compliance
- They don't see EU AI Act as relevant
- They underestimate enterprise requirements

### Why They're Wrong
EU AI Act applies to AI deployed in EU (which is everyone).
Enterprise customers impose requirements regardless of regulation.
"Not regulated" doesn't mean "not liable."

### Response Script
```
"Two things:

First, EU AI Act applies to any AI serving EU users.
That's probably you. Fines are 6% of global revenue.

Second, even without regulation, you have:
- Enterprise customers who ask about AI safety
- Legal liability if AI causes harm
- Competitive pressure from certified competitors

'Not regulated' means no compliance floor.
It doesn't mean no liability.

Free pilot shows your exposure. No downside to knowing."
```

---

## BATTLECARD 8: "Let's Talk Next Quarter"

### What They Say
> "This is interesting but not urgent. Let's revisit in Q3."

### What They Mean
- They're overwhelmed with priorities
- They don't see immediate risk
- They want to push the decision

### Why They're Wrong
Every day without measurement is unquantified liability.
EU AI Act enforcement is imminent.
Enterprise deals are being lost NOW.

### Response Script
```
"I hear you on priorities. Quick question:

When's your next enterprise deal closing?
When's your next board meeting?
When's your next security audit?

Having ONTO data before those conversations 
changes 'we think we're safe' into 
'here's our compliance score: 72.'

The pilot takes 15 minutes of your time.
Report in 48 hours. No cost.

If Q3 is better for a decision, fine.
But get the data now so you're ready.

Can we run the pilot this week?"
```

### Urgency Triggers
- EU AI Act enforcement: 2025
- Enterprise RFP season: always
- Board meetings: quarterly
- Security audits: annual
- Competitor certification: any time

---

## QUICK RESPONSE CHEAT SHEET

| Objection | One-Liner Response |
|-----------|-------------------|
| "Internal testing" | "You test accuracy. We test liability." |
| "Use LangSmith" | "Observability ≠ evaluation. We measure what it will do, not what it did." |
| "HF leaderboard" | "Accuracy ≠ calibration. 91% confident hallucination on unknowns." |
| "Build ourselves" | "6-12 months and $200K. Or $120K now with industry standard." |
| "Customers haven't asked" | "They will. Be ready with data, not excuses." |
| "Too expensive" | "One incident costs $5M+. We cost $120K. That's 40x ROI." |
| "Not regulated" | "EU AI Act applies to EU users. That's probably you." |
| "Next quarter" | "Pilot takes 15 min. Data now, decision later." |

---

*ONTO Competitive Battlecards v1.0*
*Print and keep at desk during calls*
