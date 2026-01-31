#!/usr/bin/env python3
"""
Benchmark v2: Compare MedGemma extraction against human-defined ground truth.

This script compares:
- Expected entities (.expected.json files) = human-defined ground truth
- Actual MedGemma output (ground-truth.json) = what the system extracted

This is a VALID benchmark methodology because the expected files were created
independently of MedGemma output.

Usage:
    python scripts/benchmark_v2.py --expected-dir path/to/recordings --actual path/to/ground-truth.json
    python scripts/benchmark_v2.py --verbose
"""

import json
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict
import math


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

    z = 1.96 if confidence == 0.95 else 1.645  # Simplified
    p = successes / total

    denominator = 1 + z**2 / total
    center = (p + z**2 / (2 * total)) / denominator
    spread = z * math.sqrt((p * (1 - p) + z**2 / (4 * total)) / total) / denominator

    return (max(0, center - spread), min(1, center + spread))


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
        # Try multiple possible key fields
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
    """
    Compare MedGemma output (actual) against expected ground truth.

    Args:
        actual: MedGemma extracted entities
        expected: Human-defined expected entities
        key_field: Field to compare on
        threshold: Fuzzy match threshold
        context: Context string for error details

    Returns:
        Metrics with TP, FP, FN counts and details
    """
    metrics = Metrics()
    matched_expected = set()

    # Find matches (actual vs expected)
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

    # Count unmatched expected as false negatives
    for i, exp_item in enumerate(expected):
        if i not in matched_expected:
            exp_key = get_entity_key(exp_item, key_field)
            metrics.false_negatives += 1
            metrics.fn_details.append((exp_key, context))

    return metrics


def normalize_expected(expected: dict) -> dict:
    """Normalize expected.json format to match ground-truth.json structure."""
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

    # Normalize expected format
    exp_norm = normalize_expected(expected)

    # Conditions
    results['conditions'] = compare_entity_lists(
        actual.get('conditions', []),
        exp_norm.get('conditions', []),
        key_field='name',
        context=name
    )

    # Medications (current)
    results['medications'] = compare_entity_lists(
        actual.get('medications', []),
        exp_norm.get('medications', []),
        key_field='name',
        context=name
    )

    # Vitals
    results['vitals'] = compare_entity_lists(
        actual.get('vitals', []),
        exp_norm.get('vitals', []),
        key_field='type',
        context=name
    )

    # Allergies
    results['allergies'] = compare_entity_lists(
        actual.get('allergies', []),
        exp_norm.get('allergies', []),
        key_field='substance',
        context=name
    )

    # Family History
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
        with open(f, encoding='utf-8') as fp:
            expected[name] = json.load(fp)
    return expected


def load_actual_extractions(actual_path: Path) -> Dict[str, dict]:
    """Load MedGemma extractions from ground-truth.json."""
    with open(actual_path, encoding='utf-8') as f:
        data = json.load(f)

    actual = {}
    pool = data.get('state', {}).get('reviewPool', [])
    for item in pool:
        # Use filename without extension as key
        filename = item.get('filename', '')
        name = filename.replace('.webm', '').replace('.wav', '')
        actual[name] = item.get('extractedData', {})

    return actual


def print_results(totals: Dict[str, Metrics], show_errors: bool = False):
    """Print formatted results table."""
    print("\n" + "=" * 70)
    print("BENCHMARK RESULTS: MedGemma vs Human-Defined Ground Truth")
    print("=" * 70)
    print(f"{'Entity Type':<18} {'Precision':>10} {'Recall':>10} {'F1':>10} {'Support':>10}")
    print("-" * 70)

    overall_tp = 0
    overall_fp = 0
    overall_fn = 0

    for entity_type, metrics in totals.items():
        if metrics.support > 0:
            lower, upper = wilson_ci(metrics.true_positives, metrics.support)
            ci_str = f"[{lower*100:.0f}-{upper*100:.0f}%]"
            print(f"{entity_type:<18} {metrics.precision:>9.1%} {metrics.recall:>9.1%} {metrics.f1:>9.1%} {metrics.support:>10}")
            overall_tp += metrics.true_positives
            overall_fp += metrics.false_positives
            overall_fn += metrics.false_negatives

    print("-" * 70)

    # Overall metrics
    overall_precision = overall_tp / (overall_tp + overall_fp) if (overall_tp + overall_fp) > 0 else 0
    overall_recall = overall_tp / (overall_tp + overall_fn) if (overall_tp + overall_fn) > 0 else 0
    overall_f1 = 2 * (overall_precision * overall_recall) / (overall_precision + overall_recall) if (overall_precision + overall_recall) > 0 else 0
    overall_support = overall_tp + overall_fn

    print(f"{'OVERALL':<18} {overall_precision:>9.1%} {overall_recall:>9.1%} {overall_f1:>9.1%} {overall_support:>10}")
    print("=" * 70)

    # Confidence interval for overall F1
    lower, upper = wilson_ci(overall_tp, overall_support)
    print(f"\n95% Confidence Interval (Recall): [{lower*100:.1f}% - {upper*100:.1f}%]")
    print(f"Total: {overall_tp} true positives, {overall_fp} false positives, {overall_fn} false negatives")

    if show_errors:
        print("\n" + "=" * 70)
        print("ERROR ANALYSIS")
        print("=" * 70)

        for entity_type, metrics in totals.items():
            if metrics.fp_details or metrics.fn_details:
                print(f"\n### {entity_type.upper()}")
                if metrics.fn_details:
                    print("  FALSE NEGATIVES (MedGemma missed):")
                    for item, context in metrics.fn_details[:5]:
                        print(f"    - '{item}' in {context}")
                    if len(metrics.fn_details) > 5:
                        print(f"    ... and {len(metrics.fn_details) - 5} more")

                if metrics.fp_details:
                    print("  FALSE POSITIVES (MedGemma hallucinated):")
                    for item, context in metrics.fp_details[:5]:
                        print(f"    - '{item}' in {context}")
                    if len(metrics.fp_details) > 5:
                        print(f"    ... and {len(metrics.fp_details) - 5} more")


def main():
    parser = argparse.ArgumentParser(
        description='Benchmark MedGemma against human-defined ground truth'
    )
    parser.add_argument(
        '--expected-dir', '-e',
        default=None,
        help='Directory containing .expected.json files'
    )
    parser.add_argument(
        '--actual', '-a',
        default=None,
        help='Path to ground-truth.json (MedGemma output)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show per-recording details'
    )
    parser.add_argument(
        '--errors', '-E',
        action='store_true',
        help='Show error analysis'
    )
    args = parser.parse_args()

    # Find files
    script_dir = Path(__file__).parent.parent

    if args.expected_dir:
        expected_dir = Path(args.expected_dir)
    else:
        # Try common locations
        for p in [
            script_dir / 'tests' / 'recordings',
            Path('C:/Users/PaulGaljan/Github/cleansheet-voice-to-fhir/tests/recordings'),
        ]:
            if p.exists():
                expected_dir = p
                break
        else:
            print("Error: Could not find expected files directory")
            return 1

    if args.actual:
        actual_path = Path(args.actual)
    else:
        for p in [
            script_dir / 'tests' / 'fixtures' / 'ground-truth.json',
            script_dir / 'test' / 'fixtures' / 'ground-truth.json',
            Path('C:/Users/PaulGaljan/Github/cleansheet-voice-to-fhir/test/fixtures/ground-truth.json'),
        ]:
            if p.exists():
                actual_path = p
                break
        else:
            print("Error: Could not find ground-truth.json")
            return 1

    print(f"Expected files: {expected_dir}")
    print(f"Actual (MedGemma): {actual_path}")

    # Load data
    expected = load_expected_files(expected_dir)
    actual = load_actual_extractions(actual_path)

    print(f"\nFound {len(expected)} expected files, {len(actual)} actual extractions")

    # Match recordings
    matched = set(expected.keys()) & set(actual.keys())
    print(f"Matched recordings: {len(matched)}")

    if not matched:
        print("\nNo matched recordings found!")
        print(f"Expected keys: {list(expected.keys())[:5]}")
        print(f"Actual keys: {list(actual.keys())[:5]}")
        return 1

    # Aggregate metrics
    totals = {
        'conditions': Metrics(),
        'medications': Metrics(),
        'vitals': Metrics(),
        'allergies': Metrics(),
        'familyHistory': Metrics(),
        'orders': Metrics()
    }

    for name in sorted(matched):
        results = compare_recording(actual[name], expected[name], name)

        for entity_type, metrics in results.items():
            totals[entity_type] = totals[entity_type] + metrics

        if args.verbose:
            print(f"\n{name}")
            print("-" * 40)
            for entity_type, metrics in results.items():
                if metrics.support > 0 or metrics.false_positives > 0:
                    print(f"  {entity_type:<15} P={metrics.precision:.0%} R={metrics.recall:.0%} F1={metrics.f1:.0%} (TP={metrics.true_positives}, FP={metrics.false_positives}, FN={metrics.false_negatives})")

    # Print results
    print_results(totals, show_errors=args.errors)

    return 0


if __name__ == '__main__':
    exit(main())
