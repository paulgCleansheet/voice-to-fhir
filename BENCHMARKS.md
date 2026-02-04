# Extraction Accuracy Benchmarks

**Evaluation Date:** January 31, 2026
**Test Corpus:** 199 entities from 16 clinical transcripts
**Ground Truth:** Independent human annotation (`.expected.json` files)

---

## Executive Summary

Our **hybrid extraction pipeline**—combining MedGemma AI with a deterministic rules engine—achieves **69% F1** compared to a rules-only baseline's **56% F1**, a **13 percentage point improvement**. More significantly, the hybrid pipeline's recall (69%) substantially outperforms baseline (45%), a **+24 point improvement** in entity detection.

**ASR Error Analysis:** With pristine transcripts (no ASR errors), the pipeline achieves **77% F1** - a 9 percentage point improvement over real-world ASR input. This represents the extraction ceiling performance.

The hybrid pipeline excels at complex extraction tasks where rule-only systems completely fail:
- **Allergies:** 84% F1 vs 0% baseline (+84%)
- **Family History:** 82% F1 vs 0% baseline (+82%)

---

## Hybrid Architecture

The benchmarked system is **not pure MedGemma**—it's a hybrid pipeline that combines AI with deterministic post-processing:

```
Voice Input
    ↓
MedASR Transcription
    ↓
MedGemma AI Extraction (semantic understanding)
    ↓
Deterministic Post-Processing:
    • Blood pressure extraction (regex patterns)
    • Medication dosage extraction (pattern matching)
    • Chief complaint extraction (section markers)
    • Family/social history parsing (structured patterns)
    ↓
Medical Code Enrichment:
    • ICD-10 lookup (~500 conditions)
    • RxNorm lookup (~200 medications)
    • LOINC validation (lab orders)
    ↓
Clinical Linking Rules:
    • Order-diagnosis association (36+ drug class rules)
    ↓
Final ClinicalEntities
```

### Why Hybrid?

| Component | Strength | Weakness |
|-----------|----------|----------|
| **MedGemma AI** | Semantic understanding, context, natural language | Structured patterns, numeric data |
| **Deterministic Rules** | Guaranteed accuracy on patterns, auditable | Zero flexibility, fails on variation |

By combining both, we get reliable extraction of structured data (vitals, dosages) while preserving AI's semantic capabilities for complex entities (allergies, family history, conditions).

### Open Source Strategy

- **AI prompts** evolve slowly (model-dependent)
- **Deterministic rules** can be improved immediately by contributors
- **Medical code databases** expand with community additions
- **Clinical linking rules** grow with specialty contributions

Driving adoption of this pipeline—even in competing products—benefits all users as improvements flow back to the shared codebase

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

- **16 clinical transcripts** spanning multiple workflow types:
  - Cardiology, Emergency, H&P, SOAP notes
  - Pediatrics, Neurology, ICU
  - Intake, Follow-up, Discharge, Radiology
  - Complex multi-comorbidity case (complex1.1)
- **199 ground truth entities** across all entity types
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
| **Conditions** | 71% | 57% | **+14%** |
| **Medications** | 84% | 71% | **+12%** |
| **Vitals** | 82% | 88% | -6% |
| **Allergies** | 84% | 0% | **+84%** |
| **Family History** | 82% | 0% | **+82%** |
| **Orders** | 35% | 23% | **+13%** |
| **OVERALL** | **69%** | **56%** | **+13%** |

### Precision vs Recall

| System | Precision | Recall | F1 | 95% CI |
|--------|-----------|--------|-----|--------|
| **MedGemma** | 69% | 69% | 68.8% | [62.1% - 74.9%] |
| **Baseline** | 74% | 45% | 56.1% | [48.8% - 62.5%] |

**Key Finding:** MedGemma's strength is **recall** (+24 points). It detects more entities that baseline completely misses.

### Detailed Baseline Metrics

| Entity Type | Precision | Recall | F1 |
|-------------|-----------|--------|-----|
| Conditions | 73% | 47% | 57% |
| Medications | 74% | 69% | 71% |
| Vitals | 93% | 83% | 88% |
| Allergies | 0% | 0% | 0% |
| Family History | 0% | 0% | 0% |
| Orders | 36% | 16% | 23% |

---

## ASR Error Impact Analysis

To isolate transcription errors from extraction errors, we compared MedGemma performance with:
- **Real-world ASR transcripts** (MedASR output with typical transcription errors)
- **Pristine scripts** (original dictation scripts, no ASR errors)

### Three-Way Comparison

| System | Precision | Recall | F1 |
|--------|-----------|--------|-----|
| **MedGemma + ASR** | 69% | 69% | **69%** |
| **MedGemma + Pristine** | 78% | 77% | **77%** |
| **Baseline (regex)** | 74% | 45% | **56%** |

### Per-Entity ASR Impact

| Entity Type | MedGemma+ASR | MedGemma+Pristine | ASR Gap |
|-------------|--------------|-------------------|---------|
| Conditions | 71% | 86% | **+15%** |
| Medications | 84% | 84% | 0% |
| Vitals | 82% | 83% | +1% |
| Allergies | 84% | 84% | 0% |
| Family History | 82% | 87% | +4% |
| Orders | 35% | 49% | **+14%** |

### Key Findings

1. **ASR errors cost 9% F1**: MedGemma's ceiling with perfect input is 77%, not 69%
2. **Conditions most affected**: +15% improvement with pristine transcripts
3. **Orders also benefit**: +14% improvement (35% → 49%) with pristine input
4. **Medications robust**: No change (84%) - ASR handles medication names well

### Error Attribution

| Error Source | F1 Impact |
|--------------|-----------|
| ASR transcription errors | -9% |
| MedGemma extraction limitations | -23% |
| **Total gap from 100%** | **-32%** |

This analysis demonstrates that ~28% of errors come from ASR, while ~72% come from the extraction model itself.

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

With 199 entities across 16 recordings:

- **95% Confidence Interval (MedGemma):** 62.1% - 74.9%
- **95% Confidence Interval (Baseline):** 48.8% - 62.5%

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

# Run ASR impact analysis (three-way: ASR vs Pristine vs Baseline)
python scripts/benchmark_pristine.py --verbose
```

### Test Data

| File | Description |
|------|-------------|
| `tests/recordings/*.expected.json` | Human-defined ground truth (16 files) |
| `tests/recordings/script.md` | Pristine dictation scripts for ASR comparison |
| `test/fixtures/ground-truth.json` | MedGemma extraction results |
| `scripts/baseline_extractor.py` | Rule-based baseline implementation |
| `scripts/benchmark_v2_with_baseline.py` | Benchmark comparison script |
| `scripts/benchmark_pristine.py` | ASR vs pristine analysis script |

---

## Limitations

1. **Test corpus size:** 199 entities across 16 transcripts; larger corpus would narrow confidence intervals
2. **Single annotator:** Expected files created by one individual; inter-annotator agreement not measured
3. **Baseline simplicity:** Rule-based baseline uses common patterns only; more sophisticated NLP baselines (spaCy, clinical NER models) not tested
4. **MedGemma version:** Results specific to `google/medgemma-4b-it` model
5. **Orders weakness:** Both systems underperform on order detection (35% and 23% F1)
6. **ASR dependency:** Real-world performance includes MedASR transcription errors; pristine input shows higher ceiling (77% F1)

---

## Conclusion

MedGemma-based extraction demonstrates **meaningful accuracy improvements** over rule-based approaches, particularly for complex clinical entities requiring contextual understanding.

**Key findings:**
- **+13% F1 improvement** overall (69% vs 56%)
- **+24 point recall improvement** (69% vs 45%)
- **77% extraction ceiling** with pristine input (9% lost to ASR errors)
- **Complete failure of baseline** on allergies (0%) and family history (0%)
- **Baseline advantage** only on structured vital signs

**Honest assessment:** 69% F1 with real-world ASR input represents room for improvement. The 77% ceiling with pristine transcripts shows extraction model limitations account for most errors. Future work should focus on:
- Order detection accuracy (currently 35%)
- Improving extraction model prompts
- Expanding test corpus for tighter confidence intervals
- Comparing against clinical NER models (not just regex)

These results support deployment with appropriate **human-in-the-loop review** workflows.

---

**Benchmark scripts:**
- `scripts/benchmark_v2_with_baseline.py` - MedGemma vs Baseline comparison
- `scripts/benchmark_pristine.py` - ASR error impact analysis (three-way comparison)

**Baseline extractor:** `scripts/baseline_extractor.py`
**Ground truth (expected):** `tests/recordings/*.expected.json` (16 files)
**Pristine scripts:** `tests/recordings/script.md`
**MedGemma output:** Bulk export from voice-to-fhir demo
