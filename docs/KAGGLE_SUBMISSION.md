# Voice to FHIR

### Project name
Voice to FHIR

### Your team
**Cleansheet LLC** — Technical architecture, pipeline development, benchmarking

**Leah Galjan Post, MD, FAAP** — Clinical workflow design, medical advisory

**DugganUSA** — Security and regulatory compliance advisory

---

### Problem statement

Physicians spend 4.5 hours daily on documentation — more time than with patients. The core problem is a translation gap: clinicians speak in natural language, but EHRs require structured, coded data (RxNorm medication codes, ICD-10 diagnoses, LOINC lab identifiers). Current solutions are inadequate: scribes cost $30–50K/year per physician, voice transcription tools like Dragon produce unstructured text, and ambient AI systems like Nuance DAX are proprietary and expensive.

The impact falls hardest on underserved settings. Approximately 4,500 rural hospitals, FQHCs, and critical access hospitals serving 96 million patients cannot afford these solutions at all. An open, affordable, accurate alternative is a genuine access issue, not just an efficiency one.

---

### Overall solution

Voice to FHIR uses `google/medgemma-4b-it` to extract structured clinical entities from physician dictation and transform them into interoperable healthcare data formats (FHIR R4, CDA R2, HL7 v2.x).

MedGemma is the right model for this problem because clinical documentation requires medical reasoning that general-purpose LLMs cannot reliably provide. The clearest evidence: on our benchmark corpus, rule-based extraction scores **0% F1** on allergies and family history — entities that require understanding clinical context, not pattern matching. MedGemma scores **84% and 82% F1** on those same entity types.

The pipeline pairs MedGemma extraction with deterministic post-processing — fuzzy matching against RxNorm, ICD-10-CM, and LOINC databases — to validate and code what the model extracts. Unverified items are explicitly flagged for clinician review. Nothing enters the EHR without human approval.

Overall benchmark results against 199 entities from 16 clinical transcripts:

| Entity | MedGemma F1 | Baseline F1 |
|--------|-------------|-------------|
| Medications | 84% | 71% |
| Allergies | 84% | 0% |
| Family History | 82% | 0% |
| Conditions | 71% | 57% |
| **Overall** | **69%** | **56%** |

At 69% F1, the clinician's task shifts from entering data to reviewing pre-populated fields — a meaningfully faster workflow. Ground truth is AI-assisted annotation from human-authored scripts; SME validation is planned as future work.

---

### Technical details

**Architecture:** Three-stage pipeline — MedGemma extraction → deterministic terminology validation → multi-format export. Deployed as a FastAPI REST service with Docker.

**MedGemma integration:** 15 workflow-specific prompts tuned for clinical contexts (ED, H&P, SOAP, discharge, medication reconciliation, etc.). The model distinguishes "start lisinopril" (new order) from "takes lisinopril" (current medication) — a distinction rule-based systems cannot make.

**Post-processing:** Medications validated against RxNorm (89% match rate), diagnoses against ICD-10-CM (92%), lab orders against LOINC. Orders automatically linked to supporting diagnoses for medical necessity documentation.

**Output:** FHIR R4 Bundles (Epic, Azure FHIR), CDA R2 Documents (Epic chart import), HL7 v2.x Messages (Cerner, hospital interface engines).

**Deployment:** Cloud via HuggingFace Inference Endpoints at ~$0.04/extraction, or on-premises GPU (NVIDIA L4) for privacy-sensitive environments at ~$2,000 one-time cost — a fraction of annual scribe costs.

**Responsible AI:** All extractions require clinician approval before EHR entry. Unverified codes are flagged `*_matched: false`. The system suggests; the clinician decides.

**Repository:** [github.com/paulgCleansheet/voice-to-fhir](https://github.com/paulgCleansheet/voice-to-fhir) — CC BY 4.0
**Demo:** [https://youtu.be/4tIWJ4M27Xs](https://youtu.be/4tIWJ4M27Xs)
