# Data Collection Protocol

This is the procedure that turns "we have an idea" into "we have a real dataset that
survives a judge asking how you collected it". Follow it exactly and record what you do.

Everything here applies to **real people**. The most common way a project like this fails
is not a bad model — it is a dataset that leaks, or that was collected without consent,
or that was labelled with signs nobody verified.

---

## 1. Before you collect anything

### 1.1 Verify the signs first

Do this **before** the first sample, not after. A dataset of the wrong handshape is worse
than no dataset.

1. Open the ISL Dictionary for the term:
   `https://divyangjan.depwd.gov.in/islrtc/search.php?search=<Term>`
   (or browse at `https://islrtc.nic.in/isl-dictionary/`).
2. Watch the sign video.
3. The dictionary usually shows several variants ("Sign 1", "Sign 2", …). **Fix exactly
   one canonical variant** for the project and write down which one.
4. Check the three conditions:
   - the meaning is the one you intend;
   - it uses **one** hand;
   - it is **static** — no movement, no repeated motion, no change of handshape.
5. Record the decision in `configs/signs.json`:
   - `validation_status`: `"verified"` **only** after a human has checked it;
   - `validator`: the real name and role of the person who checked it;
   - `notes`: which variant you fixed, and any regional note.
6. Only then set `enabled: true`.

**The official ISL Dictionary is video-only.** There is no written handshape table and no
API. A human check is not optional and cannot be automated.

### 1.2 Get a Deaf signer or a qualified ISL interpreter involved

At minimum, one person who signs should review the vocabulary. Ideally they should also
review the recording session. Budget time for this; it is the single highest-value hour
in the whole project, and it is the thing that separates this from a gesture demo.

### 1.3 Decide the target region

ISL has regional variation — ISLRTC explicitly records regional variants of numerals and
colour terms (Hyderabad, Mumbai, Kolkata, Munger/Bihar, Manipur). Decide whether the
prototype targets one region or several, write it down, and say so in the model card and
the slides. If you only have signers from one region, say that too.

---

## 2. Consent

Ask **every** participant, every time, and record the answer.

```
CONSENT CHECK
  Only hand landmarks (numbers) are saved. No photos, no video, no audio.
  Record only people who have agreed to contribute, and use a pseudonymous id (S01, S02...).
  A signer may withdraw by asking you to delete their rows from data/processed/landmarks.csv
  and their line from data/signers.csv.
Continue? [y/N]
```

### Consent checklist

- [ ] The participant was **told** what is recorded: 21 landmark numbers, plus a
      pseudonymous id, a session id, a timestamp and a capture-condition tag.
- [ ] The participant was **told** what is *not* recorded: no photos, no video, no audio.
- [ ] The participant was **told** the data will be used to train a sign-recognition
      model, and published with the project.
- [ ] The participant was **told** they can withdraw at any time, and how.
- [ ] Consent was recorded in `data/signers.csv` with the date.
- [ ] A **pseudonymous** id is used. Never a real name. The tool rejects a
      non-alphanumeric `--signer` value as a small guard against typing a name.

### Withdrawal

Delete the participant's rows from `data/processed/landmarks.csv` and their line from
`data/signers.csv`, then retrain. A withdrawn participant must not remain in any
published artefact.

---

## 3. Capture conditions

Vary these **deliberately**. A model trained only on one lighting condition and one
background will fail at the actual desk, which is the whole point.

| Dimension | Vary across |
|---|---|
| Lighting | bright indoor · dim indoor · daylight from a window · backlit |
| Background | plain wall · busy/patterned · desk clutter |
| Distance | close (~30 cm) · normal (~50 cm) · far (~80 cm) |
| Angle | straight on · slight tilt left · slight tilt right |
| Hand side | left hand · right hand |
| Handedness | whichever the signer actually uses |
| Clothing | sleeve visible · sleeve not visible (affects wrist detection) |

Record a condition tag per session, e.g. `indoor_bright_plain_bg_50cm`.

**Do not** record the same pose over and over from one position. The capture tool will
refuse near-identical samples — that is intentional.

---

## 4. The capture session

```powershell
python -m sanket_setu.collect_data --signer S01 --condition indoor_bright_plain_bg_50cm
```

Controls:

| Key | Action |
|---|---|
| `SPACE` | capture **one** sample of the current sign |
| `N` / `P` | next / previous sign |
| `R` | reset the stability window (after repositioning) |
| `Q` / `Esc` | quit |

What the tool enforces for you:

- **Consent first.** Nothing is written before the prompt is accepted.
- **One deliberate sample per key press.** Never one sample per video frame.
- **Stability gate.** The hand must hold still across 12 frames, so a sample is a settled
  pose and not a mid-transition frame.
- **Size gate.** The hand must be large enough in frame, which rejects a signer who is
  too far away.
- **Separation gate.** Two samples of the same sign must be at least 0.06 apart in
  landmark space. Without this, a signer who holds a static pose for three seconds
  produces three near-identical rows — which inflate every metric and leak straight
  across the train/test split. This is the single most common way a dataset like this
  is ruined.
- **Minimum gap.** 0.8 s between two samples of the same sign.

If the tool refuses a capture, fix the cause (move closer, hold still, reposition) rather
than working around it.

### Target per session

- **20 samples per sign** per session (the default `--target`).
- **2 sessions per signer**, at least on different days or with visibly different
  conditions.
- **Minimum 3 signers.** Three is the bare minimum for a signer-held-out split. Five or
  more is meaningfully better. With fewer than three, the training run marks
  cross-person generalisation as UNVALIDATED — which is correct and must not be hidden.

A minimal but usable dataset: 3 signers × 6 classes (5 numerals + `none`) × 2 sessions ×
20 samples = **720 samples**.

### Capturing the `none` class

`none` is not an ISL sign. It is "a visible hand that is *not* one of the supported
signs": a relaxed open hand, or a hand mid-transition. Capture it with the same rigour,
otherwise the model cannot refuse to guess.

### Importing images you already have

If you already hold photos you are allowed to use:

```powershell
python -m sanket_setu.collect_data --signer S02 --import-dir
```

Put them in `data/raw_images/<class_name>/`. **Check the licence of every source first**
(§6). The importer records the signer id and session id you pass, so imported images are
treated as one person's samples and can be split accordingly.

---

## 5. Dataset structure and splitting

`data/processed/landmarks.csv` has one row per sample:

| Column | Meaning |
|---|---|
| `sample_id` | unique hex id |
| `label` | sign id, e.g. `num_3` |
| `signer_id` | pseudonymous participant id, e.g. `S01` |
| `session_id` | recording session, e.g. `2026-10-30` |
| `timestamp` | ISO-8601 UTC |
| `capture_condition` | lighting/background/distance tag |
| `hand_side` | Left / Right, from MediaPipe |
| `f0` … `f62` | the 63-d feature vector |

**Metadata is stored but never used as a model input.** `X` is built from `f0…f62` only,
and `tests/test_dataset_train.py::test_metadata_never_in_features` asserts the model
still has 63 features. Keep it that way.

### Splitting rule

Split by **signer**, never by row. The training pipeline does this automatically:

- 3+ signers → hold out whole signers (the honest test);
- otherwise → hold out whole sessions;
- otherwise → random stratified split, and the metadata records
  `cross_person_validated: false` with a loud warning.

Do not override this. A random split over frames of the same signer inflates the score
and means nothing.

---

## 6. Dataset provenance and licence checklist

Record this for every source of data, including photos you did not record yourself.

- [ ] Where did it come from? (your own capture / an existing dataset / the ISL Dictionary)
- [ ] What is the licence, and is it compatible with redistribution?
- [ ] Did anyone consent to it being used for model training?
- [ ] Does it contain any personal data that must not be published?
- [ ] Has the source been recorded in the repository?

**On the official ISL Dictionary:** it is published by ISLRTC (DEPwD, Ministry of Social
Justice & Empowerment) and is **video only**. The site carries its own copyright,
privacy, disclaimer and hyperlinking policies. Read them before you reuse any footage.
Do not scrape it, and do not redistribute its videos in your repository.

**A legitimate, openly described alternative** is the ISL translation dictionary released
by Digital India's BHASHINI division with ISLRTC and AI4Bharat, which covers roughly
13,000 ISL dictionary entries across 11 Indian languages and is organised by domain
(Everyday, Medical, Legal, Finance & Banking, …). If the team uses it, record the
provenance and the licence in the model card.

**Never** scrape or redistribute copyrighted media without permission.

---

## 7. Data quality checks

Run these before training:

```powershell
python -m sanket_setu.collect_data --status
```

This prints samples per label, the number of signers and sessions, and warns if there
are fewer than three signers.

The training pipeline then validates automatically and **fails loudly** on:

- missing columns in the CSV;
- NaN, infinite or non-numeric feature values;
- a label that is not enabled in `configs/signs.json`;
- a class with no samples at all;
- duplicate `sample_id`s;
- fewer than 10 samples in a class.

It also drops exact-duplicate feature rows and reports how many.

Manually, before the first run, also check:

- [ ] No real names anywhere — only `S01`-style ids.
- [ ] `data/raw_images/` is not committed to git (`.gitignore` already covers it).
- [ ] Every row's `signer_id` matches someone in `data/signers.csv` who consented.
- [ ] A random spot-check of 20 rows: does the recorded label match the pose?

---

## 8. What is still missing, and who has to do it

| Step | Owner | Status |
|---|---|---|
| Verify each sign against the ISL Dictionary | Deaf signer / ISL interpreter | ☐ not done |
| Choose the canonical variant per sign | Deaf signer / ISL interpreter | ☐ not done |
| Decide the target region | Team | ☐ not done |
| Collect from ≥ 3 signers, ≥ 2 sessions each | Team | ☐ not done |
| Record consent for each signer | Team | ☐ not done |
| Record dataset provenance and licence | Team | ☐ not done |
| Run training and read the real report | Team | ☐ not done |
| Run a small user test with Deaf participants | Team | ☐ not done |
| Fill the model card from the real artefacts | Team | ☐ not done |
