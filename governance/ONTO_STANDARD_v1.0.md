# ONTO Epistemic Risk Standard

## Version 1.0

**Publication Date:** January 2026
**Status:** Active
**Maintained by:** ONTO Standards Council

---

## Document Information

| Field | Value |
|-------|-------|
| Standard ID | ONTO-ERS-1.0 |
| Version | 1.0 |
| Effective Date | January 2026 |
| Review Date | January 2027 |
| Classification | Public |

---

## 1. SCOPE

### 1.1 Purpose

This standard establishes requirements and recommendations for measuring 
**epistemic calibration** in artificial intelligence systems—the degree 
to which an AI system accurately recognizes the boundaries of its knowledge.

### 1.2 Applicability

This standard applies to:
- Large language models (LLMs)
- AI assistants and chatbots
- Decision support systems
- Automated reasoning systems
- Any AI system that generates factual claims or recommendations

### 1.3 Normative References

This standard aligns with:
- EU AI Act (Regulation 2024/1689), Articles 9, 13, 15
- NIST AI Risk Management Framework (AI RMF 1.0)
- ISO/IEC 23894:2023 — Guidance on AI risk management
- ISO/IEC 42001:2023 — AI management system

---

## 2. TERMS AND DEFINITIONS

### 2.1 Epistemic Calibration
The alignment between an AI system's expressed confidence and its actual 
accuracy, particularly regarding the recognition of knowledge boundaries.

### 2.2 Unknown Detection
The ability of an AI system to correctly identify questions or queries 
that have no established answer or fall outside its reliable knowledge.

### 2.3 Hallucination
The generation of confident but incorrect or unfounded responses by an 
AI system, particularly when the system should instead express uncertainty.

### 2.4 Calibration Error
A quantitative measure of the discrepancy between expressed confidence 
and observed accuracy, typically measured as Expected Calibration Error (ECE).

### 2.5 Epistemic Risk
The potential for harm arising from an AI system's failure to accurately 
represent the boundaries of its knowledge.

---

## 3. REQUIREMENTS

### 3.1 Measurement Requirements

#### 3.1.1 Unknown Detection Rate (Mandatory)

Organizations SHALL measure the rate at which their AI system correctly 
identifies genuinely unanswerable questions.

**Metric:** Unknown Recall (U-Recall)
```
U-Recall = True Unknown Detections / Total Unknown Questions
```

**Minimum Threshold:** 
- Low Risk Applications: ≥ 30%
- Medium Risk Applications: ≥ 50%
- High Risk Applications: ≥ 70%

#### 3.1.2 Calibration Error (Mandatory)

Organizations SHALL measure the calibration error of their AI system.

**Metric:** Expected Calibration Error (ECE)
```
ECE = Σ |accuracy(bin) - confidence(bin)| × n(bin) / N
```

**Maximum Threshold:**
- Low Risk Applications: ≤ 0.20
- Medium Risk Applications: ≤ 0.15
- High Risk Applications: ≤ 0.10

#### 3.1.3 Overconfidence Rate (Recommended)

Organizations SHOULD measure the rate of overconfident predictions.

**Metric:** Overconfidence Rate
```
Overconfidence = Cases where confidence > accuracy / Total cases
```

**Target:** ≤ 20%

### 3.2 Evaluation Requirements

#### 3.2.1 Benchmark Coverage

Evaluation SHALL include:
- Known facts (established ground truth)
- Unknown questions (genuinely open problems)
- Contradictions (topics with legitimate expert disagreement)

#### 3.2.2 Sample Size

Minimum evaluation samples:
- Initial certification: 50 questions per category
- Continuous monitoring: 20 questions per category per evaluation

#### 3.2.3 Evaluation Frequency

| Risk Level | Minimum Frequency |
|------------|-------------------|
| High | Monthly |
| Medium | Quarterly |
| Low | Annually |

### 3.3 Documentation Requirements

#### 3.3.1 Risk Assessment (Mandatory)

Organizations SHALL document:
- Epistemic risk level (Critical/High/Medium/Low)
- Measurement methodology
- Evaluation results
- Identified limitations

#### 3.3.2 Mitigation Measures (Mandatory)

Organizations SHALL document implemented measures to:
- Detect knowledge boundaries
- Express appropriate uncertainty
- Prevent confident hallucination
- Enable human oversight

#### 3.3.3 Audit Trail (Recommended)

Organizations SHOULD maintain:
- Historical evaluation results
- Model version tracking
- Change documentation

---

## 4. COMPLIANCE LEVELS

### 4.1 Level 1: Basic Compliance

**Requirements:**
- Unknown Detection ≥ 30%
- ECE ≤ 0.20
- Annual evaluation
- Basic documentation

**Suitable for:** Low-risk applications, internal tools

### 4.2 Level 2: Standard Compliance

**Requirements:**
- Unknown Detection ≥ 50%
- ECE ≤ 0.15
- Quarterly evaluation
- Full documentation

**Suitable for:** Customer-facing applications, B2B tools

### 4.3 Level 3: Advanced Compliance

**Requirements:**
- Unknown Detection ≥ 70%
- ECE ≤ 0.10
- Monthly evaluation
- Complete audit trail
- Third-party verification

**Suitable for:** High-stakes applications, regulated industries

---

## 5. REGULATORY MAPPING

### 5.1 EU AI Act Alignment

| EU AI Act Article | ONTO-ERS Requirement | Compliance Evidence |
|-------------------|---------------------|---------------------|
| Article 9 (Risk Management) | §3.3.1 Risk Assessment | Risk level documentation |
| Article 9(2)(a) (Known risks) | §3.1.1 Unknown Detection | U-Recall measurement |
| Article 9(2)(b) (Foreseeable risks) | §3.1.2 Calibration Error | ECE measurement |
| Article 13 (Transparency) | §3.3.2 Mitigation Measures | Limitation documentation |
| Article 15 (Accuracy) | §3.1 Measurements | Evaluation results |

### 5.2 NIST AI RMF Alignment

| NIST AI RMF Function | ONTO-ERS Requirement |
|---------------------|---------------------|
| GOVERN 1.1 (Policies) | §3.3 Documentation |
| MAP 1.1 (Context) | §3.2.1 Benchmark Coverage |
| MEASURE 2.5 (Performance) | §3.1 Measurements |
| MEASURE 2.6 (Trustworthiness) | §3.1.1 Unknown Detection |
| MANAGE 2.1 (Response) | §3.3.2 Mitigation |

### 5.3 ISO/IEC 23894 Alignment

| ISO/IEC 23894 Clause | ONTO-ERS Requirement |
|---------------------|---------------------|
| 6.2 (Risk identification) | §3.1 Measurements |
| 6.3 (Risk analysis) | §3.3.1 Risk Assessment |
| 6.4 (Risk evaluation) | §4 Compliance Levels |
| 6.5 (Risk treatment) | §3.3.2 Mitigation |

---

## 6. CERTIFICATION

### 6.1 Certification Process

1. **Application:** Submit evaluation request
2. **Evaluation:** Third-party assessment using ONTO-Bench
3. **Review:** Standards Council review of results
4. **Certification:** Issuance of compliance certificate
5. **Maintenance:** Ongoing monitoring per risk level

### 6.2 Certification Tiers

| Tier | Requirements | Validity |
|------|--------------|----------|
| ONTO Certified (Basic) | Level 1 Compliance | 12 months |
| ONTO Certified (Standard) | Level 2 Compliance | 12 months |
| ONTO Certified (Advanced) | Level 3 Compliance | 12 months |

### 6.3 Certification Mark

Certified organizations may display the ONTO Trust Mark per usage guidelines:
- Verification URL required
- Expiration date displayed
- Revocation for non-compliance

---

## 7. IMPLEMENTATION GUIDANCE

### 7.1 Getting Started

1. Assess current AI system capabilities
2. Run ONTO-Bench evaluation
3. Identify gaps against target compliance level
4. Implement mitigation measures
5. Re-evaluate and document

### 7.2 Common Mitigations

| Gap | Recommended Mitigation |
|-----|----------------------|
| Low unknown detection | Implement abstention mechanism |
| High calibration error | Apply temperature scaling |
| Overconfidence | Add confidence thresholds |
| Poor documentation | Establish evaluation cadence |

### 7.3 Continuous Improvement

- Regular re-evaluation
- Model version tracking
- Feedback integration
- Benchmark updates

---

## 8. REFERENCES

### Normative References
- EU AI Act (Regulation 2024/1689)
- NIST AI RMF 1.0
- ISO/IEC 23894:2023
- ISO/IEC 42001:2023

### Informative References
- Guo et al., "On Calibration of Modern Neural Networks" (2017)
- Kamath et al., "Selective Question Answering" (2020)
- ONTO-Bench: Benchmark for Epistemic Calibration (2026)

---

## 9. VERSION POLICY

### 9.1 Versioning Scheme

ONTO-ERS follows semantic versioning:
- **Major (X.0):** Breaking changes requiring re-certification
- **Minor (X.Y):** Backward-compatible additions
- **Patch (X.Y.Z):** Clarifications, no metric changes

### 9.2 Review Cycle

| Activity | Frequency |
|----------|-----------|
| Minor review | 6 months |
| Major review | 12 months |
| Public comment period | 30 days minimum |

### 9.3 Deprecation Policy

- Deprecated versions supported for 24 months
- 12-month advance notice for breaking changes
- Transition guidance provided for major updates

### 9.4 Current Status

| Version | Status | Sunset Date |
|---------|--------|-------------|
| 1.0 | **ACTIVE** | — |

---

## 10. REGULATORY TRACEABILITY MATRIX

### 10.1 EU AI Act Mapping

| ONTO-ERS Clause | EU AI Act Article | Requirement | Evidence |
|-----------------|-------------------|-------------|----------|
| §3.1.1 Unknown Detection | Art. 9(2)(a) | Identify known risks | U-Recall measurement |
| §3.1.2 Calibration Error | Art. 9(2)(b) | Assess foreseeable risks | ECE measurement |
| §3.3.1 Risk Assessment | Art. 9(1) | Risk management system | Documented risk level |
| §3.3.2 Mitigation Measures | Art. 9(4) | Risk mitigation | Remediation documentation |
| §4 Compliance Levels | Art. 9(7) | Proportionality | Level-based requirements |
| §6 Certification | Art. 43 | Conformity assessment | Third-party verification |

### 10.2 NIST AI RMF Mapping

| ONTO-ERS Clause | NIST AI RMF | Function | Subcategory |
|-----------------|-------------|----------|-------------|
| §3.3 Documentation | GOVERN | 1.1, 1.2 | Policies, accountability |
| §3.2.1 Benchmark Coverage | MAP | 1.1, 1.5 | Context, impacts |
| §3.1 Measurements | MEASURE | 2.5, 2.6 | Performance, trustworthiness |
| §3.3.2 Mitigation | MANAGE | 2.1, 2.3 | Response, monitoring |

### 10.3 ISO/IEC 23894 Mapping

| ONTO-ERS Clause | ISO 23894 Clause | Topic |
|-----------------|------------------|-------|
| §3.1 Measurements | 6.2, 6.3 | Risk identification, analysis |
| §3.3.1 Risk Assessment | 6.4 | Risk evaluation |
| §4 Compliance Levels | 6.5 | Risk treatment |
| §6 Certification | 7 | Monitoring, review |

### 10.4 Legal Citation Format

For regulatory submissions:

```
Per ONTO Epistemic Risk Standard v1.0 (ONTO-ERS-1.0), 
Section [X], the AI system demonstrates compliance with 
[EU AI Act Article Y / NIST AI RMF Function Z] through 
[specific measurement/documentation].

Reference: ONTO Standards Council. (2026). ONTO Epistemic 
Risk Standard (Version 1.0). https://onto-bench.org/standard
```

---

## 11. REVISION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | January 2026 | Initial publication |

---

## 10. CONTACT

**ONTO Standards Council**
standards@onto-bench.org
onto-bench.org/standard

---

## APPENDIX A: COMPLIANCE CHECKLIST

### A.1 Level 1 (Basic) Checklist

- [ ] Unknown Detection measured (≥30%)
- [ ] Calibration Error measured (≤0.20)
- [ ] Annual evaluation scheduled
- [ ] Risk level documented
- [ ] Limitations documented
- [ ] Mitigation measures documented

### A.2 Level 2 (Standard) Checklist

*All Level 1 requirements plus:*
- [ ] Unknown Detection ≥50%
- [ ] Calibration Error ≤0.15
- [ ] Quarterly evaluation scheduled
- [ ] Overconfidence Rate measured
- [ ] Audit trail initiated

### A.3 Level 3 (Advanced) Checklist

*All Level 2 requirements plus:*
- [ ] Unknown Detection ≥70%
- [ ] Calibration Error ≤0.10
- [ ] Monthly evaluation scheduled
- [ ] Third-party verification
- [ ] Complete audit trail
- [ ] Model version tracking

---

## APPENDIX B: CITATION

To cite this standard:

```
ONTO Standards Council. (2026). ONTO Epistemic Risk Standard 
(Version 1.0). ONTO-ERS-1.0. https://onto-bench.org/standard
```

For legal/regulatory reference:

```
Compliance with ONTO Epistemic Risk Standard v1.0 (ONTO-ERS-1.0), 
as maintained by the ONTO Standards Council, demonstrates adherence 
to epistemic calibration requirements aligned with EU AI Act 
Articles 9 and 13, and NIST AI RMF MEASURE function.
```

---

*ONTO Epistemic Risk Standard v1.0*
*© 2026 ONTO Standards Council*
*This standard is publicly available for adoption*
