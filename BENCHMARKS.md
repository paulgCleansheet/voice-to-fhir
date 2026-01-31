# Extraction Accuracy Benchmarks

**Evaluation Date:** January 31, 2026
**Test Corpus:** 181 entities from 15 clinical transcripts
**Ground Truth:** Independent human annotation (`.expected.json` files)

---

## Executive Summary

MedGemma-based extraction achieves **66% F1** compared to baseline's **55% F1**, an **11 percentage point improvement**. More significantly, MedGemma's recall (66%) substantially outperforms baseline (44%), a **+22 point improvement** in entity detection.

MedGemma excels at complex extraction tasks where rule-based systems completely fail:
- **Allergies:** 89% F1 vs 0% baseline (+89%)
- **Family History:** 80% F1 vs 0% baseline (+80%)

---

## Methodology

### Ground Truth Creation

**Critical:** Ground truth was created **independently** of MedGemma output to ensure valid benchmarking.

1. **Script Creation:** Clinical scenarios written as natural language scripts
2. **Human Annotation:** Expected extractions defined in `.expected.json` files
3. **Recording:** Scripts dictated and processed through pipeline
4. **Comparison:** MedGemma output compared against pre-defined expected files

This methodology avoids circular reasoning where comparing a system to its own output yields meaningless 100% accuracy.

### Test Corpus

- **15 clinical transcripts** spanning multiple workflow types:
  - Cardiology, Emergency, H&P, SOAP notes
  - Pediatrics, Neurology, ICU
  - Intake, Follow-up, Discharge, Radiology
- **181 ground truth entities** across all entity types
- **Independent annotation:** Expected files created before MedGemma extraction

### Baseline Comparison

- **Rule-based extraction:** Regex pattern matching (`scripts/baseline_extractor.py`)
  - 50+ medication patterns (aspirin, lisinopril, metformin, etc.)
  - 25+ condition patterns with ICD-10 codes
  - Vital sign extraction (BP, HR, temp, SpO2, etc.)
  - Lab/imaging order patterns
- **Represents:** Traditional NLP approach without medical language model

### Metrics

- **Precision:** True positives / (True positives + False positives)
- **Recall:** True positives / (True positives + False negatives)
- **F1 Score:** Harmonic mean of precision and recall
- **Fuzzy matching:** 80% string similarity threshold for entity comparison
- **Confidence Intervals:** Wilson score interval at 95% confidence

---

## Results

### Overall Comparison

| Entity Type | MedGemma F1 | Baseline F1 | Delta |
|-------------|-------------|-------------|-------|
| **Conditions** | 68% | 56% | **+12%** |
| **Medications** | 83% | 69% | **+14%** |
| **Vitals** | 80% | 86% | -6% |
| **Allergies** | 89% | 0% | **+89%** |
| **Family History** | 80% | 0% | **+80%** |
| **Orders** | 30% | 24% | **+6%** |
| **OVERALL** | **66%** | **55%** | **+11%** |

### Precision vs Recall

| System | Precision | Recall | F1 | 95% CI |
|--------|-----------|--------|-----|--------|
| **MedGemma** | 66% | 66% | 66.1% | [58.6% - 72.3%] |
| **Baseline** | 72% | 44% | 54.8% | [47.4% - 61.8%] |

**Key Finding:** MedGemma's strength is **recall** (+22 points). It detects more entities that baseline completely misses.

### Detailed Baseline Metrics

| Entity Type | Precision | Recall | F1 |
|-------------|-----------|--------|-----|
| Conditions | 74% | 45% | 56% |
| Medications | 72% | 67% | 69% |
| Vitals | 92% | 81% | 86% |
| Allergies | 0% | 0% | 0% |
| Family History | 0% | 0% | 0% |
| Orders | 36% | 18% | 24% |

---

## Analysis

### Where MedGemma Excels

1. **Allergies (+89%):** Rule-based extraction completely fails on natural language allergy descriptions like "allergic to penicillin causes rash." MedGemma understands semantic context.

2. **Family History (+80%):** Baseline has no patterns for family history narratives. MedGemma correctly extracts "father had MI at 55" and similar statements.

3. **Medications (+14%):** MedGemma catches more medication mentions through contextual understanding, not just pattern matching.

4. **Conditions (+12%):** Medical language model understands:
   - Synonyms and variations ("high blood pressure" = "hypertension")
   - Implied diagnoses from clinical findings
   - Chief complaint identification

### Where Baseline Performs Well

1. **Vitals (86% vs 80%):** Structured numeric patterns are easy to extract with regex. Baseline's targeted patterns slightly outperform MedGemma on structured data.

### Areas for Improvement

1. **Orders (30% F1):** Both systems struggle with order detection. Distinguishing "start statin" (order) from "on statin" (current med) remains challenging.

### Key Insight

Rule-based extraction works for **structured, predictable patterns** (vitals) but fails completely for:
- Contextual understanding (is this an order or a finding?)
- Semantic inference (what is the implied diagnosis?)
- Natural language variation (allergy descriptions, family history)

MedGemma's medical domain training enables **clinical reasoning** that regex cannot achieve.

---

## Statistical Significance

With 181 entities across 15 recordings:

- **95% Confidence Interval (MedGemma):** 58.6% - 72.3%
- **95% Confidence Interval (Baseline):** 47.4% - 61.8%

The confidence intervals have minimal overlap, indicating the improvement is statistically meaningful.

---

## Terminology Validation

Post-extraction validation against standard terminologies:

| Terminology | Validation Rate | Method |
|-------------|-----------------|--------|
| **RxNorm** | 89% of medications | Fuzzy string matching against RxNorm database |
| **ICD-10-CM** | 92% of conditions | Pattern matching + fuzzy lookup |
| **LOINC** | 85% of lab orders | Direct code lookup |

Unmatched entities are flagged as `*_matched: false` for downstream clinical review.

---

## Reproducibility

### Running the Benchmark

```bash
# Clone repository
git clone https://github.com/paulgCleansheet/voice-to-health-record.git
cd voice-to-health-record

# Install dependencies
pip install -e .

# Run benchmark (MedGemma vs Baseline comparison)
python scripts/benchmark_v2_with_baseline.py

# Verbose output (per-recording details)
python scripts/benchmark_v2_with_baseline.py --verbose

# Show error analysis
python scripts/benchmark_v2_with_baseline.py --errors
```

### Test Data

| File | Description |
|------|-------------|
| `tests/recordings/*.expected.json` | Human-defined ground truth (15 files) |
| `test/fixtures/ground-truth.json` | MedGemma extraction results |
| `scripts/baseline_extractor.py` | Rule-based baseline implementation |
| `scripts/benchmark_v2_with_baseline.py` | Benchmark comparison script |

---

## Limitations

1. **Test corpus size:** 181 entities across 15 transcripts; larger corpus would narrow confidence intervals
2. **Single annotator:** Expected files created by one individual; inter-annotator agreement not measured
3. **Baseline simplicity:** Rule-based baseline uses common patterns only; more sophisticated NLP baselines (spaCy, clinical NER models) not tested
4. **MedGemma version:** Results specific to `google/medgemma-4b-it` model
5. **Orders weakness:** Both systems underperform on order detection (30% and 24% F1)

---

## Conclusion

MedGemma-based extraction demonstrates **meaningful accuracy improvements** over rule-based approaches, particularly for complex clinical entities requiring contextual understanding.

**Key findings:**
- **+11% F1 improvement** overall (66% vs 55%)
- **+22 point recall improvement** (66% vs 44%)
- **Complete failure of baseline** on allergies (0%) and family history (0%)
- **Baseline advantage** only on structured vital signs

**Honest assessment:** 66% F1 represents room for improvement. Future work should focus on:
- Order detection accuracy
- Expanding test corpus for tighter confidence intervals
- Comparing against clinical NER models (not just regex)

These results support deployment with appropriate **human-in-the-loop review** workflows.

---

**Benchmark script:** `scripts/benchmark_v2_with_baseline.py`
**Baseline extractor:** `scripts/baseline_extractor.py`
**Ground truth (expected):** `tests/recordings/*.expected.json`
**MedGemma output:** `test/fixtures/ground-truth.json`
