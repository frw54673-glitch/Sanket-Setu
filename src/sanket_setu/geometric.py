"""Geometric baseline (Engine A): rule-based finger-extension estimation from 21 landmarks.

Why this exists
---------------
The ML classifier (Engine B) needs a consented, verified dataset that does not exist yet.
Without it the app can only show a "model not trained yet" dead end. This module provides a
second, *honest* engine that needs no training data: it measures finger extension directly
from landmark geometry, maps counts to configured numerals, and names a few common hand
poses without claiming that those poses translate to ISL words.

It is deliberately NOT presented as a machine-learning model:
  * no training, no fitted parameters, no accuracy claim, no probability;
  * the result is a deterministic geometric reading, labelled "geometric baseline" in the UI;
  * it can be wrong in ways a trained model would not be (lighting, occlusion, unusual hands).

The finger-extension test is the standard one: a finger counts as extended when the angle at
its PIP joint (proximal interphalangeal) is close to straight, cross-checked against the
tip-to-wrist distance relative to the fully-extended reference for that finger.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from .config import NONE_LABEL, Sign

# MediaPipe hand landmark topology.
WRIST = 0
THUMB = (1, 2, 3, 4)
FINGERS = {
    "index": (5, 6, 7, 8),
    "middle": (9, 10, 11, 12),
    "ring": (13, 14, 15, 16),
    "pinky": (17, 18, 19, 20),
}
# Thumb is excluded from the extension count: ISL numerals one..five are counted on the
# four fingers, and the thumb's position varies too much between signers to count reliably.
COUNTED = ("index", "middle", "ring", "pinky")

# A finger is extended when the angle at the PIP joint is at least this many degrees.
EXTENDED_ANGLE_DEG = 135.0
# ...and when the tip is not tucked back toward the wrist.
TIP_RATIO_MIN = 0.72


@dataclass
class GeometricReading:
    """Result of the geometric baseline for one image."""

    status: str  # ok | no_hand | multiple_hands | unsupported_sign
    count: int | None = None
    finger_states: dict = field(default_factory=dict)
    label: str | None = None
    sign: Sign | None = None
    message: str = ""

    @property
    def is_recognized(self) -> bool:
        return self.status == "ok"


def _angle_deg(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    """Interior angle at b for the chain a-b-c, in degrees."""
    v1, v2 = a - b, c - b
    n1, n2 = np.linalg.norm(v1), np.linalg.norm(v2)
    if n1 < 1e-9 or n2 < 1e-9:
        return 0.0
    cos = float(np.clip(np.dot(v1, v2) / (n1 * n2), -1.0, 1.0))
    return math.degrees(math.acos(cos))


def analyse_landmarks(points) -> GeometricReading:
    """Count extended fingers from raw (21, 3) MediaPipe landmarks."""
    pts = np.asarray(points, dtype=float)
    if pts.shape != (21, 3) or not np.isfinite(pts).all():
        raise ValueError("Expected 21 finite (x, y, z) landmarks.")

    wrist = pts[WRIST]
    states: dict[str, dict] = {}

    for name in COUNTED:
        mcp, pip, dip, tip = (pts[i] for i in FINGERS[name])
        # Angle at the PIP joint: straight finger -> ~180 degrees.
        angle = _angle_deg(mcp, pip, dip)
        # Tip distance from the wrist vs the PIP distance, using the 2D image plane.
        tip_r = float(np.linalg.norm(tip[:2] - wrist[:2]))
        pip_r = float(np.linalg.norm(pip[:2] - wrist[:2]))
        ratio = tip_r / pip_r if pip_r > 1e-9 else 0.0
        extended = angle >= EXTENDED_ANGLE_DEG and ratio >= TIP_RATIO_MIN
        states[name] = {
            "angle_deg": round(angle, 1),
            "tip_ratio": round(ratio, 3),
            "extended": bool(extended),
        }

    # Thumb: extended when it sticks out away from the index MCP.
    t_cmc, t_mcp, t_ip, t_tip = (pts[i] for i in THUMB)
    thumb_angle = _angle_deg(pts[5], t_mcp, t_ip)
    thumb_out = float(np.linalg.norm(t_tip[:2] - pts[5][:2])) / max(
        float(np.linalg.norm(t_mcp[:2] - wrist[:2])), 1e-9
    )
    palm_scale = float(np.linalg.norm(pts[9, :2] - wrist[:2]))
    thumb_spread = float(np.linalg.norm(t_tip[:2] - pts[5, :2])) / max(palm_scale, 1e-9)
    # Use thumb-to-index separation as a third cue. The old angle/reach-only test often
    # dropped a sideways open thumb and reported an open palm as four instead of five.
    thumb_extended = thumb_angle >= 130.0 or thumb_out >= 1.05 or thumb_spread >= 0.58
    states["thumb"] = {
        "angle_deg": round(thumb_angle, 1),
        "reach_ratio": round(thumb_out, 3),
        "extended": bool(thumb_extended),
    }

    count = sum(1 for name in COUNTED if states[name]["extended"])
    # The counted four fingers alone cannot express "five": ISL shows four as four fingers
    # with the thumb folded, and five as all five digits out. So the thumb decides between them.
    if count == 4 and thumb_extended:
        count = 5

    return GeometricReading(status="ok", count=count, finger_states=states)


def label_for_count(count: int, signs: dict[str, Sign]) -> Sign | None:
    """Map an extended-finger count onto the configured numeral sign, if one exists.

    Only ENABLED signs are returned: a sign that is still awaiting interpreter
    confirmation must not be produced by any engine.
    """
    if count <= 0:
        none = signs.get(NONE_LABEL)
        return none if none and none.enabled else None
    sign = signs.get(f"num_{count}")
    if sign is None or not sign.enabled:
        return None
    return sign


def read(points, signs: dict[str, Sign]) -> GeometricReading:
    """Full baseline: analyse landmarks and resolve them to a configured sign."""
    reading = analyse_landmarks(points)
    if reading.status != "ok":
        return reading
    sign = label_for_count(reading.count, signs)
    if sign is None:
        reading.status = "unsupported_sign"
        reading.message = (
            f"{reading.count} extended finger(s) detected, but no sign is configured for that count. "
            "Only static one-hand signs from the vocabulary can be read."
        )
        return reading
    if sign.id == NONE_LABEL:
        reading.status = "unsupported_sign"
        reading.message = "A hand was seen, but no fingers were extended, so this is not one of the supported signs."
        return reading
    reading.label = sign.id
    reading.sign = sign
    return reading


def detect_common_gesture(points) -> str | None:
    """Name a few camera-visible gestures without translating their meaning to ISL."""
    reading = analyse_landmarks(points)
    pts = np.asarray(points, dtype=float)
    states = reading.finger_states
    thumb = states["thumb"]["extended"]
    index = states["index"]["extended"]
    middle = states["middle"]["extended"]
    ring = states["ring"]["extended"]
    pinky = states["pinky"]["extended"]

    # Name an OK pose only when the thumb and index fingertips are close, with the
    # remaining three fingers raised. This is still a gesture label, not a translation.
    palm_scale = float(np.linalg.norm(pts[9, :2] - pts[WRIST, :2]))
    touch_ratio = float(np.linalg.norm(pts[4, :2] - pts[8, :2])) / max(palm_scale, 1e-9)
    if not index and middle and ring and pinky and touch_ratio <= 0.38:
        return "ok"
    if thumb and pinky and not index and not middle and not ring:
        return "shaka"
    if thumb and index and pinky and not middle and not ring:
        return "ily"
    if not thumb and index and pinky and not middle and not ring:
        return "rock_on"
    if not middle and not ring and not pinky and touch_ratio <= 0.38:
        return "pinch"

    # Read vertical thumb direction from the raw tip vector even if the extension
    # threshold was missed; this avoids turning a thumb-down pose into a fist/no-sign.
    thumb_vector = pts[4, :2] - pts[2, :2]
    length = float(np.linalg.norm(thumb_vector))
    if reading.count == 0 and length >= 0.35 * palm_scale and length > 1e-6:
        if abs(float(thumb_vector[1])) / length >= 0.72:
            return "thumbs_up" if thumb_vector[1] < 0 else "thumbs_down"
    if not any((thumb, index, middle, ring, pinky)):
        return "closed_fist"
    return None


def describe(reading: GeometricReading) -> str:
    """Short human-readable breakdown, e.g. 'index, middle extended (2 of 4)'."""
    if reading.status != "ok":
        return ""
    ext = [n for n in COUNTED if reading.finger_states.get(n, {}).get("extended")]
    base = f"{', '.join(ext) if ext else 'none'} extended ({reading.count} of 4)"
    if reading.count == 5:
        base += ", thumb out"
    elif reading.count == 4 and not reading.finger_states.get("thumb", {}).get("extended"):
        base += ", thumb folded"
    return base
