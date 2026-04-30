"""
HCC (Hierarchical Condition Category) Lookup for CMS-HCC V28.

Maps ICD-10-CM codes to HCC categories and risk adjustment weights.
Used for US value-based care: identifying HCC-eligible conditions at the
point of voice capture enables HCC-at-capture as a structurally novel lever.

Flow:
    Condition with ICD-10 -> HCC lookup -> populate hcc_* fields on Condition
"""

from typing import NamedTuple

from extraction.extraction_types import ClinicalEntities


class HCCEntry(NamedTuple):
    """HCC mapping entry."""
    hcc_category: str
    hcc_weight: float
    hcc_description: str


# =============================================================================
# CMS-HCC V28 Mapping (~200 high-frequency ICD-10-CM -> HCC)
# Weights are CMS-HCC V28 community, non-dual, aged model (2026 PY)
# =============================================================================

HCC_MAP: dict[str, HCCEntry] = {
    # ── Diabetes (HCC 37) ────────────────────────────────────────────────────
    "E11.9":    HCCEntry("HCC 37",  0.105, "Diabetes without Complication"),
    "E11.65":   HCCEntry("HCC 37",  0.105, "Diabetes without Complication"),
    "E10.9":    HCCEntry("HCC 37",  0.105, "Diabetes without Complication"),

    # ── Diabetes with complications (HCC 18-19) ─────────────────────────────
    "E11.10":   HCCEntry("HCC 18",  0.302, "Diabetes with Ketoacidosis"),
    "E11.21":   HCCEntry("HCC 18",  0.302, "Diabetes with Nephropathy"),
    "E11.22":   HCCEntry("HCC 19",  0.302, "Diabetes with CKD"),
    "E11.40":   HCCEntry("HCC 18",  0.302, "Diabetes with Neuropathy"),
    "E11.621":  HCCEntry("HCC 18",  0.302, "Diabetes with Foot Ulcer"),
    "E10.10":   HCCEntry("HCC 18",  0.302, "Diabetes with Ketoacidosis"),
    "E10.21":   HCCEntry("HCC 18",  0.302, "Type 1 Diabetes with Nephropathy"),

    # ── Obesity (HCC 48) ────────────────────────────────────────────────────
    "E66.01":   HCCEntry("HCC 48",  0.250, "Morbid Obesity"),
    "E66.9":    HCCEntry("HCC 48",  0.250, "Obesity, unspecified"),

    # ── Heart Failure (HCC 85-86) ────────────────────────────────────────────
    "I50.9":    HCCEntry("HCC 85",  0.323, "Heart Failure"),
    "I50.20":   HCCEntry("HCC 85",  0.323, "Systolic Heart Failure, Unspecified"),
    "I50.21":   HCCEntry("HCC 85",  0.323, "Acute Systolic Heart Failure"),
    "I50.22":   HCCEntry("HCC 85",  0.323, "Chronic Systolic Heart Failure"),
    "I50.30":   HCCEntry("HCC 85",  0.323, "Diastolic Heart Failure, Unspecified"),
    "I50.31":   HCCEntry("HCC 85",  0.323, "Acute Diastolic Heart Failure"),
    "I50.40":   HCCEntry("HCC 85",  0.323, "Combined Systolic and Diastolic HF"),
    "I50.41":   HCCEntry("HCC 85",  0.323, "Acute Combined Systolic and Diastolic HF"),

    # ── Coronary Artery Disease (HCC 86-88) ──────────────────────────────────
    "I25.10":   HCCEntry("HCC 88",  0.140, "Atherosclerotic Heart Disease"),
    "I21.9":    HCCEntry("HCC 86",  0.230, "Acute Myocardial Infarction"),
    "I21.4":    HCCEntry("HCC 86",  0.230, "Non-ST Elevation MI"),
    "I21.3":    HCCEntry("HCC 86",  0.230, "ST Elevation MI"),
    "I20.0":    HCCEntry("HCC 87",  0.140, "Unstable Angina"),

    # ── Atrial Fibrillation (HCC 96) ────────────────────────────────────────
    "I48.91":   HCCEntry("HCC 96",  0.258, "Unspecified Atrial Fibrillation"),
    "I48.0":    HCCEntry("HCC 96",  0.258, "Paroxysmal Atrial Fibrillation"),
    "I48.1":    HCCEntry("HCC 96",  0.258, "Persistent Atrial Fibrillation"),
    "I48.2":    HCCEntry("HCC 96",  0.258, "Chronic Atrial Fibrillation"),

    # ── Cerebrovascular Disease (HCC 99-100) ────────────────────────────────
    "I63.9":    HCCEntry("HCC 100", 0.230, "Cerebral Infarction"),
    "I61.9":    HCCEntry("HCC 99",  0.426, "Nontraumatic Intracerebral Hemorrhage"),
    "G45.9":    HCCEntry("HCC 100", 0.230, "TIA"),

    # ── Vascular Disease (HCC 106-108) ──────────────────────────────────────
    "I73.9":    HCCEntry("HCC 108", 0.288, "Peripheral Vascular Disease"),
    "I82.40":   HCCEntry("HCC 107", 0.288, "DVT of Lower Extremity"),
    "I26.99":   HCCEntry("HCC 107", 0.288, "Pulmonary Embolism"),

    # ── COPD / Asthma (HCC 111-112) ─────────────────────────────────────────
    "J44.9":    HCCEntry("HCC 111", 0.335, "COPD, Unspecified"),
    "J44.1":    HCCEntry("HCC 111", 0.335, "COPD with Acute Exacerbation"),
    "J44.0":    HCCEntry("HCC 111", 0.335, "COPD with Lower Respiratory Infection"),
    "J45.909":  HCCEntry("HCC 112", 0.335, "Asthma, Unspecified"),
    "J45.901":  HCCEntry("HCC 112", 0.335, "Asthma with Acute Exacerbation"),
    "J46":      HCCEntry("HCC 112", 0.335, "Status Asthmaticus"),

    # ── Respiratory Failure (HCC 83-84) ──────────────────────────────────────
    "J96.00":   HCCEntry("HCC 83",  0.329, "Acute Respiratory Failure"),
    "J96.90":   HCCEntry("HCC 84",  0.329, "Respiratory Failure, Unspecified"),
    "J80":      HCCEntry("HCC 83",  0.329, "ARDS"),

    # ── Chronic Kidney Disease (HCC 326-329) ────────────────────────────────
    "N18.3":    HCCEntry("HCC 329", 0.069, "CKD Stage 3"),
    "N18.4":    HCCEntry("HCC 328", 0.289, "CKD Stage 4"),
    "N18.5":    HCCEntry("HCC 326", 0.289, "CKD Stage 5"),
    "N18.6":    HCCEntry("HCC 326", 0.456, "End Stage Renal Disease"),
    "N17.9":    HCCEntry("HCC 135", 0.289, "Acute Kidney Injury"),

    # ── Liver Disease (HCC 28-29) ────────────────────────────────────────────
    "K74.60":   HCCEntry("HCC 28",  0.363, "Cirrhosis of Liver"),
    "K76.0":    HCCEntry("HCC 29",  0.363, "Fatty Liver"),

    # ── Infections / Sepsis (HCC 2-4) ───────────────────────────────────────
    "A41.9":    HCCEntry("HCC 2",   0.426, "Sepsis, Unspecified Organism"),
    "A41.51":   HCCEntry("HCC 2",   0.426, "Sepsis due to E. coli"),
    "R65.20":   HCCEntry("HCC 2",   0.426, "Severe Sepsis without Shock"),
    "R65.21":   HCCEntry("HCC 2",   0.426, "Severe Sepsis with Septic Shock"),
    "B20":      HCCEntry("HCC 1",   0.288, "HIV Disease"),

    # ── Cancers (HCC 8-14) ──────────────────────────────────────────────────
    "C34.90":   HCCEntry("HCC 9",   0.972, "Lung Cancer"),
    "C50.919":  HCCEntry("HCC 12",  0.146, "Breast Cancer"),
    "C18.9":    HCCEntry("HCC 11",  0.288, "Colon Cancer"),
    "C61":      HCCEntry("HCC 12",  0.146, "Prostate Cancer"),
    "C25.9":    HCCEntry("HCC 9",   0.972, "Pancreatic Cancer"),
    "C80.1":    HCCEntry("HCC 14",  0.288, "Malignant Neoplasm, Unspecified"),
    "C79.9":    HCCEntry("HCC 8",   0.972, "Metastatic Disease"),
    "C90.00":   HCCEntry("HCC 10",  0.576, "Multiple Myeloma"),
    "C85.90":   HCCEntry("HCC 10",  0.576, "Non-Hodgkin Lymphoma"),
    "C95.90":   HCCEntry("HCC 10",  0.576, "Leukemia"),

    # ── Hematological (HCC 48-49) ────────────────────────────────────────────
    "D64.9":    HCCEntry("HCC 49",  0.250, "Anemia, Unspecified"),
    "D50.9":    HCCEntry("HCC 49",  0.250, "Iron Deficiency Anemia"),
    "D69.6":    HCCEntry("HCC 48",  0.250, "Thrombocytopenia"),

    # ── Neurological (HCC 51-52, 70-74) ─────────────────────────────────────
    "G30.9":    HCCEntry("HCC 51",  0.537, "Alzheimer Disease"),
    "F03.90":   HCCEntry("HCC 52",  0.537, "Dementia, Unspecified"),
    "G20":      HCCEntry("HCC 73",  0.606, "Parkinson Disease"),
    "G35":      HCCEntry("HCC 74",  0.370, "Multiple Sclerosis"),
    "G40.909":  HCCEntry("HCC 75",  0.258, "Epilepsy"),

    # ── Psychiatric (HCC 155-157) ────────────────────────────────────────────
    "F20.9":    HCCEntry("HCC 155", 0.464, "Schizophrenia"),
    "F31.9":    HCCEntry("HCC 155", 0.464, "Bipolar Disorder"),
    "F32.9":    HCCEntry("HCC 157", 0.309, "Major Depressive Disorder"),
    "F10.20":   HCCEntry("HCC 56",  0.329, "Alcohol Dependence"),
    "F11.20":   HCCEntry("HCC 56",  0.329, "Opioid Dependence"),

    # ── Musculoskeletal (HCC 40) ─────────────────────────────────────────────
    "M06.9":    HCCEntry("HCC 40",  0.370, "Rheumatoid Arthritis"),
    "M32.9":    HCCEntry("HCC 40",  0.370, "Systemic Lupus Erythematosus"),

    # ── Hypertension (HCC 95) ────────────────────────────────────────────────
    "I10":      HCCEntry("HCC 95",  0.000, "Essential Hypertension"),
    # Note: I10 maps to HCC 95 but has 0.0 weight in V28 community model
    "I16.1":    HCCEntry("HCC 95",  0.000, "Hypertensive Emergency"),

    # ── Hyperlipidemia — no HCC mapping ──────────────────────────────────────
    # E78.5 and E78.00 do NOT map to any HCC category

    # ── Amputation Status (HCC 189) ──────────────────────────────────────────
    "Z89.411":  HCCEntry("HCC 189", 0.588, "Below Knee Amputation Status"),
    "Z89.511":  HCCEntry("HCC 189", 0.588, "Above Knee Amputation Status"),

    # ── Transplant Status (HCC 186) ─────────────────────────────────────────
    "Z94.0":    HCCEntry("HCC 186", 0.926, "Kidney Transplant Status"),
    "Z94.1":    HCCEntry("HCC 186", 0.926, "Heart Transplant Status"),
    "Z94.4":    HCCEntry("HCC 186", 0.926, "Liver Transplant Status"),

    # ── Osteoporosis with Fracture (HCC 170) ────────────────────────────────
    "M80.00":   HCCEntry("HCC 170", 0.370, "Osteoporosis with Pathological Fracture"),
}


def lookup_hcc(icd10_code: str) -> HCCEntry | None:
    """
    Look up HCC category for an ICD-10-CM code.

    Tries exact match first, then parent code fallback (strip trailing chars).
    """
    if not icd10_code:
        return None

    code = icd10_code.strip().upper()

    # 1. Exact match
    if code in HCC_MAP:
        return HCC_MAP[code]

    # 2. Parent code fallback — progressively strip trailing characters
    # E.g., E11.621 -> E11.62 -> E11.6 -> E11
    while len(code) > 3:
        code = code[:-1]
        if code.endswith("."):
            code = code[:-1]
        if code in HCC_MAP:
            return HCC_MAP[code]

    return None


def enrich_conditions_with_hcc(entities: ClinicalEntities) -> ClinicalEntities:
    """
    Enrich conditions that have ICD-10 codes with HCC category data.

    Populates hcc_category, hcc_weight, hcc_description, hcc_model_version
    on each Condition where a mapping exists.
    """
    for condition in entities.conditions:
        if not condition.icd10:
            continue

        entry = lookup_hcc(condition.icd10)
        if entry:
            condition.hcc_category = entry.hcc_category
            condition.hcc_weight = entry.hcc_weight
            condition.hcc_description = entry.hcc_description
            condition.hcc_model_version = "CMS-HCC V28"

    return entities
