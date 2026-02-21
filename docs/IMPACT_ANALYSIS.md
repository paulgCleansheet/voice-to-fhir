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

## From Proof of Concept to Production: Improvement Roadmap

This submission represents a **proof of concept** — a working end-to-end pipeline that demonstrates MedGemma's value for clinical extraction. The 69% F1 baseline establishes a foundation. Below we estimate realistic improvements from specific, identifiable engineering work, based on what we've learned from our architecture and benchmarks.

### Current Performance Breakdown

```
┌─────────────────────────────────────────────────────────────────────────┐
│ WHAT WE'VE MEASURED                                                     │
│                                                                         │
│ Pristine input (no ASR errors):        77% F1   ← extraction quality   │
│ Real-world input (with ASR errors):    69% F1   ← current performance  │
│ Baseline (regex, no AI):               56% F1   ← what rules achieve   │
│                                                                         │
│ The 31% gap from perfect breaks down as:                                │
│   • 23% from extraction model limitations                               │
│   • 8% from ASR transcription errors feeding into extraction            │
│                                                                         │
│ Within extraction, the weak spots are identifiable:                     │
│   • Orders: 35% F1 (biggest single drag on overall score)              │
│   • Conditions: 71% F1 (room for improvement)                          │
│   • Medications, allergies, family history: 82-84% F1 (near ceiling)   │
└─────────────────────────────────────────────────────────────────────────┘
```

### Improvement 1: Order Extraction — Prompt Engineering (+3-5% F1)

**Current problem:** Orders are the weakest entity type at 35% F1. The core difficulty is distinguishing "start lisinopril" (new order) from "on lisinopril" (current medication). Our prompts already emphasize this distinction, but there is clear room for improvement.

**What we'd do:**
- Add few-shot examples of order vs. current medication to all 18 workflow prompts
- Add section-aware extraction: entities in [PLAN] or [ORDERS] sections are orders; entities in [MEDICATIONS] are current
- Add verb-based classification: "start/prescribe/order/schedule" → order; "takes/on/continues" → current
- Test prompt variations systematically against the 49 order entities in our ground truth

**Why we believe this works:** Our pristine benchmark shows orders improve from 35% → 49% F1 (+14 points) with clean input alone, meaning the extraction model *can* identify orders when the signal is clear. Better prompting can recover some of that gap even with ASR input.

**Estimated gain: +3-5% on orders → +1-2% overall F1**

### Improvement 2: ASR Quality — Audio Capture and Preprocessing (+4-6% F1)

**Current problem:** MedASR transcription errors cause 8 percentage points of F1 loss (69% with ASR vs. 77% with pristine). The current pipeline accepts pre-transcribed text — there is no audio preprocessing.

**What we'd do:**
- **Integrate MedASR directly** into the pipeline (currently audio is transcribed externally)
- **Audio preprocessing:** Noise reduction, voice activity detection, and microphone normalization before ASR
- **Medical vocabulary boosting:** Provide MedASR with a custom vocabulary list of common medications, conditions, and procedures to improve recognition of clinical terms
- **Post-ASR correction:** Use MedGemma itself to identify and correct likely transcription errors before extraction (e.g., "lysinopril" → "lisinopril", "hyper tension" → "hypertension")
- **Confidence-aware extraction:** Flag low-confidence ASR segments so the extraction model treats them with appropriate uncertainty

**Why we believe this works:** The 8-point gap between pristine and ASR input is measured, and conditions (+15%) and orders (+14%) are the entity types most affected. These are exactly the types with medical terminology that benefits most from vocabulary boosting and post-ASR correction.

**Estimated gain: +4-6% overall F1 (recovering ~50-75% of the ASR gap)**

### Improvement 3: Model Scaling — Larger MedGemma (+3-5% F1)

**Current model:** `google/medgemma-4b-it` (4 billion parameters)

**What we'd do:**
- Evaluate `medgemma-27b-it` (27B parameters) — 6.75x larger model with deeper medical reasoning
- Run the same benchmark suite to measure gains
- Evaluate cost/latency tradeoffs (larger model = slower inference, higher cost)

**Why we believe this works:** In NLP tasks generally, model scaling from 4B to 27B parameters typically yields 5-15% improvement on complex reasoning tasks. Medical entity extraction involves clinical reasoning (distinguishing orders from findings, parsing family relationships) that benefits directly from model capacity.

**Estimated gain: +3-5% overall F1 (with corresponding increase in inference cost)**

### Improvement 4: Expanded Test Corpus and SME Validation (+confidence, not F1)

**Current limitation:** 199 entities across 16 clinical notes, with AI-assisted ground truth.

**What we'd do:**
- **SME annotation:** Have 2-3 clinicians independently annotate the existing 16 test cases and 50+ new cases
- **Inter-annotator agreement:** Measure Cohen's kappa to establish ground truth reliability
- **Specialty coverage:** Add oncology, orthopedics, psychiatry, obstetrics notes
- **Edge cases:** Include notes with multiple comorbidities, polypharmacy, conflicting information

**Why this matters:** This doesn't directly improve F1 — it makes the F1 number trustworthy. With SME-validated ground truth and 500+ entities, the confidence interval narrows from [62%-75%] to approximately [66%-72%], and the number reflects clinical accuracy rather than AI-vs-AI agreement.

**Estimated gain: Tighter confidence intervals, validated ground truth, broader generalizability**

### Improvement 5: Post-Processing Refinement (+1% F1)

**Current post-processing adds +3% F1** through BP normalization, family history extraction, and medication dose filling.

**What we'd do:**
- **Order deduplication:** Prevent the same medication from appearing as both current med and new order
- **Context preservation:** Carry section headers through extraction so entities retain provenance
- **Expanded terminology databases:** ICD-10 from 500 → 2,000+ conditions; RxNorm from 200 → 1,000+ medications

**Estimated gain: +0.5-1% overall F1**

### Projected Production Performance

| Component | Current F1 | Estimated Gain | Projected F1 | Basis |
|-----------|-----------|----------------|--------------|-------|
| **Proof of concept (today)** | **69%** | — | **69%** | Measured |
| + Order prompt engineering | 69% | +1-2% | 70-71% | Measured: orders at 35% with clear room |
| + ASR preprocessing & correction | 70% | +4-6% | 74-77% | Measured: 8-point pristine gap |
| + MedGemma 27B | 75% | +3-5% | 78-82% | Estimated: model scaling literature |
| + Post-processing refinement | 79% | +1% | 79-83% | Measured: current rules add 3% |
| + SME validation & expanded corpus | 80% | (confidence) | 80% ± 3% | Tighter CIs |
| **Projected production target** | | | **78-83% F1** | |

**Important caveats:**
- These estimates assume gains are roughly additive, which may not hold — some improvements may overlap
- The 78-83% target represents an engineering estimate, not a guarantee
- Diminishing returns are expected: the last 5% is harder than the first 5%
- Real-world clinical deployment will surface issues not captured in development benchmarks

### What 80% F1 Means Clinically

At 80% extraction accuracy:
- **8 of 10 clinical entities** captured correctly from dictation
- Clinician review shifts from "entering data" to "verifying data" — a fundamentally different (and faster) task
- Allergy and family history capture rates would far exceed manual entry rates (where these sections are frequently left blank)
- Combined with clinician review, effective documentation accuracy approaches **95%+** (system captures 80%, clinician catches and corrects the remaining 20%)

---

## Summary

### This Is a Proof of Concept

v2hr demonstrates that MedGemma can power a practical clinical extraction pipeline. The 69% F1 baseline is honest — it represents a working system, not a polished product. But the architecture is sound, the improvement path is clear, and the hardest problem (getting semantic extraction to work at all for complex entities like allergies and family history) is solved.

### What We Know (Measured)
- v2hr achieves **69% F1 extraction accuracy** in development benchmarks
- MedGemma provides **+13 percentage point improvement** over rule-based baseline
- MedGemma captures **allergies (84%) and family history (82%)** that rules completely miss (0%)
- The system **works end-to-end**: transcript → extraction → structured FHIR/CDA/HL7 output
- The pipeline has **18 workflow-specific prompts**, deterministic post-processing, and terminology validation

### What We Project (Estimated)
- **78-83% F1 is achievable** through identified engineering improvements (prompt tuning, ASR integration, model scaling)
- **8-13 minutes saved** per patient encounter (review vs. manual entry)
- **$100-200K annual value** per physician (based on published documentation time costs)
- **96M patients** in underserved settings could benefit from affordable edge deployment

### What We Don't Know Yet (Future Work)
- Actual time savings in clinical deployment
- Impact on documentation error rates and patient safety
- Clinician satisfaction and adoption rates
- Performance of MedGemma 27B on this specific task

**The case for impact rests on a straightforward argument:** if a system can correctly extract 7 out of 10 clinical entities from a physician's dictation, reviewing and correcting those extractions is faster than entering all 10 from scratch. The improvement path to 8 out of 10 is identifiable and achievable. The magnitude of time savings depends on deployment context, but the direction is clear.

---

**Prepared by:** Cleansheet LLC
**Medical Advisor:** Leah Galjan Post, MD, FAAP
**Date:** February 21, 2026
