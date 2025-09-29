#!/usr/bin/env python3
"""
Script para combinar URLs de diferentes fuentes y eliminar duplicados.

Uso:
    python src/services/merge_urls.py --input extracted_airs_full.txt --existing urls.txt --output urls_merged.txt
"""

import argparse
import re
from typing import Set


def extract_product_id(url: str) -> str:
    """
    Extrae el ID del producto de una URL de MercadoLibre.
    """
    match = re.search(r'/p/([A-Z0-9]+)', url)
    return match.group(1) if match else None


def load_urls_from_file(filename: str) -> Set[str]:
    """
    Carga URLs desde un archivo y las normaliza.
    """
    urls = set()
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                url = line.strip()
                if url and not url.startswith('#'):
                    # Normalizar URL
                    if url.startswith('/'):
                        url = f"https://www.mercadolibre.com.ar{url}"
                    elif not url.startswith('http'):
                        url = f"https://www.mercadolibre.com.ar/p/{url}"
                    
                    # Limpiar fragmentos
                    url = url.split('#')[0]
                    
                    urls.add(url)
    except FileNotFoundError:
        print(f"⚠️ Archivo no encontrado: {filename}")
    
    return urls


def main():
    parser = argparse.ArgumentParser(description='Combina URLs de diferentes fuentes y elimina duplicados')
    parser.add_argument('--input', '-i', required=True, help='Archivo con URLs nuevas')
    parser.add_argument('--existing', '-e', help='Archivo con URLs existentes')
    parser.add_argument('--output', '-o', default='urls_merged.txt', help='Archivo de salida')
    parser.add_argument('--show-stats', action='store_true', help='Mostrar estadísticas detalladas')
    
    args = parser.parse_args()
    
    # Cargar URLs
    print("📂 Cargando URLs...")
    new_urls = load_urls_from_file(args.input)
    print(f"   ✅ {len(new_urls)} URLs cargadas desde {args.input}")
    
    existing_urls = set()
    if args.existing:
        existing_urls = load_urls_from_file(args.existing)
        print(f"   ✅ {len(existing_urls)} URLs cargadas desde {args.existing}")
    
    # Combinar y eliminar duplicados
    all_urls = new_urls.union(existing_urls)
    
    # Eliminar duplicados por ID de producto
    unique_urls = set()
    seen_ids = set()
    
    for url in all_urls:
        product_id = extract_product_id(url)
        if product_id and product_id not in seen_ids:
            unique_urls.add(url)
            seen_ids.add(product_id)
    
    # Guardar resultado
    with open(args.output, 'w', encoding='utf-8') as f:
        for url in sorted(unique_urls):
            f.write(f"{url}\n")
    
    # Estadísticas
    print(f"\n📊 Estadísticas:")
    print(f"   📄 URLs nuevas: {len(new_urls)}")
    print(f"   📄 URLs existentes: {len(existing_urls)}")
    print(f"   📄 Total combinadas: {len(all_urls)}")
    print(f"   📄 URLs únicas (por ID): {len(unique_urls)}")
    print(f"   📄 Duplicados eliminados: {len(all_urls) - len(unique_urls)}")
    print(f"   💾 Guardadas en: {args.output}")
    
    # Mostrar ejemplos
    if unique_urls:
        print(f"\n📋 Ejemplos de URLs combinadas:")
        for i, url in enumerate(sorted(unique_urls)[:5], 1):
            print(f"   {i}. {url}")
        
        if len(unique_urls) > 5:
            print(f"   ... y {len(unique_urls) - 5} más")


if __name__ == "__main__":
    main()

