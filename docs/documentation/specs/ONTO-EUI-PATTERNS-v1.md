# ONTO Epistemic Interface Patterns

## A Design System for Cognitive Risk Communication

**Version:** 1.0  
**Status:** Reference Specification  
**Date:** January 2025  
**Document ID:** ONTO-EUI-PATTERNS-v1

---

## Abstract

This document defines a new class of user interfaces: **Epistemic Interfaces**. These interfaces do not merely display data — they transform understanding. They guide users through cognitive journeys that reshape how they perceive, evaluate, and act on AI risk.

Traditional dashboards show metrics. Epistemic interfaces create comprehension.

---

## 1. Introduction

### 1.1 The Problem with Traditional AI Risk Interfaces

Current AI risk communication interfaces suffer from fundamental design failures:

| Interface Type | Failure Mode |
|----------------|--------------|
| Dashboards | Data without context |
| Reports | Information without transformation |
| Alerts | Reaction without understanding |
| Metrics panels | Numbers without meaning |

Users see data. They do not understand risk.

### 1.2 The Epistemic Interface Paradigm

Epistemic Interfaces operate on a different principle:

```
Traditional: Data → Display → User interprets
Epistemic:   Data → Narrative → Understanding → Decision
```

The interface is not a window to data. It is a cognitive transformation engine.

### 1.3 Design Philosophy

Three core principles:

1. **Narrative over Metrics**: Numbers serve story, not vice versa
2. **Transformation over Information**: Change understanding, not just awareness
3. **Decision over Display**: Every element drives toward action

---

## 2. Pattern Catalog

### 2.1 Overview

| Pattern | Purpose | Category |
|---------|---------|----------|
| EUI-1: Counterfactual Toggle | Show alternative realities | Core |
| EUI-2: Abstract Risk Object | Make invisible visible | Core |
| EUI-3: Narrative Phase Engine | Guide cognitive journey | Core |
| EUI-4: Liability Translation | Convert risk to $ | Conversion |
| EUI-5: Persona Routing | Adaptive institutional UI | Adaptation |
| EUI-6: Compliance Binding | Metrics → Regulation | Governance |
| EUI-7: Epistemic Passport | Artifact generation | Output |
| EUI-8: Decision Gate | Force binary choice | Conversion |

---

## 3. Core Patterns

### Pattern EUI-1: Counterfactual Toggle

#### Intent

Enable users to experience two realities: with and without epistemic risk mitigation.

#### Problem

Users cannot evaluate risk mitigation value without experiencing the alternative.

#### Solution

A binary toggle that instantly transforms the entire interface between two states:

```
State A: "Without ONTO" — High risk, chaos, danger signals
State B: "With ONTO" — Low risk, calm, safety signals
```

#### Structure

```
┌─────────────────────────────────────────┐
│                                         │
│    WITHOUT ONTO  ◉────────○  WITH ONTO  │
│                                         │
├─────────────────────────────────────────┤
│                                         │
│   [All UI elements transform based      │
│    on toggle state]                     │
│                                         │
└─────────────────────────────────────────┘
```

#### Implementation

```javascript
const toggle = {
    states: ['baseline', 'onto'],
    current: 'baseline',
    
    affects: [
        'chaos_orb.intensity',
        'gauges.values',
        'radar.shape',
        'liability.numbers',
        'compliance.badges',
        'color.scheme'
    ],
    
    transition: {
        duration: 400,
        easing: 'ease-out'
    }
};
```

#### Key Behaviors

1. **Instant Transformation**: All dependent elements update simultaneously
2. **Persistent State**: Toggle position maintained across scrolling
3. **Visual Feedback**: Smooth animation reinforces state change
4. **Cascading Updates**: Metrics, visuals, and text all transform

#### Psychological Effect

Users experience the counterfactual. They don't read about risk reduction — they feel it.

---

### Pattern EUI-2: Abstract Risk Object (Chaos Orb)

#### Intent

Make abstract epistemic risk tangible through a visual metaphor object.

#### Problem

"Epistemic risk" is an abstract concept. Users cannot see, touch, or intuitively grasp it.

#### Solution

Create a persistent visual object that embodies risk state:

```
High Risk State:
- Chaotic motion
- Red/orange glow
- Irregular pulsing
- Sharp edges
- Text: "UNCALIBRATED"

Low Risk State:
- Calm motion
- Green glow
- Steady breathing
- Smooth edges
- Text: "CALIBRATED"
```

#### Structure

```
┌──────────────────┐
│                  │
│    ╭──────╮      │
│   ╱ CHAOS  ╲     │  ← Visual metaphor object
│   ╲  ORB  ╱      │
│    ╰──────╯      │
│                  │
│  UNCALIBRATED    │  ← State label
│                  │
└──────────────────┘
```

#### Implementation

```css
.chaos-orb {
    /* Baseline: Chaotic */
    animation: chaosCore 2s infinite;
    box-shadow: 0 0 80px rgba(239, 68, 68, 0.5);
}

.chaos-orb.calibrated {
    /* Mitigated: Calm */
    animation: calmCore 4s infinite;
    box-shadow: 0 0 30px rgba(34, 197, 94, 0.3);
}
```

#### Key Properties

1. **Always Visible**: Persistent in viewport during scroll
2. **Responsive to State**: Transforms with toggle
3. **Visceral**: Motion and color create emotional response
4. **Memorable**: Becomes mental anchor for "epistemic risk"

#### Psychological Effect

The orb becomes the user's internal representation of epistemic risk. When they think "AI risk," they see the orb.

---

### Pattern EUI-3: Narrative Phase Engine

#### Intent

Transform passive scrolling into guided cognitive journey.

#### Problem

Scrolling is passive. Users scan, skip, and miss the transformation.

#### Solution

Divide the page into distinct narrative phases with observable state:

```
Phase 0: HOOK      — Capture attention
Phase 1: PROBLEM   — Establish pain
Phase 2: SIMULATION — Interactive discovery
Phase 3: SOLUTION  — Present framework
Phase 4: PROOF     — Show evidence
Phase 5: IMPACT    — Business translation
Phase 6: GOVERNANCE — Institutional framing
Phase 7: ACTION    — Force decision
```

#### Structure

```
<body data-phase="problem">
    <section data-phase="hook">...</section>
    <section data-phase="problem">...</section>
    <section data-phase="simulation">...</section>
    ...
</body>
```

#### Implementation

```javascript
const phaseObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            document.body.dataset.phase = entry.target.dataset.phase;
            applyPhaseEffects(entry.target.dataset.phase);
        }
    });
}, { threshold: 0.3 });
```

#### Phase-Based Effects

```css
[data-phase="hook"] {
    --phase-accent: var(--danger);
    /* Maximum tension */
}

[data-phase="solution"] {
    --phase-accent: var(--accent);
    /* Understanding emerges */
}

[data-phase="action"] {
    --phase-accent: var(--safe);
    /* Decision urgency */
}
```

#### Key Behaviors

1. **Observable State**: `body[data-phase]` available for CSS and JS
2. **Cascading Styles**: Colors, animations, urgency shift with phase
3. **Progress Indication**: User knows where they are in journey
4. **Chapter Navigation**: Explicit prev/next controls available

#### Psychological Effect

The journey has structure. Users feel guided, not lost. The narrative builds to inevitable conclusion.

---

## 4. Conversion Patterns

### Pattern EUI-4: Liability Translation Layer

#### Intent

Convert abstract risk metrics into concrete financial exposure.

#### Problem

"ECE = 0.23" means nothing to executives. "$8.2M exposure" means everything.

#### Solution

A calculation engine that translates metrics to dollars:

```
Input:  ECE, U-Recall, Domain, Scale
Output: Annual Liability Exposure ($)
```

#### Structure

```
┌─────────────────────────────────────────┐
│  DOMAIN: [Medical ▼]  SCALE: [100K/mo]  │
├─────────────────────────────────────────┤
│                                         │
│  WITHOUT ONTO          WITH ONTO        │
│  ┌──────────┐         ┌──────────┐      │
│  │ $8.2M    │   →     │ $410K    │      │
│  │ exposure │         │ exposure │      │
│  └──────────┘         └──────────┘      │
│                                         │
│  ANNUAL SAVINGS: $7.8M                  │
│  RISK REDUCTION: 95%                    │
│  ROI: 1,560%                            │
│                                         │
└─────────────────────────────────────────┘
```

#### Implementation

```javascript
function calculateLiability(domain, scale, mode) {
    const config = DOMAIN_CONFIG[domain];
    const failureRate = mode === 'onto' 
        ? config.failure_onto 
        : config.failure_baseline;
    
    return scale * 12 * failureRate * 
           config.incident_cost * config.multiplier;
}
```

#### Key Behaviors

1. **Real-time Calculation**: Updates as inputs change
2. **Comparison Display**: Always shows both states
3. **CFO Language**: Dollars, ROI, savings — not metrics
4. **Domain Sensitivity**: Different domains = different exposure

#### Psychological Effect

Risk becomes budget item. Mitigation becomes investment. Decision becomes financial.

---

### Pattern EUI-8: Decision Gate

#### Intent

Force binary decision at journey's end.

#### Problem

Users browse, learn, and leave. No commitment extracted.

#### Solution

A terminal section that presents exactly two paths:

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│  ┌─────────────────┐    OR    ┌─────────────────┐  │
│  │                 │          │                 │  │
│  │  CONTINUE       │          │  ADOPT          │  │
│  │  WITHOUT ONTO   │          │  ONTO           │  │
│  │                 │          │                 │  │
│  │  [Download      │          │  [Request       │  │
│  │   Risk Report]  │          │   Assessment]   │  │
│  │                 │          │                 │  │
│  │  Danger styling │          │  Safe styling   │  │
│  │                 │          │                 │  │
│  └─────────────────┘          └─────────────────┘  │
│                                                     │
│  Your Annual Exposure: $8.2M                        │
│  Your Risk Score: 73                                │
│                                                     │
└─────────────────────────────────────────────────────┘
```

#### Key Behaviors

1. **Binary Choice**: Exactly two options, no third path
2. **Asymmetric Styling**: Danger vs. safety visual coding
3. **Personalized Stakes**: User's calculated numbers displayed
4. **Both Paths Productive**: Even "no" generates lead artifact

#### Psychological Effect

Fence-sitting becomes uncomfortable. The user must choose. Both choices advance the relationship.

---

## 5. Adaptation Patterns

### Pattern EUI-5: Persona Routing

#### Intent

Same interface, different experience per user type.

#### Problem

Enterprise executives, researchers, regulators, and developers need different information.

#### Solution

Gate the journey with persona selection that adapts subsequent content:

```
┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐
│ ENTERPRISE │  │  AI LAB    │  │ REGULATOR  │  │ DEVELOPER  │
│            │  │            │  │            │  │            │
│ CFO, CISO  │  │ Researcher │  │ Policy     │  │ Engineer   │
│ Risk focus │  │ Benchmark  │  │ Compliance │  │ SDK focus  │
└────────────┘  └────────────┘  └────────────┘  └────────────┘
```

#### Routing Matrix

| Persona | Emphasized Sections | Hidden Sections | CTA |
|---------|---------------------|-----------------|-----|
| Enterprise | Liability, Compliance, Tiers | SDK docs | Request Assessment |
| AI Lab | Metrics, Benchmark, Methodology | Pricing | Try Benchmark |
| Regulator | Compliance, Standards, Audit | Pricing | Request Briefing |
| Developer | SDK, Metrics, Integration | Compliance | Get API Key |

#### Implementation

```javascript
const PERSONA_ROUTES = {
    enterprise: {
        emphasize: ['liability', 'compliance', 'tiers'],
        hide: ['sdk', 'benchmark'],
        cta: 'Request Assessment'
    },
    // ...
};

function applyPersona(persona) {
    document.body.dataset.persona = persona;
    // Show/hide sections
    // Update CTA text
    // Adjust metric emphasis
}
```

#### Psychological Effect

The user feels understood. The interface "knows" what they need. Trust increases.

---

## 6. Governance Patterns

### Pattern EUI-6: Compliance Binding

#### Intent

Connect live metrics to regulatory pass/fail status.

#### Problem

Compliance is seen as checkbox exercise. Metrics are seen as technical detail.

#### Solution

Real-time binding between calculated metrics and regulatory status:

```
┌─────────────────────────────────────────────────────┐
│  REGULATORY COMPLIANCE STATUS                        │
├──────────────┬──────────────┬───────────────────────┤
│  🇪🇺 EU AI Act  │  🇺🇸 NIST RMF  │  🌐 ISO 42001       │
│  ┌──────────┐ │  ┌──────────┐ │  ┌──────────┐       │
│  │ ✗ FAIL   │ │  │ ✓ PASS   │ │  │ ✗ FAIL   │       │
│  └──────────┘ │  └──────────┘ │  └──────────┘       │
│  Risk > 40    │  ECE < 0.15   │  U-Recall < 0.70    │
└──────────────┴──────────────┴───────────────────────┘
```

#### Implementation

```javascript
const COMPLIANCE_RULES = {
    'EU AI Act': () => ONTO_STATE.risk_score <= 40,
    'NIST RMF': () => ONTO_STATE.ece <= 0.15,
    'ISO 42001': () => ONTO_STATE.u_recall >= 0.70
};

function updateCompliance() {
    Object.entries(COMPLIANCE_RULES).forEach(([reg, test]) => {
        const status = test() ? 'pass' : 'fail';
        renderBadge(reg, status);
    });
}
```

#### Key Behaviors

1. **Live Binding**: Badges update when metrics change
2. **Toggle Responsive**: Compliance shifts with calibration state
3. **Threshold Visible**: User sees the rule, not just the result
4. **Multi-framework**: Multiple regulations evaluated simultaneously

#### Psychological Effect

Compliance becomes real-time. Metrics have regulatory meaning. Risk becomes regulatory risk.

---

### Pattern EUI-7: Epistemic Passport

#### Intent

Generate shareable institutional artifact from session.

#### Problem

Web sessions are ephemeral. Enterprise decisions need documents.

#### Solution

Generate downloadable artifact capturing epistemic risk profile:

```
┌─────────────────────────────────────────┐
│  ONTO EPISTEMIC PASSPORT                │
│  ─────────────────────────────────────  │
│                                         │
│  Session: S1x7k2m9                      │
│  Generated: 2025-01-27                  │
│                                         │
│  CONFIGURATION                          │
│  Domain: Medical                        │
│  Scale: 100,000 queries/month           │
│                                         │
│  METRICS                                │
│  ┌──────────┬──────────┬──────────┐    │
│  │ Metric   │ Baseline │ ONTO     │    │
│  ├──────────┼──────────┼──────────┤    │
│  │ U-Recall │ 38%      │ 89%      │    │
│  │ ECE      │ 0.23     │ 0.04     │    │
│  │ Risk     │ 73       │ 18       │    │
│  └──────────┴──────────┴──────────┘    │
│                                         │
│  LIABILITY                              │
│  Baseline: $8,200,000                   │
│  Mitigated: $410,000                    │
│  Reduction: 95%                         │
│                                         │
│  RECOMMENDATION                         │
│  Tier: L2 Continuous Guardian           │
│                                         │
│  ─────────────────────────────────────  │
│  Verify: ontostandard.org/verify#S1x7k  │
└─────────────────────────────────────────┘
```

#### Export Formats

1. **PDF**: For committees, boards, print
2. **JSON**: For systems, APIs, integration
3. **Share Link**: For collaboration (URL-encoded state)

#### Key Behaviors

1. **Session-bound**: Captures user's specific exploration
2. **Verifiable**: Hash enables authenticity check
3. **Shareable**: Multiple export formats
4. **Timestamped**: Creates audit trail

#### Psychological Effect

The session becomes an artifact. The exploration becomes documentation. The website becomes institution.

---

## 7. Implementation Guidelines

### 7.1 State Architecture

All patterns depend on unified state:

```javascript
window.ONTO_STATE = {
    // Identity
    session_hash: 'S1x7k2m9',
    persona: 'enterprise',
    
    // Configuration
    domain: 'medical',
    ai_scale: 100000,
    
    // UI State
    calibration_mode: 'baseline', // or 'onto'
    journey_phase: 'simulation',
    scroll_progress: 0.45,
    
    // Computed
    metrics: { ece: 0.23, u_recall: 0.38, risk: 73 },
    liability: { baseline: 8200000, onto: 410000 }
};
```

### 7.2 Event Flow

```
User Action → State Update → Broadcast → UI Update

Example:
Toggle Click → calibration_mode = 'onto' 
            → Event: 'onto:calibration:change'
            → Chaos Orb transforms
            → Gauges update
            → Liability recalculates
            → Compliance badges refresh
            → Passport data updates
```

### 7.3 Persistence Strategy

```javascript
// Local persistence
localStorage.setItem('onto_state', JSON.stringify(state));

// URL persistence (shareable)
location.hash = btoa(JSON.stringify(state));

// Recovery priority
1. URL hash (shared link)
2. localStorage (return visit)
3. Defaults (new user)
```

### 7.4 Accessibility Requirements

1. **Keyboard Navigation**: All interactions keyboard-accessible
2. **Screen Reader**: State changes announced
3. **Reduced Motion**: Respect prefers-reduced-motion
4. **Color Independence**: Information not color-only

---

## 8. Anti-Patterns

### 8.1 What NOT to Do

| Anti-Pattern | Problem | Correct Pattern |
|--------------|---------|-----------------|
| Metrics without context | Numbers don't transform understanding | EUI-4: Liability Translation |
| Static compliance cards | No connection to user state | EUI-6: Compliance Binding |
| Single exit path | Users leave without commitment | EUI-8: Decision Gate |
| Undifferentiated content | All users see same thing | EUI-5: Persona Routing |
| Dashboard layout | Data display, not narrative | EUI-3: Narrative Phases |
| Abstract risk language | "Epistemic risk" means nothing | EUI-2: Chaos Orb |

### 8.2 Common Mistakes

1. **Showing metrics before establishing problem**: Users don't care about ECE until they feel the pain
2. **Offering too many choices**: Decision Gate has TWO options, not five
3. **Making toggle optional**: Toggle must be prominent and irresistible
4. **Burying the transformation**: Before/after must be instantly visible

---

## 9. Validation Criteria

### 9.1 Functional Requirements

| Pattern | Validation Test |
|---------|-----------------|
| EUI-1 | Toggle transforms ALL dependent elements |
| EUI-2 | Orb state visually distinct between modes |
| EUI-3 | body[data-phase] updates on scroll |
| EUI-4 | Numbers update in real-time with inputs |
| EUI-5 | Different personas see different content |
| EUI-6 | Badges change with toggle state |
| EUI-7 | PDF/JSON export includes session data |
| EUI-8 | Both paths capture user engagement |

### 9.2 Experience Requirements

1. **Time to Comprehension**: User understands epistemic risk within 60 seconds
2. **Toggle Discovery**: 90%+ of users interact with toggle
3. **Journey Completion**: 40%+ reach Decision Gate
4. **Artifact Generation**: 20%+ download passport

---

## 10. Future Patterns

### 10.1 Planned Extensions

- **EUI-9: Temporal Risk Projection**: Show risk evolution over time
- **EUI-10: Comparative Analysis**: Side-by-side model comparison
- **EUI-11: Real-time Monitoring**: Live production metrics
- **EUI-12: Audit Trail**: Complete decision documentation

### 10.2 Research Directions

- Optimal phase sequencing
- Persona detection automation
- Emotional response measurement
- Conversion optimization

---

## Bibliography

[1] Norman, D. (2013). *The Design of Everyday Things*. Basic Books.

[2] Kahneman, D. (2011). *Thinking, Fast and Slow*. Farrar, Straus and Giroux.

[3] Cialdini, R. (2006). *Influence: The Psychology of Persuasion*. Harper Business.

[4] Tufte, E. (2001). *The Visual Display of Quantitative Information*. Graphics Press.

[5] Spence, R. (2014). *Information Visualization: An Introduction*. Springer.

---

*© 2025 ONTO Standards Committee. This document may be freely distributed with attribution.*
