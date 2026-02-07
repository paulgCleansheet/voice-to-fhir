#!/usr/bin/env python3
"""
Benchmark v2 with Baseline: Compare MedGemma AND baseline against human-defined ground truth.

This script compares:
- Expected entities (.expected.json files) = human-defined ground truth
- Actual MedGemma output (ground-truth.json) = what MedGemma extracted
- Baseline output (regex-based) = simple rule-based extraction

Usage:
    python scripts/benchmark_v2_with_baseline.py
    python scripts/benchmark_v2_with_baseline.py --verbose
    python scripts/benchmark_v2_with_baseline.py --errors
"""

import json
import argparse
import sys
from pathlib import Path
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any, Dict, List, Tuple
import math

# Add scripts directory to path for baseline_extractor
sys.path.insert(0, str(Path(__file__).parent))
from baseline_extractor import baseline_extract


@dataclass
class Metrics:
    """Precision/Recall/F1 metrics accumulator."""
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    matches: list = field(default_factory=list)
    fp_details: list = field(default_factory=list)
    fn_details: list = field(default_factory=list)

    @property
    def precision(self) -> float:
        if self.true_positives + self.false_positives == 0:
            return 0.0
        return self.true_positives / (self.true_positives + self.false_positives)

    @property
    def recall(self) -> float:
        if self.true_positives + self.false_negatives == 0:
            return 0.0
        return self.true_positives / (self.true_positives + self.false_negatives)

    @property
    def f1(self) -> float:
        if self.precision + self.recall == 0:
            return 0.0
        return 2 * (self.precision * self.recall) / (self.precision + self.recall)

    @property
    def support(self) -> int:
        """Total ground truth items."""
        return self.true_positives + self.false_negatives

    def __add__(self, other: 'Metrics') -> 'Metrics':
        return Metrics(
            true_positives=self.true_positives + other.true_positives,
            false_positives=self.false_positives + other.false_positives,
            false_negatives=self.false_negatives + other.false_negatives,
            matches=self.matches + other.matches,
            fp_details=self.fp_details + other.fp_details,
            fn_details=self.fn_details + other.fn_details
        )


def wilson_ci(successes: int, total: int, confidence: float = 0.95) -> Tuple[float, float]:
    """Wilson score confidence interval for proportions."""
    if total == 0:
        return (0.0, 0.0)

    z = 1.96 if confidence == 0.95 else 1.645
    p = successes / total

    denominator = 1 + z**2 / total
    center = (p + z**2 / (2 * total)) / denominator
    spread = z * math.sqrt((p * (1 - p) + z**2 / (4 * total)) / total) / denominator

    return (max(0, center - spread), min(1, center + spread))


def normalize_recording_name(name: str) -> str:
    """Normalize recording names for consistent matching.

    Handles variations like 'h-p' vs 'hp', 'follow-up' vs 'followup'.
    """
    # Remove file extensions
    name = name.replace('.webm', '').replace('.wav', '').replace('.expected', '')
    # Normalize common variations
    name_map = {
        'h-p': 'hp',
        'follow-up': 'follow-up',  # keep as-is
        'lab-review': 'lab-review',  # keep as-is
        'cardiology-consult': 'cardiology-consult',  # keep as-is
    }
    return name_map.get(name, name)


def fuzzy_match(s1: str, s2: str, threshold: float = 0.80) -> bool:
    """Check if two strings are fuzzy matches."""
    if not s1 or not s2:
        return False
    s1_norm = s1.lower().strip()
    s2_norm = s2.lower().strip()

    # Exact match
    if s1_norm == s2_norm:
        return True

    # Substring match (for partial names)
    if s1_norm in s2_norm or s2_norm in s1_norm:
        return True

    # Fuzzy match
    return SequenceMatcher(None, s1_norm, s2_norm).ratio() >= threshold


def get_entity_key(entity: Any, key_field: str) -> str:
    """Extract comparable key from entity."""
    if isinstance(entity, dict):
        for k in [key_field, 'name', 'type', 'condition', 'substance']:
            if k in entity and entity[k]:
                return str(entity[k])
        return str(entity)
    return str(entity)


def compare_entity_lists(
    actual: List[Any],
    expected: List[Any],
    key_field: str = 'name',
    threshold: float = 0.80,
    context: str = ""
) -> Metrics:
    """Compare extracted entities against expected ground truth."""
    metrics = Metrics()
    matched_expected = set()

    for act_item in actual:
        act_key = get_entity_key(act_item, key_field)
        if not act_key:
            continue

        found = False
        for i, exp_item in enumerate(expected):
            if i in matched_expected:
                continue
            exp_key = get_entity_key(exp_item, key_field)
            if fuzzy_match(act_key, exp_key, threshold):
                metrics.true_positives += 1
                matched_expected.add(i)
                metrics.matches.append((act_key, exp_key, context))
                found = True
                break

        if not found:
            metrics.false_positives += 1
            metrics.fp_details.append((act_key, context))

    for i, exp_item in enumerate(expected):
        if i not in matched_expected:
            exp_key = get_entity_key(exp_item, key_field)
            metrics.false_negatives += 1
            metrics.fn_details.append((exp_key, context))

    return metrics


def normalize_expected(expected: dict) -> dict:
    """Normalize expected.json format."""
    ehr = expected.get('ehr_data', {})
    orders = expected.get('orders', {})

    return {
        'conditions': ehr.get('conditions', []),
        'medications': ehr.get('medications', []),
        'vitals': ehr.get('vitals', []),
        'allergies': ehr.get('allergies', []),
        'familyHistory': ehr.get('family_history', []),
        'labResults': ehr.get('lab_results', []),
        'orders': {
            'medications': orders.get('medication_orders', []),
            'labs': orders.get('lab_orders', []),
            'imaging': orders.get('imaging_orders', []),
            'procedures': orders.get('procedure_orders', []),
            'consults': orders.get('referral_orders', []),
        }
    }


def compare_recording(actual: dict, expected: dict, name: str) -> Dict[str, Metrics]:
    """Compare all entity types for a single recording."""
    results = {}
    exp_norm = normalize_expected(expected)

    results['conditions'] = compare_entity_lists(
        actual.get('conditions', []),
        exp_norm.get('conditions', []),
        key_field='name',
        context=name
    )

    results['medications'] = compare_entity_lists(
        actual.get('medications', []),
        exp_norm.get('medications', []),
        key_field='name',
        context=name
    )

    results['vitals'] = compare_entity_lists(
        actual.get('vitals', []),
        exp_norm.get('vitals', []),
        key_field='type',
        context=name
    )

    results['allergies'] = compare_entity_lists(
        actual.get('allergies', []),
        exp_norm.get('allergies', []),
        key_field='substance',
        context=name
    )

    results['familyHistory'] = compare_entity_lists(
        actual.get('familyHistory', []),
        exp_norm.get('familyHistory', []),
        key_field='condition',
        context=name
    )

    # Orders (combined)
    actual_orders = []
    expected_orders = []
    for order_type in ['medications', 'labs', 'imaging', 'procedures', 'consults']:
        actual_orders.extend(actual.get('orders', {}).get(order_type, []))
        expected_orders.extend(exp_norm.get('orders', {}).get(order_type, []))

    results['orders'] = compare_entity_lists(
        actual_orders,
        expected_orders,
        key_field='name',
        context=name
    )

    return results


def load_expected_files(expected_dir: Path) -> Dict[str, dict]:
    """Load all .expected.json files."""
    expected = {}
    for f in expected_dir.glob('*.expected.json'):
        name = f.stem.replace('.expected', '')
        name = normalize_recording_name(name)
        with open(f, encoding='utf-8') as fp:
            expected[name] = json.load(fp)
    return expected


def load_actual_extractions(actual_path: Path) -> Dict[str, Tuple[dict, str]]:
    """Load MedGemma extractions AND transcripts from ground-truth.json."""
    with open(actual_path, encoding='utf-8') as f:
        data = json.load(f)

    actual = {}
    pool = data.get('state', {}).get('reviewPool', [])
    for item in pool:
        filename = item.get('filename', '')
        name = filename.replace('.webm', '').replace('.wav', '')
        name = normalize_recording_name(name)
        transcript = item.get('transcript', '')
        extracted = item.get('extractedData', {})
        actual[name] = (extracted, transcript)

    return actual


def load_bulk_export(export_path: Path) -> Dict[str, Tuple[dict, str]]:
    """Load MedGemma extractions from bulk export format (voice-to-fhir-results-*.json).

    Bulk export format:
    {
        "results": [
            {
                "metadata": {"script_file": "cardiology-consult.webm"},
                "ehr_data": {"transcript": "...", "conditions": [...], ...},
                "orders": {"medication_orders": [...], ...}
            }
        ]
    }

    Returns dict mapping recording name to (normalized_extraction, transcript).
    """
    with open(export_path, encoding='utf-8') as f:
        data = json.load(f)

    actual = {}
    results = data.get('results', [])

    for item in results:
        # Get filename from metadata
        metadata = item.get('metadata', {})
        filename = metadata.get('script_file', '')
        name = filename.replace('.webm', '').replace('.wav', '')
        name = normalize_recording_name(name)

        if not name:
            continue

        # Get ehr_data and orders
        ehr_data = item.get('ehr_data', {})
        orders = item.get('orders', {})

        transcript = ehr_data.get('transcript', '')

        # Normalize to the format compare_recording expects
        extracted = {
            'conditions': ehr_data.get('conditions', []),
            'medications': ehr_data.get('medications', []),
            'vitals': ehr_data.get('vitals', []),
            'allergies': ehr_data.get('allergies', []),
            'familyHistory': ehr_data.get('family_history', []),
            'labResults': ehr_data.get('lab_results', []),
            'orders': {
                'medications': orders.get('medication_orders', []),
                'labs': orders.get('lab_orders', []),
                'imaging': orders.get('imaging_orders', []),
                'procedures': orders.get('procedure_orders', []),
                'consults': orders.get('referral_orders', []),
            }
        }

        actual[name] = (extracted, transcript)

    return actual


def detect_file_format(file_path: Path) -> str:
    """Detect whether a JSON file is bulk export or ground-truth format."""
    with open(file_path, encoding='utf-8') as f:
        data = json.load(f)

    if 'results' in data and isinstance(data.get('results'), list):
        return 'bulk_export'
    elif 'state' in data and 'reviewPool' in data.get('state', {}):
        return 'ground_truth'
    else:
        raise ValueError(f"Unknown file format: {file_path}")


def aggregate_metrics(totals: Dict[str, Metrics]) -> Tuple[float, float, float, int]:
    """Calculate overall metrics from per-entity-type totals."""
    overall_tp = sum(m.true_positives for m in totals.values())
    overall_fp = sum(m.false_positives for m in totals.values())
    overall_fn = sum(m.false_negatives for m in totals.values())

    overall_precision = overall_tp / (overall_tp + overall_fp) if (overall_tp + overall_fp) > 0 else 0
    overall_recall = overall_tp / (overall_tp + overall_fn) if (overall_tp + overall_fn) > 0 else 0
    overall_f1 = 2 * (overall_precision * overall_recall) / (overall_precision + overall_recall) if (overall_precision + overall_recall) > 0 else 0
    overall_support = overall_tp + overall_fn

    return overall_precision, overall_recall, overall_f1, overall_support


def print_comparison_table(medgemma_totals: Dict[str, Metrics], baseline_totals: Dict[str, Metrics]):
    """Print side-by-side comparison table."""
    print("\n" + "=" * 90)
    print("BENCHMARK RESULTS: MedGemma vs Baseline (Against Human-Defined Ground Truth)")
    print("=" * 90)
    print(f"{'Entity Type':<16} {'MedGemma':^30} {'Baseline':^30} {'Delta':>10}")
    print(f"{'':16} {'P':>8} {'R':>8} {'F1':>8} {'P':>8} {'R':>8} {'F1':>8} {'F1':>10}")
    print("-" * 90)

    for entity_type in ['conditions', 'medications', 'vitals', 'allergies', 'familyHistory', 'orders']:
        mg = medgemma_totals[entity_type]
        bl = baseline_totals[entity_type]

        if mg.support > 0 or bl.support > 0:
            delta = (mg.f1 - bl.f1) * 100
            delta_str = f"+{delta:.0f}%" if delta > 0 else f"{delta:.0f}%"

            print(f"{entity_type:<16} "
                  f"{mg.precision:>7.0%} {mg.recall:>7.0%} {mg.f1:>7.0%} "
                  f"{bl.precision:>7.0%} {bl.recall:>7.0%} {bl.f1:>7.0%} "
                  f"{delta_str:>10}")

    print("-" * 90)

    # Overall
    mg_p, mg_r, mg_f1, mg_sup = aggregate_metrics(medgemma_totals)
    bl_p, bl_r, bl_f1, bl_sup = aggregate_metrics(baseline_totals)

    delta_f1 = (mg_f1 - bl_f1) * 100
    delta_str = f"+{delta_f1:.0f}%" if delta_f1 > 0 else f"{delta_f1:.0f}%"

    print(f"{'OVERALL':<16} "
          f"{mg_p:>7.0%} {mg_r:>7.0%} {mg_f1:>7.0%} "
          f"{bl_p:>7.0%} {bl_r:>7.0%} {bl_f1:>7.0%} "
          f"{delta_str:>10}")
    print("=" * 90)

    # Summary statistics
    print(f"\nMedGemma F1: {mg_f1:.1%} | Baseline F1: {bl_f1:.1%} | Improvement: {delta_str}")
    print(f"Support: {mg_sup} ground truth entities across all recordings")

    # Confidence intervals
    mg_lower, mg_upper = wilson_ci(int(mg_f1 * mg_sup), mg_sup)
    bl_lower, bl_upper = wilson_ci(int(bl_f1 * bl_sup), bl_sup)
    print(f"\n95% CI - MedGemma: [{mg_lower*100:.1f}% - {mg_upper*100:.1f}%]")
    print(f"95% CI - Baseline: [{bl_lower*100:.1f}% - {bl_upper*100:.1f}%]")


def main():
    parser = argparse.ArgumentParser(
        description='Benchmark MedGemma vs Baseline against human-defined ground truth'
    )
    parser.add_argument('--expected-dir', '-e', default=None,
                        help='Directory containing .expected.json files')
    parser.add_argument('--actual', '-a', default=None,
                        help='Path to MedGemma extractions (ground-truth.json or bulk export)')
    parser.add_argument('--bulk-export', '-b', default=None,
                        help='Path to bulk export file (voice-to-fhir-results-*.json)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show per-recording details')
    parser.add_argument('--errors', '-E', action='store_true',
                        help='Show error analysis (false negatives)')
    args = parser.parse_args()

    script_dir = Path(__file__).parent.parent

    # Find expected files (ground truth)
    if args.expected_dir:
        expected_dir = Path(args.expected_dir)
    else:
        for p in [
            script_dir / 'tests' / 'fixtures' / 'recordings',  # Primary: v2hr repo
            script_dir / 'tests' / 'recordings',               # Legacy location
        ]:
            if p.exists() and list(p.glob('*.expected.json')):
                expected_dir = p
                break
        else:
            print("Error: Could not find expected files directory")
            print("Expected: tests/fixtures/recordings/*.expected.json")
            return 1

    # Find actual extractions - prefer bulk export if specified
    if args.bulk_export:
        actual_path = Path(args.bulk_export)
        file_format = 'bulk_export'
    elif args.actual:
        actual_path = Path(args.actual)
        file_format = detect_file_format(actual_path)
    else:
        # Look for bulk export first, then ground-truth.json
        bulk_paths = [
            script_dir / 'tests' / 'fixtures' / 'bulk-export.json',  # Primary: v2hr repo
        ]
        ground_truth_paths = [
            script_dir / 'tests' / 'fixtures' / 'ground-truth.json',
        ]

        actual_path = None
        file_format = None

        # Try bulk export first
        for p in bulk_paths:
            if p.exists():
                actual_path = p
                file_format = 'bulk_export'
                break

        # Fall back to ground-truth.json
        if not actual_path:
            for p in ground_truth_paths:
                if p.exists():
                    actual_path = p
                    file_format = 'ground_truth'
                    break

        if not actual_path:
            print("Error: Could not find MedGemma extractions file")
            print("Use --bulk-export or --actual to specify the file path")
            return 1

    print(f"Expected files (human-defined): {expected_dir}")
    print(f"MedGemma extractions: {actual_path}")
    print(f"File format: {file_format}")

    # Load data based on format
    expected = load_expected_files(expected_dir)

    if file_format == 'bulk_export':
        actual_data = load_bulk_export(actual_path)
    else:
        actual_data = load_actual_extractions(actual_path)

    print(f"\nFound {len(expected)} expected files, {len(actual_data)} MedGemma extractions")

    # Match recordings
    matched = set(expected.keys()) & set(actual_data.keys())
    print(f"Matched recordings: {len(matched)}")

    if not matched:
        print("\nNo matched recordings found!")
        print(f"Expected keys: {list(expected.keys())[:5]}")
        print(f"Actual keys: {list(actual_data.keys())[:5]}")
        return 1

    # Initialize totals
    medgemma_totals = {k: Metrics() for k in ['conditions', 'medications', 'vitals', 'allergies', 'familyHistory', 'orders']}
    baseline_totals = {k: Metrics() for k in ['conditions', 'medications', 'vitals', 'allergies', 'familyHistory', 'orders']}

    for name in sorted(matched):
        medgemma_extracted, transcript = actual_data[name]
        exp = expected[name]

        # Run baseline extraction on transcript
        baseline_extracted = baseline_extract(transcript)

        # Compare both against expected
        mg_results = compare_recording(medgemma_extracted, exp, name)
        bl_results = compare_recording(baseline_extracted, exp, name)

        for entity_type in medgemma_totals.keys():
            medgemma_totals[entity_type] = medgemma_totals[entity_type] + mg_results[entity_type]
            baseline_totals[entity_type] = baseline_totals[entity_type] + bl_results[entity_type]

        if args.verbose:
            print(f"\n{name}")
            print("-" * 60)
            print(f"  {'Entity':<16} {'MedGemma':^20} {'Baseline':^20}")
            print(f"  {'':16} {'P':>5} {'R':>5} {'F1':>6} {'P':>5} {'R':>5} {'F1':>6}")
            for entity_type in ['conditions', 'medications', 'vitals', 'allergies', 'orders']:
                mg = mg_results[entity_type]
                bl = bl_results[entity_type]
                if mg.support > 0 or mg.false_positives > 0 or bl.false_positives > 0:
                    print(f"  {entity_type:<16} "
                          f"{mg.precision:>4.0%} {mg.recall:>4.0%} {mg.f1:>5.0%} "
                          f"{bl.precision:>4.0%} {bl.recall:>4.0%} {bl.f1:>5.0%}")

    # Print comparison table
    print_comparison_table(medgemma_totals, baseline_totals)

    if args.errors:
        print("\n" + "=" * 90)
        print("ERROR ANALYSIS")
        print("=" * 90)

        print("\n### MEDGEMMA FALSE NEGATIVES (missed extractions):")
        for entity_type, metrics in medgemma_totals.items():
            if metrics.fn_details:
                print(f"\n  {entity_type.upper()}:")
                for item, context in metrics.fn_details[:5]:
                    print(f"    - '{item}' in {context}")
                if len(metrics.fn_details) > 5:
                    print(f"    ... and {len(metrics.fn_details) - 5} more")

        print("\n### BASELINE FALSE NEGATIVES (missed extractions):")
        for entity_type, metrics in baseline_totals.items():
            if metrics.fn_details:
                print(f"\n  {entity_type.upper()}:")
                for item, context in metrics.fn_details[:5]:
                    print(f"    - '{item}' in {context}")
                if len(metrics.fn_details) > 5:
                    print(f"    ... and {len(metrics.fn_details) - 5} more")

    return 0


if __name__ == '__main__':
    exit(main())
