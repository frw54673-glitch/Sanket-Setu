// Slide 1 - Cover page (asymmetric left-right)
const C = require("./_common.js");

function createSlide(pres, theme) {
  const slide = pres.addSlide();
  slide.background = { color: theme.bg };

  // Right panel: the product's own feature layout, drawn from the real landmark set.
  slide.addShape("rect", { x: 5.75, y: 0, w: 4.25, h: C.SH, fill: { color: C.NAVY } });
  slide.addShape("ellipse", { x: 6.35, y: 0.3, w: 3.45, h: 3.45, fill: { color: C.INDIGO, transparency: 45 } });
  C.drawHand(slide, 6.42, 0.55, 2.92, 3.41);

  slide.addText("21 landmarks", {
    x: 5.75, y: 4.28, w: 4.25, h: 0.32, margin: 0,
    fontSize: 13, bold: true, color: C.SAFFRON, align: "center", fontFace: C.BODY, valign: "middle",
  });
  slide.addText("MediaPipe hand tracking, drawn to scale", {
    x: 5.75, y: 4.58, w: 4.25, h: 0.28, margin: 0,
    fontSize: 10.5, color: "C9C6FF", align: "center", fontFace: C.BODY, valign: "middle",
  });

  // Left: title stack.
  slide.addShape("rect", { x: 0.6, y: 0.7, w: 4.42, h: 0.4, fill: { color: C.INDIGO }, rectRadius: 0.2 });
  slide.addText("Hack for Social Cause  |  Theme 10: Assistive Technology", {
    x: 0.6, y: 0.7, w: 4.42, h: 0.4, margin: 0,
    fontSize: 9.5, bold: true, color: C.WHITE, align: "center", valign: "middle", fontFace: C.BODY,
  });

  slide.addText("Sanket Setu", {
    x: 0.56, y: 1.26, w: 5.05, h: 0.8, margin: 0,
    fontSize: 46, bold: true, color: C.INK, fontFace: C.HEAD, align: "left", valign: "middle", fit: "shrink",
  });
  slide.addText("\u0938\u0909\u0915\u0947\u0924 \u0938\u0947\u0924\u0941", {
    x: 0.6, y: 2.1, w: 5.0, h: 0.44, margin: 0,
    fontSize: 23, bold: true, color: C.SAFFRON, fontFace: C.DEVA, align: "left", valign: "middle",
  });

  slide.addText("Har sanket, ab samajhne ke aur kareeb.", {
    x: 0.6, y: 2.6, w: 4.9, h: 0.32, margin: 0,
    fontSize: 14, italic: true, color: C.IRIS, fontFace: C.BODY, align: "left", valign: "middle",
  });

  slide.addText(
    "A limited-vocabulary ISL sign-recognition and communication-support prototype for help desks. One hand sign in, Hindi and English out, and a human always confirms before anything is understood.",
    {
      x: 0.6, y: 3.02, w: 4.75, h: 1.12, margin: 0,
      fontSize: 12, color: C.INK, fontFace: C.BODY, align: "left", valign: "top", lineSpacing: 18,
    }
  );

  slide.addShape("rect", { x: 0.6, y: 4.36, w: 0.09, h: 0.32, fill: { color: C.SAFFRON } });
  slide.addText("Team:", {
    x: 0.78, y: 4.36, w: 0.62, h: 0.32, margin: 0,
    fontSize: 11, color: C.SOFT, fontFace: C.BODY, align: "left", valign: "middle",
  });
  slide.addText("[ team member names and roles ]", {
    x: 1.42, y: 4.36, w: 3.9, h: 0.32, margin: 0,
    fontSize: 11, bold: true, color: C.FILL, fontFace: C.BODY, align: "left", valign: "middle",
  });

  slide.addText("VBYLD 2027  |  Public source repository", {
    x: 0.6, y: 4.8, w: 4.75, h: 0.28, margin: 0,
    fontSize: 10, color: C.SOFT, fontFace: C.BODY, align: "left", valign: "middle",
  });

  return slide;
}

module.exports = { createSlide };
