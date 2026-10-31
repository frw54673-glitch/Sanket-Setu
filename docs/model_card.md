# Model Card — Sanket Setu static one-hand sign classifier

> **Status of this card: partially filled in, on purpose.**
> Every section that depends on real data or human validation is marked `NOT YET FILLED IN`.
> Those sections must be completed by the team from the artefacts the training run
> actually produced. Do not fill them in from memory, from a slide, or from a guess.

## 1. Model details

| | |
|---|---|
| Name | `isl_static_classifier` |
| Algorithm | `RandomForestClassifier(n_estimators=300, class_weight="balanced")` |
| Seed | 42 (fixed) |
| Input | 63 floats: 21 MediaPipe hand landmarks × (x, y, z), wrist-relative, scaled by the wrist → middle-finger-MCP distance |
| Output | one class label + an uncalibrated score |
| Classes | `none`, `num_1` … `num_5` (see `configs/signs.json` — this is the live list, not a copy) |
| Artifacts | `models/isl_static_classifier.joblib`, `models/model_metadata.json` |
| Reports | `reports/metrics.json`, `reports/classification_report.txt` |
| Library versions | recorded in `model_metadata.json` → `library_versions` at training time |
| Probability calibration | **none.** The score is a raw RandomForest vote share. It is not a real-world probability and it is not accuracy. |

### What the score means

`predict_proba().max()` from a RandomForest is the fraction of trees that voted for the
winning class. It is not calibrated against reality. The reject threshold is tuned on the
**validation** partition only and applied unchanged to the test partition. The UI says
"model score (not accuracy)" for exactly this reason.

## 2. Intended use

A communication-support aid at a healthcare or public-service help desk:

- a Deaf or signing visitor shows one supported static one-hand sign;
- the app displays the meaning in Hindi and English, large enough to read across a desk;
- the visitor confirms it was understood correctly;
- hearing staff reply from a fixed phrase board;
- optional spoken output for visitors who cannot read quickly.

**Intended users:** signing visitors, and hearing staff who need to communicate with them.

## 3. Supported signs

The authoritative list is `configs/signs.json`. The app renders it directly, so it can
never drift from the model.

| Sign | Hindi | Enabled | Meaning verified by a human? |
|---|---|---|---|
| One | एक | yes | **not yet** — `needs_review` |
| Two | दो | yes | **not yet** — `needs_review` |
| Three | तीन | yes | **not yet** — `needs_review` |
| Four | चार | yes | **not yet** — `needs_review` |
| Five | पाँच | yes | **not yet** — `needs_review` |
| Doctor | डॉक्टर | no (candidate) | **not yet** — awaiting interpreter sign-off |
| Wait | प्रतीक्षा करें | no (candidate) | **not yet** — awaiting interpreter sign-off |
| Police | पुलिस | no (candidate) | **not yet** — awaiting interpreter sign-off |
| Water | पानी | no (candidate) | **not yet** — awaiting interpreter sign-off |
| Hello | नमस्ते | no (candidate) | **not yet** — awaiting interpreter sign-off |

`none` is a background/rejection class, not an ISL sign: a visible hand that is not one of
the supported signs. The model needs it in order to refuse to guess.

### Why the vocabulary is so small

The official ISL Dictionary is **video-only** and publishes no written handshape, movement
or notation, and no machine-readable API. There is therefore no way to check a sign
automatically. Every entry needs a Deaf signer or a qualified ISL interpreter to confirm
that the meaning is right, that it uses one hand, and that it is static.

Sources also disagree with each other. `HELP` appears in a curated list of 140 static ISL
signs (IITM, *Gesture Classification of Indian Sign Language*), while Zeshan (2003) and the
People's Linguistic Survey of India describe it as a **directional** sign whose meaning
changes with the direction of movement. A still frame cannot distinguish those, so the
model would have learned an arbitrary meaning.

Signs deliberately excluded from the static model, with the reason for each, are recorded
in `configs/signs.json` → `excluded_signs` and shown in the app.

## 4. Excluded use cases

- **Sentence-level translation.** Not implemented and not attempted. ISL grammar, spatial
  reference, facial expression and body posture are not modelled.
- **Moving or two-hand signs** (HELP, THANK YOU, MONEY, PAIN, ACCIDENT, ALLERGY, CALL,
  HOT, LOSE, THIEF). A static single-hand model cannot represent them.
- **Non-manual signs.** `YES` in ISL is a head nod with no manual component (Zeshan 2003),
  so a hand-landmark model cannot see it.
- **Fingerspelling.** Not implemented.
- **Emergency and high-stakes decisions.** Never use alone. A human must confirm.
- **Replacement for a qualified ISL interpreter.** This is a support aid, not a substitute.

## 5. Training data

| Field | Value |
|---|---|
| Source | **NOT YET FILLED IN.** The team collects it: `python -m sanket_setu.collect_data --signer S01` |
| Signers | **NOT YET FILLED IN.** See `data/signers.csv` and `model_metadata.json` → `held_out_signers` |
| Sessions per signer | **NOT YET FILLED IN** |
| Samples per class | **NOT YET FILLED IN.** See `reports/metrics.json` → `class_counts` |
| Regional coverage | **NOT YET FILLED IN.** ISL has regional variants, especially for numerals. Record which region(s) were sampled. |
| Licensing / provenance | **NOT YET FILLED IN.** See the checklist in `docs/data_collection_protocol.md` §6. |

Only hand landmarks are stored. **No images or videos are written to disk by the capture
tool.** If images are imported from `data/raw_images/`, the licence of every source must
be recorded first, and the images stay local and out of git.

The dataset's SHA-256 hash is stored in `model_metadata.json` → `data_hash`, so a report
can always be tied back to the exact rows it was computed from.

## 6. Splits

- Group-aware: by `signer_id` when there are 3 or more signers, otherwise by
  `signer_id/session_id`. Never a random split over adjacent frames.
- 70 % train / 30 % of the remainder to validation / 30 % of the remainder to test, with
  the test partition read exactly once.
- The strategy actually used is recorded in `model_metadata.json` → `split_strategy`.
- `cross_person_validated` is `true` only when the split held out whole signers.
- With fewer than three signers the training run refuses to imply representativeness and
  records the warning.

## 7. Metrics

Read from `reports/metrics.json` after a real run. **Nothing is written here by hand.**

| Metric | Value |
|---|---|
| Held-out test accuracy | **NOT YET FILLED IN** |
| Macro precision / recall / F1 | **NOT YET FILLED IN** |
| Coverage at the reject threshold | **NOT YET FILLED IN** |
| Accuracy on accepted samples | **NOT YET FILLED IN** |
| Per-signer accuracy (held-out signers) | **NOT YET FILLED IN** |
| Test sample count | **NOT YET FILLED IN** |

The per-signer table is the most useful one: each row is a person who was **not** in the
training partition, which is the closest an offline dataset can get to a new-visitor test.

## 8. Failure modes

| Failure | What the user sees | Mitigation |
|---|---|---|
| No hand in frame | "No hand found. Keep one hand fully visible, in good light." | Guidance in the UI |
| Two hands in frame | "More than one hand found. This prototype reads one hand only." | One-hand capture rule |
| Hand too small / too far | Capture tool refuses the sample | `MIN_HAND_FRACTION` gate |
| Signer still moving | Capture tool refuses the sample | stability gate over 12 frames |
| Two near-identical samples | Capture tool refuses the sample | minimum-distance gate |
| Sign outside the vocabulary | "A hand was seen, but not one of the supported signs." | the `none` class |
| Low model score | "Sign not confidently recognized. Please try again…" | validation-tuned threshold |
| Poor lighting / occlusion | Wrong or refused reading | disclosed limitation |
| Signer with an unusual hand shape | May be refused or misread | per-signer reporting exposes this |
| Regional variant of a sign | May be refused or misread | disclose the targeted region |

## 9. Privacy and consent

- The capture tool asks for consent **before** anything is recorded.
- Only 21 landmark numbers plus metadata are stored. No photos, no video, no audio.
- Signer identity is a pseudonymous id (`S01`). The tool rejects a non-alphanumeric id,
  which is a small guard against someone typing a real name.
- `data/signers.csv` records who contributed and when. A signer may withdraw: delete
  their rows from `data/processed/landmarks.csv` and their line from `data/signers.csv`.
- Nothing is uploaded anywhere. The only outbound request in the whole system is the
  optional gTTS call, which sends **plain text only** and only after the user clicks
  "Generate audio". Images and landmarks are never sent to any external service.
- The conversation panel lives in the browser session only.

## 10. Ethical considerations and intended impact

The point of this prototype is a specific, unglamorous moment: a Deaf visitor at a
government office and a hearing clerk who cannot sign, facing each other with no way to
talk. Every design decision here — large type, both languages, human confirmation, the
refusal to guess — exists to make that moment less bad.

The risk of harm is real and must be stated: **a wrong reading in a medical or legal
setting can cause harm.** That is why the app refuses below its threshold, why a human
must confirm, why the vocabulary is tiny and verified rather than large and guessed, and
why the app must never be used alone for emergency or high-stakes decisions.

## 11. Known limitations

1. Five numeral signs plus one rejection class. This is a prototype, not a translator.
2. No sign in the vocabulary has yet been verified by a Deaf signer or interpreter.
3. Static single-hand signs only — no movement, no two-hand signs, no facial expression.
4. The score is uncalibrated and must not be read as a probability or as accuracy.
5. Generalisation across signers is unvalidated until at least three signers have been
   collected and a signer-held-out split has been run.
6. The camera-facing setup is unforgiving: poor light, partial occlusion and unusual hand
   shapes will cause refusals and errors.
7. Regional variants of ISL numerals are not modelled.
8. No validated user study with Deaf participants has been run. The team must not claim
   one until it has.
