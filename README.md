## ML Reviews Analyzer

### Descripción
Extractor y API para reviews de MercadoLibre con base de datos Postgres (Docker), scraper por API noindex y job batch.

### Estructura
- `src/api/`: cliente ML y rate limiter
- `src/models/`: modelos `Product` y `Review`, `database.py`
- `src/services/`: `scrape_final.py` (scraper principal), `review_scraper.py` (cache y fallback), `batch_fetch.py` (job), `sentiment_analyzer.py` (análisis de sentimiento), `extract_product_simple.py` (extractor de productos)
- `src/web/app.py`: FastAPI con endpoints
- `frontend/`: Aplicación React con TypeScript

### Requisitos
- Python 3.11+ (o Docker)
- Node.js 18+ (para frontend)
- Playwright (para extractor de productos): `pip install playwright && playwright install`

### Setup local (venv)
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -c "from src.models.database import init_db; init_db()"
python main.py
# Healthcheck
curl http://127.0.0.1:8000/health
```

### Variables de entorno
- `ML_OFFLINE_MODE` (True/False) — por defecto False
- `ML_ACCESS_TOKEN` — token OAuth para ML (opcional). Si no está, se usa endpoint noindex.
- `DATABASE_URL` — por defecto `sqlite:///data/reviews.db`. En Docker usamos Postgres: `postgresql+psycopg2://mluser:mlpass@db:5432/mlreviews`

### Endpoints principales
- `GET /health`
- `GET /api/search?q=...&limit=...` — usa cliente ML (offline/online)
- `GET /api/items/{id}` — trae/guarda producto
- `GET /api/items/{id}/reviews?limit=20&offset=0&refresh=true` — lee DB y opcionalmente refresca desde ML

### Job batch (manual)
```bash
source venv/bin/activate
python -m src.services.batch_fetch --items MLA123,MLA456 --count 200 --page-size 50
```

### Scraper principal (API noindex)
# Ya no requiere instalación de navegador - usa solo API noindex

Uso (una o varias URLs):
```bash
source venv/bin/activate
python -m src.services.scrape_final --url "https://.../p/MLA25265609#reviews" --url "https://.../p/MLA00000001#reviews" --count 150
# o usando archivo
python -m src.services.scrape_final --urls-file urls.txt --count 150
```

### Extractor de productos (Playwright)
```bash
source venv/bin/activate
python -m src.services.extract_product_simple                       # Lee desde urls.txt
python -m src.services.extract_product_simple "https://.../p/MLA25265609"  # URL específica
```

### Analizador de sentimiento
```bash
source venv/bin/activate
python -m src.services.sentiment_analyzer                           # Todas las reviews sin análisis
python -m src.services.sentiment_analyzer --from-date 2024-01-01   # Desde fecha específica
python -m src.services.sentiment_analyzer --dry-run                 # Ver qué se procesaría
```

### Frontend React
```bash
cd frontend
npm install
npm run dev
# Abrir http://localhost:5173
```

### Docker (Postgres + scraper job opcional)
```bash
cp .env.example .env
docker compose up -d db
# Configurar DATABASE_URL a Postgres en tu .env o export (host local)
export DATABASE_URL=postgresql+psycopg2://mluser:mlpass@localhost:5432/mlreviews
source venv/bin/activate
pip install -r requirements.txt
python -c "from src.models.database import init_db; init_db(); print('ok')"
python main.py
# Healthcheck
curl http://127.0.0.1:8000/health
```

Job scraper en contenedor (lee `urls.txt` y trae 300 reviews c/u):
```bash
docker compose run --rm scraper
```

Scraper local (sin contenedor), por API noindex integrado en `src/services/scrape_final.py`:
```bash
export DATABASE_URL=postgresql+psycopg2://mluser:mlpass@localhost:5432/mlreviews
source venv/bin/activate
python -m src.services.scrape_final --urls-file urls.txt --count 150
```

### Scraper final: parámetros y orígenes

El script `src/services/scrape_final.py` acepta parámetros por CLI y usa variables de entorno para la conexión y modo de operación.

- Parámetros CLI:
  - `--url`: puede repetirse para pasar varias URLs a la vez
  - `--urls-file`: archivo con una URL por línea (ej. `urls.txt`)
  - `--count`: cantidad objetivo de reviews por producto (paginado por API noindex)

- Derivación de datos desde la URL:
  - `item_id` y `site_id` se infieren del path (ej.: `/p/MLA25265603#reviews` → `item_id=MLA25265603`, `site_id=MLA`)
  - Se consulta el endpoint paginado noindex: `/noindex/catalog/reviews/{objectId}/search?offset=...&limit=...`

- Variables de entorno relevantes:
  - `DATABASE_URL`: conexión a la base (en docker-compose: `postgresql+psycopg2://mluser:mlpass@db:5432/mlreviews`, en host: `...@localhost:5432/...`)
  - `ML_OFFLINE_MODE`: por defecto `False`
  - `ML_ACCESS_TOKEN`: opcional; si se setea, el proyecto puede usar el cliente oficial; si no, usa noindex

- Ejemplos:
  ```bash
  # Por archivo
  export DATABASE_URL=postgresql+psycopg2://mluser:mlpass@localhost:5432/mlreviews
  source venv/bin/activate
  python -m src.services.scrape_final --urls-file urls.txt --count 150

  # URLs sueltas
  python -m src.services.scrape_final \
    --url "https://www.mercadolibre.com.ar/p/MLA25265603#reviews" \
    --url "https://www.mercadolibre.com.ar/p/OTRA#reviews" \
    --count 120
  ```

### Online vs Offline
- Default actual: `ML_OFFLINE_MODE=False`. Si hay `ML_ACCESS_TOKEN`, se usa cliente oficial; si no, se usa endpoint noindex paginado (`/noindex/catalog/reviews/.../search?offset=...&limit=...`).
- DB por defecto en desarrollo: Postgres con docker-compose.

### Próximos pasos sugeridos
- Autenticación para panel admin
- Scheduler (cron/K8s) para job batch
- Enriquecimiento de reviews (sentimiento, keywords)


