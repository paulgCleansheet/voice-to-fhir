#!/usr/bin/env python3
"""
Rule-Based Baseline Extractor

Simple regex-based clinical entity extraction for benchmarking comparison.
This represents a "naive" approach without medical language model support.

Copyright (c) 2026 Cleansheet LLC
License: CC BY 4.0
"""

import re
from dataclasses import dataclass, field
from typing import Any


# Common medication patterns
MEDICATION_PATTERNS = [
    r'\b(aspirin|lisinopril|metformin|atorvastatin|amlodipine|omeprazole|metoprolol|losartan|gabapentin|hydrochlorothiazide|levothyroxine|simvastatin|pravastatin|rosuvastatin|pantoprazole|furosemide|prednisone|albuterol|fluticasone|montelukast|sertraline|escitalopram|duloxetine|bupropion|trazodone|amoxicillin|azithromycin|ciprofloxacin|doxycycline|cephalexin|ibuprofen|acetaminophen|naproxen|tramadol|oxycodone|hydrocodone|morphine|fentanyl|insulin|glipizide|pioglitazone|sitagliptin|warfarin|apixaban|rivaroxaban|clopidogrel|digoxin|diltiazem|verapamil|carvedilol|spironolactone|potassium|magnesium|calcium|vitamin\s*d|vitamin\s*b12|iron|folic\s*acid)\b',
]

# Dose patterns
DOSE_PATTERN = r'(\d+(?:\.\d+)?)\s*(mg|mcg|g|ml|units?|iu)\b'
FREQUENCY_PATTERN = r'\b(once|twice|three times|four times|daily|bid|tid|qid|q\d+h|every\s+\d+\s+hours?|prn|as needed|at bedtime|qhs|qam|qpm)\b'

# Vital signs patterns
VITALS_PATTERNS = {
    'blood_pressure': r'\b(?:blood pressure|bp)\s*(?:is|of|:)?\s*(\d{2,3})\s*[/\\]\s*(\d{2,3})',
    'heart_rate': r'\b(?:heart rate|hr|pulse)\s*(?:is|of|:)?\s*(\d{2,3})\s*(?:bpm|beats per minute)?',
    'temperature': r'\b(?:temperature|temp)\s*(?:is|of|:)?\s*(\d{2,3}(?:\.\d)?)\s*(?:degrees?|°|f|c)?',
    'respiratory_rate': r'\b(?:respiratory rate|rr|respirations?)\s*(?:is|of|:)?\s*(\d{1,2})',
    'oxygen_saturation': r'\b(?:oxygen saturation|o2 sat|spo2|sat)\s*(?:is|of|:)?\s*(\d{2,3})\s*%?',
    'weight': r'\b(?:weight|wt)\s*(?:is|of|:)?\s*(\d{2,3}(?:\.\d)?)\s*(?:kg|lbs?|pounds?|kilograms?)',
    'height': r'\b(?:height|ht)\s*(?:is|of|:)?\s*(\d{1,3}(?:\.\d)?)\s*(?:cm|in|inches|feet|m)',
}

# Condition patterns (common diagnoses)
CONDITION_PATTERNS = [
    (r'\b(?:type\s*2?\s*)?diabetes(?:\s+mellitus)?\b', 'Diabetes mellitus', 'E11.9'),
    (r'\bhypertension\b', 'Hypertension', 'I10'),
    (r'\bhyperlipidemia\b', 'Hyperlipidemia', 'E78.5'),
    (r'\b(?:coronary\s+artery\s+disease|cad)\b', 'Coronary artery disease', 'I25.10'),
    (r'\batrial\s+fibrillation\b', 'Atrial fibrillation', 'I48.91'),
    (r'\bheart\s+failure\b', 'Heart failure', 'I50.9'),
    (r'\bcopd\b', 'COPD', 'J44.9'),
    (r'\basthma\b', 'Asthma', 'J45.909'),
    (r'\bpneumonia\b', 'Pneumonia', 'J18.9'),
    (r'\b(?:urinary\s+tract\s+infection|uti)\b', 'Urinary tract infection', 'N39.0'),
    (r'\bcellulitis\b', 'Cellulitis', 'L03.90'),
    (r'\bchest\s+pain\b', 'Chest pain', 'R07.9'),
    (r'\b(?:angina|stable\s+angina)\b', 'Angina pectoris', 'I20.9'),
    (r'\bheadache\b', 'Headache', 'R51.9'),
    (r'\bmigraine\b', 'Migraine', 'G43.909'),
    (r'\banxiety\b', 'Anxiety disorder', 'F41.9'),
    (r'\bdepression\b', 'Depression', 'F32.9'),
    (r'\bosteoarthritis\b', 'Osteoarthritis', 'M19.90'),
    (r'\bback\s+pain\b', 'Back pain', 'M54.9'),
    (r'\bgerd\b', 'GERD', 'K21.0'),
    (r'\bhypothyroidism\b', 'Hypothyroidism', 'E03.9'),
    (r'\bobesity\b', 'Obesity', 'E66.9'),
    (r'\bckd\b', 'Chronic kidney disease', 'N18.9'),
    (r'\banemia\b', 'Anemia', 'D64.9'),
]

# Lab order patterns
LAB_PATTERNS = [
    (r'\b(?:cbc|complete\s+blood\s+count)\b', 'Complete blood count', '58410-2'),
    (r'\b(?:bmp|basic\s+metabolic\s+panel)\b', 'Basic metabolic panel', '51990-0'),
    (r'\b(?:cmp|comprehensive\s+metabolic\s+panel)\b', 'Comprehensive metabolic panel', '24323-8'),
    (r'\blipid\s+panel\b', 'Lipid panel', '24331-1'),
    (r'\b(?:hba1c|hemoglobin\s+a1c|a1c)\b', 'Hemoglobin A1c', '4548-4'),
    (r'\btsh\b', 'TSH', '3016-3'),
    (r'\burinalysis\b', 'Urinalysis', '24356-8'),
    (r'\b(?:troponin|troponins?)\b', 'Troponin', '6598-7'),
    (r'\bbnp\b', 'BNP', '42637-9'),
    (r'\bpt\s*/?\s*inr\b', 'PT/INR', '5902-2'),
    (r'\bd-dimer\b', 'D-dimer', '48066-5'),
    (r'\bcrp\b', 'C-reactive protein', '1988-5'),
    (r'\besr\b', 'ESR', '4537-7'),
    (r'\bliver\s+function\b', 'Liver function tests', '24325-3'),
    (r'\bcreatinine\b', 'Creatinine', '2160-0'),
    (r'\begfr\b', 'eGFR', '33914-3'),
]

# Imaging order patterns
IMAGING_PATTERNS = [
    (r'\bchest\s+x-?ray\b', 'Chest X-ray'),
    (r'\b(?:ct\s+scan|ct)\s+(?:of\s+)?(?:the\s+)?(?:chest|abdomen|head|brain)\b', 'CT scan'),
    (r'\bmri\b', 'MRI'),
    (r'\bultrasound\b', 'Ultrasound'),
    (r'\b(?:echo|echocardiogram)\b', 'Echocardiogram'),
    (r'\bstress\s+test\b', 'Stress test'),
    (r'\bekg|ecg|electrocardiogram\b', 'ECG'),
]

# Allergy patterns
ALLERGY_PATTERN = r'\b(?:allergic?\s+to|allergy\s+to|allergies?\s*:?\s*)\s*([a-zA-Z\s,]+?)(?:\.|,|\band\b|$)'


@dataclass
class BaselineExtraction:
    """Extracted entities from baseline rule-based extraction."""
    conditions: list = field(default_factory=list)
    medications: list = field(default_factory=list)
    vitals: list = field(default_factory=list)
    allergies: list = field(default_factory=list)
    lab_orders: list = field(default_factory=list)
    imaging_orders: list = field(default_factory=list)


def extract_medications(text: str) -> list[dict]:
    """Extract medications using regex patterns."""
    text_lower = text.lower()
    medications = []

    for pattern in MEDICATION_PATTERNS:
        for match in re.finditer(pattern, text_lower, re.IGNORECASE):
            med_name = match.group(1).strip()

            # Look for dose near the medication
            dose = None
            freq = None
            context = text_lower[max(0, match.start()-20):min(len(text_lower), match.end()+50)]

            dose_match = re.search(DOSE_PATTERN, context, re.IGNORECASE)
            if dose_match:
                dose = f"{dose_match.group(1)} {dose_match.group(2)}"

            freq_match = re.search(FREQUENCY_PATTERN, context, re.IGNORECASE)
            if freq_match:
                freq = freq_match.group(1)

            medications.append({
                'name': med_name,
                'dose': dose,
                'frequency': freq,
                'rxnorm': None,
                'rxnorm_matched': False,
            })

    # Deduplicate by name
    seen = set()
    unique_meds = []
    for med in medications:
        if med['name'] not in seen:
            seen.add(med['name'])
            unique_meds.append(med)

    return unique_meds


def extract_vitals(text: str) -> list[dict]:
    """Extract vital signs using regex patterns."""
    text_lower = text.lower()
    vitals = []

    for vital_type, pattern in VITALS_PATTERNS.items():
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            if vital_type == 'blood_pressure':
                value = f"{match.group(1)}/{match.group(2)}"
                unit = 'mmHg'
            elif vital_type == 'heart_rate':
                value = match.group(1)
                unit = 'bpm'
            elif vital_type == 'temperature':
                value = match.group(1)
                unit = 'F'
            elif vital_type == 'respiratory_rate':
                value = match.group(1)
                unit = '/min'
            elif vital_type == 'oxygen_saturation':
                value = match.group(1)
                unit = '%'
            elif vital_type == 'weight':
                value = match.group(1)
                unit = 'kg'
            elif vital_type == 'height':
                value = match.group(1)
                unit = 'cm'
            else:
                value = match.group(1)
                unit = None

            vitals.append({
                'type': vital_type,
                'value': value,
                'unit': unit,
            })

    return vitals


def extract_conditions(text: str) -> list[dict]:
    """Extract conditions/diagnoses using regex patterns."""
    text_lower = text.lower()
    conditions = []

    for pattern, name, icd10 in CONDITION_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            conditions.append({
                'name': name,
                'icd10': icd10,
                'status': 'active',
            })

    return conditions


def extract_lab_orders(text: str) -> list[dict]:
    """Extract lab orders using regex patterns."""
    text_lower = text.lower()
    orders = []

    # Look for order context
    order_context = bool(re.search(r'\b(?:order|get|check|draw|obtain|send)\b', text_lower))

    for pattern, name, loinc in LAB_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            # Only include as order if order context present, otherwise it's a result
            if order_context or 'order' in text_lower or 'check' in text_lower:
                orders.append({
                    'name': name,
                    'loinc': loinc,
                })

    return orders


def extract_imaging_orders(text: str) -> list[dict]:
    """Extract imaging orders using regex patterns."""
    text_lower = text.lower()
    orders = []

    for pattern, name in IMAGING_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            orders.append({
                'name': name,
            })

    return orders


def extract_allergies(text: str) -> list[dict]:
    """Extract allergies using regex patterns."""
    text_lower = text.lower()
    allergies = []

    match = re.search(ALLERGY_PATTERN, text_lower, re.IGNORECASE)
    if match:
        allergy_text = match.group(1).strip()
        # Split by common separators
        for allergen in re.split(r'[,;]|\band\b', allergy_text):
            allergen = allergen.strip()
            if allergen and len(allergen) > 2:
                allergies.append({
                    'substance': allergen,
                    'reaction': None,
                })

    # Also look for "NKDA" or "no known allergies"
    if re.search(r'\bnkda\b|no known (?:drug )?allergies', text_lower):
        pass  # No allergies to add

    return allergies


def baseline_extract(transcript: str) -> dict[str, Any]:
    """
    Perform rule-based extraction on a clinical transcript.

    Args:
        transcript: Clinical transcript text

    Returns:
        Dictionary with extracted entities
    """
    return {
        'conditions': extract_conditions(transcript),
        'medications': extract_medications(transcript),
        'vitals': extract_vitals(transcript),
        'allergies': extract_allergies(transcript),
        'orders': {
            'medications': [],  # Hard to detect new orders vs existing meds with regex
            'labs': extract_lab_orders(transcript),
            'imaging': extract_imaging_orders(transcript),
            'consults': [],  # Hard to detect with simple patterns
            'procedures': [],
        },
        'labResults': [],
        'familyHistory': [],
        'socialHistory': None,
    }


if __name__ == '__main__':
    # Test with sample transcript
    sample = """
    Patient is a 55-year-old male with type 2 diabetes and hypertension.
    Current medications include metformin 1000mg twice daily and lisinopril 20mg daily.
    Blood pressure today 142/88. Heart rate 78.
    Allergic to penicillin.
    Order CBC, BMP, and HbA1c.
    """

    result = baseline_extract(sample)
    import json
    print(json.dumps(result, indent=2))
