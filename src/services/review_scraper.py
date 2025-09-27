from __future__ import annotations

from datetime import datetime
from typing import List, Dict, Any

from sqlalchemy.orm import Session

from src.api.ml_client import MercadoLibreClient
from src.models.review import Review
from src.models.product import Product


class ReviewCacheService:
    def __init__(self, client: MercadoLibreClient) -> None:
        self.client = client

    def get_or_fetch_product(self, db: Session, item_id: str, site_id_hint: str | None = None, title_hint: str | None = None) -> Product:
        prod = db.get(Product, item_id)
        if prod is not None:
            return prod
        data = self.client.get_product_info(item_id)
        prod = Product(
            id=data.get("id", item_id),
            title=(data.get("title") or title_hint or f"Item {item_id}"),
            price=float(data.get("price") or 0.0),
            site_id=(data.get("site_id") or site_id_hint or "MLA"),
            currency_id=data.get("currency_id", "ARS"),
            sold_quantity=int(data.get("sold_quantity") or 0),
            available_quantity=int(data.get("available_quantity") or 0),
            marca=data.get("marca", ""),
            modelo=data.get("modelo", ""),
            caracteristicas=data.get("caracteristicas"),
        )
        db.add(prod)
        db.flush()
        return prod

    def get_reviews_cached(self, db: Session, item_id: str, limit: int = 50, offset: int = 0) -> List[Review]:
        q = (
            db.query(Review)
            .filter(Review.product_id == item_id)
            .order_by(Review.date_created.desc())
        )
        return q.offset(offset).limit(limit).all()

    def fetch_and_store_reviews(self, db: Session, item_id: str, limit: int = 50, offset: int = 0) -> List[Review]:
        payload = self.client.get_product_reviews(item_id, limit=limit, offset=offset)
        reviews_raw: List[Dict[str, Any]] = payload.get("reviews") or payload.get("results") or []

        stored: List[Review] = []
        for r in reviews_raw:
            rid = str(r.get("id"))
            if not rid:
                continue
            existing = db.get(Review, rid)
            if existing:
                stored.append(existing)
                continue
            review = Review(
                id=rid,
                product_id=item_id,
                rate=int(r.get("rate") or 0),
                title=str(r.get("title") or ""),
                content=str(r.get("content") or r.get("text") or ""),
                date_created=_parse_date(r.get("date_created") or r.get("date") or datetime.utcnow().isoformat()),
                reviewer_id=str(r.get("reviewer_id") or r.get("user_id") or ""),
                likes=int(r.get("likes") or 0),
                dislikes=int(r.get("dislikes") or 0),
                sentiment_score=0.0,
                sentiment_label="neutral",
                api_review_id=str(r.get("api_review_id") or ""),
                date_text=str(r.get("date_text") or ""),
                source=str(r.get("source") or "api"),
                media=r.get("media"),
                raw_json=r.get("raw_json"),
            )
            db.add(review)
            stored.append(review)
        db.flush()
        return stored


def _parse_date(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return datetime.utcnow()


