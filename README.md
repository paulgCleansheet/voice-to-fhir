# Clinical Transcript Extraction Pipeline

Extract structured, coded clinical data from natural language transcripts using Google MedGemma.

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FHIR R4](https://img.shields.io/badge/FHIR-R4-orange.svg)](https://www.hl7.org/fhir/)

## Overview

This pipeline transforms clinical text transcripts into structured, coded healthcare data using Google's MedGemma medical language model with deterministic post-processing validation.

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Clinical   │───▶│  MedGemma   │───▶│    Post-    │───▶│  FHIR R4 /  │
│  Transcript │    │  Extraction │    │  Processor  │    │  CDA / HL7  │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

**Input:** Natural language clinical transcript (from any source)
**Output:** Structured FHIR R4 bundles, CDA documents, or HL7 v2 messages

## MedGemma Impact Challenge

This project was developed for the [Kaggle MedGemma Impact Challenge](https://www.kaggle.com/competitions/med-gemma-impact-challenge), demonstrating practical clinical applications of Google's Health AI Developer Foundations (HAI-DEF) models.

**Challenge Focus:** Build demonstration applications using MedGemma that showcase real-world healthcare impact with responsible AI practices.

## Features

- **MedGemma Integration** — Structured entity extraction using Google's medical language model
- **Terminology Validation** — Deterministic verification against RxNorm, ICD-10-CM, and LOINC databases
- **Order-Diagnosis Linking** — Automatic association of orders with supporting diagnoses
- **Multi-Format Output** — FHIR R4, CDA R2, and HL7 v2.x support
- **Uncertainty Flagging** — Unverified items explicitly marked for downstream review
- **API-First Design** — RESTful API for integration with any transcript source

## Benchmark Results

Development benchmarks evaluated against 199 entities from 16 clinical transcripts (AI-assisted annotation from human-authored scripts; SME validation planned), comparing MedGemma extraction vs. rule-based baseline:

| Entity Type | MedGemma F1 | Baseline F1 | Delta |
|-------------|-------------|-------------|-------|
| Conditions | 71% | 57% | **+14%** |
| Medications | 84% | 71% | **+12%** |
| Allergies | 84% | 0% | **+84%** |
| Family History | 82% | 0% | **+82%** |
| **Overall** | **69%** | **56%** | **+13%** |

### What This Means in Plain Terms

**F1 Score** measures how well the system finds the right information. It balances two questions:
- **Did it find everything?** (Recall) — Out of all the items that should be extracted, how many did it actually find?
- **Was it accurate?** (Precision) — Out of everything it extracted, how much was correct?

**In practical terms:**
- MedGemma correctly extracts **about 7 out of 10** clinical entities from physician dictation
- The simple rule-based system only gets **about 1 out of 2** correct
- For allergies and family history, rule-based extraction **completely fails** (0%) while MedGemma succeeds (82-84%)

**Why this matters:** A physician dictating "patient is allergic to penicillin, father had heart attack at 55" will have both items captured by MedGemma. Rule-based regex patterns miss them entirely.

**ASR Error Analysis:** With pristine transcripts (no transcription errors), MedGemma achieves **77% F1** — a 9 percentage point improvement. This represents this model's performance with clean input, not a hard ceiling.

See [BENCHMARKS.md](BENCHMARKS.md) for detailed methodology and results.

### Reproducing Benchmark Results

All data required to reproduce these results is included in the repository:

```bash
# Run MedGemma vs Baseline comparison
python scripts/benchmark_v2_with_baseline.py

# Run ASR error analysis (requires HuggingFace API token)
cp .env.example .env
# Edit .env with your HF_API_TOKEN
python scripts/benchmark_pristine.py --verbose
```

**Test data included:**
- `tests/fixtures/recordings/*.expected.json` — 16 ground truth files (199 entities)
- `tests/fixtures/scripts/script.md` — Pristine dictation scripts
- `tests/fixtures/bulk-export.json` — MedGemma+ASR extraction results

See [docs/IMPACT_ANALYSIS.md](docs/IMPACT_ANALYSIS.md) for projected clinical impact analysis.

## Extracted Entities

| Entity Type | Terminology | Output |
|-------------|-------------|--------|
| Conditions/Diagnoses | ICD-10-CM | Coded conditions with clinical status |
| Medications | RxNorm | Current medications with dosage |
| Medication Orders | RxNorm | New prescriptions with frequency, instructions |
| Lab Orders | LOINC | Laboratory test requests |
| Allergies | — | Substance and reaction |
| Vital Signs | LOINC | BP, HR, Temp, SpO2, Weight, Height |
| Consult Orders | — | Specialty referrals with reason |
| Procedure Orders | CPT | Imaging, procedures with indication |

## Quick Start

### Prerequisites

- Python 3.10+
- HuggingFace account with MedGemma access

### Installation

```bash
# Clone repository
git clone https://github.com/paulgCleansheet/voice-to-health-record.git
cd voice-to-health-record

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or: .venv\Scripts\activate  # Windows

# Install package and dependencies
pip install -e .
```

### Configuration

Create a `.env` file with your HuggingFace endpoint:

```bash
# MedGemma Endpoint Configuration
MEDGEMMA_ENDPOINT=https://your-endpoint.endpoints.huggingface.cloud
HF_TOKEN=hf_your_token_here
```

**Setting up your MedGemma endpoint:**

1. Go to [HuggingFace](https://huggingface.co) and create an account
2. Request access to [MedGemma](https://huggingface.co/google/medgemma-4b-it) model
3. Create an Inference Endpoint:
   - Navigate to Inference Endpoints
   - Select `google/medgemma-4b-it` model
   - Choose GPU instance (recommended: NVIDIA L4 or A10G)
   - Deploy and copy the endpoint URL
4. Generate an access token with `read` permissions

### Running the API Server

```bash
# Start the API server
python -m uvicorn api.main:app --host 0.0.0.0 --port 8001

# Server will be available at http://localhost:8001
# API documentation at http://localhost:8001/docs
```

### Docker (Alternative)

```bash
# Copy environment file and configure
cp .env.example .env
# Edit .env with your HuggingFace endpoint and token

# Build and run with Docker Compose
docker-compose up -d

# Or build manually
docker build -t voice-to-health-record .
docker run -p 8001:8001 --env-file .env voice-to-health-record
```

## API Usage

### Extract from Transcript

```bash
curl -X POST http://localhost:8001/api/v1/extract \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Patient is a 55-year-old male with type 2 diabetes and hypertension. Current medications include metformin 1000mg twice daily and lisinopril 20mg daily. Blood pressure today 142/88. Start atorvastatin 20mg daily for hyperlipidemia. Order HbA1c and lipid panel.",
    "workflow": "general"
  }'
```

### Response

```json
{
  "conditions": [
    {"name": "Type 2 diabetes", "icd10": "E11.9", "status": "active"},
    {"name": "Hypertension", "icd10": "I10", "status": "active"},
    {"name": "Hyperlipidemia", "icd10": "E78.5", "status": "active"}
  ],
  "medications": [
    {"name": "Metformin", "dosage": "1000mg twice daily", "rxnorm": "861004", "rxnorm_matched": true},
    {"name": "Lisinopril", "dosage": "20mg daily", "rxnorm": "314076", "rxnorm_matched": true}
  ],
  "orders": {
    "medications": [
      {"name": "Atorvastatin", "dosage": "20mg daily", "rxnorm": "617312", "linked_diagnosis": {"icd10": "E78.5", "display": "Hyperlipidemia"}}
    ],
    "labs": [
      {"name": "Hemoglobin A1c", "loinc": "4548-4", "linked_diagnosis": {"icd10": "E11.9", "display": "Type 2 diabetes"}},
      {"name": "Lipid Panel", "loinc": "24331-1", "linked_diagnosis": {"icd10": "E78.5", "display": "Hyperlipidemia"}}
    ]
  },
  "vitals": [
    {"type": "Blood Pressure", "value": "142/88", "unit": "mmHg"}
  ]
}
```

### Transform to FHIR/CDA/HL7

```bash
# Get FHIR R4 Bundle
curl -X POST http://localhost:8001/api/v1/transform \
  -H "Content-Type: application/json" \
  -d '{"extracted_data": {...}, "format": "fhir-r4"}'

# Get CDA Document
curl -X POST http://localhost:8001/api/v1/transform \
  -H "Content-Type: application/json" \
  -d '{"extracted_data": {...}, "format": "cda"}'

# Get HL7 v2 Message
curl -X POST http://localhost:8001/api/v1/transform \
  -H "Content-Type: application/json" \
  -d '{"extracted_data": {...}, "format": "hl7v2"}'
```

## Workflow Types

The `workflow` parameter optimizes extraction for specific clinical contexts:

| Workflow | Focus | Use Case |
|----------|-------|----------|
| `general` | Balanced extraction | General documentation |
| `emergency` | Chief complaint, acuity, critical findings | ED encounters |
| `intake` | History, medications, allergies, social history | New patient visits |
| `charting` | Assessment, plan, orders | Progress notes |
| `medication-reconciliation` | Current medications, doses, changes | Medication review |

## Architecture

```
src/
├── extraction/
│   ├── medgemma_client.py      # MedGemma API integration
│   ├── prompts/                # Workflow-specific extraction prompts
│   ├── post_processor.py       # Transcript parsing, cleanup
│   ├── rxnorm_lookup.py        # Medication verification
│   ├── icd10_lookup.py         # Diagnosis coding
│   └── order_diagnosis_linker.py # Medical necessity linking
├── export/
│   ├── fhir_r4.py              # FHIR R4 bundle generation
│   ├── cda.py                  # CDA document generation
│   └── hl7v2.py                # HL7 v2.x message generation
└── api/
    └── main.py                 # FastAPI server
```

## Post-Processing Pipeline

The extraction output undergoes deterministic validation:

1. **Medication Verification** — Names matched against RxNorm database using fuzzy string matching; unmatched medications flagged as `rxnorm_matched: false`

2. **Diagnosis Coding** — Condition names matched against ICD-10-CM database; codes assigned only when confident match found

3. **Order-Diagnosis Linking** — Orders automatically linked to supporting diagnoses using semantic similarity; supports medical necessity documentation

4. **Placeholder Removal** — AI placeholder values (e.g., "[value]", "XX mg") removed from output

5. **Verification Flagging** — All unverified items explicitly marked for downstream clinical review

## Testing

```bash
# Test the API health endpoint
curl http://localhost:8001/health

# Test extraction with a sample transcript
curl -X POST http://localhost:8001/api/v1/extract \
  -H "Content-Type: application/json" \
  -d '{"transcript": "55 year old male with hypertension on lisinopril 10mg daily.", "workflow": "general"}'
```

## Terminology Databases

This project uses publicly available terminology databases embedded in the source code:

- **RxNorm** — National Library of Medicine medication database (common medications)
- **ICD-10-CM** — CMS diagnosis code set (common diagnoses)
- **LOINC** — Regenstrief Institute laboratory codes (common lab tests)

Terminology matching uses fuzzy string matching to handle variations in naming.

## Acknowledgments

- **Google Health AI** — MedGemma model and HAI-DEF framework
- **National Library of Medicine** — RxNorm and UMLS terminologies
- **HL7 International** — FHIR R4 specification
- **Regenstrief Institute** — LOINC terminology

### Contributors

- Clinical workflow design and validation: **Leah Galjan Post, MD, FAAP**
- Security and regulatory compliance: **[DugganUSA](https://dugganusa.com)**

## License

This project is licensed under [CC BY 4.0](LICENSE).

When using this software, please provide attribution:

> Clinical Transcript Extraction Pipeline by Cleansheet LLC

## Disclaimer

This software is intended for research and development purposes. It is **not** a medical device and has **not** been cleared or approved by the FDA or any other regulatory body for clinical use.

Extracted data should be reviewed by qualified healthcare professionals before being used for clinical decision-making.

---

© 2026 Cleansheet LLC. All rights reserved.
