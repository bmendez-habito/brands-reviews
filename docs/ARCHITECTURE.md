# ML Reviews Analyzer – Arquitectura y Flujos

Este documento resume las piezas del sistema y cómo interactúan. Incluye diagramas Mermaid para visualizar los flujos clave.

## Componentes

- API Web (FastAPI)
  - Endpoints: `GET /api/items/{id}`, `GET /api/items/{id}/reviews`, `GET /api/search`
  - Lee desde la base; con `refresh=true` hace fallback a la API oficial de ML, persiste y responde.
- Cliente oficial de MercadoLibre
  - Archivo: `src/api/ml_client.py`
  - Usa `Authorization: Bearer` si `ML_ACCESS_TOKEN` está definido. Retries (429/5xx) + delay configurables.
- Job Batch (por item_id)
  - Archivo: `src/services/batch_fetch.py`
  - Poblado masivo por IDs vía API oficial; persiste en DB.
- Scraper principal por URL(s) (API noindex)
  - Archivo: `src/services/scrape_final.py` (CLI principal)
  - Extrae `item_id`, `site_id` y `title` desde la URL. Usa API noindex para obtener reviews; guarda producto + reviews en la misma DB.
- Extractor de productos (Playwright)
  - Archivo: `src/services/extract_product_simple.py` (CLI independiente)
  - Extrae información detallada de productos (marca, modelo, características) usando Playwright. Solo guarda productos en la DB.
- Analizador de sentimiento
  - Archivo: `src/services/sentiment_analyzer.py` (CLI independiente)
  - Completa los campos `sentiment_score` y `sentiment_label` para reviews usando TextBlob con mejoras para español.
- Base de Datos
  - Archivos: `src/models/product.py`, `src/models/review.py`, `src/models/database.py`
  - Modelos canónicos para todo el sistema.

---

## Flujo: API Web con Fallback a ML

```mermaid
flowchart TD
  A[Cliente REST] -->|GET /api/items/{id}/reviews| B[API Web]
  B --> C{En DB? \n o refresh=true}
  C -- No/Refresh --> D[Cliente ML API]
  D --> E[DB: Persistir Product/Reviews]
  E --> F[Responder API]
  C -- Sí --> F[Responder API]
```

Notas:
- Por defecto, la API responde desde la DB.
- Si `refresh=true`, consulta ML, guarda y responde.

---

## Flujo: Job Batch (IDs conocidos)

```mermaid
flowchart TD
  A[Operador] -->|python -m src.services.batch_fetch\n--items MLA123,MLA456 --count 200| B[Batch]
  B --> C[Loop items]
  C --> D[Loop paginado]
  D --> E[Cliente ML API]
  E --> F[DB: Persistir]
  F --> C
```

Notas:
- Usa siempre la API oficial (requiere token cuando sea online).
- `--count` es el total por item; `--page-size<=50`.

---

## Flujo: Scraper principal por URL(s) (API noindex)

```mermaid
flowchart TD
  A[Operador] -->|python -m src.services.scrape_final\n--url https://.../p/MLA25265609#reviews\n--urls-file urls.txt| B[CLI Scraper Final]
  B --> C[Extraer item_id, site_id, title hints]
  C --> D[API noindex paginado]
  D --> E[DB: Persistir Product + Reviews]
  E --> F{¿Más reviews?}
  F -->|Sí| D
  F -->|No| G[Completado]
```

Notas:
- Usa API noindex (más eficiente y confiable).
- No depende del servidor web.
- Usa el mismo modelo en DB que el resto del sistema.

---

## Flujo: Extractor de productos (Playwright)

```mermaid
flowchart TD
  A[Operador] -->|python -m src.services.extract_product_simple\n--urls-file urls.txt| B[Extractor de Productos]
  A -->|python -m src.services.extract_product_simple URL| B
  B --> C[Playwright: Navegar a URL]
  C --> D[Extraer: ID, título, precio, marca, modelo]
  D --> E[Extraer: características (especificaciones)]
  E --> F[Crear ml_additional_info JSONB]
  F --> G[DB: Guardar Product]
  G --> H{¿Más URLs?}
  H -->|Sí| C
  H -->|No| I[Completado]
```

Notas:
- Usa Playwright para extraer datos de la página web.
- Solo extrae información de productos, no reviews.
- Guarda directamente en la base de datos PostgreSQL.
- Maneja URLs con fragmentos automáticamente.

---

## Flujo: Analizador de sentimiento

```mermaid
flowchart TD
  A[Operador] -->|python -m src.services.sentiment_analyzer\n--from-date 2024-01-01| B[Analizador de Sentimiento]
  A -->|python -m src.services.sentiment_analyzer --dry-run| B
  B --> C[Obtener reviews sin análisis]
  C --> D[Filtrar por fecha opcional]
  D --> E[Procesar en batch]
  E --> F[Analizar con TextBlob + palabras clave español]
  F --> G[Actualizar sentiment_score y sentiment_label]
  G --> H{¿Más reviews?}
  H -->|Sí| E
  H -->|No| I[Mostrar estadísticas finales]
```

Notas:
- Procesa reviews que no tienen análisis de sentimiento completo.
- Combina TextBlob con diccionario de palabras en español para mejor precisión.
- Procesamiento en batch con commits periódicos para eficiencia.
- Modo dry-run para ver qué se procesaría sin hacer cambios.

---

## Modelo de Datos (ER)

```mermaid
erDiagram
  PRODUCT ||--o{ REVIEW : has
  PRODUCT {
    string id PK
    string title
    float price
    string site_id
    string currency_id
    int sold_quantity
    int available_quantity
    string marca
    string modelo
    jsonb caracteristicas
    jsonb ml_additional_info
  }
  REVIEW {
    string id PK
    string product_id FK
    int rate
    string title
    text content
    datetime date_created
    string reviewer_id
    int likes
    int dislikes
    float sentiment_score
    string sentiment_label
    string api_review_id
    string date_text
    string source
    jsonb media
    jsonb raw_json
  }
```

---

## Cuándo usar cada camino

- API Web: consumir datos cacheados; refrescar puntual con `refresh=true`.
- Batch (IDs): backfill/ingesta masiva cuando conocés los `item_id`.
- Scraper URL: cuando tenés URLs (y/o no tenés token) y querés poblar la DB con el mismo modelo. Usa API noindex.
- Extractor de productos: cuando necesitás información detallada de productos (marca, modelo, características) usando scraping web.
- Analizador de sentimiento: cuando tenés reviews sin análisis de sentimiento y querés completar los campos `sentiment_score` y `sentiment_label`.

---

## Comandos de referencia

- API local
  ```bash
  python main.py
  curl "http://127.0.0.1:8000/health"
  ```
- Batch por IDs
  ```bash
  python -m src.services.batch_fetch --items MLA123,MLA456 --count 200 --page-size 50
  ```
- Scraper principal por URL(s)
  ```bash
  python -m src.services.scrape_final --url "https://.../p/MLA25265609#reviews" --count 150
  python -m src.services.scrape_final --urls-file urls.txt --count 150
  ```
- Extractor de productos
  ```bash
  python -m src.services.extract_product_simple                       # Lee desde urls.txt
  python -m src.services.extract_product_simple "https://.../p/MLA25265609"  # URL específica
  ```
- Analizador de sentimiento
  ```bash
  python -m src.services.sentiment_analyzer                           # Todas las reviews sin análisis
  python -m src.services.sentiment_analyzer --from-date 2024-01-01   # Desde fecha específica
  python -m src.services.sentiment_analyzer --dry-run                 # Ver qué se procesaría
  ```

---

## Configuración rápida

- DB en Docker (Postgres)
  ```bash
  docker compose up -d db
  export DATABASE_URL=postgresql+psycopg2://mluser:mlpass@localhost:5432/mlreviews
  python -c "from src.models.database import init_db; init_db(); print('ok')"
  ```
- Online vs Offline
  - Offline (default): `ML_OFFLINE_MODE=True` o sin token → fixtures determinísticas.
  - Online: `ML_ACCESS_TOKEN=...` y `ML_OFFLINE_MODE=False` → API oficial con retries/backoff.
  - Scraper principal: usa API noindex por defecto (no requiere token).
