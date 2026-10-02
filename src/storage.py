"""SQLite/Postgres storage layer (stage 5, plus narrative storage for
stage 6). Everything here is deterministic code — no model calls.
"""
from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy import Boolean, Column, DateTime, Float, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class ClassifiedItem(Base):
    __tablename__ = "classified_items"

    id = Column(String, primary_key=True)
    source = Column(String, nullable=False)  # return | ticket | review
    sku = Column(String, nullable=True)
    order_id = Column(String, nullable=True)
    text = Column(Text, nullable=False)
    category = Column(String, nullable=False)  # final category, post-evaluation if applicable
    confidence = Column(Float, nullable=True)  # classifier's original confidence
    was_evaluated = Column(Boolean, default=False)
    agrees_with_classifier = Column(Boolean, nullable=True)
    needs_human = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)


class Narrative(Base):
    __tablename__ = "narratives"

    id = Column(String, primary_key=True)
    headline = Column(Text, nullable=False)
    body = Column(Text, nullable=False)
    top_skus = Column(Text, nullable=True)  # comma-joined; fine for an MVP
    created_at = Column(DateTime, default=dt.datetime.utcnow)


def get_engine(database_url: str):
    return create_engine(database_url, future=True)


def init_db(engine) -> None:
    Base.metadata.create_all(engine)


def get_session(engine):
    return sessionmaker(bind=engine, future=True)()


def save_items(session, items: list[dict]) -> None:
    """Upserts by primary key so re-running the pipeline on the same rows
    updates them instead of duplicating."""
    for item in items:
        session.merge(ClassifiedItem(**item))
    session.commit()


def save_narrative(session, headline: str, body: str, top_skus: list[str]) -> None:
    session.add(
        Narrative(
            id=str(uuid.uuid4()),
            headline=headline,
            body=body,
            top_skus=", ".join(top_skus),
        )
    )
    session.commit()


def get_latest_narrative(session) -> Narrative | None:
    return session.query(Narrative).order_by(Narrative.created_at.desc()).first()


def get_aggregates(session) -> dict:
    """Plain counting over rows already in the DB — no model involved."""
    rows = session.query(ClassifiedItem).all()
    by_category: dict[str, int] = {}
    fit_sku_counts: dict[str, int] = {}
    needs_review_count = 0

    for row in rows:
        by_category[row.category] = by_category.get(row.category, 0) + 1
        if row.needs_human:
            needs_review_count += 1
        if row.category == "fit" and row.sku:
            fit_sku_counts[row.sku] = fit_sku_counts.get(row.sku, 0) + 1

    top_fit_skus = sorted(fit_sku_counts, key=fit_sku_counts.get, reverse=True)[:5]

    return {
        "by_category": by_category,
        "top_fit_skus": top_fit_skus,
        "needs_review_count": needs_review_count,
        "total": len(rows),
    }


def get_review_queue(session, limit: int = 200) -> list[ClassifiedItem]:
    return session.query(ClassifiedItem).filter_by(needs_human=True).limit(limit).all()


def get_recent_items(session, limit: int = 500) -> list[ClassifiedItem]:
    return (
        session.query(ClassifiedItem)
        .order_by(ClassifiedItem.created_at.desc())
        .limit(limit)
        .all()
    )
