# ML Reviews Analyzer - Frontend

Frontend React con TypeScript para el análisis de productos y reviews de MercadoLibre.

## 🚀 Características

- **React 18** con TypeScript
- **Vite** como bundler (rápido y moderno)
- **React Router** para navegación
- **Axios** para comunicación con la API
- **Componentes reutilizables** para productos y reviews
- **Análisis de sentimiento** visual
- **Diseño responsive** y moderno

## 📁 Estructura

```
src/
├── components/          # Componentes reutilizables
│   ├── ProductCard.tsx  # Tarjeta de producto
│   └── ReviewCard.tsx   # Tarjeta de review
├── pages/              # Páginas de la aplicación
│   ├── ProductsPage.tsx      # Lista de productos
│   └── ProductDetailPage.tsx # Detalle de producto con reviews
├── services/           # Servicios para comunicación con API
│   └── api.ts         # Cliente de API
├── types/             # Tipos TypeScript
│   └── index.ts       # Definiciones de tipos
├── config.ts          # Configuración de la aplicación
└── App.tsx           # Componente principal
```

## 🛠️ Instalación

```bash
# Instalar dependencias
npm install

# Crear archivo de configuración
cp .env.example .env

# Editar configuración
# VITE_API_URL=http://localhost:8000
```

## 🚀 Desarrollo

```bash
# Iniciar servidor de desarrollo
npm run dev

# Construir para producción
npm run build

# Preview de producción
npm run preview
```

## 🔧 Configuración

### Variables de entorno

Crea un archivo `.env` en la raíz del proyecto frontend:

```env
# URL de la API backend
VITE_API_URL=http://localhost:8000

# Modo de desarrollo
VITE_DEV_MODE=true
```

### Conectar con el backend

1. Asegúrate de que el backend esté corriendo en `http://localhost:8000`
2. Verifica que la API responda en `/health`
3. El frontend se conectará automáticamente y mostrará el estado de conexión

## 📱 Funcionalidades

### Página de Productos
- Lista de productos con información básica
- Búsqueda por título, marca o modelo
- Navegación a detalles del producto

### Página de Detalles
- Información completa del producto
- Estadísticas de reviews (positivos, negativos, neutrales)
- Lista de reviews con análisis de sentimiento
- Botón para actualizar reviews desde MercadoLibre

### Componentes
- **ProductCard**: Muestra información básica del producto
- **ReviewCard**: Muestra review individual con análisis de sentimiento
- **Navegación**: Header con estado de conexión de API

## 🎨 Diseño

- **Colores**: Azul primario (#1976d2), verde para positivos, rojo para negativos
- **Layout**: Responsive con grid y flexbox
- **Tipografía**: Sistema de tipografía consistente
- **Iconos**: Emojis para ratings y sentimientos

## 🔌 API Integration

El frontend se conecta con los siguientes endpoints:

- `GET /health` - Health check
- `GET /api/items/{id}` - Obtener producto
- `GET /api/items/{id}/reviews` - Obtener reviews
- `GET /api/search?q={query}` - Buscar productos

## 🚀 Deployment

```bash
# Construir para producción
npm run build

# Los archivos estarán en dist/
# Servir con cualquier servidor estático
```

## 📊 Análisis de Sentimiento

El frontend muestra:
- **Distribución**: Positivos, negativos, neutrales
- **Porcentajes**: Visualización clara de proporciones
- **Rating promedio**: Calificación promedio de estrellas
- **Score de sentimiento**: Puntuación numérica (0-100%)

## 🔄 Estado de Conexión

El header muestra el estado de conexión con la API:
- 🟢 **Verde**: API conectada
- 🔴 **Rojo**: API desconectada
- 🟡 **Amarillo**: Verificando conexión