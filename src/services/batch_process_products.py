#!/usr/bin/env python3
"""
Proceso que barra todos los productos de la base de datos y use sus URLs
para reprocesar si es necesario (extraer más información o reviews)
"""

import os
import sys
import argparse
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.database import Base
from src.models.product import Product
from src.models.review import Review


def load_env():
    """Carga variables de entorno desde .env"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("⚠️  python-dotenv no está instalado. Usando variables de entorno del sistema.")


def get_db_session():
    """Obtiene una sesión de base de datos"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        database_url = "postgresql://postgres:postgres@localhost:5432/comment_ml_scraper"
    
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def get_all_products(session):
    """Obtiene todos los productos de la base de datos"""
    products = session.query(Product).all()
    return products


def get_product_review_count(session, product_id):
    """Obtiene el número de reviews de un producto"""
    count = session.query(Review).filter(Review.product_id == product_id).count()
    return count


def process_product_extraction(session, product, force_reprocess=False):
    """
    Procesa la extracción de información del producto usando extract_product_simple
    """
    print(f"🔄 Procesando extracción de producto: {product.id}")
    
    # Importar y usar el extractor
    from src.services.extract_product_simple import process_single_url
    
    # Obtener URL del producto
    url = None
    if product.ml_additional_info and 'url' in product.ml_additional_info:
        url = product.ml_additional_info['url']
    
    if not url:
        print(f"❌ No se encontró URL para el producto {product.id}")
        return False
    
    try:
        result = process_single_url(url, skip_existing=not force_reprocess)
        return result.get('success', False)
    except Exception as e:
        print(f"❌ Error procesando {product.id}: {e}")
        return False


def process_product_reviews(session, product, min_reviews=50):
    """
    Procesa la extracción de reviews del producto usando scrape_final
    """
    print(f"📝 Procesando reviews de producto: {product.id}")
    
    # Obtener URL del producto
    url = None
    if product.ml_additional_info and 'url' in product.ml_additional_info:
        url = product.ml_additional_info['url']
    
    if not url:
        print(f"❌ No se encontró URL para el producto {product.id}")
        return False
    
    # Verificar si ya tiene suficientes reviews
    current_reviews = get_product_review_count(session, product.id)
    if current_reviews >= min_reviews:
        print(f"✅ Producto {product.id} ya tiene {current_reviews} reviews (mínimo: {min_reviews})")
        return True
    
    try:
        # Importar y usar scrape_final
        import subprocess
        cmd = [
            sys.executable, '-m', 'src.services.scrape_final',
            '--url', url,
            '--count', str(min_reviews)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Reviews extraídas exitosamente para {product.id}")
            return True
        else:
            print(f"❌ Error extrayendo reviews para {product.id}: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error procesando reviews de {product.id}: {e}")
        return False


def analyze_sentiment_for_product(session, product_id):
    """
    Analiza el sentimiento de las reviews de un producto
    """
    print(f"🧠 Analizando sentimiento para producto: {product_id}")
    
    try:
        # Importar y usar sentiment_analyzer
        import subprocess
        cmd = [
            sys.executable, '-m', 'src.services.sentiment_analyzer',
            '--product-id', product_id
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Sentimiento analizado para {product_id}")
            return True
        else:
            print(f"❌ Error analizando sentimiento para {product_id}: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error analizando sentimiento de {product_id}: {e}")
        return False


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description='Proceso batch para productos en la base de datos')
    parser.add_argument('--action', choices=['extract', 'reviews', 'sentiment', 'all'], 
                       default='all', help='Acción a realizar')
    parser.add_argument('--min-reviews', type=int, default=50,
                       help='Número mínimo de reviews por producto')
    parser.add_argument('--force-reprocess', action='store_true',
                       help='Forzar reprocesamiento de productos existentes')
    parser.add_argument('--product-id', type=str,
                       help='Procesar solo un producto específico')
    
    args = parser.parse_args()
    
    # Cargar variables de entorno
    load_env()
    
    print("🚀 Proceso Batch de Productos")
    print("=" * 60)
    print(f"Acción: {args.action}")
    print(f"Mínimo de reviews: {args.min_reviews}")
    print(f"Forzar reprocesamiento: {args.force_reprocess}")
    print()
    
    # Obtener sesión de base de datos
    session = get_db_session()
    
    try:
        # Obtener productos
        if args.product_id:
            products = session.query(Product).filter(Product.id == args.product_id).all()
            if not products:
                print(f"❌ No se encontró producto con ID: {args.product_id}")
                return
        else:
            products = get_all_products(session)
        
        print(f"📊 Total de productos a procesar: {len(products)}")
        print()
        
        # Estadísticas
        stats = {
            'total': len(products),
            'extract_success': 0,
            'extract_failed': 0,
            'reviews_success': 0,
            'reviews_failed': 0,
            'sentiment_success': 0,
            'sentiment_failed': 0,
            'skipped': 0
        }
        
        # Procesar cada producto
        for i, product in enumerate(products, 1):
            print(f"\n🔍 PRODUCTO {i}/{len(products)}: {product.id}")
            print("-" * 50)
            print(f"Título: {product.title[:80]}...")
            print(f"Marca: {product.marca}")
            print(f"Precio: ${product.price:,.2f}")
            
            # Obtener URL
            url = product.ml_additional_info.get('url', 'N/A') if product.ml_additional_info else 'N/A'
            print(f"URL: {url}")
            
            # Obtener número de reviews actual
            current_reviews = get_product_review_count(session, product.id)
            print(f"Reviews actuales: {current_reviews}")
            
            # Ejecutar acciones según el parámetro
            if args.action in ['extract', 'all']:
                if process_product_extraction(session, product, args.force_reprocess):
                    stats['extract_success'] += 1
                else:
                    stats['extract_failed'] += 1
            
            if args.action in ['reviews', 'all']:
                if process_product_reviews(session, product, args.min_reviews):
                    stats['reviews_success'] += 1
                else:
                    stats['reviews_failed'] += 1
            
            if args.action in ['sentiment', 'all']:
                if current_reviews > 0:
                    if analyze_sentiment_for_product(session, product.id):
                        stats['sentiment_success'] += 1
                    else:
                        stats['sentiment_failed'] += 1
                else:
                    print(f"⏭️  Saltando análisis de sentimiento (sin reviews)")
                    stats['skipped'] += 1
        
        # Resumen final
        print("\n" + "=" * 60)
        print("📊 RESUMEN FINAL:")
        print(f"Total productos: {stats['total']}")
        
        if args.action in ['extract', 'all']:
            print(f"Extracción exitosa: {stats['extract_success']}")
            print(f"Extracción fallida: {stats['extract_failed']}")
        
        if args.action in ['reviews', 'all']:
            print(f"Reviews exitosas: {stats['reviews_success']}")
            print(f"Reviews fallidas: {stats['reviews_failed']}")
        
        if args.action in ['sentiment', 'all']:
            print(f"Sentimiento exitoso: {stats['sentiment_success']}")
            print(f"Sentimiento fallido: {stats['sentiment_failed']}")
            print(f"Saltados (sin reviews): {stats['skipped']}")
        
    finally:
        session.close()


if __name__ == "__main__":
    main()
