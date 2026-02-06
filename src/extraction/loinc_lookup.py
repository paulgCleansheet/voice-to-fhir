"""
LOINC Lookup Database for Laboratory Test Coding.

This module provides verified LOINC codes for common laboratory tests.
Instead of relying on LLM-generated codes (which can hallucinate), this lookup
provides deterministic, auditable lab test coding.

LOINC (Logical Observation Identifiers Names and Codes) is the international
standard for identifying laboratory and clinical observations.

Flow:
    MedGemma extracts lab test name → fuzzy match → LOINC lookup → verified code

Copyright (c) 2026 Cleansheet LLC
License: CC BY 4.0
"""

import re
from difflib import SequenceMatcher
from typing import NamedTuple


class LOINCCode(NamedTuple):
    """LOINC code with metadata."""
    code: str
    display: str
    category: str  # e.g., "hematology", "chemistry", "lipids"


# =============================================================================
# LOINC Database (~150 common laboratory tests)
# Organized by clinical category for maintainability
# =============================================================================

LOINC_DATABASE: dict[str, LOINCCode] = {
    # -------------------------------------------------------------------------
    # Hematology - Complete Blood Count (CBC)
    # -------------------------------------------------------------------------
    "complete blood count": LOINCCode("58410-2", "Complete blood count (CBC) panel - Blood by Automated count", "hematology"),
    "cbc": LOINCCode("58410-2", "Complete blood count (CBC) panel - Blood by Automated count", "hematology"),
    "cbc with differential": LOINCCode("57021-8", "CBC W Auto Differential panel - Blood", "hematology"),
    "hemoglobin": LOINCCode("718-7", "Hemoglobin [Mass/volume] in Blood", "hematology"),
    "hgb": LOINCCode("718-7", "Hemoglobin [Mass/volume] in Blood", "hematology"),
    "hematocrit": LOINCCode("4544-3", "Hematocrit [Volume Fraction] of Blood by Automated count", "hematology"),
    "hct": LOINCCode("4544-3", "Hematocrit [Volume Fraction] of Blood by Automated count", "hematology"),
    "white blood cell": LOINCCode("6690-2", "Leukocytes [#/volume] in Blood by Automated count", "hematology"),
    "wbc": LOINCCode("6690-2", "Leukocytes [#/volume] in Blood by Automated count", "hematology"),
    "white blood cell count": LOINCCode("6690-2", "Leukocytes [#/volume] in Blood by Automated count", "hematology"),
    "platelet": LOINCCode("777-3", "Platelets [#/volume] in Blood by Automated count", "hematology"),
    "platelet count": LOINCCode("777-3", "Platelets [#/volume] in Blood by Automated count", "hematology"),
    "red blood cell": LOINCCode("789-8", "Erythrocytes [#/volume] in Blood by Automated count", "hematology"),
    "rbc": LOINCCode("789-8", "Erythrocytes [#/volume] in Blood by Automated count", "hematology"),
    "red blood cell count": LOINCCode("789-8", "Erythrocytes [#/volume] in Blood by Automated count", "hematology"),

    # -------------------------------------------------------------------------
    # Chemistry - Metabolic Panels
    # -------------------------------------------------------------------------
    "basic metabolic panel": LOINCCode("51990-0", "Basic metabolic panel - Blood", "chemistry"),
    "bmp": LOINCCode("51990-0", "Basic metabolic panel - Blood", "chemistry"),
    "comprehensive metabolic panel": LOINCCode("24323-8", "Comprehensive metabolic panel - Blood", "chemistry"),
    "cmp": LOINCCode("24323-8", "Comprehensive metabolic panel - Blood", "chemistry"),
    "metabolic panel": LOINCCode("24323-8", "Comprehensive metabolic panel - Blood", "chemistry"),
    "electrolytes": LOINCCode("24326-1", "Electrolytes 1998 panel - Serum or Plasma", "chemistry"),

    # -------------------------------------------------------------------------
    # Chemistry - Individual Tests
    # -------------------------------------------------------------------------
    "glucose": LOINCCode("2345-7", "Glucose [Mass/volume] in Serum or Plasma", "chemistry"),
    "blood glucose": LOINCCode("2345-7", "Glucose [Mass/volume] in Serum or Plasma", "chemistry"),
    "sodium": LOINCCode("2951-2", "Sodium [Moles/volume] in Serum or Plasma", "chemistry"),
    "potassium": LOINCCode("2823-3", "Potassium [Moles/volume] in Serum or Plasma", "chemistry"),
    "chloride": LOINCCode("2075-0", "Chloride [Moles/volume] in Serum or Plasma", "chemistry"),
    "bicarbonate": LOINCCode("1963-8", "Bicarbonate [Moles/volume] in Serum or Plasma", "chemistry"),
    "co2": LOINCCode("1963-8", "Bicarbonate [Moles/volume] in Serum or Plasma", "chemistry"),
    "blood urea nitrogen": LOINCCode("3094-0", "Urea nitrogen [Mass/volume] in Serum or Plasma", "chemistry"),
    "bun": LOINCCode("3094-0", "Urea nitrogen [Mass/volume] in Serum or Plasma", "chemistry"),
    "creatinine": LOINCCode("2160-0", "Creatinine [Mass/volume] in Serum or Plasma", "chemistry"),
    "calcium": LOINCCode("17861-6", "Calcium [Mass/volume] in Serum or Plasma", "chemistry"),
    "magnesium": LOINCCode("19123-9", "Magnesium [Mass/volume] in Serum or Plasma", "chemistry"),
    "phosphorus": LOINCCode("2777-1", "Phosphate [Mass/volume] in Serum or Plasma", "chemistry"),

    # -------------------------------------------------------------------------
    # Lipids
    # -------------------------------------------------------------------------
    "lipid panel": LOINCCode("24331-1", "Lipid panel - Serum or Plasma", "lipids"),
    "lipid profile": LOINCCode("24331-1", "Lipid panel - Serum or Plasma", "lipids"),
    "cholesterol": LOINCCode("2093-3", "Cholesterol [Mass/volume] in Serum or Plasma", "lipids"),
    "total cholesterol": LOINCCode("2093-3", "Cholesterol [Mass/volume] in Serum or Plasma", "lipids"),
    "hdl": LOINCCode("2085-9", "Cholesterol in HDL [Mass/volume] in Serum or Plasma", "lipids"),
    "hdl cholesterol": LOINCCode("2085-9", "Cholesterol in HDL [Mass/volume] in Serum or Plasma", "lipids"),
    "ldl": LOINCCode("13457-7", "Cholesterol in LDL [Mass/volume] in Serum or Plasma by calculation", "lipids"),
    "ldl cholesterol": LOINCCode("13457-7", "Cholesterol in LDL [Mass/volume] in Serum or Plasma by calculation", "lipids"),
    "triglycerides": LOINCCode("2571-8", "Triglyceride [Mass/volume] in Serum or Plasma", "lipids"),
    "vldl": LOINCCode("13458-5", "Cholesterol in VLDL [Mass/volume] in Serum or Plasma by calculation", "lipids"),

    # -------------------------------------------------------------------------
    # Diabetes / Endocrine
    # -------------------------------------------------------------------------
    "hemoglobin a1c": LOINCCode("4548-4", "Hemoglobin A1c/Hemoglobin.total in Blood", "endocrine"),
    "hba1c": LOINCCode("4548-4", "Hemoglobin A1c/Hemoglobin.total in Blood", "endocrine"),
    "a1c": LOINCCode("4548-4", "Hemoglobin A1c/Hemoglobin.total in Blood", "endocrine"),
    "glycated hemoglobin": LOINCCode("4548-4", "Hemoglobin A1c/Hemoglobin.total in Blood", "endocrine"),
    "fasting glucose": LOINCCode("1558-6", "Fasting glucose [Mass/volume] in Serum or Plasma", "endocrine"),

    # -------------------------------------------------------------------------
    # Liver Function Tests (LFTs)
    # -------------------------------------------------------------------------
    "liver function tests": LOINCCode("24325-3", "Liver function panel - Serum or Plasma", "hepatic"),
    "lft": LOINCCode("24325-3", "Liver function panel - Serum or Plasma", "hepatic"),
    "hepatic function panel": LOINCCode("24325-3", "Liver function panel - Serum or Plasma", "hepatic"),
    "alt": LOINCCode("1742-6", "Alanine aminotransferase [Enzymatic activity/volume] in Serum or Plasma", "hepatic"),
    "alanine aminotransferase": LOINCCode("1742-6", "Alanine aminotransferase [Enzymatic activity/volume] in Serum or Plasma", "hepatic"),
    "sgpt": LOINCCode("1742-6", "Alanine aminotransferase [Enzymatic activity/volume] in Serum or Plasma", "hepatic"),
    "ast": LOINCCode("1920-8", "Aspartate aminotransferase [Enzymatic activity/volume] in Serum or Plasma", "hepatic"),
    "aspartate aminotransferase": LOINCCode("1920-8", "Aspartate aminotransferase [Enzymatic activity/volume] in Serum or Plasma", "hepatic"),
    "sgot": LOINCCode("1920-8", "Aspartate aminotransferase [Enzymatic activity/volume] in Serum or Plasma", "hepatic"),
    "alkaline phosphatase": LOINCCode("6768-6", "Alkaline phosphatase [Enzymatic activity/volume] in Serum or Plasma", "hepatic"),
    "alp": LOINCCode("6768-6", "Alkaline phosphatase [Enzymatic activity/volume] in Serum or Plasma", "hepatic"),
    "total bilirubin": LOINCCode("1975-2", "Bilirubin.total [Mass/volume] in Serum or Plasma", "hepatic"),
    "bilirubin": LOINCCode("1975-2", "Bilirubin.total [Mass/volume] in Serum or Plasma", "hepatic"),
    "direct bilirubin": LOINCCode("1968-7", "Bilirubin.direct [Mass/volume] in Serum or Plasma", "hepatic"),
    "indirect bilirubin": LOINCCode("1971-1", "Bilirubin.indirect [Mass/volume] in Serum or Plasma", "hepatic"),
    "albumin": LOINCCode("1751-7", "Albumin [Mass/volume] in Serum or Plasma", "hepatic"),
    "total protein": LOINCCode("2885-2", "Protein [Mass/volume] in Serum or Plasma", "hepatic"),

    # -------------------------------------------------------------------------
    # Thyroid Function Tests
    # -------------------------------------------------------------------------
    "thyroid function tests": LOINCCode("24348-5", "Thyroid function panel - Serum or Plasma", "endocrine"),
    "thyroid panel": LOINCCode("24348-5", "Thyroid function panel - Serum or Plasma", "endocrine"),
    "tsh": LOINCCode("3016-3", "Thyrotropin [Units/volume] in Serum or Plasma", "endocrine"),
    "thyroid stimulating hormone": LOINCCode("3016-3", "Thyrotropin [Units/volume] in Serum or Plasma", "endocrine"),
    "free t4": LOINCCode("3024-7", "Thyroxine (T4) free [Mass/volume] in Serum or Plasma", "endocrine"),
    "t4 free": LOINCCode("3024-7", "Thyroxine (T4) free [Mass/volume] in Serum or Plasma", "endocrine"),
    "t4": LOINCCode("3026-2", "Thyroxine (T4) [Mass/volume] in Serum or Plasma", "endocrine"),
    "total t4": LOINCCode("3026-2", "Thyroxine (T4) [Mass/volume] in Serum or Plasma", "endocrine"),
    "free t3": LOINCCode("3051-0", "Triiodothyronine (T3) Free [Mass/volume] in Serum or Plasma", "endocrine"),
    "t3 free": LOINCCode("3051-0", "Triiodothyronine (T3) Free [Mass/volume] in Serum or Plasma", "endocrine"),
    "t3": LOINCCode("3053-6", "Triiodothyronine (T3) [Mass/volume] in Serum or Plasma", "endocrine"),
    "total t3": LOINCCode("3053-6", "Triiodothyronine (T3) [Mass/volume] in Serum or Plasma", "endocrine"),

    # -------------------------------------------------------------------------
    # Cardiac Markers
    # -------------------------------------------------------------------------
    "troponin": LOINCCode("10839-9", "Troponin I.cardiac [Mass/volume] in Serum or Plasma", "cardiac"),
    "troponin i": LOINCCode("10839-9", "Troponin I.cardiac [Mass/volume] in Serum or Plasma", "cardiac"),
    "troponin t": LOINCCode("6598-7", "Troponin T.cardiac [Mass/volume] in Serum or Plasma", "cardiac"),
    "bnp": LOINCCode("33762-6", "Natriuretic peptide.B prohormone N-Terminal [Mass/volume] in Serum or Plasma", "cardiac"),
    "b-type natriuretic peptide": LOINCCode("33762-6", "Natriuretic peptide.B prohormone N-Terminal [Mass/volume] in Serum or Plasma", "cardiac"),
    "nt-probnp": LOINCCode("33762-6", "Natriuretic peptide.B prohormone N-Terminal [Mass/volume] in Serum or Plasma", "cardiac"),
    "pro-bnp": LOINCCode("33762-6", "Natriuretic peptide.B prohormone N-Terminal [Mass/volume] in Serum or Plasma", "cardiac"),
    "ck": LOINCCode("2157-6", "Creatine kinase [Enzymatic activity/volume] in Serum or Plasma", "cardiac"),
    "creatine kinase": LOINCCode("2157-6", "Creatine kinase [Enzymatic activity/volume] in Serum or Plasma", "cardiac"),
    "cpk": LOINCCode("2157-6", "Creatine kinase [Enzymatic activity/volume] in Serum or Plasma", "cardiac"),
    "ck-mb": LOINCCode("13969-1", "Creatine kinase.MB [Mass/volume] in Serum or Plasma", "cardiac"),
    "d-dimer": LOINCCode("48065-7", "Fibrin D-dimer FEU [Mass/volume] in Platelet poor plasma", "cardiac"),

    # -------------------------------------------------------------------------
    # Coagulation Studies
    # -------------------------------------------------------------------------
    "prothrombin time": LOINCCode("5902-2", "Prothrombin time (PT)", "coagulation"),
    "pt": LOINCCode("5902-2", "Prothrombin time (PT)", "coagulation"),
    "inr": LOINCCode("6301-6", "INR in Platelet poor plasma by Coagulation assay", "coagulation"),
    "ptt": LOINCCode("14979-9", "Activated partial thromboplastin time (aPTT)", "coagulation"),
    "aptt": LOINCCode("14979-9", "Activated partial thromboplastin time (aPTT)", "coagulation"),
    "activated partial thromboplastin time": LOINCCode("14979-9", "Activated partial thromboplastin time (aPTT)", "coagulation"),
    "fibrinogen": LOINCCode("3255-7", "Fibrinogen [Mass/volume] in Platelet poor plasma by Coagulation assay", "coagulation"),

    # -------------------------------------------------------------------------
    # Urinalysis
    # -------------------------------------------------------------------------
    "urinalysis": LOINCCode("24356-8", "Urinalysis complete panel - Urine", "urinalysis"),
    "ua": LOINCCode("24356-8", "Urinalysis complete panel - Urine", "urinalysis"),
    "urine analysis": LOINCCode("24356-8", "Urinalysis complete panel - Urine", "urinalysis"),
    "urine culture": LOINCCode("630-4", "Bacteria identified in Urine by Culture", "microbiology"),
    "urine protein": LOINCCode("2888-6", "Protein [Mass/volume] in Urine", "urinalysis"),

    # -------------------------------------------------------------------------
    # Microbiology / Culture
    # -------------------------------------------------------------------------
    "blood culture": LOINCCode("600-7", "Bacteria identified in Blood by Culture", "microbiology"),
    "sputum culture": LOINCCode("626-2", "Bacteria identified in Sputum by Culture", "microbiology"),
    "wound culture": LOINCCode("625-4", "Bacteria identified in Wound by Culture", "microbiology"),
    "stool culture": LOINCCode("625-4", "Bacteria identified in Stool by Culture", "microbiology"),

    # -------------------------------------------------------------------------
    # Inflammatory Markers
    # -------------------------------------------------------------------------
    "esr": LOINCCode("4537-7", "Erythrocyte sedimentation rate by Westergren method", "inflammatory"),
    "sed rate": LOINCCode("4537-7", "Erythrocyte sedimentation rate by Westergren method", "inflammatory"),
    "erythrocyte sedimentation rate": LOINCCode("4537-7", "Erythrocyte sedimentation rate by Westergren method", "inflammatory"),
    "crp": LOINCCode("1988-5", "C reactive protein [Mass/volume] in Serum or Plasma", "inflammatory"),
    "c-reactive protein": LOINCCode("1988-5", "C reactive protein [Mass/volume] in Serum or Plasma", "inflammatory"),
    "high sensitivity crp": LOINCCode("30522-7", "C reactive protein [Mass/volume] in Serum or Plasma by High sensitivity method", "inflammatory"),
    "hs-crp": LOINCCode("30522-7", "C reactive protein [Mass/volume] in Serum or Plasma by High sensitivity method", "inflammatory"),

    # -------------------------------------------------------------------------
    # Vitamins / Nutrients
    # -------------------------------------------------------------------------
    "vitamin d": LOINCCode("14635-7", "25-Hydroxyvitamin D3 [Moles/volume] in Serum or Plasma", "vitamins"),
    "25-oh vitamin d": LOINCCode("14635-7", "25-Hydroxyvitamin D3 [Moles/volume] in Serum or Plasma", "vitamins"),
    "vitamin b12": LOINCCode("2132-9", "Vitamin B12 (Cobalamin) [Mass/volume] in Serum or Plasma", "vitamins"),
    "b12": LOINCCode("2132-9", "Vitamin B12 (Cobalamin) [Mass/volume] in Serum or Plasma", "vitamins"),
    "folate": LOINCCode("2284-8", "Folate [Moles/volume] in Red Blood Cells", "vitamins"),
    "folic acid": LOINCCode("2284-8", "Folate [Moles/volume] in Red Blood Cells", "vitamins"),
    "ferritin": LOINCCode("2276-4", "Ferritin [Mass/volume] in Serum or Plasma", "vitamins"),
    "iron": LOINCCode("2498-4", "Iron [Mass/volume] in Serum or Plasma", "vitamins"),
    "tibc": LOINCCode("2500-7", "Iron binding capacity [Mass/volume] in Serum or Plasma", "vitamins"),
    "total iron binding capacity": LOINCCode("2500-7", "Iron binding capacity [Mass/volume] in Serum or Plasma", "vitamins"),

    # -------------------------------------------------------------------------
    # Tumor Markers / Cancer Screening
    # -------------------------------------------------------------------------
    "psa": LOINCCode("2857-1", "Prostate specific Ag [Mass/volume] in Serum or Plasma", "tumor_markers"),
    "prostate specific antigen": LOINCCode("2857-1", "Prostate specific Ag [Mass/volume] in Serum or Plasma", "tumor_markers"),
    "cea": LOINCCode("2039-6", "Carcinoembryonic Ag [Mass/volume] in Serum or Plasma", "tumor_markers"),
    "carcinoembryonic antigen": LOINCCode("2039-6", "Carcinoembryonic Ag [Mass/volume] in Serum or Plasma", "tumor_markers"),
    "ca 19-9": LOINCCode("24108-3", "Cancer Ag 19-9 [Units/volume] in Serum or Plasma", "tumor_markers"),
    "ca 125": LOINCCode("10334-1", "Cancer Ag 125 [Units/volume] in Serum or Plasma", "tumor_markers"),

    # -------------------------------------------------------------------------
    # Renal Function
    # -------------------------------------------------------------------------
    "renal function panel": LOINCCode("24362-6", "Renal function 2000 panel - Serum or Plasma", "renal"),
    "kidney function": LOINCCode("24362-6", "Renal function 2000 panel - Serum or Plasma", "renal"),
    "egfr": LOINCCode("33914-3", "Glomerular filtration rate/1.73 sq M.predicted [Volume Rate/Area] in Serum or Plasma by Creatinine-based formula (MDRD)", "renal"),
    "glomerular filtration rate": LOINCCode("33914-3", "Glomerular filtration rate/1.73 sq M.predicted [Volume Rate/Area] in Serum or Plasma by Creatinine-based formula (MDRD)", "renal"),
    "uric acid": LOINCCode("3084-1", "Uric acid [Mass/volume] in Serum or Plasma", "renal"),

    # -------------------------------------------------------------------------
    # Arterial Blood Gas (ABG)
    # -------------------------------------------------------------------------
    "arterial blood gas": LOINCCode("24336-0", "Gas panel - Arterial blood", "blood_gas"),
    "abg": LOINCCode("24336-0", "Gas panel - Arterial blood", "blood_gas"),
    "venous blood gas": LOINCCode("24338-6", "Gas panel - Venous blood", "blood_gas"),
    "vbg": LOINCCode("24338-6", "Gas panel - Venous blood", "blood_gas"),
    "ph": LOINCCode("2744-1", "pH of Arterial blood", "blood_gas"),
    "pco2": LOINCCode("2019-8", "Carbon dioxide [Partial pressure] in Arterial blood", "blood_gas"),
    "po2": LOINCCode("2703-7", "Oxygen [Partial pressure] in Arterial blood", "blood_gas"),

    # -------------------------------------------------------------------------
    # Other Common Tests
    # -------------------------------------------------------------------------
    "lactate": LOINCCode("2524-7", "Lactate [Moles/volume] in Serum or Plasma", "chemistry"),
    "lactic acid": LOINCCode("2524-7", "Lactate [Moles/volume] in Serum or Plasma", "chemistry"),
    "ammonia": LOINCCode("1845-7", "Ammonia [Moles/volume] in Serum or Plasma", "chemistry"),
    "lipase": LOINCCode("3040-3", "Lipase [Enzymatic activity/volume] in Serum or Plasma", "chemistry"),
    "amylase": LOINCCode("1798-8", "Amylase [Enzymatic activity/volume] in Serum or Plasma", "chemistry"),
}


def normalize_lab_name(name: str) -> str:
    """
    Normalize a lab test name for matching.

    Strips common suffixes like "test", "level", "panel".
    """
    if not name:
        return ""

    # Lowercase and strip
    name = name.lower().strip()

    # Remove common suffixes
    suffixes = [
        r'\s+test[s]?$', r'\s+level[s]?$', r'\s+panel[s]?$',
        r'\s+serum$', r'\s+plasma$', r'\s+blood$',
        r'\s+check$', r'\s+screen$', r'\s+screening$',
    ]
    for pattern in suffixes:
        name = re.sub(pattern, '', name, flags=re.IGNORECASE)

    # Remove extra whitespace
    name = re.sub(r'\s+', ' ', name).strip()

    return name


def similarity_score(s1: str, s2: str) -> float:
    """Calculate similarity between two strings (0.0 to 1.0)."""
    return SequenceMatcher(None, s1, s2).ratio()


def lookup_loinc(
    lab_name: str,
    min_similarity: float = 0.85
) -> tuple[str | None, str | None, float, bool]:
    """
    Look up LOINC code for a lab test name.

    Args:
        lab_name: The lab test name to look up
        min_similarity: Minimum similarity score for fuzzy matching (0.0-1.0)

    Returns:
        Tuple of (loinc_code, display_name, confidence, matched)
        - confidence is 1.0 for exact match, <1.0 for fuzzy match
        - matched is True if found in database, False otherwise
    """
    if not lab_name:
        return None, None, 0.0, False

    normalized = normalize_lab_name(lab_name)

    # 1. Exact match
    if normalized in LOINC_DATABASE:
        code = LOINC_DATABASE[normalized]
        return code.code, code.display, 1.0, True

    # 2. Fuzzy matching
    best_match = None
    best_score = 0.0

    for db_name, code in LOINC_DATABASE.items():
        score = similarity_score(normalized, db_name)
        if score > best_score and score >= min_similarity:
            best_score = score
            best_match = code

    if best_match:
        return best_match.code, best_match.display, round(best_score, 2), True

    # No match found
    return None, None, 0.0, False


def get_lab_category(lab_name: str) -> str | None:
    """
    Get the category for a lab test.

    Args:
        lab_name: The lab test name

    Returns:
        Category string or None if not found
    """
    normalized = normalize_lab_name(lab_name)

    if normalized in LOINC_DATABASE:
        return LOINC_DATABASE[normalized].category

    return None


def enrich_labs_with_loinc(lab_orders: list) -> list:
    """
    Enrich a list of lab order objects with LOINC codes.

    This function adds verified LOINC codes to lab orders, preferring
    lookup codes over any LLM-generated codes.

    Args:
        lab_orders: List of lab order objects

    Returns:
        The same list with LOINC codes and match status added
    """
    for lab in lab_orders:
        if not lab.get('name'):
            continue

        loinc, display, confidence, matched = lookup_loinc(lab['name'])

        # Add loinc_matched field to track verification status
        lab['loinc_matched'] = matched

        if loinc and confidence >= 0.85:
            # Use lookup code (verified) over any existing code
            lab['loinc'] = loinc
            # Store confidence in metadata if available
            if 'confidence' not in lab:
                lab['loinc_confidence'] = confidence

    return lab_orders
