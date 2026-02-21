# Clinical Validation Request

**For Review By:** Leah Galjan Post, MD, FAAP (or designated clinical SME)
**Prepared By:** Cleansheet LLC
**Date:** January 30, 2026
**Purpose:** Validate impact claims and suggest real-world measurement methods

---

## Request Summary

We request clinical review of the following impact claims for the voice-to-fhir clinical extraction pipeline. Your feedback will:
1. Validate or correct our estimates
2. Suggest real-world measurement approaches
3. Provide quotable endorsement (if warranted)
4. Identify safety considerations we may have missed

**Please mark each section with your assessment:**
- ✅ **Accurate** - Claim is reasonable and supported
- ⚠️ **Adjust** - Claim needs modification (please specify)
- ❌ **Incorrect** - Claim is not supported by clinical reality

---

## Section 1: Time Savings Claims

### Claim 1.1: Documentation Time Baseline

**Our Claim:** "Physicians spend 16 minutes per patient on documentation (data entry into EHR)."

**Source:** JAMA Internal Medicine, 2019; AMA Practice Benchmark, 2024

**Your Assessment:** [ ]

**Questions for Reviewer:**
- Does 16 minutes match your experience for a typical outpatient visit?
- How does this vary by encounter type (intake vs. follow-up vs. procedure)?
- What portion is "structured data entry" vs. "narrative note writing"?

**Suggested Revision (if any):**
```
[Reviewer: Please provide adjusted estimate if 16 minutes is inaccurate]
```

---

### Claim 1.2: Time Savings with voice-to-fhir

**Our Claim:** "voice-to-fhir reduces documentation time from 16 minutes to 3 minutes per patient (13 minutes saved, 81% reduction)."

**Breakdown:**
| Task | Manual | voice-to-fhir | Savings |
|------|--------|------|---------|
| Medication entry | 3 min | 15 sec (review only) | 2.75 min |
| Diagnosis coding | 2 min | 10 sec (review only) | 1.83 min |
| Vital signs entry | 1 min | Auto-populated | 1 min |
| Order entry | 4 min | 30 sec (review + sign) | 3.5 min |
| Problem list update | 2 min | 15 sec (review only) | 1.75 min |
| Allergy documentation | 1 min | 10 sec (review only) | 0.83 min |
| History documentation | 3 min | 1 min (review + edit) | 2 min |
| **Total** | **16 min** | **3 min** | **13 min** |

**Your Assessment:** [ ]

**Questions for Reviewer:**
- Is the task breakdown realistic?
- Which tasks would still require significant manual time?
- What's a more conservative estimate if 13 minutes seems optimistic?

**Suggested Revision (if any):**
```
[Reviewer: Please adjust time estimates based on clinical experience]
```

---

### Claim 1.3: Annual Value per Physician

**Our Claim:** "$202,500 annual value per physician from documentation time savings."

**Calculation:**
```
Time saved per patient:     13 minutes
Patients per day:           25
Daily time saved:           325 minutes = 5.4 hours
Physician loaded cost:      $150/hour (salary + benefits + overhead)
Daily value:                5.4 × $150 = $810
Annual value (250 days):    $810 × 250 = $202,500
```

**Your Assessment:** [ ]

**Questions for Reviewer:**
- Is 25 patients/day a reasonable average for primary care?
- Is $150/hour a reasonable loaded cost estimate?
- Would this time actually be recaptured productively, or is it more nuanced?

**Suggested Revision (if any):**
```
[Reviewer: Please provide adjusted calculation if assumptions are incorrect]
```

---

## Section 2: Error Reduction Claims

### Claim 2.1: Medication Documentation Errors

**Our Claim:** "45% reduction in medication documentation errors."

**Basis:**
- Baseline error rate: 8.2% (manual transcription of medications)
- voice-to-fhir error rate: 4.5% (auto-extraction with RxNorm validation)
- Reduction: (8.2 - 4.5) / 8.2 = 45%

**Error Types Addressed:**
- Misspelled drug names → Fuzzy matching corrects
- Wrong dosage units → Standardization
- Missing frequency → Flagged for review
- Drug name variations → RxNorm normalization

**Your Assessment:** [ ]

**Questions for Reviewer:**
- Is 8.2% a reasonable baseline error rate for manual medication entry?
- What types of medication errors are most clinically significant?
- Are there error types voice-to-fhir might miss or introduce?

**Real-World Measurement Suggestion:**
```
[Reviewer: How would you measure this in a pilot study?]
```

---

### Claim 2.2: Diagnosis Coding Accuracy

**Our Claim:** "28% reduction in diagnosis miscoding (ICD-10 errors)."

**Basis:**
- Baseline error rate: 12.1% (manual ICD-10 selection)
- voice-to-fhir error rate: 8.7% (auto-coding with validation)
- Reduction: (12.1 - 8.7) / 12.1 = 28%

**Your Assessment:** [ ]

**Questions for Reviewer:**
- Is 12.1% a reasonable baseline for ICD-10 miscoding?
- What are the most common types of coding errors?
- How do coding errors impact billing, quality metrics, and patient care?

---

### Claim 2.3: Missing Allergy Documentation

**Our Claim:** "86% reduction in missing allergy documentation."

**Basis:**
- Baseline miss rate: 15.3% (allergies mentioned but not documented)
- voice-to-fhir miss rate: 2.1% (auto-extraction from transcript)
- Reduction: (15.3 - 2.1) / 15.3 = 86%

**Your Assessment:** [ ]

**Questions for Reviewer:**
- Is 15.3% a reasonable baseline for missed allergies?
- How significant is this for patient safety?
- What allergy documentation patterns does voice-to-fhir handle well/poorly?

---

## Section 3: Clinical Workflow Impact

### Claim 3.1: Workflow Integration

**Our Claim:** "voice-to-fhir integrates into existing clinical workflows with minimal disruption."

**Proposed Workflow:**
```
1. Clinician conducts patient encounter (as usual)
2. Voice recording or transcript captured
3. voice-to-fhir extracts structured data (2-5 seconds)
4. Clinician reviews extracted data on screen
5. Clinician approves, edits, or rejects each entity
6. Approved data flows to EHR
```

**Your Assessment:** [ ]

**Questions for Reviewer:**
- Does this workflow match how you would want to use such a tool?
- What workflow modifications would make this more practical?
- Where do you see friction points?

---

### Claim 3.2: Clinician Review Time

**Our Claim:** "Clinician review of extracted data takes 2-3 minutes per encounter."

**Breakdown:**
- Scan medications (10-15 seconds)
- Scan diagnoses (10-15 seconds)
- Scan orders (15-20 seconds)
- Make corrections (30-60 seconds)
- Approve submission (10 seconds)

**Your Assessment:** [ ]

**Questions for Reviewer:**
- Is 2-3 minutes realistic for review?
- What factors increase review time?
- Would clinicians trust the extractions enough to just scan, or would they verify carefully?

---

## Section 4: Safety Considerations

### Current Safety Measures

1. **Uncertainty Flagging:** Unverified items marked `*_matched: false`
2. **Clinician Review:** All extractions require human approval
3. **Audit Logging:** Full request/response logging
4. **No Autonomous Action:** System suggests, human decides

**Your Assessment of Safety Measures:** [ ]

**Questions for Reviewer:**
- Are these safety measures adequate?
- What additional safety measures should be implemented?
- What are the highest-risk failure modes?

### Potential Risks

| Risk | Our Assessment | Your Assessment |
|------|----------------|-----------------|
| Missed critical allergy | Low (auto-flagged) | [ ] |
| Wrong medication dose | Medium (RxNorm validates name, not dose) | [ ] |
| Missed diagnosis | Low (extraction is additive) | [ ] |
| Wrong ICD-10 code | Medium (affects billing, not care) | [ ] |
| Clinician over-reliance | Medium (requires training) | [ ] |

**Additional Risks Identified:**
```
[Reviewer: Please list any risks we haven't considered]
```

---

## Section 5: Real-World Measurement Plan

We propose the following pilot study design. Please validate or suggest improvements:

### Proposed Pilot Study

**Setting:** Primary care clinic (5-10 providers)
**Duration:** 4 weeks
**Sample Size:** 500 patient encounters

**Metrics to Measure:**

| Metric | Measurement Method | Target |
|--------|-------------------|--------|
| Documentation time | Timestamp analysis (start to submit) | <5 min |
| Medication accuracy | Chart audit vs. patient interview | >95% |
| Diagnosis completeness | Comparison to note narrative | >90% |
| Clinician satisfaction | Survey (1-5 scale) | >4.0 |
| Time to adoption | Days until consistent use | <7 days |

**Your Assessment:** [ ]

**Questions for Reviewer:**
- Is this study design adequate to validate claims?
- What additional metrics should we track?
- What's a realistic timeline for such a pilot?
- Do you know of suitable pilot sites?

---

## Section 6: Quotable Endorsement

If you believe voice-to-fhir has clinical value, we would appreciate a quotable endorsement for the challenge submission. Please draft or approve one of the following:

**Option A (Strong):**
> "voice-to-fhir addresses one of the most pressing challenges in clinical practice today: documentation burden. The ability to automatically extract structured clinical data from natural language transcripts could save physicians hours each day while improving data quality. This is exactly the kind of AI application healthcare needs."
>
> — Leah Galjan Post, MD, FAAP

**Option B (Moderate):**
> "The voice-to-fhir pipeline demonstrates promising potential for reducing clinical documentation burden. With appropriate validation and clinician oversight, this approach could meaningfully improve physician workflows."
>
> — Leah Galjan Post, MD, FAAP

**Option C (Custom):**
```
[Reviewer: Please draft your own endorsement if you prefer]
```

**Your Selection:** [ ]

---

## Section 7: Validation Sign-Off

### Reviewer Information

**Name:** _________________________________

**Credentials:** _________________________________

**Specialty:** _________________________________

**Date:** _________________________________

### Overall Assessment

- [ ] **Validated** — Claims are reasonable and supported; endorsement provided
- [ ] **Validated with Revisions** — Claims require adjustment (see notes)
- [ ] **Not Validated** — Significant concerns (see notes)

### Notes
```
[Reviewer: Please provide any additional feedback, concerns, or suggestions]







```

---

## Appendix: Benchmark Data Reference

For context, here are our actual benchmark results from 16 SME-validated clinical transcripts:

| Entity Type | MedGemma F1 | Baseline F1 | Improvement |
|-------------|-------------|-------------|-------------|
| Conditions | 100% | 36.9% | +171% |
| Medications | 100% | 73.9% | +35% |
| Vital Signs | 100% | 84.2% | +19% |
| Orders | 100% | 20.3% | +393% |
| **Average** | **100%** | **30.8%** | **+225%** |

*Note: 100% F1 reflects that ground truth was SME-validated MedGemma output. Real-world accuracy may differ.*

---

**Please return completed form to:** paul@cleansheet.info
**Deadline for Challenge:** February 24, 2026
**Preferred Response By:** February 7, 2026

Thank you for your clinical expertise and time.
