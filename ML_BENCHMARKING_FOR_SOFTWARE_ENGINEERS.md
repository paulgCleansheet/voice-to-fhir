# ML Benchmarking for Software Engineers

**Target audience:** Software testers, QA engineers, materials testing professionals
**Purpose:** Bridge the gap between traditional testing and ML evaluation

---

## ⚠️ Critical Warning: This Is NOT Software Testing

If you're reading this with a software QA mindset, **stop and recalibrate**. ML benchmarking looks superficially similar to software testing but operates under fundamentally different assumptions. Applying traditional testing logic will lead to incorrect conclusions.

**Key mindset shift:** You're not testing if code is correct. You're measuring how well a probabilistic model approximates human judgment.

---

## Side-by-Side Comparison

| Concept | Software Testing | ML Benchmarking |
|---------|-----------------|-----------------|
| **Output determinism** | Same input → same output (always) | Same input → potentially different output (stochastic) |
| **Correctness** | Binary (correct/incorrect) | Continuous (69% F1 score) |
| **Success metric** | 100% pass rate expected | 60-90% F1 typical, 100% impossible |
| **Ground truth source** | Requirements specification (objective) | Annotation — human or AI-assisted (subjective) |
| **Test oracle** | Automated assertion (`assert x == y`) | Fuzzy comparison + human judgment |
| **Failure** | Bug to be fixed | Inherent task difficulty (some errors unavoidable) |
| **Test independence** | Doesn't matter if devs saw tests | **Critical:** Model must not train on test data |
| **Reproducibility** | Exact results every run | Approximate results (±1-2% variance normal) |
| **Metrics** | Pass/fail count, code coverage | Precision, recall, F1, confidence intervals |
| **Baseline** | Not required (spec is success) | **Required** (must beat baseline to show value) |
| **Error analysis** | Find root cause, fix bug | Categorize error types, improve model |

---

## What 69% Means in Different Contexts

### Software Testing: 69% Pass Rate
```
137 tests pass, 62 tests fail
→ FAILING GRADE
→ Block release, fix bugs
→ Goal: 100% pass rate
```

### ML Benchmarking: 69% F1 Score
```
Correctly extracted 69% of entities
→ ACCEPTABLE PERFORMANCE
→ May be state-of-the-art for task
→ Goal: Beat baseline, show improvement
```

**Critical insight:** In software, 69% means broken. In ML, 69% might mean success.

---

## The Precision-Recall Trade-off (Doesn't Exist in Software)

**Software analogy that DOESN'T exist:**
- You can't improve a sorting algorithm's "correctness" by sacrificing "completeness"
- A sort function either works or doesn't—no trade-off

**ML reality:**
```
System A: 95% precision, 40% recall (conservative, misses a lot)
System B: 60% precision, 90% recall (aggressive, many false positives)
System C: 69% precision, 69% recall (balanced)
```

**Which is "correct"?** Depends on use case:
- Medical diagnosis: Prefer high recall (don't miss diseases)
- Spam filter: Prefer high precision (don't flag real emails)

**In our benchmark:**
- Baseline: 74% precision, 45% recall (misses 55% of entities)
- Our system: 69% precision, 69% recall (catches more, slightly more false positives)

**Question for you:** Is this trade-off valid? Or should we optimize differently?

---

## Ground Truth Is Not a Specification

### Software Testing
```
Specification: "sort() returns ascending order"
Test: assert sort([3,1,2]) == [1,2,3]
✓ Definitive right answer
```

### ML Benchmarking
```
Dictation: "patient allergic to penicillin"
Expected extraction: {"allergy": "penicillin"}
AI extraction: {"allergy": "penicillin allergy"}

Is this correct? (strings don't match exactly)
→ Requires fuzzy matching (80% similarity)
→ Human judgment required
```

**Key difference:** Software specs are law. ML ground truth is human opinion, which can be:
- Subjective (two annotators disagree)
- Ambiguous (is "high blood pressure" same as "hypertension"?)
- Wrong (annotator makes mistakes)

**Our limitation:** AI-assisted annotation (Claude) from human-authored scripts, not SME-validated. No inter-rater reliability measured. Suitable for development benchmarking; relative comparisons (MedGemma vs. baseline) are the stronger claim.

**Question for you:** How would you validate ground truth quality without clinical expertise?

---

## Test Data Independence (Critical in ML, Irrelevant in Software)

### Software Testing
✓ Developers can write their own tests
✓ Test cases can be public during development
✓ No "cheating" risk—code either works or doesn't

### ML Benchmarking
❌ **Data leakage:** Model trained on test data → inflated scores → meaningless results
❌ **Circular reasoning:** Ground truth created after seeing model output → not independent
✅ **Our approach:** Ground truth derived from human-authored scripts using a separate AI model (Claude), independent of the extraction pipeline under test (MedGemma). Not self-referential, but also not SME-validated.

**Red flag scenario:**
1. Run AI on test data
2. Human reviews AI output
3. Human writes "expected output" that matches AI
4. Compare AI vs expected → 95% accuracy!
5. **Problem:** You compared AI to itself, not to independent truth

**Question for you:** How can you verify our ground truth wasn't influenced by AI output?

---

## Statistical Significance (Required in ML, Not in Software)

### Software Testing
- Deterministic: One test run proves correctness
- No need for confidence intervals
- Randomness is a bug, not a feature

### ML Benchmarking
- Probabilistic: Must report confidence intervals
- **Our results:** 69% F1 with 95% CI of [62% - 75%]
- Sample size matters: n=199 entities across 16 test cases

**Interpretation:**
- True performance likely between 62-75% with 95% confidence
- Wider intervals = less certainty (need more test data)
- Baseline CI [49% - 63%] barely overlaps → improvement is significant

**Question for you:** Are these confidence intervals calculated correctly for n=199? (We use Wilson score interval)

---

## Baseline Comparison (Required in ML, Not in Software)

### Software Testing
- Feature meets requirements? → Ship it
- No need to compare to "old way"

### ML Benchmarking
- **Must beat baseline** to demonstrate value
- Absolute performance means nothing without context

**Examples:**
- "69% F1" → Is this good? Can't tell.
- "69% F1 vs 30% baseline" → +39pp improvement → Excellent!
- "69% F1 vs 90% baseline" → -21pp regression → Terrible!

**Our benchmark:**
- Hybrid system: 69% F1
- Regex baseline: 56% F1
- **Improvement: +13pp** → Meaningful gain

**Question for you:** Is regex a fair baseline? Should we compare against modern NLP (spaCy, BERT)?

---

## What TO Apply from Software Testing

These principles **DO** transfer from software testing:

✅ **Test independence** → Ground truth must be independent of system output
✅ **Reproducibility** → Provide test data, scripts, and detailed methodology
✅ **Edge cases** → Test on diverse scenarios (simple → complex cases)
✅ **Regression testing** → Ablation testing (which components contribute?)
✅ **Documentation** → Clear methodology, limitations, and assumptions
✅ **Error analysis** → Categorize failure modes, identify patterns
✅ **Honest reporting** → Report limitations and negative results

---

## What NOT to Apply from Software Testing

These principles **DO NOT** transfer:

❌ **"Why only 69% pass rate?"** → F1 score ≠ pass rate. 69% F1 is acceptable.
❌ **"Fix bugs until 100%"** → Some errors are inherent to task difficulty, not fixable.
❌ **"Exact string matching"** → NLP requires fuzzy matching (80% similarity).
❌ **"Deterministic results"** → LLMs are probabilistic, ±1-2% variance is normal.
❌ **"One test run proves it"** → Need multiple runs + confidence intervals.
❌ **"Binary pass/fail"** → Continuous metrics (precision, recall, F1).

---

## Quick Reference: Interpreting ML Metrics

### Precision
**Definition:** Of everything the system extracted, what percentage was correct?
**Formula:** TP / (TP + FP)
**Software analogy:** How many of your "bug reports" are real bugs? (vs false alarms)

### Recall
**Definition:** Of everything that should be extracted, what percentage did we find?
**Formula:** TP / (TP + FN)
**Software analogy:** How many real bugs did your test suite catch? (vs missed bugs)

### F1 Score
**Definition:** Harmonic mean of precision and recall (balanced metric)
**Formula:** 2 × (Precision × Recall) / (Precision + Recall)
**Interpretation:** Single number summarizing overall performance

### Example from Our Benchmark
| System | Precision | Recall | F1 | Interpretation |
|--------|-----------|--------|-----|----------------|
| Baseline | 74% | 45% | 56% | Conservative (few false positives, misses a lot) |
| Ours | 69% | 69% | 69% | Balanced (catches more, slightly more errors) |

**Trade-off:** We sacrifice 5pp precision to gain 24pp recall → Net +13pp F1 improvement.

---

## Your Review Checklist

**Validate these (from software testing mindset):**
- [ ] Ground truth created independently of system output? (No circular reasoning?)
- [ ] Test data diverse enough? (16 scenarios cover real-world cases?)
- [ ] Methodology documented clearly? (Can someone else reproduce?)
- [ ] Limitations reported honestly? (Single annotator, small corpus acknowledged?)
- [ ] Baseline comparison fair? (Regex vs AI—is this apples to apples?)

**Don't evaluate these (different framework):**
- [ ] ~~Why isn't F1 score 100%?~~ (Impossible for subjective tasks)
- [ ] ~~Why fuzzy matching instead of exact?~~ (NLP requires flexibility)
- [ ] ~~Why not deterministic results?~~ (LLMs are inherently probabilistic)

---

## Specific Questions for You

1. **Sample size:** Is n=199 entities across 16 test cases adequate for 95% CI of [62%-75%]?

2. **Ground truth independence:** We claim annotator wrote expected outputs BEFORE running AI. How would you verify this claim? What evidence would convince you?

3. **Fuzzy matching threshold:** 80% string similarity for matching. How would you justify or challenge this choice?

4. **Baseline fairness:** We compare ML system against regex. Is this fair, or should we test against modern NLP baselines (spaCy, BERT)?

5. **Confidence intervals:** We use Wilson score interval. Is this appropriate for n=199, or should we use bootstrap/permutation testing?

6. **Inter-rater reliability:** We used single annotator (acknowledged limitation). How critical is this? What would you recommend?

7. **Test-retest reliability:** Repeated runs show ±1pp variation. Is this acceptable, or does it indicate instability?

8. **Generalization:** 16 test scenarios—does this represent real-world distribution, or is it cherry-picked?

---

## Bottom Line

**If you approach this like software testing, you'll conclude:**
- "69% pass rate = failing grade"
- "Fix bugs until 100% pass"
- "Results not deterministic = system is broken"

**If you approach this like ML benchmarking, you'll conclude:**
- "69% F1 = respectable performance for NLP task"
- "+13pp over baseline = meaningful improvement"
- "±1pp variance = normal for probabilistic system"

**We need you to do the second one, not the first.**

Your engineering rigor is valuable—apply it to:
- Ground truth independence
- Sample size adequacy
- Statistical validity
- Baseline fairness
- Methodology transparency

But don't apply software testing pass/fail logic to ML performance metrics.

---

**Questions?** Happy to clarify any of these distinctions before you dive into the full methodology review.
