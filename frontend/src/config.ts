// Configuración de la aplicación
export const config = {
  // URL base de la API
  apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  
  // Modo de desarrollo
  devMode: import.meta.env.VITE_DEV_MODE === 'true' || import.meta.env.DEV,
  
  // Configuraciones por defecto
  defaults: {
    reviewsPerPage: 20,
    maxReviews: 100,
    searchLimit: 10,
  },
  
  // Colores del tema
  colors: {
    primary: '#1976d2',
    secondary: '#424242',
    success: '#2e7d32',
    error: '#d32f2f',
    warning: '#f57c00',
    info: '#0288d1',
  },
};
