"""Sanket Setu: limited-vocabulary ISL sign-recognition and communication-support prototype.

Two engines, clearly separated in the interface:
  * ML model      - the trained classifier over collected landmarks. Needs real data.
  * Geometric     - a rule-based baseline that counts extended fingers. Needs no data.

Both go through the same shared inference module, so the Streamlit app and the local
webcam runner can never disagree about what a sign means.
"""
import json
import base64
import sys
from html import escape as esc
from pathlib import Path

APP = Path(__file__).resolve().parent
sys.path.insert(0, str(APP.parent / "src"))  # works from a fresh clone without installing

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402
from PIL import Image  # noqa: E402

from sanket_setu import config as C  # noqa: E402
from sanket_setu.inference import TRAIN_HELP, GeometricPredictor, Predictor  # noqa: E402
from sanket_setu.speech import SpeechUnavailable, synthesize  # noqa: E402

LOGO = APP / "assets" / "sanket-setu-mark.png"
st.set_page_config(page_title="Sanket Setu", page_icon=str(LOGO), layout="wide", initial_sidebar_state="collapsed")
PAGES = ["Home", "Signer mode", "Staff mode", "Supported signs", "Model status"]
VERSION, SIGNS = C.load_signs()
SUPPORTED = [s for s in C.trainable(SIGNS) if s.sign_type != "background"]
PENDING = [s for s in C.blocked(SIGNS)]
PHRASES = C.load_phrases()
EXCLUDED = C.load_excluded()
TAG = {"verified": "ok", "needs_review": "review", "demo_only": "review", "n/a": "na"}
st.session_state.setdefault("log", [])
st.session_state.setdefault("page", "Home")

# 21 MediaPipe-style landmarks, drawn for the hero (illustration of the real feature layout)
PTS = [(150, 310), (105, 280), (72, 240), (50, 200), (32, 165), (110, 185), (100, 130), (95, 95), (92, 62), (150, 170),
       (152, 108), (153, 70), (154, 34), (190, 180), (205, 128), (212, 95), (218, 66), (225, 205), (248, 165), (260, 140), (270, 116)]
EDGES = [(0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8), (5, 9), (9, 10), (10, 11), (11, 12), (9, 13), (13, 14),
         (14, 15), (15, 16), (13, 17), (17, 18), (18, 19), (19, 20), (0, 17)]


def html(s: str) -> None:
    st.markdown(" ".join(line.strip() for line in s.splitlines()), unsafe_allow_html=True)


def hand_svg() -> str:
    lines = "".join(f'<line x1="{PTS[a][0]}" y1="{PTS[a][1]}" x2="{PTS[b][0]}" y2="{PTS[b][1]}"/>' for a, b in EDGES)
    dots = "".join(f'<circle cx="{x}" cy="{y}" r="5" class="{"tip" if i in (4, 8, 12, 16, 20) else ""}" '
                   f'style="animation-delay:{(i // 4) * .3}s"/>' for i, (x, y) in enumerate(PTS))
    palm = " ".join(f"{PTS[i][0]},{PTS[i][1]}" for i in (0, 1, 5, 9, 13, 17))
    return (f'<svg viewBox="0 0 300 350" role="img" aria-label="Hand with 21 tracked landmarks"><polygon points="{palm}" fill="#ffffff12"/>'
            f'<g stroke="#A5A2FF" stroke-width="2.5" stroke-linecap="round">{lines}</g><g fill="#FF9933">{dots}</g>'
            '<circle cx="150" cy="310" r="13" fill="none" stroke="#FF9933" stroke-width="2"/>'
            '<text x="172" y="338" fill="#C9C6FF" font-size="12" font-family="sans-serif">wrist = origin (0, 0)</text></svg>')


def model_help(pred: Predictor) -> None:
    if pred.reason == TRAIN_HELP or "not trained yet" in pred.reason:
        st.info("**ML model not trained yet.** Collect real samples, then train:")
        st.code("python -m sanket_setu.collect_data --signer S01\npython -m sanket_setu.train_model", language="bash")
    else:
        st.warning(pred.reason)


@st.cache_resource
def ml_predictor() -> Predictor:
    return Predictor()


@st.cache_resource
def geo_predictor() -> GeometricPredictor:
    return GeometricPredictor()


def say(role: str, hi: str, en: str, note: str = "") -> None:
    st.session_state.log.append({"role": role, "hi": hi, "en": en, "note": note})


def audio_button(text: str, lang: str, key: str) -> None:
    if st.button("🔊 Generate audio", key=f"aud_{key}", help="Sends only this plain text to Google TTS. Needs internet."):
        try:
            st.audio(synthesize(text, lang), format="audio/mp3")
        except SpeechUnavailable as exc:
            st.error(str(exc))


def show_log() -> None:
    html('<div class="sec">Conversation <span class="tag na">this session only</span></div>')
    if not st.session_state.log:
        st.caption("Confirmed signs and staff replies appear here. Nothing is saved to disk.")
        return
    for m in st.session_state.log:
        who = m["role"] == "visitor"
        with st.chat_message("user" if who else "assistant", avatar="🧑" if who else "🧑‍💼"):
            st.markdown(f"**{m['hi']}**  \n{m['en']}" if m["hi"] else m["en"])
            if m["note"]:
                st.caption(m["note"])
    a, b = st.columns(2)
    if a.button("Clear conversation", use_container_width=True):
        st.session_state.log = []
        st.rerun()
    b.download_button("Download as text", "\n".join(f"[{m['role']}] {m['hi']} | {m['en']}" for m in st.session_state.log),
                      "conversation.txt", use_container_width=True)


# ---------- shell ----------
st.markdown(f"<style>{(APP / 'style.css').read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
c1, c2, c3 = st.columns([1.1, 4, 1.1], vertical_alignment="center")
logo_data = base64.b64encode((APP / 'assets' / 'sanket-setu-mark.svg').read_bytes()).decode('ascii')
c1.markdown(f'<div class="brand"><img src="data:image/svg+xml;base64,{logo_data}" alt=""> Sanket Setu</div>', unsafe_allow_html=True)
page = c2.radio("Navigate", PAGES, horizontal=True, key="page", label_visibility="collapsed")
if c3.toggle("Large text"):
    st.markdown("<style>html{font-size:20px}</style>", unsafe_allow_html=True)

bad = C.unverified(SIGNS)
if bad:
    html(f'<div class="notice"><b>Prototype vocabulary:</b> {len(bad)} sign(s) are not yet verified against the official ISL '
         'dictionary by a Deaf signer or qualified interpreter. Treat meanings as demo-only until then.</div>')

# ---------- pages ----------
if page == "Home":
    html(f'''<div class="hero"><div>
        <span class="pill">Hack for Social Cause · Assistive Technology &amp; Accessibility</span>
        <h1>Sanket Setu<span class="dev">सङ्केत सेतु</span></h1>
        <p class="lead">A bridge between a signing visitor and the help desk. One hand sign in, Hindi and English text out,
        and a human always confirms before anything is understood.</p>
        <div class="chips"><span>21 hand landmarks</span><span>Hindi + English</span><span>Human-confirmed</span><span>No photo saved</span></div>
        </div><div class="hero-art">{hand_svg()}</div></div>''')
    st.write("")
    st.button("Try it as a signer →", type="primary", on_click=lambda: st.session_state.update(page="Signer mode"))
    html('<div class="sec">How it works</div>')
    html('''<div class="flow">
        <div><b>📷</b>Snapshot<small>one hand, one sign</small></div>
        <div><b>✋</b>21 landmarks<small>found by MediaPipe</small></div>
        <div><b>📐</b>Normalize<small>63 position-free numbers</small></div>
        <div><b>🌲</b>Classify + reject<small>unsure means "try again"</small></div>
        <div><b>🗣️</b>Hindi · English<small>visitor confirms</small></div></div>''')
    html('<div class="sec">Two engines, both honest about what they are</div>')
    html('''<div class="cards">
        <div class="card"><b>Geometric baseline</b><p>Reads numerals and names a few common poses. Gesture labels do not claim an ISL meaning; this is not a trained model.</p></div>
        <div class="card"><b>ML classifier</b><p>A RandomForest over landmarks collected from real consenting signers. Trained by the team on their own dataset, with a signer-held-out split. Scores are model scores, not accuracy.</p></div>
        <div class="card"><b>It says "not sure"</b><p>Below a validation-tuned threshold the ML engine refuses to guess and asks the visitor to retry, instead of forcing a label.</p></div></div>''')
    html('<div class="sec">What this prototype does not do</div>')
    html('''<div class="cards">
        <div class="card"><b>Not a translator</b><p>Static single-hand signs only. Real ISL also uses movement, two hands, facial expression and context. There is no sentence translation.</p></div>
        <div class="card"><b>Not an interpreter</b><p>This supports a help desk conversation. It does not replace a qualified ISL interpreter, and it must not be used for emergency or high-stakes decisions on its own.</p></div>
        <div class="card"><b>Not a photo vault</b><p>Only 21 landmark numbers are stored, never images. Consent is asked before any recording, and a signer can withdraw.</p></div></div>''')
    html('<div class="foot">Static single-hand signs only · still snapshot, not live video · not a replacement for a qualified '
         'interpreter · not for emergencies</div>')

elif page == "Signer mode":
    html('<div class="sec">Live recognition</div>')
    st.markdown("Start the live backend in a second terminal, then open the camera experience. Frames are processed in memory and are not saved.")
    a, b = st.columns([1, 2], vertical_alignment="center")
    a.link_button("Open live camera →", "http://127.0.0.1:8765", type="primary", use_container_width=True)
    b.code("python -m sanket_setu.live_server", language="bash")
    st.caption("Allow camera access in the browser. Use localhost on this same computer. The live page uses the shared inference engine and needs no separate cloud account.")
    st.divider()
    ml = ml_predictor()
    geo = geo_predictor()
    left, right = st.columns(2, gap="large")
    with left:
        html('<div class="sec">1 · Show one hand sign</div>')
        engines = ["Geometric baseline", "ML model"]
        engine_label = st.radio("Engine", engines, horizontal=True, label_visibility="collapsed",
                                help="Geometric = rule-based, works with no dataset. ML = trained on real collected samples.")
        use_ml = engine_label == "ML model"
        if use_ml and not ml.ready:
            st.warning("The ML model has not been trained yet, so it cannot predict anything.")
            st.code("python -m sanket_setu.collect_data --signer S01\npython -m sanket_setu.train_model", language="bash")
            st.caption("Switch to the geometric baseline to try the app right now.")
        src = st.radio("Input", ["Camera snapshot", "Upload image"], horizontal=True, label_visibility="collapsed")
        img = None
        if src == "Camera snapshot":
            st.caption("Still snapshot, not live video. Keep one hand fully visible in good light.")
            shot = st.camera_input("Take a photo of one hand sign", label_visibility="collapsed")
            img = Image.open(shot) if shot else None
        else:
            up = st.file_uploader("JPG or PNG with one hand", type=["jpg", "jpeg", "png"])
            try:
                img = Image.open(up) if up else None
            except Exception:
                st.error("That file is not a readable image.")
        if img is not None:
            st.image(img, width=300)
            can_run = ml.ready if use_ml else True
            if st.button("Recognize sign", type="primary", use_container_width=True, disabled=not can_run):
                st.session_state.result = ml.predict_image(img) if use_ml else geo.predict_image(img)
    with right:
        html('<div class="sec">2 · Check the reading</div>')
        res = st.session_state.get("result")
        if res is None:
            if use_ml and not ml.ready:
                model_help(ml)
            else:
                html('<div class="result empty">Your result will appear here</div>')
        elif res.status == "recognized":
            s = res.sign
            engine_tag = "geometric baseline" if res.engine == "geometric" else "ML model"
            scope_note = "Informal gesture interpretation · confirm with visitor · not ISL · " if s.sign_type == "static_gesture" else ""
            score_txt = "" if res.score is None else f"Model score {res.score:.2f} (not accuracy) · "
            html(f'<div class="result"><div class="hi">{esc(s.text_hi)}</div><div class="en">{esc(s.text_en)}</div>'
                 f'<div class="meta">{scope_note}{score_txt}<span class="tag {TAG[s.validation_status]}">'
                 f'{esc(s.validation_status)}</span> · <span class="tag na">{esc(engine_tag)}</span></div>'
                 f'<div class="meta">{esc(res.detail)}</div></div>')
            audio_button(s.text_hi, "hi", "sign")
            a, b = st.columns(2)
            if a.button("✅ Yes, this is what I meant", use_container_width=True):
                say("visitor", s.text_hi, s.text_en, f"sign · {s.validation_status} · {engine_tag}")
                st.session_state.result = None
                st.rerun()
            if b.button("🔁 Try again", use_container_width=True):
                st.session_state.result = None
                st.rerun()
        else:
            st.warning(res.message)
            if st.button("🔁 Try again", use_container_width=True):
                st.session_state.result = None
                st.rerun()
    with st.expander("💬 Choose a phrase manually (not an AI result)"):
        pick = st.selectbox("Supported meanings", SUPPORTED, format_func=lambda s: f"{s.text_hi} · {s.text_en}")
        if st.button("Use this phrase") and pick:
            say("visitor", pick.text_hi, pick.text_en, "picked manually")
            st.rerun()
    show_log()

elif page == "Staff mode":
    html('<div class="sec">Staff reply</div>')
    st.caption("Phrase picker, not AI output. Generic phrases only, no medical or legal advice.")
    lang = st.radio("Display language", ["हिन्दी", "English"], horizontal=True)
    hindi = lang == "हिन्दी"
    cur = st.session_state.get("staff")
    if cur:
        main, sub = (cur["text_hi"], cur["text_en"]) if hindi else (cur["text_en"], cur["text_hi"])
        html(f'<div class="result big"><div class="hi">{esc(main)}</div>'
             f'<div class="en">{esc(sub) if sub != main else ""}</div></div>')
        audio_button(main, "hi" if hindi else "en", "staff")
    else:
        html('<div class="result big empty">Tap a phrase below. It shows here in large text for the visitor.</div>')
    cols = st.columns(3)
    for i, p in enumerate(PHRASES):
        if cols[i % 3].button(p["text_hi"] if hindi else p["text_en"], key=f"ph_{p['id']}", use_container_width=True):
            st.session_state.staff = p
            say("staff", p["text_hi"], p["text_en"], "phrase")
            st.rerun()
    custom = st.text_input("Or type a short message", max_chars=140)
    if st.button("Show typed message") and custom.strip():
        st.session_state.staff = {"text_hi": custom.strip(), "text_en": custom.strip()}
        say("staff", "", custom.strip(), "typed")
        st.rerun()
    show_log()

elif page == "Supported signs":
    html('<div class="sec">Supported signs</div>')
    st.caption(f"Config version {VERSION}. Status shows whether a human has confirmed the meaning and handshape.")

    html('<div class="sub">Enabled in the model</div>')
    html('<div class="signs">' + "".join(
        f'<div class="sign"><div class="hi">{esc(s.text_hi)}</div><div class="en">{esc(s.text_en)}</div>'
        f'<span class="tag {TAG[s.validation_status]}">{esc(s.validation_status)}</span>'
        f'<div class="src"><a href="{esc(s.source_url)}" target="_blank" rel="noopener">ISL Dictionary ↗</a>'
        f' · {esc(s.dictionary_category or "—")}</div></div>' for s in SUPPORTED) + '</div>')

    if PENDING:
        html('<div class="sub">Candidates — disabled until an interpreter confirms them</div>')
        st.caption("These are switched off on purpose. Turning one on without human confirmation would teach the model a sign "
                   "that may not even be static.")
        rows = []
        for s in PENDING:
            rows.append({
                "Sign": f"{s.text_hi} · {s.text_en}",
                "Type evidence": s.type_evidence[:120] + ("…" if len(s.type_evidence) > 120 else ""),
                "Source confidence": s.type_confidence,
                "Category": s.dictionary_category or "—",
                "Enabled": "no",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        for s in PENDING:
            with st.expander(f"How to verify “{s.text_en}”"):
                st.markdown(f"**Dictionary entry:** {s.source_url}")
                st.markdown(f"**Why it is a candidate:** {s.type_evidence}")
                st.markdown("**Checklist:**")
                for item in s.verification_checklist:
                    st.markdown(f"- {item}")
                st.caption("Set validation_status=verified, fill in validator, set enabled=true, then collect and retrain.")

    if EXCLUDED:
        html('<div class="sub">Deliberately excluded from the static model</div>')
        st.caption("These are real ISL signs. They are excluded because a single still frame cannot carry their meaning, "
                   "not because they are unimportant.")
        for e in EXCLUDED:
            with st.expander(f"{e['text_en']} — {e['label_en']}"):
                st.markdown(e["reason"])
                st.caption(f"ISL Dictionary: {e['source_url']}")

    html('<div class="sub">Why human verification is not optional</div>')
    html('<div class="cards">'
         '<div class="card"><b>The dictionary is video-only</b><p>The official ISL Dictionary publishes videos and no written '
         'handshape or notation. There is no API to check a sign automatically, so a Deaf signer or qualified interpreter has to '
         'confirm every entry.</p></div>'
         '<div class="card"><b>Sources disagree</b><p>“Help” appears in a curated list of 140 static ISL signs, while other '
         'authorities describe it as a directional sign whose meaning changes with movement. A static frame cannot tell those '
         'apart, so the model would learn an arbitrary meaning.</p></div>'
         '<div class="card"><b>ISL varies by region</b><p>ISLRTC records regional variants of numerals and colour terms. The team '
         'must decide which region the prototype targets and record it.</p></div></div>')
    st.info("To verify a sign: open the ISL Dictionary link, watch the video, fix one canonical variant, confirm it is one hand "
            "and static, then update `configs/signs.json`.")

elif page == "Model status":
    html('<div class="sec">Model status</div>')
    pred = ml_predictor()
    if st.button("Reload model"):
        st.cache_resource.clear()
        st.rerun()
    if not pred.ready:
        model_help(pred)
        st.write("No metrics are shown because none have been measured.")
        st.markdown("**The geometric baseline does not need a trained model.** It is available in *Signer mode* right now.")
    else:
        m = pred.meta
        st.success(f"Model loaded (trained {m['trained_at']}).")
        st.write(f"**Split:** {m['split_strategy']}")
        if not m["cross_person_validated"]:
            st.error("Cross-person generalization is UNVALIDATED (fewer than 3 signers).")
        for w in m["warnings"]:
            st.warning(w)
        mt = m["metrics"]
        a, b, c = st.columns(3)
        a.metric("Held-out test accuracy", f"{mt['test_accuracy']:.1%}")
        b.metric("Macro F1", f"{mt['macro_f1']:.2f}")
        c.metric("Test samples", mt["n_test"])
        st.caption(f"Reject threshold {m['reject_threshold']} (tuned on validation only). Measured on this dataset only; "
                   "it does not describe real-world accuracy.")
        if m.get("per_signer"):
            html('<div class="sub">Per held-out signer</div>')
            ps = pd.DataFrame([
                {"Signer": k, "Test samples": v["n_test_samples"],
                 "Accuracy": f"{v['accuracy']:.1%}" if v["accuracy"] is not None else "—",
                 "Accuracy on accepted": (f"{v['accuracy_on_accepted']:.1%}"
                                           if v.get("accuracy_on_accepted") is not None else "—"),
                 "Labels seen": ", ".join(v["labels_present"])}
                for k, v in m["per_signer"].items()
            ])
            st.dataframe(ps, use_container_width=True, hide_index=True)
            st.caption("Each row is a person who was NOT in the training partition. This is the closest thing to a real "
                       "new-visitor test that an offline dataset can give.")
        if m.get("score_semantics"):
            st.caption(m["score_semantics"])
        rep = C.REPORT_DIR / "metrics.json"
        if rep.exists():
            cm = json.loads(rep.read_text(encoding="utf-8"))["confusion_matrix"]
            st.write("Confusion matrix (rows = true, columns = predicted)")
            st.dataframe(pd.DataFrame(cm["matrix"], index=cm["labels"], columns=cm["labels"]))
        st.markdown("**Next step to improve this:** collect from more signers and sessions, then retrain. The held-out "
                    "signer rows above tell you whether it is actually getting better.")
