"""Boundary checks for the local browser camera service."""

from fastapi.testclient import TestClient

from sanket_setu.live_server import _frame_guidance, app


def test_health_page_and_walkthrough_assets():
    with TestClient(app) as client:
        assert client.get("/health").json()["status"] == "ok"
        page = client.get("/")
        assert page.status_code == 200
        assert "Sanket Setu" in page.text
        assert "wss:" in page.text
        assert 'href="tel:112"' in page.text
        assert "Call emergency services?" in page.text
        assert 'id="setupButton"' in page.text
        assert 'class="phrase-filter" data-filter="needs"' in page.text
        assert 'class="phrase-filter" data-filter="care"' in page.text
        assert 'class="phrase-filter" data-filter="urgent"' in page.text
        assert client.get("/assets/sanket-setu-mark.svg").status_code == 200
        assert client.head("/assets/sanket-setu-walkthrough.mp4").status_code == 200
        for asset in (
            "/assets/sanket-setu-polish.css?v=3",
            "/assets/sanket-setu-walkthrough-poster.jpg",
            "/assets/sanket-setu-walkthrough.vtt",
            "/assets/sanket-setu-walkthrough-hi.vtt",
        ):
            assert client.get(asset).status_code == 200, asset
        assert client.get("/sw.js").headers["service-worker-allowed"] == "/"
        assert client.get("/manifest.webmanifest").json()["display"] == "standalone"
        diagnostics = client.get("/api/diagnostics").json()
        assert diagnostics["status"] == "ok"
        assert "geometric_available" in diagnostics
        assert diagnostics["trainable_signs"]
        assert diagnostics["recommended_signers"] == 3
        assert "scorecard" in diagnostics
        assert client.get("/api/signs").json()["signs"]
        if diagnostics["sample_count"] == 0:
            assert client.post("/api/train").status_code == 409


def test_speech_rejects_empty_or_unsupported_requests():
    with TestClient(app) as client:
        assert client.post("/api/speech", json={"text": "", "lang": "hi"}).status_code == 400
        assert client.post("/api/speech", json={"text": "नमस्ते", "lang": "xx"}).status_code == 400
        assert client.post("/api/speech", json={"text": "a" * 281, "lang": "en"}).status_code == 400


def test_websocket_handles_malformed_requests_and_invalid_frames():
    with TestClient(app) as client:
        with client.websocket_connect("/ws/live") as socket:
            socket.send_text("{")
            assert socket.receive_json()["status"] == "error"

            socket.send_json([])
            assert socket.receive_json()["status"] == "error"

            socket.send_json({"type": "configure", "engine": "geometric"})
            assert socket.receive_json()["model_ready"] is True

            socket.send_json({"type": "frame", "engine": "geometric", "jpeg": "AAAA"})
            assert socket.receive_json()["status"] == "error"

            socket.send_json({"type": "frame", "engine": [], "jpeg": "AAAA"})
            assert socket.receive_json()["status"] == "error"


def test_frame_guidance_distinguishes_small_clipped_and_framed_hands():
    import numpy as np

    small = np.tile(np.array([0.48, 0.48, 0.0]), (21, 1))
    small[:, 0] += np.linspace(-0.04, 0.04, 21)
    small[:, 1] += np.linspace(-0.05, 0.05, 21)
    assert _frame_guidance(small) == "small"

    clipped = np.tile(np.array([0.5, 0.5, 0.0]), (21, 1))
    clipped[4, 0] = 0.003
    assert _frame_guidance(clipped) == "clipped"

    clear = np.tile(np.array([0.5, 0.5, 0.0]), (21, 1))
    clear[:, 0] += np.linspace(-0.18, 0.18, 21)
    clear[:, 1] += np.linspace(-0.25, 0.25, 21)
    assert _frame_guidance(clear) is None
