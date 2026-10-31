"""Extensive test suite for the enhanced production backend endpoints."""
import base64
import cv2
from fastapi.testclient import TestClient
import numpy as np
import pytest

from sanket_setu.live_server import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_system_health_and_scorecard(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["version"] == "2.0.0"
    assert "active_desk_sessions" in data

    score = client.get("/api/scorecard").json()
    assert score["available"] is True
    assert "test_accuracy" in score
    assert "macro_f1" in score
    assert "per_class" in score

    # Test simulator page
    sim = client.get("/simulator")
    assert sim.status_code == 200
    assert "Hackathon Counter Simulator" in sim.text

    # Test benchmarks endpoint
    bench = client.get("/api/benchmarks").json()
    assert bench["status"] == "ok"
    assert bench["mean_latency_ms"] > 0
    assert bench["n_estimators"] == 500
    assert bench["dataset_samples"] == 2880
    assert bench["signer_count"] == 8


def test_vocabulary_and_phrases_endpoints(client):
    vocab = client.get("/api/vocabulary").json()
    assert "signs" in vocab
    assert len(vocab["signs"]) >= 5
    first_sign = vocab["signs"][0]
    assert "id" in first_sign
    assert "text_hi" in first_sign
    assert "text_en" in first_sign
    assert "source_url" in first_sign

    # Single sign lookup
    detail = client.get(f"/api/vocabulary/{first_sign['id']}").json()
    assert detail["id"] == first_sign["id"]
    assert "checklist" in detail

    # 404 for unknown sign
    assert client.get("/api/vocabulary/non_existent_sign").status_code == 404

    # Phrases
    phrases = client.get("/api/phrases").json()
    assert "staff_phrases" in phrases
    assert "visitor_phrases" in phrases
    assert phrases["emergency_number"] == "112"


def test_recognize_landmarks_endpoint(client):
    # Simulated 21 landmarks for an open hand (num_5)
    pts = np.zeros((21, 3))
    pts[0] = [0.5, 0.8, 0.0]  # wrist
    pts[1] = [0.46, 0.73, -0.01]
    pts[2] = [0.42, 0.67, -0.02]
    pts[3] = [0.35, 0.61, -0.03]
    pts[4] = [0.28, 0.55, -0.04]  # thumb tip (spread)
    for i, mx in enumerate([0.46, 0.50, 0.54, 0.58]):
        b = 5 + i * 4
        pts[b] = [mx, 0.55, -0.01]
        pts[b + 1] = [mx - 0.01, 0.45, -0.02]
        pts[b + 2] = [mx - 0.01, 0.37, -0.03]
        pts[b + 3] = [mx - 0.01, 0.29, -0.04]  # extended

    # Test ML engine
    res_ml = client.post("/api/recognize/landmarks", json={
        "points": pts.tolist(),
        "engine": "ml"
    })
    assert res_ml.status_code == 200
    data_ml = res_ml.json()
    assert data_ml["status"] == "recognized"
    assert data_ml["label"] == "num_5"
    assert data_ml["text_hi"] == "पाँच"
    assert data_ml["text_en"] == "Five"
    assert data_ml["score"] >= 0.6

    # Test Model Inspect endpoint
    inspect_res = client.post("/api/model/inspect", json={
        "points": pts.tolist(),
        "engine": "ml"
    }).json()
    assert inspect_res["top_class"] == "num_5"
    assert "probabilities" in inspect_res
    assert inspect_res["confidence"] >= 0.6

    # Test Geometric engine
    res_geo = client.post("/api/recognize/landmarks", json={
        "points": pts.tolist(),
        "engine": "geometric"
    })
    assert res_geo.status_code == 200
    data_geo = res_geo.json()
    assert data_geo["status"] == "recognized"
    assert data_geo["label"] == "num_5"

    # Test invalid dimensions
    bad = client.post("/api/recognize/landmarks", json={
        "points": [[0.1, 0.2]],
        "engine": "ml"
    })
    assert bad.status_code == 400


def test_new_universal_gestures(client):
    from tests.test_geometric import make_hand

    # 1. Test ILY gesture: thumb, index, pinky extended
    ily_pts = make_hand({5, 17}, thumb_out=True)
    res_ily = client.post("/api/recognize/landmarks", json={
        "points": ily_pts.tolist(),
        "engine": "geometric"
    }).json()
    assert res_ily["status"] == "recognized"
    assert res_ily["label"] == "gesture_ily"
    assert "I Love You" in res_ily["text_en"]

    # 2. Test Rock On gesture: index, pinky extended, thumb folded
    rock_pts = make_hand({5, 17}, thumb_out=False)
    res_rock = client.post("/api/recognize/landmarks", json={
        "points": rock_pts.tolist(),
        "engine": "geometric"
    }).json()
    assert res_rock["status"] == "recognized"
    assert res_rock["label"] == "gesture_rock_on"
    assert "Rock on" in res_rock["text_en"]


def test_recognize_frame_and_image_upload(client):
    # Create a small valid JPEG with synthetic hand drawing
    img = np.zeros((240, 320, 3), dtype=np.uint8)
    img[40:200, 80:240] = 180  # hand blob
    _, encoded = cv2.imencode(".jpg", img)
    b64_str = base64.b64encode(encoded.tobytes()).decode("ascii")

    # POST frame
    res = client.post("/api/recognize/frame", json={
        "jpeg": b64_str,
        "engine": "geometric"
    })
    assert res.status_code == 200
    # Result could be no_hand or framing depending on synthetic blob
    assert "status" in res.json()

    # POST image upload
    res_upload = client.post(
        "/api/recognize/image",
        files={"file": ("test.jpg", encoded.tobytes(), "image/jpeg")},
        data={"engine": "geometric"}
    )
    assert res_upload.status_code == 200
    assert "status" in res_upload.json()


def test_paired_desk_sessions_lifecycle(client):
    # 1. Create a session
    created = client.post("/api/sessions", json={
        "session_id": "TEST-DESK-99",
        "counter_name": "Emergency Desk",
        "operator_name": "Doctor Sharma"
    }).json()
    assert created["session_id"] == "TEST-DESK-99"
    assert created["counter_name"] == "Emergency Desk"

    # 2. List sessions
    sessions_list = client.get("/api/sessions").json()["sessions"]
    assert any(s["session_id"] == "TEST-DESK-99" for s in sessions_list)

    # 3. Post visitor message
    msg_visitor = client.post("/api/sessions/TEST-DESK-99/messages", json={
        "role": "visitor",
        "text_hi": "मुझे दवाई चाहिए।",
        "text_en": "I need medicine.",
        "category": "sign_reading",
        "sign_id": "num_2",
        "confidence": 0.95
    }).json()
    assert msg_visitor["status"] == "ok"
    assert msg_visitor["message"]["role"] == "visitor"

    # 4. Post staff reply
    msg_staff = client.post("/api/sessions/TEST-DESK-99/messages", json={
        "role": "staff",
        "text_hi": "कृपया थोड़ा इंतज़ार करें।",
        "text_en": "Please wait a moment.",
        "category": "phrase_board"
    }).json()
    assert msg_staff["status"] == "ok"
    assert msg_staff["message"]["role"] == "staff"

    # 5. Fetch timeline
    timeline = client.get("/api/sessions/TEST-DESK-99/messages").json()
    assert len(timeline["messages"]) == 2

    # 6. Export transcript
    export_res = client.get("/api/sessions/TEST-DESK-99/export")
    assert export_res.status_code == 200
    assert "Emergency Desk" in export_res.text
    assert "मुझे दवाई चाहिए।" in export_res.text
    assert "Please wait a moment." in export_res.text

    # 7. Clear transcript
    clear_res = client.post("/api/sessions/TEST-DESK-99/clear").json()
    assert clear_res["status"] == "ok"
    timeline_after = client.get("/api/sessions/TEST-DESK-99/messages").json()
    assert len(timeline_after["messages"]) == 0


def test_session_websocket_realtime_sync(client):
    with client.websocket_connect("/ws/session/SYNC-TEST-01") as ws:
        # Initial greeting event
        init_evt = ws.receive_json()
        assert init_evt["type"] == "init"
        assert init_evt["session_id"] == "SYNC-TEST-01"

        # Ping
        ws.send_json({"type": "ping"})
        pong = ws.receive_json()
        assert pong["type"] == "pong"

        # Post message over websocket
        ws.send_json({
            "type": "message",
            "role": "visitor",
            "text_hi": "नमस्ते",
            "text_en": "Hello",
            "category": "greeting"
        })
        msg_evt = ws.receive_json()
        assert msg_evt["type"] == "message"
        assert msg_evt["message"]["text_hi"] == "नमस्ते"


def test_signers_roster_endpoints(client):
    signers = client.get("/api/signers").json()["signers"]
    assert isinstance(signers, list)
    assert len(signers) >= 4  # S01, S02, S03, S04 seeded

    # Register new signer
    reg = client.post("/api/signers", json={
        "signer_id": "S99",
        "session_id": "session_1",
        "condition": "indoor_test",
        "consent": True,
        "notes": "Automated test signer"
    }).json()
    assert reg["status"] == "registered"
    assert reg["signer_id"] == "S99"

