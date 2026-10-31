// Slide 5 - Impact: what is measured versus what is targeted
const C = require("./_common.js");

function createSlide(pres, theme) {
  const slide = pres.addSlide();
  slide.background = { color: theme.bg };

  C.kicker(slide, "Impact and scalability  -  targets set, results measured");
  C.title(slide, "What we have measured, and what we have promised");

  // --- Left: measured ---
  slide.addShape("rect", { x: 0.6, y: 1.1, w: 4.2, h: 0.42, fill: { color: C.NAVY }, rectRadius: 0.1 });
  slide.addText("MEASURED RESULTS", {
    x: 0.82, y: 1.1, w: 3.8, h: 0.42, margin: 0,
    fontSize: 10.5, bold: true, color: C.SAFFRON, charSpacing: 1.6, fontFace: C.BODY, valign: "middle",
  });
  C.panel(slide, 0.6, 1.6, 4.2, 3.0, C.WHITE, 0.12);

  slide.addText("Not yet measured", {
    x: 0.84, y: 1.78, w: 3.8, h: 0.4, margin: 0,
    fontSize: 21, bold: true, color: C.INK, fontFace: C.HEAD, valign: "middle",
  });
  slide.addText(
    "The team is collecting samples from consenting signers. Every number below will be copied from reports/metrics.json after a real training run.",
    {
      x: 0.84, y: 2.2, w: 3.76, h: 0.68, margin: 0,
      fontSize: 11, color: C.SOFT, fontFace: C.BODY, valign: "top", lineSpacing: 14,
    }
  );

  const rows = [
    "Held-out test accuracy",
    "Macro F1",
    "Per held-out signer accuracy",
    "Unknown-sign rejection rate",
  ];
  for (let i = 0; i < rows.length; i++) {
    const y = 2.98 + i * 0.38;
    slide.addText(rows[i], {
      x: 0.84, y: y, w: 2.7, h: 0.32, margin: 0,
      fontSize: 11, color: C.INK, fontFace: C.BODY, valign: "middle",
    });
    slide.addText("pending", {
      x: 3.5, y: y, w: 1.1, h: 0.32, margin: 0,
      fontSize: 10.5, bold: true, color: C.SAFFRON, fontFace: C.BODY, align: "right", valign: "middle",
    });
    slide.addShape("rect", { x: 0.84, y: y + 0.33, w: 3.76, h: 0.01, fill: { color: C.LINE } });
  }

  // --- Right: targets ---
  slide.addShape("rect", { x: 5.2, y: 1.1, w: 4.2, h: 0.42, fill: { color: C.IRIS }, rectRadius: 0.1 });
  slide.addText("PROPOSED KPIs - TARGETS ONLY", {
    x: 5.42, y: 1.1, w: 3.8, h: 0.42, margin: 0,
    fontSize: 10, bold: true, color: C.WHITE, charSpacing: 1.2, fontFace: C.BODY, valign: "middle",
  });
  C.panel(slide, 5.2, 1.6, 4.2, 3.0, C.WHITE, 0.12);

  const kpis = [
    "Per-class held-out macro F1",
    "Unknown-sign rejection rate",
    "End-to-end response time",
    "Task completion in user testing",
    "User-reported ease of use",
  ];
  for (let i = 0; i < kpis.length; i++) {
    const y = 1.8 + i * 0.42;
    slide.addShape("ellipse", { x: 5.46, y: y + 0.11, w: 0.12, h: 0.12, fill: { color: C.SAFFRON } });
    slide.addText(kpis[i], {
      x: 5.72, y: y, w: 2.72, h: 0.34, margin: 0,
      fontSize: 11, color: C.INK, fontFace: C.BODY, valign: "middle",
    });
    slide.addText("[ target ]", {
      x: 8.44, y: y, w: 0.8, h: 0.34, margin: 0,
      fontSize: 9.5, bold: true, color: C.FILL, fontFace: C.BODY, align: "right", valign: "middle",
    });
    slide.addShape("rect", { x: 5.46, y: y + 0.35, w: 3.78, h: 0.01, fill: { color: C.LINE } });
  }

  slide.addText(
    "These are the KPIs the team will be judged against once the pilot runs. They are labelled as targets on purpose.",
    {
      x: 5.46, y: 3.96, w: 3.78, h: 0.56, margin: 0,
      fontSize: 10, italic: true, color: C.SOFT, fontFace: C.BODY, valign: "top", lineSpacing: 13,
    }
  );

  // Scalability strip.
  slide.addShape("rect", { x: 0.6, y: 4.74, w: 8.6, h: 0.68, fill: { color: C.MIST }, line: { color: C.LINE, width: 1 }, rectRadius: 0.12 });
  slide.addText("SCALABILITY", {
    x: 0.86, y: 4.74, w: 1.5, h: 0.68, margin: 0,
    fontSize: 9.5, bold: true, color: C.SAFFRON, charSpacing: 1.3, fontFace: C.BODY, valign: "middle",
  });
  slide.addText(
    "The vocabulary is configuration, not code. More signs, regions and languages are added by editing one JSON file, not by rewriting the model.",
    {
      x: 2.4, y: 4.74, w: 6.6, h: 0.68, margin: 0,
      fontSize: 10.5, color: C.INK, fontFace: C.BODY, valign: "middle", lineSpacing: 14,
    }
  );

  C.pageNum(slide, 5, theme);
  return slide;
}

module.exports = { createSlide };
