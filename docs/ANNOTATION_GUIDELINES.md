# Clinical Entity Annotation Guidelines

**Version:** 1.0
**Purpose:** Standardize ground truth annotation for benchmark validation
**Audience:** Medical SME annotators

---

## Overview

You will review clinical transcripts and extract structured entities. Your annotations will serve as the **gold standard** for evaluating automated extraction systems.

**Important:** Do NOT look at any automated extraction output before completing your annotation. This ensures independence.

---

## Entity Types to Extract

### 1. Conditions / Diagnoses

**Definition:** Medical conditions, diseases, symptoms, or clinical findings mentioned as relevant to the patient.

**Include:**
- Active diagnoses ("hypertension", "type 2 diabetes")
- Suspected conditions ("possible stable angina", "rule out PE")
- Symptoms that function as working diagnoses ("chest pain", "dyspnea")
- Chief complaint

**Exclude:**
- Negated conditions ("no history of diabetes")
- Family history (separate category)
- Past surgical history (unless current complication)

**Fields to capture:**
| Field | Required | Example |
|-------|----------|---------|
| name | Yes | "stable angina" |
| icd10 | If known | "I20.9" |
| status | Yes | active / resolved / suspected |
| isChiefComplaint | If applicable | true / false |

**Examples:**

| Transcript Text | Extract? | Annotation |
|-----------------|----------|------------|
| "48-year-old with chest pain" | ✅ Yes | name: "chest pain", status: active, isChiefComplaint: true |
| "history of hypertension" | ✅ Yes | name: "hypertension", status: active |
| "no diabetes" | ❌ No | (negated) |
| "possible stable angina" | ✅ Yes | name: "stable angina", status: suspected |
| "father had CAD" | ❌ No | (family history, not patient) |

---

### 2. Medications

**Definition:** Drugs the patient is currently taking or has recently taken.

**Include:**
- Current medications ("takes lisinopril 10mg daily")
- Recently discontinued ("stopped metformin last week")
- PRN medications ("ibuprofen as needed")

**Exclude:**
- Medications being ordered (see Orders)
- Allergic reactions to medications (see Allergies)
- Family member medications

**Fields to capture:**
| Field | Required | Example |
|-------|----------|---------|
| name | Yes | "lisinopril" |
| dose | If mentioned | "10 mg" |
| frequency | If mentioned | "daily" |
| route | If mentioned | "oral" |
| status | Yes | active / discontinued / prn |

**Examples:**

| Transcript Text | Extract? | Annotation |
|-----------------|----------|------------|
| "on aspirin 81mg daily" | ✅ Yes | name: "aspirin", dose: "81 mg", frequency: "daily" |
| "start atorvastatin" | ❌ No | (this is an order, not current med) |
| "allergic to penicillin" | ❌ No | (allergy, not medication) |
| "stopped lisinopril 2 weeks ago" | ✅ Yes | name: "lisinopril", status: discontinued |

---

### 3. Vital Signs

**Definition:** Measured physiological parameters.

**Include:**
- Blood pressure, heart rate, respiratory rate, temperature, SpO2
- Weight, height, BMI (if documented as vitals)
- Pain scale

**Fields to capture:**
| Field | Required | Example |
|-------|----------|---------|
| type | Yes | "blood_pressure" |
| value | Yes | "142/88" |
| unit | Yes | "mmHg" |

**Standard Types:**
- blood_pressure
- heart_rate
- respiratory_rate
- temperature
- oxygen_saturation
- weight
- height
- bmi
- pain_scale

**Examples:**

| Transcript Text | Extract? | Annotation |
|-----------------|----------|------------|
| "BP 142/88" | ✅ Yes | type: blood_pressure, value: "142/88", unit: "mmHg" |
| "heart rate 78" | ✅ Yes | type: heart_rate, value: "78", unit: "bpm" |
| "afebrile" | ⚠️ Maybe | Could extract as temperature: "afebrile" or skip |
| "vital signs stable" | ❌ No | (no specific values) |

---

### 4. Orders

**Definition:** New tests, procedures, medications, or referrals being ordered.

**Include:**
- Lab orders ("order CBC", "check lipid panel")
- Imaging orders ("CT chest", "stress test")
- Medication orders ("start statin", "prescribe metformin")
- Procedure orders ("schedule colonoscopy")
- Referral orders ("refer to cardiology")

**Exclude:**
- Tests already completed ("CT showed...")
- Current medications (see Medications)

**Fields to capture:**
| Field | Required | Example |
|-------|----------|---------|
| type | Yes | labs / imaging / medications / procedures / consults |
| name | Yes | "lipid panel" |
| indication | If mentioned | "hyperlipidemia" |

**Examples:**

| Transcript Text | Extract? | Annotation |
|-----------------|----------|------------|
| "order stress test" | ✅ Yes | type: imaging, name: "stress test" |
| "start atorvastatin 20mg" | ✅ Yes | type: medications, name: "atorvastatin", dose: "20mg" |
| "CT showed no PE" | ❌ No | (completed test, not order) |
| "recommend echocardiogram" | ✅ Yes | type: imaging, name: "echocardiogram" |
| "refer to cardiology" | ✅ Yes | type: consults, name: "cardiology" |

---

### 5. Allergies

**Definition:** Patient allergies or adverse drug reactions.

**Include:**
- Drug allergies ("allergic to penicillin")
- Environmental allergies if clinically relevant
- Food allergies if clinically relevant
- Documented adverse reactions

**Fields to capture:**
| Field | Required | Example |
|-------|----------|---------|
| substance | Yes | "penicillin" |
| reaction | If mentioned | "rash" |
| severity | If mentioned | mild / moderate / severe |

**Examples:**

| Transcript Text | Extract? | Annotation |
|-----------------|----------|------------|
| "allergic to penicillin" | ✅ Yes | substance: "penicillin" |
| "sulfa causes rash" | ✅ Yes | substance: "sulfa", reaction: "rash" |
| "no known drug allergies" | ❌ No | (negated) |
| "NKDA" | ❌ No | (no known drug allergies) |

---

### 6. Family History

**Definition:** Medical conditions in family members.

**Include:**
- Conditions in first-degree relatives (parents, siblings, children)
- Conditions in second-degree relatives if noted
- Genetic conditions

**Fields to capture:**
| Field | Required | Example |
|-------|----------|---------|
| condition | Yes | "coronary artery disease" |
| relation | If mentioned | "father" |

**Examples:**

| Transcript Text | Extract? | Annotation |
|-----------------|----------|------------|
| "father had MI at 55" | ✅ Yes | condition: "MI", relation: "father" |
| "family history of CAD" | ✅ Yes | condition: "CAD" |
| "no family history of cancer" | ❌ No | (negated) |

---

### 7. Social History

**Definition:** Lifestyle factors relevant to health.

**Include:**
- Tobacco use (current, former, never)
- Alcohol use
- Drug use
- Occupation (if clinically relevant)

**Fields to capture:**
| Field | Required | Example |
|-------|----------|---------|
| type | Yes | tobacco / alcohol / drugs / occupation |
| status | Yes | current / former / never |
| details | If mentioned | "1 pack per day for 20 years" |

**Examples:**

| Transcript Text | Extract? | Annotation |
|-----------------|----------|------------|
| "smokes 1 PPD x 20 years" | ✅ Yes | type: tobacco, status: current, details: "1 PPD x 20 years" |
| "quit smoking 5 years ago" | ✅ Yes | type: tobacco, status: former |
| "denies alcohol" | ✅ Yes | type: alcohol, status: never |

---

## Annotation Process

### Step 1: Read Entire Transcript
Read the full transcript once without annotating to understand context.

### Step 2: Extract Entities
Go through transcript systematically, extracting each entity type.

### Step 3: Review for Completeness
- Did you capture all conditions mentioned?
- Did you distinguish current meds from orders?
- Did you note negations correctly (exclude them)?

### Step 4: Record Confidence
For each entity, rate your confidence:
- **High:** Clear, unambiguous mention
- **Medium:** Requires some inference
- **Low:** Uncertain, may be misinterpreted

### Step 5: Note Difficult Cases
Document any entities you're uncertain about for adjudication.

---

## Edge Cases

### Ambiguous Mentions

| Situation | Guidance |
|-----------|----------|
| "chest pain, possible angina" | Extract BOTH as conditions |
| "on lisinopril, increasing to 20mg" | Current med (lisinopril) + med order (dose increase) |
| "diabetes, well controlled on metformin" | Condition (diabetes) + medication (metformin) |
| "recommend CT vs MRI" | Extract as single order with both options, or two separate orders |

### Implied Information

| Situation | Guidance |
|-----------|----------|
| "continue current medications" | Do NOT invent specific meds |
| "vitals stable" | Do NOT extract (no specific values) |
| "labs pending" | Do NOT extract as order (already ordered) |

### Abbreviations

Common abbreviations to recognize:
- HTN = hypertension
- DM = diabetes mellitus
- CAD = coronary artery disease
- COPD = chronic obstructive pulmonary disease
- CHF = congestive heart failure
- MI = myocardial infarction
- CVA = cerebrovascular accident (stroke)
- PE = pulmonary embolism
- DVT = deep vein thrombosis
- NKDA = no known drug allergies
- PPD = packs per day

---

## Quality Checklist

Before submitting your annotation:

- [ ] All conditions extracted (including chief complaint)
- [ ] Negated conditions excluded
- [ ] Current meds distinguished from orders
- [ ] All orders captured (labs, imaging, meds, consults)
- [ ] Allergies captured with reactions if mentioned
- [ ] Family history separated from patient conditions
- [ ] Social history captured
- [ ] Confidence rated for uncertain entities
- [ ] Difficult cases documented

---

## Questions?

Contact Paul for clarification on edge cases before proceeding.

---

**Remember:** Your annotation is the gold standard. Be thorough, consistent, and document uncertainty.
