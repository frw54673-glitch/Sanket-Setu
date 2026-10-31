// Slide 7 - Team, disclosure and close (closing page)
const C = require("./_common.js");

function createSlide(pres, theme) {
  const slide = pres.addSlide();
  slide.background = { color: C.NAVY };

  slide.addShape("rect", { x: 0, y: 0, w: 0.14, h: C.SH, fill: { color: C.SAFFRON } });

  C.kicker(slide, "Team and disclosure", { x: 0.6, y: 0.26 });
  slide.addText("Sanket Setu", {
    x: 0.56, y: 0.5, w: 4.4, h: 0.68, margin: 0,
    fontSize: 38, bold: true, color: C.WHITE, fontFace: C.HEAD, valign: "middle", fit: "shrink",
  });
  slide.addText("\u0938\u0909\u0915\u0947\u0924 \u0938\u0947\u0924\u0941", {
    x: 0.6, y: 1.18, w: 4.4, h: 0.38, margin: 0,
    fontSize: 17, bold: true, color: C.SAFFRON, fontFace: C.DEVA, valign: "middle",
  });

  // --- Team block ---
  slide.addShape("rect", { x: 0.6, y: 1.76, w: 4.3, h: 1.66, fill: { color: C.INDIGO }, rectRadius: 0.12 });
  slide.addText("TEAM", {
    x: 0.84, y: 1.9, w: 3.8, h: 0.24, margin: 0,
    fontSize: 9.5, bold: true, color: C.SAFFRON, charSpacing: 1.6, fontFace: C.BODY, valign: "middle",
  });
  slide.addText("[ member name ]   [ member name ]   [ member name ]", {
    x: 0.84, y: 2.16, w: 3.84, h: 0.28, margin: 0,
    fontSize: 9.5, bold: true, color: C.SAFFRON, fontFace: C.BODY, valign: "middle",
  });
  slide.addText("Roles: [ data collection ]  [ ML ]  [ design ]  [ interpreter liaison ]", {
    x: 0.84, y: 2.46, w: 3.84, h: 0.42, margin: 0,
    fontSize: 10, color: C.WHITE, fontFace: C.BODY, valign: "top", lineSpacing: 13,
  });
  slide.addText("One team member per role. Fill in names before submitting.", {
    x: 0.84, y: 2.92, w: 3.84, h: 0.38, margin: 0,
    fontSize: 9, italic: true, color: "C9C6FF", fontFace: C.BODY, valign: "top", lineSpacing: 12,
  });

  // --- Repository ---
  slide.addShape("rect", { x: 0.6, y: 3.54, w: 4.3, h: 0.66, fill: { color: C.INDIGO }, rectRadius: 0.12 });
  slide.addText("PUBLIC SOURCE REPOSITORY", {
    x: 0.84, y: 3.62, w: 3.8, h: 0.2, margin: 0,
    fontSize: 8.5, bold: true, color: C.SAFFRON, charSpacing: 1.2, fontFace: C.BODY, valign: "middle",
  });
  slide.addText("[ repository URL ]", {
    x: 0.84, y: 3.84, w: 3.8, h: 0.26, margin: 0,
    fontSize: 11, bold: true, color: C.WHITE, fontFace: C.BODY, valign: "middle",
  });

  // --- Disclosure ---
  slide.addShape("rect", { x: 5.2, y: 1.76, w: 3.85, h: 2.44, fill: { color: C.INDIGO }, rectRadius: 0.12 });
  slide.addText("AI-USE DISCLOSURE", {
    x: 5.44, y: 1.9, w: 3.4, h: 0.24, margin: 0,
    fontSize: 9.5, bold: true, color: C.SAFFRON, charSpacing: 1.6, fontFace: C.BODY, valign: "middle",
  });
  slide.addText(
    [
      { text: "Tools used: ", options: { bold: true, color: C.SAFFRON } },
      { text: "[ AI coding and research tools, with versions ]", options: { color: C.WHITE, breakLine: true } },
      { text: "Helped with: ", options: { bold: true, color: C.SAFFRON } },
      { text: "[ code scaffolding, test skeletons, documentation wording ]", options: { color: C.WHITE, breakLine: true } },
      { text: "Built and verified by us: ", options: { bold: true, color: C.SAFFRON } },
      { text: "[ vocabulary verification, data collection, training, evaluation ]", options: { color: C.WHITE, breakLine: true } },
      { text: "Estimated AI-assisted share: ", options: { bold: true, color: C.SAFFRON } },
      { text: "[ estimate ]", options: { color: C.WHITE } },
    ],
    {
      x: 5.44, y: 2.16, w: 3.4, h: 1.94, margin: 0,
      fontSize: 10, fontFace: C.BODY, valign: "top", lineSpacing: 13,
    }
  );

  // --- Closing line ---
  slide.addShape("rect", { x: 5.2, y: 4.34, w: 3.85, h: 0.98, fill: { color: C.SAFFRON }, rectRadius: 0.12 });
  slide.addText(
    "We would rather ship five signs we verified with a Deaf signer than five hundred we guessed. The app refuses when it is not sure, and so does this project.",
    {
      x: 5.42, y: 4.34, w: 3.42, h: 0.98, margin: 0,
      fontSize: 10.5, bold: true, color: C.NAVY, fontFace: C.BODY, valign: "middle", lineSpacing: 13,
    }
  );

  slide.addText("Har sanket, ab samajhne ke aur kareeb.", {
    x: 0.6, y: 4.38, w: 4.3, h: 0.36, margin: 0,
    fontSize: 14, italic: true, color: "C9C6FF", fontFace: C.BODY, valign: "middle",
  });
  slide.addText("Thank you.", {
    x: 0.6, y: 4.76, w: 4.3, h: 0.46, margin: 0,
    fontSize: 24, bold: true, color: C.WHITE, fontFace: C.HEAD, valign: "middle",
  });

  C.pageNum(slide, 7, theme);
  return slide;
}

module.exports = { createSlide };
