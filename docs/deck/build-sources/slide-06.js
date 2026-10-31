// Slide 6 - Where the project actually is, and the roadmap (two-column)
const C = require("./_common.js");

function createSlide(pres, theme) {
  const slide = pres.addSlide();
  slide.background = { color: theme.bg };

  C.kicker(slide, "Status and roadmap  -  what is finished, what is not");
  C.title(slide, "Where we actually are, and what we do next");

  // --- Left: status ---
  slide.addText("Where we actually are", {
    x: 0.6, y: 1.02, w: 4.4, h: 0.3, margin: 0,
    fontSize: 14, bold: true, color: C.INK, fontFace: C.HEAD, valign: "middle",
  });

  const done = [
    "Consent-gated capture with stability, size and separation gates",
    "Two engines behind one shared inference module",
    "Group-aware training, per-signer report, honest threshold",
    "Web app plus a local webcam runner",
    "Test suite, model card, data protocol, slide outline, demo script",
  ];
  const open = [
    "Dataset from real consenting signers",
    "Sign verification by a Deaf signer or ISL interpreter",
    "Trained model with measured held-out metrics",
    "User study with Deaf participants",
  ];

  for (let i = 0; i < done.length; i++) {
    const y = 1.42 + i * 0.46;
    slide.addShape("rect", { x: 0.6, y: y + 0.05, w: 0.22, h: 0.22, fill: { color: C.IRIS }, rectRadius: 0.04 });
    slide.addText("Y", {
      x: 0.6, y: y + 0.05, w: 0.22, h: 0.22, margin: 0,
      fontSize: 9.5, bold: true, color: C.WHITE, fontFace: C.BODY, align: "center", valign: "middle",
    });
    slide.addText(done[i], {
      x: 0.9, y: y, w: 3.95, h: 0.32, margin: 0,
      fontSize: 10.5, color: C.INK, fontFace: C.BODY, valign: "middle",
    });
  }

  for (let i = 0; i < open.length; i++) {
    const y = 3.84 + i * 0.32;
    slide.addShape("rect", { x: 0.6, y: y + 0.04, w: 0.22, h: 0.22, fill: { color: C.WHITE }, line: { color: C.SAFFRON, width: 1.5 }, rectRadius: 0.04 });
    slide.addText(open[i], {
      x: 0.9, y: y, w: 3.95, h: 0.3, margin: 0,
      fontSize: 10, color: C.SOFT, fontFace: C.BODY, valign: "middle",
    });
  }

  slide.addText("Y = built and tested      empty box = still open", {
    x: 0.6, y: 5.16, w: 4.4, h: 0.24, margin: 0,
    fontSize: 8.5, italic: true, color: C.SOFT, fontFace: C.BODY, valign: "middle",
  });

  // --- Right: roadmap ---
  slide.addText("Roadmap", {
    x: 5.3, y: 1.02, w: 3.85, h: 0.3, margin: 0,
    fontSize: 14, bold: true, color: C.INK, fontFace: C.HEAD, valign: "middle",
  });

  const phases = [
    ["WEEK 1", "Verify the vocabulary with an interpreter. Collect from signers 1 to 3."],
    ["WEEK 2", "Extend to 5 signers. Train. Read the held-out report. Fill the model card."],
    ["WEEK 3", "Pilot at a help desk with 3 to 5 Deaf visitors. Measure task completion."],
    ["WEEK 4", "Add moving signs with a temporal model. Write the deployment guide."],
  ];

  slide.addShape("rect", { x: 5.42, y: 1.56, w: 0.03, h: 3.3, fill: { color: C.LINE } });

  for (let i = 0; i < phases.length; i++) {
    const y = 1.48 + i * 0.86;
    slide.addShape("ellipse", { x: 5.3, y: y + 0.09, w: 0.26, h: 0.26, fill: { color: C.SAFFRON } });
    slide.addText(phases[i][0], {
      x: 5.72, y: y, w: 1.1, h: 0.26, margin: 0,
      fontSize: 9.5, bold: true, color: C.SAFFRON, charSpacing: 1.2, fontFace: C.BODY, valign: "middle",
    });
    slide.addText(phases[i][1], {
      x: 5.72, y: y + 0.25, w: 3.6, h: 0.52, margin: 0,
      fontSize: 11, color: C.INK, fontFace: C.BODY, valign: "top", lineSpacing: 14,
    });
  }

  slide.addShape("rect", { x: 5.3, y: 4.92, w: 3.85, h: 0.02, fill: { color: C.LINE } });
  slide.addText(
    "The critical path is the interpreter session. It is also the thing a judge should push us on.",
    {
      x: 5.3, y: 5.0, w: 3.85, h: 0.44, margin: 0,
      fontSize: 9.5, italic: true, color: C.SOFT, fontFace: C.BODY, valign: "top", lineSpacing: 12,
    }
  );

  C.pageNum(slide, 6, theme);
  return slide;
}

module.exports = { createSlide };
