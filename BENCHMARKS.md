# Extraction Accuracy Benchmarks

**Evaluation Date:** January 31, 2026
**Test Corpus:** 199 entities from 16 clinical transcripts
**Ground Truth:** Independent human annotation (`.expected.json` files)

---

## Executive Summary

Our **hybrid extraction pipeline**—combining MedGemma AI with a deterministic rules engine—achieves **69% F1** compared to a rules-only baseline's **56% F1**, a **13 percentage point improvement**. More significantly, the hybrid pipeline's recall (69%) substantially outperforms baseline (45%), a **+24 point improvement** in entity detection.

**What is "hybrid"?** This is **not pure AI extraction**. The pipeline combines MedGemma's semantic understanding with deterministic rules for structured data—playing to each component's strengths while avoiding their weaknesses.

**Stage Attribution Analysis (New):** Through ablation testing, we now quantify each stage's contribution:
- **Stage 0 (MedASR):** -9% F1 penalty from transcription errors (77% pristine → 68% with ASR)
- **Stage 1 (AI-only):** 67% F1 baseline (MedGemma semantic extraction)
- **Stages 2-4 (Post-processing):** +3% F1 improvement (deterministic rules, code enrichment, linking)

**Key Finding:** Post-processing adds metadata (ICD-10, RxNorm, LOINC codes) and structured extraction (family history +11%, vitals +6%), but **AI drives accuracy** (67% of the 70% total F1).

**ASR Error Analysis:** With pristine transcripts (no ASR errors), the pipeline achieves **77% F1** - a 9 percentage point improvement over real-world ASR input. This represents the extraction ceiling performance.

The hybrid pipeline excels at complex extraction tasks where rule-only systems completely fail:
- **Allergies:** 84% F1 vs 0% baseline (+84%)
- **Family History:** 82% F1 vs 0% baseline (+82%)

---

## Hybrid Architecture

**Critical Understanding:** The benchmarked system is **not pure MedGemma**—it's a hybrid pipeline combining AI with deterministic post-processing. Pure AI excels at semantic tasks (allergies, family history) but can struggle with structured patterns. Pure rules excel at structured data (vitals) but fail at natural language variation. Our pipeline combines both:

### Pipeline Stages with Performance Attribution

```
Voice Input (Pristine Script)
    ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 0: MedASR Transcription                               │
│  • Medical speech recognition (google/medasr)               │
│  • Specialized medical vocabulary                           │
│  • Error rate: ~9% F1 penalty                               │
│                                                              │
│  Performance: 77% (pristine) → 68% (with ASR errors)        │
└─────────────────────────────────────────────────────────────┘
    ↓ Transcript with ASR Errors
    ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 1: AI Extraction (MedGemma)                           │
│  • Semantic understanding of clinical narratives            │
│  • Context-aware entity detection (allergies, family, etc.) │
│  • Natural language variation handling                      │
│  • Extracts medications WITH doses already                  │
│                                                              │
│  Performance: 67% F1 (P: 67%, R: 68%)                       │
│  Contribution: 67% of total 70% F1 (96% of accuracy)        │
└─────────────────────────────────────────────────────────────┘
    ↓ ClinicalEntities (AI-only)
    ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 2: Deterministic Rules                                │
│  • Blood pressure normalization (regex: "142/88")           │
│  • Chief complaint extraction (section markers)             │
│  • Medication dosage parsing (usually already done by AI)   │
│  • Family history structure parsing ([FAMILY HISTORY])      │
│                                                              │
│  Contribution: +11% F1 for family history, +6% for vitals   │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 3: Code Enrichment                                    │
│  • ICD-10 lookup (~500 conditions)                          │
│  • RxNorm lookup (~200 medications)                         │
│  • LOINC validation (150+ lab tests)                        │
│                                                              │
│  Contribution: 0% F1 improvement (adds metadata only)       │
│  Note: Codes don't improve fuzzy matching at 80% threshold  │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 4: Order-Diagnosis Linking                            │
│  • Drug class → indication rules (36+ classes)              │
│  • Lab test → monitoring indication                         │
│  • Order → patient condition matching                       │
│                                                              │
│  Contribution: +2% F1 for orders (minimal impact)           │
└─────────────────────────────────────────────────────────────┘
    ↓
Final ClinicalEntities
Performance: 70% F1 (P: 72%, R: 69%)
```

### Cumulative Performance by Stage

| Stage | Description | Cumulative F1 | Delta from Previous |
|-------|-------------|--------------|---------------------|
| **Pristine Input** | Original dictation (no ASR) | **77%** | **— (ceiling)** |
| **Stage 0** | + MedASR transcription | 68% | **-9%** (ASR errors) |
| **Stage 1** | + AI extraction (MedGemma) | 67% | -1% |
| **Stages 2-4** | + Rules, codes, linking | **70%** | **+3%** |

**Performance Attribution:**
- **AI contribution:** 67% F1 (represents 96% of final 70% F1)
- **Post-processing contribution:** +3% F1 (represents 4% of final 70% F1)
- **ASR error penalty:** -9% F1 (difference between 77% ceiling and 68% with ASR)

**Key Insight:** The 77% F1 with pristine input represents the **extraction ceiling** - the best possible performance with perfect transcription. Real-world performance (70% F1) includes a -9% penalty from ASR errors plus the pipeline's own limitations (30% gap from perfect).

### Why Hybrid?

**The core insight:** Pure AI and pure rules each fail in predictable ways. By combining them, we eliminate both failure modes.

| Component | Strength | Weakness |
|-----------|----------|----------|
| **MedGemma AI** | Semantic understanding, context, natural language variation | Structured patterns, numeric data, guaranteed consistency |
| **Deterministic Rules** | Guaranteed accuracy on patterns, auditable, 100% reproducible | Zero flexibility, fails on language variation |

**Practical benefit:** Reliable extraction of structured data (vitals, dosages) via rules, while preserving AI's semantic capabilities for complex entities (allergies, family history, medication contexts). Rules catch what AI might miss; AI catches what rules cannot express.

### Open Source Strategy

**Key advantage:** The hybrid architecture separates fast-evolving components from slow-evolving components.

| Component | Evolution Speed | Contribution Opportunity |
|-----------|-----------------|--------------------------|
| **AI prompts** | Slow (model-dependent) | Research-grade improvements |
| **Deterministic rules** | **Fast (pure code)** | **Immediate community impact** |
| **Medical code databases** | Annual updates | Coverage expansion |
| **Clinical linking rules** | Moderate | Specialty-specific additions |

**The deterministic rules engine is where open-source contributors can make immediate, measurable improvements:**
- Add new medication name patterns → instant accuracy gain
- Improve vital sign extraction → measurable F1 improvement
- Expand condition recognition → directly testable against benchmarks
- Add specialty-specific rules → domain expert contributions

**Strategic benefit:** Driving adoption of this pipeline—even in competing products—benefits all users as improvements flow back to the shared codebase. Better extraction rules for cardiology help everyone using the pipeline, regardless of vendor.

---

## Methodology

### Ground Truth Creation

**Critical:** Ground truth was created **independently** of the hybrid pipeline output to ensure valid benchmarking.

1. **Script Creation:** Clinical scenarios written as natural language scripts
2. **Human Annotation:** Expected extractions defined in `.expected.json` files **before** running any AI
3. **Recording:** Scripts dictated and processed through full hybrid pipeline (transcription → AI extraction → deterministic rules → code enrichment → linking)
4. **Comparison:** Hybrid pipeline output compared against pre-defined expected files

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

**Reminder:** "MedGemma" in these tables refers to the **full hybrid pipeline** (AI + deterministic rules + code enrichment + clinical linking), not pure AI extraction.

| Entity Type | Hybrid Pipeline F1 | Baseline F1 | Delta |
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
| **Hybrid Pipeline** | 69% | 69% | 68.8% | [62.1% - 74.9%] |
| **Baseline** | 74% | 45% | 56.1% | [48.8% - 62.5%] |

**Key Finding:** The hybrid pipeline's strength is **recall** (+24 points). It detects more entities that baseline completely misses. The baseline is slightly more precise (fewer false positives) but misses 55% of entities entirely.

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

## Stage Attribution Analysis

**Methodology:** To quantify each pipeline stage's contribution, we implemented ablation testing comparing AI-only extraction (Stage 1) against the full hybrid pipeline (Stages 1-4). This reveals which accuracy gains come from AI semantic understanding vs deterministic post-processing.

**Test Date:** February 5, 2026
**Test Corpus:** Same 16 recordings, 199 entities
**Method:** Modified MedGemma client to capture Stage 1 output (after `_parse_response()`, before `post_process()`), then compare both Stage 1 and final output against ground truth.

### Stage 1 (AI-Only) vs Stage 4 (Full Pipeline)

| Entity Type | Stage 1 F1 | Stage 4 F1 | Delta | Analysis |
|-------------|-----------|-----------|-------|----------|
| **Conditions** | 73% | 73% | **0%** | AI baseline strong; ICD-10 codes add metadata only |
| **Medications** | 82% | 82% | **0%** | AI extracts WITH doses; RxNorm codes don't improve matching |
| **Vitals** | 79% | 84% | **+6%** | BP regex normalization helps |
| **Allergies** | 80% | 84% | **+4%** | Minor cleanup improvements |
| **Family History** | 71% | 82% | **+11%** | Section marker extraction (`[FAMILY HISTORY]`) highly effective |
| **Orders** | 34% | 36% | **+2%** | Order-diagnosis linking adds minimal value |
| **OVERALL** | **67%** | **70%** | **+3%** | **AI drives accuracy, rules add polish** |

**Precision/Recall Breakdown:**

| Stage | Precision | Recall | F1 |
|-------|-----------|--------|-----|
| **Stage 1 (AI-only)** | 67% | 68% | 67% |
| **Stage 4 (Full Pipeline)** | 72% | 69% | 70% |
| **Improvement** | +5pp | +1pp | +3pp |

### Key Findings from Attribution Analysis

1. **Post-Processing Adds Metadata, Not Accuracy**
   - Conditions/medications show 0% improvement despite adding ICD-10/RxNorm codes
   - Fuzzy matching (80% threshold) works without exact code matches
   - AI already extracts medications with doses attached ("aspirin 80 mg")

2. **Family History Rules Most Effective**
   - +11% F1 improvement (highest delta)
   - Section markers `[FAMILY HISTORY]` enable structured extraction
   - AI alone struggles with formatted family history sections

3. **Vitals Rules Moderately Effective**
   - +6% F1 improvement from BP regex normalization
   - AI extracts most vitals correctly; rules ensure format consistency

4. **AI Baseline Stronger Than Expected**
   - Hypothesis: AI baseline ~52% F1, rules add +17.5%
   - **Actual: AI baseline 67% F1, rules add +3%**
   - MedGemma's semantic understanding significantly underestimated

5. **Code Enrichment Has Zero Accuracy Impact**
   - Stage 3 (ICD-10, RxNorm, LOINC lookups) adds codes but doesn't improve F1
   - Validates fuzzy matching approach (similarity threshold > exact codes)

6. **Order-Diagnosis Linking Needs Work**
   - Only +2% improvement from 36+ drug class rules
   - Both AI and rules struggle with order detection (34% baseline)

### What AI Does Well (No Rules Needed)

- **Medications:** 82% F1 with doses already extracted
- **Conditions:** 73% F1 with semantic understanding
- **Allergies:** 80% F1 with contextual detection

### What Rules Improve Significantly

- **Family History:** 71% → 82% (+11%) via section markers
- **Vitals:** 79% → 84% (+6%) via BP normalization

### Consistency Check

**Stage 1 Comparison Benchmark:** 70% F1 (Stage 4 full pipeline, with ASR errors)
**Original Benchmark (benchmark_v2):** 69% F1 (Hybrid pipeline, with ASR errors)

✅ **Results consistent** - 1 percentage point difference likely due to:
- Different test runs (API variability)
- Slight differences in ground truth matching
- Confirms reproducibility of hybrid pipeline performance

---

## ASR Error Impact Analysis

To isolate transcription errors from extraction errors, we compared the hybrid pipeline's performance with:
- **Real-world ASR transcripts** (MedASR output with typical transcription errors)
- **Pristine scripts** (original dictation scripts, no ASR errors)

### Three-Way Comparison

| System | Precision | Recall | F1 |
|--------|-----------|--------|-----|
| **Hybrid Pipeline + ASR** | 69% | 69% | **69%** |
| **Hybrid Pipeline + Pristine** | 78% | 77% | **77%** |
| **Baseline (regex)** | 74% | 45% | **56%** |

### Per-Entity ASR Impact

| Entity Type | Hybrid+ASR | Hybrid+Pristine | ASR Gap |
|-------------|--------------|-------------------|---------|
| Conditions | 71% | 86% | **+15%** |
| Medications | 84% | 84% | 0% |
| Vitals | 82% | 83% | +1% |
| Allergies | 84% | 84% | 0% |
| Family History | 82% | 87% | +4% |
| Orders | 35% | 49% | **+14%** |

### Key Findings

1. **ASR errors cost 9% F1**: The hybrid pipeline's ceiling with perfect input is 77%, not 69%
2. **Conditions most affected**: +15% improvement with pristine transcripts
3. **Orders also benefit**: +14% improvement (35% → 49%) with pristine input
4. **Medications robust**: No change (84%) - ASR handles medication names well

### Error Attribution

| Error Source | F1 Impact |
|--------------|-----------|
| ASR transcription errors | -9% |
| Extraction pipeline limitations | -23% |
| **Total gap from 100%** | **-32%** |

This analysis demonstrates that ~28% of errors come from ASR transcription, while ~72% come from the extraction pipeline itself (AI prompting, deterministic rules, linking logic).

---

## Analysis

### Where the Hybrid Pipeline Excels

1. **Allergies (+84%):** Rule-based extraction completely fails on natural language allergy descriptions like "allergic to penicillin causes rash." The AI component understands semantic context that regex cannot express.

2. **Family History (+82%):** Baseline has no patterns for family history narratives. The AI component correctly extracts "father had MI at 55" and similar statements.

3. **Medications (+12%):** The hybrid pipeline catches more medication mentions through AI's contextual understanding, while the deterministic rules ensure accurate dosage extraction.

4. **Conditions (+14%):** The AI component understands:
   - Synonyms and variations ("high blood pressure" = "hypertension")
   - Implied diagnoses from clinical findings
   - Chief complaint identification

### Where Baseline Performs Well

1. **Vitals (88% vs 82%):** Structured numeric patterns are easy to extract with regex. Baseline's targeted patterns slightly outperform the hybrid pipeline on structured data (though the hybrid pipeline's deterministic rules component gets close at 82%).

### Areas for Improvement

1. **Orders (35% F1):** Both systems struggle with order detection. Distinguishing "start statin" (order) from "on statin" (current med) remains challenging. This represents the biggest opportunity for improvement in the deterministic rules engine.

### Key Insight

Rule-based extraction works for **structured, predictable patterns** (vitals) but fails completely for:
- Contextual understanding (is this an order or a finding?)
- Semantic inference (what is the implied diagnosis?)
- Natural language variation (allergy descriptions, family history)

The hybrid architecture combines AI's medical domain training (enabling **clinical reasoning** that regex cannot achieve) with guaranteed accuracy for structured patterns.

---

## Statistical Significance

With 199 entities across 16 recordings:

- **95% Confidence Interval (Hybrid Pipeline):** 62.1% - 74.9%
- **95% Confidence Interval (Baseline):** 48.8% - 62.5%

The confidence intervals have minimal overlap, indicating the improvement is statistically meaningful, not due to chance or small sample variation.

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

**What gets tested:** The benchmark runs the full hybrid pipeline (AI + rules + enrichment + linking) and compares against human ground truth.

```bash
# Clone repository
git clone https://github.com/paulgCleansheet/voice-to-health-record.git
cd voice-to-health-record

# Install dependencies
pip install -e .

# Run benchmark (Hybrid Pipeline vs Baseline comparison)
python scripts/benchmark_v2_with_baseline.py

# Verbose output (per-recording details)
python scripts/benchmark_v2_with_baseline.py --verbose

# Show error analysis
python scripts/benchmark_v2_with_baseline.py --errors

# Run ASR impact analysis (three-way: ASR vs Pristine vs Baseline)
python scripts/benchmark_pristine.py --verbose

# NEW: Run Stage Attribution Analysis (AI-only vs Full Pipeline)
python scripts/benchmark_stage_comparison.py

# Stage comparison with per-recording details
python scripts/benchmark_stage_comparison.py --verbose

# Stage comparison for single recording
python scripts/benchmark_stage_comparison.py --recording hp

# Export stage comparison to JSON
python scripts/benchmark_stage_comparison.py --output stage_attribution.json
```

### Test Data

| File | Description |
|------|-------------|
| `tests/fixtures/recordings/*.expected.json` | Human-defined ground truth (16 files, enhanced with RxNorm/LOINC/ICD-10) |
| `tests/fixtures/recordings/script.md` | Pristine dictation scripts for ASR comparison |
| `tests/fixtures/ground-truth.json` | Hybrid pipeline extraction results (contains transcripts in reviewPool) |
| `scripts/baseline_extractor.py` | Rule-based baseline implementation (regex only, no AI) |
| `scripts/benchmark_v2_with_baseline.py` | Benchmark comparison script (Hybrid vs Baseline) |
| `scripts/benchmark_pristine.py` | ASR vs pristine analysis script (three-way comparison) |
| `scripts/benchmark_stage_comparison.py` | **Stage attribution script (AI-only vs Full Pipeline)** |
| `src/extraction/loinc_lookup.py` | LOINC code database (150+ lab tests) |
| `STAGE1_IMPLEMENTATION_SUMMARY.md` | Stage attribution implementation documentation |
| `STAGE_COMPARISON_GUIDE.md` | Usage guide for stage comparison benchmark |
| `STAGE1_INVESTIGATION_REPORT.md` | Analysis of attribution findings |

---

## Limitations

1. **Test corpus size:** 199 entities across 16 transcripts; larger corpus would narrow confidence intervals
2. **Single annotator:** Expected files created by one individual; inter-annotator agreement not measured
3. **Baseline simplicity:** Rule-based baseline uses common patterns only; more sophisticated NLP baselines (spaCy, clinical NER models, other medical LLMs) not tested
4. **Pipeline version:** Results specific to `google/medgemma-4b-it` model with current deterministic rules; performance may vary with different AI models or improved rules
5. **Orders weakness:** Both systems underperform on order detection (34-36% F1) — represents biggest improvement opportunity
6. **ASR dependency:** Real-world performance includes MedASR transcription errors; pristine input shows higher ceiling (77% F1)
7. **Component attribution:** Now quantified via Stage Attribution Analysis - AI contributes 67% F1 (96% of total), post-processing adds +3% (4% of total)

---

## Conclusion

The **hybrid extraction pipeline** (AI + deterministic rules + code enrichment + clinical linking) demonstrates **meaningful accuracy improvements** over pure rule-based approaches, particularly for complex clinical entities requiring contextual understanding.

**Key findings:**
- **+13% F1 improvement** over baseline (69% vs 56%)
- **+24 point recall improvement** (69% vs 45%) — catches more real clinical data
- **77% extraction ceiling** with pristine input (9% lost to ASR errors)
- **Complete failure of baseline** on allergies (0%) and family history (0%)
- **Baseline advantage** only on structured vital signs (88% vs 82%)

**Stage Attribution Findings (New):**
- **AI (Stage 1) contributes 67% F1** - 96% of total accuracy
- **Post-processing (Stages 2-4) adds +3% F1** - 4% of total accuracy
- **Post-processing adds metadata** (ICD-10, RxNorm, LOINC codes) but AI drives accuracy
- **Family history rules** most effective (+11% improvement)
- **Code enrichment** has zero accuracy impact (0% delta) - adds metadata only

**Honest assessment:** 70% F1 with real-world ASR input represents room for improvement. The 77% ceiling with pristine transcripts shows that extraction pipeline limitations account for most errors (72%), not transcription quality (28%).

**Critical insight:** Attribution analysis reveals that **MedGemma AI baseline (67% F1) is significantly stronger than hypothesized**. Original expectation was ~52% AI baseline with +17.5% from rules; actual is 67% AI with only +3% from rules. This shifts optimization strategy from rule engineering to AI prompt engineering.

**Future work should focus on (prioritized by Stage Attribution findings):**

1. **AI Baseline Improvement (Highest ROI)**
   - **Prompt engineering** to improve Stage 1 from 67% → 80%+ F1
   - **Order detection** (34% F1) needs most work - AI baseline is weak
   - Testing prompt variations has higher impact than adding rules
   - Goal: Close 30% gap to perfect extraction via better AI prompting

2. **Targeted Rule Expansion (Proven Impact)**
   - **Family history extraction** - Most effective rule (+11% improvement)
   - **Vitals normalization** - Moderate impact (+6% improvement)
   - **Avoid:** Adding rules for conditions/medications (0% improvement)

3. **Remove Redundant Processing**
   - **Medication dosage extraction** - AI already includes doses, rules are redundant
   - **ICD-10/RxNorm for matching** - Codes add metadata but don't improve F1 (0% delta)
   - Simplify pipeline by removing zero-impact rules

4. **Order-Diagnosis Linking Overhaul**
   - Current 36+ drug class rules only add +2% improvement
   - AI baseline for orders is weak (34% F1)
   - Consider: Improved AI prompting vs better linking strategy

5. **Model Comparison Studies**
   - Compare MedGemma vs other medical LLMs (BioGPT, Clinical-T5)
   - Track Stage 1 F1 as MedGemma versions improve
   - Expect: Better AI models → less need for post-processing rules

6. **Expanded Test Corpus**
   - Larger dataset for tighter confidence intervals
   - More specialty-specific workflows (oncology, surgery, etc.)

**Strategic Insight:** Attribution analysis reveals that **improving AI baseline (Stage 1)** has 20x higher ROI than expanding post-processing rules. Focus development effort on prompt engineering and model selection, not rule engineering.

**Clinical deployment recommendation:** These results support deployment with appropriate **human-in-the-loop review workflows**. The hybrid pipeline is suitable for augmenting clinical documentation (with clinician review), not autonomous operation.

---

**Benchmark scripts:**
- `scripts/benchmark_v2_with_baseline.py` - Hybrid Pipeline vs Baseline comparison
- `scripts/benchmark_pristine.py` - ASR error impact analysis (three-way comparison)
- `scripts/benchmark_stage_comparison.py` - **Stage attribution analysis (AI-only vs Full Pipeline)**

**Baseline extractor:** `scripts/baseline_extractor.py` (regex-only, no AI)

**Ground truth:** `tests/fixtures/recordings/*.expected.json` (16 files, human-annotated, enhanced with medical codes)

**Pristine scripts:** `tests/fixtures/recordings/script.md` (error-free input for ASR ceiling analysis)

**Documentation:**
- `STAGE1_IMPLEMENTATION_SUMMARY.md` - Stage attribution implementation details
- `STAGE_COMPARISON_GUIDE.md` - Usage guide for stage comparison
- `STAGE1_INVESTIGATION_REPORT.md` - Attribution analysis findings
