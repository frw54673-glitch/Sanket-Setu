// Shared helpers and brand constants for the Sanket Setu deck.
// The palette is the product's own (app/style.css) so the slides and the app look like one thing.

const NAVY = "0E0B2E";   // --night
const INDIGO = "312E81"; // --indigo
const IRIS = "4F46E5";  // --iris
const SAFFRON = "FF9933"; // --saffron
const MIST = "F5F4FF";  // --mist
const LINE = "E0E0F5";  // --line
const INK = "1B1A4A";   // --ink
const SOFT = "6B6A99";  // --soft
const WHITE = "FFFFFF";

const HEAD = "Trebuchet MS";
const BODY = "Calibri";
const DEVA = "Nirmala UI"; // Devanagari-capable system font on Windows

const SW = 10.0;   // slide width  (LAYOUT_16x9)
const SH = 5.625;  // slide height (LAYOUT_16x9)

// Fresh option objects every call - PptxGenJS mutates them in place.
const shadow = () => ({ type: "outer", color: "000000", blur: 10, offset: 2, angle: 90, opacity: 0.10 });

// Page number badge, mandatory on every non-cover slide.
function pageNum(slide, n, theme) {
  slide.addShape("rect", {
    x: 9.3, y: 5.1, w: 0.42, h: 0.3,
    fill: { color: theme.primary }, rectRadius: 0.05,
  });
  slide.addText(String(n), {
    x: 9.3, y: 5.1, w: 0.42, h: 0.3, margin: 0,
    fontSize: 11, bold: true, color: theme.light,
    align: "center", valign: "middle", fontFace: BODY,
  });
}

// Slide title block. No accent rule under the title (that is an AI-deck tell).
function title(slide, text, opts) {
  const o = opts || {};
  slide.addText(text, {
    x: o.x !== undefined ? o.x : 0.6,
    y: o.y !== undefined ? o.y : 0.42,
    w: o.w !== undefined ? o.w : 9.0,
    h: 0.52, margin: 0,
    fontSize: o.fontSize || 25, bold: true, color: INK,
    fontFace: HEAD, align: "left", valign: "middle", fit: "shrink",
  });
}

function kicker(slide, text, opts) {
  const o = opts || {};
  slide.addText(text.toUpperCase(), {
    x: o.x !== undefined ? o.x : 0.62,
    y: o.y !== undefined ? o.y : 0.16,
    w: o.w !== undefined ? o.w : 8.9, h: 0.22, margin: 0,
    fontSize: 9.5, bold: true, color: SAFFRON,
    charSpacing: 1.6, fontFace: BODY, align: "left", valign: "middle",
  });
}

// A line segment between two arbitrary points.
function seg(slide, x1, y1, x2, y2, color, width) {
  const x = Math.min(x1, x2);
  const y = Math.min(y1, y2);
  const w = Math.abs(x2 - x1);
  const h = Math.abs(y2 - y1);
  const opts = {
    x: x, y: y, w: w === 0 ? 0.001 : w, h: h === 0 ? 0.001 : h,
    line: { color: color, width: width || 2 },
  };
  // pptxgenjs draws a shape's bounding box top-left -> bottom-right. Only the
  // bottom-right -> top-left diagonal is a different segment, so that is the
  // only case that needs flipping (both axes).
  if (x2 < x1 && y2 < y1) { opts.flipH = true; opts.flipV = true; }
  slide.addShape("line", opts);
}

// The 21-landmark hand skeleton. Rendered to a PNG by render_hand.py from the same
// point set the application uses, so the deck shows the real feature layout.
function drawHand(slide, x, y, w, h) {
  slide.addImage({
    path: require("path").join(__dirname, "assets", "hand.png"),
    x: x, y: y, w: w, h: h,
  });
}

// A soft panel with a heading and body lines.
function panel(slide, x, y, w, h, fill, radius) {
  slide.addShape("rect", {
    x: x, y: y, w: w, h: h,
    fill: { color: fill }, line: { color: LINE, width: 1 },
    rectRadius: radius === undefined ? 0.12 : radius,
  });
}

// Fill-in marker for fields only the team can supply.
const FILL = SAFFRON;

module.exports = {
  NAVY: NAVY, INDIGO: INDIGO, IRIS: IRIS, SAFFRON: SAFFRON, MIST: MIST,
  LINE: LINE, INK: INK, SOFT: SOFT, WHITE: WHITE,
  HEAD: HEAD, BODY: BODY, DEVA: DEVA,
  SW: SW, SH: SH,
  shadow: shadow, pageNum: pageNum, title: title, kicker: kicker,
  seg: seg, drawHand: drawHand, panel: panel, FILL: FILL,
};
