# Benchmark Methodology Review (Non-Clinical)

**Review Request:** 30-minute sanity check on ML testing methodology
**Reviewer Background Needed:** ML fundamentals, testing/QA experience
**NOT Needed:** Medical/clinical knowledge

---

## What We're Testing

An **information extraction system** that converts unstructured verbal reports into structured data.

**Analogy:** Like a system that listens to a pilot's flight report ("cruising at 35,000 feet, 450 knots, fuel at 60%") and extracts structured fields: `altitude=35000, speed=450, fuel_level=0.6`.

**Our domain:** Medical dictation → structured clinical data (diagnoses, medications, vital signs, etc.)

---

## Test Methodology

### Ground Truth Creation (Independence Check)

**Process:**
1. Human annotator writes 16 test scenarios (like test cases)
2. Annotator defines **expected outputs** in structured format BEFORE running AI
3. AI system processes test inputs (blind to expected outputs)
4. Compare AI output vs pre-defined expected output

**Critical question:** Does this avoid circular reasoning? Or could the annotator have biased expected outputs based on knowing what the AI would extract?

### Test Corpus

- **16 test cases** spanning different scenario types
- **199 data points** (extracted entities) across all test cases
- Each test case: 1-2 minute verbal report transcribed to text

**Question for you:** Is 199 data points adequate sample size for reported confidence intervals?

### Baseline Comparison

**Baseline system:** Rule-based regex pattern matching (traditional NLP)
- 50+ medication name patterns
- 25+ condition patterns
- Vital sign extraction (BP, heart rate, etc.)

**Hybrid system (ours):** AI model (google/medgemma-4b-it) + deterministic post-processing rules

**Question:** Is comparing ML against regex fair? Should we compare against other ML models (spaCy, BERT-based NER)?

---

## Metrics

**Standard ML classification metrics:**
- **Precision:** TP / (TP + FP)
- **Recall:** TP / (TP + FN)
- **F1 Score:** Harmonic mean of P and R

**Matching criteria:**
- Fuzzy string matching at **80% similarity threshold**
- Example: "hypertension" matches "high blood pressure" at 83% similarity

**Question:** Is 80% threshold arbitrary? How would we justify this choice?

### Statistical Significance

- **Confidence Intervals:** Wilson score interval at 95% confidence
- **Hybrid System CI:** 62.1% - 74.9% F1
- **Baseline CI:** 48.8% - 62.5% F1

**Question:** Are these confidence intervals calculated correctly for n=199? Minimal overlap suggests significance—do you agree?

---

## Key Results

| Metric | Hybrid System | Baseline | Delta |
|--------|--------------|----------|-------|
| **Precision** | 69% | 74% | -5pp |
| **Recall** | 69% | 45% | +24pp |
| **F1 Score** | 69% | 56% | +13pp |

**Interpretation:** Our system catches more true positives (higher recall) but makes slightly more false positive errors (lower precision). Net improvement: +13pp F1.

---

## Ablation Testing (Component Attribution)

**Method:** Compare AI-only output (Stage 1) vs AI + post-processing (Stage 4)

| Stage | Description | F1 Score | Delta |
|-------|-------------|----------|-------|
| Stage 1 | AI extraction only | 67% | — |
| Stage 4 | AI + rules + enrichment | 70% | +3pp |

**Finding:** AI contributes 67% F1 (96% of total accuracy), post-processing adds +3pp (4% of total).

**Question:** Does this ablation approach correctly attribute accuracy improvements to components? Any confounding factors?

---

## Error Source Analysis

Tested with **pristine input** (no transcription errors) vs **real-world transcription**:

| Input Type | F1 Score | Delta |
|------------|----------|-------|
| Real ASR transcription | 69% | — |
| Pristine (no errors) | 77% | +8pp |

**Interpretation:**
- 8pp lost to transcription errors (external factor)
- 23pp lost to extraction pipeline itself (our system's limitation)

**Question:** Is this decomposition valid? Are there interaction effects between transcription quality and extraction accuracy?

---

## Known Limitations (Self-Assessment)

1. **Single annotator** - No inter-rater reliability measured
2. **Small corpus** - 199 entities → wide confidence intervals
3. **Simplistic baseline** - Regex-only, not modern NLP (spaCy, BERT)
4. **Fuzzy threshold** - 80% similarity seems arbitrary
5. **API variability** - Repeated runs show ±1pp variation

---

## Specific Questions for Review

Please critique:

1. **Ground truth independence:** Does our process avoid circular reasoning? Could annotator bias exist?

2. **Sample size:** Is n=199 entities across 16 test cases adequate? What would you recommend?

3. **Baseline fairness:** Is regex comparison reasonable, or should we test against modern NLP baselines?

4. **Fuzzy matching:** How would you defend 80% similarity threshold? Seems arbitrary—alternatives?

5. **Confidence intervals:** Are Wilson score intervals appropriate here? Any calculation concerns?

6. **Ablation validity:** Does Stage 1 vs Stage 4 comparison correctly attribute improvements? Confounds?

7. **Reproducibility:** We provide test data and scripts—what else would you need to verify results?

8. **Obvious blind spots:** What methodology flaws are we missing?

---

## What Success Looks Like

**You validate:**
- Ground truth creation is independent ✓
- Sample size is defensible (if limited) ✓
- Confidence intervals calculated correctly ✓
- Ablation methodology sound ✓

**You identify concerns:**
- Single annotator → recommend inter-rater reliability test
- Fuzzy threshold → suggest systematic threshold sweep (70%, 75%, 80%, 85%)
- Small corpus → recommend power analysis for target n
- Baseline simplicity → compare against spaCy or clinical BERT

**Your critique helps us:**
- Strengthen methodology for peer review
- Identify critical weaknesses before submission
- Justify design choices with engineering rigor

---

**Full technical details:** See `BENCHMARKS.md` in repository (62 pages)

