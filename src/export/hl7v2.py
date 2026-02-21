"""
HL7 v2.x Exporter

Transform approved clinical data to HL7 v2.x message format.
Generates ORU^R01 (Observation Result) messages for clinical data.

Copyright (c) 2026 Cleansheet LLC
License: CC BY 4.0
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
import uuid


@dataclass
class ExportResult:
    """Result of export operation."""
    format: str
    content: str
    content_type: str
    success: bool
    error: str | None = None


class HL7v2Exporter:
    """Export approved clinical data to HL7 v2.x Message."""

    # HL7 v2 constants
    FIELD_SEP = "|"
    COMPONENT_SEP = "^"
    REPEAT_SEP = "~"
    ESCAPE_CHAR = "\\"
    SUBCOMPONENT_SEP = "&"

    def __init__(self, version: str = "2.5.1"):
        """Initialize exporter."""
        self.version = version
        self.format = "hl7v2"
        self.content_type = "text/plain"

    def export(
        self,
        approved_data: dict[str, Any],
        patient: dict[str, Any] | None = None,
        workflow: str = "general",
    ) -> ExportResult:
        """
        Export approved data to HL7 v2.x Message.

        Args:
            approved_data: Dict with conditions, medications, vitals, allergies, orders
            patient: Optional patient demographics
            workflow: Workflow type for message context

        Returns:
            ExportResult with HL7 v2 message
        """
        try:
            segments = []

            # MSH - Message Header
            segments.append(self._create_msh(workflow))

            # PID - Patient Identification
            segments.append(self._create_pid(patient))

            # PV1 - Patient Visit
            segments.append(self._create_pv1(workflow))

            # OBR/OBX - Observations (vitals, lab results)
            obr_obx = self._create_observations(
                approved_data.get("vitals", []),
                approved_data.get("labResults", []),
            )
            segments.extend(obr_obx)

            # DG1 - Diagnoses
            for i, condition in enumerate(approved_data.get("conditions", []), 1):
                segments.append(self._create_dg1(i, condition))

            # AL1 - Allergies
            for i, allergy in enumerate(approved_data.get("allergies", []), 1):
                segments.append(self._create_al1(i, allergy))

            # RXA - Medications (current)
            for med in approved_data.get("medications", []):
                segments.append(self._create_rxa(med))

            # ORC/RXO - Orders
            orders = approved_data.get("orders", {})
            order_segments = self._create_orders(orders)
            segments.extend(order_segments)

            # Join segments with CR
            content = "\r".join(segments)

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

    def _create_msh(self, workflow: str) -> str:
        """Create MSH (Message Header) segment."""
        now = datetime.now(timezone.utc)
        timestamp = now.strftime("%Y%m%d%H%M%S")
        message_id = str(uuid.uuid4())[:20]

        fields = [
            "MSH",
            f"{self.COMPONENT_SEP}{self.REPEAT_SEP}{self.ESCAPE_CHAR}{self.SUBCOMPONENT_SEP}",
            "voice-to-fhir",  # Sending Application
            "CLEANSHEET",  # Sending Facility
            "EHR",  # Receiving Application
            "HOSPITAL",  # Receiving Facility
            timestamp,  # Date/Time of Message
            "",  # Security
            f"ORU{self.COMPONENT_SEP}R01",  # Message Type
            message_id,  # Message Control ID
            "P",  # Processing ID (P=Production)
            self.version,  # Version ID
        ]
        return self.FIELD_SEP.join(fields)

    def _create_pid(self, patient: dict[str, Any] | None) -> str:
        """Create PID (Patient Identification) segment."""
        patient = patient or {}

        # Parse name into components
        name = patient.get("name", "")
        name_parts = name.split() if name else ["", ""]
        family = name_parts[-1] if len(name_parts) > 0 else ""
        given = name_parts[0] if len(name_parts) > 1 else name_parts[0] if name_parts else ""

        # Format name: Family^Given
        formatted_name = f"{family}{self.COMPONENT_SEP}{given}"

        # Format DOB
        dob = patient.get("date_of_birth", "")
        if dob:
            dob = dob.replace("-", "")

        # Gender code
        gender = patient.get("gender", "")
        gender_code = ""
        if gender:
            g = gender.lower()
            gender_code = "M" if g in ("male", "m") else "F" if g in ("female", "f") else "U"

        fields = [
            "PID",
            "1",  # Set ID
            "",  # Patient ID (external)
            patient.get("mrn", "") + f"{self.COMPONENT_SEP}{self.COMPONENT_SEP}{self.COMPONENT_SEP}MR",  # Patient ID (internal)
            "",  # Alternate Patient ID
            formatted_name,  # Patient Name
            "",  # Mother's Maiden Name
            dob,  # Date of Birth
            gender_code,  # Sex
        ]
        return self.FIELD_SEP.join(fields)

    def _create_pv1(self, workflow: str) -> str:
        """Create PV1 (Patient Visit) segment."""
        # Map workflow to patient class
        patient_class_map = {
            "emergency": "E",
            "icu": "I",
            "intake": "O",
            "general": "O",
            "followup": "O",
            "procedure": "O",
            "discharge": "I",
        }
        patient_class = patient_class_map.get(workflow, "O")

        fields = [
            "PV1",
            "1",  # Set ID
            patient_class,  # Patient Class (I=Inpatient, O=Outpatient, E=Emergency)
            "",  # Assigned Patient Location
            "",  # Admission Type
            "",  # Preadmit Number
            "",  # Prior Patient Location
            "",  # Attending Doctor
            "",  # Referring Doctor
            "",  # Consulting Doctor
            "",  # Hospital Service
        ]
        return self.FIELD_SEP.join(fields)

    def _create_observations(
        self,
        vitals: list[dict[str, Any]],
        lab_results: list[dict[str, Any]],
    ) -> list[str]:
        """Create OBR and OBX segments for observations."""
        segments = []

        if not vitals and not lab_results:
            return segments

        # OBR - Observation Request
        now = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        obr_fields = [
            "OBR",
            "1",  # Set ID
            str(uuid.uuid4())[:20],  # Placer Order Number
            str(uuid.uuid4())[:20],  # Filler Order Number
            f"PANEL{self.COMPONENT_SEP}Clinical Observations{self.COMPONENT_SEP}L",  # Universal Service ID
            "",  # Priority
            now,  # Requested Date/Time
            now,  # Observation Date/Time
        ]
        segments.append(self.FIELD_SEP.join(obr_fields))

        # OBX for vitals
        obx_id = 1
        for vital in vitals:
            segments.append(self._create_obx(obx_id, vital, "vital"))
            obx_id += 1

        # OBX for lab results
        for lab in lab_results:
            segments.append(self._create_obx(obx_id, lab, "lab"))
            obx_id += 1

        return segments

    def _create_obx(
        self,
        set_id: int,
        data: dict[str, Any],
        obs_type: str,
    ) -> str:
        """Create OBX (Observation Result) segment."""
        # Determine value type
        value = str(data.get("value", ""))
        try:
            float(value.replace(",", ""))
            value_type = "NM"  # Numeric
        except ValueError:
            value_type = "ST"  # String

        # Get observation identifier
        if obs_type == "vital":
            name = data.get("type", "Unknown")
            code = data.get("loinc", "")
        else:
            name = data.get("name", "Unknown")
            code = data.get("loinc", "")

        # Format identifier: Code^Name^System
        identifier = f"{code}{self.COMPONENT_SEP}{name}{self.COMPONENT_SEP}LN" if code else f"{self.COMPONENT_SEP}{name}"

        # Units
        unit = data.get("unit", "")

        # Interpretation
        interp = data.get("interpretation", "")
        abnormal_flag = ""
        if interp:
            interp_lower = interp.lower()
            if "high" in interp_lower:
                abnormal_flag = "H"
            elif "low" in interp_lower:
                abnormal_flag = "L"
            elif "normal" in interp_lower:
                abnormal_flag = "N"
            elif "critical" in interp_lower:
                abnormal_flag = "AA"

        fields = [
            "OBX",
            str(set_id),  # Set ID
            value_type,  # Value Type
            identifier,  # Observation Identifier
            "",  # Observation Sub-ID
            value,  # Observation Value
            unit,  # Units
            "",  # Reference Range
            abnormal_flag,  # Abnormal Flags
            "",  # Probability
            "",  # Nature of Abnormal Test
            "F",  # Observation Result Status (F=Final)
        ]
        return self.FIELD_SEP.join(fields)

    def _create_dg1(self, set_id: int, condition: dict[str, Any]) -> str:
        """Create DG1 (Diagnosis) segment."""
        name = condition.get("name", "Unknown")
        icd10 = condition.get("icd10", "")

        # Diagnosis code: Code^Description^Coding System
        diag_code = f"{icd10}{self.COMPONENT_SEP}{name}{self.COMPONENT_SEP}ICD10" if icd10 else f"{self.COMPONENT_SEP}{name}"

        # Diagnosis type
        diag_type = "A"  # A=Admitting, F=Final, W=Working
        if condition.get("isChiefComplaint"):
            diag_type = "A"

        fields = [
            "DG1",
            str(set_id),  # Set ID
            "ICD10",  # Diagnosis Coding Method
            diag_code,  # Diagnosis Code
            "",  # Diagnosis Description (deprecated)
            datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"),  # Diagnosis Date/Time
            diag_type,  # Diagnosis Type
        ]
        return self.FIELD_SEP.join(fields)

    def _create_al1(self, set_id: int, allergy: dict[str, Any]) -> str:
        """Create AL1 (Allergy) segment."""
        substance = allergy.get("name", "") or allergy.get("substance", "Unknown")
        reaction = allergy.get("reaction", "")
        severity = allergy.get("severity", "")

        # Severity code
        severity_code = ""
        if severity:
            sev_lower = severity.lower()
            if "severe" in sev_lower or "life" in sev_lower:
                severity_code = "SV"
            elif "moderate" in sev_lower:
                severity_code = "MO"
            elif "mild" in sev_lower:
                severity_code = "MI"

        fields = [
            "AL1",
            str(set_id),  # Set ID
            "DA",  # Allergy Type (DA=Drug Allergy, FA=Food, MA=Misc, MC=Misc Contra)
            f"{self.COMPONENT_SEP}{substance}",  # Allergy Code/Description
            severity_code,  # Allergy Severity
            reaction,  # Allergy Reaction
        ]
        return self.FIELD_SEP.join(fields)

    def _create_rxa(self, medication: dict[str, Any]) -> str:
        """Create RXA (Pharmacy Administration) segment."""
        name = medication.get("name", "Unknown")
        rxnorm = medication.get("rxnorm", "")
        dose = medication.get("dose", "")
        route = medication.get("route", "")

        # Admin code: RxNorm^Name^System
        admin_code = f"{rxnorm}{self.COMPONENT_SEP}{name}{self.COMPONENT_SEP}RXN" if rxnorm else f"{self.COMPONENT_SEP}{name}"

        now = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")

        fields = [
            "RXA",
            "0",  # Give Sub-ID Counter
            "1",  # Administration Sub-ID Counter
            now,  # Date/Time Start of Administration
            now,  # Date/Time End of Administration
            admin_code,  # Administered Code
            dose or "1",  # Administered Amount
            "",  # Administered Units
            "",  # Administered Dosage Form
            "",  # Administration Notes
            "",  # Administering Provider
            "",  # Administered-at Location
            "",  # Administered Per (Time Unit)
            "",  # Administered Strength
            "",  # Administered Strength Units
            "",  # Substance Lot Number
            "",  # Substance Expiration Date
            "",  # Substance Manufacturer Name
            "",  # Substance/Treatment Refusal Reason
            "",  # Indication
            "",  # Completion Status
            "A",  # Action Code (A=Add)
        ]
        return self.FIELD_SEP.join(fields)

    def _create_orders(self, orders: dict[str, Any]) -> list[str]:
        """Create ORC and order detail segments."""
        segments = []
        order_num = 1

        # Lab orders
        for lab in orders.get("labs", []):
            segments.extend(self._create_lab_order(order_num, lab))
            order_num += 1

        # Medication orders
        for med in orders.get("medications", []):
            segments.extend(self._create_med_order(order_num, med))
            order_num += 1

        # Procedure orders
        for proc in orders.get("procedures", []):
            segments.extend(self._create_proc_order(order_num, proc))
            order_num += 1

        # Imaging orders
        for img in orders.get("imaging", []):
            segments.extend(self._create_imaging_order(order_num, img))
            order_num += 1

        return segments

    def _create_orc(self, order_num: int, order_control: str = "NW") -> str:
        """Create ORC (Common Order) segment."""
        now = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        order_id = f"ORD{order_num:05d}"

        fields = [
            "ORC",
            order_control,  # Order Control (NW=New, SC=Status Changed)
            order_id,  # Placer Order Number
            order_id,  # Filler Order Number
            "",  # Placer Group Number
            "SC",  # Order Status (SC=Scheduled)
            "",  # Response Flag
            "",  # Quantity/Timing
            "",  # Parent
            now,  # Date/Time of Transaction
        ]
        return self.FIELD_SEP.join(fields)

    def _create_lab_order(self, order_num: int, lab: dict[str, Any]) -> list[str]:
        """Create ORC and OBR for lab order."""
        segments = [self._create_orc(order_num)]

        name = lab.get("name", "Unknown")
        loinc = lab.get("loinc", "")
        service_id = f"{loinc}{self.COMPONENT_SEP}{name}{self.COMPONENT_SEP}LN" if loinc else f"{self.COMPONENT_SEP}{name}"

        now = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        obr_fields = [
            "OBR",
            str(order_num),  # Set ID
            f"ORD{order_num:05d}",  # Placer Order Number
            f"ORD{order_num:05d}",  # Filler Order Number
            service_id,  # Universal Service ID
            "R",  # Priority (R=Routine)
            now,  # Requested Date/Time
        ]
        segments.append(self.FIELD_SEP.join(obr_fields))

        return segments

    def _create_med_order(self, order_num: int, med: dict[str, Any]) -> list[str]:
        """Create ORC and RXO for medication order."""
        segments = [self._create_orc(order_num)]

        name = med.get("name", "Unknown")
        rxnorm = med.get("rxnorm", "")
        dose = med.get("dosage") or med.get("dose", "")
        frequency = med.get("frequency", "")
        instructions = med.get("instructions", "")

        # Requested Give Code: RxNorm^Name^System
        give_code = f"{rxnorm}{self.COMPONENT_SEP}{name}{self.COMPONENT_SEP}RXN" if rxnorm else f"{self.COMPONENT_SEP}{name}"

        rxo_fields = [
            "RXO",
            give_code,  # Requested Give Code
            dose or "1",  # Requested Give Amount - Minimum
            dose or "1",  # Requested Give Amount - Maximum
            "",  # Requested Give Units
            "",  # Requested Dosage Form
            "",  # Provider's Pharmacy/Treatment Instructions
            instructions,  # Provider's Administration Instructions
            "",  # Deliver-to Location
            "",  # Allow Substitutions
            "",  # Requested Dispense Code
            "",  # Requested Dispense Amount
            "",  # Requested Dispense Units
            "",  # Number of Refills
            "",  # Ordering Provider's DEA Number
            "",  # Pharmacist/Treatment Supplier's Verifier ID
            "",  # Needs Human Review
            frequency,  # Requested Give Per (Time Unit)
        ]
        segments.append(self.FIELD_SEP.join(rxo_fields))

        return segments

    def _create_proc_order(self, order_num: int, proc: dict[str, Any]) -> list[str]:
        """Create ORC and OBR for procedure order."""
        segments = [self._create_orc(order_num)]

        name = proc.get("name", "Unknown")
        service_id = f"{self.COMPONENT_SEP}{name}{self.COMPONENT_SEP}L"

        now = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        obr_fields = [
            "OBR",
            str(order_num),  # Set ID
            f"ORD{order_num:05d}",  # Placer Order Number
            f"ORD{order_num:05d}",  # Filler Order Number
            service_id,  # Universal Service ID
            "R",  # Priority
            now,  # Requested Date/Time
        ]
        segments.append(self.FIELD_SEP.join(obr_fields))

        return segments

    def _create_imaging_order(self, order_num: int, img: dict[str, Any]) -> list[str]:
        """Create ORC and OBR for imaging order."""
        # Same structure as procedure order
        return self._create_proc_order(order_num, img)
