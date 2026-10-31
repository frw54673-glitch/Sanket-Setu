// Slide 3 - The solution: two honest engines (mixed media)
const C = require("./_common.js");

function createSlide(pres, theme) {
  const slide = pres.addSlide();
  slide.background = { color: theme.bg };

  C.kicker(slide, "The solution  -  one interface, two clearly labelled engines");
  C.title(slide, "Two engines, each honest about what it is");

  // --- Left: a faithful mock of the app's result card ---
  slide.addText("What the visitor sees", {
    x: 0.6, y: 1.04, w: 3.5, h: 0.26, margin: 0,
    fontSize: 11, bold: true, color: C.SOFT, fontFace: C.BODY, valign: "middle",
  });
  slide.addShape("rect", { x: 0.6, y: 1.36, w: 3.5, h: 2.06, fill: { color: C.NAVY }, rectRadius: 0.16 });
  slide.addShape("rect", { x: 0.6, y: 1.36, w: 3.5, h: 0.08, fill: { color: C.SAFFRON } });

  slide.addText("\u0924\u0940\u0928", {
    x: 0.6, y: 1.5, w: 3.5, h: 0.76, margin: 0,
    fontSize: 44, bold: true, color: C.WHITE, fontFace: C.DEVA, align: "center", valign: "middle",
  });
  slide.addText("Three", {
    x: 0.6, y: 2.24, w: 3.5, h: 0.38, margin: 0,
    fontSize: 19, bold: true, color: "D8D6FF", fontFace: C.HEAD, align: "center", valign: "middle",
  });
  slide.addShape("rect", { x: 0.85, y: 2.68, w: 3.0, h: 0.3, fill: { color: C.INDIGO }, rectRadius: 0.15 });
  slide.addText("model score 0.87  (not accuracy)", {
    x: 0.85, y: 2.68, w: 3.0, h: 0.3, margin: 0,
    fontSize: 9, bold: true, color: C.SAFFRON, fontFace: C.BODY, align: "center", valign: "middle",
  });
  slide.addText("visitor confirms before it reaches the clerk", {
    x: 0.72, y: 3.04, w: 3.26, h: 0.28, margin: 0,
    fontSize: 9.5, color: "C9C6FF", fontFace: C.BODY, align: "center", valign: "middle",
  });

  slide.addText(
    "Mock of the interface. Replace with a real screenshot before you present.",
    { x: 0.6, y: 3.5, w: 3.5, h: 0.42, margin: 0, fontSize: 9, italic: true, color: C.SAFFRON, fontFace: C.BODY, lineSpacing: 12 }
  );

  // --- Right: the two engine cards ---
  const cards = [
    {
      tag: "ENGINE A  -  AVAILABLE TODAY",
      head: "Geometric baseline",
      body: "Counts the extended fingers straight from the landmarks. Needs no training data, so it works on a real hand from day one.",
      foot: "Rule-based, not machine learning. Numeral signs only. No accuracy claim.",
      bar: C.IRIS,
    },
    {
      tag: "ENGINE B  -  NEEDS REAL DATA",
      head: "ML classifier",
      body: "A RandomForest over 63-d landmark vectors collected from real consenting signers, with a signer-held-out split.",
      foot: "Score is an uncalibrated model score, not accuracy. Threshold tuned on validation only.",
      bar: C.SAFFRON,
    },
  ];

  for (let i = 0; i < cards.length; i++) {
    const y = 1.02 + i * 1.9;
    C.panel(slide, 4.4, y, 5.0, 1.8, C.WHITE, 0.14);
    slide.addShape("rect", { x: 4.4, y: y, w: 0.09, h: 1.8, fill: { color: cards[i].bar } });
    slide.addText(cards[i].tag, {
      x: 4.7, y: y + 0.13, w: 4.5, h: 0.22, margin: 0,
      fontSize: 9, bold: true, color: C.SAFFRON, charSpacing: 1.3, fontFace: C.BODY, valign: "middle",
    });
    slide.addText(cards[i].head, {
      x: 4.7, y: y + 0.36, w: 4.5, h: 0.34, margin: 0,
      fontSize: 17, bold: true, color: C.INK, fontFace: C.HEAD, valign: "middle",
    });
    slide.addText(cards[i].body, {
      x: 4.7, y: y + 0.70, w: 4.5, h: 0.60, margin: 0,
      fontSize: 11, color: C.INK, fontFace: C.BODY, valign: "top", lineSpacing: 14,
    });
    slide.addText(cards[i].foot, {
      x: 4.7, y: y + 1.34, w: 4.5, h: 0.40, margin: 0,
      fontSize: 9.5, italic: true, color: C.SOFT, fontFace: C.BODY, valign: "top", lineSpacing: 12,
    });
  }

  // --- Pipeline strip ---
  const steps = ["Photo", "21 landmarks", "63 numbers", "Classify or refuse", "Hindi + English"];
  const sw = 1.6, sgap = 0.1;
  const sx0 = 0.6;
  for (let i = 0; i < steps.length; i++) {
    const x = sx0 + i * (sw + sgap);
    slide.addShape("rect", {
      x: x, y: 4.86, w: sw, h: 0.46,
      fill: { color: i === 3 ? C.INDIGO : C.WHITE },
      line: { color: i === 3 ? C.INDIGO : C.LINE, width: 1 }, rectRadius: 0.1,
    });
    slide.addText(steps[i], {
      x: x, y: 4.86, w: sw, h: 0.46, margin: 0,
      fontSize: 10.5, bold: true, color: i === 3 ? C.WHITE : C.INK,
      fontFace: C.BODY, align: "center", valign: "middle",
    });
    if (i < steps.length - 1) {
      slide.addText(">", {
        x: x + sw - 0.04, y: 4.86, w: sgap + 0.08, h: 0.46, margin: 0,
        fontSize: 12, bold: true, color: C.SAFFRON, fontFace: C.BODY, align: "center", valign: "middle",
      });
    }
  }

  slide.addText(
    "Both engines share one inference module, so the web app and the webcam runner can never disagree.",
    { x: 0.6, y: 5.36, w: 8.4, h: 0.24, margin: 0, fontSize: 9.5, italic: true, color: C.SOFT, fontFace: C.BODY, valign: "middle" }
  );

  C.pageNum(slide, 3, theme);
  return slide;
}

module.exports = { createSlide };
