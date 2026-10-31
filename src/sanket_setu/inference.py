"""One shared predictor for the app (and any local runner).

Two engines, both honest about what they are:

``Predictor`` (engine "ml")
    The trained RandomForest over collected landmarks. Requires a real, consented
    dataset. Returns a *model score* from the forest, which is NOT accuracy.

``GeometricPredictor`` (engine "geometric")
    A rule-based baseline that reads the number of extended fingers straight from the
    landmarks. It needs no training data, so it works on real hands from day one, but it
    covers the iconic numeral signs and a few explicitly labelled common camera gestures;
    it has no notion of confidence. It is
    labelled as a geometric baseline everywhere it appears - never as a trained model.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

import joblib
import numpy as np

from .config import META_PATH, MODEL_PATH, N_FEATURES, NONE_LABEL, Sign, load_signs
from .geometric import GeometricReading, describe, detect_common_gesture, read
from .landmarks import HandDetector, pil_to_rgb

log = logging.getLogger("sanket_setu")

LOW_SCORE_MSG = "Sign not confidently recognized. Please try again or choose a phrase manually."
TRAIN_HELP = ("Model not trained yet. 1) python -m sanket_setu.collect_data --signer S01   "
              "2) python -m sanket_setu.train_model")
GEOMETRIC_HELP = ("Geometric baseline: reads numerals and a few common camera gestures from hand "
                  "landmarks. It is not a trained model.")


@dataclass
class Result:
    status: str  # recognized | low_score | no_hand | unsupported_sign | model_not_ready
    message: str = ""
    label: str | None = None
    score: float | None = None
    top: list = field(default_factory=list)
    sign: Sign | None = None
    engine: str = "ml"          # ml | geometric
    detail: str = ""            # engine-specific explanation, e.g. which fingers were extended


class Predictor:
    def __init__(self, model_path=MODEL_PATH, meta_path=META_PATH, signs: list[Sign] | None = None, detector=None):
        self.signs = {s.id: s for s in (signs or load_signs()[1])}
        self._detector = detector
        self.model = self.meta = None
        self.reason = ""
        self.threshold = 1.0
        self._load(model_path, meta_path)

    @property
    def ready(self) -> bool:
        return self.model is not None

    def _load(self, model_path, meta_path) -> None:
        if not model_path.exists() or not meta_path.exists():
            self.reason = TRAIN_HELP
            return
        try:
            model = joblib.load(model_path)
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            log.exception("model load failed")
            self.reason = "Model files are corrupted. Re-run: python -m sanket_setu.train_model"
            return
        if meta.get("feature_schema", {}).get("n_features") != N_FEATURES or list(model.classes_) != meta.get("class_order"):
            self.reason = "Model and metadata do not match the current feature schema/class order. Re-train."
            return
        if set(meta["class_order"]) - set(self.signs):
            self.reason = "Model has classes missing from configs/signs.json. Re-train."
            return
        self.model, self.meta, self.threshold = model, meta, float(meta["reject_threshold"])

    def predict_features(self, feats) -> Result:
        if not self.ready:
            return Result("model_not_ready", self.reason)
        x = np.asarray(feats, float).reshape(1, -1)
        if x.shape[1] != N_FEATURES or not np.isfinite(x).all():
            return Result("unsupported_sign", "Could not read the hand shape. Try again.")
        proba = self.model.predict_proba(x)[0]
        order = np.argsort(proba)[::-1]
        classes = self.meta["class_order"]  # saved order, never dict order
        top = [(classes[i], float(proba[i])) for i in order[:3]]
        label, score = top[0]
        if score < self.threshold:
            return Result("low_score", LOW_SCORE_MSG, label, score, top)
        if label == NONE_LABEL:
            return Result("unsupported_sign", "A hand was seen, but not one of the supported signs.", label, score, top)
        return Result("recognized", "", label, score, top, self.signs[label])

    def predict_image(self, img) -> Result:
        if not self.ready:
            return Result("model_not_ready", self.reason)
        try:
            if self._detector is None:
                self._detector = HandDetector()
            det = self._detector.detect(pil_to_rgb(img))
        except Exception:
            log.exception("image processing failed")
            return Result("unsupported_sign", "This image could not be processed. Try another photo.")
        if det.status == "no_hand":
            return Result("no_hand", "No hand found. Keep one hand fully visible, in good light.")
        if det.status == "multiple_hands":
            return Result("unsupported_sign", "More than one hand found. This prototype reads one hand only.")
        return self.predict_features(det.features)


class GeometricPredictor:
    """Rule-based baseline for numerals and a few non-ISL common gesture labels."""

    engine = "geometric"

    def __init__(self, signs: list[Sign] | None = None, detector=None):
        self.signs = {s.id: s for s in (signs or load_signs()[1])}
        self._detector = detector
        self.reason = GEOMETRIC_HELP

    @property
    def ready(self) -> bool:
        return True

    def _detect(self, img):
        if self._detector is None:
            self._detector = HandDetector()
        return self._detector.detect(pil_to_rgb(img))

    def predict_points(self, points) -> Result:
        try:
            gesture = detect_common_gesture(points)
        except ValueError as exc:
            return Result("unsupported_sign", f"Could not read the hand shape: {exc}", engine=self.engine)
        if gesture:
            gesture_data = {
                # This is an informal, user-confirmable interpretation of a common gesture,
                # not a claim that thumbs-up is a validated ISL sign.
                "thumbs_up": (
                    "Thumbs up · informal meaning", "मैं ठीक हूँ।", "I'm okay.",
                    "Informal thumbs-up interpretation · please confirm with the visitor · not ISL",
                ),
                "thumbs_down": (
                    "Thumbs down · informal disapproval", "मुझे यह ठीक नहीं लगता।", "I don't think this is okay.",
                    "Informal thumbs-down reading: disapproval · please confirm with the visitor · not ISL",
                ),
                "ok": (
                    "OK hand gesture", "हाथ का OK इशारा", "OK hand gesture",
                    "Common gesture label · please confirm · not ISL",
                ),
                "ily": (
                    "I Love You · universal sign", "स्नेह / प्यार भरा संकेत (I Love You)", "I Love You (affection)",
                    "Universal sign for love and affection (Thumb + Index + Pinky extended) · please confirm · not ISL",
                ),
                "rock_on": (
                    "Rock on / Horns gesture", "उत्साह / रॉक ऑन (Rock on)", "Rock on / enthusiasm",
                    "Common gesture of horns / enthusiasm (Index + Pinky extended) · please confirm · not ISL",
                ),
                "pinch": (
                    "Pinch gesture · small amount", "थोड़ा सा / ज़रा सा", "A little bit / small quantity",
                    "Pinch gesture indicating small amount or brief time · please confirm · not ISL",
                ),
                "closed_fist": (
                    "Closed fist", "बंद मुट्ठी", "Closed fist",
                    "Pose label only · not an ISL translation",
                ),
                "shaka": (
                    "Shaka · friendly greeting (informal)", "दोस्ती भरा अभिवादन", "Friendly greeting (shaka)",
                    "दोस्ती भरा अनौपचारिक अभिवादन—संदर्भ के अनुसार नमस्ते, अलविदा, धन्यवाद या आराम से का भाव; ISL अनुवाद नहीं · Informal friendly greeting; meaning varies by context; not ISL",
                ),
            }
            label_en, text_hi, text_en, note = gesture_data[gesture]
            sign = Sign(
                id=f"gesture_{gesture}",
                label_en=label_en,
                text_hi=text_hi,
                text_en=text_en,
                sign_type="static_gesture",
                validation_status="demo_only",
                validator="not an ISL translation",
                notes=note,
            )
            return Result("recognized", note, sign.id, None, [], sign, self.engine, label_en)
        try:
            reading: GeometricReading = read(points, self.signs)
        except ValueError as exc:
            return Result("unsupported_sign", f"Could not read the hand shape: {exc}", engine=self.engine)
        detail = describe(reading)
        if reading.status != "ok":
            return Result("unsupported_sign", reading.message, engine=self.engine, detail=detail)
        return Result("recognized", "", reading.label, None, [], reading.sign, self.engine, detail)

    def predict_image(self, img) -> Result:
        try:
            det = self._detect(img)
        except Exception:
            log.exception("geometric image processing failed")
            return Result("unsupported_sign", "This image could not be processed. Try another photo.",
                          engine=self.engine)
        if det.status == "no_hand":
            return Result("no_hand", "No hand found. Keep one hand fully visible, in good light.",
                          engine=self.engine)
        if det.status == "multiple_hands":
            return Result("unsupported_sign", "More than one hand found. This prototype reads one hand only.",
                          engine=self.engine)
        return self.predict_points(det.points)

