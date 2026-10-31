import numpy as np
import pytest
from PIL import Image

from sanket_setu.config import N_FEATURES
from sanket_setu.landmarks import HandDetector, bgr_to_rgb, normalize, pil_to_rgb


def hand(seed=0):
    return np.random.default_rng(seed).uniform(0.1, 0.9, size=(21, 3))


def test_shape_and_finite():
    f = normalize(hand())
    assert f.shape == (N_FEATURES,) and np.isfinite(f).all()


def test_translation_and_scale_invariant():
    h = hand()
    assert np.allclose(normalize(h), normalize(h * 3.5 + 0.2))


@pytest.mark.parametrize("bad", [np.zeros((20, 3)), np.full((21, 3), np.nan), np.zeros((21, 3))])
def test_rejects_bad_landmarks(bad):
    with pytest.raises(ValueError):
        normalize(bad)


def test_bgr_to_rgb_swaps_channels():
    assert bgr_to_rgb(np.array([[[1, 2, 3]]], dtype=np.uint8)).tolist() == [[[3, 2, 1]]]


def test_pil_stays_rgb_and_rgba_ok():
    assert pil_to_rgb(Image.new("RGB", (2, 2), (255, 0, 0)))[0, 0].tolist() == [255, 0, 0]
    assert pil_to_rgb(Image.new("RGBA", (2, 2), (0, 0, 255, 255))).shape == (2, 2, 3)


def test_blank_image_is_no_hand():
    pytest.importorskip("mediapipe")
    det = HandDetector()
    try:
        assert det.detect(np.full((240, 320, 3), 127, dtype=np.uint8)).status == "no_hand"
    finally:
        det.close()
