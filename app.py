"""Streamlit dashboard — the MVP's required frontend.

Shows Neha a ranked view of classified returns/tickets/reviews instead of
raw free text, plus a "needs review" queue for anything the pipeline
couldn't confidently label.

Run with: streamlit run app.py
"""
from __future__ import annotations

import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from src.pipeline import (
    CLASSIFY_TEMPERATURE,
    DATABASE_URL,
    EVAL_TEMPERATURE,
    NARRATIVE_TEMPERATURE,
    run_pipeline,
)
from src.storage import (
    get_aggregates,
    get_engine,
    get_latest_narrative,
    get_review_queue,
    get_session,
    init_db,
)

load_dotenv()

st.set_page_config(page_title="Dhaga & Co. — Returns intelligence", layout="wide")
st.title("Returns & review intelligence")
st.caption(
    "Classifies unstructured return reasons, tickets, and reviews so "
    "nobody has to read them a few hundred at a time."
)

engine = get_engine(DATABASE_URL)
init_db(engine)
session = get_session(engine)

with st.sidebar:
    st.header("Run")
    st.write(f"Cheap model: `{os.getenv('CHEAP_MODEL', 'gpt-4o-mini')}`")
    st.write(f"Strong model: `{os.getenv('STRONG_MODEL', 'gpt-4o')}`")
    st.caption(
        f"Classify/evaluate temperature: {CLASSIFY_TEMPERATURE} · "
        f"Narrative temperature: {NARRATIVE_TEMPERATURE}"
    )
    limit = st.number_input(
        "Row limit for this run (0 = all)",
        min_value=0,
        value=50,
        step=50,
        help="Keep this small the first few times — each run costs real API calls.",
    )
    if st.button("Run pipeline", type="primary"):
        with st.spinner("Classifying..."):
            summary = run_pipeline(limit=limit or None)
        st.success(
            f"Processed {summary['processed']} rows, "
            f"{summary['needs_review']} flagged for review."
        )
        st.rerun()

agg = get_aggregates(session)

if agg["total"] == 0:
    st.info("No classified data yet — run the pipeline from the sidebar first.")
    st.stop()

narrative = get_latest_narrative(session)
if narrative:
    st.subheader(narrative.headline)
    st.write(narrative.body)
    if narrative.top_skus:
        st.caption(f"Top SKUs involved: {narrative.top_skus}")

st.divider()

col1, col2, col3 = st.columns(3)
col1.metric("Total classified", agg["total"])
col2.metric("Needs human review", agg["needs_review_count"])
pct_auto = 100 * (1 - agg["needs_review_count"] / agg["total"]) if agg["total"] else 0
col3.metric("Auto-classified", f"{pct_auto:.0f}%")

st.subheader("Category breakdown")
cat_df = pd.DataFrame(
    {"category": list(agg["by_category"].keys()), "count": list(agg["by_category"].values())}
).sort_values("count", ascending=False)
st.bar_chart(cat_df.set_index("category"), height=300)

st.subheader("Needs review")
st.caption(
    "Rows the model couldn't confidently classify, or that failed "
    "validation twice — shown here instead of silently mislabeled."
)
review_rows = get_review_queue(session)
if review_rows:
    review_df = pd.DataFrame(
        [
            {
                "source": r.source,
                "sku": r.sku,
                "text": r.text,
                "model's best guess": r.category,
                "notes": r.notes,
            }
            for r in review_rows
        ]
    )
    st.dataframe(review_df, use_container_width=True, height=300)
else:
    st.write("Nothing flagged right now.")

session.close()
