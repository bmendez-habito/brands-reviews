## Checkpoint - ML Reviews Analyzer

### Estado actual (Actualizado)
- **API REST moderna** (`src/web/app.py`) con endpoints completos:
  - Endpoints modernos: `/api/products`, `/api/reviews`, `/api/reviews/timeline`
  - Endpoints legacy: `/api/items/{id}`, `/api/search`, `/health`
  - CORS configurado para frontend React
  - Filtros avanzados por marca, fecha, rating, sentimiento
- **Frontend React** con TypeScript:
  - Análisis por marca con gráficos interactivos
  - Comparación lado a lado de marcas
  - Gráficos temporales (Recharts)
  - Análisis de sentimiento visual
  - Distribución de ratings con porcentajes correctos
- **Servicios de procesamiento**:
  - `scrape_final.py`: Scraper principal con API noindex (mejorado)
  - `extract_product_simple.py`: Extractor de productos con Playwright
  - `batch_process_products.py`: Procesamiento batch eficiente
  - `sentiment_analyzer.py`: Análisis de sentimiento en español mejorado
- **Base de datos PostgreSQL** con modelos extendidos:
  - Productos: marca, modelo, características (JSONB), ml_additional_info
  - Reviews: fecha original, sentimiento, raw_json, date_text
  - Relaciones optimizadas con índices
- **Análisis de sentimiento**:
  - Enfoque híbrido: TextBlob + diccionario español
  - Procesamiento batch con commits eficientes
  - Corrección de fechas (2025 → 2024)
  - Cálculos de porcentajes corregidos

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

### Comandos actualizados para uso diario

#### Frontend
```bash
cd frontend
npm run dev
# http://localhost:5173 - Análisis por marca
# http://localhost:5173/comparison - Comparación de marcas
```

#### Backend
```bash
# API REST
python main.py
# http://localhost:8000/api/products - Lista productos
# http://localhost:8000/api/reviews/timeline - Datos temporales
```

#### Procesamiento de datos
```bash
# Scraping completo (recomendado)
python -m src.services.scrape_final --urls-file urls.txt --count 1000

# Análisis de sentimiento
python -m src.services.sentiment_analyzer

# Procesamiento batch
python -m src.services.batch_process_products --action reviews --min-reviews 1000
```

### Próximos pasos sugeridos
- ✅ **Completado**: Sistema completo de análisis visual
- ✅ **Completado**: Análisis de sentimiento en español
- ✅ **Completado**: Gráficos temporales y comparativos
- 🔄 **En progreso**: Optimización de performance
- 📋 **Próximos**: Scheduler automático, exportación de datos, dashboard ejecutivo


