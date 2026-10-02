# Discovery Note — Dhaga & Co.

*Tech Track Mini Project 1 — dated before first commit*

## 1. The problem, in one sentence

We don't know why a third of our orders come back, because nobody can read six thousand unlabeled "Other" return reasons and nine thousand support tickets a week by hand.

## 2. Who owns it today, and what they do instead

Neha (Category Head) reads the free-text "Other" box on returns herself, a few hundred at a time, and estimates most of it is about fit — but she can't get through the volume. Karthik (Data Analyst) fields the "why" questions this data should answer, and requests queue up for about two weeks before he gets to them, for the whole company. Arpita's 34 support agents also generate nine thousand free-text tickets a week with no consistent tagging, so the same signal is scattered and duplicated across two teams who aren't reading each other's data.

## 3. The evidence

- Returns run 31% overall; 44% of return reasons land in "Other" — roughly 6,500 a week with no structure.
- 410,000 product reviews, 18 months deep, star rating plus free text — "nobody reads them. They are displayed and never analysed."
- Support tickets: ~9,000/week, mostly free text, "no consistent tagging. Agents pick a category only when they remember to."
- Faizan's adjacent number — 26% COD return-to-origin at ₹120 each — shows the fit/quality problem also has a hard cost once a return is already in motion, a second, related loss if the underlying cause (sizing, fabric, photos) is never fixed.

## 4. What it costs them

At 48,000 orders/week, 6,500 unlabeled returns a week is a backlog Neha's manual reading can never clear — at "a few hundred at a time" it would take weeks to read one week's volume, so the backlog only grows. That's a standing blind spot on the metric the company already tracks and already argues about: the return rate itself, plus the unread half-million-word archive (reviews) that could explain it.

## 5. What success looks like

Every "Other" return, plus the free-text in returns/reviews/tickets, gets auto-classified into a small set of causes (fit, fabric/quality, wrong item, changed mind, delivery damage, other) with a confidence score, so Neha reviews a ranked list instead of raw text. Measured with data they already hold:

- % of "Other" volume auto-classified with high confidence
- Whether Neha's spot-checks agree with the model's labels
- Over a few weeks, whether return rate moves on SKUs where the top flagged cause (e.g. a mislabeled size chart) gets corrected

## 6. Ranked shortlist

| Rank | Problem | Owner | Why it sits here |
|---|---|---|---|
| 1 | **Returns & review intelligence** | Neha / Karthik | Named owners losing something measurable today. All input data already exists and is untouched. Purely internal, so no publish-unread risk. Upstream of at least two other complaints (fit-driven returns, "why" questions Karthik can't get to). |
| 2 | **Catalogue enrichment / attribute normalization** | Vivek | Strong LLM fit (colour typed 90 ways, free-text fabric, per-vendor size charts) and plausibly upstream of *why* returns happen, but doesn't directly answer Neha's or Karthik's question, and is a slower build (vision + text). |
| 3 | **WISMO ticket deflection** | Arpita | Real cost (58% of 9,000 tickets/week, 9-hour first response) but is a symptom of 4–7 day delivery, not the delivery problem itself. Customer-facing, which adds the review-step requirement. |
| 4 | **COD RTO prediction** | Faizan | Cleanest, most quantified cost (₹120 × 26% of COD orders), but scoring who's likely to reject a COD order is a better fit for a classical ML model than for an LLM-based system — the weakest match to what this build is meant to showcase. |

## 7. Biggest assumption, and what would disprove it

We're assuming the "Other" free text and reviews actually contain diagnosable signal — that customers write something like "size too small" rather than just "didn't like it." To check: pull 200 raw "Other" entries and see whether a human can sort at least 70% of them into an actionable category. If most turn out to be low-signal noise, the real problem isn't classification — it's that the return-reason taxonomy itself needs to be redesigned before any model can help.
