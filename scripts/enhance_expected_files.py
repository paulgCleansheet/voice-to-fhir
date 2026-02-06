"""
Ground Truth Enhancement Script for Expected.json Files.

This script systematically enhances all expected.json ground truth files by:
1. Adding RxNorm codes to medications (using rxnorm_lookup.py)
2. Adding LOINC codes to lab orders (using inline LOINC database)
3. Adding order-diagnosis linking (using order_diagnosis_linker.py)
4. Validating all enhancements for accuracy and completeness

Usage:
    python scripts/enhance_expected_files.py [--dry-run] [--file FILENAME]

Copyright (c) 2026 Cleansheet LLC
License: CC BY 4.0
"""

import json
import sys
from pathlib import Path
from typing import Any
from difflib import SequenceMatcher

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from extraction.rxnorm_lookup import lookup_rxnorm, get_drug_class
from extraction.icd10_lookup import ICD10_DATABASE
from extraction.loinc_lookup import lookup_loinc as loinc_lookup_func


def add_rxnorm_codes(expected: dict, missing_meds: list) -> dict:
    """Add RxNorm codes to medications."""
    medications = expected.get('ehr_data', {}).get('medications', [])
    med_orders = expected.get('orders', {}).get('medication_orders', [])

    all_meds = medications + med_orders

    for med in all_meds:
        if not med.get('name'):
            continue

        rxcui, display, confidence, matched = lookup_rxnorm(med['name'])

        if rxcui and confidence >= 0.85:
            med['rxcui'] = rxcui
            med['rxcui_verified'] = True
            med['rxcui_confidence'] = confidence

            # Add drug class if available
            drug_class = get_drug_class(med['name'])
            if drug_class:
                med['drug_class'] = drug_class
        else:
            # Track missing medications
            missing_meds.append({
                'file': expected.get('metadata', {}).get('script_file', 'unknown'),
                'medication': med['name']
            })
            med['rxcui'] = None
            med['rxcui_verified'] = False

    return expected


def add_loinc_codes(expected: dict, missing_labs: list) -> dict:
    """Add LOINC codes to lab orders."""
    lab_orders = expected.get('orders', {}).get('lab_orders', [])

    for lab in lab_orders:
        if not lab.get('name'):
            continue

        loinc, display, confidence, matched = loinc_lookup_func(lab['name'])

        if loinc and confidence >= 0.85:
            lab['loinc'] = loinc
            lab['loinc_verified'] = True
            lab['loinc_confidence'] = confidence
        else:
            # Track missing labs
            missing_labs.append({
                'file': expected.get('metadata', {}).get('script_file', 'unknown'),
                'lab': lab['name']
            })
            lab['loinc'] = lab.get('loinc')  # Preserve existing if present
            lab['loinc_verified'] = False

    return expected


def link_order_to_diagnosis(order: dict, patient_conditions: list, drug_class: str | None = None) -> dict | None:
    """
    Link an order to a patient diagnosis.

    Returns:
        DiagnosisLink dict or None if no match
    """
    # Import linking rules
    from extraction.order_diagnosis_linker import MEDICATION_DIAGNOSIS_RULES

    # Strategy 1: If drug class provided, use medication rules
    if drug_class and drug_class in MEDICATION_DIAGNOSIS_RULES:
        rules = MEDICATION_DIAGNOSIS_RULES[drug_class]

        # Match against patient conditions
        for icd10, display, base_confidence in rules:
            for condition in patient_conditions:
                if condition.get('icd10') == icd10:
                    return {
                        'icd10': icd10,
                        'display': display,
                        'confidence': 0.95,  # High confidence for matched condition
                        'method': 'patient_condition'
                    }

        # No patient condition match - use highest confidence rule
        if rules:
            icd10, display, confidence = rules[0]  # First rule is highest confidence
            return {
                'icd10': icd10,
                'display': display,
                'confidence': confidence,
                'method': 'rule'
            }

    # Strategy 2: Match order reason text against patient conditions
    reason = order.get('reason', '').lower()
    if reason:
        for condition in patient_conditions:
            condition_name = condition.get('name', '').lower()
            if condition_name and condition_name in reason:
                return {
                    'icd10': condition.get('icd10'),
                    'display': condition.get('name'),
                    'confidence': 0.90,
                    'method': 'patient_condition'
                }

    return None


def add_linked_diagnoses(expected: dict) -> dict:
    """Add linked_diagnosis fields to all orders."""
    patient_conditions = expected.get('ehr_data', {}).get('conditions', [])

    # Process medication orders
    med_orders = expected.get('orders', {}).get('medication_orders', [])
    for order in med_orders:
        drug_class = order.get('drug_class')
        link = link_order_to_diagnosis(order, patient_conditions, drug_class)
        if link:
            order['linked_diagnosis'] = link

    # Process existing medications (if they don't have links)
    medications = expected.get('ehr_data', {}).get('medications', [])
    for med in medications:
        if 'linked_diagnosis' not in med:
            drug_class = med.get('drug_class')
            link = link_order_to_diagnosis(med, patient_conditions, drug_class)
            if link:
                med['linked_diagnosis'] = link

    # Process lab orders
    lab_orders = expected.get('orders', {}).get('lab_orders', [])
    for order in lab_orders:
        link = link_order_to_diagnosis(order, patient_conditions)
        if link:
            order['linked_diagnosis'] = link

    # Process imaging orders
    imaging_orders = expected.get('orders', {}).get('imaging_orders', [])
    for order in imaging_orders:
        link = link_order_to_diagnosis(order, patient_conditions)
        if link:
            order['linked_diagnosis'] = link

    # Process procedure orders
    procedure_orders = expected.get('orders', {}).get('procedure_orders', [])
    for order in procedure_orders:
        link = link_order_to_diagnosis(order, patient_conditions)
        if link:
            order['linked_diagnosis'] = link

    # Process referral orders
    referral_orders = expected.get('orders', {}).get('referral_orders', [])
    for order in referral_orders:
        link = link_order_to_diagnosis(order, patient_conditions)
        if link:
            order['linked_diagnosis'] = link

    return expected


def validate_enhancements(expected: dict) -> dict:
    """Validate all enhancements for accuracy."""
    issues = []

    # Check RxNorm codes
    medications = expected.get('ehr_data', {}).get('medications', [])
    med_orders = expected.get('orders', {}).get('medication_orders', [])
    all_meds = medications + med_orders

    for med in all_meds:
        if med.get('rxcui') and med['rxcui'] not in [code.rxcui for code in __import__('extraction.rxnorm_lookup', fromlist=['RXNORM_DATABASE']).RXNORM_DATABASE.values()]:
            issues.append(f"Invalid RXCUI: {med['name']} -> {med['rxcui']}")

    # Check LOINC codes
    from extraction.loinc_lookup import LOINC_DATABASE as LOINC_DB
    valid_loinc_codes = set(code.code for code in LOINC_DB.values())

    lab_orders = expected.get('orders', {}).get('lab_orders', [])
    for lab in lab_orders:
        if lab.get('loinc') and lab['loinc'] not in valid_loinc_codes:
            issues.append(f"Invalid LOINC: {lab['name']} -> {lab['loinc']}")

    # Check ICD-10 codes in linked diagnoses
    all_orders = (
        expected.get('orders', {}).get('medication_orders', []) +
        expected.get('orders', {}).get('lab_orders', []) +
        expected.get('orders', {}).get('imaging_orders', []) +
        expected.get('orders', {}).get('procedure_orders', []) +
        expected.get('orders', {}).get('referral_orders', [])
    )

    # Get all ICD-10 codes from database
    valid_icd10_codes = set(code.code for code in ICD10_DATABASE.values())

    for order in all_orders:
        if 'linked_diagnosis' in order:
            icd10 = order['linked_diagnosis'].get('icd10')
            if icd10 and icd10 not in valid_icd10_codes:
                issues.append(f"Invalid ICD-10 in linked_diagnosis: {order.get('name')} -> {icd10}")

    return {'valid': len(issues) == 0, 'issues': issues}


def enhance_file(filepath: Path, dry_run: bool = False) -> dict:
    """Enhance a single expected.json file."""
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Processing: {filepath.name}")

    # Load file
    with open(filepath, 'r', encoding='utf-8') as f:
        expected = json.load(f)

    # Track missing codes
    missing_meds = []
    missing_labs = []

    # Add enhancements
    expected = add_rxnorm_codes(expected, missing_meds)
    expected = add_loinc_codes(expected, missing_labs)
    expected = add_linked_diagnoses(expected)

    # Validate
    validation = validate_enhancements(expected)

    # Calculate coverage stats
    medications = expected.get('ehr_data', {}).get('medications', [])
    med_orders = expected.get('orders', {}).get('medication_orders', [])
    all_meds = medications + med_orders

    rxnorm_count = sum(1 for m in all_meds if m.get('rxcui'))
    rxnorm_total = len(all_meds)

    lab_orders = expected.get('orders', {}).get('lab_orders', [])
    loinc_count = sum(1 for l in lab_orders if l.get('loinc'))
    loinc_total = len(lab_orders)

    all_orders = (
        med_orders + lab_orders +
        expected.get('orders', {}).get('imaging_orders', []) +
        expected.get('orders', {}).get('procedure_orders', []) +
        expected.get('orders', {}).get('referral_orders', [])
    )
    linked_count = sum(1 for o in all_orders if 'linked_diagnosis' in o)
    linked_total = len(all_orders)

    stats = {
        'rxnorm': {'count': rxnorm_count, 'total': rxnorm_total, 'coverage': rxnorm_count / rxnorm_total if rxnorm_total > 0 else 0},
        'loinc': {'count': loinc_count, 'total': loinc_total, 'coverage': loinc_count / loinc_total if loinc_total > 0 else 0},
        'linking': {'count': linked_count, 'total': linked_total, 'coverage': linked_count / linked_total if linked_total > 0 else 0},
        'missing_meds': missing_meds,
        'missing_labs': missing_labs,
        'validation': validation
    }

    # Print stats
    print(f"  RxNorm: {rxnorm_count}/{rxnorm_total} ({stats['rxnorm']['coverage']:.0%})")
    print(f"  LOINC:  {loinc_count}/{loinc_total} ({stats['loinc']['coverage']:.0%})")
    print(f"  Linking: {linked_count}/{linked_total} ({stats['linking']['coverage']:.0%})")

    if not validation['valid']:
        print(f"  WARNING: Validation issues: {len(validation['issues'])}")
        for issue in validation['issues'][:3]:
            print(f"     - {issue}")

    # Write enhanced file (unless dry run)
    if not dry_run:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(expected, f, indent=2, ensure_ascii=False)
        print(f"  [OK] Enhanced file written")

    return stats


def generate_report(all_stats: dict, output_path: Path):
    """Generate enhancement report."""
    total_meds = sum(s['rxnorm']['total'] for s in all_stats.values())
    total_rxnorm = sum(s['rxnorm']['count'] for s in all_stats.values())

    total_labs = sum(s['loinc']['total'] for s in all_stats.values())
    total_loinc = sum(s['loinc']['count'] for s in all_stats.values())

    total_orders = sum(s['linking']['total'] for s in all_stats.values())
    total_linked = sum(s['linking']['count'] for s in all_stats.values())

    # Collect all missing items
    all_missing_meds = []
    all_missing_labs = []
    for stats in all_stats.values():
        all_missing_meds.extend(stats['missing_meds'])
        all_missing_labs.extend(stats['missing_labs'])

    report = f"""
================================================================================
GROUND TRUTH ENHANCEMENT REPORT
================================================================================

Overall Coverage:
  RxNorm:  {total_rxnorm}/{total_meds} ({total_rxnorm/total_meds:.1%}) medications have codes
  LOINC:   {total_loinc}/{total_labs} ({total_loinc/total_labs:.1%}) lab orders have codes
  Linking: {total_linked}/{total_orders} ({total_linked/total_orders:.1%}) orders have linked diagnoses

Files Processed: {len(all_stats)}

Missing Medications (need research):
"""

    # Group missing meds by name
    missing_med_names = {}
    for item in all_missing_meds:
        name = item['medication']
        if name not in missing_med_names:
            missing_med_names[name] = []
        missing_med_names[name].append(item['file'])

    for name, files in sorted(missing_med_names.items()):
        report += f"  - {name} (in {', '.join(files)})\n"

    report += "\nMissing Lab Tests (need research):\n"

    # Group missing labs by name
    missing_lab_names = {}
    for item in all_missing_labs:
        name = item['lab']
        if name not in missing_lab_names:
            missing_lab_names[name] = []
        missing_lab_names[name].append(item['file'])

    for name, files in sorted(missing_lab_names.items()):
        report += f"  - {name} (in {', '.join(files)})\n"

    report += "\n"
    report += "="*80
    report += "\n"

    # Write report
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(report)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Enhance expected.json ground truth files')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without writing')
    parser.add_argument('--file', type=str, help='Process single file instead of all')

    args = parser.parse_args()

    # Find expected.json files
    fixtures_dir = Path(__file__).parent.parent / 'tests' / 'fixtures' / 'recordings'

    if args.file:
        files = [fixtures_dir / args.file]
    else:
        files = sorted(fixtures_dir.glob('*.expected.json'))

    print(f"Found {len(files)} files to process")

    # Process files
    all_stats = {}
    for filepath in files:
        try:
            stats = enhance_file(filepath, dry_run=args.dry_run)
            all_stats[filepath.name] = stats
        except Exception as e:
            print(f"  ERROR: {e}")

    # Generate report
    report_path = Path(__file__).parent.parent / 'enhancement_report.txt'
    generate_report(all_stats, report_path)

    print(f"\nReport written to: {report_path}")

    if args.dry_run:
        print("\nDRY RUN - No files were modified")


if __name__ == '__main__':
    main()
