"""Prompt templates for every model call in the pipeline.

Kept separate from chains.py so the wording can be tuned without touching
the routing/orchestration logic.
"""
from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

CATEGORY_DESCRIPTIONS = """\
- fit: too small, too large, wrong length, wrong shape
- fabric_quality: material, stitching, fading, defects
- wrong_item: different product, size, or color than what was ordered
- changed_mind: no longer wanted, found elsewhere, ordered by mistake
- delivery_damage: arrived torn, broken, stained, or damaged in transit
- other: doesn't fit any of the above, or too vague to tell
"""

RETURN_CLASSIFY_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You classify why a Dhaga & Co. customer returned an item. "
            "Text is often Hinglish (Hindi written in Latin script, mixed "
            "with English) and may contain typos — read it as a fluent "
            "Hinglish speaker would, not literally.\n\n"
            "Categories:\n{categories}\n\n"
            "The customer picked 'Other' on a dropdown and wrote this free "
            "text. If the text is too vague or ambiguous to confidently "
            "pick one category, say so honestly with a low confidence "
            "score rather than guessing.",
        ),
        ("human", "Language hint: {language_hint}\nSKU: {sku}\n\nReturn note: {text}"),
    ]
).partial(categories=CATEGORY_DESCRIPTIONS)

TICKET_CLASSIFY_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You classify the underlying cause of a Dhaga & Co. support "
            "ticket, when the cause matches one of the return-reason "
            "categories below. Text may be Hinglish with typos.\n\n"
            "Categories:\n{categories}\n\n"
            "Many tickets are just 'where is my order' with no "
            "return-reason content — if so, classify as 'other' and say "
            "why in the rationale.",
        ),
        ("human", "Language hint: {language_hint}\n\nTicket: {text}"),
    ]
).partial(categories=CATEGORY_DESCRIPTIONS)

REVIEW_CLASSIFY_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You classify the main complaint, if any, in a Dhaga & Co. "
            "product review. A positive review with no complaint should "
            "be classified 'other' with a note that no issue was raised. "
            "Text may be Hinglish with typos.\n\nCategories:\n{categories}",
        ),
        (
            "human",
            "Language hint: {language_hint}\nSKU: {sku}\nRating: {rating}/5\n\nReview: {text}",
        ),
    ]
).partial(categories=CATEGORY_DESCRIPTIONS)

EVALUATOR_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are auditing a cheaper model's classification of Dhaga & "
            "Co. customer text into return-reason categories. Re-read the "
            "original text yourself and decide independently, then "
            "compare against the first model's answer.\n\n"
            "Categories:\n{categories}\n\n"
            "Only set needs_human=true if you genuinely cannot tell even "
            "after reading carefully — not simply because the first model "
            "was unsure.",
        ),
        (
            "human",
            "Original text: {text}\n\n"
            "First model's classification: {category} (confidence {confidence})\n"
            "First model's rationale: {rationale}",
        ),
    ]
).partial(categories=CATEGORY_DESCRIPTIONS)

NARRATIVE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You write a short weekly summary for Neha, Dhaga & Co.'s "
            "Category Head, based on pre-computed classification counts. "
            "Use only the numbers you're given — never estimate or invent "
            "one. Write in plain, direct language, the way you'd brief a "
            "busy colleague in person.",
        ),
        (
            "human",
            "This week's classified volume: {total} items.\n"
            "Category breakdown: {category_counts}\n"
            "Top SKUs by fit-related returns: {top_fit_skus}\n"
            "Week-over-week change in top category: {trend}",
        ),
    ]
)
