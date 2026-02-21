# Clinical Impact Analysis

**Voice-to-Health-Record Extraction Pipeline**
**Date:** February 21, 2026

---

## Executive Summary

The v2hr clinical extraction pipeline addresses physician documentation burden — a well-documented healthcare crisis — by automating the extraction of structured clinical data from natural language transcripts using Google's MedGemma.

**What we measured:**
- **69% F1 extraction accuracy** across 6 entity types (199 entities, 16 clinical notes)
- **+13 percentage point improvement** over rule-based baseline
- **84% F1 on medications and allergies** — entities critical for patient safety
- **0% baseline on allergies and family history** — MedGemma captures what rules cannot

**What we project (with assumptions stated):**
- **8-13 minutes saved** per patient encounter (review vs. manual entry)
- Potential to reduce documentation time by **30-40%** for routine visits

All projections below are estimates based on published literature and our measured extraction performance. They are not validated in clinical deployment.

---

## The Problem: Documentation Burden

### Published Evidence

| Metric | Value | Source |
|--------|-------|--------|
| Daily documentation time | 4.5 hours | AMA Physician Practice Benchmark Survey, 2024 |
| Documentation time per encounter | 16 minutes avg | Sinsky et al., Annals of Internal Medicine, 2016 |
| EHR interaction as % of workday | 37% | Arndt et al., Annals of Internal Medicine, 2017 |
| Physician burnout rate | 63% | Medscape Physician Burnout Report, 2024 |
| After-hours EHR time ("pajama time") | 1.4 hours/day | Adler-Milstein & Zhao, JAMA, 2022 |

### The Translation Gap

Clinicians think and speak in natural clinical language. EHRs require structured, coded data. This translation is currently performed manually:

**Current workflow (manual):**
```
Dictation/Notes → Manual Review → Manual Data Entry → Manual Coding → EHR
    (5 min)          (3 min)          (5 min)           (3 min)
                                                              Total: ~16 min
```

**v2hr workflow (automated extraction + clinician review):**
```
Dictation/Notes → MedGemma Extraction → Auto-Coding → Clinician Review → EHR
    (0 min)           (3 seconds)        (instant)       (3-5 min)
                                                              Total: ~3-5 min
```

### Why Existing Solutions Fall Short

| Solution | Approach | Limitation |
|----------|----------|------------|
| Medical scribes | Human documentation | $30-50K/year per physician; labor shortage |
| Dragon Medical | Speech-to-text only | No structured extraction; still requires manual coding |
| Nuance DAX | Ambient AI scribe | Proprietary; $15-25K/physician/year; vendor lock-in |
| Suki AI | AI documentation | Closed source; limited EHR integration |
| **v2hr** | **MedGemma + post-processing** | **Open-source; $0.03/extraction cloud or $2K on-prem** |

---

## Projected Time Savings

### Assumptions (Stated Explicitly)

These projections are based on:
1. **Published literature** on documentation time per encounter (Sinsky et al., 2016)
2. **Our measured extraction accuracy** (69% F1 overall; 84% on medications/allergies)
3. **Estimated review time** based on BENCHMARKS-CLINICAL-REVIEW.md workflow analysis (3-5 min for clinician to review and correct structured output vs. 16 min for full manual entry)

We have **not validated these time savings in clinical deployment**. Actual savings will depend on note complexity, clinician comfort with the system, and EHR integration quality.

### Per-Encounter Estimates

| Encounter Type | Manual Documentation | v2hr + Review | Estimated Savings |
|----------------|---------------------|---------------|-------------------|
| Routine follow-up | 10 min | 2-3 min | **7-8 min** |
| General visit | 16 min | 3-5 min | **11-13 min** |
| H&P (comprehensive) | 25 min | 5-8 min | **17-20 min** |
| Emergency note | 12 min | 3-4 min | **8-9 min** |
| Discharge summary | 20 min | 5-7 min | **13-15 min** |

**Basis for review times:** At 69% extraction accuracy, roughly 7 of 10 entities are correct. The clinician reviews the structured output, corrects ~3 entities, and approves. This is faster than entering all 10 entities from scratch.

**Conservative estimate: 8 minutes saved per encounter (routine visits)**
**Moderate estimate: 13 minutes saved per encounter (general visits)**

### Per-Physician Annual Projections

**Conservative scenario (routine outpatient only):**
```
Time saved per patient:      8 minutes (conservative)
Patients per day:            20 (outpatient primary care)
Daily time saved:            160 minutes = 2.7 hours
Annual time saved:           2.7 hours × 250 working days = 667 hours

At $150/hr physician loaded cost:
Annual value per physician:  667 × $150 = $100,000
```

**Moderate scenario (mixed encounter types):**
```
Time saved per patient:      13 minutes (general visits)
Patients per day:            25 (mixed practice)
Daily time saved:            325 minutes = 5.4 hours
Annual time saved:           5.4 hours × 250 working days = 1,354 hours

At $150/hr physician loaded cost:
Annual value per physician:  1,354 × $150 = $203,000
```

**These are projections, not measured outcomes.** The $150/hr figure represents total cost-to-employer (salary + benefits + overhead), not physician salary alone.

---

## Quality Impact

### What We Measured (Development Benchmarks)

| Entity Type | v2hr F1 | Baseline F1 | Improvement |
|-------------|---------|-------------|-------------|
| Medications | 84% | 71% | +13 pp |
| Allergies | 84% | 0% | +84 pp |
| Conditions | 71% | 57% | +14 pp |
| Family History | 82% | 0% | +82 pp |
| Vitals | 82% | 88% | -6 pp |
| Orders | 35% | 23% | +12 pp |
| **Overall** | **69%** | **56%** | **+13 pp** |

*Ground truth: AI-assisted annotation from human-authored clinical scripts. SME validation planned. See BENCHMARKS.md for full methodology.*

### Where MedGemma Provides Unique Value

The strongest impact case is not overall accuracy — it's the entities that **rule-based systems completely cannot extract**:

- **Allergies (84% vs. 0%):** "Patient is allergic to penicillin, causes rash" — requires semantic understanding. Regex patterns cannot express this. Missing allergy documentation is a patient safety issue.

- **Family History (82% vs. 0%):** "Father had MI at 55, mother has diabetes" — requires relationship parsing. Critical for risk assessment. Currently under-documented in most EHRs.

These two entity types represent the highest clinical safety impact: allergies affect medication safety checks, and family history drives screening and prevention decisions.

### What We Have Not Measured

To be transparent, we have **not** measured:
- Error reduction rates in clinical deployment (no before/after study)
- Impact on medication safety events
- Impact on clinical decision-making quality
- Time savings in actual clinical workflows
- Clinician satisfaction or adoption rates

These would require a prospective clinical study, which is planned as future work.

---

## Health Equity Potential

### The Access Gap

Documentation automation is currently available only to well-resourced health systems:
- Medical scribes: $30-50K/year per physician — prohibitive for small practices
- Commercial AI scribes: $15-25K/year per physician — requires enterprise contracts
- Most solutions require cloud connectivity — problematic for privacy-sensitive or low-bandwidth settings

### How v2hr Addresses This

| Setting | Challenge | v2hr Approach | Cost |
|---------|-----------|---------------|------|
| Rural clinics | Cannot afford scribes | Self-hosted edge deployment | $2,000 one-time |
| Small practices | No IT department | Docker single-command setup | $0.03/extraction cloud |
| Safety-net hospitals | Documentation backlog | Batch processing | $2,000 one-time |
| FQHCs | High volume, low resources | API integration with existing EHR | $0.03/extraction cloud |

### Potential Reach

| Setting | US Facilities | Patients Served |
|---------|---------------|-----------------|
| Rural hospitals | ~1,800 | 46M rural Americans |
| FQHCs | ~1,400 | 30M underserved patients |
| Critical access hospitals | ~1,300 | 20M rural patients |
| **Total potential** | **~4,500 facilities** | **~96M patients** |

*Source: HRSA data warehouse, AHA hospital statistics*

**Infrastructure cost to serve all 4,500 facilities:** $9M (edge deployment at $2,000 each)

This is a **cost model**, not a deployment plan. Actual adoption depends on EHR integration, regulatory requirements, and clinician acceptance.

### Why Open Source Matters for Equity

Proprietary solutions create vendor lock-in and pricing barriers that disproportionately affect under-resourced settings. v2hr's open-source model (CC BY 4.0) means:

- **No per-physician licensing fees** — the software is free
- **Community-driven improvements** — specialized rules for cardiology, pediatrics, etc. benefit everyone
- **Local deployment** — no cloud dependency, no data leaving the facility
- **Transparency** — clinicians and administrators can audit the extraction logic

---

## Deployment Feasibility

### Cloud Deployment (Recommended for Most)

```
Cost:         $0.03-0.05 per extraction (HuggingFace Inference Endpoint)
Setup:        2-4 hours (Docker + environment configuration)
Scaling:      Automatic (HuggingFace manages infrastructure)
Maintenance:  Minimal (endpoint auto-scales)
```

### Edge/On-Premises Deployment (Privacy-Sensitive)

```
Hardware:     NVIDIA L4 GPU or Jetson Orin ($2,000 one-time)
Cost:         $0 per extraction after hardware
Setup:        1-2 days (hardware setup + Docker deployment)
Latency:      <1 second per extraction
Maintenance:  Standard IT server maintenance
```

### EHR Integration Points

| EHR System | Integration Method | Output Format |
|------------|-------------------|---------------|
| Epic | FHIR R4 REST API | FHIR R4 Bundle |
| Cerner | FHIR API / HL7 v2.x interface | FHIR R4 / HL7 v2 |
| Legacy systems | CDA R2 import | CDA R2 Document |
| Any FHIR server | Standard REST API | FHIR R4 Bundle |

---

## Clinical Safety Design

### Clinician-in-the-Loop

v2hr is designed as a **documentation aid, not an autonomous system**. Every extraction requires clinician review before EHR entry.

```
Transcript → MedGemma Extraction → Structured Output → Clinician Review → EHR
                                                            │
                                                            ├── Approve (entity correct)
                                                            ├── Edit (entity needs correction)
                                                            └── Reject (entity is wrong)
```

### Safety Features

| Risk | Mitigation |
|------|------------|
| Extraction errors (31% of entities) | All extractions flagged for clinician review |
| Hallucinated entities | Post-processing validation against RxNorm/ICD-10 databases |
| Unverified codes | Items marked `*_matched: false` for explicit review |
| Over-reliance on automation | System designed to require approval workflow |
| Audit trail | Full request/response logging for compliance |

### What This System Is Not

- **Not a medical device** — does not make clinical decisions
- **Not autonomous** — requires clinician approval for all extractions
- **Not a replacement for clinical judgment** — a time-saving tool only
- **Not validated for billing/coding** — ICD-10 codes require clinician verification

---

## Future Validation Roadmap

### Phase 1: SME Ground Truth Validation (Next)
- Clinical SMEs review the 16 existing test cases
- Establish inter-annotator agreement
- Refine ground truth where AI annotation was incorrect
- **Outcome:** Clinically validated benchmarks

### Phase 2: Prospective Time Study (3-6 months)
- Deploy in 1-2 willing practice sites
- Measure actual documentation time: before vs. after
- Record clinician review time per note
- **Outcome:** Validated time savings figures

### Phase 3: Quality Impact Study (6-12 months)
- Compare documentation completeness (before vs. after)
- Track allergy documentation rates
- Measure family history capture rates
- **Outcome:** Validated quality improvement metrics

### Phase 4: Multi-Site Expansion (12+ months)
- Deploy across multiple practice types
- Measure specialty-specific performance
- Track clinician adoption and satisfaction
- **Outcome:** Generalizability evidence

---

## Summary

### What We Know (Measured)
- v2hr achieves **69% F1 extraction accuracy** in development benchmarks
- MedGemma provides **+13 percentage point improvement** over rule-based baseline
- MedGemma captures **allergies and family history** that rules completely miss
- The system **works end-to-end**: voice → extraction → structured FHIR/CDA/HL7 output

### What We Project (Estimated)
- **8-13 minutes saved** per patient encounter (review vs. manual entry)
- **$100-200K annual value** per physician (based on published time costs)
- **96M patients** in underserved settings could benefit from affordable edge deployment

### What We Don't Know Yet (Future Work)
- Actual time savings in clinical deployment
- Impact on documentation error rates
- Clinician satisfaction and adoption rates
- Long-term quality improvement metrics

**The case for impact rests on a straightforward argument:** if a system can correctly extract 7 out of 10 clinical entities from a physician's dictation, reviewing and correcting those extractions is faster than entering all 10 from scratch. The magnitude of time savings depends on deployment context, but the direction is clear.

---

**Prepared by:** Cleansheet LLC
**Medical Advisor:** Leah Galjan Post, MD, FAAP
**Date:** February 21, 2026
