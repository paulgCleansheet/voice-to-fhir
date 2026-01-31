# Voice-to-Health-Record: Clinical Documentation Extraction with MedGemma

**MedGemma Impact Challenge 2026 Submission**

**Team:** Cleansheet LLC
**Medical Advisor:** Leah Galjan Post, MD, FAAP

---

## 1. Problem Statement

Physician documentation burden is a healthcare crisis. The average physician spends 4.5 hours daily on documentation—more time than with patients. This burden drives burnout (63% of physicians report symptoms), reduces patient face time, and introduces errors as clinicians rush through EHR data entry.

The core problem is a **translation gap**: clinicians speak and think in natural clinical language, but EHRs require structured, coded data. Current solutions either:
- Require expensive scribes ($30-50K/year per physician)
- Provide transcription without structuring (Dragon Medical)
- Use proprietary systems with limited interoperability (Nuance DAX)

**We need an open, accurate, and affordable solution that transforms clinical language into structured health records.**

---

## 2. Solution: Voice-to-Health-Record (v2hr)

v2hr is an end-to-end clinical extraction pipeline that transforms natural language clinical transcripts into structured, coded healthcare data using Google's MedGemma medical language model.

### Architecture

```
Clinical Transcript → MedGemma Extraction → Terminology Validation → Multi-Format Output
                           │                        │                       │
                    Medical LLM              RxNorm/ICD-10/LOINC       FHIR R4/CDA/HL7v2
```

### Key Capabilities

**1. MedGemma-Powered Extraction**
- Uses `google/medgemma-4b-it` for clinical entity recognition
- Workflow-specific prompts optimized for 15 clinical scenarios (ED, H&P, SOAP, discharge, etc.)
- Understands clinical context: distinguishes orders from findings, new medications from current medications

**2. Deterministic Post-Processing**
- Validates medications against RxNorm (89% match rate)
- Codes diagnoses against ICD-10-CM (92% match rate)
- Links orders to supporting diagnoses for medical necessity documentation
- Flags unverified items for clinician review

**3. Multi-Format Output**
- FHIR R4 Bundles (modern interoperability standard)
- CDA R2 Documents (Epic, legacy systems)
- HL7 v2.x Messages (Cerner, hospital interfaces)

### Extracted Entities

| Entity | Terminology | Clinical Use |
|--------|-------------|--------------|
| Conditions | ICD-10-CM | Diagnosis coding, problem list |
| Medications | RxNorm | Medication reconciliation |
| Medication Orders | RxNorm + diagnosis link | e-Prescribing |
| Lab Orders | LOINC + diagnosis link | Lab ordering |
| Vital Signs | LOINC | Flowsheet documentation |
| Allergies | — | Safety alerts |
| Family/Social History | — | Risk assessment |

---

## 3. MedGemma Advantage

### Benchmark Results

We evaluated v2hr against a rule-based baseline (regex pattern matching) on 181 independently annotated entities from 15 clinical transcripts:

| Entity Type | MedGemma F1 | Baseline F1 | Delta |
|-------------|-------------|-------------|-------|
| Conditions | 68% | 56% | **+12%** |
| Medications | 83% | 69% | **+14%** |
| Allergies | 89% | 0% | **+89%** |
| Family History | 80% | 0% | **+80%** |
| **Overall** | **66%** | **55%** | **+11%** |

**Key metric:** MedGemma recall (66%) significantly outperforms baseline (44%), a +22 percentage point improvement in entity detection.

### Why MedGemma Excels

**Complex Entity Recognition:** Rule-based extraction completely fails (0% F1) on:
- Allergies: "allergic to penicillin" requires semantic understanding
- Family history: "father had MI at 55" requires relationship parsing

MedGemma achieves 80-89% F1 on these entities that regex patterns cannot capture.

**Contextual Understanding:** MedGemma understands:
- Synonyms ("high blood pressure" = "hypertension" = I10)
- Implied diagnoses from clinical context
- Chief complaint identification from narrative

**Honest Assessment:** Both systems struggle with order detection (30% vs 24% F1). Distinguishing "start lisinopril" from "takes lisinopril" remains challenging and represents an area for future improvement.

---

## 4. Projected Clinical Impact

### Time Savings

| Metric | Value |
|--------|-------|
| Time saved per patient | 13 minutes |
| Daily time saved (25 patients) | 5.4 hours |
| Annual value per physician | $202,500 |

### Extraction Accuracy

| Entity Type | MedGemma Accuracy | Baseline Comparison |
|-------------|-------------------|---------------------|
| Medications | 83% F1 | +14% over baseline |
| Allergies | 89% F1 | Baseline fails (0%) |
| Conditions | 68% F1 | +12% over baseline |
| Overall | 66% F1 | +11% over baseline |

*Note: All extractions require clinician review before EHR entry.*

### Health Equity

v2hr enables affordable documentation automation for settings that cannot afford scribes or expensive enterprise solutions:

- **4,500 rural/underserved facilities** could deploy edge infrastructure for $2,000 each
- **96 million patients** in underserved areas could benefit
- **$2.25B annual value** created in safety-net settings

---

## 5. Deployment Options

### Cloud (Recommended for most)
- HuggingFace Inference Endpoint + Azure Container Apps
- Cost: $0.03-0.05 per extraction
- Setup: 2-4 hours

### Edge (Privacy-sensitive)
- On-premises GPU (NVIDIA L4 or Jetson Orin)
- Cost: $2,000 one-time
- Latency: <1 second

### EHR Integration
- **Epic:** FHIR R4 REST API, CDA import
- **Cerner:** HL7 v2.x interface, FHIR API
- **Others:** Generic FHIR R4 server compatibility

---

## 6. Responsible AI

### Safety Design

1. **Uncertainty Flagging:** Unverified items marked `*_matched: false` for review
2. **Clinician-in-the-Loop:** All extractions require human approval before EHR entry
3. **Deterministic Validation:** Post-processing catches hallucinated medications/codes
4. **Audit Logging:** Full request/response logging for compliance

### Limitations

- Not a medical device; requires clinician review
- Accuracy dependent on transcript quality
- Model may miss rare conditions or medications not in training data

---

## 7. Reproducibility

```bash
# Clone and install
git clone https://github.com/paulgCleansheet/voice-to-health-record.git
cd voice-to-health-record
pip install -e .

# Configure (see .env.example)
cp .env.example .env
# Edit .env with HuggingFace endpoint

# Run API server
uvicorn api.main:app --port 8001

# Run benchmark (compares MedGemma vs baseline against human-annotated ground truth)
python scripts/benchmark_v2_with_baseline.py
```

**Repository:** https://github.com/paulgCleansheet/voice-to-health-record
**License:** CC BY 4.0

---

## 8. Conclusion

v2hr demonstrates that MedGemma can transform clinical documentation by:

1. **Achieving 66% F1 extraction accuracy** with +11% improvement over rule-based baseline
2. **Capturing complex entities** (allergies, family history) that regex patterns completely miss
3. **Saving an estimated 13 minutes per patient** in documentation time
4. **Enabling affordable automation** for underserved settings
5. **Maintaining safety** through clinician-in-the-loop design

The hardest clinical NLP problems—allergy recognition, family history parsing, context understanding—are exactly where medical language models like MedGemma provide the greatest value. While 66% F1 indicates room for improvement, MedGemma's ability to extract entities that rule-based systems cannot even attempt (0% baseline on allergies/family history) demonstrates the fundamental advantage of medical language models.

**v2hr is open-source and designed for real clinical workflows with human-in-the-loop review.**

---

**Team:** Cleansheet LLC
**Medical Advisor:** Leah Galjan Post, MD, FAAP
**Security Advisor:** DugganUSA

---

*This project was developed for the MedGemma Impact Challenge 2026, demonstrating practical clinical applications of Google's Health AI Developer Foundations (HAI-DEF) models.*
