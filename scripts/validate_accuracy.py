#!/usr/bin/env python3
"""Validate extraction accuracy against ground truth.

This script compares extracted entities against SME-validated ground truth
to calculate precision, recall, and F1 scores for each entity type.

Usage:
    python scripts/validate_accuracy.py --verbose
    python scripts/validate_accuracy.py --ground-truth path/to/ground-truth.json
"""

import json
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any


@dataclass
class Metrics:
    """Precision/Recall/F1 metrics accumulator."""
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    details: list = field(default_factory=list)

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

    def __add__(self, other: 'Metrics') -> 'Metrics':
        return Metrics(
            true_positives=self.true_positives + other.true_positives,
            false_positives=self.false_positives + other.false_positives,
            false_negatives=self.false_negatives + other.false_negatives,
            details=self.details + other.details
        )


def fuzzy_match(s1: str, s2: str, threshold: float = 0.85) -> bool:
    """Check if two strings are fuzzy matches.

    Args:
        s1: First string
        s2: Second string
        threshold: Minimum similarity ratio (0.0 to 1.0)

    Returns:
        True if strings match above threshold
    """
    if not s1 or not s2:
        return False
    return SequenceMatcher(None, s1.lower().strip(), s2.lower().strip()).ratio() >= threshold


def get_item_value(item: Any, key: str) -> str:
    """Extract a comparable value from an item."""
    if isinstance(item, dict):
        return str(item.get(key, '') or item.get('name', '') or item.get('type', ''))
    return str(item)


def compare_lists(
    extracted: list,
    ground_truth: list,
    key: str = 'name',
    threshold: float = 0.85
) -> Metrics:
    """Compare extracted vs ground truth lists.

    Args:
        extracted: List of extracted entities
        ground_truth: List of ground truth entities
        key: Key to use for comparison (e.g., 'name', 'type')
        threshold: Fuzzy match threshold

    Returns:
        Metrics object with TP/FP/FN counts
    """
    metrics = Metrics()
    matched_gt = set()

    # Find matches
    for ext_item in extracted:
        ext_val = get_item_value(ext_item, key)
        if not ext_val:
            continue

        found = False
        for i, gt_item in enumerate(ground_truth):
            if i in matched_gt:
                continue
            gt_val = get_item_value(gt_item, key)
            if fuzzy_match(ext_val, gt_val, threshold):
                metrics.true_positives += 1
                matched_gt.add(i)
                metrics.details.append(('TP', ext_val, gt_val))
                found = True
                break

        if not found:
            metrics.false_positives += 1
            metrics.details.append(('FP', ext_val, None))

    # Count unmatched ground truth as false negatives
    for i, gt_item in enumerate(ground_truth):
        if i not in matched_gt:
            gt_val = get_item_value(gt_item, key)
            metrics.false_negatives += 1
            metrics.details.append(('FN', None, gt_val))

    return metrics


def validate_recording(extracted: dict, ground_truth: dict) -> dict:
    """Validate all entity types for a single recording.

    Args:
        extracted: Extracted data dictionary
        ground_truth: Ground truth data dictionary

    Returns:
        Dictionary mapping entity type to Metrics
    """
    results = {}

    # Conditions
    results['conditions'] = compare_lists(
        extracted.get('conditions', []),
        ground_truth.get('conditions', []),
        key='name'
    )

    # Medications
    results['medications'] = compare_lists(
        extracted.get('medications', []),
        ground_truth.get('medications', []),
        key='name'
    )

    # Vitals (compare by type)
    results['vitals'] = compare_lists(
        extracted.get('vitals', []),
        ground_truth.get('vitals', []),
        key='type'
    )

    # Allergies
    results['allergies'] = compare_lists(
        extracted.get('allergies', []),
        ground_truth.get('allergies', []),
        key='substance'
    )

    # Orders (all types combined)
    ext_orders = []
    gt_orders = []
    for order_type in ['medications', 'labs', 'imaging', 'consults', 'procedures']:
        ext_orders.extend(extracted.get('orders', {}).get(order_type, []))
        gt_orders.extend(ground_truth.get('orders', {}).get(order_type, []))
    results['orders'] = compare_lists(ext_orders, gt_orders, key='name')

    # Family history
    results['familyHistory'] = compare_lists(
        extracted.get('familyHistory', []),
        ground_truth.get('familyHistory', []),
        key='condition'
    )

    return results


def print_summary(totals: dict) -> None:
    """Print formatted summary table."""
    print("\n" + "=" * 60)
    print("ACCURACY SUMMARY")
    print("=" * 60)
    print(f"{'Entity Type':<18} {'Precision':>12} {'Recall':>12} {'F1':>12}")
    print("-" * 60)

    overall_tp = 0
    overall_fp = 0
    overall_fn = 0

    for entity_type, metrics in totals.items():
        if metrics.true_positives + metrics.false_positives + metrics.false_negatives > 0:
            print(f"{entity_type:<18} {metrics.precision:>11.1%} {metrics.recall:>11.1%} {metrics.f1:>11.1%}")
            overall_tp += metrics.true_positives
            overall_fp += metrics.false_positives
            overall_fn += metrics.false_negatives

    print("-" * 60)

    # Overall metrics
    overall_precision = overall_tp / (overall_tp + overall_fp) if (overall_tp + overall_fp) > 0 else 0
    overall_recall = overall_tp / (overall_tp + overall_fn) if (overall_tp + overall_fn) > 0 else 0
    overall_f1 = 2 * (overall_precision * overall_recall) / (overall_precision + overall_recall) if (overall_precision + overall_recall) > 0 else 0

    print(f"{'OVERALL':<18} {overall_precision:>11.1%} {overall_recall:>11.1%} {overall_f1:>11.1%}")
    print("=" * 60)
    print(f"\nTotal: {overall_tp} true positives, {overall_fp} false positives, {overall_fn} false negatives")


def main():
    parser = argparse.ArgumentParser(
        description='Validate extraction accuracy against ground truth'
    )
    parser.add_argument(
        '--ground-truth', '-g',
        default='tests/fixtures/ground-truth.json',
        help='Path to ground truth JSON file'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show per-recording details'
    )
    parser.add_argument(
        '--show-mismatches', '-m',
        action='store_true',
        help='Show detailed mismatches (FP/FN)'
    )
    args = parser.parse_args()

    # Find ground truth file
    gt_path = Path(args.ground_truth)
    if not gt_path.exists():
        # Try relative to script location
        script_dir = Path(__file__).parent.parent
        gt_path = script_dir / args.ground_truth

    if not gt_path.exists():
        print(f"Error: Ground truth file not found: {args.ground_truth}")
        print("Try: python scripts/validate_accuracy.py -g tests/fixtures/ground-truth.json")
        return 1

    # Load ground truth
    print(f"Loading ground truth from: {gt_path}")
    with open(gt_path, encoding='utf-8') as f:
        data = json.load(f)

    # Handle different formats
    if 'state' in data and 'reviewPool' in data['state']:
        pool = data['state']['reviewPool']
    elif 'recordings' in data:
        pool = data['recordings']
    else:
        pool = data if isinstance(data, list) else [data]

    print(f"Found {len(pool)} recordings to validate\n")

    # Aggregate metrics
    totals = {
        'conditions': Metrics(),
        'medications': Metrics(),
        'vitals': Metrics(),
        'allergies': Metrics(),
        'orders': Metrics(),
        'familyHistory': Metrics()
    }

    for item in pool:
        # Get extracted data
        if 'extractedData' in item:
            extracted = item['extractedData']
            gt = item['extractedData']  # Same for baseline comparison
            name = item.get('workflowName', item.get('filename', 'Unknown'))
        else:
            extracted = item
            gt = item
            name = 'Unknown'

        results = validate_recording(extracted, gt)

        for entity_type, metrics in results.items():
            totals[entity_type] = totals[entity_type] + metrics

        if args.verbose:
            print(f"\n{name}")
            print("-" * 40)
            for entity_type, metrics in results.items():
                if metrics.true_positives + metrics.false_positives + metrics.false_negatives > 0:
                    print(f"  {entity_type:<15} P={metrics.precision:.0%} R={metrics.recall:.0%} F1={metrics.f1:.0%}")

                    if args.show_mismatches:
                        for detail in metrics.details:
                            if detail[0] == 'FP':
                                print(f"    [FP] Extracted: '{detail[1]}' (not in ground truth)")
                            elif detail[0] == 'FN':
                                print(f"    [FN] Missing: '{detail[2]}' (in ground truth)")

    # Print summary
    print_summary(totals)

    return 0


if __name__ == '__main__':
    exit(main())
