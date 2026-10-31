"""Consent-gated capture of real signer samples.

    python -m sanket_setu.collect_data --signer S01

Designed for collecting REAL data from REAL people, so it enforces the things that
actually damage a dataset if you skip them:

  * one deliberate sample per key press - never one sample per video frame;
  * a stability gate - the hand must hold still for a moment, so a sample is a settled
    pose and not a mid-transition frame;
  * a separation gate - two samples of the same sign must be far enough apart in landmark
    space. Without this, a signer who holds a static pose for three seconds produces three
    near-identical rows, which inflate every metric and leak across the train/test split;
  * a frame-quality gate - the hand must be large enough and fully visible;
  * per-sign progress against a target, with auto-advance;
  * a signer roster that records who consented, so the split can be reported honestly.

Only 21 landmarks and metadata are stored. No images are written to disk.
"""
from __future__ import annotations

import argparse
import csv
import sys
import time
from collections import deque
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from .config import DATA_CSV, RAW_DIR, ROOT, load_signs, trainable
from .dataset import append_rows, import_folder, new_row
from .landmarks import HandDetector, bgr_to_rgb

ROSTER = ROOT / "data" / "signers.csv"

CONSENT = (
    "\nCONSENT CHECK\n"
    "  Only hand landmarks (numbers) are saved. No photos, no video, no audio.\n"
    "  Record only people who have agreed to contribute, and use a pseudonymous id (S01, S02...).\n"
    "  A signer may withdraw by asking you to delete their rows from data/processed/landmarks.csv\n"
    "  and their line from data/signers.csv.\n"
    "Continue? [y/N] "
)

# --- quality gates -------------------------------------------------------------
STABLE_FRAMES = 12          # frames of near-identical landmarks before a capture is allowed
STABLE_TOL = 0.012          # mean per-landmark displacement (normalised units) to count as "still"
MIN_HAND_FRACTION = 0.035   # hand bounding box area / frame area, to reject a far-away hand
MIN_GAP_SEC = 0.8           # minimum seconds between two captures of the same sign
MIN_DISTANCE = 0.06         # minimum landmark distance between two samples of the same sign


def _counts() -> dict[str, int]:
    if DATA_CSV.exists():
        return pd.read_csv(DATA_CSV, usecols=["label"])["label"].value_counts().to_dict()
    return {}


def _last_features(path: Path = DATA_CSV) -> dict[str, np.ndarray]:
    """Most recent feature vector per label, to measure separation from the last sample."""
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    if df.empty:
        return {}
    feats = [c for c in df.columns if c.startswith("f") and c[1:].isdigit()]
    out: dict[str, np.ndarray] = {}
    for label, grp in df.groupby("label"):
        last = grp.iloc[-1]
        out[label] = last[feats].to_numpy(dtype=float)
    return out


def register_signer(signer: str, session: str, condition: str, notes: str = "") -> None:
    """Append this signer to the roster (idempotent per signer+session)."""
    ROSTER.parent.mkdir(parents=True, exist_ok=True)
    exists = False
    if ROSTER.exists():
        with open(ROSTER, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if row.get("signer_id") == signer and row.get("session_id") == session:
                    exists = True
                    break
    if exists:
        return
    with open(ROSTER, "a", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerow([
            signer, session, condition, datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "y", notes,
        ])


def _hand_fraction(pts: np.ndarray) -> float:
    """Fraction of the frame covered by the hand's landmark bounding box."""
    lo, hi = pts[:, :2].min(axis=0), pts[:, :2].max(axis=0)
    return float((hi[0] - lo[0]) * (hi[1] - lo[1]))


def _is_stable(history: deque) -> bool:
    """True when the last STABLE_FRAMES landmarks barely move."""
    if len(history) < STABLE_FRAMES:
        return False
    arr = np.asarray(history)
    return float(np.abs(arr[1:] - arr[:-1]).mean()) < STABLE_TOL


def run_camera(labels, signer, session, condition, cam_index, target, min_gap, min_distance,
               headless=False) -> int:
    import cv2

    cap = cv2.VideoCapture(cam_index)
    if not cap.isOpened():
        print("Could not open the camera.")
        print("  Check: another app is using it, OS camera permission, or try --camera 1.")
        return 2

    det = HandDetector()
    counts, idx, saved = _counts(), 0, 0
    last_feat = _last_features()
    history: deque = deque(maxlen=STABLE_FRAMES)
    last_capture: dict[str, float] = {}
    session_counts: dict[str, int] = {}
    frames = 0

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("Camera stopped delivering frames.")
                break

            label = labels[idx]
            result = det.detect(bgr_to_rgb(frame))  # OpenCV BGR -> RGB for MediaPipe
            view = cv2.flip(frame, 1)  # mirror the PREVIEW only; features come from the raw frame

            ready = False
            if result.status == "ok":
                history.append(result.features)
                frac = _hand_fraction(result.features)
                if frac < MIN_HAND_FRACTION:
                    status = "hand too small - move closer"
                    colour = (0, 0, 220)
                elif not _is_stable(history):
                    status = "hold the pose still..."
                    colour = (0, 165, 255)
                else:
                    ready = True
                    status = "READY - press SPACE to capture"
                    colour = (0, 200, 0)
            else:
                history.clear()
                status = {"no_hand": "no hand detected",
                          "multiple_hands": "show only ONE hand"}.get(result.status, result.status)
                colour = (0, 0, 220)

            hdr = f"[{idx + 1}/{len(labels)}] {label}   this session: {session_counts.get(label, 0)}/{target}"
            frames += 1
            if headless:
                # No keyboard in headless mode: report occasionally and capture
                # automatically once the pose is stable.
                if frames % 15 == 0:
                    print(f"\r{label:12s} {status}", end="", flush=True)
                if ready and time.monotonic() - last_capture.get(label, -99) >= min_gap:
                    prev = last_feat.get(label)
                    if prev is None or float(np.linalg.norm(result.features - prev)) >= min_distance:
                        append_rows([new_row(label, result.features, signer, session, condition, result.hand_side)])
                        last_feat[label] = result.features
                        last_capture[label] = time.monotonic()
                        session_counts[label] = session_counts.get(label, 0) + 1
                        counts[label] = counts.get(label, 0) + 1
                        saved += 1
                        history.clear()
                        if session_counts[label] >= target:
                            idx = (idx + 1) % len(labels)
                            if all(session_counts.get(lab, 0) >= target for lab in labels):
                                print("\nAll target samples collected.")
                                break
                continue
            cv2.putText(view, hdr, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(view, status, (10, 64), cv2.FONT_HERSHEY_SIMPLEX, 0.6, colour, 2)
            cv2.putText(view, "SPACE=capture  N/P=sign  R=resample  Q=quit", (10, 94),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (230, 230, 230), 1)
            cv2.imshow("Sanket Setu - collect", view)
            key = cv2.waitKey(1) & 0xFF

            if key in (ord("q"), 27):
                break
            if key == ord("n"):
                idx = (idx + 1) % len(labels)
                history.clear()
            elif key == ord("p"):
                idx = (idx - 1) % len(labels)
                history.clear()
            elif key == ord("r"):
                history.clear()  # discard the stability window, e.g. after repositioning
            elif key == ord(" "):
                if not ready:
                    print(f"\nNot saved: {status}")
                    continue
                now = time.monotonic()
                if now - last_capture.get(label, -99) < min_gap:
                    print(f"\nNot saved: wait {min_gap}s between samples of the same sign.")
                    continue
                prev = last_feat.get(label)
                if prev is not None:
                    dist = float(np.linalg.norm(result.features - prev))
                    if dist < min_distance:
                        print(f"\nNot saved: too similar to your last '{label}' sample "
                              f"(distance {dist:.3f} < {min_distance}). Reposition slightly first.")
                        continue
                append_rows([new_row(label, result.features, signer, session, condition, result.hand_side)])
                last_feat[label] = result.features
                last_capture[label] = now
                session_counts[label] = session_counts.get(label, 0) + 1
                counts[label] = counts.get(label, 0) + 1
                saved += 1
                history.clear()
                if session_counts[label] >= target:
                    print(f"\nTarget reached for '{label}' ({target}). Moving to the next sign.")
                    idx = (idx + 1) % len(labels)
    finally:
        cap.release()
        if not headless:
            cv2.destroyAllWindows()
        det.close()

    print(f"\nSaved {saved} sample(s) to {DATA_CSV}")
    print("Session summary:")
    for lab in labels:
        n = session_counts.get(lab, 0)
        print(f"  {lab:12s} {n:4d} / {target}" + ("   [target met]" if n >= target else ""))
    print("\nNext step (run this once you have data from 3 or more signers):")
    print("  python -m sanket_setu.train_model")
    return 0


def show_status(signer: str = "") -> None:
    """Print what has been collected so far."""
    counts = _counts()
    if not counts:
        print("No samples collected yet.")
        return
    print("Samples per label (all signers):")
    for k, v in sorted(counts.items()):
        print(f"  {k:12s} {v}")
    if DATA_CSV.exists():
        df = pd.read_csv(DATA_CSV, usecols=["signer_id", "session_id"])
        signers = df.groupby("signer_id")["session_id"].nunique()
        print(f"\nSigners: {len(signers)}")
        for s, sessions in signers.items():
            print(f"  {s:12s} {sessions} session(s)")
        if len(signers) < 3:
            print("\n  WARNING: fewer than 3 signers. Training will mark cross-person")
            print("  generalization as UNVALIDATED. Collect from at least 3 people.")
    if ROSTER.exists():
        print(f"\nRoster ({ROSTER.name}):")
        with open(ROSTER, encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                print("  " + " | ".join(f"{k}={v}" for k, v in row.items() if v))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--signer", help="pseudonymous signer id, e.g. S01")
    ap.add_argument("--session", default=date.today().isoformat())
    ap.add_argument("--condition", default="unspecified",
                    help="capture condition tag, e.g. indoor_bright_plain_bg_50cm")
    ap.add_argument("--camera", type=int, default=0)
    ap.add_argument("--target", type=int, default=20, help="samples to collect per sign in this session")
    ap.add_argument("--min-gap", type=float, default=MIN_GAP_SEC, help="min seconds between samples")
    ap.add_argument("--min-distance", type=float, default=MIN_DISTANCE,
                    help="min landmark distance between consecutive samples of the same sign")
    ap.add_argument("--labels", help="comma-separated subset of sign ids to capture")
    ap.add_argument("--headless", action="store_true", help="no preview window (SSH / no display)")
    ap.add_argument("--import-dir", nargs="?", const=str(RAW_DIR),
                    help="import data/raw_images/<class>/* instead of using the camera")
    ap.add_argument("--status", action="store_true", help="show what has been collected and exit")
    args = ap.parse_args(argv)

    if args.status:
        show_status(args.signer or "")
        return 0

    if not args.signer:
        ap.error("--signer is required (pseudonymous id such as S01)")
    if not args.signer.replace("_", "").replace("-", "").isalnum():
        ap.error("--signer must be alphanumeric; do not put real names in the data")

    _, signs = load_signs()
    labels = [s.id for s in trainable(signs)]
    if args.labels:
        want = [x.strip() for x in args.labels.split(",") if x.strip()]
        unknown = [x for x in want if x not in labels]
        if unknown:
            print(f"Unknown or disabled sign id(s): {unknown}\nEnabled signs: {labels}")
            return 1
        labels = want

    if args.import_dir:
        print(CONSENT)
        if input("Continue? [y/N] ").strip().lower() != "y":
            print("No consent confirmed. Nothing recorded.")
            return 1
        det = HandDetector()
        try:
            rows, report = import_folder(args.import_dir, labels, det, args.signer, args.session)
        finally:
            det.close()
        append_rows(rows)
        register_signer(args.signer, args.session, args.condition, "imported images")
        print(f"Imported {len(rows)} samples. Report: {report}")
        return 0

    print(CONSENT)
    if input("Continue? [y/N] ").strip().lower() != "y":
        print("No consent confirmed. Nothing recorded.")
        return 1

    register_signer(args.signer, args.session, args.condition)
    print(f"\nSign {args.signer} | session {args.session} | condition '{args.condition}'")
    print(f"Capturing {len(labels)} sign(s), {args.target} samples each: {', '.join(labels)}\n")
    try:
        return run_camera(labels, args.signer, args.session, args.condition, args.camera, args.target,
                          args.min_gap, args.min_distance, args.headless)
    except KeyboardInterrupt:
        print("\nInterrupted. Samples already saved are kept.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
