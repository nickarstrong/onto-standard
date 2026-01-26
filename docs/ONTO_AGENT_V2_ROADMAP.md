# ONTO-Agent v2: Scientific Discovery Engine

## Vision

ONTO-Agent v2 transforms from an epistemic evaluation framework into an autonomous scientific discovery system. The agent identifies knowledge gaps, formulates hypotheses, designs experiments, and synthesizes findings—all while maintaining rigorous epistemic calibration.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ONTO-Agent v2                            │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Reader    │  │  Reasoner   │  │   Writer    │         │
│  │   Agent     │  │   Agent     │  │   Agent     │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                 │
│  ┌──────▼────────────────▼────────────────▼──────┐         │
│  │              ONTO Core v6 (Kernel)             │         │
│  │  • Ontology Graph    • Gap Detection          │         │
│  │  • Claim Network     • Epistemic Oracle       │         │
│  │  • Trust Scoring     • Forcing Resolution     │         │
│  └───────────────────────┬───────────────────────┘         │
│                          │                                  │
│  ┌───────────────────────▼───────────────────────┐         │
│  │           External Integration                 │         │
│  │  • arXiv API    • Semantic Scholar            │         │
│  │  • PubMed       • OpenAlex                    │         │
│  │  • Web Search   • Code Execution              │         │
│  └───────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

---

## Modules

### 1. Reader Agent

**Purpose:** Ingest and structure scientific literature.

**Capabilities:**
- Parse PDF papers → structured claims
- Extract methodology, results, limitations
- Identify cited claims and dependencies
- Detect contradictions across papers

**Pipeline:**
```
PDF → OCR/Parse → Sections → Claims → Graph
```

**Output:**
```json
{
  "paper_id": "arxiv:2401.12345",
  "claims": [
    {
      "text": "GPT-4 achieves 87% accuracy on MMLU",
      "type": "empirical",
      "confidence": 0.95,
      "dependencies": ["MMLU dataset", "GPT-4 model"],
      "contradicts": ["arxiv:2312.54321"]
    }
  ]
}
```

### 2. Reasoner Agent

**Purpose:** Identify gaps, generate hypotheses, plan experiments.

**Capabilities:**
- Gap detection via ontology analysis
- Hypothesis generation from gap patterns
- Experiment design suggestions
- Counter-argument anticipation

**Gap Detection:**
```python
def detect_gaps(ontology):
    gaps = []
    
    # Missing dependencies
    for claim in ontology.claims:
        for dep in claim.dependencies:
            if not ontology.has(dep):
                gaps.append(MissingDependencyGap(claim, dep))
    
    # Unresolved contradictions
    for c1, c2 in ontology.contradictions:
        if not ontology.has_resolution(c1, c2):
            gaps.append(UnresolvedContradiction(c1, c2))
    
    # Unexplained phenomena
    for phenomenon in ontology.phenomena:
        if not ontology.has_explanation(phenomenon):
            gaps.append(UnexplainedPhenomenon(phenomenon))
    
    return gaps
```

**Hypothesis Generation:**
```
Gap: "No explanation for dark matter observations"
→ Hypothesis: "Modified gravity (MOND) explains rotation curves"
→ Hypothesis: "Weakly interacting particles (WIMPs)"
→ Hypothesis: "Primordial black holes"
```

### 3. Writer Agent

**Purpose:** Synthesize findings into publishable artifacts.

**Capabilities:**
- Literature review generation
- Research proposal drafting
- Paper outline creation
- Citation management

**Output Types:**
- Survey papers
- Research proposals
- Hypothesis papers
- Technical reports

---

## Forcing Mechanism

### What is Forcing?

Borrowed from set theory: forcing adds new truths to a model while preserving consistency.

**In ONTO-Agent:**
- **Generic conditions**: Verifiable experiments/observations
- **Forcing extensions**: New knowledge added to ontology
- **Consistency preservation**: No contradictions in updated model

### Forcing Pipeline

```
1. Identify gap in current ontology
2. Generate candidate claims (hypotheses)
3. Design forcing condition (experiment)
4. Execute/simulate experiment
5. If result validates hypothesis → extend ontology
6. If result invalidates → prune hypothesis space
```

### Example

```
Gap: "Unknown: Does transformer attention follow power law?"

Candidates:
  H1: Attention weights are uniformly distributed
  H2: Attention follows Zipf distribution
  H3: Attention follows power law with α ≈ 1.5

Forcing condition:
  Experiment: Analyze attention matrices across 100 models
  
Execution:
  Result: α = 1.47 ± 0.12

Resolution:
  H3 validated → Add to ontology with confidence 0.92
  H1, H2 pruned
```

---

## Implementation Roadmap

### Phase 1: Foundation (Q1)

**ONTO Core v6:**
- [ ] Claim dependency graph
- [ ] Contradiction detection
- [ ] Gap analysis API
- [ ] Forcing primitive types

**Reader Agent v1:**
- [ ] PDF parsing (PyMuPDF)
- [ ] Section extraction
- [ ] Basic claim extraction
- [ ] arXiv API integration

### Phase 2: Reasoning (Q2)

**Reasoner Agent v1:**
- [ ] Gap pattern recognition
- [ ] Hypothesis generation
- [ ] Experiment design templates
- [ ] Counter-argument generation

**Knowledge Sources:**
- [ ] Semantic Scholar integration
- [ ] OpenAlex integration
- [ ] PubMed integration

### Phase 3: Synthesis (Q3)

**Writer Agent v1:**
- [ ] Literature review generation
- [ ] Research proposal drafts
- [ ] LaTeX output
- [ ] Citation formatting

**Evaluation:**
- [ ] Gap discovery benchmark
- [ ] Hypothesis quality metrics
- [ ] Human expert comparison

### Phase 4: Autonomy (Q4)

**Full Pipeline:**
- [ ] End-to-end discovery workflow
- [ ] Multi-agent coordination
- [ ] Human-in-the-loop review
- [ ] Continuous learning

**Deployment:**
- [ ] API service
- [ ] Web interface
- [ ] Integration with research tools

---

## Research Questions

### Tractable

1. Can LLMs accurately extract structured claims from papers?
2. What gap patterns predict fruitful research directions?
3. How to measure hypothesis quality before experimental validation?

### Open

1. Can agents discover genuinely novel hypotheses?
2. How to balance exploration vs. exploitation in research?
3. What's the role of serendipity in automated discovery?

---

## Evaluation

### Benchmarks

**Gap Detection:**
- Input: Papers with known follow-up work
- Task: Predict which gaps led to discoveries
- Metric: Precision/recall of identified gaps

**Hypothesis Generation:**
- Input: Historical gaps
- Task: Generate hypothesis matching actual discovery
- Metric: Semantic similarity to real hypotheses

**Literature Review:**
- Input: Research topic
- Task: Generate survey
- Metric: Coverage, accuracy, coherence (human eval)

### Baselines

- GPT-4 with prompting
- Semantic Scholar API
- Elicit.org
- Consensus.app

---

## Technical Stack

### Core

```
Language: Python 3.11+
Graph DB: Neo4j
Vector DB: Qdrant / Pinecone
LLM: Claude 3.5 / GPT-4
```

### APIs

```yaml
arxiv:
  endpoint: http://export.arxiv.org/api/query
  rate_limit: 1 req/3 sec

semantic_scholar:
  endpoint: https://api.semanticscholar.org/graph/v1
  key: required

openAlex:
  endpoint: https://api.openalex.org
  key: optional
```

### Infrastructure

```
Compute: GPU for embeddings
Storage: S3 for papers
Queue: Redis for async jobs
Monitoring: Prometheus + Grafana
```

---

## Risk Analysis

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| LLM hallucination | High | High | Strict verification, human review |
| Incorrect gap identification | Medium | Medium | Multiple verification passes |
| Hypothesis overfitting to training | Medium | High | Holdout temporal validation |
| Scalability issues | Medium | Low | Async processing, caching |
| API rate limits | High | Low | Request queuing, caching |

---

## Success Criteria

### Year 1

- [ ] Reader agent processes 10K papers
- [ ] Gap detection precision > 70%
- [ ] 1 validated hypothesis from agent suggestions
- [ ] Published paper on methodology

### Year 2

- [ ] End-to-end discovery demonstration
- [ ] Integration with 3+ research groups
- [ ] Gap-to-publication pipeline proven
- [ ] Open-source release with community

---

## Related Work

### Automated Science

- **AI Scientist** (Sakana): LLM-driven paper generation
- **ScienceWorld**: Simulation for scientific reasoning
- **Nobel Turing Challenge**: AI for scientific discovery

### Knowledge Graphs

- **Semantic Scholar Graph**: Paper relationship network
- **OpenAlex**: Open bibliometric data
- **Wikidata**: Structured knowledge base

### Hypothesis Generation

- **SciGen**: Hypothesis generation from literature
- **Elicit**: Research assistant with reasoning
- **Consensus**: Claim extraction and synthesis

---

## Team Requirements

| Role | FTE | Skills |
|------|-----|--------|
| ML Engineer | 1 | LLM, RAG, embeddings |
| Backend Engineer | 1 | Python, APIs, Neo4j |
| Research Scientist | 0.5 | Philosophy of science, ontology |
| Domain Expert | 0.5 | Target research domain |

---

## Budget (Year 1)

| Item | Cost |
|------|------|
| Compute (GPU) | $12K |
| LLM API calls | $8K |
| Cloud infrastructure | $4K |
| Data sources | $2K |
| **Total** | **$26K** |

---

## Conclusion

ONTO-Agent v2 represents a shift from benchmarking to discovery. The forcing mechanism provides rigorous foundations for knowledge extension. Success would demonstrate that explicit epistemic structure enables not just better evaluation, but better science.

**Next step:** Prototype Reader Agent with arXiv integration.
