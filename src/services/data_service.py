#!/usr/bin/env python3
"""
Servicio de datos para consultas web
Proporciona métodos para obtener productos y reviews desde la base de datos
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from datetime import datetime
import os

from src.models.database import get_session
from src.models.product import Product
from src.models.review import Review


class DataService:
    """Servicio para consultas de datos desde la base de datos"""
    
    def __init__(self, session: Session):
        self.session = session
    
    # ===== MÉTODOS DE PRODUCTOS =====
    
    def get_all_products(self, limit: Optional[int] = None, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Obtiene todos los productos con paginación
        
        Args:
            limit: Número máximo de productos a retornar
            offset: Número de productos a saltar
            
        Returns:
            Lista de diccionarios con información de productos
        """
        query = self.session.query(Product).order_by(desc(Product.id))
        
        if offset > 0:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        products = query.all()
        
        return [self._product_to_dict(product) for product in products]
    
    def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un producto por su ID
        
        Args:
            product_id: ID del producto
            
        Returns:
            Diccionario con información del producto o None si no existe
        """
        product = self.session.query(Product).filter(Product.id == product_id).first()
        
        if product:
            return self._product_to_dict(product)
        return None
    
    def get_products_by_brand(self, marca: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Obtiene productos filtrados por marca
        
        Args:
            marca: Nombre de la marca
            limit: Número máximo de productos a retornar
            
        Returns:
            Lista de diccionarios con productos de la marca
        """
        query = self.session.query(Product).filter(Product.marca.ilike(f"%{marca}%")).order_by(desc(Product.id))
        
        if limit:
            query = query.limit(limit)
        
        products = query.all()
        
        return [self._product_to_dict(product) for product in products]
    
    def get_products_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas generales de productos
        
        Returns:
            Diccionario con estadísticas
        """
        total_products = self.session.query(Product).count()
        
        # Productos con reviews
        products_with_reviews = self.session.query(Product).join(Review, Product.id == Review.product_id).distinct().count()
        
        # Marcas únicas
        unique_brands = self.session.query(Product.marca).filter(Product.marca != "").distinct().count()
        
        # Precio promedio
        avg_price = self.session.query(Product.price).filter(Product.price > 0).all()
        avg_price_value = sum(p[0] for p in avg_price) / len(avg_price) if avg_price else 0
        
        return {
            "total_products": total_products,
            "products_with_reviews": products_with_reviews,
            "unique_brands": unique_brands,
            "average_price": round(avg_price_value, 2)
        }
    
    # ===== MÉTODOS DE REVIEWS =====
    
    def get_reviews_by_product(self, product_id: str, limit: Optional[int] = None, 
                             offset: int = 0, order_by: str = "date_created") -> List[Dict[str, Any]]:
        """
        Obtiene reviews de un producto específico
        
        Args:
            product_id: ID del producto
            limit: Número máximo de reviews a retornar
            offset: Número de reviews a saltar
            order_by: Campo por el cual ordenar (date_created, rate, sentiment_score)
            
        Returns:
            Lista de diccionarios con información de reviews
        """
        # Validar que el producto existe
        product = self.session.query(Product).filter(Product.id == product_id).first()
        if not product:
            return []
        
        # Construir query
        query = self.session.query(Review).filter(Review.product_id == product_id)
        
        # Ordenamiento
        if order_by == "date_created":
            query = query.order_by(desc(Review.date_created))
        elif order_by == "rate":
            query = query.order_by(desc(Review.rate))
        elif order_by == "sentiment_score":
            query = query.order_by(desc(Review.sentiment_score))
        
        # Paginación
        if offset > 0:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        reviews = query.all()
        
        return [self._review_to_dict(review) for review in reviews]
    
    def get_reviews_by_rating(self, rating: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Obtiene reviews filtradas por calificación
        
        Args:
            rating: Calificación (1-5)
            limit: Número máximo de reviews a retornar
            
        Returns:
            Lista de diccionarios con reviews de la calificación especificada
        """
        query = self.session.query(Review).filter(Review.rate == rating).order_by(desc(Review.date_created))
        
        if limit:
            query = query.limit(limit)
        
        reviews = query.all()
        
        return [self._review_to_dict(review) for review in reviews]
    
    def get_reviews_by_sentiment(self, sentiment: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Obtiene reviews filtradas por sentimiento
        
        Args:
            sentiment: Sentimiento (positive, negative, neutral)
            limit: Número máximo de reviews a retornar
            
        Returns:
            Lista de diccionarios con reviews del sentimiento especificado
        """
        query = self.session.query(Review).filter(Review.sentiment_label == sentiment).order_by(desc(Review.date_created))
        
        if limit:
            query = query.limit(limit)
        
        reviews = query.all()
        
        return [self._review_to_dict(review) for review in reviews]
    
    def get_reviews_stats(self, product_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtiene estadísticas de reviews
        
        Args:
            product_id: ID del producto (opcional, si no se especifica son estadísticas globales)
            
        Returns:
            Diccionario con estadísticas de reviews
        """
        # Query base
        query = self.session.query(Review)
        if product_id:
            query = query.filter(Review.product_id == product_id)
        
        # Total de reviews
        total_reviews = query.count()
        
        if total_reviews == 0:
            return {
                "total_reviews": 0,
                "average_rating": 0,
                "rating_distribution": {},
                "sentiment_distribution": {}
            }
        
        # Rating promedio
        avg_rating = query.with_entities(Review.rate).all()
        avg_rating_value = sum(r[0] for r in avg_rating) / len(avg_rating) if avg_rating else 0
        
        # Distribución de ratings
        rating_dist = {}
        for i in range(1, 6):
            count = query.filter(Review.rate == i).count()
            rating_dist[f"{i}_stars"] = count
        
        # Distribución de sentimientos
        sentiment_dist = {}
        for sentiment in ["positive", "negative", "neutral"]:
            count = query.filter(Review.sentiment_label == sentiment).count()
            sentiment_dist[sentiment] = count
        
        return {
            "total_reviews": total_reviews,
            "average_rating": round(avg_rating_value, 2),
            "rating_distribution": rating_dist,
            "sentiment_distribution": sentiment_dist
        }
    
    def get_recent_reviews(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene las reviews más recientes
        
        Args:
            limit: Número máximo de reviews a retornar
            
        Returns:
            Lista de diccionarios con las reviews más recientes
        """
        reviews = self.session.query(Review).order_by(desc(Review.date_created)).limit(limit).all()
        
        return [self._review_to_dict(review) for review in reviews]
    
    # ===== MÉTODOS AUXILIARES =====
    
    def _product_to_dict(self, product: Product) -> Dict[str, Any]:
        """Convierte un objeto Product a diccionario"""
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
            "ml_additional_info": product.ml_additional_info,
            "url": product.ml_additional_info.get("url") if product.ml_additional_info else None
        }
    
    def _review_to_dict(self, review: Review) -> Dict[str, Any]:
        """Convierte un objeto Review a diccionario"""
        return {
            "id": review.id,
            "product_id": review.product_id,
            "rate": review.rate,
            "title": review.title,
            "content": review.content,
            "date_created": review.date_created.isoformat() if review.date_created else None,
            "reviewer_id": review.reviewer_id,
            "likes": review.likes,
            "dislikes": review.dislikes,
            "sentiment_score": review.sentiment_score,
            "sentiment_label": review.sentiment_label,
            "api_review_id": review.api_review_id,
            "date_text": review.date_text,
            "source": review.source,
            "media": review.media
        }


# ===== FUNCIONES DE CONVENIENCIA =====

def get_all_products(limit: Optional[int] = None, offset: int = 0) -> List[Dict[str, Any]]:
    """Función de conveniencia para obtener todos los productos"""
    with get_session() as session:
        service = DataService(session)
        return service.get_all_products(limit, offset)


def get_product_by_id(product_id: str) -> Optional[Dict[str, Any]]:
    """Función de conveniencia para obtener un producto por ID"""
    with get_session() as session:
        service = DataService(session)
        return service.get_product_by_id(product_id)


def get_reviews_by_product(product_id: str, limit: Optional[int] = None, 
                          offset: int = 0, order_by: str = "date_created") -> List[Dict[str, Any]]:
    """Función de conveniencia para obtener reviews de un producto"""
    with get_session() as session:
        service = DataService(session)
        return service.get_reviews_by_product(product_id, limit, offset, order_by)


def get_products_stats() -> Dict[str, Any]:
    """Función de conveniencia para obtener estadísticas de productos"""
    with get_session() as session:
        service = DataService(session)
        return service.get_products_stats()


def get_reviews_stats(product_id: Optional[str] = None) -> Dict[str, Any]:
    """Función de conveniencia para obtener estadísticas de reviews"""
    with get_session() as session:
        service = DataService(session)
        return service.get_reviews_stats(product_id)
