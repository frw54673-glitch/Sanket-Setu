# Data directory

Everything in this directory is **local only** and is excluded from git by `.gitignore`.
Nothing here should ever be committed, pushed, or published without checking the
provenance and consent checklist in
[`../docs/data_collection_protocol.md`](../docs/data_collection_protocol.md).

```
data/
├── processed/
│   ├── landmarks.csv     # the dataset: 21 landmark numbers + metadata, one row per sample
│   └── demo_landmarks.csv  # (unused) kept out of the real dataset on purpose
├── raw_images/           # only if you import photos you are allowed to use
│   └── <class_name>/*.jpg
└── signers.csv           # who consented: pseudonymous id, session, condition, date
```

## `processed/landmarks.csv`

Written by `python -m sanket_setu.collect_data`. One row per captured sample.

| Column | Meaning |
|---|---|
| `sample_id` | unique id |
| `label` | sign id, e.g. `num_3`, or `none` for the rejection class |
| `signer_id` | pseudonymous participant id, e.g. `S01` |
| `session_id` | recording session, e.g. `2026-10-30` |
| `timestamp` | ISO-8601 UTC |
| `capture_condition` | lighting / background / distance tag |
| `hand_side` | Left / Right, reported by MediaPipe |
| `f0` … `f62` | the 63-d feature vector: 21 landmarks × (x, y, z), wrist-relative and hand-size scaled |

The metadata columns are **never** used as model inputs. The feature matrix is built from
`f0…f62` only, and a test asserts the trained model still has exactly 63 features.

## `raw_images/`

Only for images you already have and are allowed to use. Put them in
`raw_images/<class_name>/` and run:

```powershell
python -m sanket_setu.collect_data --signer S02 --import-dir
```

**Before you import anything**, check the licence of the source and record it. If the
source is the official ISL Dictionary, read its copyright policy first — it is published
by ISLRTC (DEPwD) and its videos are not ours to redistribute. If you are not sure, do
not import it.

Raw images are never committed: `.gitignore` excludes `data/raw_images/*`.

## `signers.csv`

Written by the capture tool when a session starts. One row per signer per session:

| Column | Meaning |
|---|---|
| `signer_id` | pseudonymous id |
| `session_id` | session |
| `capture_condition` | condition tag used for that session |
| `timestamp` | when the session started |
| `consented` | `y` |
| `notes` | free text |

### Withdrawing a participant

1. Delete that signer's rows from `processed/landmarks.csv`.
2. Delete their line from `signers.csv`.
3. Retrain.

A withdrawn participant must not remain in any published artefact, including the metrics
in `reports/`.

## Why there is no real data in the repository

Because there isn't any yet. This project is not allowed to ship with invented samples,
and it is not allowed to ship real people's hand data without their explicit consent. The
repository ships the **tooling** to collect it honestly, and the protocol to do it
properly. `tests/` uses synthetic vectors to check pipeline mechanics only — those are
never used for reported metrics.
