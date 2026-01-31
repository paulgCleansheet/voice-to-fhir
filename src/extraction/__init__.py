"""
Clinical Transcript Extraction Pipeline

Extract structured, coded clinical data from natural language transcripts using Google MedGemma.

Copyright (c) 2026 Cleansheet LLC
License: CC BY 4.0
"""

from extraction.extraction_types import (
    ClinicalEntities,
    Condition,
    Medication,
    MedicationOrder,
    Vital,
    LabResult,
    LabOrder,
    ReferralOrder,
    ProcedureOrder,
    ImagingOrder,
    Allergy,
    FamilyHistory,
    SocialHistory,
    PatientDemographics,
)

from extraction.medgemma_client import MedGemmaClient, MedGemmaClientConfig
from extraction.post_processor import post_process
from extraction.icd10_lookup import enrich_conditions_with_icd10, lookup_icd10
from extraction.rxnorm_lookup import enrich_medications_with_rxnorm, lookup_rxnorm, get_drug_class
from extraction.order_diagnosis_linker import (
    enrich_orders_with_diagnoses,
    link_medication_to_diagnosis,
    link_lab_to_diagnosis,
    link_consult_to_diagnosis,
    link_procedure_to_diagnosis,
)

__all__ = [
    # Types
    "ClinicalEntities",
    "Condition",
    "Medication",
    "MedicationOrder",
    "Vital",
    "LabResult",
    "LabOrder",
    "ReferralOrder",
    "ProcedureOrder",
    "ImagingOrder",
    "Allergy",
    "FamilyHistory",
    "SocialHistory",
    "PatientDemographics",
    # Client
    "MedGemmaClient",
    "MedGemmaClientConfig",
    # Post-processing
    "post_process",
    # Lookups
    "enrich_conditions_with_icd10",
    "lookup_icd10",
    "enrich_medications_with_rxnorm",
    "lookup_rxnorm",
    "get_drug_class",
    # Order-diagnosis linking
    "enrich_orders_with_diagnoses",
    "link_medication_to_diagnosis",
    "link_lab_to_diagnosis",
    "link_consult_to_diagnosis",
    "link_procedure_to_diagnosis",
]
