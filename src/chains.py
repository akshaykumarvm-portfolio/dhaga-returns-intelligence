"""LangChain chains: routing, classification, evaluation, narrative.

Two model tiers, matching the architecture doc:
- CHEAP model does bulk classification (stage 3).
- STRONG model audits low-confidence/sampled rows (stage 4) and writes
  the weekly narrative (stage 6), at different temperatures.
"""
from __future__ import annotations

import re

from langchain_core.runnables import RunnableBranch

from .prompts import (
    EVALUATOR_PROMPT,
    NARRATIVE_PROMPT,
    RETURN_CLASSIFY_PROMPT,
    REVIEW_CLASSIFY_PROMPT,
    TICKET_CLASSIFY_PROMPT,
)
from .schemas import ClassificationResult, EvaluationResult, NarrativeSummary

# A short list is enough to flag likely Hinglish/vernacular input; it only
# changes which instructions go into the prompt, never the classification
# result itself, so a missed word costs nothing but a slightly plainer
# prompt. This is a heuristic (code), not a model call.
HINGLISH_MARKERS = {
    "hai", "nahi", "bahut", "kar", "kya", "kab", "kaha", "mera", "apne",
    "chahiye", "wala", "gaya", "gayi", "ho", "hoga", "bhi", "tha", "thi",
}


def detect_language_hint(text: str) -> str:
    """Cheap heuristic, not a model call — flags likely Hinglish so the
    classify prompt can tell the model to read it accordingly."""
    words = set(re.findall(r"[a-zA-Z]+", text.lower()))
    return "hinglish" if words & HINGLISH_MARKERS else "english"


def get_llm(model_name: str, temperature: float = 0.0):
    """Routes both the cheap and strong model through OpenRouter's
    OpenAI-compatible endpoint using OPENROUTER_API_KEY. `model_name`
    should use OpenRouter's "provider/model" naming, e.g.
    "openai/gpt-4o-mini" or "anthropic/claude-3.5-sonnet" — see
    openrouter.ai/models for the current list."""
    import os

    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )


def build_classifier_router(cheap_llm) -> RunnableBranch:
    """Routing pattern: picks the classify prompt by source, then runs the
    cheap model with a validated schema as output. Expects `cheap_llm` to
    already be constructed at temperature 0 — consistency matters more
    than creativity for classification."""
    structured_llm = cheap_llm.with_structured_output(ClassificationResult)

    return RunnableBranch(
        (lambda x: x["source"] == "return", RETURN_CLASSIFY_PROMPT | structured_llm),
        (lambda x: x["source"] == "ticket", TICKET_CLASSIFY_PROMPT | structured_llm),
        REVIEW_CLASSIFY_PROMPT | structured_llm,  # default: review
    )


def build_evaluator_chain(strong_llm):
    """Evaluator-optimizer pattern: a strong model re-checks anything the
    cheap model was unsure about, plus a random audit sample. Expects
    `strong_llm` at temperature 0, same reasoning as the classifier."""
    structured_llm = strong_llm.with_structured_output(EvaluationResult)
    return EVALUATOR_PROMPT | structured_llm


def build_narrative_chain(strong_llm):
    """Turns pre-computed aggregate numbers (never model-computed) into
    Neha's weekly summary. Expects `strong_llm` at a slightly higher
    temperature (~0.3) — this is the one business-facing text-generation
    step, as opposed to the judgment-call classification/evaluation steps."""
    structured_llm = strong_llm.with_structured_output(NarrativeSummary)
    return NARRATIVE_PROMPT | structured_llm
