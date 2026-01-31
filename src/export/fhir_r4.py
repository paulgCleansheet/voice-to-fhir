"""
FHIR R4 Exporter

Transform approved clinical data to FHIR R4 Bundle format.
Wraps the existing FHIRTransformer with a dict-based input interface.

Copyright (c) 2026 Cleansheet LLC
License: CC BY 4.0
"""

from dataclasses import dataclass
from typing import Any
import json

from fhir.transformer import FHIRTransformer, FHIRConfig
from extraction.extraction_types import (
    ClinicalEntities,
    Condition,
    Medication,
    Vital,
    LabResult,
    LabOrder,
    MedicationOrder,
    ReferralOrder,
    ProcedureOrder,
    ImagingOrder,
    Allergy,
    FamilyHistory,
    SocialHistory,
    PatientDemographics,
)


@dataclass
class ExportResult:
    """Result of export operation."""
    format: str
    content: str
    content_type: str
    success: bool
    error: str | None = None


class FHIRR4Exporter:
    """Export approved clinical data to FHIR R4 Bundle."""

    def __init__(self, config: FHIRConfig | None = None):
        """Initialize exporter."""
        self.transformer = FHIRTransformer(config)
        self.format = "fhir_r4"
        self.content_type = "application/fhir+json"

    def export(
        self,
        approved_data: dict[str, Any],
        patient: dict[str, Any] | None = None,
        workflow: str = "general",
    ) -> ExportResult:
        """
        Export approved data to FHIR R4 Bundle.

        Args:
            approved_data: Dict with conditions, medications, vitals, allergies, orders
            patient: Optional patient demographics
            workflow: Workflow type for encounter context

        Returns:
            ExportResult with FHIR Bundle JSON
        """
        try:
            # Convert dict to ClinicalEntities dataclass
            entities = self._dict_to_entities(approved_data, patient, workflow)

            # Transform to FHIR Bundle
            bundle = self.transformer.transform(entities)

            # Serialize to JSON
            content = json.dumps(bundle, indent=2)

            return ExportResult(
                format=self.format,
                content=content,
                content_type=self.content_type,
                success=True,
            )

        except Exception as e:
            return ExportResult(
                format=self.format,
                content="",
                content_type=self.content_type,
                success=False,
                error=str(e),
            )

    def _dict_to_entities(
        self,
        data: dict[str, Any],
        patient: dict[str, Any] | None,
        workflow: str,
    ) -> ClinicalEntities:
        """Convert approved data dict to ClinicalEntities dataclass."""
        entities = ClinicalEntities(workflow=workflow)

        # Patient demographics
        if patient:
            entities.patient = PatientDemographics(
                name=patient.get("name"),
                gender=patient.get("gender"),
                date_of_birth=patient.get("date_of_birth"),
                mrn=patient.get("mrn"),
            )

        # Conditions
        for c in data.get("conditions", []):
            entities.conditions.append(Condition(
                name=c.get("name"),
                icd10=c.get("icd10"),
                snomed=c.get("snomed"),
                status=c.get("status", "active"),
                severity=c.get("severity"),
                is_chief_complaint=c.get("isChiefComplaint", False),
            ))

        # Medications (current)
        for m in data.get("medications", []):
            entities.medications.append(Medication(
                name=m.get("name"),
                dose=m.get("dose"),
                frequency=m.get("frequency"),
                route=m.get("route"),
                status=m.get("status", "active"),
                rxnorm=m.get("rxnorm"),
                is_new_order=m.get("isNewOrder", False),
            ))

        # Vitals
        for v in data.get("vitals", []):
            entities.vitals.append(Vital(
                type=v.get("type"),
                value=v.get("value"),
                unit=v.get("unit"),
                loinc=v.get("loinc"),
            ))

        # Allergies
        for a in data.get("allergies", []):
            entities.allergies.append(Allergy(
                substance=a.get("name") or a.get("substance"),
                reaction=a.get("reaction"),
                severity=a.get("severity"),
            ))

        # Lab Results
        for lr in data.get("labResults", []):
            entities.lab_results.append(LabResult(
                name=lr.get("name"),
                value=lr.get("value"),
                unit=lr.get("unit"),
                loinc=lr.get("loinc"),
                interpretation=lr.get("interpretation"),
                reference_range=lr.get("referenceRange"),
            ))

        # Orders
        orders = data.get("orders", {})

        # Lab orders
        for lo in orders.get("labs", []):
            entities.lab_orders.append(LabOrder(
                name=lo.get("name"),
                loinc=lo.get("loinc"),
            ))

        # Medication orders
        for mo in orders.get("medications", []):
            entities.medication_orders.append(MedicationOrder(
                name=mo.get("name"),
                dose=mo.get("dosage") or mo.get("dose"),
                frequency=mo.get("frequency"),
                instructions=mo.get("instructions"),
                rxnorm=mo.get("rxnorm"),
            ))

        # Consult/Referral orders
        for co in orders.get("consults", []):
            entities.referral_orders.append(ReferralOrder(
                specialty=co.get("specialty"),
                reason=co.get("reason"),
            ))

        # Procedure orders
        for po in orders.get("procedures", []):
            entities.procedure_orders.append(ProcedureOrder(
                name=po.get("name"),
            ))

        # Imaging orders
        for io in orders.get("imaging", []):
            entities.imaging_orders.append(ImagingOrder(
                name=io.get("name"),
            ))

        # Family history
        for fh in data.get("familyHistory", []):
            entities.family_history.append(FamilyHistory(
                relationship=fh.get("relationship"),
                condition=fh.get("condition"),
                age_of_onset=fh.get("ageOfOnset"),
                deceased=fh.get("deceased"),
            ))

        # Social history
        sh = data.get("socialHistory")
        if sh:
            entities.social_history = SocialHistory(
                tobacco=sh.get("tobacco"),
                alcohol=sh.get("alcohol"),
                drugs=sh.get("drugs"),
                occupation=sh.get("occupation"),
                living_situation=sh.get("living_situation"),
            )

        return entities
