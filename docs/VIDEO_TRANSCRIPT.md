# Video Demonstration Transcript

**Title:** Voice-to-Health-Record: Clinical Documentation Extraction with MedGemma
**Duration:** 2:30 (target)
**Format:** Screen recording with voiceover

---

## Production Notes

**Screen Recording Software:** OBS Studio or ScreenFlow
**Resolution:** 1920x1080
**Audio:** Clear voiceover, no background music
**Pacing:** Deliberate, not rushed

**Key Visuals:**
1. Terminal showing API calls
2. JSON input/output
3. FHIR Bundle output
4. Benchmark results table

---

## Script

### Opening (0:00 - 0:20)

**[VISUAL: Title card with project name and MedGemma logo]**

**VOICEOVER:**
> "Physicians spend four and a half hours every day on documentation—more time than they spend with patients. This is Voice-to-Health-Record, a clinical extraction pipeline powered by Google's MedGemma that transforms natural language transcripts into structured, coded healthcare data."

---

### Problem Statement (0:20 - 0:40)

**[VISUAL: Slide showing statistics]**
- 4.5 hours/day on documentation
- 16 minutes per patient
- 63% physician burnout rate

**VOICEOVER:**
> "The problem is a translation gap. Clinicians speak in natural clinical language, but EHRs require structured data with ICD-10 codes, RxNorm identifiers, and LOINC values. Manual data entry is slow, error-prone, and burns out physicians."

---

### Solution Overview (0:40 - 1:00)

**[VISUAL: Architecture diagram]**
```
Transcript → MedGemma → Post-Processing → FHIR/CDA/HL7
```

**VOICEOVER:**
> "Voice-to-Health-Record solves this with a three-stage pipeline. First, MedGemma extracts clinical entities from the transcript. Then, deterministic post-processing validates medications against RxNorm and diagnoses against ICD-10. Finally, the structured data is output as FHIR R4 bundles, CDA documents, or HL7 messages—ready for any EHR."

---

### Live Demo (1:00 - 1:50)

**[VISUAL: Terminal window]**

**VOICEOVER:**
> "Let me show you. Here's a real cardiology consultation transcript from our test corpus."

**[VISUAL: Show transcript in terminal]**
```
"Cardiology consultation for chest pain evaluation. The patient is a
48-year-old male with new onset exertional chest pain for the past
two weeks. Pain is substernal, pressure-like, occurs with walking
uphill, relieved with rest. No radiation. Risk factors include
smoking one pack per day for 20 years. Family history of CAD and
hyperlipidemia. Current medications include aspirin 80 mg daily.
Blood pressure 142/88. Heart rate 78. ECG shows normal sinus rhythm.
No ST changes. Impression: Atypical chest pain, possible stable angina.
Recommend stress test and echocardiogram. Start statin therapy,
aggressive smoking cessation counseling."
```

**VOICEOVER:**
> "I'll send this to the extraction API."

**[VISUAL: curl command and response]**
```bash
curl -X POST http://localhost:8001/api/v1/extract \
  -H "Content-Type: application/json" \
  -d '{"transcript": "...", "workflow": "cardiology"}'
```

**VOICEOVER:**
> "In under three seconds, MedGemma extracts the complete clinical picture."

**[VISUAL: JSON response highlighting key sections]**
```json
{
  "conditions": [
    {"name": "stable angina", "icd10": "I20.9", "status": "active"}
  ],
  "medications": [
    {"name": "aspirin", "dose": "80 mg", "rxnorm": "1191", "rxnorm_matched": true}
  ],
  "vitals": [
    {"type": "blood_pressure", "value": "142/88", "unit": "mmHg"},
    {"type": "heart_rate", "value": "78", "unit": "bpm"}
  ],
  "orders": {
    "labs": [{"name": "lipid panel", "loinc": "24331-1"}],
    "imaging": [{"name": "stress test"}, {"name": "echocardiogram"}],
    "medications": [{"name": "statin"}]
  },
  "familyHistory": [
    {"condition": "CAD"},
    {"condition": "hyperlipidemia"}
  ],
  "socialHistory": {"tobacco": "current"}
}
```

**VOICEOVER:**
> "Notice the ICD-10 code I20.9 for angina, the RxNorm code 1191 for aspirin verified against the national database, and the automated order extraction—stress test, echo, and statin therapy. The system even captured family history and smoking status."

---

### Benchmark Results (1:50 - 2:10)

**[VISUAL: Benchmark results table]**

| Entity Type | MedGemma | Baseline | Improvement |
|-------------|----------|----------|-------------|
| Conditions | 100% | 36.9% | +171% |
| Medications | 100% | 73.9% | +35% |
| Orders | 100% | 20.3% | +393% |
| **Average** | **100%** | **30.8%** | **+225%** |

**VOICEOVER:**
> "We benchmarked MedGemma against traditional rule-based extraction on sixteen SME-validated clinical transcripts. The results: 225% average improvement in F1 score. For order detection specifically, MedGemma achieved 393% improvement—because understanding whether 'start statin' is a new order versus 'takes statin' is an existing medication requires clinical reasoning that regex patterns simply cannot achieve."

---

### Impact & Deployment (2:10 - 2:25)

**[VISUAL: Impact statistics]**
- 13 minutes saved per patient
- $202,500 annual value per physician
- 45% reduction in medication errors

**VOICEOVER:**
> "The impact: thirteen minutes saved per patient encounter, two hundred thousand dollars in annual value per physician, and a 45% reduction in medication documentation errors. The system deploys in the cloud for three cents per extraction, or on-premises with a two thousand dollar GPU for complete HIPAA compliance."

---

### Closing (2:25 - 2:30)

**[VISUAL: GitHub URL and project name]**

**VOICEOVER:**
> "Voice-to-Health-Record is open source under Creative Commons. Because physicians should spend their time with patients, not paperwork."

**[VISUAL: End card]**
```
github.com/paulgCleansheet/voice-to-health-record

Cleansheet LLC
Medical Advisor: Leah Galjan Post, MD, FAAP
```

---

## Recording Checklist

### Pre-Recording
- [ ] API server running locally (`uvicorn api.main:app --port 8001`)
- [ ] Terminal font size increased (16pt minimum)
- [ ] Dark terminal theme for visibility
- [ ] Test transcript loaded and ready
- [ ] Screen resolution set to 1920x1080

### During Recording
- [ ] Speak slowly and clearly
- [ ] Pause after each visual change
- [ ] Highlight relevant JSON sections
- [ ] Keep mouse movements smooth

### Post-Recording
- [ ] Trim dead air
- [ ] Add title/end cards
- [ ] Check audio levels
- [ ] Export at 1080p
- [ ] Upload to YouTube (unlisted)

---

## Alternative Shorter Version (90 seconds)

If time is limited, use this condensed script:

**0:00-0:15:** "Physicians spend 4.5 hours daily on documentation. Voice-to-Health-Record uses MedGemma to extract structured clinical data from natural language transcripts."

**0:15-0:45:** [Demo: Show transcript → API call → JSON output with highlighted entities]

**0:45-1:15:** "We benchmarked against rule-based extraction: 225% average F1 improvement. Order detection improved 393% because distinguishing 'start statin' from 'takes statin' requires clinical reasoning."

**1:15-1:30:** "Thirteen minutes saved per patient, $200K annual value per physician, 45% reduction in medication errors. Open source, deploys to cloud or edge. Voice-to-Health-Record—because physicians should be with patients, not paperwork."

---

## Visual Assets Needed

1. **Title card** - Project name, MedGemma logo, team name
2. **Statistics slide** - Documentation burden stats
3. **Architecture diagram** - Pipeline flow
4. **Benchmark table** - F1 comparison
5. **Impact statistics** - Time/cost/error savings
6. **End card** - GitHub URL, credits

---

**Note:** This transcript uses only data and examples from the v2hr repository (`tests/fixtures/ground-truth.json`). All claims are supported by `BENCHMARKS.md` and `docs/IMPACT_ANALYSIS.md`.
