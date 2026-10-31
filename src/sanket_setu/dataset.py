"""Landmark CSV schema, validation and image-folder import."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

from .config import ALL_COLS, DATA_CSV, FEATURE_COLS, META_COLS
from .landmarks import HandDetector, pil_to_rgb

IMAGE_EXT = {".jpg", ".jpeg", ".png"}


class DatasetError(Exception):
    """Actionable dataset/training problem."""


def new_row(label, feats, signer_id, session_id, condition="unspecified", hand_side="") -> dict:
    row = {
        "sample_id": uuid.uuid4().hex,
        "label": label,
        "signer_id": signer_id,
        "session_id": session_id,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "capture_condition": condition,
        "hand_side": hand_side or "",
    }
    row.update({c: float(v) for c, v in zip(FEATURE_COLS, feats)})
    return row


def append_rows(rows: list[dict], path: Path = DATA_CSV) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=ALL_COLS).to_csv(path, mode="a", header=not path.exists(), index=False)


def validate(df: pd.DataFrame, allowed: list[str], min_per_class: int = 10) -> tuple[pd.DataFrame, list[str]]:
    warnings: list[str] = []
    missing_cols = [c for c in ALL_COLS if c not in df.columns]
    if missing_cols:
        raise DatasetError(f"Dataset is missing columns: {missing_cols[:5]}... Re-collect with sanket_setu.collect_data.")
    feats = df[FEATURE_COLS].apply(pd.to_numeric, errors="coerce")
    if (~np.isfinite(feats.to_numpy(dtype=float))).any():
        raise DatasetError("Dataset contains NaN/inf/non-numeric feature values. Remove or re-collect those rows.")
    df = df.copy()
    df[FEATURE_COLS] = feats
    unknown = sorted(set(df["label"]) - set(allowed))
    if unknown:
        raise DatasetError(f"Labels not enabled in configs/signs.json: {unknown}")
    missing = sorted(set(allowed) - set(df["label"]))
    if missing:
        raise DatasetError(f"No samples for class(es) {missing}. Collect them: python -m sanket_setu.collect_data --signer S01")
    if df["sample_id"].duplicated().any():
        raise DatasetError("Duplicate sample_id values found.")
    dup = df.duplicated(subset=FEATURE_COLS)
    if dup.any():
        warnings.append(f"Dropped {int(dup.sum())} exact-duplicate feature rows.")
        df = df[~dup]
    counts = df["label"].value_counts()
    small = {k: int(v) for k, v in counts.items() if v < min_per_class}
    if small:
        raise DatasetError(f"Too few samples (need >= {min_per_class} per class): {small}")
    return df.reset_index(drop=True), warnings


def load_dataset(path: Path, allowed: list[str], min_per_class: int = 10) -> tuple[pd.DataFrame, list[str]]:
    if not Path(path).exists():
        raise DatasetError(f"No dataset at {path}. Collect data first: python -m sanket_setu.collect_data --signer S01")
    return validate(pd.read_csv(path, dtype={"signer_id": str, "session_id": str}), allowed, min_per_class)


def import_folder(root: Path, allowed: list[str], detector: HandDetector, signer_id: str, session_id: str,
                  condition: str = "imported_images") -> tuple[list[dict], dict]:
    """data/raw_images/<class>/* -> landmark rows. Only images you are allowed to use."""
    rows, report = [], {"unreadable": 0, "no_hand": 0, "multiple_hands": 0, "unknown_folders": [], "imported": {}}
    for folder in sorted(p for p in Path(root).iterdir() if p.is_dir()):
        if folder.name not in allowed:
            report["unknown_folders"].append(folder.name)
            continue
        for f in sorted(folder.iterdir()):
            if f.suffix.lower() not in IMAGE_EXT:
                continue
            try:
                with Image.open(f) as im:
                    det = detector.detect(pil_to_rgb(im))
            except Exception:
                report["unreadable"] += 1
                continue
            if det.status != "ok":
                report[det.status] += 1
                continue
            rows.append(new_row(folder.name, det.features, signer_id, session_id, condition, det.hand_side))
            report["imported"][folder.name] = report["imported"].get(folder.name, 0) + 1
    return rows, report
