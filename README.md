---
title: Dhaga Returns Intelligence
emoji: 🧵
colorFrom: purple
colorTo: blue
sdk: streamlit
sdk_version: "1.40.1"
app_file: app.py
pinned: false
license: apache-2.0
short_description: dhaga
---

# Dhaga & Co. — Returns & Review Intelligence

Classifies unstructured "Other" return reasons, support tickets, and product
reviews into a small set of actionable causes (fit, fabric/quality, wrong
item, changed mind, delivery damage, other), so Neha can review a ranked
list instead of reading raw text a few hundred rows at a time.

See `docs/discovery-note.md` for the problem statement, evidence, and
ranked shortlist.

## Quickstart (5 minutes)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then add your API key(s)
python scripts/generate_synthetic_data.py
streamlit run app.py
```

## What it expects

Input rows with a `source` (`return` / `ticket` / `review`) and a
free-text field, shaped like real Dhaga & Co. data: Hinglish mixed with
English, typos, and the "Other" free-text box. See
`scripts/generate_synthetic_data.py` for the exact schema — it also writes
a hidden `true_category` column, used only to measure classifier/evaluator
accuracy, never fed to a model.

## What it does when something goes wrong

A row that fails schema validation twice, or that the evaluator marks
`needs_human`, shows up in the dashboard's "Needs review" queue instead of
being silently mislabeled.

## Structure

```
.
├── app.py                          # Streamlit dashboard (entry point)
├── requirements.txt
├── .env.example
├── docs/
│   ├── discovery-note.md           # problem, evidence, ranked shortlist
│   └── build-note.md               # code/model table, cost line (add during build)
├── scripts/
│   └── generate_synthetic_data.py  # real-shaped synthetic returns/tickets/reviews
├── src/
│   ├── schemas.py                  # Pydantic models for every model boundary
│   ├── prompts.py                  # prompt templates, per source/language
│   ├── chains.py                   # router, classifier, evaluator, narrative chains
│   ├── pipeline.py                 # orchestrates ingest -> route -> classify ->
│   │                                #   evaluate -> aggregate -> store -> narrate
│   └── storage.py                  # SQLite/Postgres read/write
└── data/                           # generated CSVs + local DB (gitignored)
```

## A note on testing

Every file here passed `python -m py_compile` (syntax-checked), and
`scripts/generate_synthetic_data.py` was run end to end and produces real
output. The LangChain/SQLAlchemy/Streamlit-dependent files
(`chains.py`, `pipeline.py`, `storage.py`, `app.py`) were **not**
runtime-tested against live packages or a real API key — they were
written offline, without network access to `pip install` and verify
against the current LangChain API surface. Before you build on top of
this:

1. `pip install -r requirements.txt`, then `pip freeze > requirements.txt`
   to pin what actually installed.
2. `python scripts/generate_synthetic_data.py --n-returns 20 --n-tickets 20 --n-reviews 20`
   for a small dataset.
3. `python -m src.pipeline` with a real API key set in `.env` — this is
   where you'll find any LangChain version drift (`with_structured_output`,
   `RunnableBranch`, `ChatPromptTemplate.partial` are all stable APIs, but
   double-check against your installed version if something errors).
4. Only then `streamlit run app.py`.

Record what actually breaks in `docs/build-note.md` — that's the "thing
that broke that you did not expect" the brief asks for, and this step is
exactly where it'll show up.
