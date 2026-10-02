"""Pydantic schemas for every model boundary in the pipeline.

Keeping these separate from prompts/chains means the same schema
validates output regardless of which model (cheap or strong) produced it,
and gives the pipeline a single place to change if the taxonomy changes.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Category = Literal[
    "fit",
    "fabric_quality",
    "wrong_item",
    "changed_mind",
    "delivery_damage",
    "other",
]


class ClassificationResult(BaseModel):
    """Output of the cheap-model classifier chain (stage 3)."""

    category: Category
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = Field(
        description=(
            "One short sentence explaining the classification, "
            "quoting the input where useful."
        )
    )


class EvaluationResult(BaseModel):
    """Output of the strong-model evaluator chain (stage 4).

    Runs on anything below CONFIDENCE_THRESHOLD, plus a random audit
    sample of high-confidence rows (see .env.example).
    """

    final_category: Category
    agrees_with_classifier: bool
    needs_human: bool = Field(
        description=(
            "True if even the strong model isn't confident enough to "
            "auto-label this row. Routes to the review queue."
        )
    )
    notes: str


class NarrativeSummary(BaseModel):
    """Output of the strong-model narrative chain (stage 6), shown on the dashboard."""

    headline: str = Field(description="One sentence, in Neha's language.")
    body: str = Field(description="2-4 sentences of supporting detail.")
    top_skus: list[str] = Field(default_factory=list)
