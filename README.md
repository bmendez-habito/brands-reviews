## ML Reviews Analyzer

### Descripción
Sistema completo de análisis de reviews de MercadoLibre con:
- **Backend**: API REST (FastAPI) con base de datos PostgreSQL
- **Frontend**: Aplicación React con TypeScript y gráficos interactivos
- **Scraping**: Múltiples métodos (API oficial, API noindex, Playwright)
- **Análisis**: Sentimiento en español, análisis temporal, comparación de marcas
- **Visualización**: Gráficos temporales, distribuciones de ratings, análisis de sentimiento

### Arquitectura
- `src/api/`: Cliente ML oficial y rate limiter
- `src/models/`: Modelos `Product` y `Review` con campos extendidos
- `src/services/`: Servicios de scraping, análisis y procesamiento
- `src/web/app.py`: API REST con endpoints modernos
- `frontend/`: Aplicación React con TypeScript y Recharts
- `docs/`: Documentación técnica y arquitectura

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

### Endpoints principales (API REST)

#### Endpoints modernos (recomendados)
- `GET /api/products` — Lista todos los productos con filtros opcionales
- `GET /api/products/{id}` — Detalles de un producto específico
- `GET /api/products/{id}/reviews` — Reviews de un producto (sin límite por defecto)
- `GET /api/products/{id}/reviews/stats` — Estadísticas de reviews de un producto
- `GET /api/reviews` — Lista todas las reviews con filtros
- `GET /api/reviews/timeline` — Datos temporales para gráficos (últimos 365 días)
- `GET /api/reviews/stats` — Estadísticas globales de reviews

#### Endpoints legacy (compatibilidad)
- `GET /health` — Health check
- `GET /api/search?q=...&limit=...` — Búsqueda de productos
- `GET /api/items/{id}` — Producto por ID (legacy)
- `GET /api/items/{id}/reviews` — Reviews de producto (legacy)

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

#### Características del Frontend
- **Análisis por Marca**: Visualización de estadísticas por marca con gráficos interactivos
- **Comparación de Marcas**: Comparación lado a lado de dos marcas
- **Gráficos Temporales**: Evolución de reviews, ratings y sentimiento en el tiempo
- **Análisis de Sentimiento**: Distribución de sentimientos (positivo, negativo, neutral)
- **Distribución de Ratings**: Visualización de estrellas con porcentajes correctos
- **Responsive Design**: Interfaz moderna y adaptativa

#### Páginas disponibles
- `/` - Análisis por marca (página principal)
- `/comparison` - Comparación de marcas
- `/reviews` - Lista de todas las reviews
- `/products` - Lista de productos

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

## Flujo de Trabajo Recomendado

### 1. Extracción de URLs
```bash
# Extraer URLs desde páginas de listado
python3 src/services/extract_urls_simple.py "https://listado.mercadolibre.com.ar/aires-acondicionados" --max-pages 5 --output new_urls.txt

# Combinar con URLs existentes
python3 src/services/merge_urls.py --input new_urls.txt --existing urls.txt --output urls_final.txt --show-stats
```

### 2. Extracción de Datos
```bash
# Extraer información de productos
python3 src/services/extract_product_simple.py

# Extraer reviews
python3 src/services/batch_process_products.py --action reviews --min-reviews 1000
```

### 3. Análisis
```bash
# Análisis de sentimiento
python3 src/services/sentiment_analyzer.py

# Iniciar frontend para visualización
cd frontend && npm run dev
```

## Servicios de Procesamiento

### 1. Extractor de URLs (`extract_urls_simple.py`)
**Extrae URLs de productos desde páginas de listado de MercadoLibre**
```bash
# Extraer URLs de una página de listado
python3 src/services/extract_urls_simple.py "https://listado.mercadolibre.com.ar/aires-acondicionados" --max-pages 5

# Extraer con delay personalizado
python3 src/services/extract_urls_simple.py "https://listado.mercadolibre.com.ar/aires-acondicionados" --max-pages 3 --delay 1.5 --output aires_urls.txt
```

### 2. Combinador de URLs (`merge_urls.py`)
**Combina URLs de diferentes fuentes y elimina duplicados**
```bash
# Combinar URLs extraídas con existentes
python3 src/services/merge_urls.py --input extracted_airs.txt --existing urls.txt --output urls_combined.txt

# Ver estadísticas detalladas
python3 src/services/merge_urls.py --input new_urls.txt --existing old_urls.txt --output combined.txt --show-stats
```

### 3. Scraper Principal (`scrape_final.py`)
**Uso recomendado para ingesta masiva**
```bash
# Por archivo de URLs
python -m src.services.scrape_final --urls-file urls.txt --count 1000

# URLs individuales
python -m src.services.scrape_final --url "https://..." --count 500
```

### 4. Extractor de Productos (`extract_product_simple.py`)
**Para información detallada de productos (marca, modelo, características)**
```bash
# Desde archivo urls.txt
python -m src.services.extract_product_simple

# URL específica
python -m src.services.extract_product_simple "https://..."
```

### 5. Procesamiento Batch (`batch_process_products.py`)
**Para procesar múltiples productos de forma eficiente**
```bash
# Scraping de reviews para todos los productos
python -m src.services.batch_process_products --action reviews --min-reviews 1000

# Análisis de sentimiento
python -m src.services.sentiment_analyzer
```

### 4. Análisis de Sentimiento
**Sistema mejorado para español con palabras clave**
```bash
# Todas las reviews
python -m src.services.sentiment_analyzer

# Desde fecha específica
python -m src.services.sentiment_analyzer --from-date 2024-01-01

# Modo dry-run
python -m src.services.sentiment_analyzer --dry-run
```

## Características Técnicas

### Modelo de Datos Extendido
- **Productos**: ID, título, precio, marca, modelo, características (JSONB), información adicional ML
- **Reviews**: Rating, contenido, fecha original, sentimiento, datos raw de la API
- **Relaciones**: Foreign keys optimizadas con índices

### Análisis de Sentimiento
- **Enfoque híbrido**: TextBlob + diccionario de palabras en español
- **Clasificación**: Positivo, negativo, neutral con score numérico
- **Procesamiento batch**: Eficiente para grandes volúmenes

### API REST Moderna
- **Endpoints RESTful**: Siguiendo convenciones estándar
- **Filtros avanzados**: Por marca, fecha, rating, sentimiento
- **Paginación**: Sin límites por defecto para máxima flexibilidad
- **CORS**: Configurado para desarrollo frontend

### Frontend React
- **TypeScript**: Tipado estático para mejor desarrollo
- **Recharts**: Gráficos interactivos y responsivos
- **Routing**: Navegación entre páginas de análisis
- **Estado global**: Gestión eficiente de datos

## Estado Actual del Proyecto

✅ **Completado**:
- Sistema de scraping completo (API noindex + Playwright)
- Base de datos PostgreSQL con modelos extendidos
- API REST moderna con endpoints completos
- Frontend React con análisis visual
- Análisis de sentimiento en español
- Gráficos temporales y comparativos
- Corrección de fechas y cálculos de porcentajes

🔄 **En progreso**:
- Optimización de performance para grandes volúmenes
- Mejoras en la UI/UX del frontend

📋 **Próximos pasos sugeridos**:
- Autenticación para panel admin
- Scheduler automático para actualizaciones periódicas
- Exportación de datos (CSV, Excel)
- Alertas y notificaciones
- Dashboard ejecutivo con KPIs


