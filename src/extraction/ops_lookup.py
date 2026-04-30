"""
OPS (Operationen- und Prozedurenschluessel) Lookup Database.

German procedure classification for inpatient billing. Follows the same
pattern as icd10_lookup.py: static database + fuzzy match + enrichment.

Flow:
    Procedure/ProcedureOrder name -> normalize -> fuzzy match -> OPS code -> BillingCandidate
"""

import re
from difflib import SequenceMatcher
from typing import NamedTuple

from extraction.extraction_types import BillingCandidate, ClinicalEntities


class OPSCode(NamedTuple):
    """OPS code with metadata."""
    code: str
    display: str
    chapter: str       # "1"-"9"
    setting: str       # "inpatient", "outpatient", "both"
    category: str      # e.g., "diagnostic", "surgical", "imaging"


# =============================================================================
# OPS Database (~200 common inpatient codes)
# Organized by OPS chapter
# =============================================================================

OPS_DATABASE: dict[str, OPSCode] = {
    # -------------------------------------------------------------------------
    # Chapter 1: Diagnostic procedures
    # -------------------------------------------------------------------------
    "echocardiography": OPSCode("1-268", "Transthorakale Echokardiographie", "1", "both", "diagnostic"),
    "transesophageal echocardiography": OPSCode("1-269", "Transosophageale Echokardiographie", "1", "inpatient", "diagnostic"),
    "tee": OPSCode("1-269", "Transosophageale Echokardiographie", "1", "inpatient", "diagnostic"),
    "bronchoscopy": OPSCode("1-620", "Diagnostische Bronchoskopie", "1", "both", "diagnostic"),
    "gastroscopy": OPSCode("1-631", "Diagnostische Osophagogastroduodenoskopie", "1", "both", "diagnostic"),
    "egd": OPSCode("1-631", "Diagnostische Osophagogastroduodenoskopie", "1", "both", "diagnostic"),
    "colonoscopy": OPSCode("1-650", "Diagnostische Koloskopie", "1", "both", "diagnostic"),
    "cystoscopy": OPSCode("1-661", "Diagnostische Urethrozystoskopie", "1", "both", "diagnostic"),
    "lumbar puncture": OPSCode("1-204", "Lumbalpunktion", "1", "both", "diagnostic"),
    "spinal tap": OPSCode("1-204", "Lumbalpunktion", "1", "both", "diagnostic"),
    "bone marrow biopsy": OPSCode("1-424", "Biopsie ohne Inzision am Knochenmark", "1", "both", "diagnostic"),
    "liver biopsy": OPSCode("1-441", "Perkutane Leberbiopsie", "1", "inpatient", "diagnostic"),
    "kidney biopsy": OPSCode("1-463", "Perkutane Nierenbiopsie", "1", "inpatient", "diagnostic"),
    "cardiac catheterization": OPSCode("1-275", "Herzkatheteruntersuchung", "1", "inpatient", "diagnostic"),
    "left heart catheterization": OPSCode("1-275.2", "Linksherzkatheteruntersuchung", "1", "inpatient", "diagnostic"),
    "right heart catheterization": OPSCode("1-275.1", "Rechtsherzkatheteruntersuchung", "1", "inpatient", "diagnostic"),
    "eeg": OPSCode("1-207", "Elektroenzephalographie", "1", "both", "diagnostic"),
    "electroencephalography": OPSCode("1-207", "Elektroenzephalographie", "1", "both", "diagnostic"),
    "emg": OPSCode("1-206", "Elektromyographie", "1", "both", "diagnostic"),
    "nerve conduction study": OPSCode("1-208", "Neurographie", "1", "both", "diagnostic"),
    "arthroscopy diagnostic": OPSCode("1-697", "Diagnostische Arthroskopie", "1", "both", "diagnostic"),
    "thoracentesis": OPSCode("1-844", "Diagnostische Pleurapunktion", "1", "inpatient", "diagnostic"),
    "paracentesis": OPSCode("1-853", "Diagnostische Aszitespunktion", "1", "inpatient", "diagnostic"),

    # -------------------------------------------------------------------------
    # Chapter 3: Imaging procedures
    # -------------------------------------------------------------------------
    "ct head": OPSCode("3-200", "CT Schaedel", "3", "both", "imaging"),
    "ct chest": OPSCode("3-202", "CT Thorax", "3", "both", "imaging"),
    "ct abdomen": OPSCode("3-207", "CT Abdomen", "3", "both", "imaging"),
    "ct pelvis": OPSCode("3-208", "CT Becken", "3", "both", "imaging"),
    "ct angiography": OPSCode("3-228", "CT-Angiographie", "3", "both", "imaging"),
    "mri brain": OPSCode("3-800", "MRT Schaedel", "3", "both", "imaging"),
    "mri spine": OPSCode("3-802", "MRT Wirbelsaeule", "3", "both", "imaging"),
    "mri abdomen": OPSCode("3-807", "MRT Abdomen", "3", "both", "imaging"),
    "mri cardiac": OPSCode("3-808", "MRT Herz", "3", "inpatient", "imaging"),
    "mri knee": OPSCode("3-806", "MRT Knie", "3", "both", "imaging"),
    "chest x-ray": OPSCode("3-020", "Roentgen Thorax", "3", "both", "imaging"),
    "abdominal x-ray": OPSCode("3-025", "Roentgen Abdomen", "3", "both", "imaging"),
    "fluoroscopy": OPSCode("3-05a", "Durchleuchtung", "3", "both", "imaging"),
    "pet ct": OPSCode("3-74x", "PET-CT", "3", "inpatient", "imaging"),
    "bone scintigraphy": OPSCode("3-709", "Skelettszintigraphie", "3", "both", "imaging"),
    "ultrasound abdomen": OPSCode("3-05a.0", "Sonographie Abdomen", "3", "both", "imaging"),
    "doppler ultrasound": OPSCode("3-03d", "Dopplersonographie", "3", "both", "imaging"),
    "angiography": OPSCode("3-600", "Arteriographie", "3", "inpatient", "imaging"),
    "coronary angiography": OPSCode("3-601", "Koronarangiographie", "3", "inpatient", "imaging"),

    # -------------------------------------------------------------------------
    # Chapter 5: Surgical procedures
    # -------------------------------------------------------------------------
    "appendectomy": OPSCode("5-470", "Appendektomie", "5", "inpatient", "surgical"),
    "laparoscopic appendectomy": OPSCode("5-470.1", "Laparoskopische Appendektomie", "5", "inpatient", "surgical"),
    "cholecystectomy": OPSCode("5-511", "Cholezystektomie", "5", "inpatient", "surgical"),
    "laparoscopic cholecystectomy": OPSCode("5-511.1", "Laparoskopische Cholezystektomie", "5", "inpatient", "surgical"),
    "hernia repair": OPSCode("5-530", "Verschluss einer Hernia inguinalis", "5", "both", "surgical"),
    "inguinal hernia repair": OPSCode("5-530", "Verschluss einer Hernia inguinalis", "5", "both", "surgical"),
    "hip replacement": OPSCode("5-820", "Implantation Hueftgelenkendoprothese", "5", "inpatient", "surgical"),
    "total hip arthroplasty": OPSCode("5-820.0", "Zementierte Hueft-TEP", "5", "inpatient", "surgical"),
    "knee replacement": OPSCode("5-822", "Implantation Kniegelenkendoprothese", "5", "inpatient", "surgical"),
    "total knee arthroplasty": OPSCode("5-822.0", "Bikondylaere Knie-TEP", "5", "inpatient", "surgical"),
    "cabg": OPSCode("5-361", "Koronararterienbypass", "5", "inpatient", "surgical"),
    "coronary artery bypass": OPSCode("5-361", "Koronararterienbypass", "5", "inpatient", "surgical"),
    "valve replacement": OPSCode("5-351", "Herzklappenersatz", "5", "inpatient", "surgical"),
    "aortic valve replacement": OPSCode("5-351.1", "Aortenklappenersatz", "5", "inpatient", "surgical"),
    "pacemaker implantation": OPSCode("5-377", "Schrittmacherimplantation", "5", "inpatient", "surgical"),
    "icd implantation": OPSCode("5-377.5", "ICD-Implantation", "5", "inpatient", "surgical"),
    "central venous catheter": OPSCode("5-399.5", "ZVK-Anlage", "5", "inpatient", "surgical"),
    "tracheostomy": OPSCode("5-311", "Tracheostomie", "5", "inpatient", "surgical"),
    "chest tube insertion": OPSCode("5-340.0", "Thoraxdrainage", "5", "inpatient", "surgical"),
    "thoracotomy": OPSCode("5-340", "Inzision von Brustwand und Pleura", "5", "inpatient", "surgical"),
    "lobectomy": OPSCode("5-324", "Lobektomie", "5", "inpatient", "surgical"),
    "colectomy": OPSCode("5-455", "Partielle Kolektomie", "5", "inpatient", "surgical"),
    "hemicolectomy": OPSCode("5-455.0", "Hemikolektomie", "5", "inpatient", "surgical"),
    "gastrectomy": OPSCode("5-434", "Partielle Gastrektomie", "5", "inpatient", "surgical"),
    "splenectomy": OPSCode("5-413", "Splenektomie", "5", "inpatient", "surgical"),
    "nephrectomy": OPSCode("5-554", "Nephrektomie", "5", "inpatient", "surgical"),
    "cystectomy": OPSCode("5-576", "Zystektomie", "5", "inpatient", "surgical"),
    "prostatectomy": OPSCode("5-604", "Radikale Prostatektomie", "5", "inpatient", "surgical"),
    "hysterectomy": OPSCode("5-683", "Hysterektomie", "5", "inpatient", "surgical"),
    "cesarean section": OPSCode("5-740", "Sectio caesarea", "5", "inpatient", "surgical"),
    "craniotomy": OPSCode("5-010", "Kraniotomie", "5", "inpatient", "surgical"),
    "laminectomy": OPSCode("5-032", "Laminektomie", "5", "inpatient", "surgical"),
    "discectomy": OPSCode("5-831", "Diskektomie", "5", "inpatient", "surgical"),
    "spinal fusion": OPSCode("5-836", "Spondylodese", "5", "inpatient", "surgical"),
    "amputation": OPSCode("5-864", "Amputation", "5", "inpatient", "surgical"),
    "skin graft": OPSCode("5-902", "Freie Hauttransplantation", "5", "inpatient", "surgical"),
    "debridement": OPSCode("5-896", "Chirurgisches Wunddebridement", "5", "both", "surgical"),
    "wound closure": OPSCode("5-900", "Wundverschluss", "5", "both", "surgical"),
    "arterial bypass": OPSCode("5-393", "Arterielle Bypassoperation", "5", "inpatient", "surgical"),
    "endovascular repair": OPSCode("5-38a", "Endovaskulaere Implantation", "5", "inpatient", "surgical"),
    "thyroidectomy": OPSCode("5-062", "Thyreoidektomie", "5", "inpatient", "surgical"),
    "mastectomy": OPSCode("5-870", "Mastektomie", "5", "inpatient", "surgical"),
    "stent placement": OPSCode("8-836", "Perkutane Gefaesskatheterintervention", "8", "inpatient", "surgical"),
    "pci": OPSCode("8-837", "Perkutane Koronarintervention", "8", "inpatient", "surgical"),
    "percutaneous coronary intervention": OPSCode("8-837", "Perkutane Koronarintervention", "8", "inpatient", "surgical"),

    # -------------------------------------------------------------------------
    # Chapter 5: Psychiatric procedures (ch5 linked dx required)
    # -------------------------------------------------------------------------
    "psychiatric evaluation": OPSCode("5-901.0", "Psychiatrische Diagnostik", "5", "inpatient", "psychiatric"),

    # -------------------------------------------------------------------------
    # Chapter 8: Non-surgical therapeutic procedures
    # -------------------------------------------------------------------------
    "mechanical ventilation": OPSCode("8-706", "Maschinelle Beatmung", "8", "inpatient", "therapeutic"),
    "invasive ventilation": OPSCode("8-706", "Maschinelle Beatmung", "8", "inpatient", "therapeutic"),
    "non-invasive ventilation": OPSCode("8-706.0", "NIV-Beatmung", "8", "inpatient", "therapeutic"),
    "niv": OPSCode("8-706.0", "NIV-Beatmung", "8", "inpatient", "therapeutic"),
    "dialysis": OPSCode("8-854", "Haemodialyse", "8", "both", "therapeutic"),
    "hemodialysis": OPSCode("8-854", "Haemodialyse", "8", "both", "therapeutic"),
    "peritoneal dialysis": OPSCode("8-857", "Peritonealdialyse", "8", "both", "therapeutic"),
    "blood transfusion": OPSCode("8-800", "Transfusion von Vollblut/Erythrozytenkonzentrat", "8", "inpatient", "therapeutic"),
    "red cell transfusion": OPSCode("8-800", "Transfusion von Vollblut/Erythrozytenkonzentrat", "8", "inpatient", "therapeutic"),
    "platelet transfusion": OPSCode("8-800.6", "Thrombozytentransfusion", "8", "inpatient", "therapeutic"),
    "plasma transfusion": OPSCode("8-800.8", "FFP-Transfusion", "8", "inpatient", "therapeutic"),
    "chemotherapy": OPSCode("8-542", "Chemotherapie", "8", "both", "therapeutic"),
    "radiation therapy": OPSCode("8-522", "Strahlentherapie", "8", "both", "therapeutic"),
    "cardioversion": OPSCode("8-640", "Elektrische Kardioversion", "8", "inpatient", "therapeutic"),
    "defibrillation": OPSCode("8-640.1", "Defibrillation", "8", "inpatient", "therapeutic"),
    "thrombolysis": OPSCode("8-836.8", "Systemische Thrombolyse", "8", "inpatient", "therapeutic"),
    "intubation": OPSCode("8-701", "Endotracheale Intubation", "8", "inpatient", "therapeutic"),
    "extubation": OPSCode("8-701.1", "Extubation", "8", "inpatient", "therapeutic"),
    "enteral nutrition": OPSCode("8-015", "Enterale Ernaehrung", "8", "inpatient", "therapeutic"),
    "parenteral nutrition": OPSCode("8-016", "Parenterale Ernaehrung", "8", "inpatient", "therapeutic"),
    "tpn": OPSCode("8-016", "Parenterale Ernaehrung", "8", "inpatient", "therapeutic"),
    "physiotherapy": OPSCode("8-561", "Physiotherapie", "8", "both", "therapeutic"),
    "occupational therapy": OPSCode("8-562", "Ergotherapie", "8", "both", "therapeutic"),
    "speech therapy": OPSCode("8-563", "Logopaedie", "8", "both", "therapeutic"),
    "pain management": OPSCode("8-910", "Schmerztherapie", "8", "both", "therapeutic"),
    "epidural anesthesia": OPSCode("8-910.1", "Epiduralanaesthesie", "8", "inpatient", "therapeutic"),
    "wound vacuum therapy": OPSCode("8-190", "VAC-Therapie", "8", "inpatient", "therapeutic"),
    "phototherapy": OPSCode("8-560", "Phototherapie", "8", "both", "therapeutic"),
    "plasmapheresis": OPSCode("8-822", "Plasmapherese", "8", "inpatient", "therapeutic"),
    "immunoglobulin therapy": OPSCode("8-812", "Immunglobulintherapie", "8", "inpatient", "therapeutic"),
    "ivig": OPSCode("8-812", "Immunglobulintherapie", "8", "inpatient", "therapeutic"),
    "ecmo": OPSCode("8-852", "Extrakorporale Membranoxygenierung", "8", "inpatient", "therapeutic"),
    "cpap": OPSCode("8-706.0", "NIV-Beatmung", "8", "inpatient", "therapeutic"),
    "bronchial lavage": OPSCode("8-100", "Therapeutische Bronchiallavage", "8", "inpatient", "therapeutic"),

    # -------------------------------------------------------------------------
    # Chapter 9: Supplementary procedures
    # -------------------------------------------------------------------------
    "complex treatment icu": OPSCode("8-980", "Intensivmedizinische Komplexbehandlung", "9", "inpatient", "complex"),
    "icu complex care": OPSCode("8-980", "Intensivmedizinische Komplexbehandlung", "9", "inpatient", "complex"),
    "stroke unit treatment": OPSCode("8-981", "Neurologische Komplexbehandlung", "9", "inpatient", "complex"),
    "palliative care": OPSCode("8-982", "Palliativmedizinische Komplexbehandlung", "9", "inpatient", "complex"),
    "geriatric complex treatment": OPSCode("8-550", "Geriatrische Komplexbehandlung", "9", "inpatient", "complex"),
    "early rehabilitation": OPSCode("8-559", "Fruehrehabilitation", "9", "inpatient", "complex"),
    "multimodal pain therapy": OPSCode("8-918", "Multimodale Schmerztherapie", "9", "inpatient", "complex"),
}


# =============================================================================
# Synonym Mappings (German clinical terms to canonical names)
# =============================================================================

OPS_SYNONYMS: dict[str, str] = {
    # German terms
    "herzkatheter": "cardiac catheterization",
    "herz-echo": "echocardiography",
    "herzecho": "echocardiography",
    "schluck-echo": "transesophageal echocardiography",
    "magenspiegelung": "gastroscopy",
    "darmspiegelung": "colonoscopy",
    "blasenspiegelung": "cystoscopy",
    "lungenspiegelung": "bronchoscopy",
    "beatmung": "mechanical ventilation",
    "dialyse": "dialysis",
    "bluttransfusion": "blood transfusion",
    "blinddarm op": "appendectomy",
    "gallenblasen op": "cholecystectomy",
    "hueft-tep": "total hip arthroplasty",
    "knie-tep": "total knee arthroplasty",
    "bypass op": "cabg",
    "herzschrittmacher": "pacemaker implantation",
    "luftroehrenschnitt": "tracheostomy",
    "roentgen thorax": "chest x-ray",
    "roentgen abdomen": "abdominal x-ray",
    "kopf-ct": "ct head",
    "schaedel-ct": "ct head",
    "thorax-ct": "ct chest",
    "abdomen-ct": "ct abdomen",
    "kopf-mrt": "mri brain",
    "schaedel-mrt": "mri brain",
    "wirbelsaeulen-mrt": "mri spine",
    "herz-mrt": "mri cardiac",
    "zvk": "central venous catheter",
    "krankengymnastik": "physiotherapy",
    "ernaehrungssonde": "enteral nutrition",
    "elektroschock": "cardioversion",
    "defi": "defibrillation",
    "katheterintervention": "pci",
    "koronarintervention": "pci",
    "stenting": "stent placement",
    "lyse": "thrombolysis",
    "schmerzkatheter": "epidural anesthesia",
    "vac therapie": "wound vacuum therapy",
    "vakuumtherapie": "wound vacuum therapy",

    # English abbreviations / synonyms
    "echo": "echocardiography",
    "scope": "bronchoscopy",
    "upper endoscopy": "gastroscopy",
    "lower endoscopy": "colonoscopy",
    "lp": "lumbar puncture",
    "bmb": "bone marrow biopsy",
    "cath": "cardiac catheterization",
    "left cath": "left heart catheterization",
    "right cath": "right heart catheterization",
    "picc line": "central venous catheter",
    "central line": "central venous catheter",
    "vent": "mechanical ventilation",
    "ventilator": "mechanical ventilation",
    "bipap": "non-invasive ventilation",
    "hd": "hemodialysis",
    "pd": "peritoneal dialysis",
    "rbc transfusion": "red cell transfusion",
    "ffp": "plasma transfusion",
    "chemo": "chemotherapy",
    "xrt": "radiation therapy",
    "pt": "physiotherapy",
    "ot": "occupational therapy",
    "st": "speech therapy",
    "tube feed": "enteral nutrition",
    "c-section": "cesarean section",
    "section": "cesarean section",
    "crani": "craniotomy",
    "lap chole": "laparoscopic cholecystectomy",
    "lap appy": "laparoscopic appendectomy",
    "tha": "total hip arthroplasty",
    "tka": "total knee arthroplasty",
    "tavr": "aortic valve replacement",
    "tavi": "aortic valve replacement",
}


def normalize_procedure(name: str) -> str:
    """Normalize a procedure name for matching."""
    if not name:
        return ""
    name = name.lower().strip()
    # Remove common prefixes
    prefixes = ["diagnostic ", "therapeutic ", "emergent ", "elective ", "planned "]
    for prefix in prefixes:
        if name.startswith(prefix):
            name = name[len(prefix):]
    # Remove punctuation and extra whitespace
    name = re.sub(r'[^\w\s]', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def similarity_score(s1: str, s2: str) -> float:
    """Calculate similarity between two strings (0.0 to 1.0)."""
    return SequenceMatcher(None, s1, s2).ratio()


def lookup_ops(procedure_name: str, min_similarity: float = 0.80) -> tuple[str | None, str | None, float]:
    """
    Look up OPS code for a procedure name.

    Returns:
        Tuple of (ops_code, display_name, confidence)
    """
    if not procedure_name:
        return None, None, 0.0

    normalized = normalize_procedure(procedure_name)

    # 1. Exact match
    if normalized in OPS_DATABASE:
        code = OPS_DATABASE[normalized]
        return code.code, code.display, 1.0

    # 2. Check synonyms
    if normalized in OPS_SYNONYMS:
        canonical = OPS_SYNONYMS[normalized]
        if canonical in OPS_DATABASE:
            code = OPS_DATABASE[canonical]
            return code.code, code.display, 0.95

    # 3. Fuzzy matching
    best_match = None
    best_score = 0.0

    for db_name, code in OPS_DATABASE.items():
        score = similarity_score(normalized, db_name)
        if score > best_score and score >= min_similarity:
            best_score = score
            best_match = code

    if best_match:
        return best_match.code, best_match.display, round(best_score, 2)

    return None, None, 0.0


def validate_ops_candidate(candidate: BillingCandidate) -> BillingCandidate:
    """
    Validate an OPS billing candidate.

    Checks: code format, setting eligibility, chapter 5 linked diagnosis requirement.
    """
    messages = []
    status = "valid"

    if not candidate.code:
        candidate.validation_status = "error"
        candidate.validation_messages = ["No OPS code assigned"]
        return candidate

    # Check code format: X-XXX or X-XXX.X
    if not re.match(r'^\d-\d{3}(\.\d+)?$', candidate.code):
        messages.append(f"Non-standard OPS code format: {candidate.code}")
        status = "warning"

    # Check setting eligibility
    if candidate.ops_setting == "inpatient":
        pass  # inpatient-only is fine for hospital billing
    elif candidate.ops_setting == "outpatient":
        messages.append("Code typically outpatient-only; verify inpatient applicability")
        status = "warning"

    # Chapter 5 psychiatric procedures require linked diagnosis
    if candidate.ops_chapter == "5" and candidate.code and candidate.code.startswith("5-9"):
        if not candidate.linked_diagnosis:
            messages.append("Psychiatric procedure (OPS Ch.5) requires linked ICD-10 diagnosis")
            status = "warning"

    candidate.validation_status = status
    candidate.validation_messages = messages
    return candidate


def enrich_billing_candidates_with_ops(entities: ClinicalEntities) -> ClinicalEntities:
    """
    Create BillingCandidate entries from procedures and procedure_orders.

    Iterates over both completed procedures and ordered procedures, looks up OPS codes,
    validates, and appends to entities.billing_candidates.
    """
    # Process completed procedures
    for proc in entities.procedures:
        code, display, confidence = lookup_ops(proc.name)
        if code and confidence >= 0.80:
            ops_entry = OPS_DATABASE.get(normalize_procedure(proc.name))
            # Try synonym resolution for metadata
            if not ops_entry:
                syn = OPS_SYNONYMS.get(normalize_procedure(proc.name))
                if syn:
                    ops_entry = OPS_DATABASE.get(syn)

            candidate = BillingCandidate(
                name=proc.name,
                code=code,
                code_system="OPS",
                confidence=confidence,
                linked_diagnosis=None,
                reasoning=f"Matched procedure '{proc.name}' to OPS {code} ({display})",
                ops_chapter=ops_entry.chapter if ops_entry else None,
                ops_setting=ops_entry.setting if ops_entry else None,
            )
            # Build alternatives from fuzzy near-matches
            normalized = normalize_procedure(proc.name)
            alts = []
            for db_name, db_code in OPS_DATABASE.items():
                if db_code.code != code:
                    alt_score = similarity_score(normalized, db_name)
                    if alt_score >= 0.70:
                        alts.append({"code": db_code.code, "display": db_code.display, "confidence": round(alt_score, 2)})
            candidate.alternatives = sorted(alts, key=lambda a: a["confidence"], reverse=True)[:3]

            candidate = validate_ops_candidate(candidate)
            entities.billing_candidates.append(candidate)

    # Process procedure orders
    for order in entities.procedure_orders:
        code, display, confidence = lookup_ops(order.name)
        if code and confidence >= 0.80:
            ops_entry = OPS_DATABASE.get(normalize_procedure(order.name))
            if not ops_entry:
                syn = OPS_SYNONYMS.get(normalize_procedure(order.name))
                if syn:
                    ops_entry = OPS_DATABASE.get(syn)

            # Link diagnosis from order if available
            linked_dx = None
            if order.linked_diagnosis and isinstance(order.linked_diagnosis, dict):
                linked_dx = order.linked_diagnosis.get("icd10")

            candidate = BillingCandidate(
                name=order.name,
                code=code,
                code_system="OPS",
                confidence=confidence,
                linked_diagnosis=linked_dx,
                reasoning=f"Matched order '{order.name}' to OPS {code} ({display})",
                ops_chapter=ops_entry.chapter if ops_entry else None,
                ops_setting=ops_entry.setting if ops_entry else None,
            )
            candidate = validate_ops_candidate(candidate)
            entities.billing_candidates.append(candidate)

    return entities
