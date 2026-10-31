# Architecture

Sanket Setu is a **limited-vocabulary ISL sign-recognition and communication-support
prototype**. It reads a small, verified set of static one-hand ISL signs and shows the
result as Hindi and English text, with optional speech.

Two engines sit behind one interface and one shared inference module.

## Data flow

```mermaid
flowchart TD
    subgraph Capture["Data capture (real consenting signers)"]
        CAM[Webcam] --> DET[MediaPipe Hands<br/>21 landmarks]
        DET --> NORM[Wrist-relative +<br/>hand-size scaled<br/>63-d vector]
        NORM --> CSV[(landmarks.csv<br/>landmarks + metadata)]
    end

    subgraph Training["Training"]
        CSV --> VAL[Schema validation<br/>duplicates, NaN, counts]
        VAL --> SPLIT[Group-aware split<br/>by signer / session]
        SPLIT --> RF[RandomForest<br/>class_weight=balanced]
        RF --> THR[Reject threshold<br/>tuned on VALIDATION only]
        RF --> ART[(models/*.joblib<br/>model_metadata.json)]
        RF --> REP[(reports/metrics.json<br/>classification_report.txt)]
    end

    subgraph Inference["Inference (shared by app + local webcam)"]
        IMG[Photo / webcam frame] --> RGB[RGB conversion]
        RGB --> DET2[MediaPipe Hands]
        DET2 --> NORM2[Same 63-d normalisation]
        NORM2 --> GEO[Engine A: Geometric<br/>rule-based finger count]
        NORM2 --> ML[Engine B: ML classifier]
        ML --> GATE{score >= threshold?}
        GATE -->|no| REJ[low_score - "try again"]
        GATE -->|yes| NONE{class == none?}
        NONE -->|yes| UNS[unsupported_sign]
        NONE -->|no| OUT[Hindi + English text]
        GEO --> OUT
        OUT --> CONF[Visitor confirms]
        CONF --> LOG[Conversation panel<br/>session only]
    end

    ART --> ML
```

## Components

| Path | Responsibility | Status |
|---|---|---|
| `app/streamlit_app.py` | Web UI: home, signer mode, staff mode, vocabulary, model status | implemented |
| `src/sanket_setu/config.py` | Paths, feature schema, `Sign` model, vocabulary loading | implemented |
| `src/sanket_setu/landmarks.py` | MediaPipe adapter, RGB/BGR contract, 63-d normalisation | implemented |
| `src/sanket_setu/geometric.py` | Engine A: rule-based finger-extension baseline | implemented |
| `src/sanket_setu/inference.py` | Shared inference for both engines, unknown-sign handling | implemented |
| `src/sanket_setu/dataset.py` | CSV schema, validation, image-folder import | implemented |
| `src/sanket_setu/collect_data.py` | Consent-gated capture from real signers | implemented |
| `src/sanket_setu/train_model.py` | Group-aware training, threshold tuning, reports | implemented |
| `src/sanket_setu/realtime.py` | Local-device webcam runner | implemented |
| `src/sanket_setu/speech.py` | Optional gTTS Hindi/English audio, graceful fallback | implemented |
| `src/sanket_setu/labels.py` | — | not needed; label logic lives in `config.py` |
| `src/sanket_setu/preprocessing.py` | — | not needed; preprocessing lives in `landmarks.py` |

## Two engines, one contract

Both engines return the same `Result` object from `inference.py`, so the UI and the
webcam runner can never disagree about what a sign means.

| | Engine A — Geometric | Engine B — ML classifier |
|---|---|---|
| Type | rule-based | trained classifier |
| Needs data | no | yes |
| Covers | numeral signs only | every enabled vocabulary entry |
| Output confidence | none (no score) | uncalibrated RandomForest score |
| Honest label | "geometric baseline" | "model score (not accuracy)" |

Engine A exists so the prototype is usable before any dataset exists. It is never
presented as machine learning, and it carries no accuracy claim.

## Feature representation

21 MediaPipe landmarks → 63 floats.

1. Translate so the wrist is the origin.
2. Scale by the wrist → middle-finger-MCP distance, so the vector is independent of how
   far away the signer stands and how big their hand is.
3. Flatten in MediaPipe's fixed landmark order.

**Mirroring rule:** features are **not** mirrored. `hand_side` is recorded as metadata
only. A browser camera snapshot is usually mirrored by the OS, an OpenCV frame is not, so
the two capture paths can disagree; the capture tool shows a mirrored *preview* while the
features come from the raw frame.

## Leakage controls

This is the part that decides whether the reported metrics mean anything.

- Metadata (`signer_id`, `session_id`, `sample_id`, `timestamp`, `hand_side`,
  `capture_condition`) is stored in the CSV but **never** enters the feature matrix.
  `X` is built from `FEATURE_COLS` only, and a test asserts `n_features_in_ == 63`.
- The split is **group-aware**: by `signer_id` when there are 3+ signers, otherwise by
  `signer_id/session_id`. It is never a random split over adjacent frames.
- The reject threshold is tuned on the **validation** partition only and applied
  unchanged to the test partition, which is read once.
- The capture tool refuses two samples of the same sign that are too similar in landmark
  space, which is what stops a held pose from generating near-duplicate rows that leak
  across partitions.
- If there is only one signer, the split falls back to a random stratified split and the
  metadata records `cross_person_validated: false` with a loud warning.

## Data flow into the conversation

Nothing reaches the conversation panel automatically. A recognised sign is shown as a
proposal, and the visitor has to press **"Yes, this is what I meant"**. Staff replies come
from a fixed phrase board. The conversation exists only in the browser session; nothing is
written to disk.

## Future scope (not implemented)

- Temporal / two-hand model for moving signs such as HELP, THANK YOU, MONEY.
- Fingerspelling (26 letters) as a separate classifier.
- On-device deployment for a tablet at the help desk.
- Per-region vocabulary variants, once the team decides which region it targets.
