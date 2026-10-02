"""Orchestrates the full pipeline: ingest -> route -> classify -> evaluate
-> aggregate -> store -> narrate.

Run directly for a one-off batch:
    python -m src.pipeline

Or import `run_pipeline()` from app.py to trigger it from the dashboard.
"""
from __future__ import annotations

import json
import os
import random
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from .chains import (
    build_classifier_router,
    build_evaluator_chain,
    build_narrative_chain,
    detect_language_hint,
    get_llm,
)
from .storage import get_aggregates, get_engine, get_session, init_db, save_items, save_narrative

load_dotenv()

DATA_DIR = Path("data")
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.7"))
AUDIT_SAMPLE_RATE = float(os.getenv("AUDIT_SAMPLE_RATE", "0.05"))
CHEAP_MODEL = os.getenv("CHEAP_MODEL", "gpt-4o-mini")
STRONG_MODEL = os.getenv("STRONG_MODEL", "gpt-4o")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/dhaga.db")

# Classification/evaluation stay deterministic (consistency matters more
# than creativity for a judgment call); narrative gets a little room to
# write in plain language. Named here so the dashboard can show them.
CLASSIFY_TEMPERATURE = 0.0
EVAL_TEMPERATURE = 0.0
NARRATIVE_TEMPERATURE = 0.3


def load_raw_rows() -> list[dict]:
    """Ingest & normalize (stage 1, code only): reads the three synthetic
    CSVs and maps each into one common row shape."""
    rows: list[dict] = []

    returns_path = DATA_DIR / "synthetic_returns.csv"
    if returns_path.exists():
        for _, r in pd.read_csv(returns_path).iterrows():
            rows.append(
                {
                    "id": r["return_id"],
                    "source": "return",
                    "sku": r["sku"],
                    "order_id": r["order_id"],
                    "rating": None,
                    "text": r["free_text"],
                }
            )

    tickets_path = DATA_DIR / "synthetic_tickets.csv"
    if tickets_path.exists():
        for _, r in pd.read_csv(tickets_path).iterrows():
            rows.append(
                {
                    "id": r["ticket_id"],
                    "source": "ticket",
                    "sku": None,
                    "order_id": r["order_id"],
                    "rating": None,
                    "text": r["message"],
                }
            )

    reviews_path = DATA_DIR / "synthetic_reviews.csv"
    if reviews_path.exists():
        for _, r in pd.read_csv(reviews_path).iterrows():
            rows.append(
                {
                    "id": r["review_id"],
                    "source": "review",
                    "sku": r["sku"],
                    "order_id": None,
                    "rating": r["rating"],
                    "text": r["review_text"],
                }
            )

    if not rows:
        raise FileNotFoundError(
            "No input CSVs found in data/. Run scripts/generate_synthetic_data.py first."
        )
    return rows


def classify_with_fallback(router, row: dict) -> dict:
    """Runs the classifier chain with one retry on a validation/parsing
    failure. If both attempts fail, the row fails visibly (flagged for
    human review) rather than getting a guessed label."""
    payload = {**row, "language_hint": detect_language_hint(row["text"])}
    last_error: Exception | None = None
    for _ in range(2):
        try:
            result = router.invoke(payload)
            return {
                "category": result.category,
                "confidence": result.confidence,
                "rationale": result.rationale,
                "parse_failed": False,
            }
        except Exception as exc:  # noqa: BLE001 - any provider/schema failure should fall back, not crash the run
            last_error = exc
    return {
        "category": "other",
        "confidence": 0.0,
        "rationale": f"Classifier failed twice: {last_error}",
        "parse_failed": True,
    }


def run_pipeline(limit: int | None = None) -> dict:
    """Runs the full pipeline once and returns a small summary dict.
    `limit` caps rows processed — use it for a cheap test run before
    spending on the full dataset."""
    rows = load_raw_rows()
    if limit:
        rows = rows[:limit]

    cheap_llm = get_llm(CHEAP_MODEL, temperature=CLASSIFY_TEMPERATURE)
    strong_llm_eval = get_llm(STRONG_MODEL, temperature=EVAL_TEMPERATURE)
    strong_llm_narrative = get_llm(STRONG_MODEL, temperature=NARRATIVE_TEMPERATURE)

    router = build_classifier_router(cheap_llm)
    evaluator = build_evaluator_chain(strong_llm_eval)
    narrator = build_narrative_chain(strong_llm_narrative)

    classified = []
    for row in rows:
        result = classify_with_fallback(router, row)
        needs_evaluation = (
            not result["parse_failed"]
            and (result["confidence"] < CONFIDENCE_THRESHOLD or random.random() < AUDIT_SAMPLE_RATE)
        )

        item = {
            "id": row["id"],
            "source": row["source"],
            "sku": row["sku"],
            "order_id": row["order_id"],
            "text": row["text"],
            "category": result["category"],
            "confidence": result["confidence"],
            "was_evaluated": False,
            "agrees_with_classifier": None,
            "needs_human": result["parse_failed"],
            "notes": result["rationale"],
        }

        if needs_evaluation:
            try:
                eval_result = evaluator.invoke(
                    {
                        "text": row["text"],
                        "category": result["category"],
                        "confidence": result["confidence"],
                        "rationale": result["rationale"],
                    }
                )
                item.update(
                    {
                        "category": eval_result.final_category,
                        "was_evaluated": True,
                        "agrees_with_classifier": eval_result.agrees_with_classifier,
                        "needs_human": eval_result.needs_human,
                        "notes": eval_result.notes,
                    }
                )
            except Exception as exc:  # noqa: BLE001 - evaluator failure also fails visibly, not silently
                item["needs_human"] = True
                item["notes"] = f"Evaluator failed: {exc}"

        classified.append(item)

    engine = get_engine(DATABASE_URL)
    init_db(engine)
    session = get_session(engine)
    save_items(session, classified)

    agg = get_aggregates(session)
    narrative_input = {
        "total": len(classified),
        "category_counts": json.dumps(agg["by_category"]),
        "top_fit_skus": json.dumps(agg["top_fit_skus"]),
        "trend": "not enough history yet",  # first run has no prior week to compare
    }
    try:
        narrative = narrator.invoke(narrative_input)
        save_narrative(session, narrative.headline, narrative.body, narrative.top_skus)
    except Exception as exc:  # noqa: BLE001
        save_narrative(session, "Narrative unavailable", str(exc), [])

    session.close()
    return {"processed": len(classified), "needs_review": agg["needs_review_count"]}


if __name__ == "__main__":
    print(run_pipeline())
