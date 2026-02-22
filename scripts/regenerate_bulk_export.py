#!/usr/bin/env python3
"""
Regenerate bulk-export.json by re-running all 16 transcripts through the live API.

Reads transcripts and workflows from the existing bulk-export.json, sends each
to the running API server, and writes a new bulk-export file in the same format
that benchmark_v2_with_baseline.py expects.

Usage:
    # API must be running on localhost:8001
    python scripts/regenerate_bulk_export.py
    python scripts/regenerate_bulk_export.py --api http://localhost:8001
    python scripts/regenerate_bulk_export.py --output tests/fixtures/bulk-export-new.json
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests


def extract_transcript(api_url: str, transcript: str, workflow: str) -> dict:
    """Send a transcript to the API and return the raw JSON response."""
    response = requests.post(
        f"{api_url}/api/v1/extract",
        headers={"Content-Type": "application/json"},
        json={"transcript": transcript, "workflow": workflow},
        timeout=300,
    )
    response.raise_for_status()
    return response.json()


def api_response_to_bulk_item(metadata: dict, transcript: str, result: dict, elapsed_ms: float) -> dict:
    """Convert an API extract response into the bulk-export item format."""
    return {
        "metadata": {
            "script_file": metadata["script_file"],
            "workflow": metadata["workflow"],
            "description": metadata.get("description", ""),
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "metrics": {
                "extraction_ms": round(elapsed_ms, 1),
                "extraction_model": "MedGemma (dedicated)",
            },
        },
        "patient": result.get("patient", {}),
        "ehr_data": {
            "transcript": transcript,
            "conditions": result.get("conditions", []),
            "medications": result.get("medications", []),
            "vitals": result.get("vitals", []),
            "allergies": result.get("allergies", []),
            "family_history": result.get("familyHistory", []),
            "lab_results": result.get("labResults", []),
            "chief_complaint": result.get("chiefComplaint"),
            "social_history": result.get("socialHistory", {}),
        },
        "orders": {
            "medication_orders": result.get("orders", {}).get("medications", []),
            "lab_orders": result.get("orders", {}).get("labs", []),
            "imaging_orders": result.get("orders", {}).get("imaging", []),
            "procedure_orders": result.get("orders", {}).get("procedures", []),
            "referral_orders": result.get("orders", {}).get("consults", []),
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Regenerate bulk-export.json from live API")
    parser.add_argument("--api", default="http://localhost:8001", help="API base URL")
    parser.add_argument(
        "--input",
        default="tests/fixtures/bulk-export.json",
        help="Existing bulk-export to read transcripts/workflows from",
    )
    parser.add_argument(
        "--output",
        default="tests/fixtures/bulk-export.json",
        help="Output path (defaults to overwriting existing bulk-export.json)",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    # Check API health
    print(f"Checking API at {args.api} ...")
    try:
        health = requests.get(f"{args.api}/health", timeout=10).json()
        print(f"  status: {health.get('status')}  medgemma_available: {health.get('medgemma_available')}")
        if not health.get("medgemma_available"):
            print("WARNING: medgemma_available=false — extractions may fail or use fallback.")
    except Exception as e:
        print(f"ERROR: Cannot reach API: {e}")
        sys.exit(1)

    # Load existing bulk-export for transcripts + metadata
    print(f"\nLoading transcripts from {input_path} ...")
    with open(input_path, encoding="utf-8") as f:
        existing = json.load(f)

    items = existing.get("results", [])
    print(f"  Found {len(items)} items\n")

    results = []
    succeeded = 0
    failed = 0

    for i, item in enumerate(items, 1):
        metadata = item.get("metadata", {})
        script_file = metadata.get("script_file", f"unknown-{i}")
        workflow = metadata.get("workflow", "general")
        transcript = item.get("ehr_data", {}).get("transcript", "")

        if not transcript:
            print(f"[{i:2d}/{len(items)}] SKIP  {script_file} — no transcript")
            failed += 1
            continue

        print(f"[{i:2d}/{len(items)}] {script_file} (workflow: {workflow}) ... ", end="", flush=True)
        start = time.time()
        try:
            result = extract_transcript(args.api, transcript, workflow)
            elapsed_ms = (time.time() - start) * 1000
            bulk_item = api_response_to_bulk_item(metadata, transcript, result, elapsed_ms)
            results.append(bulk_item)
            succeeded += 1
            print(f"OK ({elapsed_ms/1000:.1f}s)")
        except Exception as e:
            elapsed_ms = (time.time() - start) * 1000
            print(f"FAILED ({elapsed_ms/1000:.1f}s): {e}")
            # Keep the original item on failure so the benchmark still has data
            results.append(item)
            failed += 1

    # Write output
    output = {
        "exportedAt": datetime.now(timezone.utc).isoformat(),
        "totalItems": len(results),
        "summary": {
            "successful": succeeded,
            "failed": failed,
            "workflows": list({r["metadata"]["workflow"] for r in results}),
        },
        "results": results,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"\nDone: {succeeded} succeeded, {failed} failed")
    print(f"Written to {output_path}")
    if succeeded > 0:
        print("\nRun benchmark against new results:")
        print("  python scripts/benchmark_v2_with_baseline.py")


if __name__ == "__main__":
    main()
