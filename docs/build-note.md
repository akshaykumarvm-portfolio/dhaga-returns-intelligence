# Build Note — Dhaga & Co. Returns & Review Intelligence

*Two pages maximum, per the brief. Fill in the bracketed parts after your
first real run.*

## Code vs model table

| Step | Code or model | Why |
|---|---|---|
| Ingest & normalize | Code | Reading CSVs, deduping — no judgment required |
| Language hint (Hinglish detection) | Code | Keyword heuristic; only changes prompt wording, not the classification, so it doesn't need a model |
| Route by source | Code | Simple lookup on a known field (`return` / `ticket` / `review`) |
| Classify | Model (cheap) | Reading messy Hinglish free text and mapping it to a cause needs language understanding, not lookup |
| Evaluate & audit | Model (strong) | Judging *whether the first model's read was right* is itself a judgment call, not arithmetic |
| Aggregate & store | Code | Counting and grouping rows already labeled |
| Narrative | Model (strong) | Turning numbers into a sentence a busy person reads is a language task; the numbers themselves come from code, never the model |

## Why each pattern is here

- **Routing** — a return's "Other" box, a support ticket, and a review need different prompt context (different noise, different baseline sentiment). Without it, one prompt has to awkwardly serve three very different inputs.
- **Evaluator-optimizer** — the cheap model alone would either over-trust itself on ambiguous Hinglish, or [TODO: fill in actual disagreement rate once you've run the audit sample] cost real accuracy. Without it, Neha gets a list she can't fully trust; without the cheap model doing the bulk pass first, evaluating everything with the strong model would cost [TODO: recompute below] instead.

## Cost line

Formula: `rows × avg_input_tokens × price_per_token`, computed separately per model tier.

- Cheap model (classify, all rows): `[TODO: total weekly volume] × [TODO: measured avg tokens/row] × [TODO: current price]`
- Strong model (evaluate, ~15–20% of rows + 5% audit sample): `[TODO] × [TODO] × [TODO]`
- Strong model (narrative, ~1 call/week): negligible

At Dhaga & Co.'s actual volume (6,500 unlabeled returns/week alone, before tickets and reviews): **[TODO: fill in once you've measured real token counts from a test run — check current model pricing rather than assuming last quarter's rates]**.

## The thing that broke that we did not expect

[TODO — this is deliberately left blank. Run the pipeline for real and
write down what actually broke: a LangChain version mismatch, a schema
validation edge case, a Hinglish phrase the classifier misreads, a
SQLite locking issue under concurrent runs, whatever it turns out to be.
That's the point of this section — an honest account, not a clean one.]
