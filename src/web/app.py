from fastapi import FastAPI, Query, HTTPException
from src.utils.config import settings
from src.api.ml_client import MercadoLibreClient
from src.models.database import get_session
from src.services.review_scraper import ReviewCacheService

app = FastAPI(title="ML Reviews Analyzer", version="0.1.0")

@app.get("/health")
async def health():
    return {"status": "ok", "debug": settings.DEBUG}


@app.get("/api/search")
async def search(q: str = Query(..., min_length=1), site_id: str = Query("MLA"), limit: int = Query(5, ge=1, le=50), offset: int = Query(0, ge=0)):
    try:
        client = MercadoLibreClient()
        data = client.search_products(q, site_id=site_id, limit=limit, offset=offset)
        return data
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.get("/api/items/{item_id}")
async def get_item(item_id: str):
    try:
        client = MercadoLibreClient()
        svc = ReviewCacheService(client)
        with get_session() as db:
            product = svc.get_or_fetch_product(db, item_id)
            return {
                "id": product.id,
                "title": product.title,
                "price": product.price,
                "site_id": product.site_id,
                "currency_id": product.currency_id,
                "sold_quantity": product.sold_quantity,
                "available_quantity": product.available_quantity,
                "marca": product.marca,
                "modelo": product.modelo,
                "caracteristicas": product.caracteristicas,
            }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.get("/api/items/{item_id}/reviews")
async def get_item_reviews(item_id: str, limit: int = Query(20, ge=1, le=50), offset: int = Query(0, ge=0), refresh: bool = Query(False)):
    try:
        client = MercadoLibreClient()
        svc = ReviewCacheService(client)
        with get_session() as db:
            if refresh:
                svc.get_or_fetch_product(db, item_id)
                svc.fetch_and_store_reviews(db, item_id, limit=limit, offset=offset)
            reviews = svc.get_reviews_cached(db, item_id, limit=limit, offset=offset)
            return {
                "item_id": item_id,
                "count": len(reviews),
                "reviews": [
                    {
                        "id": r.id,
                        "product_id": r.product_id,
                        "rate": r.rate,
                        "title": r.title,
                        "content": r.content,
                        "date_created": r.date_created.isoformat(),
                        "date_text": r.date_text,
                        "reviewer_id": r.reviewer_id,
                        "likes": r.likes,
                        "dislikes": r.dislikes,
                        "sentiment_score": r.sentiment_score,
                        "sentiment_label": r.sentiment_label,
                        "api_review_id": r.api_review_id,
                        "source": r.source,
                        "media": r.media,
                    }
                    for r in reviews
                ],
            }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
