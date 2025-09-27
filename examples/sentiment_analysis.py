#!/usr/bin/env python3
"""
Ejemplos de uso del servicio de análisis de sentimiento
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.sentiment_analyzer import (
    analyze_sentiment, 
    get_reviews_to_process, 
    process_reviews_batch
)
from datetime import date

def example_analyze_text():
    """Ejemplo de análisis de texto individual"""
    print("🔍 Ejemplo de análisis de texto:")
    
    texts = [
        "Excelente producto, muy recomendado!",
        "Muy malo, no funciona nada",
        "Está bien, cumple su función",
        "Increíble calidad, superó mis expectativas",
        "Pésimo servicio, no lo recomiendo para nada"
    ]
    
    for text in texts:
        score, label = analyze_sentiment(text)
        print(f"  '{text}' -> {label} ({score:.3f})")

def example_get_reviews():
    """Ejemplo de obtener reviews a procesar"""
    print("\n📊 Ejemplo de reviews a procesar:")
    
    # Todas las reviews sin análisis
    reviews = get_reviews_to_process()
    print(f"  Total reviews sin análisis: {len(reviews)}")
    
    # Reviews desde una fecha específica
    from_date = date(2024, 1, 1)
    reviews_from_date = get_reviews_to_process(from_date)
    print(f"  Reviews desde {from_date}: {len(reviews_from_date)}")

def example_process_batch():
    """Ejemplo de procesamiento en batch"""
    print("\n🔄 Ejemplo de procesamiento en batch:")
    
    reviews = get_reviews_to_process()
    if reviews:
        print(f"  Procesando {len(reviews)} reviews...")
        stats = process_reviews_batch(reviews[:5])  # Solo las primeras 5 como ejemplo
        print(f"  Estadísticas: {stats}")
    else:
            print("  No hay reviews para procesar")

def example_extract_product():
    """Ejemplo de uso del extractor de productos"""
    print("\n🛍️ Ejemplo de extractor de productos:")
    print("  python -m src.services.extract_product_simple")
    print("  python -m src.services.extract_product_simple 'https://.../p/MLA25265609'")

if __name__ == "__main__":
    print("🚀 Ejemplos de Análisis de Sentimiento")
    print("=" * 50)
    
    example_analyze_text()
    example_get_reviews()
    example_process_batch()
    example_extract_product()
