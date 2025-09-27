from __future__ import annotations

from sqlalchemy import String, Integer, Float, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional, Dict, Any
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from .database import Base


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    product_id: Mapped[str] = mapped_column(String(32), index=True)
    rate: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(255), default="")
    content: Mapped[str] = mapped_column(Text)
    date_created: Mapped[datetime] = mapped_column(DateTime)
    reviewer_id: Mapped[str] = mapped_column(String(64), default="")
    likes: Mapped[int] = mapped_column(Integer, default=0)
    dislikes: Mapped[int] = mapped_column(Integer, default=0)
    sentiment_score: Mapped[float] = mapped_column(Float, default=0.0)
    sentiment_label: Mapped[str] = mapped_column(String(16), default="neutral")

    # Nuevos campos
    api_review_id: Mapped[str] = mapped_column(String(64), default="")
    date_text: Mapped[str] = mapped_column(String(64), default="")
    source: Mapped[str] = mapped_column(String(16), default="api")
    media: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    raw_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        Index("ix_reviews_product_date", "product_id", "date_created"),
    )


