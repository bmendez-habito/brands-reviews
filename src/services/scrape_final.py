#!/usr/bin/env python3

import argparse
import re
from pathlib import Path
from typing import List, Set
from urllib.parse import urlparse
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

# MercadoLibrePlaywright eliminado - ya no se usa
from src.models.database import get_session, init_db
from src.models.product import Product
from src.models.review import Review
from datetime import datetime


def extract_product_code(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path or ""
    segments = [seg for seg in path.split("/") if seg]
    candidate = ""
    for seg in segments[::-1]:
        if re.match(r"^[A-Z]{2,4}\d+", seg):
            candidate = seg
            break
    if not candidate and segments:
        candidate = segments[-1]
    return candidate


def extract_hints(url: str, item_id: str) -> tuple:
    site_id = None
    m = re.match(r"^([A-Z]{3,4})\d+", item_id)
    if m:
        site_id = m.group(1)

    parsed = urlparse(url)
    segments = [seg for seg in (parsed.path or "").split("/") if seg]
    title_hint = None
    try:
        p_idx = segments.index("p")
        if p_idx > 0:
            candidate = segments[p_idx - 1]
            if candidate and not re.match(r"^[A-Z]{2,4}\d+", candidate):
                title_hint = candidate.replace("-", " ").strip().title()
    except ValueError:
        for seg in reversed(segments):
            if not re.match(r"^[A-Z]{2,4}\d+", seg):
                title_hint = seg.replace("-", " ").strip().title()
                break

    return site_id, title_hint


def _api_fetch_reviews_page(object_id: str, site_id: str, offset: int, limit: int = 15) -> dict:
    """Llama al endpoint público de reviews (noindex) y devuelve el JSON."""
    base_url = f"https://www.mercadolibre.com.ar/noindex/catalog/reviews/{object_id}/search"
    params = {
        "objectId": object_id,
        "siteId": site_id or "MLA",
        "isItem": "false",
        "offset": offset,
        "limit": limit,
    }
    url = base_url + "?" + urlencode(params)
    req = Request(url, headers={
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
        "Referer": f"https://www.mercadolibre.com.ar/p/{object_id}",
    })
    with urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def scrape_reviews_via_api(object_id: str, site_id: str, max_count: int) -> List[dict]:
    """Scrapea reviews vía API noindex. Devuelve lista en el mismo formato que guarda run_for_item."""
    all_reviews: List[dict] = []
    seen_ids: Set[str] = set()
    offset = 0
    page_size = 15
    try:
        while len(all_reviews) < max_count:
            data = _api_fetch_reviews_page(object_id, site_id or "MLA", offset, page_size)
            items = data.get("reviews") or data.get("results") or []
            if not items:
                break
            added = 0
            for r in items:
                try:
                    rid = str(r.get("id") or "")
                    if not rid:
                        continue
                    if rid in seen_ids:
                        continue
                    seen_ids.add(rid)
                    # rating
                    rate = int(r.get("rating") or 0)
                    # content
                    content = ""
                    if isinstance(r.get("comment"), dict):
                        c = r["comment"].get("content")
                        if isinstance(c, dict):
                            content = c.get("text") or ""
                        elif isinstance(c, str):
                            content = c
                    elif isinstance(r.get("content"), str):
                        content = r.get("content")
                    content = (content or "").strip()
                    # date text
                    date_text = ""
                    if isinstance(r.get("comment"), dict):
                        date_text = r["comment"].get("date") or (r["comment"].get("time") or {}).get("text", "")
                    date_text = r.get("date") or date_text or ""
                    title = content[:50] + "..." if len(content) > 50 else content
                    likes = 0
                    for act in r.get("actions") or []:
                        if act.get("id") == "LIKE":
                            try:
                                likes = int(act.get("value") or 0)
                            except Exception:
                                likes = 0
                            break
                    all_reviews.append({
                        "id": f"A{rid}",
                        "rate": rate,
                        "title": title,
                        "content": content,
                        "date_created": date_text,
                        "reviewer_id": f"user_{rid}",
                        "likes": likes,
                        "dislikes": 0,
                    })
                    added += 1
                    if len(all_reviews) >= max_count:
                        break
                except Exception:
                    continue
            if added == 0:
                break
            offset += page_size
    except Exception as e:
        print(f"⚠️ API reviews falló: {e}")
    print(f"API: recolectadas {len(all_reviews)} reviews")
    return all_reviews


def scrape_reviews_directly(item_id: str, count: int) -> List[dict]:
    """Scraper directo usando la lógica que sabemos que funciona"""
    from playwright.sync_api import sync_playwright
    import time
    
    url = f"https://www.mercadolibre.com.ar/p/{item_id}#reviews"
    reviews = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            print(f"Accediendo a: {url}")
            page.goto(url, wait_until="domcontentloaded")
            
            # Esperar que cargue completamente
            time.sleep(8)
            
            # Cerrar cualquier modal de Google Sign-in que pueda aparecer
            try:
                google_modal_close = page.locator('button[aria-label="Close"], .google-modal button, [data-testid="close-button"]').first
                if google_modal_close.is_visible():
                    print("Cerrando modal de Google Sign-in...")
                    google_modal_close.click()
                    time.sleep(2)
            except Exception as e:
                print(f"No se encontró modal de Google para cerrar: {e}")
            
            # Fallback inmediato: leer Opiniones destacadas sin abrir el modal
            # Objetivo: superar rápidamente el umbral de 6 comentarios si ya están en el DOM
            all_collected_comments = set()
            comments_data = []
            try:
                print("Buscando opiniones destacadas en la página (sin modal)...")
                summary_selector_list = [
                    '.ui-review-capability__summary [data-testid="comments-component"] article[data-testid="comment-component"]',
                    '.ui-review-capability__summary .ui-review-capability-comments article[data-testid="comment-component"]',
                    '.ui-review-capability__summary .ui-review-capability-comments article'
                ]
                found_any = False
                for sel in summary_selector_list:
                    items = page.locator(sel).all()
                    if len(items) > 0:
                        print(f"  ✅ Encontrados {len(items)} artículos con '{sel}'")
                        found_any = True
                        for art in items:
                            try:
                                text = art.text_content()
                                if text and len(text.strip()) > 50:
                                    comment_id = text[:100].strip()
                                    if comment_id in all_collected_comments:
                                        continue
                                    all_collected_comments.add(comment_id)
                                    # Parseo simple (mismos patrones que abajo)
                                    rating_match = re.search(r'Calificación (\d+) de 5', text)
                                    rate = int(rating_match.group(1)) if rating_match else 0
                                    date_match = re.search(r'(\d{1,2} \w+\. \d{4})', text)
                                    date_text = date_match.group(1) if date_match else ""
                                    content_parts = text.split(date_text)
                                    if len(content_parts) > 1:
                                        content = content_parts[1].strip()
                                        content = re.sub(r'Es útil\d+.*$', '', content).strip()
                                        content = re.sub(r'Más opciones$', '', content).strip()
                                    else:
                                        content = text.strip()
                                    comments_data.append({
                                        'text': text,
                                        'id': comment_id,
                                        'rate': rate,
                                        'date': date_text,
                                        'content': content,
                                        'extracted_immediately': True
                                    })
                            except Exception:
                                continue
                        break
                print(f"  📊 Opiniones destacadas recolectadas: {len(comments_data)}")
                # Si ya superamos 6 (más que lo actual), devolvemos directamente
                if len(comments_data) > 6:
                    print("✅ Suficientes comentarios desde el summary, sin abrir el modal")
                    for i, comment_data in enumerate(comments_data[:count]):
                        try:
                            rate = comment_data.get('rate', 0)
                            date_text = comment_data.get('date', '')
                            content = comment_data.get('content', '')
                            title = content[:50] + "..." if len(content) > 50 else content
                            review_data = {
                                "id": f"R{item_id}{i+1}",
                                "rate": rate,
                                "title": title,
                                "content": content,
                                "date_created": date_text,
                                "reviewer_id": f"user_{i+1}",
                                "likes": 0,
                                "dislikes": 0,
                            }
                            reviews.append(review_data)
                            print(f"  📄 Review {i+1}: {title[:60]}... (Rating: {rate})")
                        except Exception:
                            continue
                    return reviews
            except Exception as e:
                print(f"  ⚠️ No se pudieron leer opiniones destacadas: {e}")

            # Intentar hacer click en "Mostrar todas las opiniones" para abrir el modal
            try:
                print("Buscando botón 'Mostrar todas las opiniones'...")
                all_opinions_button = page.locator('button:has-text("Mostrar todas las opiniones")').first
                if all_opinions_button.is_visible():
                    print("Botón encontrado, scrolleando hacia él...")
                    # Scroll hacia el botón para asegurar que es clickeable
                    all_opinions_button.scroll_into_view_if_needed()
                    time.sleep(2)
                    
                    print("Haciendo click en 'Mostrar todas las opiniones' para abrir modal...")
                    # Múltiples estrategias de click
                    try:
                        all_opinions_button.click()
                    except:
                        # Si falla, intentar con fuerza
                        all_opinions_button.click(force=True)
                    
                    print("Esperando que se abra el modal...")
                    time.sleep(8)  # Más tiempo para que se abra el modal
                    
                    # Verificar si se abrió el modal
                    modal_check = page.locator('.andes-modal__content').first
                    if modal_check.is_visible():
                        print("✅ Modal abierto correctamente!")
                    else:
                        print("⚠️ Modal no detectado, pero continuando...")
                else:
                    print("Botón 'Mostrar todas las opiniones' no encontrado")
            except Exception as e:
                print(f"Error haciendo click en 'Mostrar todas las opiniones': {e}")
            
            # Buscar el modal de comentarios que se abrió
            print("Buscando modal de comentarios...")
            modal_container = None
            
            # Intentar diferentes selectores para el modal
            modal_selectors = [
                '.andes-modal__content',
                '.ui-review-capability-modal',
                '[data-testid="modal"]',
                '.modal-content',
                '.ui-review-capability-comments'
            ]
            
            for selector in modal_selectors:
                try:
                    modal = page.locator(selector).first
                    if modal.is_visible():
                        print(f"Modal encontrado con selector: {selector}")
                        modal_container = modal
                        break
                except:
                    continue
            
            if modal_container:
                print("Modal encontrado, haciendo scroll en el modal (como estaba funcionando)...")
                
                # Conjunto para almacenar comentarios únicos DURANTE el scroll
                all_collected_comments = set()
                comments_data = []
                api_comments_data = []  # Fallback vía API capturada
                try:
                    def _try_parse_api_review(obj):
                        try:
                            # Intentar mapear estructuras comunes
                            rate = int(obj.get('rating', obj.get('rate', 0)) or 0)
                            content = obj.get('content') or obj.get('comment') or obj.get('text') or ''
                            date_text = obj.get('date_created') or obj.get('date') or obj.get('created_at') or ''
                            if content and len(content.strip()) > 10:
                                return {
                                    'text': content,
                                    'id': (content[:80] + str(rate)).strip(),
                                    'rate': rate,
                                    'date': str(date_text),
                                    'content': content.strip(),
                                    'extracted_immediately': True
                                }
                        except Exception:
                            return None
                        return None

                    def _on_response(response):
                        try:
                            url_l = response.url.lower()
                            if ('review' in url_l or 'opinion' in url_l) and 'image' not in url_l:
                                ctype = response.headers.get('content-type', '')
                                if 'application/json' in ctype:
                                    data = response.json()
                                    candidates = []
                                    if isinstance(data, dict):
                                        for key in ['reviews', 'results', 'list', 'data', 'items']:
                                            if isinstance(data.get(key), list):
                                                candidates = data.get(key)
                                                break
                                        # Algunas APIs anidan en data.results
                                        if not candidates and isinstance(data.get('data'), dict) and isinstance(data['data'].get('results'), list):
                                            candidates = data['data']['results']
                                    if isinstance(data, list):
                                        candidates = data
                                    added_now = 0
                                    for obj in candidates or []:
                                        parsed = _try_parse_api_review(obj)
                                        if parsed:
                                            key = parsed['id']
                                            if key not in all_collected_comments:
                                                all_collected_comments.add(key)
                                                api_comments_data.append(parsed)
                                                added_now += 1
                                    if added_now:
                                        print(f"  🌐 API: capturadas {added_now} nuevas reviews (total API {len(api_comments_data)})")
                        except Exception:
                            pass

                    page.on('response', _on_response)
                except Exception:
                    pass

                # Inicializar colector persistente en el contexto de la página (evita pérdida por virtualización)
                try:
                    page.evaluate("""
                        (() => {
                          if (!window.__mlReviewsSet) { window.__mlReviewsSet = new Set(); }
                          if (!window.__mlReviews) { window.__mlReviews = []; }
                        })();
                    """)
                except Exception:
                    pass
                
                # EL SCROLL ORIGINAL QUE FUNCIONABA - reforzado sobre contenedor de comentarios
                for i in range(12):  # subir intentos para asegurar carga incremental
                    print(f"Scroll en modal {i+1}/3...")
                    
                    # DEBUG: Pausa manual para inspeccionar
                    if i == 0:  # Solo en el primer scroll
                        print("🔍 PAUSA DEBUG: Presiona Enter para continuar...")
  
                    
                    # RECOLECTAR COMENTARIOS que están visibles AHORA (NUEVO)
                    try:
                        # ESPERAR y REFRESCAR para que se rendericen nuevos elementos
                        page.wait_for_timeout(1000)  # Pausa para renderizado
                        
                        # INVESTIGAR el contenedor principal MÁS A FONDO
                        print(f"  🔍 DEBUG PROFUNDO:")
                        
                        # ¿Cuántos contenedores hay?
                        all_containers = page.locator('.ui-review-capability-comments').all()
                        print(f"      - Total contenedores .ui-review-capability-comments: {len(all_containers)}")
                        
                        # Investigar cada contenedor
                        for idx, container in enumerate(all_containers):
                            if container.is_visible():
                                print(f"      - Contenedor {idx+1} (visible):")
                                all_divs = container.locator('> div').all()
                                all_articles = container.locator('article').all()
                                all_children = container.locator('> *').all()
                                
                                print(f"          * Divs directos: {len(all_divs)}")
                                print(f"          * Articles: {len(all_articles)}")
                                print(f"          * Todos los hijos: {len(all_children)}")
                                
                                # Obtener el HTML para verificar
                                try:
                                    html_content = container.inner_html()
                                    div_count_in_html = html_content.count('<div')
                                    article_count_in_html = html_content.count('<article')
                                    print(f"          * En HTML: {div_count_in_html} <div>, {article_count_in_html} <article>")
                                except:
                                    print(f"          * No se pudo obtener HTML")
                            else:
                                print(f"      - Contenedor {idx+1} (NO visible)")
                        
                        # Usar el primer contenedor visible
                        container = page.locator('.ui-review-capability-comments').first
                        if container.is_visible():
                            all_divs = container.locator('> div').all()
                            all_articles = container.locator('article').all()
                            all_children = container.locator('> *').all()
                        else:
                            print(f"      ❌ NINGÚN contenedor visible!")
                            all_divs = []
                            all_articles = []
                            all_children = []
                        
                        # Probar múltiples selectores DENTRO del contenedor
                        current_comments = page.locator('.ui-review-capability-comments__comment').all()
                        alt_comments1 = page.locator('article[data-testid="comment-component"]').all()
                        alt_comments2 = page.locator('article[aria-roledescription="Review"]').all()
                        
                        # NUEVO: Probar selectores más amplios DENTRO del contenedor
                        container_articles = page.locator('.ui-review-capability-comments article').all()
                        container_divs = page.locator('.ui-review-capability-comments > div').all()
                        
                        print(f"  🔍 Selectores específicos:")
                        print(f"      - .ui-review-capability-comments__comment: {len(current_comments)}")
                        print(f"      - article[data-testid='comment-component']: {len(alt_comments1)}")
                        print(f"      - article[aria-roledescription='Review']: {len(alt_comments2)}")
                        print(f"  🔍 Selectores amplios:")
                        print(f"      - .ui-review-capability-comments article: {len(container_articles)}")
                        print(f"      - .ui-review-capability-comments > div: {len(container_divs)}")
                        
                        # Usar el selector que encuentre MÁS elementos
                        all_selectors = [
                            (current_comments, "principal (.ui-review-capability-comments__comment)"),
                            (alt_comments1, "data-testid"), 
                            (alt_comments2, "aria-role"),
                            (container_articles, "container articles"),
                            (container_divs, "container divs")
                        ]
                        
                        best_comments, best_name = max(all_selectors, key=lambda x: len(x[0]))
                        current_comments = best_comments
                        
                        if len(current_comments) > 5:
                            print(f"  ✅ Usando selector '{best_name}' con {len(current_comments)} elementos!")
                        else:
                            print(f"  ⚠️ Usando selector '{best_name}' pero solo {len(current_comments)} elementos")
                        
                        for j, comment in enumerate(current_comments):
                            try:
                                # EXTRAER INMEDIATAMENTE todo el contenido antes de que se reemplace
                                text = comment.text_content()
                                if text and len(text.strip()) > 50:
                                    comment_id = text[:100].strip()
                                    if comment_id not in all_collected_comments:
                                        all_collected_comments.add(comment_id)
                                        
                                        # EXTRAER INMEDIATAMENTE todos los datos del comentario
                                        # No guardar el elemento DOM, guardar todos los datos
                                        try:
                                            # Extraer rating
                                            rating_match = re.search(r'Calificación (\d+) de 5', text)
                                            rate = int(rating_match.group(1)) if rating_match else 0
                                            
                                            # Extraer fecha
                                            date_match = re.search(r'(\d{1,2} \w+\. \d{4})', text)
                                            date_text = date_match.group(1) if date_match else ""
                                            
                                            # Extraer contenido del comentario
                                            content_parts = text.split(date_text)
                                            if len(content_parts) > 1:
                                                content = content_parts[1].strip()
                                                # Limpiar texto
                                                content = re.sub(r'Es útil\d+.*$', '', content).strip()
                                                content = re.sub(r'Más opciones$', '', content).strip()
                                            else:
                                                content = text.strip()
                                            
                                            comments_data.append({
                                                'text': text,
                                                'id': comment_id,
                                                'rate': rate,
                                                'date': date_text,
                                                'content': content,
                                                'extracted_immediately': True  # Marcador de que fue extraído inmediatamente
                                            })
                                            print(f"  💬 NUEVO #{len(comments_data)}: Rating {rate} - {content[:30]}...")
                                        except Exception as parse_error:
                                            # Si falla el parsing, guardar el texto crudo
                                            comments_data.append({
                                                'text': text,
                                                'id': comment_id,
                                                'rate': 0,
                                                'date': '',
                                                'content': text.strip(),
                                                'extracted_immediately': True
                                            })
                                            print(f"  💬 NUEVO #{len(comments_data)} (parsing falló): {comment_id[:30]}...")
                                    else:
                                        print(f"  🔄 Comentario {j+1} ya visto: {comment_id[:30]}...")
                                else:
                                    print(f"  ⚠️ Comentario {j+1} muy corto o vacío")
                            except Exception as e:
                                print(f"  ❌ Error procesando comentario {j+1}: {e}")
                    except Exception as e:
                        print(f"  ❌ Error buscando comentarios: {e}")
                    
                    # EL SCROLL ORIGINAL QUE FUNCIONABA
                    try:
                        modal_container.evaluate("element => element.scrollTop += 1000")
                    except Exception:
                        pass
                    page.wait_for_timeout(500)
                    
                    # Intentar scroll específico en el contenedor de comentarios
                    try:
                        comments_container_strict = modal_container.locator('.ui-review-capability-comments').first
                        if comments_container_strict.is_visible():
                            # foco y scroll del contenedor real
                            try:
                                comments_container_strict.focus()
                            except Exception:
                                pass
                            comments_container_strict.evaluate("el => el.scrollTop += 1200")
                            page.wait_for_timeout(400)
                            try:
                                comments_container_strict.hover()
                                page.mouse.wheel(0, 1200)
                            except Exception:
                                pass
                            # key End para forzar virtualización
                            try:
                                page.keyboard.press('End')
                            except Exception:
                                pass
                    except Exception:
                        pass
                    
                    # Buscar botones de "Cargar más" que puedan aparecer (ORIGINAL)
                    try:
                        load_more_buttons = modal_container.locator('button:has-text("Cargar más"), button:has-text("Ver más"), button:has-text("Mostrar más")').all()
                        for button in load_more_buttons:
                            if button.is_visible():
                                print(f"  Haciendo click en botón de cargar más...")
                                button.click()
                                time.sleep(2)
                                break
                    except Exception as e:
                        pass
                    
                    # Buscar botones de "Cargar más" dentro del modal con más selectores (ORIGINAL)
                    try:
                        button_texts = [
                            "Cargar más", "Ver más", "Mostrar más", "Cargar más comentarios", 
                            "Ver más comentarios", "Mostrar más comentarios", "Cargar más opiniones",
                            "Ver más opiniones", "Mostrar más opiniones", "Ver todas las opiniones"
                        ]
                        
                        for text in button_texts:
                            buttons = modal_container.locator(f'button:has-text("{text}")').all()
                            for button in buttons:
                                if button.is_visible():
                                    print(f"Haciendo click en botón '{text}' dentro del modal...")
                                    button.click()
                                    time.sleep(3)
                                    break
                            else:
                                continue
                            break
                    except Exception as e:
                        pass
                    
                    # También buscar botones por atributos data-testid (ORIGINAL)
                    try:
                        testid_buttons = modal_container.locator('[data-testid*="load"], [data-testid*="more"], [data-testid*="button"]').all()
                        for button in testid_buttons:
                            if button.is_visible() and button.text_content():
                                text = button.text_content().strip()
                                if any(keyword in text.lower() for keyword in ['cargar', 'ver', 'mostrar', 'más']):
                                    print(f"Haciendo click en botón por testid: {text}")
                                    button.click()
                                    time.sleep(3)
                                    break
                    except Exception as e:
                        pass
                
                    # Snapshot persistente de artículos visibles (acumula en window.__mlReviews)
                    try:
                        added_now = page.evaluate("""
                          () => {
                            const modal = document.querySelector('.andes-modal__content');
                            if (!modal) return 0;
                            const container = modal.querySelector('.ui-review-capability-comments') || modal;
                            const articles = container.querySelectorAll('article[data-testid="comment-component"], article[aria-roledescription="Review"]');
                            if (!window.__mlReviewsSet) window.__mlReviewsSet = new Set();
                            if (!window.__mlReviews) window.__mlReviews = [];
                            let added = 0;
                            for (const a of articles) {
                              const text = (a.textContent || '').trim();
                              if (text.length < 50) continue;
                              const id = text.slice(0, 120).trim();
                              if (window.__mlReviewsSet.has(id)) continue;
                              // Parse rating y fecha simples
                              let rate = 0; const m = text.match(/Calificación\s+(\d+)\s+de\s+5/i); if (m) rate = parseInt(m[1], 10) || 0;
                              let date = ''; const d = text.match(/\b\d{1,2}\s+\w+\.?\s+\d{4}\b/); if (d) date = d[0];
                              let content = text;
                              if (date) { const parts = text.split(date); content = parts.slice(1).join(' ').trim(); }
                              // Limpiar UI común
                              content = content.replace(/Es útil\s*\d+.*/i, '').replace(/Más opciones.*/i, '').trim();
                              window.__mlReviewsSet.add(id);
                              window.__mlReviews.push({ id, rate, date, content, extracted_immediately: true });
                              added++;
                            }
                            return added;
                          }
                        """)
                        if added_now:
                            print(f"  🧩 Snapshot sumó {added_now} nuevos (persistentes)")
                    except Exception:
                        pass

                    # Intentar paginación dentro del modal (Siguiente)
                    try:
                        next_selectors = [
                            '.andes-pagination [aria-label="Siguiente"]:not([disabled])',
                            'button[aria-label="Siguiente"]:not([disabled])',
                            'a[aria-label="Siguiente"]',
                            '.ui-pagination__link:has-text("Siguiente")',
                            '.andes-button:has-text("Siguiente")'
                        ]
                        clicked = False
                        for sel in next_selectors:
                            btn = modal_container.locator(sel).first
                            if btn.count() > 0 and btn.is_visible():
                                print(f"  ➡️ Paginando con: {sel}")
                                try:
                                    btn.click()
                                except Exception:
                                    btn.click(force=True)
                                page.wait_for_timeout(1500)
                                clicked = True
                                break
                        if not clicked:
                            # si no hay siguiente y ya agregamos algunos, podemos terminar antes
                            pass
                    except Exception:
                        pass

                print(f"\n🎯 SCROLL COMPLETADO: {len(comments_data)} comentarios únicos recolectados")
                if api_comments_data:
                    print(f"  🌐 Además, vía API capturadas {len(api_comments_data)} reviews")
                    # Mezclar API con DOM manteniendo unicidad
                    for r in api_comments_data:
                        key = r['id']
                        if key not in all_collected_comments:
                            all_collected_comments.add(key)
                            comments_data.append(r)

                # Mezclar los del snapshot persistente
                try:
                    persisted = page.evaluate("() => (window.__mlReviews || [])")
                    if persisted:
                        added_from_persist = 0
                        for r in persisted:
                            key = r.get('id') if isinstance(r, dict) else None
                            if not key:
                                continue
                            if key not in all_collected_comments:
                                all_collected_comments.add(key)
                                # asegurar campos esperados
                                comments_data.append({
                                    'text': r.get('content', ''),
                                    'id': key,
                                    'rate': r.get('rate', 0),
                                    'date': r.get('date', ''),
                                    'content': r.get('content', ''),
                                    'extracted_immediately': True
                                })
                                added_from_persist += 1
                        if added_from_persist:
                            print(f"  📌 Persistente sumó {added_from_persist} nuevos (total {len(comments_data)})")
                except Exception:
                    pass
                
                # Usar los comentarios recolectados durante el scroll
                # Ya tenemos los datos extraídos, no necesitamos elementos DOM
                cards = comments_data  # Son dictionaries con todos los datos ya extraídos
            else:
                print("Modal no encontrado, intentando scroll en contenedor principal...")
                
                # Fallback: buscar el contenedor de comentarios en la página principal
                comments_container = page.locator('.ui-review-capability-comments').first
                
                if comments_container.is_visible():
                    print("Contenedor de comentarios encontrado en página principal...")
                    for i in range(10):
                        comments_container.evaluate("element => element.scrollTop = element.scrollHeight")
                        time.sleep(2)
                else:
                    print("No se encontró contenedor de comentarios, usando scroll general...")
                    for i in range(8):
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        time.sleep(2)
            
            # Ya recolectamos durante el scroll, solo mostrar resumen
            print(f"\n📊 Total de comentarios recolectados durante el scroll: {len(cards)}")
            
            # Mostrar muestra de los primeros comentarios
            if len(cards) > 0:
                print("\n📝 Muestra de comentarios recolectados:")
                for i, comment_data in enumerate(cards[:5]):
                    try:
                        if isinstance(comment_data, dict):
                            # Los datos ya están extraídos
                            content = comment_data.get('content', 'Sin contenido')
                            rate = comment_data.get('rate', 0)
                            print(f"  {i+1}. Rating {rate}: {content[:100]}...")
                        else:
                            # Fallback por si acaso
                            text = comment_data.text_content()
                            print(f"  {i+1}. {text[:100]}...")
                    except Exception as e:
                        print(f"  {i+1}. Error obteniendo texto: {e}")
            
            for i, comment_data in enumerate(cards[:count]):
                try:
                    if isinstance(comment_data, dict) and comment_data.get('extracted_immediately'):
                        # Usar los datos ya extraídos durante el scroll
                        rate = comment_data.get('rate', 0)
                        date_text = comment_data.get('date', '')
                        content = comment_data.get('content', '')
                        title = content[:50] + "..." if len(content) > 50 else content
                    else:
                        # Fallback: extraer de elemento DOM (no debería pasar)
                        text = comment_data.text_content() if hasattr(comment_data, 'text_content') else str(comment_data)
                        
                        # Parsear rating
                        rating_match = re.search(r'Calificación (\d+) de 5', text)
                        rate = int(rating_match.group(1)) if rating_match else 0
                        
                        # Parsear fecha
                        date_match = re.search(r'(\d{1,2} \w+\. \d{4})', text)
                        date_text = date_match.group(1) if date_match else ""
                        
                        # Extraer contenido
                        content_parts = text.split(date_text)
                        content = content_parts[1].strip() if len(content_parts) > 1 else text
                        content = re.sub(r'^Calificación \d+ de 5\s*', '', content)
                        content = re.sub(r'^\d{1,2} \w+\. \d{4}\s*', '', content)
                        content = content.strip()
                        
                        # Crear título basado en el contenido
                        title = content[:50] + "..." if len(content) > 50 else content
                    
                    review_data = {
                        "id": f"R{item_id}{i+1}",
                        "rate": rate,
                        "title": title,
                        "content": content,
                        "date_created": date_text,
                        "reviewer_id": f"user_{i+1}",
                        "likes": 0,
                        "dislikes": 0,
                    }
                    
                    reviews.append(review_data)
                    print(f"  📄 Review {i+1}: {title[:60]}... (Rating: {rate})")
                    
                except Exception as e:
                    print(f"Error procesando review {i+1}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error general: {e}")
        finally:
            browser.close()
    
    return reviews


def run_for_item(item_id: str, count: int, site_id_hint, title_hint) -> None:
    with get_session() as db:
        # Get or create product
        prod = db.get(Product, item_id)
        if prod is None:
            print(f"Creando producto {item_id}...")
            prod = Product(
                id=item_id,
                title=title_hint or f"Item {item_id}",
                price=0.0,
                site_id=site_id_hint or "MLA",
                currency_id="ARS",
                sold_quantity=0,
                available_quantity=0,
            )
            db.add(prod)
            db.flush()
            print(f"✅ Producto creado: {prod.title}")
        
        # Scrape via API primero (más robusto y masivo)
        print(f"Obteniendo reviews via API para {item_id}...")
        api_reviews = scrape_reviews_via_api(item_id, site_id_hint or "MLA", count)
        reviews_data = api_reviews
        # Si la API devolvió menos de las pedidas, intentar complementar con DOM
        if len(reviews_data) < count:
            print(f"API devolvió {len(reviews_data)} < {count}. Complementando con DOM...")
            try:
                dom_reviews = scrape_reviews_directly(item_id, count - len(reviews_data))
                reviews_data.extend(dom_reviews)
            except Exception as e:
                print(f"DOM complementario falló: {e}")
        
        stored_count = 0
        for review_data in reviews_data:
            existing = db.get(Review, review_data["id"])
            if existing:
                continue
                
            # Parsear fecha original de la API
            original_date = None
            if "date_created" in review_data and review_data["date_created"]:
                try:
                    # La API devuelve formato ISO: "2024-01-01T00:00:00Z"
                    original_date = datetime.fromisoformat(review_data["date_created"].replace('Z', '+00:00'))
                except Exception:
                    original_date = datetime.utcnow()
            else:
                original_date = datetime.utcnow()
            
            review = Review(
                id=review_data["id"],
                product_id=item_id,
                rate=review_data["rate"],
                title=review_data["title"],
                content=review_data["content"],
                date_created=original_date,
                reviewer_id=review_data["reviewer_id"],
                likes=review_data["likes"],
                dislikes=review_data["dislikes"],
                sentiment_score=0.0,
                sentiment_label="neutral",
                date_text=review_data.get("date_created", ""),  # Guardar fecha original como texto
                raw_json=review_data,  # Guardar datos originales completos
            )
            db.add(review)
            stored_count += 1
        
        print(f"✅ Guardadas {stored_count} reviews nuevas")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape reviews from MercadoLibre URLs")
    parser.add_argument("--url", action="append", default=[], help="MercadoLibre product URL")
    parser.add_argument("--urls-file", type=str, help="Path to file with URLs")
    parser.add_argument("--count", type=int, default=10, help="Number of reviews to fetch")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    init_db()
    
    urls: List[str] = []
    if args.url:
        urls.extend(args.url)
    if args.urls_file:
        p = Path(args.urls_file)
        if p.exists():
            with p.open("r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        urls.append(line)
    
    if not urls:
        raise SystemExit("Provide at least one --url or --urls-file")
    
    seen: Set[str] = set()
    for url in urls:
        if url in seen:
            continue
        seen.add(url)
        
        item_id = extract_product_code(url)
        site_id_hint, title_hint = extract_hints(url, item_id)
        
        print(f"\n🚀 Procesando: {url}")
        print(f"📋 Item ID: {item_id}")
        
        run_for_item(item_id, args.count, site_id_hint, title_hint)
        print(f"✅ Completado: {item_id}")


if __name__ == "__main__":
    main()
