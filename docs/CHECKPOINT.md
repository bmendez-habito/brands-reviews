## Checkpoint - ML Reviews Analyzer

### Estado actual
- API en FastAPI (`src/web/app.py`) con endpoints:
  - `GET /health`
  - `GET /api/search?q=...` (modo offline/online)
  - `GET /api/items/{id}` (sirve desde DB con fallback a ML y cachea)
  - `GET /api/items/{id}/reviews?limit=&offset=&refresh=` (lee DB y opcional refresca desde ML)
- Cliente MercadoLibre (`src/api/ml_client.py`) con:
  - Rate limiting simple, retries 429/5xx, `Authorization: Bearer` si hay `ML_ACCESS_TOKEN`
  - Modo offline cuando no hay token o `ML_OFFLINE_MODE=True`
- Modelos y DB:
  - `Product` y `Review` en `src/models/*` (actualizados con `product_id`, `marca`, `modelo`, `caracteristicas`)
  - `init_db()` en `src/models/database.py`
- Scraper principal (`src/services/scrape_final.py`) con API noindex
- Job batch manual (`src/services/batch_fetch.py`) para ingerir N reviews por item.
- Extractor de productos (`src/services/extract_product_simple.py`) con Playwright para información detallada de productos.
- Analizador de sentimiento (`src/services/sentiment_analyzer.py`) para completar análisis de sentimiento en reviews.
- Docker Compose solo para base de datos Postgres.

### Variables de entorno (.env)
- `ML_OFFLINE_MODE=True|False` (por defecto False para scraper)
- `ML_ACCESS_TOKEN=` (opcional; obliga modo online)
- `DATABASE_URL=`
  - SQLite (local): `sqlite:///data/reviews.db`
  - Postgres (Docker): `postgresql+psycopg2://mluser:mlpass@localhost:5432/mlreviews`

### Cómo correr local (venv)
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

### Base de datos en Docker (Postgres)
```bash
docker compose up -d db
# exportar o setear DATABASE_URL a Postgres
export DATABASE_URL=postgresql+psycopg2://mluser:mlpass@localhost:5432/mlreviews
source venv/bin/activate
pip install -r requirements.txt
python -c "from src.models.database import init_db; init_db(); print('ok')"
```

### Job batch (manual)
```bash
source venv/bin/activate
python -m src.services.batch_fetch --items MLA123,MLA456 --count 200 --page-size 50
```

### Scraper principal (API noindex)
```bash
source venv/bin/activate
python -m src.services.scrape_final --url "https://.../p/MLA25265603#reviews" --count 150
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

### Próximos pasos sugeridos
- Scheduler (cron/K8s) para ejecutar el batch periódico.
- Agregar autenticación y panel para administrar items a trackear.
- Enriquecimiento (sentimiento/keywords) y endpoints de analítica.


