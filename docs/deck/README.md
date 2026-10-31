# Proposal deck

`Sanket_Setu_Proposal.pptx` is the 7-slide submission deck for Hack for Social Cause
(VBYLD 2027), Theme 10. It matches the outline in
[`../presentation_outline.md`](../presentation_outline.md).

## Before you present - fill these in

The deck ships with bracketed fields that only the team can complete. They are marked in
saffron so they are impossible to miss.

| Slide | Field | What to put there |
|---|---|---|
| 1 | `[ team member names and roles ]` | every team member and what they own |
| 5 | `[ target ]` (x5) | the KPI targets the team commits to, with a number if you can commit to one |
| 7 | `[ member name ]` x3, `[ role ]` | team members and roles |
| 7 | `[ repository URL ]` | the public repository link |
| 7 | `[ AI coding and research tools, with versions ]` | the AI tools used, from `../ai_disclosure_template.md` |
| 7 | `[ code scaffolding, test skeletons, documentation wording ]` | what the AI actually helped with |
| 7 | `[ vocabulary verification, data collection, training, evaluation ]` | what the team did and verified itself |
| 7 | `[ estimate ]` | your honest AI-assisted share |
| 3 | the interface mock | **replace with a real screenshot** of Signer mode |
| 5 | `pending` rows | copy the real numbers from `reports/metrics.json` after a training run |

## Rebuilding the deck

The deck is generated with PptxGenJS so it stays consistent and reviewable in source.

```bash
cd build-sources
python render_hand.py                 # regenerate assets/hand.png (needs Pillow)
npm install pptxgenjs                # or: npm install -g pptxgenjs
node lint.js                          # pre-compile lint: source must be pure ASCII
node compile.js                       # writes ../Sanket_Setu_Proposal.pptx
```

`lint.js` rejects smart quotes and any non-ASCII character in the slide sources. Devanagari
strings are written as `\u` escapes so the source stays ASCII-only; see `slide-01.js`.

### Rules the build enforces

- Layout is `LAYOUT_16x9` - the canvas is **10.0 x 5.625 inches**. Every element must
  satisfy `x + w <= 10.0` and `y + h <= 5.625`.
- Colours are 6-character hex strings with no `#`.
- Slide modules export a synchronous `createSlide(pres, theme)`.
- Slides 2-7 carry a page-number badge; the cover does not.
- The palette comes from the application's own design system (`app/style.css`), so the
  deck and the product look like one thing.

### Checking the result

```bash
soffice --headless --convert-to pdf --outdir /tmp Sanket_Setu_Proposal.pptx
pdftoppm -png -r 100 /tmp/Sanket_Setu_Proposal.pdf /tmp/slide
```

Look at every rendered page before presenting. Overflowing text does not show up in the
source, only in the render.
