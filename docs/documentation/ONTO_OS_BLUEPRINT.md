# ONTO-OS: Epistemic Operating System for AGI

## Executive Summary

ONTO-OS is an operating system layer for artificial general intelligence that provides rigorous epistemic infrastructure. Unlike current AI systems that conflate knowledge with generation, ONTO-OS enforces structural separation between what is known, unknown, and contested—making epistemic status a first-class citizen of the computational substrate.

**Core Thesis:** AGI without epistemic structure is dangerous by default. ONTO-OS makes safety structural rather than behavioral.

---

## The Problem

### Current State

```
User: What causes consciousness?

GPT-4: [1500 words of confident speculation]
Claude: [1200 words of hedged speculation]  
Llama: [800 words of speculation with citations]
```

All three fail the same way: **no structural representation of "this is unknown."**

### Root Cause

Current architectures conflate:
- **Generation** (producing text) with **Knowledge** (representing facts)
- **Confidence** (probability of next token) with **Epistemic status** (established vs unknown)
- **Memory** (context window) with **Understanding** (structured knowledge)

### Consequence

Systems that cannot structurally represent unknowns cannot reliably:
1. Abstain from speculation
2. Request clarification appropriately
3. Update beliefs on evidence
4. Reason about their own limitations

---

## ONTO-OS Architecture

### Design Principles

1. **Epistemic First**: Knowledge status is primitive, not derived
2. **Structure Over Behavior**: Safety through architecture, not prompting
3. **Composable**: Modules can be combined without epistemic contamination
4. **Auditable**: Every claim traceable to source and status

### System Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                        │
│         (Agents, Assistants, Research Tools)               │
├─────────────────────────────────────────────────────────────┤
│                    REASONING LAYER                          │
│    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐         │
│    │  Inference  │ │  Planning   │ │  Learning   │         │
│    │   Engine    │ │   Engine    │ │   Engine    │         │
│    └──────┬──────┘ └──────┬──────┘ └──────┬──────┘         │
│           └───────────────┼───────────────┘                 │
│                           ▼                                 │
├─────────────────────────────────────────────────────────────┤
│                    EPISTEMIC LAYER                          │
│    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐         │
│    │    Claim    │ │    Trust    │ │     Gap     │         │
│    │   Registry  │ │    Graph    │ │   Detector  │         │
│    └──────┬──────┘ └──────┬──────┘ └──────┬──────┘         │
│           └───────────────┼───────────────┘                 │
│                           ▼                                 │
├─────────────────────────────────────────────────────────────┤
│                    ONTOLOGY LAYER                           │
│    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐         │
│    │   Concept   │ │  Relation   │ │  Axiom      │         │
│    │    Graph    │ │   Index     │ │  Store      │         │
│    └─────────────┘ └─────────────┘ └─────────────┘         │
├─────────────────────────────────────────────────────────────┤
│                    STORAGE LAYER                            │
│              (Neo4j, Vector DB, Document Store)             │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Claim Registry

Every assertion in ONTO-OS is a first-class **Claim** object:

```python
@dataclass
class Claim:
    id: str
    content: str                    # Natural language statement
    formal: Optional[Formula]       # Formal representation
    status: EpistemicStatus         # ESTABLISHED | CONTESTED | UNKNOWN | REFUTED
    confidence: float               # 0.0 - 1.0
    source: Source                  # Where this came from
    dependencies: List[ClaimID]     # What it depends on
    contradicts: List[ClaimID]      # What it conflicts with
    timestamp: datetime
    version: int
```

**Epistemic Status Transitions:**

```
UNKNOWN ──evidence──▶ CONTESTED ──consensus──▶ ESTABLISHED
    ▲                     │                        │
    │                     │                        │
    └────refutation───────┴────────────────────────┘
```

### 2. Trust Graph

Sources are nodes with trust scores:

```python
@dataclass
class Source:
    id: str
    type: SourceType           # PEER_REVIEWED | PREPRINT | TEXTBOOK | WEB | MODEL
    trust_score: float         # Computed from history
    domain_expertise: Dict[Domain, float]
    citation_count: int
    retraction_count: int
```

**Trust Propagation:**

```
Claim.confidence = f(source.trust, evidence_strength, contradiction_penalty)
```

### 3. Gap Detector

Continuously monitors ontology for epistemic gaps:

```python
class GapDetector:
    def detect_gaps(self, ontology: Ontology) -> List[Gap]:
        gaps = []
        
        # Missing dependencies
        for claim in ontology.claims:
            for dep in claim.dependencies:
                if not ontology.has(dep):
                    gaps.append(MissingDependency(claim, dep))
        
        # Unresolved contradictions
        for c1, c2 in ontology.contradictions():
            if not ontology.has_resolution(c1, c2):
                gaps.append(UnresolvedContradiction(c1, c2))
        
        # Orphan concepts
        for concept in ontology.concepts:
            if concept.claim_count == 0:
                gaps.append(OrphanConcept(concept))
        
        # Stale claims
        for claim in ontology.claims:
            if claim.age > STALENESS_THRESHOLD:
                gaps.append(StaleClaim(claim))
        
        return gaps
```

### 4. Inference Engine

Reasoning that respects epistemic boundaries:

```python
class EpistemicInference:
    def infer(self, query: Query) -> Answer:
        # 1. Check if query hits known claim
        direct = self.ontology.lookup(query)
        if direct and direct.status == ESTABLISHED:
            return Answer(direct, confidence=direct.confidence)
        
        # 2. Check for contradictions
        if self.ontology.has_contradiction(query):
            return Answer.contested(
                self.ontology.get_positions(query)
            )
        
        # 3. Check for explicit unknown
        if self.ontology.is_known_unknown(query):
            return Answer.unknown(
                reason=self.ontology.get_unknown_reason(query)
            )
        
        # 4. Attempt derivation from axioms
        derivation = self.derive(query)
        if derivation:
            return Answer(
                derivation.conclusion,
                confidence=derivation.confidence,
                trace=derivation.steps
            )
        
        # 5. Default: acknowledge uncertainty
        return Answer.uncertain(
            "No established knowledge or derivation found"
        )
```

---

## Forcing Mechanism

### What is Forcing?

Borrowed from mathematical logic: forcing extends models with new truths while preserving consistency.

**In ONTO-OS:** Forcing is the protocol for adding new knowledge.

### Forcing Protocol

```python
class ForcingProtocol:
    def force(self, hypothesis: Claim, evidence: Evidence) -> Result:
        # 1. Consistency check
        conflicts = self.ontology.check_consistency(hypothesis)
        if conflicts:
            return Result.conflict(conflicts)
        
        # 2. Evidence evaluation
        strength = self.evaluate_evidence(evidence)
        if strength < THRESHOLD:
            return Result.insufficient_evidence(strength)
        
        # 3. Tentative addition
        self.ontology.add_tentative(hypothesis, evidence)
        
        # 4. Propagate implications
        implications = self.derive_implications(hypothesis)
        
        # 5. Check for new contradictions
        new_conflicts = self.check_implications(implications)
        if new_conflicts:
            self.ontology.rollback(hypothesis)
            return Result.downstream_conflict(new_conflicts)
        
        # 6. Commit
        self.ontology.commit(hypothesis)
        return Result.success(hypothesis, implications)
```

### Forcing Conditions

A claim can only be forced if:

1. **Consistency**: No contradiction with ESTABLISHED claims
2. **Evidence**: Sufficient supporting evidence
3. **Derivability**: Implications don't contradict established facts
4. **Provenance**: Source meets trust threshold

---

## Application: ONTO-AGI

### Agent Architecture

```python
class ONTOAgent:
    def __init__(self):
        self.ontology = Ontology()
        self.inference = EpistemicInference(self.ontology)
        self.forcing = ForcingProtocol(self.ontology)
        self.gap_detector = GapDetector(self.ontology)
        self.llm = LanguageModel()  # For generation only
    
    def respond(self, query: str) -> Response:
        # 1. Parse query
        parsed = self.parse(query)
        
        # 2. Epistemic lookup
        answer = self.inference.infer(parsed)
        
        # 3. Generate response respecting epistemic status
        if answer.status == ESTABLISHED:
            return self.generate_confident(answer)
        elif answer.status == CONTESTED:
            return self.generate_balanced(answer)
        elif answer.status == UNKNOWN:
            return self.generate_uncertainty(answer)
        else:
            return self.generate_tentative(answer)
    
    def learn(self, source: Source, content: str):
        # Extract claims
        claims = self.extract_claims(content)
        
        # Attempt to force each claim
        for claim in claims:
            result = self.forcing.force(claim, source)
            self.log(result)
    
    def research(self, topic: str) -> ResearchPlan:
        # Identify gaps
        gaps = self.gap_detector.detect_gaps()
        relevant = [g for g in gaps if g.relates_to(topic)]
        
        # Prioritize by importance
        prioritized = self.prioritize(relevant)
        
        # Generate research plan
        return ResearchPlan(prioritized)
```

### Safety Properties

ONTO-AGI provides structural guarantees:

1. **No Hallucination of Facts**: Claims only asserted if ESTABLISHED in ontology
2. **Uncertainty Acknowledgment**: UNKNOWNs generate appropriate uncertainty language
3. **Contradiction Disclosure**: CONTESTED claims present multiple positions
4. **Auditability**: Every assertion traceable to source and forcing event

---

## Implementation Roadmap

### Phase 1: Foundation (6 months)

- [ ] Core ontology storage (Neo4j)
- [ ] Claim registry with epistemic status
- [ ] Basic gap detection
- [ ] Simple forcing protocol
- [ ] Integration with one LLM

### Phase 2: Reasoning (6 months)

- [ ] Full inference engine
- [ ] Trust graph with propagation
- [ ] Advanced forcing with rollback
- [ ] Multi-source integration

### Phase 3: Agents (6 months)

- [ ] ONTO-Agent framework
- [ ] Tool use with epistemic awareness
- [ ] Multi-agent coordination
- [ ] Research automation

### Phase 4: Scale (12 months)

- [ ] Distributed ontology
- [ ] Real-time updates
- [ ] Cross-domain reasoning
- [ ] Production deployment

---

## Comparison with Alternatives

| Approach | Knowledge Rep | Epistemic Status | Consistency | Auditability |
|----------|---------------|------------------|-------------|--------------|
| Vanilla LLM | Weights | Implicit | None | None |
| RAG | Documents | None | None | Partial |
| Knowledge Graph | Triples | Optional | Manual | Yes |
| **ONTO-OS** | **Claims** | **First-class** | **Structural** | **Full** |

---

## Research Questions

### Tractable (Solvable with current techniques)

1. How to extract claims from natural language reliably?
2. What trust propagation algorithms work best?
3. How to scale ontology operations?

### Open (Fundamental research needed)

1. Can forcing extend to uncertain knowledge domains?
2. How to handle evolving scientific consensus?
3. What are the limits of structural safety guarantees?

---

## Conclusion

ONTO-OS represents a paradigm shift: from AI systems that generate plausible text to systems that reason about knowledge with structural integrity.

The key insight is simple: **epistemic status must be primitive, not derived.**

Current LLMs derive uncertainty (if at all) from generation probability. ONTO-OS inverts this: epistemic status determines what can be generated.

This inversion makes safety structural rather than behavioral—a prerequisite for AGI we can trust.

---

## References

1. Cohen, P. (1963). The independence of the continuum hypothesis. *PNAS*.
2. Hendler, J. (2001). The Semantic Web. *Scientific American*.
3. Lenat, D. (1995). CYC: A large-scale investment in knowledge infrastructure. *CACM*.
4. Russell, S. (2019). Human Compatible: AI and the Problem of Control. *Viking*.

---

*ONTO-OS v0.1 Specification*
*January 2026*
