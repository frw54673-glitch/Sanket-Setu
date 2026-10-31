# Presentation Outline — 7 slides

> Competition format for **Hack for Social Cause (VBYLD 2027)**, Theme 10:
> *Assistive Technology & Accessibility*.
>
> **Rules for this outline:**
> - Every number on every slide must come from `reports/metrics.json` after a real
>   training run. If there is no run, the slide says the metric is *not yet measured*.
> - No invented statistics about disability prevalence, market size or government
>   numbers. If a figure cannot be cited to a source, it does not go on the slide.
> - The distinction between a **target** and a **measured result** is always visible.
> - Screenshots must be real screenshots of this application.

---

## Slide 1 — Title + the problem in one picture

**Title:** Sanket Setu — सङ्केत सेतु
**Tagline:** *Har sanket, ab samajhne ke aur kareeb.*

- One line: *A signing visitor and a hearing clerk at a government help desk, with no shared
  language.*
- Right side: **a real screenshot** of the app showing a recognised sign in Hindi.
- Bottom strip: `Hack for Social Cause · Theme 10: Assistive Technology & Accessibility`

**Speaker note:** open with the human moment, not the technology. "A person has come to
pay a bill, or ask for a medicine. They sign. The clerk cannot sign back."

---

## Slide 2 — Why the current options fail

Three columns, each with one concrete failure:

| Option | Where it breaks |
|---|---|
| **Bring an interpreter** | Not available at every counter, on every day. Costs money and time. |
| **Paper note / gesture guessing** | Slow, ambiguous, and often wrong exactly when it matters. |
| **Existing sign-to-text ML models** | Trained on videos of full signs. A single still frame of a static one-hand sign is a different task, and the published datasets are small, single-signer, or closed. |

**Bottom line (one line):** *There is no dependable, offline, single-snapshot aid for the
static signs people use at a counter.*

**Do not** put a made-up "X% of deaf people cannot access Y" on this slide. If the team
has a citable figure, put it here with the source. If not, leave it out — the argument
stands without it.

---

## Slide 3 — The solution: two honest engines

- **Left:** the real screenshot of *Signer mode* — photo of a hand, result card in Hindi.
- **Right:** two cards.

> **Engine A — Geometric baseline.** Counts extended fingers directly from the 21
> landmarks. Needs no training data, so it works on a real hand from day one. Covers the
> numeral signs. It is a rule-based baseline, not machine learning, and it carries no
> accuracy claim.

> **Engine B — ML classifier.** A RandomForest over 63-d landmark vectors collected from
> real consenting signers, with a signer-held-out split and a reject threshold tuned on
> validation data only.

- **Bottom strip:** `21 hand landmarks → 63 position-free numbers → classify or refuse`

**Speaker note:** the two-engine design is the point of this slide. It shows the team
thought about what they *have* versus what they *need*.

---

## Slide 4 — Architecture & the honesty guardrails

A Mermaid diagram (or a clean image of `docs/architecture.md`):

```
webcam / photo → RGB → MediaPipe Hands → 21 landmarks
→ wrist-relative, hand-size scaled → 63 floats → classify or refuse
→ Hindi + English text → visitor confirms → staff replies with large text, optional browser voice-to-text, and a visitor message board that is clearly separate from camera recognition
```

**Four guardrail chips, each with one line:**

| Guardrail | Why |
|---|---|
| **Signer-held-out split** | A random split over video frames of the same person inflates the score and means nothing. |
| **Threshold tuned on validation only** | The test partition is read once. |
| **Refuses below threshold** | "Not confidently recognised — try again" instead of a confident wrong answer. |
| **Camera frames stay in memory; session notes stay in-page until exported** | The camera service saves no frames. Browser speech recognition is optional and may use its provider; the app saves no audio. |

---

## Slide 5 — Impact, scalability, and what is actually measured

**Left — measured results** (fill only from `reports/metrics.json`):

| Metric | Value |
|---|---|
| Held-out test accuracy | _from metrics.json_ |
| Macro F1 | _from metrics.json_ |
| Per-signer accuracy (held-out signers) | _from metrics.json_ |
| Unknown-sign rejection rate | _from metrics.json_ |
| Test sample count | _from metrics.json_ |

If no training run has happened, this table reads: **"Not yet measured — the team is
collecting data from real signers."** That is an acceptable slide. A fabricated number is
not.

**Right — proposed KPIs (targets, not results).** Label the column clearly:

| KPI | Target |
|---|---|
| Per-class held-out macro F1 | _target_ |
| Unknown-sign rejection rate at the chosen threshold | _target_ |
| End-to-end response time on the target device | _target_ |
| Task completion rate in a user test with Deaf participants | _target_ |
| User-reported ease of use | _target_ |

**Bottom — scalability:** the same pipeline extends to more signs, more regions and more
languages, because the vocabulary is configuration, not code.

---

> **Current demo state:** The live camera uses a geometric baseline for a limited set of poses/numerals. The visitor message board is manually selected and is not sign recognition. Browser voice-to-text is optional and provider-dependent. The ML dataset and trained model are currently empty.

## Slide 6 — Team, roadmap, and the honest status

**Left — where the project actually is.** Be specific; judges reward this.

| Component | Status |
|---|---|
| Capture tool with consent, stability and separation gates | ✅ working |
| Two engines, shared inference module | ✅ working |
| Group-aware training, per-signer reporting, honest threshold | ✅ working |
| Web app + local webcam runner | ✅ working |
| Tests, model card, data protocol, docs | ✅ working |
| Real dataset from consenting signers | ☐ in progress — _n_ signers, _m_ sessions |
| Sign verification by a Deaf signer / ISL interpreter | ☐ _status_ |
| Trained model + measured metrics | ☐ _status_ |
| User study with Deaf participants | ☐ _status_ |

**Right — roadmap.**

| When | What |
|---|---|
| Week 1 | Verify the vocabulary with an interpreter; collect from signers 1–3 |
| Week 2 | Extend to 5 signers; train; read the held-out report; fill the model card |
| Week 3 | Pilot at a help desk with 3–5 Deaf visitors; measure task completion |
| Week 4 | Add moving signs with a temporal model; write the deployment guide |

---

## Slide 7 — Team details and AI-use disclosure

- **Team members**, roles, and what each person owns.
- **Repository link** (public source code, as the competition requires).
- **AI-use disclosure** — the filled-in version of `docs/ai_disclosure_template.md`:
  - the AI tools used and what they helped with;
  - what the team built and verified independently — especially the sign verification
    and the data collection;
  - the honest estimated share of AI-assisted work.
- **Contact**, and the line the team wants to be judged on:

> *"We would rather ship five signs we verified with a Deaf signer than five hundred we
> guessed. The app refuses to answer when it is not sure — and so does this proposal."*

---

## Checklist before you present

- [ ] Every number traces to `reports/metrics.json`.
- [ ] Every screenshot is a real screenshot of this app.
- [ ] No invented statistic about disability, population or market.
- [ ] Targets are visibly labelled as targets.
- [ ] The vocabulary slide shows the verification status of each sign.
- [ ] Someone from the team can answer: *"which sign was hardest to verify, and why?"*
- [ ] The AI-use disclosure is filled in and accurate.
- [ ] The demo video is recorded and does not contain fabricated results.
