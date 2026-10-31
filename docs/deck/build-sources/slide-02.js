// Slide 2 - The problem (comparison: three options and where each one breaks)
const C = require("./_common.js");

function createSlide(pres, theme) {
  const slide = pres.addSlide();
  slide.background = { color: theme.bg };

  C.kicker(slide, "The problem  -  no shared language at the counter");
  C.title(slide, "A signing visitor and a hearing clerk, with no way to talk");

  const cards = [
    {
      head: "Bring an interpreter",
      body: "Not present at every counter on every day. Costs money, costs time, and the queue does not wait.",
      tag: "Availability",
    },
    {
      head: "Paper note, or guess the gesture",
      body: "Slow and ambiguous, and often wrong exactly when it matters most. There is no shared vocabulary to fall back on.",
      tag: "Accuracy",
    },
    {
      head: "Existing sign-to-text ML",
      body: "Trained on videos of full signs. A single still frame of a static one-hand sign is a different task, and the public datasets are small or closed.",
      tag: "Fit for the task",
    },
  ];

  const w = 2.86, gap = 0.28, x0 = 0.6;
  for (let i = 0; i < cards.length; i++) {
    const x = x0 + i * (w + gap);
    C.panel(slide, x, 1.2, w, 2.66, C.WHITE, 0.14);
    slide.addShape("rect", { x: x, y: 1.2, w: w, h: 0.09, fill: { color: C.SAFFRON } });
    slide.addText(cards[i].tag.toUpperCase(), {
      x: x + 0.24, y: 1.44, w: w - 0.48, h: 0.22, margin: 0,
      fontSize: 9, bold: true, color: C.SAFFRON, charSpacing: 1.4, fontFace: C.BODY,
    });
    slide.addText(cards[i].head, {
      x: x + 0.24, y: 1.7, w: w - 0.48, h: 0.6, margin: 0,
      fontSize: 16, bold: true, color: C.INK, fontFace: C.HEAD, valign: "top", fit: "shrink",
    });
    slide.addText(cards[i].body, {
      x: x + 0.24, y: 2.34, w: w - 0.48, h: 1.42, margin: 0,
      fontSize: 11.5, color: C.SOFT, fontFace: C.BODY, valign: "top", lineSpacing: 16,
    });
  }

  // Bottom line band.
  slide.addShape("rect", { x: 0.6, y: 4.1, w: 8.6, h: 1.02, fill: { color: C.NAVY }, rectRadius: 0.12 });
  slide.addText("THE GAP", {
    x: 0.88, y: 4.24, w: 2.0, h: 0.26, margin: 0,
    fontSize: 9.5, bold: true, color: C.SAFFRON, charSpacing: 1.6, fontFace: C.BODY, valign: "middle",
  });
  slide.addText(
    "There is no dependable, offline, single-snapshot aid for the static signs people actually use at a counter.",
    {
      x: 0.88, y: 4.5, w: 8.06, h: 0.5, margin: 0,
      fontSize: 14, color: C.WHITE, fontFace: C.BODY, valign: "top", lineSpacing: 18,
    }
  );

  slide.addText(
    "We are not quoting a statistic we cannot source. If the team has a citable figure on access to services, put it here with its citation.",
    {
      x: 0.6, y: 5.24, w: 8.4, h: 0.26, margin: 0,
      fontSize: 9, italic: true, color: C.SOFT, fontFace: C.BODY, valign: "middle",
    }
  );

  C.pageNum(slide, 2, theme);
  return slide;
}

module.exports = { createSlide };
