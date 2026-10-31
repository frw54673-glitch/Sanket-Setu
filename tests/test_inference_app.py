import json
import sys
from pathlib import Path

import pytest

from sanket_setu.inference import Predictor
from sanket_setu.speech import SpeechUnavailable, synthesize
from sanket_setu.train_model import train

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def trained(synth, tmp_path):
    df, protos = synth
    train(df, "test", n_estimators=20, model_path=tmp_path / "m.joblib", meta_path=tmp_path / "meta.json", report_dir=tmp_path / "r")
    return Predictor(tmp_path / "m.joblib", tmp_path / "meta.json"), protos, tmp_path


def test_model_not_ready(tmp_path):
    p = Predictor(tmp_path / "x.joblib", tmp_path / "y.json")
    assert not p.ready
    r = p.predict_features([0.0] * 63)
    assert r.status == "model_not_ready" and "train_model" in r.message


def test_recognized_and_low_score_and_none(trained):
    p, protos, _ = trained
    r = p.predict_features(protos["num_1"])
    assert r.status == "recognized" and r.label == "num_1" and r.sign.text_hi == "एक"
    p.threshold = 1.01
    assert p.predict_features(protos["num_1"]).status == "low_score"
    p.threshold = 0.0
    assert p.predict_features(protos["none"]).status == "unsupported_sign"


def test_bad_feature_vector(trained):
    assert trained[0].predict_features([0.0] * 5).status == "unsupported_sign"


def test_class_order_mismatch_is_not_ready(trained):
    _, _, tmp = trained
    meta = json.loads((tmp / "meta.json").read_text())
    meta["class_order"] = list(reversed(meta["class_order"]))
    (tmp / "meta.json").write_text(json.dumps(meta))
    assert not Predictor(tmp / "m.joblib", tmp / "meta.json").ready


def test_corrupt_model_is_not_ready(tmp_path):
    (tmp_path / "m.joblib").write_bytes(b"junk")
    (tmp_path / "meta.json").write_text("{}")
    assert not Predictor(tmp_path / "m.joblib", tmp_path / "meta.json").ready


def test_speech_falls_back(monkeypatch):
    monkeypatch.setitem(sys.modules, "gtts", None)
    with pytest.raises(SpeechUnavailable):
        synthesize("नमस्ते")


def test_app_boots_without_model():
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(ROOT / "app" / "streamlit_app.py"), default_timeout=60).run()
    assert not at.exception
    for page in ["Staff mode", "Supported signs", "Model status", "Signer mode"]:
        at.radio[0].set_value(page).run()
        assert not at.exception, page
