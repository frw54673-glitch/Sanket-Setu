"""Image -> normalised 63-d hand feature vector. Shared by collection, training and inference.

Colour contract: MediaPipe wants RGB. OpenCV frames are BGR -> bgr_to_rgb().
PIL images -> pil_to_rgb() (already RGB, never convert to BGR).
Mirroring: features are NOT mirrored. hand_side is stored as metadata only.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageOps

from .config import N_FEATURES


def normalize(points) -> np.ndarray:
    """Translate so the wrist is the origin, scale by wrist->middle-finger-MCP distance."""
    pts = np.asarray(points, dtype=float)
    if pts.shape != (21, 3) or not np.isfinite(pts).all():
        raise ValueError("Expected 21 finite (x, y, z) landmarks.")
    rel = pts - pts[0]
    scale = float(np.linalg.norm(rel[9]))
    if scale < 1e-6:
        raise ValueError("Degenerate hand (zero size).")
    feats = (rel / scale).ravel()
    assert feats.shape == (N_FEATURES,)
    return feats


def bgr_to_rgb(frame: np.ndarray) -> np.ndarray:
    return np.ascontiguousarray(frame[:, :, ::-1])


def pil_to_rgb(img: Image.Image) -> np.ndarray:
    return np.asarray(ImageOps.exif_transpose(img).convert("RGB"))


@dataclass
class Detection:
    status: str  # ok | no_hand | multiple_hands
    features: np.ndarray | None = None
    hand_side: str | None = None
    points: np.ndarray | None = None  # raw (21, 3) image-space landmarks, for drawing
    hands: list["HandObservation"] | None = None


@dataclass
class HandObservation:
    """Landmarks for one hand in a frame, used by live tracking."""
    features: np.ndarray
    hand_side: str
    points: np.ndarray


class HandDetector:
    """Real-time MediaPipe tracker. Returns both hands while preserving single-hand callers."""

    def __init__(self, min_confidence: float = 0.5, static_image_mode: bool = True):
        try:
            import mediapipe as mp

            self._hands = mp.solutions.hands.Hands(
                static_image_mode=static_image_mode, max_num_hands=2,
                min_detection_confidence=min_confidence, min_tracking_confidence=0.45
            )
        except (ImportError, AttributeError) as exc:
            raise RuntimeError(
                "MediaPipe with the 'solutions' API is required. Install the pinned version: "
                "pip install -r requirements.txt"
            ) from exc

    def detect(self, rgb: np.ndarray) -> Detection:
        res = self._hands.process(np.ascontiguousarray(rgb))
        if not res.multi_hand_landmarks:
            return Detection("no_hand", hands=[])
        observations = []
        for index, hand in enumerate(res.multi_hand_landmarks):
            pts = np.array([[p.x, p.y, p.z] for p in hand.landmark], dtype=float)
            side = res.multi_handedness[index].classification[0].label
            observations.append(HandObservation(normalize(pts), side, pts))
        if len(observations) > 1:
            return Detection("multiple_hands", hands=observations)
        hand = observations[0]
        return Detection("ok", hand.features, hand.hand_side, hand.points, observations)

    def close(self) -> None:
        self._hands.close()
