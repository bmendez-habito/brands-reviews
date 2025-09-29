#!/usr/bin/env python3
"""
Script para reprocesar productos que fallaron en la extracción.
"""

import asyncio
import sys
import os
from typing import List, Dict, Any
from playwright.async_api import async_playwright

# Agregar el directorio src al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.database import get_session, init_db
from models.product import Product


# URLs que fallaron según el log anterior
FAILED_URLS = [
    "https://www.mercadolibre.com.ar/p/MLA39141384",
    "https://www.mercadolibre.com.ar/p/MLA45599569", 
    "https://www.mercadolibre.com.ar/p/MLA45806125",
    "https://www.mercadolibre.com.ar/p/MLA47793225",
    "https://www.mercadolibre.com.ar/p/MLA49103126",
    "https://www.mercadolibre.com.ar/p/MLA50930351",
    "https://www.mercadolibre.com.ar/p/MLA51507289",
    "https://www.mercadolibre.com.ar/p/MLA52475765",
    "https://www.mercadolibre.com.ar/p/MLA53171467",
    "https://www.mercadolibre.com.ar/p/MLA54142126",
]


async def extract_product_fixed(page, url: str) -> Dict[str, Any]:
    """
    Extrae información de producto con el JavaScript corregido.
    """
    product_data = {
        "id": "",
        "title": "",
        "price": 0.0,
        "marca": "",
        "modelo": "",
        "success": False
    }
    
    try:
        print(f"🔍 Accediendo a: {url}")
        
        # Navegar con timeout corto
        await page.goto(url, wait_until="domcontentloaded", timeout=10000)
        
        # Extraer ID del producto desde la URL
        import re
        id_match = re.search(r'/p/([A-Z0-9]+)', url)
        if id_match:
            product_data["id"] = id_match.group(1)
            print(f"✅ ID: {product_data['id']}")
        
        # Extraer datos usando JavaScript corregido
        data = await page.evaluate('''
            () => {
                const result = {
                    title: "",
                    price: 0,
                    marca: "",
                    modelo: ""
                };
                
                // Buscar título en meta tags primero (más rápido)
                const metaTitle = document.querySelector('meta[property="og:title"]');
                if (metaTitle) {
                    result.title = metaTitle.getAttribute('content') || "";
                }
                
                // Si no hay meta title, buscar en el DOM
                if (!result.title) {
                    const titleSelectors = [
                        'h1[data-testid="product-title"]',
                        'h1.ui-pdp-title',
                        '.ui-pdp-title',
                        'h1'
                    ];
                    
                    for (let selector of titleSelectors) {
                        const el = document.querySelector(selector);
                        if (el && el.textContent && el.textContent.trim().length > 10) {
                            result.title = el.textContent.trim();
                            break;
                        }
                    }
                }
                
                // Buscar precio
                const priceSelectors = [
                    '.ui-pdp-price .andes-money-amount__fraction',
                    '.ui-pdp-price .andes-money-amount',
                    '.ui-pdp-price',
                    '[data-testid="price"]',
                    '.price-tag-fraction',
                    '.andes-money-amount__fraction'
                ];
                
                for (let selector of priceSelectors) {
                    const el = document.querySelector(selector);
                    if (el && el.textContent) {
                        const text = el.textContent.trim();
                        const numbers = text.replace(/[^\\d]/g, '');
                        if (numbers && numbers.length > 2) {
                            result.price = parseInt(numbers);
                            break;
                        }
                    }
                }
                
                // Extraer marca y modelo del título
                if (result.title) {
                    const title = result.title.toLowerCase();
                    
                    // Buscar marca conocida
                    const marcas = ['lg', 'samsung', 'bgh', 'philco', 'electra', 'midea', 'sansei', 'candy', 'comfee', 'siam', 'hyundai', 'hisense', 'surrey', 'daihatsu', 'conqueror', 'likon'];
                    for (let marca of marcas) {
                        if (title.includes(marca)) {
                            result.marca = marca.toUpperCase();
                            
                            // Extraer modelo (texto después de la marca) - CORREGIDO
                            const marcaIndex = title.indexOf(marca);
                            const afterMarca = title.substring(marcaIndex + marca.length).trim();
                            const words = afterMarca.split(' ').slice(0, 5); // Primeras 5 palabras
                            result.modelo = words.join(' ').trim(); // CORREGIDO: join(' ') en lugar de join()
                            break;
                        }
                    }
                    
                    // Si no se encontró marca conocida, usar fallback
                    if (!result.marca) {
                        const words = result.title.split(' ');
                        if (words.length > 0) {
                            result.marca = words[0].toUpperCase();
                        }
                    }
                }
                
                return result;
            }
        ''')
        
        # Actualizar datos del producto
        product_data.update(data)
        
        if product_data["title"]:
            print(f"✅ Título: {product_data['title'][:60]}...")
        if product_data["price"] > 0:
            print(f"✅ Precio: ${product_data['price']:,.2f}")
        if product_data["marca"]:
            print(f"✅ Marca: {product_data['marca']}")
        if product_data["modelo"]:
            print(f"✅ Modelo: {product_data['modelo']}")
        
        product_data["success"] = True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        product_data["error"] = str(e)
    
    return product_data


async def retry_failed_products():
    """
    Reprocesa los productos que fallaron.
    """
    print(f"🚀 Reprocesando {len(FAILED_URLS)} productos que fallaron...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # Crear context con configuración optimizada
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        
        successful = 0
        failed = 0
        
        for url in FAILED_URLS:
            page = await context.new_page()
            try:
                # Verificar si ya existe en la base de datos
                import re
                id_match = re.search(r'/p/([A-Z0-9]+)', url)
                if id_match:
                    product_id = id_match.group(1)
                    with get_session() as session:
                        existing = session.query(Product).filter(Product.id == product_id).first()
                        if existing:
                            print(f"⚠️ Producto {product_id} ya existe. Saltando...")
                            continue
                
                # Extraer datos del producto
                product_data = await extract_product_fixed(page, url)
                
                if product_data["success"] and product_data["id"]:
                    # Guardar en la base de datos
                    with get_session() as session:
                        product = Product(
                            id=product_data["id"],
                            title=product_data["title"],
                            price=float(product_data["price"]),
                            marca=product_data["marca"],
                            modelo=product_data["modelo"],
                            site_id="MLA",
                            currency_id="ARS"
                        )
                        session.add(product)
                        session.commit()
                        print(f"✅ Producto {product_data['id']} guardado en la DB")
                        successful += 1
                else:
                    print(f"❌ Falló: {product_data.get('error', 'Error desconocido')}")
                    failed += 1
                    
            except Exception as e:
                print(f"❌ Error procesando {url}: {e}")
                failed += 1
            finally:
                await page.close()
        
        await browser.close()
        
        print(f"\n📊 Estadísticas del retry:")
        print(f"   ✅ Exitosos: {successful}")
        print(f"   ❌ Fallidos: {failed}")
        print(f"   📄 Total: {len(FAILED_URLS)}")


if __name__ == "__main__":
    # Inicializar base de datos
    init_db()
    
    # Reprocesar productos fallidos
    asyncio.run(retry_failed_products())

