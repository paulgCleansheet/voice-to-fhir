# Voice to FHIR: Clinical Documentation Extraction with MedGemma

**MedGemma Impact Challenge 2026 Submission**

**Team:** Cleansheet LLC
**Medical Advisor:** Leah Galjan Post, MD, FAAP

---

## 1. Problem Statement

Physician documentation burden is a healthcare crisis. The average physician spends 4.5 hours daily on documentation—more time than with patients. This burden drives burnout (63% of physicians report symptoms), reduces patient face time, and introduces errors as clinicians rush through EHR data entry.

The core problem is a **translation gap**: clinicians speak and think in natural clinical language, but EHRs require structured, coded data. Current solutions either:
- Require scribes ($30-50K/year per physician)
- Provide transcription without structuring (Dragon Medical)
- Use proprietary systems with limited interoperability (Nuance DAX)

**We need an open, accurate, and affordable solution that transforms clinical language into structured health records.**

---

## 2. Solution: Voice to FHIR (voice-to-fhir)

voice-to-fhir is a **proof-of-concept** clinical extraction pipeline that transforms natural language clinical transcripts into structured, coded healthcare data using Google's MedGemma medical language model. This submission demonstrates a working end-to-end system with measurable results and a clear path to production-grade accuracy.

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

We evaluated voice-to-fhir against a rule-based baseline (regex pattern matching) on 199 entities from 16 clinical transcripts, annotated from human-authored clinical scripts:

| Entity Type | MedGemma F1 | Baseline F1 | Delta |
|-------------|-------------|-------------|-------|
| Conditions | 71% | 57% | **+14%** |
| Medications | 84% | 71% | **+12%** |
| Allergies | 84% | 0% | **+84%** |
| Family History | 82% | 0% | **+82%** |
| **Overall** | **69%** | **56%** | **+13%** |

**Key metric:** MedGemma recall (69%) significantly outperforms baseline (45%), a +24 percentage point improvement in entity detection.

### Why MedGemma Specifically

MedGemma's medical domain training is critical for this application. General-purpose LLMs lack the clinical vocabulary depth and medical reasoning patterns needed for reliable entity extraction from physician dictation. MedGemma's training on medical literature enables it to:

- **Recognize clinical relationships** that require domain knowledge — "father had MI at 55" requires understanding that MI is a condition, "father" indicates family history, and "55" is onset age
- **Parse allergy semantics** — "allergic to penicillin, causes rash" requires distinguishing the allergen, the reaction, and the clinical significance
- **Understand medical synonyms** — "high blood pressure" = "hypertension" = ICD-10 I10
- **Identify implied diagnoses** from clinical context and chief complaint narrative

**Complex Entity Recognition:** Rule-based extraction completely fails (0% F1) on allergies and family history. MedGemma achieves 82-84% F1 on these entities — the strongest evidence that a medical domain model is the right tool for this problem.

**Honest Assessment:** Both systems struggle with order detection (35% vs 23% F1). Distinguishing "start lisinopril" from "takes lisinopril" remains challenging and represents an area for future improvement.

### ASR Error Analysis

To isolate transcription errors from extraction errors, we compared MedGemma on real-world MedASR transcripts versus pristine original scripts:

| System | F1 Score |
|--------|----------|
| MedGemma + MedASR | 69% |
| MedGemma + Pristine | **77%** |
| Baseline (regex) | 56% |

**Key findings:**
- **ASR errors cost this model 9% F1** — MedASR transcription errors reduce MedGemma's performance from 77% to 69%
- **77% with clean input** — MedGemma's performance with pristine scripts (not a hard ceiling; a more robust model could potentially recover from ASR errors using clinical context)
- **Conditions most affected** (+15% with pristine) — clinical terminology transcription is challenging
- **Orders benefit significantly** (+14% with pristine) — order detection improves with clean input

This analysis demonstrates that improving ASR accuracy offers meaningful gains, but for this model, the majority of improvement opportunity lies in the extraction model itself.

### Path to Production: Improvement Roadmap

This proof of concept establishes 69% F1 as a baseline. We have identified specific, measurable improvements based on our architecture and benchmark analysis:

| Improvement | Estimated Gain | Basis |
|-------------|---------------|-------|
| **Order prompt engineering** | +1-2% F1 | Orders at 35% F1; pristine shows +14% with clean input |
| **ASR preprocessing & correction** | +4-6% F1 | Measured 8-point gap between pristine and ASR input |
| **MedGemma 27B model scaling** | +3-5% F1 | 6.75x larger model; standard NLP scaling gains |
| **Post-processing refinement** | +1% F1 | Current rules add 3%; room for deduplication, expanded terminology |
| **Projected production target** | | **78-83% F1** |

At 80% F1, the clinician's task shifts from *entering data* to *verifying data* — a fundamentally faster workflow. Combined with clinician review, effective documentation accuracy approaches 95%+.

These estimates assume gains are roughly additive, which may not hold. Diminishing returns are expected. See [IMPACT_ANALYSIS.md](IMPACT_ANALYSIS.md) for detailed analysis of each improvement.

---

## 4. Potential Clinical Impact

### Extraction Accuracy

| Entity Type | MedGemma Accuracy | Baseline Comparison |
|-------------|-------------------|---------------------|
| Medications | 84% F1 | +12% over baseline |
| Allergies | 84% F1 | Baseline fails (0%) |
| Conditions | 71% F1 | +14% over baseline |
| Overall | 69% F1 | +13% over baseline |

*Note: All extractions require clinician review before EHR entry. Ground truth is AI-assisted annotation from human-authored scripts; SME validation planned as future work.*

### Projected Time Savings

At 69% extraction accuracy, reviewing and correcting pre-populated structured output is significantly faster than manual entry from scratch. Based on published documentation time data (Sinsky et al., 2016) and our measured extraction performance:

- **8-13 minutes saved** per patient encounter (review vs. manual entry)
- **$100-200K estimated annual value** per physician (at $150/hr loaded cost)
- Potential **30-40% reduction** in documentation time for routine visits

These are projections based on published literature and measured performance, not validated in clinical deployment. See [IMPACT_ANALYSIS.md](IMPACT_ANALYSIS.md) for detailed calculations and assumptions.

### Health Equity Potential

Voice to FHIR's open-source, edge-deployable architecture could enable affordable documentation automation for ~4,500 rural and underserved facilities serving 96M patients who currently cannot access scribe services or enterprise AI solutions. Edge deployment costs $2,000 per facility — a fraction of annual scribe costs ($30-50K/physician/year).

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
- Benchmark ground truth is AI-assisted (not SME-validated); suitable for development testing and relative comparisons but not clinical validation
- Benchmark results represent development-stage evaluation with a small corpus (199 entities, 16 transcripts)

---

## 7. Demonstration Video

**Judges:** A walkthrough demonstration is included in the repository at [`demo/voice-to-fhir-demo.mp4`](demo/voice-to-fhir-demo.mp4). The video covers the end-to-end pipeline: transcript input, MedGemma extraction, terminology validation, and structured FHIR output.

## 8. Reproducibility

```bash
# Clone and install
git clone https://github.com/paulgCleansheet/voice-to-fhir.git
cd voice-to-fhir
pip install -e .

# Configure (see .env.example)
cp .env.example .env
# Edit .env with HuggingFace endpoint

# Run API server
uvicorn api.main:app --port 8001

# Run benchmark (compares MedGemma vs baseline against ground truth)
python scripts/benchmark_v2_with_baseline.py
```

**Repository:** https://github.com/paulgCleansheet/voice-to-fhir
**License:** CC BY 4.0

---

## 9. Conclusion

voice-to-fhir is a **proof of concept** that demonstrates MedGemma can power practical clinical documentation extraction:

1. **Working end-to-end pipeline** — transcript in, structured FHIR/CDA/HL7 out, in under 3 seconds
2. **69% F1 extraction accuracy** — +13% over rule-based baseline in development benchmarks
3. **Complex entity recognition** — allergies (84%) and family history (82%) where rules score 0%
4. **Clear path to production** — identified improvements targeting 78-83% F1 through prompt engineering, ASR integration, and model scaling
5. **Affordable and open** — $0.03/extraction cloud or $2K edge deployment, CC BY 4.0 licensed

The hardest clinical NLP problems — allergy recognition, family history parsing, context understanding — are exactly where medical language models like MedGemma provide the greatest value. MedGemma's ability to extract entities that rule-based systems cannot even attempt (0% baseline on allergies/family history) demonstrates the fundamental advantage of medical domain models.

This proof of concept establishes the architecture, measures the baseline, and maps the improvement path. The 69% → 80% journey is engineering work with identifiable steps — not research uncertainty.

**voice-to-fhir is open-source, designed for real clinical workflows, and ready for the next phase of development.**

---

**Team:** Cleansheet LLC
**Medical Advisor:** Leah Galjan Post, MD, FAAP
**Security Advisor:** DugganUSA

---

*This project was developed for the MedGemma Impact Challenge 2026, demonstrating practical clinical applications of Google's Health AI Developer Foundations (HAI-DEF) models.*
