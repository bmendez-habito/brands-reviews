from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from src.utils.config import settings
from src.api.ml_client import MercadoLibreClient
from src.services.data_service import DataService
from src.services.review_scraper import ReviewCacheService
from src.models.database import get_session

app = FastAPI(
    title="ML Reviews Analyzer", 
    version="0.1.0",
    description="API para consultar productos y reviews de MercadoLibre"
)

# Configurar CORS para permitir el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Frontend Vite
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== ENDPOINTS DE SALUD =====

@app.get("/health")
async def health():
    return {"status": "ok", "debug": settings.DEBUG}


# ===== ENDPOINTS DE BÚSQUEDA EXTERNA =====

@app.get("/api/search")
async def search(q: str = Query(..., min_length=1), site_id: str = Query("MLA"), limit: int = Query(5, ge=1, le=50), offset: int = Query(0, ge=0)):
    """Busca productos en MercadoLibre (API externa)"""
    try:
        client = MercadoLibreClient()
        data = client.search_products(q, site_id=site_id, limit=limit, offset=offset)
        return data
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


# ===== ENDPOINTS DE PRODUCTOS (BASE DE DATOS) =====

@app.get("/api/products")
async def get_products(
    limit: Optional[int] = Query(None, ge=1), 
    offset: int = Query(0, ge=0),
    marca: Optional[str] = Query(None)
):
    """Obtiene productos desde la base de datos"""
    try:
        with get_session() as session:
            service = DataService(session)
            if marca:
                products = service.get_products_by_brand(marca, limit)
            else:
                products = service.get_all_products(limit, offset)
            
            return {
                "products": products,
                "count": len(products),
                "limit": limit,
                "offset": offset
            }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/products/stats")
async def get_products_stats():
    """Obtiene estadísticas generales de productos"""
    try:
        with get_session() as session:
            service = DataService(session)
            stats = service.get_products_stats()
            return stats
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/products/{product_id}")
async def get_product(product_id: str):
    """Obtiene un producto específico por ID"""
    try:
        with get_session() as session:
            service = DataService(session)
            product = service.get_product_by_id(product_id)
            
            if not product:
                raise HTTPException(status_code=404, detail="Producto no encontrado")
            
            return product
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ===== ENDPOINTS DE REVIEWS (BASE DE DATOS) =====

@app.get("/api/reviews")
async def get_reviews(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    rating: Optional[int] = Query(None, ge=1, le=5),
    sentiment: Optional[str] = Query(None, regex="^(positive|negative|neutral)$"),
    recent: bool = Query(False)
):
    """Obtiene reviews desde la base de datos con filtros opcionales"""
    try:
        with get_session() as session:
            service = DataService(session)
            if recent:
                reviews = service.get_recent_reviews(limit)
            elif rating:
                reviews = service.get_reviews_by_rating(rating, limit)
            elif sentiment:
                reviews = service.get_reviews_by_sentiment(sentiment, limit)
            else:
                # Para obtener todas las reviews, usamos un producto específico
                # En una implementación más avanzada, podríamos tener un endpoint global
                reviews = service.get_recent_reviews(limit)
            
            return {
                "reviews": reviews,
                "count": len(reviews),
                "limit": limit,
                "offset": offset,
                "filters": {
                    "rating": rating,
                    "sentiment": sentiment,
                    "recent": recent
                }
            }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/products/{product_id}/reviews")
async def get_product_reviews(
    product_id: str,
    limit: Optional[int] = Query(None, ge=1),
    offset: int = Query(0, ge=0),
    order_by: str = Query("date_created", regex="^(date_created|rate|sentiment_score)$")
):
    """Obtiene reviews de un producto específico"""
    try:
        with get_session() as session:
            service = DataService(session)
            # Verificar que el producto existe
            product = service.get_product_by_id(product_id)
            if not product:
                raise HTTPException(status_code=404, detail="Producto no encontrado")
            
            reviews = service.get_reviews_by_product(product_id, limit, offset, order_by)
            
            return {
                "product_id": product_id,
                "reviews": reviews,
                "count": len(reviews),
                "limit": limit,
                "offset": offset,
                "order_by": order_by
            }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/products/{product_id}/reviews/stats")
async def get_product_reviews_stats(product_id: str):
    """Obtiene estadísticas de reviews de un producto específico"""
    try:
        with get_session() as session:
            service = DataService(session)
            # Verificar que el producto existe
            product = service.get_product_by_id(product_id)
            if not product:
                raise HTTPException(status_code=404, detail="Producto no encontrado")
            
            stats = service.get_reviews_stats(product_id)
            return stats
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/reviews/stats")
async def get_reviews_stats():
    """Obtiene estadísticas generales de reviews"""
    try:
        with get_session() as session:
            service = DataService(session)
            stats = service.get_reviews_stats()
            return stats
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/reviews/timeline")
async def get_reviews_timeline(
    product_id: Optional[str] = Query(None),
    marca: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365)
):
    """Obtiene datos temporales de reviews para gráficos de evolución"""
    try:
        with get_session() as session:
            service = DataService(session)
            timeline = service.get_reviews_timeline(product_id, days, marca)
            return {
                "timeline": timeline,
                "days": days,
                "product_id": product_id,
                "marca": marca
            }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ===== ENDPOINTS DE INGESTA (MANTENER COMPATIBILIDAD) =====

@app.get("/api/items/{item_id}")
async def get_item(item_id: str):
    """Endpoint de compatibilidad - obtiene producto desde API externa o cache"""
    try:
        client = MercadoLibreClient()
        svc = ReviewCacheService(client)
        from src.models.database import get_session
        
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
    """Endpoint de compatibilidad - obtiene reviews desde API externa o cache"""
    try:
        client = MercadoLibreClient()
        svc = ReviewCacheService(client)
        from src.models.database import get_session
        
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
