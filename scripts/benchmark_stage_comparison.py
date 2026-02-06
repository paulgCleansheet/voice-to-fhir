#!/usr/bin/env python3
"""
Stage Comparison Benchmark: Compare Stage 1 (AI-only) vs Full Pipeline (Stages 1-4).

This script measures the contribution of each pipeline stage:
- Stage 1: MedGemma AI extraction (semantic understanding)
- Stage 2: Deterministic rules (chief complaints, BP normalization, etc.)
- Stage 3: Code enrichment (ICD-10, RxNorm lookups)
- Stage 4: Order-diagnosis linking

Usage:
    python scripts/benchmark_stage_comparison.py [--verbose] [--output results.json]
    python scripts/benchmark_stage_comparison.py --recording hp

Copyright (c) 2026 Cleansheet LLC
License: CC BY 4.0
"""

import json
import argparse
import sys
from pathlib import Path
from dataclasses import dataclass, field, asdict
from difflib import SequenceMatcher
from typing import Any, Dict, List
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from extraction.medgemma_client import MedGemmaClient, MedGemmaClientConfig
from extraction.extraction_types import ClinicalEntities


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


def fuzzy_match(s1: str, s2: str, threshold: float = 0.80) -> bool:
    """Check if two strings are fuzzy matches."""
    if not s1 or not s2:
        return False
    s1_norm = s1.lower().strip()
    s2_norm = s2.lower().strip()

    # Exact match
    if s1_norm == s2_norm:
        return True

    # Substring match
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


def entities_to_dict(entities: ClinicalEntities) -> dict:
    """Convert ClinicalEntities to dict format."""
    return {
        'conditions': [asdict(c) for c in entities.conditions],
        'medications': [asdict(m) for m in entities.medications],
        'vitals': [asdict(v) for v in entities.vitals],
        'allergies': [asdict(a) for a in entities.allergies],
        'familyHistory': [asdict(f) for f in entities.family_history],
        'labResults': [asdict(l) for l in entities.lab_results],
        'orders': {
            'medications': [asdict(o) for o in entities.medication_orders],
            'labs': [asdict(o) for o in entities.lab_orders],
            'imaging': [asdict(o) for o in entities.imaging_orders],
            'procedures': [asdict(o) for o in entities.procedure_orders],
            'consults': [asdict(o) for o in entities.referral_orders],
        }
    }


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


def compare_stages(
    transcript: str,
    expected: dict,
    workflow: str,
    recording_name: str,
    client: MedGemmaClient
) -> dict:
    """
    Compare Stage 1 (AI-only) vs Full Pipeline (Stages 1-4) for a single recording.

    Returns:
        {
            'stage1': {'conditions': Metrics(...), 'medications': Metrics(...), ...},
            'stage4': {'conditions': Metrics(...), ...},
            'recording_name': str
        }
    """
    print(f"\n{'='*80}")
    print(f"Processing: {recording_name}")
    print(f"{'='*80}")

    # Get both Stage 1 and final output
    stage1_entities, final_entities = client.extract_with_stages(transcript, workflow)

    # Convert to dict format
    stage1_dict = entities_to_dict(stage1_entities)
    final_dict = entities_to_dict(final_entities)

    # Compare against ground truth
    print(f"\nComparing Stage 1 (AI-only) against ground truth...")
    stage1_results = compare_recording(stage1_dict, expected, recording_name)

    print(f"Comparing Stage 4 (Full pipeline) against ground truth...")
    final_results = compare_recording(final_dict, expected, recording_name)

    return {
        'recording_name': recording_name,
        'stage1': stage1_results,
        'stage4': final_results
    }


def print_stage_comparison_table(all_results: list, verbose: bool = False):
    """Print comparison table showing Stage 1 vs Stage 4 performance."""
    print("\n" + "="*120)
    print("STAGE COMPARISON: AI-Only (Stage 1) vs Full Pipeline (Stages 1-4)")
    print("="*120)

    # Header
    header = f"{'Entity Type':<20} {'Stage 1 (AI-only)':<40} {'Stage 4 (Full Pipeline)':<40} {'Delta':<10}"
    print(header)
    print(f"{'':<20} {'P      R      F1':<40} {'P      R      F1':<40} {'F1 Δ':<10}")
    print("-"*120)

    # Aggregate metrics by entity type
    entity_types = ['conditions', 'medications', 'vitals', 'allergies', 'familyHistory', 'orders']

    overall_stage1 = Metrics()
    overall_stage4 = Metrics()

    for entity_type in entity_types:
        stage1_agg = Metrics()
        stage4_agg = Metrics()

        for result in all_results:
            stage1_agg += result['stage1'][entity_type]
            stage4_agg += result['stage4'][entity_type]

        overall_stage1 += stage1_agg
        overall_stage4 += stage4_agg

        # Calculate delta
        delta_f1 = stage4_agg.f1 - stage1_agg.f1

        # Format entity type name
        display_name = {
            'conditions': 'Conditions',
            'medications': 'Medications',
            'vitals': 'Vitals',
            'allergies': 'Allergies',
            'familyHistory': 'Family History',
            'orders': 'Orders'
        }[entity_type]

        # Print row
        stage1_str = f"{stage1_agg.precision:>5.0%}  {stage1_agg.recall:>5.0%}  {stage1_agg.f1:>5.0%}"
        stage4_str = f"{stage4_agg.precision:>5.0%}  {stage4_agg.recall:>5.0%}  {stage4_agg.f1:>5.0%}"
        delta_str = f"{delta_f1:>+6.0%}" if abs(delta_f1) > 0.001 else "  --  "

        print(f"{display_name:<20} {stage1_str:<40} {stage4_str:<40} {delta_str:<10}")

    # Overall row
    print("-"*120)
    stage1_overall_str = f"{overall_stage1.precision:>5.0%}  {overall_stage1.recall:>5.0%}  {overall_stage1.f1:>5.0%}"
    stage4_overall_str = f"{overall_stage4.precision:>5.0%}  {overall_stage4.recall:>5.0%}  {overall_stage4.f1:>5.0%}"
    overall_delta = overall_stage4.f1 - overall_stage1.f1
    overall_delta_str = f"{overall_delta:>+6.0%}"

    print(f"{'OVERALL':<20} {stage1_overall_str:<40} {stage4_overall_str:<40} {overall_delta_str:<10}")
    print("="*120)

    # Key findings
    print("\nKey Findings:")

    # Find biggest improvements
    improvements = []
    for entity_type in entity_types:
        stage1_agg = Metrics()
        stage4_agg = Metrics()
        for result in all_results:
            stage1_agg += result['stage1'][entity_type]
            stage4_agg += result['stage4'][entity_type]

        delta_f1 = stage4_agg.f1 - stage1_agg.f1
        if delta_f1 > 0.05:  # More than 5% improvement
            display_name = {
                'conditions': 'Conditions',
                'medications': 'Medications',
                'vitals': 'Vitals',
                'allergies': 'Allergies',
                'familyHistory': 'Family History',
                'orders': 'Orders'
            }[entity_type]
            improvements.append((display_name, delta_f1))

    improvements.sort(key=lambda x: x[1], reverse=True)

    for name, delta in improvements:
        print(f"  - {name}: +{delta:.0%} F1 improvement (Post-processing highly effective)")

    if overall_delta > 0:
        print(f"  - Overall: +{overall_delta:.1%} F1 improvement from Stages 2-4 (Rules, Enrichment, Linking)")
    else:
        print(f"  - Overall: {overall_delta:.1%} F1 change (AI performs well standalone)")

    print("\nStage Contributions:")
    print(f"  - Stages 2-4 (Post-processing): Adds ~{overall_delta:.1%} F1 overall")

    if verbose:
        print("\n" + "="*120)
        print("PER-RECORDING RESULTS")
        print("="*120)
        for result in all_results:
            print(f"\n{result['recording_name']}:")
            for entity_type in entity_types:
                s1 = result['stage1'][entity_type]
                s4 = result['stage4'][entity_type]
                delta = s4.f1 - s1.f1
                print(f"  {entity_type:20s}: Stage1 F1={s1.f1:.0%}  Stage4 F1={s4.f1:.0%}  Δ={delta:+.0%}")


def main():
    parser = argparse.ArgumentParser(description='Stage Comparison Benchmark')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show per-recording results')
    parser.add_argument('--output', '-o', type=str, help='Output JSON file for detailed results')
    parser.add_argument('--recording', '-r', type=str, help='Process single recording (e.g., "hp")')
    args = parser.parse_args()

    # Load environment
    from dotenv import load_dotenv
    load_dotenv()

    # Initialize MedGemma client
    config = MedGemmaClientConfig(
        api_key=os.getenv('HUGGINGFACE_API_KEY'),
        backend=os.getenv('MEDGEMMA_BACKEND', 'dedicated'),
        endpoint_url=os.getenv('MEDGEMMA_ENDPOINT_URL'),
    )
    client = MedGemmaClient(config)

    # Load ground truth file (contains transcripts)
    fixtures_dir = Path(__file__).parent.parent / 'tests' / 'fixtures'
    ground_truth_file = fixtures_dir / 'ground-truth.json'

    if not ground_truth_file.exists():
        print(f"ERROR: ground-truth.json not found at {ground_truth_file}")
        sys.exit(1)

    with open(ground_truth_file, 'r', encoding='utf-8') as f:
        ground_truth = json.load(f)

    # Build transcript lookup from ground-truth.json
    transcript_lookup = {}
    for recording in ground_truth.get('state', {}).get('reviewPool', []):
        filename = recording.get('filename', '').replace('.webm', '').replace('.wav', '')
        transcript = recording.get('transcript', '')
        workflow = recording.get('workflow', 'general')
        if filename and transcript:
            transcript_lookup[filename] = {'transcript': transcript, 'workflow': workflow}

    recordings_dir = fixtures_dir / 'recordings'

    if args.recording:
        # Single recording
        expected_file = recordings_dir / f"{args.recording}.expected.json"

        if not expected_file.exists():
            print(f"ERROR: Expected file not found: {expected_file}")
            sys.exit(1)

        if args.recording not in transcript_lookup:
            print(f"ERROR: No transcript found for {args.recording} in ground-truth.json")
            sys.exit(1)

        recordings = [(args.recording, expected_file, transcript_lookup[args.recording])]
    else:
        # All recordings
        expected_files = sorted(recordings_dir.glob('*.expected.json'))
        recordings = []

        for expected_file in expected_files:
            recording_name = expected_file.stem.replace('.expected', '')

            if recording_name in transcript_lookup:
                recordings.append((recording_name, expected_file, transcript_lookup[recording_name]))
            else:
                print(f"WARNING: No transcript for {recording_name} in ground-truth.json, skipping")

    print(f"Found {len(recordings)} recordings with transcripts to process")

    # Process each recording
    all_results = []

    for recording_name, expected_file, transcript_data in recordings:
        # Load expected
        with open(expected_file, 'r', encoding='utf-8') as f:
            expected = json.load(f)

        # Get transcript and workflow
        transcript = transcript_data['transcript']
        workflow = transcript_data['workflow']

        # Compare stages
        try:
            result = compare_stages(transcript, expected, workflow, recording_name, client)
            all_results.append(result)
        except Exception as e:
            print(f"ERROR processing {recording_name}: {e}")
            import traceback
            traceback.print_exc()

    # Print comparison table
    if all_results:
        print_stage_comparison_table(all_results, verbose=args.verbose)

        # Save to JSON if requested
        if args.output:
            output_data = {
                'metadata': {
                    'total_recordings': len(all_results),
                    'timestamp': __import__('datetime').datetime.now().isoformat(),
                },
                'results': []
            }

            for result in all_results:
                # Convert Metrics to serializable format
                stage1_data = {k: {'precision': v.precision, 'recall': v.recall, 'f1': v.f1, 'support': v.support}
                               for k, v in result['stage1'].items()}
                stage4_data = {k: {'precision': v.precision, 'recall': v.recall, 'f1': v.f1, 'support': v.support}
                               for k, v in result['stage4'].items()}

                output_data['results'].append({
                    'recording_name': result['recording_name'],
                    'stage1': stage1_data,
                    'stage4': stage4_data
                })

            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2)

            print(f"\nDetailed results saved to: {args.output}")
    else:
        print("No results to display")
        sys.exit(1)


if __name__ == '__main__':
    main()
