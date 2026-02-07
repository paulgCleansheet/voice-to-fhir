#!/usr/bin/env python3
"""
Benchmark with Pristine Transcripts: Three-way comparison.

Compares:
- MedGemma + MedASR transcripts (real-world)
- MedGemma + Pristine scripts (ceiling performance)
- Baseline regex (no LLM)

This isolates whether extraction errors come from ASR or MedGemma.

Usage:
    python scripts/benchmark_pristine.py
    python scripts/benchmark_pristine.py --verbose
"""

import json
import argparse
import re
import os
import sys
from pathlib import Path
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any, Dict, List, Tuple
import requests

# Add scripts directory to path for baseline_extractor
sys.path.insert(0, str(Path(__file__).parent))
from baseline_extractor import baseline_extract


@dataclass
class Metrics:
    """Precision/Recall/F1 metrics accumulator."""
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0

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
        return self.true_positives + self.false_negatives

    def __add__(self, other: 'Metrics') -> 'Metrics':
        return Metrics(
            true_positives=self.true_positives + other.true_positives,
            false_positives=self.false_positives + other.false_positives,
            false_negatives=self.false_negatives + other.false_negatives,
        )


def fuzzy_match(s1: str, s2: str, threshold: float = 0.80) -> bool:
    """Check if two strings are fuzzy matches."""
    if not s1 or not s2:
        return False
    s1_norm = s1.lower().strip()
    s2_norm = s2.lower().strip()
    if s1_norm == s2_norm:
        return True
    if s1_norm in s2_norm or s2_norm in s1_norm:
        return True
    return SequenceMatcher(None, s1_norm, s2_norm).ratio() >= threshold


def get_entity_key(entity: Any, key_field: str) -> str:
    """Extract comparable key from entity."""
    if isinstance(entity, dict):
        for k in [key_field, 'name', 'type', 'condition', 'substance']:
            if k in entity and entity[k]:
                return str(entity[k])
        return str(entity)
    return str(entity)


def compare_entity_lists(actual: List[Any], expected: List[Any], key_field: str = 'name') -> Metrics:
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
            if fuzzy_match(act_key, exp_key):
                metrics.true_positives += 1
                matched_expected.add(i)
                found = True
                break
        if not found:
            metrics.false_positives += 1

    metrics.false_negatives = len(expected) - len(matched_expected)
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
        'orders': {
            'medications': orders.get('medication_orders', []),
            'labs': orders.get('lab_orders', []),
            'imaging': orders.get('imaging_orders', []),
            'procedures': orders.get('procedure_orders', []),
            'consults': orders.get('referral_orders', []),
        }
    }


def compare_recording(actual: dict, expected: dict) -> Dict[str, Metrics]:
    """Compare all entity types for a single recording."""
    results = {}
    exp_norm = normalize_expected(expected)

    results['conditions'] = compare_entity_lists(
        actual.get('conditions', []), exp_norm.get('conditions', []), key_field='name')
    results['medications'] = compare_entity_lists(
        actual.get('medications', []), exp_norm.get('medications', []), key_field='name')
    results['vitals'] = compare_entity_lists(
        actual.get('vitals', []), exp_norm.get('vitals', []), key_field='type')
    results['allergies'] = compare_entity_lists(
        actual.get('allergies', []), exp_norm.get('allergies', []), key_field='substance')
    results['familyHistory'] = compare_entity_lists(
        actual.get('familyHistory', []), exp_norm.get('familyHistory', []), key_field='condition')

    # Orders (combined)
    actual_orders = []
    expected_orders = []
    for order_type in ['medications', 'labs', 'imaging', 'procedures', 'consults']:
        actual_orders.extend(actual.get('orders', {}).get(order_type, []))
        expected_orders.extend(exp_norm.get('orders', {}).get(order_type, []))
    results['orders'] = compare_entity_lists(actual_orders, expected_orders, key_field='name')

    return results


def load_pristine_scripts(script_path: Path) -> Dict[str, str]:
    """Load pristine scripts from script.md file."""
    scripts = {}
    content = script_path.read_text(encoding='utf-8')

    # Parse markdown headers and content
    current_name = None
    current_content = []

    for line in content.split('\n'):
        # Match headers like "# emergency.webm" or "# hp.webm"
        header_match = re.match(r'^#\s+(\S+\.webm|complex\S*)', line.strip())
        if header_match:
            # Save previous script
            if current_name and current_content:
                script_text = '\n'.join(current_content).strip()
                if script_text:
                    scripts[current_name] = script_text
            # Start new script
            current_name = header_match.group(1).replace('.webm', '').replace('.wav', '')
            # Normalize name
            if current_name == 'h-p':
                current_name = 'hp'
            current_content = []
        elif line.strip().startswith('---'):
            # Section break, save current and reset
            if current_name and current_content:
                script_text = '\n'.join(current_content).strip()
                if script_text:
                    scripts[current_name] = script_text
            current_name = None
            current_content = []
        elif current_name:
            current_content.append(line)

    # Save last script
    if current_name and current_content:
        script_text = '\n'.join(current_content).strip()
        if script_text:
            scripts[current_name] = script_text

    return scripts


def load_complex_script(complex_path: Path) -> str:
    """Load complex patient script from markdown file."""
    content = complex_path.read_text(encoding='utf-8')

    # Extract the script section (between "## Script" and "## Expected Extractions")
    script_start = content.find('## Script')
    expected_start = content.find('## Expected Extractions')

    if script_start >= 0 and expected_start > script_start:
        script_section = content[script_start:expected_start]
        # Remove the header, instruction lines, and separators
        lines = []
        for line in script_section.split('\n'):
            # Skip the header line
            if line.strip().startswith('## Script'):
                continue
            # Skip instruction lines (starting with **)
            if line.strip().startswith('**'):
                continue
            # Skip horizontal rules
            if line.strip() == '---':
                continue
            # Include non-empty lines that are actual script content
            if line.strip():
                lines.append(line.strip())
        return ' '.join(lines)  # Join as single paragraph like script.md format

    return ""


def call_medgemma(transcript: str, endpoint_url: str, api_key: str) -> dict:
    """Call MedGemma endpoint to extract entities from transcript."""

    # Build prompt (simplified version of the full prompt)
    prompt = f"""You are a medical documentation assistant. Extract structured clinical information from the following transcript.

Return a JSON object with the following structure:
{{
  "patient": {{"name": null, "date_of_birth": null, "gender": null}},
  "chief_complaint": "string or null",
  "conditions": [{{"name": "string", "icd10": "string or null", "status": "active|resolved|suspected"}}],
  "vitals": [{{"type": "string", "value": "string", "unit": "string or null"}}],
  "medications": [{{"name": "string", "dose": "string or null", "frequency": "string or null"}}],
  "allergies": [{{"substance": "string", "reaction": "string or null", "severity": "string or null"}}],
  "family_history": [{{"relationship": "string", "condition": "string", "age_of_onset": "string or null"}}],
  "lab_results": [{{"name": "string", "value": "string", "interpretation": "string or null"}}],
  "medication_orders": [{{"name": "string", "dose": "string or null"}}],
  "lab_orders": [{{"name": "string"}}],
  "referral_orders": [{{"specialty": "string", "reason": "string or null"}}],
  "procedure_orders": [{{"name": "string"}}],
  "imaging_orders": [{{"name": "string"}}]
}}

Only include information explicitly mentioned in the transcript.
Return valid JSON only, no additional text.

TRANSCRIPT:
{transcript}

JSON:"""

    # Call endpoint (OpenAI-compatible format)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "google/medgemma-4b-it",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4096,
        "temperature": 0.1,
    }

    response = requests.post(
        f"{endpoint_url.rstrip('/')}/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=300.0
    )

    if response.status_code != 200:
        print(f"  [ERROR] MedGemma API: {response.status_code}")
        return {}

    result = response.json()
    choices = result.get("choices", [])
    if not choices:
        return {}

    generated_text = choices[0].get("message", {}).get("content", "")

    # Parse JSON from response
    try:
        json_start = generated_text.find("{")
        json_end = generated_text.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            data = json.loads(generated_text[json_start:json_end])
        else:
            print(f"  [WARN] No JSON found in response (len={len(generated_text)})")
            data = {}
    except json.JSONDecodeError as e:
        print(f"  [WARN] JSON parse error: {e}")
        print(f"  [DEBUG] Response preview: {generated_text[:500]}")
        data = {}

    # Normalize to benchmark format
    return {
        'conditions': data.get('conditions', []),
        'medications': data.get('medications', []),
        'vitals': data.get('vitals', []),
        'allergies': data.get('allergies', []),
        'familyHistory': data.get('family_history', []),
        'orders': {
            'medications': data.get('medication_orders', []),
            'labs': data.get('lab_orders', []),
            'imaging': data.get('imaging_orders', []),
            'procedures': data.get('procedure_orders', []),
            'consults': data.get('referral_orders', []),
        }
    }


def aggregate_metrics(totals: Dict[str, Metrics]) -> Tuple[float, float, float, int]:
    """Calculate overall metrics."""
    tp = sum(m.true_positives for m in totals.values())
    fp = sum(m.false_positives for m in totals.values())
    fn = sum(m.false_negatives for m in totals.values())

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    support = tp + fn

    return precision, recall, f1, support


def print_three_way_table(asr_totals: Dict[str, Metrics],
                          pristine_totals: Dict[str, Metrics],
                          baseline_totals: Dict[str, Metrics]):
    """Print three-way comparison table."""
    print("\n" + "=" * 100)
    print("BENCHMARK RESULTS: MedGemma+ASR vs MedGemma+Pristine vs Baseline")
    print("=" * 100)
    print(f"{'Entity Type':<14} {'MedGemma+ASR':^18} {'MedGemma+Pristine':^18} {'Baseline':^18} {'ASR Gap':>12}")
    print(f"{'':14} {'F1':>8} {'Sup':>8} {'F1':>8} {'Sup':>8} {'F1':>8} {'Sup':>8}")
    print("-" * 100)

    for entity_type in ['conditions', 'medications', 'vitals', 'allergies', 'familyHistory', 'orders']:
        asr = asr_totals.get(entity_type, Metrics())
        pristine = pristine_totals.get(entity_type, Metrics())
        bl = baseline_totals.get(entity_type, Metrics())

        if asr.support > 0 or pristine.support > 0:
            delta = (pristine.f1 - asr.f1) * 100
            delta_str = f"+{delta:.0f}%" if delta > 0 else f"{delta:.0f}%"

            print(f"{entity_type:<14} "
                  f"{asr.f1:>7.0%} {asr.support:>7} "
                  f"{pristine.f1:>7.0%} {pristine.support:>7} "
                  f"{bl.f1:>7.0%} {bl.support:>7} "
                  f"{delta_str:>12}")

    print("-" * 100)

    # Overall
    asr_p, asr_r, asr_f1, asr_sup = aggregate_metrics(asr_totals)
    pr_p, pr_r, pr_f1, pr_sup = aggregate_metrics(pristine_totals)
    bl_p, bl_r, bl_f1, bl_sup = aggregate_metrics(baseline_totals)

    delta_f1 = (pr_f1 - asr_f1) * 100
    delta_str = f"+{delta_f1:.0f}%" if delta_f1 > 0 else f"{delta_f1:.0f}%"

    print(f"{'OVERALL':<14} "
          f"{asr_f1:>7.0%} {asr_sup:>7} "
          f"{pr_f1:>7.0%} {pr_sup:>7} "
          f"{bl_f1:>7.0%} {bl_sup:>7} "
          f"{delta_str:>12}")
    print("=" * 100)

    # Summary
    print(f"\n{'System':<25} {'Precision':>12} {'Recall':>12} {'F1':>12}")
    print("-" * 65)
    print(f"{'MedGemma + ASR':<25} {asr_p:>12.1%} {asr_r:>12.1%} {asr_f1:>12.1%}")
    print(f"{'MedGemma + Pristine':<25} {pr_p:>12.1%} {pr_r:>12.1%} {pr_f1:>12.1%}")
    print(f"{'Baseline (regex)':<25} {bl_p:>12.1%} {bl_r:>12.1%} {bl_f1:>12.1%}")
    print("-" * 65)

    # Analysis
    print("\n" + "=" * 65)
    print("ANALYSIS: Where do errors come from?")
    print("=" * 65)

    asr_gap = (pr_f1 - asr_f1) * 100
    extraction_gap = (1.0 - pr_f1) * 100

    if asr_gap > 5:
        print(f"  ASR Error Impact: -{asr_gap:.0f}% F1 (MedASR transcription errors hurt extraction)")
    else:
        print(f"  ASR Error Impact: ~{asr_gap:.0f}% F1 (MedASR errors have minimal impact)")

    print(f"  Extraction Ceiling: {pr_f1:.0%} F1 (best MedGemma can do with perfect input)")
    print(f"  Room for Improvement: {extraction_gap:.0f}% (extraction model limitations)")


def main():
    parser = argparse.ArgumentParser(description='Three-way benchmark: ASR vs Pristine vs Baseline')
    parser.add_argument('--endpoint', '-e',
                        default='https://cp2wjw95vpf9604w.us-east-1.aws.endpoints.huggingface.cloud',
                        help='MedGemma endpoint URL')
    parser.add_argument('--token', '-t', default=None, help='HuggingFace API token')
    parser.add_argument('--expected-dir', default=None, help='Directory with .expected.json files')
    parser.add_argument('--scripts-dir', default=None, help='Directory with pristine scripts')
    parser.add_argument('--bulk-export', default=None, help='Path to bulk export JSON')
    parser.add_argument('--verbose', '-v', action='store_true')
    parser.add_argument('--limit', '-l', type=int, default=None,
                        help='Limit number of recordings to process')
    args = parser.parse_args()

    # Determine script directory for relative paths
    script_dir = Path(__file__).parent.parent

    # Get API token - check env vars and .env file
    api_key = args.token or os.environ.get('HF_API_TOKEN') or os.environ.get('HF_TOKEN')

    # Try loading from .env file if not found
    if not api_key:
        env_paths = [
            script_dir / '.env',  # Primary: v2hr repo
            Path.cwd() / '.env',  # Current directory
        ]
        for env_path in env_paths:
            if env_path.exists():
                for line in env_path.read_text().split('\n'):
                    if line.startswith('HF_API_TOKEN='):
                        api_key = line.split('=', 1)[1].strip().strip('"').strip("'")
                        break
                if api_key:
                    break

    if not api_key:
        print("Error: HuggingFace token required.")
        print("  Set HF_API_TOKEN environment variable, or")
        print("  Create .env file with HF_API_TOKEN=your_token, or")
        print("  Use --token argument")
        return 1

    # Find expected files (ground truth)
    if args.expected_dir:
        expected_dir = Path(args.expected_dir)
    else:
        for p in [
            script_dir / 'tests' / 'fixtures' / 'recordings',  # Primary: v2hr repo
        ]:
            if p.exists() and list(p.glob('*.expected.json')):
                expected_dir = p
                break
        else:
            print("Error: Could not find expected files directory")
            print("Expected: tests/fixtures/recordings/*.expected.json")
            return 1

    # Find pristine scripts
    if args.scripts_dir:
        scripts_dir = Path(args.scripts_dir)
    else:
        scripts_dir = script_dir / 'tests' / 'fixtures' / 'scripts'

    script_path = scripts_dir / 'script.md'
    complex_path = scripts_dir / 'complex-patient.md'

    # Find bulk export (MedGemma + ASR results)
    if args.bulk_export:
        bulk_path = Path(args.bulk_export)
    else:
        bulk_path = script_dir / 'tests' / 'fixtures' / 'bulk-export.json'

    if not bulk_path.exists():
        print(f"Error: Bulk export not found at {bulk_path}")
        print("Use --bulk-export to specify the path")
        return 1

    print(f"Expected files: {expected_dir}")
    print(f"Pristine scripts: {script_path}")
    print(f"ASR results: {bulk_path}")
    print(f"MedGemma endpoint: {args.endpoint}")

    # Load data
    print("\nLoading data...")

    # Load expected (ground truth)
    expected = {}
    for f in expected_dir.glob('*.expected.json'):
        name = f.stem.replace('.expected', '')
        if name == 'h-p':
            name = 'hp'
        with open(f, encoding='utf-8') as fp:
            expected[name] = json.load(fp)
    print(f"  Loaded {len(expected)} expected files")

    # Load pristine scripts
    pristine_scripts = load_pristine_scripts(script_path)
    if complex_path.exists():
        complex_script = load_complex_script(complex_path)
        if complex_script:
            pristine_scripts['complex1.1'] = complex_script
            if args.verbose:
                print(f"  Complex script loaded: {len(complex_script)} chars")
    print(f"  Loaded {len(pristine_scripts)} pristine scripts")
    if args.verbose:
        for name, script in pristine_scripts.items():
            print(f"    {name}: {len(script)} chars")

    # Load ASR results
    with open(bulk_path, encoding='utf-8') as f:
        bulk_data = json.load(f)

    asr_results = {}
    for item in bulk_data.get('results', []):
        filename = item.get('metadata', {}).get('script_file', '')
        name = filename.replace('.webm', '').replace('.wav', '')
        if name == 'h-p':
            name = 'hp'

        ehr_data = item.get('ehr_data', {})
        orders = item.get('orders', {})

        asr_results[name] = {
            'conditions': ehr_data.get('conditions', []),
            'medications': ehr_data.get('medications', []),
            'vitals': ehr_data.get('vitals', []),
            'allergies': ehr_data.get('allergies', []),
            'familyHistory': ehr_data.get('family_history', []),
            'transcript': ehr_data.get('transcript', ''),
            'orders': {
                'medications': orders.get('medication_orders', []),
                'labs': orders.get('lab_orders', []),
                'imaging': orders.get('imaging_orders', []),
                'procedures': orders.get('procedure_orders', []),
                'consults': orders.get('referral_orders', []),
            }
        }
    print(f"  Loaded {len(asr_results)} ASR results")

    # Find recordings with all three: expected, pristine, and ASR
    matched = set(expected.keys()) & set(pristine_scripts.keys()) & set(asr_results.keys())
    print(f"\nRecordings with all data: {len(matched)}")

    if args.limit:
        matched = set(list(sorted(matched))[:args.limit])
        print(f"  Limited to: {len(matched)}")

    # Initialize totals
    entity_types = ['conditions', 'medications', 'vitals', 'allergies', 'familyHistory', 'orders']
    asr_totals = {k: Metrics() for k in entity_types}
    pristine_totals = {k: Metrics() for k in entity_types}
    baseline_totals = {k: Metrics() for k in entity_types}

    # Process each recording
    print("\nProcessing recordings...")
    for i, name in enumerate(sorted(matched)):
        print(f"\n[{i+1}/{len(matched)}] {name}")

        exp = expected[name]
        asr_extracted = asr_results[name]
        pristine_script = pristine_scripts[name]
        asr_transcript = asr_results[name].get('transcript', '')

        # 1. MedGemma + ASR (already have results)
        asr_metrics = compare_recording(asr_extracted, exp)
        if args.verbose:
            print(f"  ASR: conditions={asr_metrics['conditions'].f1:.0%}, meds={asr_metrics['medications'].f1:.0%}")

        # 2. MedGemma + Pristine (call API)
        print(f"  Calling MedGemma with pristine script ({len(pristine_script)} chars)...")
        pristine_extracted = call_medgemma(pristine_script, args.endpoint, api_key)

        # Debug: show extraction counts
        cond_count = len(pristine_extracted.get('conditions', []))
        med_count = len(pristine_extracted.get('medications', []))
        if cond_count == 0 and med_count == 0:
            print(f"  [WARN] No entities extracted from pristine script!")
        else:
            print(f"  Extracted: {cond_count} conditions, {med_count} medications")

        pristine_metrics = compare_recording(pristine_extracted, exp)
        if args.verbose:
            print(f"  Pristine: conditions={pristine_metrics['conditions'].f1:.0%}, meds={pristine_metrics['medications'].f1:.0%}")

        # 3. Baseline (use ASR transcript for fair comparison)
        baseline_extracted = baseline_extract(asr_transcript)
        baseline_metrics = compare_recording(baseline_extracted, exp)
        if args.verbose:
            print(f"  Baseline: conditions={baseline_metrics['conditions'].f1:.0%}, meds={baseline_metrics['medications'].f1:.0%}")

        # Accumulate
        for entity_type in entity_types:
            asr_totals[entity_type] = asr_totals[entity_type] + asr_metrics[entity_type]
            pristine_totals[entity_type] = pristine_totals[entity_type] + pristine_metrics[entity_type]
            baseline_totals[entity_type] = baseline_totals[entity_type] + baseline_metrics[entity_type]

    # Print results
    print_three_way_table(asr_totals, pristine_totals, baseline_totals)

    return 0


if __name__ == '__main__':
    exit(main())
