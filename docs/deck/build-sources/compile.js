const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.author = "Sanket Setu Team";
pres.company = "Sanket Setu";
pres.title = "Sanket Setu - ISL Sign Recognition Prototype for Help Desks";
pres.subject = "Hack for Social Cause (VBYLD 2027) - Theme 10: Assistive Technology and Accessibility";

// Palette taken from the product's own design system (app/style.css) so the deck and the
// application read as one thing.
const theme = {
  primary: "1B1A4A",   // --ink    : body text
  secondary: "6B6A99", // --soft   : muted text
  accent: "FF9933",    // --saffron: highlight
  light: "FFFFFF",     //         : card background
  bg: "F5F4FF",        // --mist   : slide background
};

const order = [
  "./slide-01.js",
  "./slide-02.js",
  "./slide-03.js",
  "./slide-04.js",
  "./slide-05.js",
  "./slide-06.js",
  "./slide-07.js",
];

for (const f of order) {
  require(f).createSlide(pres, theme);
}

pres.writeFile({ fileName: "./slides/output/Sanket_Setu_Proposal.pptx" })
  .then((n) => console.log("WROTE:", n))
  .catch((e) => { console.error("FAILED:", e); process.exit(1); });
