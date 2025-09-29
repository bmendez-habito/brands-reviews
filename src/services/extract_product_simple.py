#!/usr/bin/env python3
"""
Script simple para extraer información de producto de MercadoLibre
Versión simplificada con mejor manejo de errores
"""

import re
import time
import json
import os
from playwright.sync_api import sync_playwright
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.database import Base
from src.models.product import Product


def load_env():
    """Carga variables de entorno desde .env"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("⚠️  python-dotenv no está instalado. Usando variables de entorno del sistema.")


def get_db_session():
    """Obtiene una sesión de base de datos"""
    # Leer DATABASE_URL desde .env
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        # Fallback a PostgreSQL local
        database_url = "postgresql://postgres:postgres@localhost:5432/comment_ml_scraper"
    
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def check_product_exists(product_id, session):
    """Verifica si un producto ya existe en la base de datos"""
    existing = session.query(Product).filter(Product.id == product_id).first()
    return existing is not None


def save_product_to_db(product_data, session):
    """Guarda el producto en la base de datos"""
    try:
        # Crear ml_additional_info
        ml_additional_info = {
            "url": product_data["url"],
            "ml_id": product_data["id"],
            "site": product_data["site_id"]
        }
        
        # Crear objeto Product
        product = Product(
            id=product_data["id"],
            title=product_data["title"],
            price=product_data["price"],
            site_id=product_data["site_id"],
            currency_id=product_data["currency_id"],
            sold_quantity=product_data["sold_quantity"],
            available_quantity=product_data["available_quantity"],
            marca=product_data["marca"],
            modelo=product_data["modelo"],
            caracteristicas=product_data["caracteristicas"],
            ml_additional_info=ml_additional_info
        )
        
        # Verificar si ya existe
        existing = session.query(Product).filter(Product.id == product_data["id"]).first()
        if existing:
            print(f"⚠️  Producto {product_data['id']} ya existe en la DB")
            return False
        
        # Guardar
        session.add(product)
        session.commit()
        print(f"✅ Producto {product_data['id']} guardado en la DB")
        return True
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error guardando en DB: {e}")
        return False


def extract_product_id_from_url(url):
    """Extrae el ID del producto desde una URL de MercadoLibre"""
    id_match = re.search(r'/p/([A-Z0-9]+)', url)
    return id_match.group(1) if id_match else None


def extract_product_info(url):
    """
    Extrae información del producto desde una URL de MercadoLibre
    """
    product_data = {
        "url": url,
        "id": "",
        "title": "",
        "price": 0.0,
        "marca": "",
        "modelo": "",
        "caracteristicas": {},
        "site_id": "MLA",
        "currency_id": "ARS",
        "sold_quantity": 0,
        "available_quantity": 0,
        "extracted_at": datetime.now().isoformat(),
        "success": False,
        "error": ""
    }
    
    try:
        with sync_playwright() as p:
            # Configurar browser con más opciones
            browser = p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            # Crear contexto con user agent
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = context.new_page()
            
            print(f"🔍 Accediendo a: {url}")
            
            # Navegar a la página
            response = page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            if response.status != 200:
                product_data["error"] = f"Error HTTP: {response.status}"
                print(f"❌ Error HTTP: {response.status}")
                return product_data
            
            # Esperar que cargue
            time.sleep(3)
            
            # Verificar si la página cargó correctamente
            page_title = page.title()
            print(f"📄 Título de página: '{page_title}'")
            
            if not page_title:
                product_data["error"] = "Página no cargó correctamente"
                print("❌ Página no cargó correctamente")
                return product_data
            
            # Extraer ID del producto desde la URL
            id_match = re.search(r'/p/([A-Z0-9]+)', url)
            if id_match:
                product_data["id"] = id_match.group(1)
                print(f"✅ ID: {product_data['id']}")
            
            # Extraer título - método más agresivo
            print("📝 Buscando título...")
            
            # Intentar diferentes métodos para obtener el título (más rápido)
            title_methods = [
                # Método 1: Buscar en meta tags (más rápido)
                lambda: page.evaluate('''
                    () => {
                        const meta = document.querySelector('meta[property="og:title"]');
                        return meta ? meta.getAttribute('content') : null;
                    }
                '''),
                
                # Método 2: Selectores específicos con timeout corto
                lambda: page.locator('h1[data-testid="product-title"]').first.wait_for(timeout=2000).text_content(),
                lambda: page.locator('h1.ui-pdp-title').first.wait_for(timeout=2000).text_content(),
                lambda: page.locator('.ui-pdp-title').first.wait_for(timeout=2000).text_content(),
                lambda: page.locator('[data-testid="product-title"]').first.wait_for(timeout=2000).text_content(),
                
                # Método 2: Buscar en todo el HTML
                lambda: page.evaluate('''
                    () => {
                        const selectors = [
                            'h1[data-testid="product-title"]',
                            'h1.ui-pdp-title',
                            '.ui-pdp-title',
                            '[data-testid="product-title"]',
                            'h1'
                        ];
                        for (let selector of selectors) {
                            const el = document.querySelector(selector);
                            if (el && el.textContent && el.textContent.trim().length > 10) {
                                return el.textContent.trim();
                            }
                        }
                        return null;
                    }
                '''),
                
                # Método 3: Buscar en meta tags
                lambda: page.evaluate('''
                    () => {
                        const meta = document.querySelector('meta[property="og:title"]');
                        return meta ? meta.getAttribute('content') : null;
                    }
                ''')
            ]
            
            for i, method in enumerate(title_methods, 1):
                try:
                    title = method()
                    if title and title.strip() and len(title.strip()) > 10:
                        product_data["title"] = title.strip()
                        print(f"✅ Título encontrado (método {i}): {title[:60]}...")
                        break
                    else:
                        print(f"  Método {i}: No encontró título válido")
                except Exception as e:
                    print(f"  Método {i}: Error - {e}")
            
            # Si no encontramos título, usar el título de la página
            if not product_data["title"] and page_title:
                product_data["title"] = page_title.strip()
                print(f"⚠️ Usando título de página: {page_title[:60]}...")
            
            # Extraer precio
            print("💰 Buscando precio...")
            
            price_methods = [
                lambda: page.evaluate('''
                    () => {
                        const selectors = [
                            '.ui-pdp-price .andes-money-amount__fraction',
                            '.ui-pdp-price .andes-money-amount',
                            '.ui-pdp-price',
                            '[data-testid="price"]',
                            '.price-tag-fraction',
                            '.andes-money-amount__fraction'
                        ];
                        for (let selector of selectors) {
                            const el = document.querySelector(selector);
                            if (el && el.textContent) {
                                const text = el.textContent.trim();
                                const numbers = text.replace(/[^\d]/g, '');
                                if (numbers && numbers.length > 2) {
                                    return parseInt(numbers);
                                }
                            }
                        }
                        return 0;
                    }
                ''')
            ]
            
            for i, method in enumerate(price_methods, 1):
                try:
                    price = method()
                    if price and price > 0:
                        product_data["price"] = price
                        print(f"✅ Precio encontrado: ${price:,.2f}")
                        break
                    else:
                        print(f"  Método {i}: No encontró precio válido")
                except Exception as e:
                    print(f"  Método {i}: Error - {e}")
            
            # Extraer marca y modelo del título
            if product_data["title"]:
                print("🏷️ Extrayendo marca y modelo...")
                
                # Lista de marcas conocidas
                marcas_conocidas = [
                    'Philco', 'Samsung', 'LG', 'Whirlpool', 'Electrolux', 'BGH', 'Sansei', 
                    'Sanyo', 'Carrier', 'York', 'TCL', 'Hisense', 'Daikin', 'Mitsubishi',
                    'Fujitsu', 'Panasonic', 'Hitachi', 'Toshiba', 'Sharp', 'Sony', 'Bosch',
                    'Mabe', 'Longvie', 'Kohinoor', 'Dream', 'Surrey', 'Siemens', 'GE',
                    'Frigidaire', 'Maytag', 'Amana', 'Kenmore', 'KitchenAid', 'Viking',
                    'Candy', 'Karcher', 'Rowenta', 'Braun', 'Oral-B', 'Philips'
                ]
                
                title_lower = product_data["title"].lower()
                
                # Buscar marca conocida
                for marca in marcas_conocidas:
                    if marca.lower() in title_lower:
                        product_data["marca"] = marca
                        print(f"✅ Marca: {marca}")
                        
                        # Extraer modelo después de la marca
                        marca_pos = title_lower.find(marca.lower())
                        if marca_pos != -1:
                            after_marca = product_data["title"][marca_pos + len(marca):].strip()
                            modelo_words = after_marca.split()[:4]
                            if modelo_words:
                                product_data["modelo"] = " ".join(modelo_words)
                                print(f"✅ Modelo: {product_data['modelo']}")
                        break
                
                # Si no se encontró marca conocida, usar primera palabra
                if not product_data["marca"]:
                    words = product_data["title"].split()
                    for word in words[:3]:
                        if len(word) >= 3 and word.isalpha() and word[0].isupper():
                            product_data["marca"] = word
                            print(f"⚠️ Marca fallback: {word}")
                            break
            
            product_data["success"] = True
            
    except Exception as e:
        product_data["error"] = str(e)
        print(f"❌ Error general: {e}")
    
    return product_data


def load_urls_from_file(filename="urls.txt"):
    """Carga URLs desde un archivo"""
    urls = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):  # Ignorar líneas vacías y comentarios
                    urls.append(line)
        print(f"📄 Cargadas {len(urls)} URLs desde {filename}")
    except FileNotFoundError:
        print(f"⚠️ Archivo {filename} no encontrado")
    except Exception as e:
        print(f"❌ Error leyendo {filename}: {e}")
    
    return urls


def process_single_url(url, skip_existing=True):
    """Procesa una sola URL"""
    print(f"\n🔍 PROCESANDO URL:")
    print("-" * 40)
    print(f"URL: {url}")
    
    # Extraer ID del producto desde la URL
    product_id = extract_product_id_from_url(url)
    if not product_id:
        print(f"❌ No se pudo extraer ID del producto de la URL")
        return {"success": False, "error": "ID no válido"}
    
    print(f"🆔 ID extraído: {product_id}")
    
    # Verificar si ya existe en la base de datos
    if skip_existing:
        session = get_db_session()
        try:
            if check_product_exists(product_id, session):
                print(f"⚠️  Producto {product_id} ya existe en la base de datos. Saltando...")
                return {"success": True, "skipped": True, "id": product_id}
        finally:
            session.close()
    
    # Extraer información del producto
    product_info = extract_product_info(url)
    
    print(f"\n📦 RESULTADO:")
    print(f"✅ Éxito: {product_info['success']}")
    print(f"🆔 ID: {product_info['id']}")
    print(f"📝 Título: {product_info['title'][:80]}...")
    print(f"💰 Precio: ${product_info['price']:,.2f}")
    print(f"🏷️ Marca: {product_info['marca']}")
    print(f"🔧 Modelo: {product_info['modelo']}")
    
    if product_info['error']:
        print(f"❌ Error: {product_info['error']}")
    else:
        # Guardar en base de datos
        if product_info['id']:
            session = get_db_session()
            try:
                save_product_to_db(product_info, session)
            finally:
                session.close()
    
    return product_info


def main():
    """Función principal"""
    import sys
    import argparse
    
    # Configurar parser de argumentos
    parser = argparse.ArgumentParser(description='Extractor Simple de Productos MercadoLibre')
    parser.add_argument('url', nargs='?', help='URL del producto a procesar')
    parser.add_argument('--force', '-f', action='store_true', 
                       help='Forzar reprocesamiento aunque el producto ya exista')
    parser.add_argument('--skip-existing', action='store_true', default=True,
                       help='Saltar productos que ya existen (por defecto)')
    
    args = parser.parse_args()
    
    # Cargar variables de entorno
    load_env()
    
    print("🚀 Extractor Simple de Productos MercadoLibre")
    print("=" * 60)
    
    # Verificar si se pasó una URL como parámetro
    if args.url:
        # Modo: URL como parámetro
        print(f"🔗 Modo: URL como parámetro")
        print(f"URL: {args.url}")
        
        skip_existing = not args.force and args.skip_existing
        product_info = process_single_url(args.url, skip_existing=skip_existing)
        
    else:
        # Modo: leer desde urls.txt
        print(f"📄 Modo: Leer desde urls.txt")
        
        urls = load_urls_from_file("urls.txt")
        
        if not urls:
            print("❌ No se encontraron URLs para procesar")
            print("\n💡 Uso:")
            print("  python -m src.services.extract_product_simple                    # Lee desde urls.txt")
            print("  python -m src.services.extract_product_simple <URL>              # Procesa una URL específica")
            print("  python -m src.services.extract_product_simple <URL> --force      # Forza reprocesamiento")
            return
        
        print(f"🔄 Procesando {len(urls)} URLs...")
        
        successful = 0
        failed = 0
        
        for i, url in enumerate(urls, 1):
            print(f"\n🔍 PRODUCTO {i}/{len(urls)}:")
            print("-" * 40)
            
            product_info = process_single_url(url, skip_existing=True)
            
            if product_info.get('skipped'):
                print(f"⏭️  Saltado (ya existe)")
                successful += 1  # Contamos como exitoso porque ya existe
            elif product_info['error']:
                print(f"❌ Error: {product_info['error']}")
                failed += 1
            elif product_info.get('success'):
                successful += 1
            else:
                failed += 1
            
            print()
        
        # Resumen final
        print("=" * 60)
        print(f"📊 RESUMEN FINAL:")
        print(f"✅ Exitosos: {successful}")
        print(f"❌ Fallidos: {failed}")
        print(f"📄 Total procesados: {len(urls)}")


if __name__ == "__main__":
    main()
