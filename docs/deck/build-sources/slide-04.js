// Slide 4 - Architecture and the guardrails (process flow)
const C = require("./_common.js");

function createSlide(pres, theme) {
  const slide = pres.addSlide();
  slide.background = { color: theme.bg };

  C.kicker(slide, "How it works  -  one pipeline, four guardrails");
  C.title(slide, "Why the numbers mean something");

  // --- Process flow ---
  const steps = [
    { n: "1", head: "Capture", body: "Photo or webcam frame" },
    { n: "2", head: "Landmarks", body: "MediaPipe finds 21 points" },
    { n: "3", head: "Normalise", body: "Wrist-relative, hand-size scaled" },
    { n: "4", head: "Classify", body: "Forest score, or a rule count" },
    { n: "5", head: "Confirm", body: "Visitor agrees, staff replies" },
  ];
  const w = 1.7, gap = 0.13, x0 = 0.6;
  for (let i = 0; i < steps.length; i++) {
    const x = x0 + i * (w + gap);
    const last = i === steps.length - 1;
    C.panel(slide, x, 1.12, w, 1.48, last ? C.INDIGO : C.WHITE, 0.12);
    slide.addShape("ellipse", { x: x + 0.16, y: 1.26, w: 0.36, h: 0.36, fill: { color: last ? C.SAFFRON : C.IRIS } });
    slide.addText(steps[i].n, {
      x: x + 0.16, y: 1.26, w: 0.36, h: 0.36, margin: 0,
      fontSize: 12, bold: true, color: C.WHITE, fontFace: C.HEAD, align: "center", valign: "middle",
    });
    slide.addText(steps[i].head, {
      x: x + 0.16, y: 1.7, w: w - 0.32, h: 0.28, margin: 0,
      fontSize: 13.5, bold: true, color: last ? C.WHITE : C.INK, fontFace: C.HEAD, valign: "middle",
    });
    slide.addText(steps[i].body, {
      x: x + 0.16, y: 2.0, w: w - 0.32, h: 0.52, margin: 0,
      fontSize: 10, color: last ? "D8D6FF" : C.SOFT, fontFace: C.BODY, valign: "top", lineSpacing: 13,
    });
    if (i < steps.length - 1) {
      slide.addText(">", {
        x: x + w - 0.04, y: 1.12, w: gap + 0.08, h: 1.48, margin: 0,
        fontSize: 15, bold: true, color: C.SAFFRON, fontFace: C.BODY, align: "center", valign: "middle",
      });
    }
  }

  // --- Guardrails ---
  slide.addText("The four guardrails", {
    x: 0.6, y: 2.84, w: 5.0, h: 0.3, margin: 0,
    fontSize: 15, bold: true, color: C.INK, fontFace: C.HEAD, valign: "middle",
  });

  const guards = [
    {
      head: "Signer-held-out split",
      body: "A random split over frames of the same person inflates the score and means nothing.",
    },
    {
      head: "Threshold tuned on validation only",
      body: "The test partition is read exactly once, and the threshold is never fitted to it.",
    },
    {
      head: "Refuses below threshold",
      body: "A confident wrong answer is worse than no answer, so the app says 'try again'.",
    },
    {
      head: "Landmarks only, never images",
      body: "Consent is asked first, and a signer can withdraw their rows at any time.",
    },
  ];

  const gw = 2.15, ggap = 0.13, gx0 = 0.6;
  for (let i = 0; i < guards.length; i++) {
    const x = gx0 + i * (gw + ggap);
    C.panel(slide, x, 3.26, gw, 1.56, C.WHITE, 0.12);
    slide.addShape("rect", { x: x, y: 3.26, w: gw, h: 0.07, fill: { color: C.SAFFRON } });
    slide.addText(guards[i].head, {
      x: x + 0.16, y: 3.44, w: gw - 0.32, h: 0.48, margin: 0,
      fontSize: 12, bold: true, color: C.INK, fontFace: C.HEAD, valign: "top", fit: "shrink",
    });
    slide.addText(guards[i].body, {
      x: x + 0.16, y: 3.94, w: gw - 0.32, h: 0.8, margin: 0,
      fontSize: 10, color: C.SOFT, fontFace: C.BODY, valign: "top", lineSpacing: 13,
    });
  }

  slide.addText(
    "Capture-time gates that stop a bad dataset: one deliberate sample per press, a stability gate, a size gate, and a minimum separation between two samples of the same sign.",
    { x: 0.6, y: 4.96, w: 8.4, h: 0.36, margin: 0, fontSize: 9.5, italic: true, color: C.SOFT, fontFace: C.BODY, valign: "top", lineSpacing: 13 }
  );

  C.pageNum(slide, 4, theme);
  return slide;
}

module.exports = { createSlide };
