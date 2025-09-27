#!/usr/bin/env python3
"""
Servicio para analizar el sentimiento de las reviews
Completa los campos sentiment_score y sentiment_label para reviews que no los tengan
"""

import argparse
from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import and_, or_
from textblob import TextBlob

from src.models.database import get_session
from src.models.review import Review


def analyze_sentiment(text: str) -> tuple[float, str]:
    """
    Analiza el sentimiento de un texto usando TextBlob con mejoras para español
    
    Args:
        text: Texto a analizar
        
    Returns:
        tuple: (sentiment_score, sentiment_label)
    """
    if not text or not text.strip():
        return 0.0, "neutral"
    
    # Limpiar y normalizar el texto
    text = text.lower().strip()
    
    # Palabras clave en español para ajustar el análisis
    positive_words = [
        'excelente', 'perfecto', 'genial', 'fantástico', 'increíble', 'maravilloso',
        'recomendado', 'bueno', 'buena', 'buen', 'buenas', 'buenos', 'súper',
        'genial', 'perfecta', 'excelente', 'increíble', 'maravillosa', 'fantástica',
        'cumple', 'cumplió', 'superó', 'excede', 'excedió', 'mejor', 'mejora',
        'feliz', 'contento', 'satisfecho', 'satisfecha', 'recomiendo', 'recomienda',
        'vale', 'valió', 'valió la pena', 'útil', 'práctico', 'fácil', 'rápido'
    ]
    
    negative_words = [
        'malo', 'mala', 'mal', 'pésimo', 'pésima', 'terrible', 'horrible',
        'no funciona', 'no sirve', 'defectuoso', 'defectuosa', 'roto', 'rota',
        'lento', 'lenta', 'difícil', 'complicado', 'complicada', 'confuso',
        'confusa', 'mal', 'malo', 'mala', 'descontento', 'descontenta',
        'insatisfecho', 'insatisfecha', 'decepcionado', 'decepcionada',
        'no recomiendo', 'no lo recomiendo', 'no la recomiendo', 'basura',
        'perdida', 'pérdida', 'tiempo perdido', 'dinero perdido'
    ]
    
    # Contar palabras positivas y negativas
    positive_count = sum(1 for word in positive_words if word in text)
    negative_count = sum(1 for word in negative_words if word in text)
    
    # Crear objeto TextBlob
    blob = TextBlob(text)
    
    # Obtener polaridad base (-1.0 a 1.0)
    polarity = blob.sentiment.polarity
    
    # Ajustar polaridad basado en palabras clave en español
    if positive_count > 0:
        polarity += (positive_count * 0.3)  # Aumentar positividad
    if negative_count > 0:
        polarity -= (negative_count * 0.3)  # Aumentar negatividad
    
    # Limitar entre -1 y 1
    polarity = max(-1.0, min(1.0, polarity))
    
    # Convertir a escala 0-1 para nuestro sistema
    sentiment_score = (polarity + 1) / 2  # -1,1 -> 0,1
    
    # Determinar label con umbrales más estrictos
    if sentiment_score >= 0.6:
        sentiment_label = "positive"
    elif sentiment_score <= 0.4:
        sentiment_label = "negative"
    else:
        sentiment_label = "neutral"
    
    return sentiment_score, sentiment_label


def get_reviews_to_process(from_date: Optional[date] = None) -> List[Review]:
    """
    Obtiene las reviews que necesitan análisis de sentimiento
    
    Args:
        from_date: Fecha opcional para filtrar reviews desde esa fecha
        
    Returns:
        List[Review]: Lista de reviews que necesitan procesamiento
    """
    with get_session() as db:
        # Query base: reviews que no tienen sentiment_score o sentiment_label
        query = db.query(Review).filter(
            or_(
                Review.sentiment_score == 0.0,
                Review.sentiment_label == "neutral",
                Review.sentiment_score.is_(None),
                Review.sentiment_label.is_(None)
            )
        )
        
        # Filtrar por fecha si se proporciona
        if from_date:
            query = query.filter(Review.date_created >= from_date)
        
        # Ordenar por fecha de creación (más recientes primero)
        query = query.order_by(Review.date_created.desc())
        
        return query.all()


def process_review_sentiment(review: Review) -> bool:
    """
    Procesa el sentimiento de una review individual
    
    Args:
        review: Review a procesar
        
    Returns:
        bool: True si se procesó exitosamente, False en caso contrario
    """
    try:
        # Combinar título y contenido para análisis
        full_text = ""
        if review.title:
            full_text += review.title + " "
        if review.content:
            full_text += review.content
        
        if not full_text.strip():
            print(f"⚠️  Review {review.id} no tiene texto para analizar")
            return False
        
        # Analizar sentimiento
        sentiment_score, sentiment_label = analyze_sentiment(full_text)
        
        # Actualizar la review
        review.sentiment_score = sentiment_score
        review.sentiment_label = sentiment_label
        
        return True
        
    except Exception as e:
        print(f"❌ Error procesando review {review.id}: {e}")
        return False


def process_reviews_batch(reviews: List[Review], batch_size: int = 100) -> dict:
    """
    Procesa un lote de reviews en batch
    
    Args:
        reviews: Lista de reviews a procesar
        batch_size: Tamaño del batch para commits
        
    Returns:
        dict: Estadísticas del procesamiento
    """
    stats = {
        "total": len(reviews),
        "processed": 0,
        "errors": 0,
        "skipped": 0
    }
    
    if not reviews:
        print("📝 No hay reviews para procesar")
        return stats
    
    print(f"🔄 Procesando {len(reviews)} reviews...")
    
    with get_session() as db:
        for i, review in enumerate(reviews):
            try:
                # Procesar sentimiento
                if process_review_sentiment(review):
                    stats["processed"] += 1
                    print(f"✅ Review {review.id}: {review.sentiment_label} ({review.sentiment_score:.3f})")
                else:
                    stats["skipped"] += 1
                
                # Commit cada batch_size reviews
                if (i + 1) % batch_size == 0:
                    db.commit()
                    print(f"💾 Guardado batch de {batch_size} reviews")
                
            except Exception as e:
                stats["errors"] += 1
                print(f"❌ Error en review {review.id}: {e}")
                db.rollback()
        
        # Commit final
        db.commit()
    
    return stats


def main():
    """Función principal del servicio"""
    parser = argparse.ArgumentParser(description="Analizar sentimiento de reviews")
    parser.add_argument(
        "--from-date",
        type=str,
        help="Fecha de inicio (YYYY-MM-DD) para procesar reviews desde esa fecha"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Tamaño del batch para commits (default: 100)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Solo mostrar cuántas reviews se procesarían sin hacer cambios"
    )
    
    args = parser.parse_args()
    
    # Parsear fecha si se proporciona
    from_date = None
    if args.from_date:
        try:
            from_date = datetime.strptime(args.from_date, "%Y-%m-%d").date()
            print(f"📅 Procesando reviews desde: {from_date}")
        except ValueError:
            print("❌ Formato de fecha inválido. Use YYYY-MM-DD")
            return
    
    print("🚀 Servicio de Análisis de Sentimiento")
    print("=" * 50)
    
    # Obtener reviews a procesar
    reviews = get_reviews_to_process(from_date)
    
    print(f"📊 Reviews encontradas para procesar: {len(reviews)}")
    
    if args.dry_run:
        print("\n🔍 MODO DRY-RUN - No se harán cambios")
        for i, review in enumerate(reviews[:10], 1):  # Mostrar solo las primeras 10
            print(f"  {i}. {review.id} - {review.date_created} - '{review.title[:50]}...'")
        if len(reviews) > 10:
            print(f"  ... y {len(reviews) - 10} más")
        return
    
    if not reviews:
        print("✅ No hay reviews que necesiten procesamiento")
        return
    
    # Procesar reviews
    stats = process_reviews_batch(reviews, args.batch_size)
    
    # Mostrar estadísticas finales
    print("\n" + "=" * 50)
    print("📊 ESTADÍSTICAS FINALES:")
    print(f"✅ Total procesadas: {stats['processed']}")
    print(f"⚠️  Saltadas: {stats['skipped']}")
    print(f"❌ Errores: {stats['errors']}")
    print(f"📝 Total encontradas: {stats['total']}")
    
    # Mostrar distribución de sentimientos
    if stats['processed'] > 0:
        print(f"\n📈 Distribución de sentimientos:")
        with get_session() as db:
            positive = db.query(Review).filter(Review.sentiment_label == "positive").count()
            negative = db.query(Review).filter(Review.sentiment_label == "negative").count()
            neutral = db.query(Review).filter(Review.sentiment_label == "neutral").count()
            
            print(f"  😊 Positivas: {positive}")
            print(f"  😞 Negativas: {negative}")
            print(f"  😐 Neutrales: {neutral}")


if __name__ == "__main__":
    main()
