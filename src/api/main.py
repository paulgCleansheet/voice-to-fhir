"""
V2HR API Server

FastAPI server for clinical transcript extraction and transformation.

Usage:
    uvicorn api.main:app --host 0.0.0.0 --port 8001

Copyright (c) 2026 Cleansheet LLC
License: CC BY 4.0
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Any
import os

from extraction import MedGemmaClient, MedGemmaClientConfig
from extraction.prompts import AVAILABLE_WORKFLOWS
from export import FHIRR4Exporter, CDAExporter, HL7v2Exporter


# =============================================================================
# Pydantic Models
# =============================================================================

class ExtractRequest(BaseModel):
    """Request model for extraction endpoint."""
    transcript: str = Field(..., description="Clinical transcript text")
    workflow: str = Field(default="general", description="Workflow type for optimized extraction")


class TransformRequest(BaseModel):
    """Request model for transformation endpoint."""
    extracted_data: dict[str, Any] = Field(..., description="Extracted clinical data")
    format: str = Field(default="fhir-r4", description="Output format: fhir-r4, cda, hl7v2")
    patient: dict[str, Any] | None = Field(default=None, description="Optional patient demographics")
    workflow: str = Field(default="general", description="Workflow context")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    medgemma_available: bool
    version: str = "1.0.0"


# =============================================================================
# FastAPI App
# =============================================================================

app = FastAPI(
    title="V2HR Clinical Extraction API",
    description="Extract structured, coded clinical data from transcripts using MedGemma",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize clients
_medgemma_client: MedGemmaClient | None = None
_fhir_exporter = FHIRR4Exporter()
_cda_exporter = CDAExporter()
_hl7v2_exporter = HL7v2Exporter()


def get_medgemma_client() -> MedGemmaClient:
    """Get or create MedGemma client."""
    global _medgemma_client
    if _medgemma_client is None:
        config = MedGemmaClientConfig.from_env()
        _medgemma_client = MedGemmaClient(config)
    return _medgemma_client


# =============================================================================
# Endpoints
# =============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    medgemma_available = False
    try:
        client = get_medgemma_client()
        medgemma_available = client.health_check()
    except Exception:
        pass

    return HealthResponse(
        status="healthy",
        medgemma_available=medgemma_available,
    )


@app.get("/api/v1/workflows")
async def list_workflows():
    """List available workflow types."""
    return {
        "workflows": AVAILABLE_WORKFLOWS,
        "default": "general",
    }


@app.post("/api/v1/extract")
async def extract_from_transcript(request: ExtractRequest):
    """
    Extract structured clinical entities from transcript.

    Uses MedGemma for extraction with deterministic post-processing
    for terminology validation (RxNorm, ICD-10, LOINC).
    """
    # Validate workflow
    if request.workflow not in AVAILABLE_WORKFLOWS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown workflow: {request.workflow}. Available: {AVAILABLE_WORKFLOWS}"
        )

    try:
        client = get_medgemma_client()
        entities = client.extract(request.transcript, request.workflow)

        # Convert to dict for JSON response
        return _entities_to_dict(entities)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@app.post("/api/v1/transform")
async def transform_to_format(request: TransformRequest):
    """
    Transform extracted data to standard healthcare format.

    Supported formats:
    - fhir-r4: FHIR R4 Bundle (JSON)
    - cda: CDA R2 Document (XML)
    - hl7v2: HL7 v2.x Message (pipe-delimited)
    """
    format_lower = request.format.lower().replace("-", "_")

    if format_lower == "fhir_r4":
        result = _fhir_exporter.export(
            request.extracted_data,
            request.patient,
            request.workflow,
        )
    elif format_lower == "cda":
        result = _cda_exporter.export(
            request.extracted_data,
            request.patient,
            request.workflow,
        )
    elif format_lower == "hl7v2":
        result = _hl7v2_exporter.export(
            request.extracted_data,
            request.patient,
            request.workflow,
        )
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown format: {request.format}. Supported: fhir-r4, cda, hl7v2"
        )

    if not result.success:
        raise HTTPException(
            status_code=500,
            detail=f"Transform failed: {result.error}"
        )

    return {
        "format": result.format,
        "content_type": result.content_type,
        "content": result.content,
    }


@app.post("/api/v1/extract-and-transform")
async def extract_and_transform(
    transcript: str,
    output_format: str = "fhir-r4",
    workflow: str = "general",
    patient: dict[str, Any] | None = None,
):
    """
    End-to-end: Extract from transcript and transform to format in one call.
    """
    # Extract
    if workflow not in AVAILABLE_WORKFLOWS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown workflow: {workflow}. Available: {AVAILABLE_WORKFLOWS}"
        )

    try:
        client = get_medgemma_client()
        entities = client.extract(transcript, workflow)
        extracted_data = _entities_to_dict(entities)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")

    # Transform
    format_lower = output_format.lower().replace("-", "_")

    if format_lower == "fhir_r4":
        result = _fhir_exporter.export(extracted_data, patient, workflow)
    elif format_lower == "cda":
        result = _cda_exporter.export(extracted_data, patient, workflow)
    elif format_lower == "hl7v2":
        result = _hl7v2_exporter.export(extracted_data, patient, workflow)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown format: {output_format}. Supported: fhir-r4, cda, hl7v2"
        )

    if not result.success:
        raise HTTPException(status_code=500, detail=f"Transform failed: {result.error}")

    return {
        "extracted": extracted_data,
        "transformed": {
            "format": result.format,
            "content_type": result.content_type,
            "content": result.content,
        }
    }


# =============================================================================
# Helpers
# =============================================================================

def _entities_to_dict(entities) -> dict[str, Any]:
    """Convert ClinicalEntities to API response dict."""
    result = {
        "workflow": entities.workflow,
        "chiefComplaint": getattr(entities, 'chief_complaint_text', None),
        "conditions": [],
        "medications": [],
        "vitals": [],
        "allergies": [],
        "labResults": [],
        "orders": {
            "medications": [],
            "labs": [],
            "consults": [],
            "procedures": [],
            "imaging": [],
        },
        "familyHistory": [],
        "socialHistory": None,
    }

    # Conditions
    for c in entities.conditions:
        result["conditions"].append({
            "name": c.name,
            "icd10": c.icd10,
            "snomed": getattr(c, 'snomed', None),
            "status": c.status,
            "severity": c.severity,
            "isChiefComplaint": c.is_chief_complaint,
        })

    # Medications
    for m in entities.medications:
        result["medications"].append({
            "name": m.name,
            "dose": m.dose,
            "frequency": m.frequency,
            "route": getattr(m, 'route', None),
            "rxnorm": m.rxnorm,
            "rxnormMatched": getattr(m, 'rxnorm_matched', False),
            "drugClass": getattr(m, 'drug_class', None),
            "status": m.status,
        })

    # Vitals
    for v in entities.vitals:
        result["vitals"].append({
            "type": v.type,
            "value": v.value,
            "unit": v.unit,
            "loinc": getattr(v, 'loinc', None),
        })

    # Allergies
    for a in entities.allergies:
        result["allergies"].append({
            "substance": a.substance,
            "reaction": a.reaction,
            "severity": a.severity,
        })

    # Lab results
    for lr in entities.lab_results:
        result["labResults"].append({
            "name": lr.name,
            "value": lr.value,
            "unit": lr.unit,
            "loinc": getattr(lr, 'loinc', None),
            "interpretation": lr.interpretation,
            "referenceRange": getattr(lr, 'reference_range', None),
        })

    # Medication orders
    for mo in entities.medication_orders:
        order = {
            "name": mo.name,
            "dose": mo.dose,
            "frequency": mo.frequency,
            "instructions": getattr(mo, 'instructions', None),
            "rxnorm": getattr(mo, 'rxnorm', None),
            "rxnormMatched": getattr(mo, 'rxnorm_matched', False),
        }
        linked = getattr(mo, 'linked_diagnosis', None)
        if linked:
            order["linkedDiagnosis"] = linked
        result["orders"]["medications"].append(order)

    # Lab orders
    for lo in entities.lab_orders:
        order = {
            "name": lo.name,
            "loinc": getattr(lo, 'loinc', None),
        }
        linked = getattr(lo, 'linked_diagnosis', None)
        if linked:
            order["linkedDiagnosis"] = linked
        result["orders"]["labs"].append(order)

    # Referral/consult orders
    for ro in entities.referral_orders:
        order = {
            "specialty": ro.specialty,
            "reason": ro.reason,
        }
        linked = getattr(ro, 'linked_diagnosis', None)
        if linked:
            order["linkedDiagnosis"] = linked
        result["orders"]["consults"].append(order)

    # Procedure orders
    for po in entities.procedure_orders:
        order = {
            "name": po.name,
        }
        linked = getattr(po, 'linked_diagnosis', None)
        if linked:
            order["linkedDiagnosis"] = linked
        result["orders"]["procedures"].append(order)

    # Imaging orders
    for io in entities.imaging_orders:
        order = {
            "name": io.name,
        }
        linked = getattr(io, 'linked_diagnosis', None)
        if linked:
            order["linkedDiagnosis"] = linked
        result["orders"]["imaging"].append(order)

    # Family history
    for fh in entities.family_history:
        result["familyHistory"].append({
            "relationship": fh.relationship,
            "condition": fh.condition,
            "ageOfOnset": fh.age_of_onset,
            "deceased": getattr(fh, 'deceased', None),
        })

    # Social history
    if entities.social_history:
        sh = entities.social_history
        result["socialHistory"] = {
            "tobacco": sh.tobacco,
            "alcohol": sh.alcohol,
            "drugs": sh.drugs,
            "occupation": sh.occupation,
            "livingSituation": getattr(sh, 'living_situation', None),
        }

    # Patient demographics
    if entities.patient:
        p = entities.patient
        result["patient"] = {
            "name": p.name,
            "gender": p.gender,
            "dateOfBirth": p.date_of_birth,
            "mrn": getattr(p, 'mrn', None),
        }

    return result


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
