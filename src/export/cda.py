"""
CDA R2 Exporter

Transform approved clinical data to CDA (Clinical Document Architecture) R2 format.
Generates a Continuity of Care Document (CCD) conformant XML.

Copyright (c) 2026 Cleansheet LLC
License: CC BY 4.0
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
import uuid
import xml.etree.ElementTree as ET


@dataclass
class ExportResult:
    """Result of export operation."""
    format: str
    content: str
    content_type: str
    success: bool
    error: str | None = None


class CDAExporter:
    """Export approved clinical data to CDA R2 Document."""

    # CDA namespaces
    CDA_NS = "urn:hl7-org:v3"
    SDTC_NS = "urn:hl7-org:sdtc"
    XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"

    # OID constants
    LOINC_OID = "2.16.840.1.113883.6.1"
    SNOMED_OID = "2.16.840.1.113883.6.96"
    ICD10_OID = "2.16.840.1.113883.6.90"
    RXNORM_OID = "2.16.840.1.113883.6.88"

    def __init__(self):
        """Initialize exporter."""
        self.format = "cda"
        self.content_type = "application/xml"

    def export(
        self,
        approved_data: dict[str, Any],
        patient: dict[str, Any] | None = None,
        workflow: str = "general",
    ) -> ExportResult:
        """
        Export approved data to CDA R2 Document.

        Args:
            approved_data: Dict with conditions, medications, vitals, allergies, orders
            patient: Optional patient demographics
            workflow: Workflow type for document context

        Returns:
            ExportResult with CDA XML
        """
        try:
            # Build CDA document
            root = self._create_document(approved_data, patient, workflow)

            # Serialize to XML string with declaration
            # Use indent for Python 3.9+
            try:
                ET.indent(root, space="  ")
            except AttributeError:
                pass  # Python < 3.9, no indentation

            content = '<?xml version="1.0" encoding="UTF-8"?>\n'
            content += ET.tostring(root, encoding="unicode")

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

    def _create_document(
        self,
        data: dict[str, Any],
        patient: dict[str, Any] | None,
        workflow: str,
    ) -> ET.Element:
        """Create CDA document structure."""
        # Root element with namespaces
        root = ET.Element("ClinicalDocument")
        root.set("xmlns", self.CDA_NS)
        root.set("xmlns:sdtc", self.SDTC_NS)
        root.set("xmlns:xsi", self.XSI_NS)

        # Header
        self._add_header(root, patient, workflow)

        # Record target (patient)
        self._add_record_target(root, patient)

        # Author
        self._add_author(root)

        # Custodian
        self._add_custodian(root)

        # Body with sections
        component = ET.SubElement(root, "component")
        structured_body = ET.SubElement(component, "structuredBody")

        # Add clinical sections
        self._add_problems_section(structured_body, data.get("conditions", []))
        self._add_medications_section(structured_body, data.get("medications", []))
        self._add_allergies_section(structured_body, data.get("allergies", []))
        self._add_vitals_section(structured_body, data.get("vitals", []))
        self._add_results_section(structured_body, data.get("labResults", []))
        self._add_plan_section(structured_body, data.get("orders", {}))

        return root

    def _add_header(
        self,
        root: ET.Element,
        patient: dict[str, Any] | None,
        workflow: str,
    ) -> None:
        """Add CDA header elements."""
        # Type ID
        type_id = ET.SubElement(root, "typeId")
        type_id.set("root", "2.16.840.1.113883.1.3")
        type_id.set("extension", "POCD_HD000040")

        # Template IDs for CCD
        template = ET.SubElement(root, "templateId")
        template.set("root", "2.16.840.1.113883.10.20.22.1.1")  # US Realm Header

        template2 = ET.SubElement(root, "templateId")
        template2.set("root", "2.16.840.1.113883.10.20.22.1.2")  # CCD

        # Document ID
        doc_id = ET.SubElement(root, "id")
        doc_id.set("root", str(uuid.uuid4()))

        # Document type code (LOINC)
        code = ET.SubElement(root, "code")
        code.set("code", "34133-9")
        code.set("codeSystem", self.LOINC_OID)
        code.set("codeSystemName", "LOINC")
        code.set("displayName", "Summarization of Episode Note")

        # Title
        title = ET.SubElement(root, "title")
        title.text = f"Clinical Summary - {workflow.replace('_', ' ').title()}"

        # Effective time
        effective_time = ET.SubElement(root, "effectiveTime")
        effective_time.set("value", datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"))

        # Confidentiality
        conf = ET.SubElement(root, "confidentialityCode")
        conf.set("code", "N")
        conf.set("codeSystem", "2.16.840.1.113883.5.25")

        # Language
        lang = ET.SubElement(root, "languageCode")
        lang.set("code", "en-US")

    def _add_record_target(
        self,
        root: ET.Element,
        patient: dict[str, Any] | None,
    ) -> None:
        """Add patient information."""
        record_target = ET.SubElement(root, "recordTarget")
        patient_role = ET.SubElement(record_target, "patientRole")

        # Patient ID
        pat_id = ET.SubElement(patient_role, "id")
        pat_id.set("root", "2.16.840.1.113883.19.5")
        pat_id.set("extension", patient.get("mrn", "UNKNOWN") if patient else "UNKNOWN")

        # Patient element
        pat_elem = ET.SubElement(patient_role, "patient")

        # Name
        name = ET.SubElement(pat_elem, "name")
        if patient and patient.get("name"):
            given = ET.SubElement(name, "given")
            given.text = patient["name"].split()[0] if " " in patient["name"] else patient["name"]
            if " " in patient.get("name", ""):
                family = ET.SubElement(name, "family")
                family.text = patient["name"].split()[-1]
        else:
            given = ET.SubElement(name, "given")
            given.text = "Unknown"

        # Gender
        gender = ET.SubElement(pat_elem, "administrativeGenderCode")
        gender_code = "UN"
        if patient and patient.get("gender"):
            g = patient["gender"].lower()
            gender_code = "M" if g in ("male", "m") else "F" if g in ("female", "f") else "UN"
        gender.set("code", gender_code)
        gender.set("codeSystem", "2.16.840.1.113883.5.1")

        # Birth time
        if patient and patient.get("date_of_birth"):
            birth = ET.SubElement(pat_elem, "birthTime")
            birth.set("value", patient["date_of_birth"].replace("-", ""))

    def _add_author(self, root: ET.Element) -> None:
        """Add author information."""
        author = ET.SubElement(root, "author")

        time = ET.SubElement(author, "time")
        time.set("value", datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"))

        assigned_author = ET.SubElement(author, "assignedAuthor")

        author_id = ET.SubElement(assigned_author, "id")
        author_id.set("root", "2.16.840.1.113883.19.5")
        author_id.set("extension", "V2HR")

        # Authoring device (software)
        device = ET.SubElement(assigned_author, "assignedAuthoringDevice")
        software = ET.SubElement(device, "softwareName")
        software.text = "V2HR Clinical Documentation System"

    def _add_custodian(self, root: ET.Element) -> None:
        """Add custodian information."""
        custodian = ET.SubElement(root, "custodian")
        assigned = ET.SubElement(custodian, "assignedCustodian")
        org = ET.SubElement(assigned, "representedCustodianOrganization")

        org_id = ET.SubElement(org, "id")
        org_id.set("root", "2.16.840.1.113883.19.5")

        name = ET.SubElement(org, "name")
        name.text = "Healthcare Organization"

    def _add_problems_section(
        self,
        body: ET.Element,
        conditions: list[dict[str, Any]],
    ) -> None:
        """Add Problems/Conditions section."""
        component = ET.SubElement(body, "component")
        section = ET.SubElement(component, "section")

        # Template ID
        template = ET.SubElement(section, "templateId")
        template.set("root", "2.16.840.1.113883.10.20.22.2.5.1")

        # Section code
        code = ET.SubElement(section, "code")
        code.set("code", "11450-4")
        code.set("codeSystem", self.LOINC_OID)
        code.set("displayName", "Problem List")

        # Title
        title = ET.SubElement(section, "title")
        title.text = "Problems"

        # Text (human readable)
        text = ET.SubElement(section, "text")
        if conditions:
            ul = ET.SubElement(text, "list")
            for c in conditions:
                item = ET.SubElement(ul, "item")
                item.text = f"{c.get('name', 'Unknown')} ({c.get('icd10', 'No code')})"
        else:
            para = ET.SubElement(text, "paragraph")
            para.text = "No known problems"

        # Entries
        for c in conditions:
            entry = ET.SubElement(section, "entry")
            act = ET.SubElement(entry, "act")
            act.set("classCode", "ACT")
            act.set("moodCode", "EVN")

            entry_rel = ET.SubElement(act, "entryRelationship")
            entry_rel.set("typeCode", "SUBJ")

            obs = ET.SubElement(entry_rel, "observation")
            obs.set("classCode", "OBS")
            obs.set("moodCode", "EVN")

            obs_code = ET.SubElement(obs, "code")
            obs_code.set("code", "64572001")
            obs_code.set("codeSystem", self.SNOMED_OID)
            obs_code.set("displayName", "Condition")

            value = ET.SubElement(obs, "value")
            value.set("xsi:type", "CD")
            if c.get("icd10"):
                value.set("code", c["icd10"])
                value.set("codeSystem", self.ICD10_OID)
            value.set("displayName", c.get("name", "Unknown"))

    def _add_medications_section(
        self,
        body: ET.Element,
        medications: list[dict[str, Any]],
    ) -> None:
        """Add Medications section."""
        component = ET.SubElement(body, "component")
        section = ET.SubElement(component, "section")

        template = ET.SubElement(section, "templateId")
        template.set("root", "2.16.840.1.113883.10.20.22.2.1.1")

        code = ET.SubElement(section, "code")
        code.set("code", "10160-0")
        code.set("codeSystem", self.LOINC_OID)
        code.set("displayName", "History of Medication Use")

        title = ET.SubElement(section, "title")
        title.text = "Medications"

        text = ET.SubElement(section, "text")
        if medications:
            table = ET.SubElement(text, "table")
            thead = ET.SubElement(table, "thead")
            tr = ET.SubElement(thead, "tr")
            for header in ["Medication", "Dose", "Frequency", "Route"]:
                th = ET.SubElement(tr, "th")
                th.text = header

            tbody = ET.SubElement(table, "tbody")
            for m in medications:
                tr = ET.SubElement(tbody, "tr")
                for val in [
                    m.get("name", "Unknown"),
                    m.get("dose", "-"),
                    m.get("frequency", "-"),
                    m.get("route", "-"),
                ]:
                    td = ET.SubElement(tr, "td")
                    td.text = val or "-"
        else:
            para = ET.SubElement(text, "paragraph")
            para.text = "No current medications"

    def _add_allergies_section(
        self,
        body: ET.Element,
        allergies: list[dict[str, Any]],
    ) -> None:
        """Add Allergies section."""
        component = ET.SubElement(body, "component")
        section = ET.SubElement(component, "section")

        template = ET.SubElement(section, "templateId")
        template.set("root", "2.16.840.1.113883.10.20.22.2.6.1")

        code = ET.SubElement(section, "code")
        code.set("code", "48765-2")
        code.set("codeSystem", self.LOINC_OID)
        code.set("displayName", "Allergies and adverse reactions")

        title = ET.SubElement(section, "title")
        title.text = "Allergies"

        text = ET.SubElement(section, "text")
        if allergies:
            ul = ET.SubElement(text, "list")
            for a in allergies:
                item = ET.SubElement(ul, "item")
                reaction = f" - {a['reaction']}" if a.get("reaction") else ""
                item.text = f"{a.get('name', 'Unknown allergen')}{reaction}"
        else:
            para = ET.SubElement(text, "paragraph")
            para.text = "No known allergies"

    def _add_vitals_section(
        self,
        body: ET.Element,
        vitals: list[dict[str, Any]],
    ) -> None:
        """Add Vital Signs section."""
        component = ET.SubElement(body, "component")
        section = ET.SubElement(component, "section")

        template = ET.SubElement(section, "templateId")
        template.set("root", "2.16.840.1.113883.10.20.22.2.4.1")

        code = ET.SubElement(section, "code")
        code.set("code", "8716-3")
        code.set("codeSystem", self.LOINC_OID)
        code.set("displayName", "Vital Signs")

        title = ET.SubElement(section, "title")
        title.text = "Vital Signs"

        text = ET.SubElement(section, "text")
        if vitals:
            table = ET.SubElement(text, "table")
            thead = ET.SubElement(table, "thead")
            tr = ET.SubElement(thead, "tr")
            for header in ["Vital Sign", "Value", "Unit"]:
                th = ET.SubElement(tr, "th")
                th.text = header

            tbody = ET.SubElement(table, "tbody")
            for v in vitals:
                tr = ET.SubElement(tbody, "tr")
                for val in [
                    v.get("type", "Unknown"),
                    v.get("value", "-"),
                    v.get("unit", "-"),
                ]:
                    td = ET.SubElement(tr, "td")
                    td.text = str(val) if val else "-"
        else:
            para = ET.SubElement(text, "paragraph")
            para.text = "No vital signs recorded"

    def _add_results_section(
        self,
        body: ET.Element,
        lab_results: list[dict[str, Any]],
    ) -> None:
        """Add Results section."""
        component = ET.SubElement(body, "component")
        section = ET.SubElement(component, "section")

        template = ET.SubElement(section, "templateId")
        template.set("root", "2.16.840.1.113883.10.20.22.2.3.1")

        code = ET.SubElement(section, "code")
        code.set("code", "30954-2")
        code.set("codeSystem", self.LOINC_OID)
        code.set("displayName", "Relevant diagnostic tests and/or laboratory data")

        title = ET.SubElement(section, "title")
        title.text = "Results"

        text = ET.SubElement(section, "text")
        if lab_results:
            table = ET.SubElement(text, "table")
            thead = ET.SubElement(table, "thead")
            tr = ET.SubElement(thead, "tr")
            for header in ["Test", "Value", "Unit", "Interpretation"]:
                th = ET.SubElement(tr, "th")
                th.text = header

            tbody = ET.SubElement(table, "tbody")
            for lr in lab_results:
                tr = ET.SubElement(tbody, "tr")
                for val in [
                    lr.get("name", "Unknown"),
                    lr.get("value", "-"),
                    lr.get("unit", "-"),
                    lr.get("interpretation", "-"),
                ]:
                    td = ET.SubElement(tr, "td")
                    td.text = str(val) if val else "-"
        else:
            para = ET.SubElement(text, "paragraph")
            para.text = "No lab results"

    def _add_plan_section(
        self,
        body: ET.Element,
        orders: dict[str, Any],
    ) -> None:
        """Add Plan of Treatment section."""
        component = ET.SubElement(body, "component")
        section = ET.SubElement(component, "section")

        template = ET.SubElement(section, "templateId")
        template.set("root", "2.16.840.1.113883.10.20.22.2.10")

        code = ET.SubElement(section, "code")
        code.set("code", "18776-5")
        code.set("codeSystem", self.LOINC_OID)
        code.set("displayName", "Plan of care note")

        title = ET.SubElement(section, "title")
        title.text = "Plan of Treatment"

        text = ET.SubElement(section, "text")

        has_orders = False

        # Medication orders
        med_orders = orders.get("medications", [])
        if med_orders:
            has_orders = True
            para = ET.SubElement(text, "paragraph")
            para.text = "Medication Orders:"
            ul = ET.SubElement(text, "list")
            for mo in med_orders:
                item = ET.SubElement(ul, "item")
                dose = f" {mo['dosage']}" if mo.get("dosage") else ""
                item.text = f"{mo.get('name', 'Unknown')}{dose}"

        # Lab orders
        lab_orders = orders.get("labs", [])
        if lab_orders:
            has_orders = True
            para = ET.SubElement(text, "paragraph")
            para.text = "Lab Orders:"
            ul = ET.SubElement(text, "list")
            for lo in lab_orders:
                item = ET.SubElement(ul, "item")
                item.text = lo.get("name", "Unknown lab")

        # Consults
        consults = orders.get("consults", [])
        if consults:
            has_orders = True
            para = ET.SubElement(text, "paragraph")
            para.text = "Consults:"
            ul = ET.SubElement(text, "list")
            for c in consults:
                item = ET.SubElement(ul, "item")
                item.text = c.get("specialty", "Unknown specialty")

        # Procedures
        procedures = orders.get("procedures", [])
        if procedures:
            has_orders = True
            para = ET.SubElement(text, "paragraph")
            para.text = "Procedures:"
            ul = ET.SubElement(text, "list")
            for p in procedures:
                item = ET.SubElement(ul, "item")
                item.text = p.get("name", "Unknown procedure")

        # Imaging
        imaging = orders.get("imaging", [])
        if imaging:
            has_orders = True
            para = ET.SubElement(text, "paragraph")
            para.text = "Imaging:"
            ul = ET.SubElement(text, "list")
            for i in imaging:
                item = ET.SubElement(ul, "item")
                item.text = i.get("name", "Unknown imaging")

        if not has_orders:
            para = ET.SubElement(text, "paragraph")
            para.text = "No orders"
