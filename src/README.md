# Source Architecture

## Pipeline Overview

```
Clinical Transcript
        │
        ▼
┌─────────────────┐
│   extraction/    │  MedGemma LLM extraction + deterministic post-processing
│                  │
│  medgemma_client │  HuggingFace Inference API → structured JSON
│  post_processor  │  Transcript markers, validation, terminology enrichment
│  icd10_lookup    │  ICD-10-CM code matching (500+ conditions)
│  rxnorm_lookup   │  RxNorm code matching (200+ medications)
│  loinc_lookup    │  LOINC code matching (100+ lab tests)
│  order_diagnosis │  Clinical rules linking orders → diagnoses
│  prompts/        │  18 workflow-specific prompt templates
│  extraction_types│  Dataclass models for all clinical entities
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│     fhir/        │  FHIR R4 Bundle transformation
│  transformer     │  Entities → FHIR Resources (Condition, MedicationStatement, etc.)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│     export/      │  Multi-format healthcare output
│  fhir_r4         │  FHIR R4 Bundle (JSON)
│  cda             │  CDA R2 Document (XML) — Epic, legacy systems
│  hl7v2           │  HL7 v2.x Message (pipe-delimited) — Cerner, interfaces
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│      api/        │  FastAPI REST server
│  main            │  POST /api/v1/extract, /transform, /extract-and-transform
└─────────────────┘
```

## Module Details

### extraction/ — Core Pipeline (4-stage hybrid)

**Stage 1: MedGemma extraction** (`medgemma_client.py`)
- Sends transcript + workflow-specific prompt to MedGemma 4B via HuggingFace Inference API
- Supports dedicated endpoints, local servers, and serverless backends
- Returns structured JSON with conditions, medications, vitals, orders, allergies, history

**Stage 2: Deterministic post-processing** (`post_processor.py`)
- Extracts entities from transcript section markers (e.g., `[VITAL SIGNS]`)
- Validates and filters placeholder values
- Normalizes blood pressure format, fills missing medication doses

**Stage 3: Terminology enrichment** (`icd10_lookup.py`, `rxnorm_lookup.py`, `loinc_lookup.py`)
- Fuzzy-matches extracted entities against standard terminology databases
- Adds verified codes (ICD-10-CM, RxNorm, LOINC) with match confidence
- Flags unmatched items (`*_matched: false`) for clinician review

**Stage 4: Order-diagnosis linking** (`order_diagnosis_linker.py`)
- Links medication, lab, imaging, and procedure orders to supporting diagnoses
- Uses clinical rules (drug class → typical indications) and patient condition matching
- Generates ICD-10 codes for medical necessity documentation

**Prompt templates** (`prompts/`)
- 18 workflow-specific templates: general, SOAP, H&P, discharge, ED, cardiology, etc.
- Temperature 0.1 for low hallucination; max 8,192 tokens
- Each template emphasizes entity distinctions relevant to that workflow type

**Data models** (`extraction_types.py`)
- Python dataclasses for all entity types: `ClinicalEntities`, `Condition`, `Medication`, `MedicationOrder`, `LabOrder`, `Vital`, `Allergy`, `FamilyHistory`, `SocialHistory`, etc.

### fhir/ — FHIR R4 Transformation

Converts `ClinicalEntities` dataclasses into FHIR R4 Bundle resources. Maps conditions to `Condition`, medications to `MedicationStatement`, vitals to `Observation`, orders to `ServiceRequest`/`MedicationRequest`.

### export/ — Multi-Format Output

Three exporters accepting the same entity dict input:
- **FHIR R4** — JSON Bundle for modern EHR APIs (Epic FHIR, Cerner FHIR)
- **CDA R2** — XML Continuity of Care Document for Epic CDA import and legacy systems
- **HL7 v2.x** — Pipe-delimited messages for hospital interface engines

### api/ — REST Server

FastAPI application with endpoints for extraction, transformation, and combined workflows. Includes health check, workflow listing, and Swagger UI at `/docs`.
