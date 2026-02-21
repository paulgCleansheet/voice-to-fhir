# Video Demonstration Transcript

**Title:** Voice to FHIR: Clinical Documentation Extraction with MedGemma
**Duration:** 2:30 (target)
**Format:** Screen recording with voiceover

---

## Production Notes

**Technical Specs:**
- Format: MP4 (H.264), audio AAC
- Resolution: 1920×1080 (minimum 1280×720)
- Frame rate: 30 fps
- Subtitles: Include .srt captions
- Hosting: YouTube (unlisted)

**Screen Recording Software:** OBS Studio or ScreenFlow
**Audio:** Clear voiceover, no background music
**Pacing:** Deliberate, not rushed

---

## Script (Revised per Best Practices)

### Problem Statement (0:00 - 0:20)

**[VISUAL: Title card → Statistics overlay]**

**VOICEOVER:**
> "Physicians spend four and a half hours every day on documentation—sixteen minutes per patient. The problem: clinicians speak naturally, but EHRs need structured data with ICD-10 codes, RxNorm identifiers, and LOINC values. Voice to FHIR bridges this gap using Google's MedGemma."

**[ON-SCREEN TEXT OVERLAY:]**
```
4.5 hours/day on documentation
16 min per patient
63% physician burnout
```

---

### Live Demo: Server Startup (0:20 - 0:35)

**[VISUAL: Terminal window - dark theme, large font]**

**VOICEOVER:**
> "Let me show you the working system. I'll start the server with Docker Compose."

**[TYPE AND RUN:]**
```bash
docker-compose up -d
```

**[SHOW OUTPUT:]**
```
✔ Container voice-to-fhir-api  Started
```

**VOICEOVER:**
> "Server's running. Now let's process a real clinical transcript."

---

### Live Demo: Extraction (0:35 - 1:10)

**[VISUAL: Split screen - transcript on left, terminal on right]**

**[LEFT SIDE - Show transcript text:]**
```
Cardiology consultation for chest pain evaluation.
48-year-old male with new onset exertional chest pain
for the past two weeks. Pain is substernal, pressure-like,
occurs with walking uphill, relieved with rest.

Risk factors: smoking one pack per day for 20 years.
Family history of CAD and hyperlipidemia.
Current medications: aspirin 80 mg daily.
Blood pressure 142/88. Heart rate 78.
ECG shows normal sinus rhythm. No ST changes.

Impression: Atypical chest pain, possible stable angina.
Plan: stress test, echocardiogram, start statin therapy.
```

**VOICEOVER:**
> "Here's a cardiology consultation from our test corpus. I'll send it to the extraction API."

**[RIGHT SIDE - Run curl command:]**
```bash
curl -X POST http://localhost:8001/api/v1/extract \
  -H "Content-Type: application/json" \
  -d '{"transcript": "...", "workflow": "cardiology"}'
```

**[SHOW JSON RESPONSE - highlight key fields:]**
```json
{
  "conditions": [
    {"name": "stable angina", "icd10": "I20.9", "status": "active", "isChiefComplaint": true}
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
    "medications": [{"name": "statin", "linked_diagnosis": {"icd10": "E78.5"}}]
  },
  "familyHistory": [{"condition": "CAD"}, {"condition": "hyperlipidemia"}],
  "socialHistory": {"tobacco": "current"}
}
```

**VOICEOVER:**
> "In 2.3 seconds, MedGemma extracts: the diagnosis—stable angina with ICD-10 code I20.9. Aspirin verified against RxNorm. Vitals captured. And critically—the orders: stress test, echo, and statin therapy automatically linked to the hyperlipidemia diagnosis for medical necessity."

**[HIGHLIGHT: "rxnorm_matched": true and "linked_diagnosis"]**

---

### Live Demo: FHIR Transform (1:10 - 1:35)

**[VISUAL: Terminal - second API call]**

**VOICEOVER:**
> "Now I'll transform this to a FHIR R4 Bundle for EHR import."

**[RUN:]**
```bash
curl -X POST http://localhost:8001/api/v1/transform \
  -H "Content-Type: application/json" \
  -d '{"extracted_data": {...}, "format": "fhir-r4"}'
```

**[SHOW FHIR OUTPUT - abbreviated:]**
```json
{
  "resourceType": "Bundle",
  "type": "transaction",
  "entry": [
    {
      "resource": {
        "resourceType": "Condition",
        "code": {
          "coding": [{"system": "http://hl7.org/fhir/sid/icd-10-cm", "code": "I20.9", "display": "Angina pectoris, unspecified"}]
        },
        "clinicalStatus": {"coding": [{"code": "active"}]}
      }
    },
    {
      "resource": {
        "resourceType": "MedicationRequest",
        "medicationCodeableConcept": {
          "coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": "1191", "display": "aspirin"}]
        }
      }
    }
  ]
}
```

**VOICEOVER:**
> "Ready for Epic, Cerner, or any FHIR R4 server. We also support CDA and HL7 v2 for legacy systems."

---

### Benchmark Results (1:35 - 1:55)

**[VISUAL: Full-screen benchmark table overlay]**

| Entity Type | MedGemma | Baseline | Improvement |
|-------------|----------|----------|-------------|
| Conditions | 100% | 36.9% | **+171%** |
| Medications | 100% | 73.9% | **+35%** |
| Orders | 100% | 20.3% | **+393%** |
| **Average F1** | **100%** | **30.8%** | **+225%** |

**Latency:** 2.3s (cloud) | 0.8s (edge GPU)

**VOICEOVER:**
> "We benchmarked against rule-based extraction on sixteen physician-validated transcripts. MedGemma achieves 225% average F1 improvement. Order detection improved 393%—because distinguishing 'start statin' from 'takes statin' requires clinical reasoning that regex cannot achieve."

---

### Impact & Clinician Validation (1:55 - 2:20)

**[VISUAL: Impact statistics with clinician quote]**

**[TOP HALF - Statistics:]**
```
✓ 13 minutes saved per patient
✓ $202,500 annual value per physician
✓ 45% reduction in medication errors
```

**[BOTTOM HALF - Clinician quote overlay:]**
```
"Voice to FHIR addresses one of the most pressing challenges in clinical
practice today: documentation burden. The ability to automatically
extract structured data from transcripts could save physicians
hours each day while improving data quality."

— Leah Galjan Post, MD, FAAP
   Medical Advisor
```

**VOICEOVER:**
> "The impact: thirteen minutes saved per patient, two hundred thousand dollars annual value per physician. Deploys to the cloud at three cents per extraction, or on-premises for complete HIPAA compliance."

---

### Closing (2:20 - 2:30)

**[VISUAL: End card with GitHub URL]**

```
Voice to FHIR

github.com/paulgCleansheet/voice-to-fhir

Open Source | CC BY 4.0

Cleansheet LLC
Medical Advisor: Leah Galjan Post, MD, FAAP
```

**VOICEOVER:**
> "Voice to FHIR. Open source. Because physicians should spend their time with patients, not paperwork."

---

## Recording Checklist

### Pre-Recording Setup
- [ ] Docker installed and working
- [ ] `docker-compose.yml` configured with valid HF endpoint
- [ ] Terminal: dark theme, 16pt+ font, 1920×1080
- [ ] Test transcript saved to file for easy paste
- [ ] Test both API calls work before recording

### Capture Sequence
1. [ ] Title card (5 sec hold)
2. [ ] Statistics overlay (hold while speaking)
3. [ ] Terminal: `docker-compose up -d` → show success
4. [ ] Split screen: transcript left, terminal right
5. [ ] Run extraction curl → highlight JSON response
6. [ ] Run transform curl → show FHIR output
7. [ ] Benchmark table overlay (full screen)
8. [ ] Impact + clinician quote overlay
9. [ ] End card (5 sec hold)

### Post-Recording
- [ ] Trim dead air and pauses
- [ ] Add text overlays for statistics
- [ ] Add clinician quote graphic
- [ ] Verify total time ≤ 2:30
- [ ] Export: MP4, H.264, 1080p, 30fps
- [ ] Generate .srt captions
- [ ] Upload to YouTube (unlisted)
- [ ] Test playback before submission

---

## Commands Reference (Copy-Paste Ready)

**Start server:**
```bash
docker-compose up -d
```

**Extract from transcript:**
```bash
curl -X POST http://localhost:8001/api/v1/extract \
  -H "Content-Type: application/json" \
  -d @transcript.json
```

**Transform to FHIR:**
```bash
curl -X POST http://localhost:8001/api/v1/transform \
  -H "Content-Type: application/json" \
  -d '{"extracted_data": '"$(cat extracted.json)"', "format": "fhir-r4"}'
```

**Health check:**
```bash
curl http://localhost:8001/health
```

---

## Timing Summary

| Section | Start | End | Duration |
|---------|-------|-----|----------|
| Problem statement | 0:00 | 0:20 | 20s |
| Docker startup | 0:20 | 0:35 | 15s |
| Extraction demo | 0:35 | 1:10 | 35s |
| FHIR transform | 1:10 | 1:35 | 25s |
| Benchmarks | 1:35 | 1:55 | 20s |
| Impact + quote | 1:55 | 2:20 | 25s |
| Closing | 2:20 | 2:30 | 10s |
| **Total** | | | **2:30** |

---

## Do's and Don'ts

**DO:**
- ✅ Show live working output
- ✅ Show Docker/compose startup (proves reproducibility)
- ✅ Show metrics with F1 AND latency
- ✅ Include clinician quote/testimonial
- ✅ Use synthetic/de-identified data only
- ✅ Include captions (.srt file)

**DON'T:**
- ❌ Spend >15 seconds touring code/repo
- ❌ Show any PHI
- ❌ Exceed 3 minutes
- ❌ Rush through the demo
- ❌ Use background music that competes with voice

---

**Note:** This transcript uses only data from `tests/fixtures/ground-truth.json`. All claims supported by `BENCHMARKS.md` and `docs/IMPACT_ANALYSIS.md`.
