"""Render the Sanket Setu hand-landmark skeleton to a transparent PNG.

The 21 points are the same ones the application uses (app/streamlit_app.py), so the
deck shows the real feature layout rather than a decorative illustration.

Run:  python render_hand.py
Out:  assets/hand.png
"""
from pathlib import Path

from PIL import Image, ImageDraw

PTS = [
    (150, 310), (105, 280), (72, 240), (50, 200), (32, 165),
    (110, 185), (100, 130), (95, 95), (92, 62),
    (150, 170), (152, 108), (153, 70), (154, 34),
    (190, 180), (205, 128), (212, 95), (218, 66),
    (225, 205), (248, 165), (260, 140), (270, 116),
]
EDGES = [
    (0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12), (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20), (0, 17),
]
PALM = [0, 1, 5, 9, 13, 17]
TIPS = {4, 8, 12, 16, 20}

EDGE = (165, 162, 255)      # periwinkle, matches the deck's edge colour
SAFFRON = (255, 153, 51)    # fingertip marker
KNUCKLE = (255, 255, 255)

SCALE = 4
W, H = 300 * SCALE, 350 * SCALE


def main() -> None:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # palm wash
    d.polygon([(PTS[i][0] * SCALE, PTS[i][1] * SCALE) for i in PALM], fill=(255, 255, 255, 28))

    # bones
    for a, b in EDGES:
        d.line([(PTS[a][0] * SCALE, PTS[a][1] * SCALE),
                (PTS[b][0] * SCALE, PTS[b][1] * SCALE)],
               fill=EDGE, width=7 * SCALE // 2, joint="curve")

    # joints
    for i, (x, y) in enumerate(PTS):
        r = (11 if i in TIPS else 9) * SCALE // 2
        fill = SAFFRON + (255,) if i in TIPS else KNUCKLE + (255,)
        d.ellipse([x * SCALE - r, y * SCALE - r, x * SCALE + r, y * SCALE + r],
                  fill=fill, outline=EDGE, width=3 * SCALE // 2)

    out = Path(__file__).parent / "assets"
    out.mkdir(parents=True, exist_ok=True)
    path = out / "hand.png"
    img.save(path)
    print("wrote", path, img.size)


if __name__ == "__main__":
    main()
