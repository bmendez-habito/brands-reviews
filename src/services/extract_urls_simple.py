#!/usr/bin/env python3
"""
Extractor simple de URLs de productos desde páginas de listado de MercadoLibre.
Usa requests + BeautifulSoup (más ligero que Playwright).

Uso:
    python src/services/extract_urls_simple.py "https://listado.mercadolibre.com.ar/aires-acondicionados"
"""

import argparse
import re
import sys
import time
from typing import List, Set
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


class SimpleURLExtractor:
    def __init__(self, max_pages: int = 5, delay: float = 2.0):
        self.max_pages = max_pages
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.extracted_urls: Set[str] = set()
    
    def extract_from_url(self, listado_url: str) -> List[str]:
        """
        Extrae URLs de productos desde una URL de listado de MercadoLibre.
        """
        print(f"🔍 Extrayendo URLs desde: {listado_url}")
        
        page_num = 1
        total_extracted = 0
        
        while page_num <= self.max_pages:
            print(f"📄 Procesando página {page_num}...")
            
            # Construir URL de la página
            if page_num == 1:
                current_url = listado_url
            else:
                # MercadoLibre usa _Desde para paginación
                offset = (page_num - 1) * 50  # 50 productos por página
                if '?' in listado_url:
                    current_url = f"{listado_url}&_Desde={offset}"
                else:
                    current_url = f"{listado_url}?_Desde={offset}"
            
            print(f"   🌐 URL: {current_url}")
            
            try:
                # Obtener la página
                response = self.session.get(current_url, timeout=30)
                response.raise_for_status()
                
                # Parsear HTML
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extraer URLs de productos
                page_urls = self._extract_product_urls_from_soup(soup, current_url)
                new_urls = 0
                
                for url in page_urls:
                    if url not in self.extracted_urls:
                        self.extracted_urls.add(url)
                        new_urls += 1
                
                total_extracted += new_urls
                print(f"   ✅ {new_urls} URLs nuevas encontradas (Total: {len(self.extracted_urls)})")
                
                if new_urls == 0:
                    print("   ⚠️ No se encontraron URLs nuevas. Fin de la extracción.")
                    break
                
                # Delay entre requests
                if page_num < self.max_pages:
                    print(f"   ⏳ Esperando {self.delay}s antes de la siguiente página...")
                    time.sleep(self.delay)
                
                page_num += 1
                
            except requests.RequestException as e:
                print(f"   ❌ Error obteniendo página {page_num}: {e}")
                break
            except Exception as e:
                print(f"   ❌ Error procesando página {page_num}: {e}")
                break
        
        print(f"\n🎉 Extracción completada!")
        print(f"   📊 Total de URLs únicas extraídas: {len(self.extracted_urls)}")
        print(f"   📄 Páginas procesadas: {page_num - 1}")
        
        return list(self.extracted_urls)
    
    def _extract_product_urls_from_soup(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Extrae URLs de productos desde el HTML parseado.
        """
        urls = set()
        
        # Buscar enlaces que contengan /p/ (productos)
        links = soup.find_all('a', href=True)
        print(f"   📊 Encontrados {len(links)} enlaces totales")
        
        for link in links:
            href = link.get('href')
            if href and ('/p/' in href or 'MLA' in href):
                # Limpiar y normalizar la URL
                clean_url = self._clean_product_url(href, base_url)
                if clean_url:
                    urls.add(clean_url)
        
        # Buscar también en atributos data o JavaScript
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                # Buscar URLs en JavaScript
                js_urls = re.findall(r'https?://[^\s"\']*mercadolibre\.com\.ar/p/[A-Z0-9]+', script.string)
                for js_url in js_urls:
                    clean_url = self._clean_product_url(js_url, base_url)
                    if clean_url:
                        urls.add(clean_url)
        
        print(f"   ✅ {len(urls)} URLs únicas encontradas en esta página")
        return list(urls)
    
    def _clean_product_url(self, url: str, base_url: str) -> str:
        """
        Limpia y normaliza una URL de producto.
        """
        if not url:
            return None
        
        # Convertir URL relativa a absoluta si es necesario
        if url.startswith('/'):
            url = urljoin(base_url, url)
        elif not url.startswith('http'):
            url = urljoin(base_url, url)
        
        # Remover fragmentos y parámetros innecesarios
        parsed = urlparse(url)
        
        # Verificar que sea una URL de MercadoLibre
        if 'mercadolibre.com.ar' not in parsed.netloc:
            return None
        
        # Verificar que tenga un ID de producto
        if '/p/' not in parsed.path:
            return None
        
        # Extraer el ID del producto
        product_id_match = re.search(r'/p/([A-Z0-9]+)', parsed.path)
        if not product_id_match:
            return None
        
        product_id = product_id_match.group(1)
        
        # Construir URL limpia
        clean_url = f"https://www.mercadolibre.com.ar/p/{product_id}"
        
        return clean_url


def main():
    parser = argparse.ArgumentParser(description='Extrae URLs de productos desde listados de MercadoLibre (versión simple)')
    parser.add_argument('url', nargs='?', help='URL del listado de MercadoLibre')
    parser.add_argument('--urls-file', help='Archivo con URLs de listados (una por línea)')
    parser.add_argument('--max-pages', type=int, default=5, help='Número máximo de páginas a procesar')
    parser.add_argument('--output', '-o', default='extracted_urls_simple.txt', help='Archivo de salida')
    parser.add_argument('--delay', type=float, default=2.0, help='Delay entre requests (segundos)')
    
    args = parser.parse_args()
    
    if not args.url and not args.urls_file:
        parser.print_help()
        return
    
    extractor = SimpleURLExtractor(max_pages=args.max_pages, delay=args.delay)
    
    if args.urls_file:
        # Procesar múltiples URLs desde archivo
        try:
            with open(args.urls_file, 'r', encoding='utf-8') as f:
                listado_urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        except FileNotFoundError:
            print(f"❌ Archivo no encontrado: {args.urls_file}")
            return
        
        all_urls = set()
        for i, listado_url in enumerate(listado_urls, 1):
            print(f"\n{'='*60}")
            print(f"📋 Procesando listado {i}/{len(listado_urls)}")
            print(f"{'='*60}")
            
            urls = extractor.extract_from_url(listado_url)
            all_urls.update(urls)
            
            # Pequeña pausa entre extracciones
            if i < len(listado_urls):
                time.sleep(2)
        
        urls = list(all_urls)
    else:
        # Procesar una sola URL
        urls = extractor.extract_from_url(args.url)
    
    # Guardar resultados
    if urls:
        with open(args.output, 'w', encoding='utf-8') as f:
            for url in sorted(urls):
                f.write(f"{url}\n")
        
        print(f"\n💾 {len(urls)} URLs guardadas en: {args.output}")
        
        # Mostrar algunas URLs de ejemplo
        print(f"\n📋 Ejemplos de URLs extraídas:")
        for i, url in enumerate(sorted(urls)[:5], 1):
            print(f"   {i}. {url}")
        
        if len(urls) > 5:
            print(f"   ... y {len(urls) - 5} más")
    else:
        print("❌ No se extrajeron URLs")


if __name__ == "__main__":
    main()
