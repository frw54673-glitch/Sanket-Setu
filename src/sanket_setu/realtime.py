"""Local webcam runner.

    python -m sanket_setu.realtime

Runs on YOUR machine against YOUR webcam. It is not the Streamlit app: Streamlit
serves a still snapshot in the browser, this opens a local camera window on the device
and reads continuously. Never describe this as working on a hosted server.

The same shared inference module is used as the Streamlit app, so the two can never
disagree about what a sign means.
"""
from __future__ import annotations

import argparse
import sys
import time

import numpy as np

from .config import load_signs
from .inference import GeometricPredictor, Predictor
from .landmarks import HandDetector, bgr_to_rgb

# MediaPipe hand skeleton, for drawing.
BONES = [(0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8),
         (5, 9), (9, 10), (10, 11), (11, 12), (9, 13), (13, 14), (14, 15), (15, 16),
         (13, 17), (17, 18), (18, 19), (19, 20), (0, 17)]

# A prediction must repeat this many frames in a row before it is accepted, so a single
# noisy frame never flips the reading.
STABLE_FRAMES = 5


def draw(frame, points: np.ndarray, label: str, score: float | None, status: str,
         colour=(0, 220, 0), engine: str = "ml") -> None:
    import cv2

    h, w = frame.shape[:2]
    for a, b in BONES:
        pa = (int(points[a][0] * w), int(points[a][1] * h))
        pb = (int(points[b][0] * w), int(points[b][1] * h))
        cv2.line(frame, pa, pb, colour, 2)
    for x, y in points[:, :2]:
        cv2.circle(frame, (int(x * w), int(y * h)), 3, (255, 180, 60), -1)
    bar = f"{label}"
    if score is not None:
        bar += f"   model score {score:.2f} (not accuracy)"
    if engine == "geometric":
        bar += "   [geometric baseline]"
    cv2.rectangle(frame, (0, 0), (w, 66), (20, 16, 60), -1)
    cv2.putText(frame, bar, (14, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
    cv2.putText(frame, status, (14, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 255), 1)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Local webcam mode (runs on this device only).")
    ap.add_argument("--camera", type=int, default=0)
    ap.add_argument("--engine", choices=["ml", "geometric"], default="ml")
    ap.add_argument("--mirror", action="store_true", help="mirror the preview (selfie view)")
    args = ap.parse_args(argv)

    try:
        import cv2
    except ImportError:
        print("OpenCV is required: pip install opencv-contrib-python")
        return 2

    _, signs = load_signs()
    predictor = Predictor() if args.engine == "ml" else GeometricPredictor(signs=signs)
    if args.engine == "ml" and not predictor.ready:
        print("No trained model found, so the ML engine has nothing to predict with.")
        print("Either train one (python -m sanket_setu.train_model) or run the")
        print("geometric baseline instead:  python -m sanket_setu.realtime --engine geometric")
        return 1

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        print(f"Could not open camera {args.camera}.")
        print("  Common causes: another app is using the camera, OS camera permission "
              "is denied, or the index is wrong (try --camera 1).")
        return 2

    det = HandDetector(static_image_mode=False)
    engine = "ml" if args.engine == "ml" else "geometric"
    pending, pending_n = None, 0
    last_spoken, last_spoken_at = None, 0.0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("Camera stopped delivering frames.")
                break
            result = det.detect(bgr_to_rgb(frame))  # OpenCV BGR -> RGB for MediaPipe

            label, score, status = "", None, ""
            colour = (0, 0, 220)
            if result.status == "ok":
                res = (predictor.predict_features(result.features) if engine == "ml"
                       else predictor.predict_points(result.points))
                if res.status == "recognized":
                    label, score, colour = res.label, res.score, (0, 220, 0)
                    status = res.detail or "recognized"
                else:
                    status = res.message or res.status
                    colour = (0, 165, 255)
                    label = res.label or ""
                    score = res.score
            elif result.status == "no_hand":
                status = "no hand detected"
            else:
                status = "show only ONE hand"

            # debounce: require the same reading on consecutive frames
            if label and label == pending:
                pending_n += 1
            else:
                pending, pending_n = label, 1 if label else 0
            if pending and pending_n >= STABLE_FRAMES:
                if pending != last_spoken or time.time() - last_spoken_at > 4:
                    last_spoken, last_spoken_at = pending, time.time()
                    print(f"  -> {pending}")

            view = cv2.flip(frame, 1) if args.mirror else frame
            if result.status == "ok":
                pts = result.points.copy()
                if args.mirror:
                    pts[:, 0] = 1.0 - pts[:, 0]
                draw(view, pts, label, score, status, colour, engine)
            cv2.imshow("Sanket Setu - local webcam mode (q to quit)", view)
            if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                break
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        det.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
