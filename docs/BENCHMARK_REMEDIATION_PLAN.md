# Benchmark Remediation Plan

**Created:** January 31, 2026
**Deadline:** February 24, 2026 (MedGemma Challenge)
**Status:** Planning

---

## Executive Summary

The current benchmark has a critical flaw: **circular reasoning** (ground truth IS MedGemma output, so comparing MedGemma to ground truth = 100% by definition). This plan addresses all issues identified in `BENCHMARK_VALIDITY_CRITICAL_ANALYSIS.md`.

### Available Resources

| Resource | Description | Use |
|----------|-------------|-----|
| Medical personas | SMEs who can annotate/validate | Independent ground truth creation |
| Voice collection framework | cleansheet-voice-to-fhir demo UI | Generate new test recordings |
| Extraction pipeline | MedGemma + post-processing | Run actual extractions |
| Dr. Leah Galjan Post | Medical Advisor | Primary annotator, methodology review |

### Timeline Overview

| Phase | Days | Effort | Critical? |
|-------|------|--------|-----------|
| 1. Methodology Fix | 1-2 | 4 hrs | ✅ YES |
| 2. Independent Annotation | 3-7 | 8-12 hrs | ✅ YES |
| 3. Corpus Expansion | 3-10 | 10-15 hrs | ⚠️ HIGH |
| 4. Run Actual Benchmark | 8-10 | 4 hrs | ✅ YES |
| 5. Statistical Analysis | 10-12 | 4 hrs | ⚠️ HIGH |
| 6. Documentation | 12-14 | 4 hrs | ✅ YES |
| 7. Final Validation | 14-16 | 2 hrs | ✅ YES |

**Total Effort:** ~40-50 hours over 2-3 weeks

---

## Phase 1: Methodology Fix (Days 1-2)

### Problem
Current benchmark claims "MedGemma F1: 100%" but this is tautological.

### Solution
Reframe to measure what was actually tested:

```
CURRENT (INVALID):
  MedGemma → Extract → Compare to Ground Truth (which IS MedGemma output) → 100%

CORRECTED:
  1. Create INDEPENDENT ground truth (human annotation)
  2. Run MedGemma on transcripts
  3. Compare MedGemma output to independent ground truth
  4. Report ACTUAL accuracy
```

### Deliverables

1. **Revised BENCHMARKS.md** with honest framing:
   - Acknowledge ground truth creation process
   - Clarify what "reference standard" means
   - Report baseline vs reference (not "MedGemma vs baseline")

2. **New benchmark methodology document** (`docs/BENCHMARK_METHODOLOGY.md`):
   - Annotation guidelines
   - Inter-annotator agreement protocol
   - Entity type definitions

### Action Items

- [ ] Draft revised BENCHMARKS.md structure
- [ ] Create annotation guidelines document
- [ ] Define entity extraction schema formally

---

## Phase 2: Independent Ground Truth Creation (Days 3-7)

### Problem
Current ground truth = MedGemma output + physician spot-check. Not independent.

### Solution
Create truly independent human annotations:

```
Transcript → Annotator 1 (Dr. Post) → Annotation Set A
         → Annotator 2 (Medical Persona) → Annotation Set B
         → Adjudication → Final Ground Truth
```

### Annotation Protocol

**For each of 16 existing transcripts + new transcripts:**

1. **Blind annotation** - Annotator does NOT see MedGemma output
2. **Structured form** - Fill entity extraction form:
   - Conditions (name, ICD-10 if known)
   - Medications (name, dose, frequency)
   - Vitals (type, value, unit)
   - Orders (type, name)
   - Allergies (substance, reaction)
   - Family history (condition, relation)

3. **Time tracking** - Record minutes per transcript
4. **Confidence rating** - Annotator rates confidence (high/medium/low) per entity

### Inter-Annotator Agreement

| Metric | Target | Method |
|--------|--------|--------|
| Cohen's Kappa | > 0.80 | Per entity type |
| % Agreement | > 85% | Exact match |
| Adjudication | 100% | Resolve disagreements |

### Annotator Assignments

| Annotator | Role | Transcripts |
|-----------|------|-------------|
| Dr. Leah Galjan Post | Primary SME | All 16 existing + new |
| Medical Persona 2 | Secondary annotator | Subset (8-10) for IAA |
| Paul (adjudicator) | Resolve disagreements | Disagreements only |

### Deliverables

- [ ] Annotation form template (spreadsheet or web form)
- [ ] Annotator guidelines document
- [ ] Completed annotations for existing 16 transcripts
- [ ] Inter-annotator agreement report

---

## Phase 3: Corpus Expansion (Days 3-10)

### Problem
16 transcripts is too small for statistical confidence (±25% CI).

### Target
**50 transcripts minimum** (±14% CI at 95% confidence)

### Expansion Strategy

| Source | Count | Workflow Coverage |
|--------|-------|-------------------|
| Existing | 16 | Mixed |
| New recordings (medical personas) | 20-25 | Fill gaps |
| Synthetic (scripted) | 10-15 | Edge cases |

### Workflow Coverage Target

| Workflow | Current | Target | Gap |
|----------|---------|--------|-----|
| Cardiology | 1 | 4 | +3 |
| General | 2 | 5 | +3 |
| Emergency | 1 | 4 | +3 |
| SOAP | 1 | 4 | +3 |
| H&P | 1 | 4 | +3 |
| Discharge | 1 | 3 | +2 |
| Procedure | 1 | 3 | +2 |
| Radiology | 1 | 3 | +2 |
| Lab Review | 1 | 3 | +2 |
| Pediatrics | 1 | 3 | +2 |
| Neurology | 1 | 3 | +2 |
| Respiratory | 1 | 3 | +2 |
| ICU | 1 | 3 | +2 |
| Intake | 1 | 3 | +2 |
| Follow-up | 1 | 3 | +2 |
| **Total** | **16** | **51** | **+35** |

### Recording Protocol

Using `cleansheet-voice-to-fhir` demo UI:

1. **Setup:** Medical persona reads scenario card
2. **Record:** Dictate clinical note (~1-3 minutes)
3. **Process:** Run through pipeline (MedASR → MedGemma)
4. **Export:** Save to ground truth pool
5. **Annotate:** Independent human annotation (Phase 2)

### Scenario Cards

Create scripted scenarios to ensure coverage:

```markdown
## Scenario: Cardiology-002

**Workflow:** Cardiology
**Setting:** Outpatient cardiology clinic
**Patient:** 62F with atrial fibrillation

**Key Elements to Include:**
- Chief complaint: palpitations, fatigue
- Medications: warfarin, metoprolol, digoxin
- Vitals: BP 138/82, HR 88 irregular
- Labs: INR 2.4
- Orders: Holter monitor, TSH
- Assessment: A-fib with RVR, subtherapeutic rate control

**Dictate naturally as if documenting real encounter.**
```

### Deliverables

- [ ] 35 scenario cards (one per new transcript needed)
- [ ] Recording sessions scheduled with medical personas
- [ ] New transcripts collected and processed
- [ ] Independent annotations for all new transcripts

---

## Phase 4: Run Actual Benchmark (Days 8-10)

### What We're Actually Measuring

```
                    ┌─────────────────────┐
                    │  Original Transcript │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
    ┌─────────────────┐ ┌─────────────┐ ┌─────────────────┐
    │ MedGemma        │ │ Baseline    │ │ Human Annotator │
    │ Extraction      │ │ (Regex)     │ │ (Ground Truth)  │
    └────────┬────────┘ └──────┬──────┘ └────────┬────────┘
             │                 │                  │
             ▼                 ▼                  ▼
    ┌─────────────────┐ ┌─────────────┐ ┌─────────────────┐
    │ MedGemma Output │ │ Baseline    │ │ Gold Standard   │
    │ (to evaluate)   │ │ Output      │ │ (reference)     │
    └────────┬────────┘ └──────┬──────┘ └────────┬────────┘
             │                 │                  │
             └────────────────┼──────────────────┘
                              ▼
                    ┌─────────────────────┐
                    │ Compare All Three   │
                    │ to Gold Standard    │
                    └─────────────────────┘
```

### Benchmark Script Updates

```python
# scripts/benchmark_v2.py

def run_benchmark(transcripts, ground_truth, baseline_extractor, medgemma_client):
    """
    Compare MedGemma AND baseline against independent ground truth.
    """
    results = {
        'medgemma': defaultdict(Metrics),
        'baseline': defaultdict(Metrics),
    }

    for transcript in transcripts:
        # Get independent ground truth (human annotation)
        gt = ground_truth[transcript.id]

        # Run MedGemma extraction (ACTUALLY RUN IT)
        medgemma_output = medgemma_client.extract(transcript.text)

        # Run baseline extraction
        baseline_output = baseline_extractor.extract(transcript.text)

        # Compare both to ground truth
        for entity_type in ENTITY_TYPES:
            results['medgemma'][entity_type] += compare(
                medgemma_output[entity_type],
                gt[entity_type]
            )
            results['baseline'][entity_type] += compare(
                baseline_output[entity_type],
                gt[entity_type]
            )

    return results
```

### Metrics to Report

| Metric | MedGemma | Baseline | Comparison |
|--------|----------|----------|------------|
| Precision | X% | Y% | +Z% |
| Recall | X% | Y% | +Z% |
| F1 | X% [95% CI] | Y% [95% CI] | +Z% |

### Deliverables

- [ ] `scripts/benchmark_v2.py` - New benchmark script
- [ ] Run benchmark on full 50+ transcript corpus
- [ ] Raw results JSON file
- [ ] Per-transcript breakdown

---

## Phase 5: Statistical Analysis (Days 10-12)

### Confidence Intervals

Use Wilson score interval for proportions:

```python
from scipy.stats import norm

def wilson_ci(successes, total, confidence=0.95):
    """Wilson score confidence interval."""
    if total == 0:
        return (0, 0)

    z = norm.ppf(1 - (1 - confidence) / 2)
    p = successes / total

    denominator = 1 + z**2 / total
    center = (p + z**2 / (2 * total)) / denominator
    spread = z * ((p * (1 - p) + z**2 / (4 * total)) / total) ** 0.5 / denominator

    return (max(0, center - spread), min(1, center + spread))
```

### Statistical Significance

McNemar's test for paired comparison:

```python
from scipy.stats import chi2

def mcnemar_test(medgemma_correct, baseline_correct, both_correct, neither_correct):
    """
    Test if MedGemma significantly outperforms baseline.

    Returns: (chi2_statistic, p_value)
    """
    # Discordant pairs
    b = medgemma_correct - both_correct  # MedGemma right, baseline wrong
    c = baseline_correct - both_correct   # Baseline right, MedGemma wrong

    if b + c == 0:
        return (0, 1.0)

    chi2_stat = (abs(b - c) - 1)**2 / (b + c)
    p_value = 1 - chi2.cdf(chi2_stat, df=1)

    return (chi2_stat, p_value)
```

### Error Analysis

Categorize errors:

| Error Type | MedGemma Count | Baseline Count | Example |
|------------|----------------|----------------|---------|
| False Negative - Synonym | X | Y | "HTN" missed, expected "hypertension" |
| False Negative - Implicit | X | Y | "on lisinopril for BP" → BP not extracted |
| False Negative - Rare entity | X | Y | "pembrolizumab" not in patterns |
| False Positive - Negation | X | Y | "no diabetes" → "diabetes" extracted |
| False Positive - Historical | X | Y | "history of MI" → current condition |

### Deliverables

- [ ] Confidence intervals for all metrics
- [ ] McNemar's test results (p-values)
- [ ] Error analysis table with examples
- [ ] Per-workflow breakdown

---

## Phase 6: Documentation (Days 12-14)

### Updated BENCHMARKS.md Structure

```markdown
# Benchmark Results: v2hr Clinical Extraction

## Executive Summary
- MedGemma achieves X% F1 [95% CI: A-B%] on clinical entity extraction
- Baseline achieves Y% F1 [95% CI: C-D%]
- Improvement: +Z% (p < 0.001, McNemar's test)

## Methodology

### Test Corpus
- N transcripts across M workflow types
- Source: [describe recording process]
- De-identification: [method]

### Ground Truth Creation
- Independent human annotation (not MedGemma output)
- Primary annotator: Leah Galjan Post, MD, FAAP
- Secondary annotator: [Medical Persona]
- Inter-annotator agreement: κ = X.XX

### Annotation Guidelines
[Link to detailed guidelines]

### Extraction Systems
1. **MedGemma:** google/medgemma-4b-it, temp=0.1, [parameters]
2. **Baseline:** Rule-based regex patterns (intentionally simple)

## Results

### Overall Performance

| System | Precision | Recall | F1 | 95% CI |
|--------|-----------|--------|-----|--------|
| MedGemma | X% | X% | X% | [A-B%] |
| Baseline | Y% | Y% | Y% | [C-D%] |

### By Entity Type
[Detailed table]

### Statistical Significance
McNemar's test: χ² = X.XX, p < 0.001

## Error Analysis

### MedGemma Errors
[Examples and categorization]

### Baseline Errors
[Examples and categorization]

## Limitations
1. Corpus size (N transcripts)
2. Single clinical domain focus
3. [Other limitations]

## Reproducibility
[Exact commands to reproduce]
```

### Additional Documents

- [ ] `docs/BENCHMARK_METHODOLOGY.md` - Detailed methodology
- [ ] `docs/ANNOTATION_GUIDELINES.md` - How to annotate
- [ ] `docs/ERROR_ANALYSIS.md` - Full error breakdown

---

## Phase 7: Final Validation (Days 14-16)

### Reproducibility Check

1. **Fresh environment:** Clone repo, install dependencies
2. **Run benchmark:** Execute benchmark script
3. **Verify results:** Confirm numbers match documented results
4. **Timing:** Document runtime, resource usage

### Peer Review Checklist

- [ ] Methodology is clearly documented
- [ ] Results are honestly framed
- [ ] Limitations are acknowledged
- [ ] Statistical claims are supported
- [ ] Error analysis is included
- [ ] Reproducibility instructions work

### Final Files

| File | Status | Notes |
|------|--------|-------|
| `BENCHMARKS.md` | ⬜ | Rewritten with honest framing |
| `scripts/benchmark_v2.py` | ⬜ | New benchmark script |
| `tests/fixtures/ground-truth-v2.json` | ⬜ | Independent annotations |
| `docs/BENCHMARK_METHODOLOGY.md` | ⬜ | Detailed methodology |
| `docs/ANNOTATION_GUIDELINES.md` | ⬜ | Annotation protocol |
| `docs/ERROR_ANALYSIS.md` | ⬜ | Error breakdown |

---

## Risk Mitigation

### Risk: Not enough annotator time

**Mitigation:**
- Prioritize existing 16 transcripts (revalidate with independent annotation)
- Use single annotator + self-review if second annotator unavailable
- Document limitation explicitly

### Risk: MedGemma accuracy lower than expected

**Mitigation:**
- This is actually GOOD - shows honest evaluation
- Frame as "room for improvement" not "failure"
- Compare favorably to baseline regardless

### Risk: Deadline pressure

**Mitigation:**
- Phase 1-2 are CRITICAL - do these first
- Phase 3 (expansion) can be scaled down if needed
- Minimum viable: 16 transcripts with proper methodology > 50 transcripts with bad methodology

---

## Quick Start

### Day 1 Actions

1. ✅ Read this plan
2. ⬜ Create annotation form template
3. ⬜ Draft annotation guidelines
4. ⬜ Schedule annotator sessions

### Day 2 Actions

1. ⬜ Begin independent annotation of existing 16 transcripts
2. ⬜ Create scenario cards for new recordings
3. ⬜ Draft revised BENCHMARKS.md structure

### Day 3+ Actions

Follow phase timeline above.

---

## Questions to Resolve

1. **Second annotator availability?** Who is the medical persona for inter-annotator agreement?
2. **Recording sessions:** When can we schedule new recordings?
3. **MedGemma API access:** Confirm HuggingFace endpoint is working
4. **Annotation tool:** Use spreadsheet, Google Form, or custom UI?

---

## Approval

- [ ] Plan reviewed by Paul
- [ ] Annotator availability confirmed
- [ ] Timeline approved
- [ ] Resources allocated

---

**Next Step:** Confirm annotator availability and begin Phase 1.
