from __future__ import annotations

import argparse
from typing import List

from src.api.ml_client import MercadoLibreClient
from src.models.database import get_session, init_db
from src.services.review_scraper import ReviewCacheService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch fetch reviews for items and store to DB")
    parser.add_argument("--items", type=str, required=True, help="Comma-separated item IDs (e.g. MLA123,MLA456)")
    parser.add_argument("--count", type=int, default=100, help="Total reviews to fetch per item (default: 100)")
    parser.add_argument("--page-size", type=int, default=50, help="Page size per request (<=50)")
    parser.add_argument("--offset", type=int, default=0, help="Initial offset")
    return parser.parse_args()


def run(items: List[str], count: int, page_size: int, offset: int) -> None:
    init_db()
    client = MercadoLibreClient()
    svc = ReviewCacheService(client)
    with get_session() as db:
        for item_id in items:
            svc.get_or_fetch_product(db, item_id)
            remaining = max(0, count)
            current_offset = max(0, offset)
            while remaining > 0:
                limit = min(page_size, remaining, 50)
                svc.fetch_and_store_reviews(db, item_id, limit=limit, offset=current_offset)
                current_offset += limit
                remaining -= limit


def main() -> None:
    args = parse_args()
    items = [s.strip() for s in args.items.split(",") if s.strip()]
    if not items:
        raise SystemExit("No items provided")
    run(items=items, count=args.count, page_size=args.page_size, offset=args.offset)


if __name__ == "__main__":
    main()


