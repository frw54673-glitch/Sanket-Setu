"""Tests for the geometric baseline engine.

The hands here are built from joint geometry, not from recorded video: extended fingers are
collinear at the PIP joint, curled fingers fold back toward the palm. That is enough to
exercise the extension test, the counting and the sign mapping.
"""
import numpy as np
import pytest

from sanket_setu.config import load_signs
from sanket_setu.geometric import analyse_landmarks, describe, label_for_count, read
from sanket_setu.inference import GeometricPredictor

MCP_X = {5: -0.30, 9: 0.0, 13: 0.28, 17: 0.52}


def make_hand(extended: set, thumb_out: bool = True) -> np.ndarray:
    """21x3 landmarks. `extended` holds the MCP ids of fingers held straight up."""
    pts = np.zeros((21, 3), dtype=float)
    pts[0] = (0.0, 0.0, 0.0)  # wrist
    for mcp, x in MCP_X.items():
        pip, dip, tip = mcp + 1, mcp + 2, mcp + 3
        pts[mcp] = (x, -1.0, 0.0)
        if mcp in extended:
            pts[pip] = (x, -1.5, 0.0)
            pts[dip] = (x, -2.0, 0.0)
            pts[tip] = (x, -2.4, 0.0)
        else:
            pts[pip] = (x, -1.3, 0.0)
            pts[dip] = (x, -0.4, 0.0)
            pts[tip] = (x, 0.3, 0.0)
    # thumb: straight out sideways when extended, folded across the palm otherwise
    if thumb_out:
        pts[1], pts[2], pts[3], pts[4] = (-0.45, -0.30, 0.0), (-0.75, -0.35, 0.0), (-1.0, -0.40, 0.0), (-1.2, -0.45, 0.0)
    else:
        pts[1], pts[2], pts[3], pts[4] = (-0.45, -0.30, 0.0), (-0.50, -0.50, 0.0), (-0.30, -0.60, 0.0), (-0.10, -0.62, 0.0)
    return pts


@pytest.mark.parametrize("count,expected", [(0, "none"), (1, "num_1"), (2, "num_2"),
                                            (3, "num_3"), (4, "num_4"), (5, "num_5")])
def test_counts_extended_fingers(count, expected):
    """Four is four fingers with the thumb folded; five is all five digits out."""
    ids = [5, 9, 13, 17]
    extended = set(ids[:min(count, 4)])
    thumb_out = count == 5
    r = analyse_landmarks(make_hand(extended, thumb_out=thumb_out))
    assert r.count == count
    assert r.status == "ok"


def test_thumb_decides_between_four_and_five():
    """All four fingers up is ambiguous until the thumb is read."""
    four = analyse_landmarks(make_hand({5, 9, 13, 17}, thumb_out=False))
    five = analyse_landmarks(make_hand({5, 9, 13, 17}, thumb_out=True))
    assert four.count == 4
    assert five.count == 5
    assert four.finger_states["thumb"]["extended"] is False
    assert five.finger_states["thumb"]["extended"] is True


def test_read_maps_count_to_configured_sign():
    _, signs = load_signs()
    by_id = {s.id: s for s in signs}
    r = read(make_hand({5}), by_id)          # index only -> one
    assert r.status == "ok" and r.label == "num_1" and r.sign.text_hi == "एक"
    r = read(make_hand({5, 9, 13}), by_id)   # three extended -> three
    assert r.label == "num_3" and r.sign.text_en == "Three"


def test_relaxed_hand_is_not_a_supported_sign():
    _, signs = load_signs()
    by_id = {s.id: s for s in signs}
    r = read(make_hand(set()), by_id)
    assert r.status == "unsupported_sign"
    assert "no fingers were extended" in r.message.lower()


def test_count_without_a_configured_sign_is_refused():
    _, signs = load_signs()
    by_id = {s.id: s for s in signs}
    # num_6 does not exist in the vocabulary, so six fingers must not be forced onto a label
    assert label_for_count(6, by_id) is None
    assert label_for_count(2, by_id).id == "num_2"


def test_disabled_signs_are_never_produced():
    _, signs = load_signs()
    by_id = {s.id: s for s in signs}
    for s in signs:
        if not s.enabled:
            assert label_for_count(0, by_id) is not s


def test_describe_is_human_readable():
    r = analyse_landmarks(make_hand({5, 9}))
    d = describe(r)
    assert "index" in d and "middle" in d and "2 of 4" in d


def test_predictor_reports_engine_and_no_fake_score():
    pred = GeometricPredictor()
    assert pred.ready
    res = pred.predict_points(make_hand({5}))
    assert res.status == "recognized" and res.engine == "geometric"
    assert res.score is None          # a rule-based reading has no confidence score
    assert res.sign.id == "num_1"


def test_thumbs_up_returns_confirmable_everyday_meaning():
    points = make_hand(set(), thumb_out=False)
    points[2] = (-0.40, -0.30, 0.0)
    points[4] = (-0.40, -1.20, 0.0)
    res = GeometricPredictor().predict_points(points)
    assert res.status == "recognized"
    assert res.sign.id == "gesture_thumbs_up"
    assert res.sign.text_hi == "मैं ठीक हूँ।"
    assert res.sign.text_en == "I'm okay."
    assert "confirm" in res.message.lower() and "not ISL" in res.message


def test_thumbs_down_suggests_disapproval_not_health_status():
    points = make_hand(set(), thumb_out=False)
    points[2] = (-0.40, -0.30, 0.0)
    points[4] = (-0.40, 0.70, 0.0)
    res = GeometricPredictor().predict_points(points)
    assert res.status == "recognized"
    assert res.sign.id == "gesture_thumbs_down"
    assert res.sign.text_hi == "मुझे यह ठीक नहीं लगता।"
    assert res.sign.text_en == "I don't think this is okay."
    assert "disapproval" in res.message.lower()
    assert "confirm" in res.message.lower() and "not ISL" in res.message


def test_predictor_refuses_unrecognised_hand():
    pred = GeometricPredictor()
    res = pred.predict_points(make_hand(set()))
    assert res.status == "unsupported_sign" and res.engine == "geometric"


def test_invalid_landmarks_are_rejected():
    with pytest.raises(ValueError):
        analyse_landmarks(np.zeros((20, 3)))
    with pytest.raises(ValueError):
        analyse_landmarks(np.full((21, 3), np.nan))
