#!/usr/bin/env python3
"""
Script para verificar el total de datos en la base de datos
"""

from src.models.database import get_session
from src.models.product import Product
from src.models.review import Review
from sqlalchemy import func

def check_total_data():
    with get_session() as session:
        # Contar productos
        product_count = session.query(func.count(Product.id)).scalar()
        print(f"📊 Total de productos: {product_count}")
        
        # Contar reviews
        review_count = session.query(func.count(Review.id)).scalar()
        print(f"📊 Total de reviews: {review_count}")
        
        # Reviews por producto
        print("\n📋 Reviews por producto:")
        products = session.query(Product).all()
        for product in products:
            product_reviews = session.query(func.count(Review.id)).filter(Review.product_id == product.id).scalar()
            print(f"  {product.id}: {product_reviews} reviews")
            print(f"    Título: {product.title[:50]}...")
        
        # Mostrar algunos reviews de ejemplo
        print("\n📝 Algunos reviews de ejemplo:")
        reviews = session.query(Review).filter(Review.content != '').limit(5).all()
        for i, review in enumerate(reviews, 1):
            print(f"  {i}. Rating: {review.rate}/5")
            print(f"     Contenido: {review.content[:100]}...")
            print()

if __name__ == "__main__":
    check_total_data()
