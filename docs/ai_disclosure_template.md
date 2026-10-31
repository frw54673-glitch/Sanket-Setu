# AI-Use Disclosure (template)

> **This is a template.** The competition requires transparent disclosure of AI-tool
> usage. Fill it in accurately and completely — an honest, specific disclosure is a
> strength with judges, and an inflated or vague one is a liability.
>
> Do not copy the placeholder values. Do not guess the percentage. Do not claim the team
> "wrote everything manually" if that is not true.

---

## 1. Tools used

List every AI tool that touched this project, including ones used for research, images,
slides, or documentation.

| Tool | Version / model | Used for |
|---|---|---|
| _(e.g. Claude Code, Cursor, ChatGPT, Gemini)_ | _(e.g. Claude Sonnet 4.5, Nov 2025)_ | _(e.g. scaffolding the Python package, writing unit tests, drafting README prose)_ |
| | | |
| | | |

## 2. What the AI helped with

Be specific. "Helped with code" is not useful; "generated the initial skeleton of
`src/sanket_setu/landmarks.py`, which the team then rewrote to fix the RGB/BGR
conversion" is.

- **Code generation** — _(which modules, and what the team changed afterwards)_
- **Debugging** — _(which bugs the AI diagnosed, and how they were verified)_
- **Documentation and wording** — _(which documents, and who fact-checked them)_
- **Research** — _(which external facts were checked against a primary source)_
- **Design and slides** — _(what was generated, and what the team rewrote)_

## 3. What the team built and verified independently

This is the important section. List the work that is the team's own and that a human
checked.

- **Vocabulary verification against the official ISL Dictionary** — performed by
  _(name/role)_ on _(date)_. Every sign's meaning, hand-count and static/one-hand
  classification was confirmed against the video at
  `https://divyangjan.depwd.gov.in/islrtc/search.php?search=<term>`.
  _Status: ☐ done ☐ not yet done_
- **Data collection** — _(number)_ real signers, _(number)_ sessions each, all consented.
  _Status: ☐ done ☐ not yet done_
- **Label and source curation** — the team chose the vocabulary, the canonical variants
  and the region targeted, and recorded the sources.
- **Model training and evaluation** — the team ran the training pipeline and read the
  held-out report. Every number in the slides comes from `reports/metrics.json`.
- **Test suite** — the team ran `python -m pytest` and fixed the failures. The AI may
  have written test skeletons; running them and fixing them is the team's work.
- **Ethical and privacy decisions** — consent flow, what is and is not stored, the
  refusal-to-guess behaviour, and the explicit exclusion of signs that a static model
  cannot honestly represent.

## 4. Estimated share of AI-assisted work

> Estimate this honestly. A range is acceptable and arguably more credible than a single
> precise number. Consider: how much of the code, documentation and design would not
> exist without the AI tool? If you had to rebuild it from scratch, what fraction would
> you write differently?

**Estimated AI-assisted share of the deliverable: _[e.g. 40–60%]_**

Reasoning: _[one or two sentences explaining how you arrived at the figure]_

## 5. Rules the team followed

- No AI-generated claim about accuracy, latency, user numbers or impact was used
  anywhere. Every performance number in the slides comes from a real training run
  recorded in `reports/metrics.json`.
- No AI-generated testimonial, user quote or field-report was included.
- AI suggestions about ISL vocabulary were **not** accepted as fact: every sign was
  checked against the official ISL Dictionary by a human, and the repository records
  which entries remain `needs_review`.
- The AI was not used to invent a validator name, a signer id, a dataset size or a
  licence.

## 6. Declaration

_(Team name / member names)_

_(Date)_

> By signing this, the team confirms that the disclosures above are accurate and that
> every quantitative claim in the submission traces to an artefact in the repository.
