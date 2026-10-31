"""Build a captioned Sanket Setu care-desk walkthrough video.

Run from the project root with the existing environment:
    python scripts/build_walkthrough_video.py
"""
from pathlib import Path
import math
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "app" / "assets" / "sanket-setu-walkthrough.mp4"
W, H, FPS = 1280, 720, 15
OUT_W, OUT_H = 960, 540
SCENE_SECONDS = 4.5
SCENES = [
    ("A clearer conversation", "A visitor signs. The app helps both people take the next step.", "CARE DESK · TWO PEOPLE · ONE CLEARER MOMENT"),
    ("1  Start the camera", "Keep one supported hand in frame and in good light.", "Two-hand movement is tracked live; it is not translated as a sentence."),
    ("2  Check the reading together", "The visitor confirms the suggested meaning before it is added.", "A thumbs-up is an informal cue. Context can change its meaning."),
    ("3  Speak, reply, or type", "Confirmed text can be spoken. Staff can reply with text or voice-to-text.", "For an unsupported message, choose a phrase or type it in the message board."),
]
BG = (246, 244, 235)
INK = (31, 47, 45)
MUTED = (99, 111, 105)
GREEN = (35, 104, 79)
ORANGE = (192, 80, 52)
PAPER = (255, 255, 250)
LINE = (220, 221, 210)
FONT_REG = r"C:\Windows\Fonts\arial.ttf"
FONT_BOLD = r"C:\Windows\Fonts\arialbd.ttf"
FONT_HI = r"C:\Windows\Fonts\Nirmala.ttf"

def font(path, size):
    return ImageFont.truetype(path if Path(path).exists() else FONT_REG, size)

F_BRAND = font(FONT_BOLD, 19)
F_META = font(FONT_BOLD, 13)
F_TITLE = font(FONT_BOLD, 44)
F_BODY = font(FONT_REG, 23)
F_SMALL = font(FONT_REG, 17)
F_BIG = font(FONT_HI, 44)
F_EN = font(FONT_BOLD, 25)
F_BUTTON = font(FONT_BOLD, 16)

def rounded(draw, box, radius, fill, outline=None, width=1):
    radius = min(radius, max(1, int(min(box[2]-box[0], box[3]-box[1]) * .35)))
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)

def center_text(draw, xy, text, f, fill):
    draw.text(xy, text, font=f, fill=fill, anchor="mm")

def hand(draw, x, y, scale=1.0, color=GREEN, palm_up=False):
    """A clearly illustrative hand pictogram, not a captured sign exemplar."""
    s = scale
    if palm_up:
        # Upright palm with five extended fingers.
        rounded(draw, (x-42*s, y-8*s, x+42*s, y+88*s), int(24*s), color)
        for i, h in enumerate((86, 112, 124, 112, 88)):
            fx = x - 45*s + i*22*s
            rounded(draw, (fx, y-h*s, fx+18*s, y+12*s), max(1, int(7*s)), color)
        rounded(draw, (x-54*s, y+29*s, x-5*s, y+48*s), int(9*s), color)
    else:
        # Thumbs-up pictogram.
        rounded(draw, (x-38*s, y+17*s, x+37*s, y+98*s), int(20*s), color)
        rounded(draw, (x-18*s, y-52*s, x+7*s, y+48*s), int(12*s), color)
        rounded(draw, (x-14*s, y+34*s, x+62*s, y+56*s), int(10*s), color)
        for i in range(3):
            rounded(draw, (x-8*s, y+58*s+i*17*s, x+48*s, y+74*s+i*17*s), int(8*s), color)

def scene_art(draw, idx, t):
    # The stage stays within a framed card, like the actual on-device camera workspace.
    card = (630, 172, 1165, 562)
    rounded(draw, card, 22, (28, 45, 43), (210, 214, 204), 2)
    draw.rounded_rectangle((652, 194, 1143, 540), radius=15, fill=(238, 239, 228))
    if idx == 0:
        # A simple help-desk illustration to establish the two-person use case.
        draw.ellipse((752, 245, 825, 318), fill=(211, 164, 127))
        draw.ellipse((1008, 245, 1081, 318), fill=(196, 146, 112))
        rounded(draw, (716, 322, 850, 425), 35, (91, 118, 105))
        rounded(draw, (984, 322, 1118, 425), 35, (201, 110, 78))
        rounded(draw, (765, 399, 1065, 469), 15, (219, 210, 187))
        draw.line((915, 400, 915, 463), fill=(174, 163, 138), width=3)
        hand(draw, 885 + 12*math.sin(t*2)*1, 385, .42, GREEN, True)
        rounded(draw, (703, 482, 1092, 521), 12, (255, 255, 250))
        center_text(draw, (897, 501), "A SIGN CAN START THE CONVERSATION", F_META, GREEN)
    elif idx == 1:
        rounded(draw, (679, 220, 1116, 490), 18, (31, 49, 48), (159, 188, 169), 2)
        # Finder frame
        for x, y, sx, sy in [(702,242,1,1),(1092,242,-1,1),(702,468,1,-1),(1092,468,-1,-1)]:
            draw.line((x,y,x+24*sx,y), fill=(222,146,101), width=5)
            draw.line((x,y,x,y+24*sy), fill=(222,146,101), width=5)
        drift = 14*math.sin(t*3.0)
        hand(draw, 895 + drift, 349, .82, (100, 215, 166), True)
        # Palm landmark trails, explicitly shown as a tracking overlay.
        for k in range(5):
            px = 858 + k*18 + drift
            py = 360 - (45 if k in (1,2,3) else 24)
            draw.ellipse((px-4, py-4, px+4, py+4), fill=PAPER, outline=GREEN, width=2)
            draw.line((px, py, 895+drift, 393), fill=(115, 173, 143), width=2)
        rounded(draw, (704, 505, 1091, 530), 12, (232, 247, 237))
        center_text(draw, (897, 518), "LIVE HAND LANDMARKS · NO VIDEO SAVED", font(FONT_BOLD, 12), GREEN)
    elif idx == 2:
        rounded(draw, (686, 213, 1108, 502), 19, PAPER, (224, 226, 218), 2)
        rounded(draw, (711, 235, 1083, 278), 11, (239, 243, 235))
        center_text(draw, (897, 257), "SUGGESTED READING · PLEASE CONFIRM", font(FONT_BOLD, 13), MUTED)
        hand(draw, 779, 358, .45, ORANGE, False)
        draw.text((839, 320), "मैं ठीक हूँ।", font=F_BIG, fill=INK)
        draw.text((841, 375), "I’m okay.", font=F_EN, fill=MUTED)
        rounded(draw, (738, 435, 1054, 482), 13, GREEN)
        center_text(draw, (896, 459), "YES, THAT IS RIGHT", F_BUTTON, PAPER)
        draw.text((779, 493), "Common gesture · visitor confirms the meaning", font=font(FONT_REG, 14), fill=MUTED)
    else:
        # Two-way communication: a large readable reply and a typed fallback.
        rounded(draw, (677, 214, 1118, 364), 17, PAPER, (224,226,218), 2)
        rounded(draw, (695, 231, 755, 291), 18, (229, 241, 231))
        center_text(draw, (725,261), "S", F_BUTTON, GREEN)
        draw.text((778, 234), "STAFF · LARGE TEXT REPLY", font=font(FONT_BOLD,13), fill=MUTED)
        draw.text((778, 269), "कृपया थोड़ा इंतज़ार करें।", font=font(FONT_HI,23), fill=INK)
        draw.text((778, 308), "Please wait a moment.", font=font(FONT_REG,18), fill=MUTED)
        rounded(draw, (677, 385, 1118, 514), 17, (250, 247, 237), (229, 220, 204), 2)
        draw.text((701, 405), "MESSAGE BOARD · TYPE ANYTHING ELSE", font=font(FONT_BOLD,13), fill=ORANGE)
        draw.text((701, 440), "मुझे मदद चाहिए।", font=font(FONT_HI,27), fill=INK)
        draw.line((701, 483, 1041, 483), fill=(196,200,187), width=2)
        # Small sound bars
        for i, bar in enumerate((10,20,29,17,24,12,19)):
            xx = 1060+i*8
            draw.line((xx, 492-bar/2, xx, 492+bar/2), fill=GREEN, width=4)
    # Labels under the hero visual make the illustration clearly non-predictive.
    draw.text((667, 578), "Illustrated walkthrough · the camera does not predict these frames", font=font(FONT_REG,14), fill=MUTED)

def frame(idx, local_t, total_t):
    im = Image.new("RGB", (W,H), BG)
    d = ImageDraw.Draw(im)
    # quiet editorial page details
    d.ellipse((1070,-220,1440,150), fill=(233, 233, 217))
    d.line((56,89,1224,89), fill=LINE, width=2)
    rounded(d, (57,32,95,70), 11, GREEN)
    # Bridge/signal mark, rendered as a tiny line emblem.
    d.line((66,56,76,45,87,56), fill=PAPER, width=3)
    d.line((66,60,87,60), fill=PAPER, width=2)
    d.text((108,38), "SANKET SETU", font=F_BRAND, fill=INK)
    d.text((912,43), "CARE DESK WALKTHROUGH", font=F_META, fill=MUTED)
    # Progress indicator, advancing on real timeline.
    rounded(d, (57,107,1223,113), 3, (229,230,219))
    progress=(idx+local_t/SCENE_SECONDS)/len(SCENES)
    d.rounded_rectangle((57,107,57+int(1166*progress),113), radius=3, fill=ORANGE)
    d.text((58,139), f"{idx+1:02d}  /  {len(SCENES):02d}", font=F_META, fill=ORANGE)
    title, body, note = SCENES[idx]
    d.text((58,184), title, font=F_TITLE, fill=INK)
    # Wrap message lines to a readable measure.
    words=body.split(); lines=[]; line=""
    for word in words:
        candidate=(line+" "+word).strip()
        if d.textlength(candidate,font=F_BODY)>490 and line:
            lines.append(line); line=word
        else: line=candidate
    if line: lines.append(line)
    for j,text in enumerate(lines): d.text((60,257+j*36), text, font=F_BODY, fill=MUTED)
    rounded(d, (58, 384, 550, 466), 15, (255,255,250), LINE, 1)
    d.ellipse((78,405,102,429), fill=GREEN)
    d.line((84,417,89,422,97,412), fill=PAPER, width=3)
    # note may be long; wrap separately
    note_lines=[]; line=""
    for word in note.split():
        candidate=(line+" "+word).strip()
        if d.textlength(candidate,font=F_SMALL)>410 and line:
            note_lines.append(line); line=word
        else: line=candidate
    if line: note_lines.append(line)
    for j,text in enumerate(note_lines[:2]): d.text((116,402+j*26), text, font=F_SMALL, fill=INK)
    scene_art(d,idx,local_t)
    d.text((59,665), "LIMITED-VOCABULARY PROTOTYPE  ·  NOT A SUBSTITUTE FOR A QUALIFIED ISL INTERPRETER", font=font(FONT_BOLD,12), fill=(117,124,114))
    d.text((1134,661), f"{total_t:04.1f}s", font=F_META, fill=MUTED)
    return cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2BGR)

def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    # Use Windows Media Foundation H.264 so Chromium/Edge can decode this MP4.
    writer=cv2.VideoWriter(str(OUT), cv2.CAP_MSMF, cv2.VideoWriter_fourcc(*"H264"), FPS, (OUT_W,OUT_H))
    if not writer.isOpened():
        raise SystemExit("Windows Media Foundation could not open the H.264 MP4 encoder.")
    writer.set(cv2.VIDEOWRITER_PROP_QUALITY, 35)
    total=0
    for idx in range(len(SCENES)):
        for n in range(round(SCENE_SECONDS*FPS)):
            t=n/FPS
            writer.write(cv2.resize(frame(idx,t,total+t), (OUT_W,OUT_H), interpolation=cv2.INTER_AREA))
        total += SCENE_SECONDS
    writer.release()
    if not OUT.exists() or OUT.stat().st_size < 50_000:
        raise SystemExit("Walkthrough video was not written correctly.")
    print(f"Wrote {OUT} ({OUT.stat().st_size:,} bytes)")

if __name__ == "__main__":
    main()
