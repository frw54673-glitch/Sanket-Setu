"""Paths, feature schema and sign configuration (single source of truth)."""
from __future__ import annotations

import json
from dataclasses import dataclass, field, fields
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "configs" / "signs.json"
DATA_CSV = ROOT / "data" / "processed" / "landmarks.csv"
RAW_DIR = ROOT / "data" / "raw_images"
MODEL_PATH = ROOT / "models" / "isl_static_classifier.joblib"
META_PATH = ROOT / "models" / "model_metadata.json"
REPORT_DIR = ROOT / "reports"

# Official Indian Sign Language Dictionary (ISLRTC, Dept of Empowerment of Persons with
# Disabilities, Govt of India). The dictionary is VIDEO-ONLY and exposes no text or
# handshape API, so every sign meaning must be confirmed by a Deaf signer or a qualified
# ISL interpreter. See docs/data_collection_protocol.md.
ISL_DICTIONARY_URL = "https://islrtc.nic.in/isl-dictionary/"
ISL_DICTIONARY_LOOKUP = "https://divyangjan.depwd.gov.in/islrtc/search.php?search={term}"
ISL_DICTIONARY_DRIVE = "https://drive.google.com/drive/folders/1U-Pr4r1-cupgNOOq9NH_uTsQnPSVEKco"
ISL_DICTIONARY_YOUTUBE = "https://www.youtube.com/@ISLRTC"

NONE_LABEL = "none"
N_FEATURES = 63  # 21 landmarks x (x, y, z)
FEATURE_COLS = [f"f{i}" for i in range(N_FEATURES)]
META_COLS = ["sample_id", "label", "signer_id", "session_id", "timestamp", "capture_condition", "hand_side"]
ALL_COLS = META_COLS + FEATURE_COLS


@dataclass(frozen=True)
class Sign:
    """One entry of the supported vocabulary.

    ``validation_status`` records whether a *human* confirmed the meaning and the
    handshape. ``type_confidence`` records how strongly the *published sources* support
    the static/one-hand classification, independently of human confirmation.
    """

    id: str
    label_en: str
    text_hi: str
    text_en: str
    sign_type: str  # static_single_hand | moving | two_hand | background
    validation_status: str  # verified | needs_review | demo_only | n/a
    source_url: str = ""
    validator: str = "not yet reviewed"
    notes: str = ""
    enabled: bool = True
    # --- provenance / review metadata (optional; older config files still load) ---
    type_evidence: str = ""
    type_confidence: str = "unknown"  # high | medium | low | unknown
    dictionary_category: str = ""
    variants_available: bool = False
    verification_checklist: list = field(default_factory=list)
    reference_photo: str = ""  # local path to the team's own consented photo, never committed


def _load(path: Path = CONFIG_PATH) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def load_signs(path: Path = CONFIG_PATH) -> tuple[str, list[Sign]]:
    raw = _load(path)
    names = {f.name for f in fields(Sign)}
    signs = [Sign(**{k: v for k, v in e.items() if k in names}) for e in raw["signs"]]
    return raw.get("config_version", "unknown"), signs


def load_phrases(path: Path = CONFIG_PATH) -> list[dict]:
    return _load(path).get("staff_phrases", [])


def load_excluded(path: Path = CONFIG_PATH) -> list[dict]:
    """Signs deliberately kept out of the static model, with the reason for each."""
    return _load(path).get("excluded_signs", [])


def load_meta(path: Path = CONFIG_PATH) -> dict:
    """Top-level documentation blocks (dictionary pointers, review protocol)."""
    return {k: v for k, v in _load(path).items() if k.startswith("_") or k == "dictionary"}


def trainable(signs: list[Sign]) -> list[Sign]:
    """Only enabled static one-hand signs (+ the background class) may enter the model."""
    return [s for s in signs if s.enabled and s.sign_type in ("static_single_hand", "background")]


def unverified(signs: list[Sign]) -> list[Sign]:
    return [s for s in trainable(signs) if s.sign_type != "background" and s.validation_status != "verified"]


def blocked(signs: list[Sign]) -> list[Sign]:
    """Configured signs that are not yet enabled, with the reason recorded in notes."""
    return [s for s in signs if not s.enabled]
