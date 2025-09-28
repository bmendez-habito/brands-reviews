import axios from 'axios';
import { config } from '../config';

// Configuración base de la API
const API_BASE_URL = config.apiUrl;

// Crear instancia de axios
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Tipos para la API
export interface Product {
  id: string;
  title: string;
  price: number;
  site_id: string;
  currency_id: string;
  sold_quantity: number;
  available_quantity: number;
  marca: string;
  modelo: string;
  caracteristicas: Record<string, any>;
  ml_additional_info?: {
    url?: string;
    ml_id?: string;
    site?: string;
  };
}

export interface Review {
  id: string;
  product_id: string;
  rate: number;
  title: string;
  content: string;
  date_created: string;
  reviewer_id: string;
  likes: number;
  dislikes: number;
  sentiment_score: number;
  sentiment_label: string;
  api_review_id: string;
  date_text: string;
  source: string;
  media?: Record<string, any>;
}

export interface ProductWithReviews {
  product: Product;
  reviews: Review[];
  total_reviews: number;
}

// Tipos adicionales para estadísticas
export interface ProductStats {
  total_products: number;
  products_with_reviews: number;
  unique_brands: number;
  average_price: number;
}

export interface ReviewStats {
  total_reviews: number;
  average_rating: number;
  rating_distribution: {
    '1_stars': number;
    '2_stars': number;
    '3_stars': number;
    '4_stars': number;
    '5_stars': number;
  };
  sentiment_distribution: {
    positive: number;
    negative: number;
    neutral: number;
  };
}

export interface ProductsResponse {
  products: Product[];
  count: number;
  limit: number;
  offset: number;
}

export interface ReviewsResponse {
  reviews: Review[];
  count: number;
  limit: number;
  offset: number;
  filters?: {
    rating?: number;
    sentiment?: string;
    recent?: boolean;
  };
}

// Funciones de la API
export const apiService = {
  // Health check
  async healthCheck(): Promise<boolean> {
    try {
      console.log('🔍 Intentando conectar a:', API_BASE_URL);
      const response = await api.get('/health');
      console.log('✅ Respuesta del servidor:', response.data);
      return response.status === 200;
    } catch (error) {
      console.error('❌ Health check failed:', error);
      console.error('🔍 URL intentada:', API_BASE_URL + '/health');
      return false;
    }
  },

  // ===== NUEVOS ENDPOINTS DE PRODUCTOS =====
  
  // Obtener todos los productos
  async getProducts(options: {
    limit?: number;
    offset?: number;
    marca?: string;
  } = {}): Promise<ProductsResponse> {
    const params = new URLSearchParams();
    if (options.limit) params.append('limit', options.limit.toString());
    if (options.offset) params.append('offset', options.offset.toString());
    if (options.marca) params.append('marca', options.marca);

    const response = await api.get(`/api/products?${params}`);
    return response.data;
  },

  // Obtener producto por ID (nuevo endpoint)
  async getProduct(productId: string): Promise<Product> {
    const response = await api.get(`/api/products/${productId}`);
    return response.data;
  },

  // Obtener estadísticas de productos
  async getProductsStats(): Promise<ProductStats> {
    const response = await api.get('/api/products/stats');
    return response.data;
  },

  // ===== NUEVOS ENDPOINTS DE REVIEWS =====

  // Obtener reviews con filtros
  async getReviews(options: {
    limit?: number;
    offset?: number;
    rating?: number;
    sentiment?: string;
    recent?: boolean;
  } = {}): Promise<ReviewsResponse> {
    const params = new URLSearchParams();
    if (options.limit) params.append('limit', options.limit.toString());
    if (options.offset) params.append('offset', options.offset.toString());
    if (options.rating) params.append('rating', options.rating.toString());
    if (options.sentiment) params.append('sentiment', options.sentiment);
    if (options.recent) params.append('recent', 'true');

    const response = await api.get(`/api/reviews?${params}`);
    return response.data;
  },

  // Obtener reviews de un producto específico
  async getProductReviews(
    productId: string,
    options: {
      limit?: number;
      offset?: number;
      order_by?: 'date_created' | 'rate' | 'sentiment_score';
    } = {}
  ): Promise<{ product_id: string; reviews: Review[]; count: number; limit: number; offset: number; order_by: string }> {
    const params = new URLSearchParams();
    if (options.limit) params.append('limit', options.limit.toString());
    if (options.offset) params.append('offset', options.offset.toString());
    if (options.order_by) params.append('order_by', options.order_by);

    const response = await api.get(`/api/products/${productId}/reviews?${params}`);
    return response.data;
  },

  // Obtener estadísticas de reviews de un producto
  async getProductReviewsStats(productId: string): Promise<ReviewStats> {
    const response = await api.get(`/api/products/${productId}/reviews/stats`);
    return response.data;
  },

  // Obtener estadísticas generales de reviews
  async getReviewsStats(): Promise<ReviewStats> {
    const response = await api.get('/api/reviews/stats');
    return response.data;
  },

  // Obtener datos temporales de reviews
  async getReviewsTimeline(options: {
    product_id?: string;
    marca?: string;
    days?: number;
  } = {}): Promise<{
    timeline: Array<{
      date: string;
      total_reviews: number;
      avg_rating: number;
      sentiment_positive: number;
      sentiment_negative: number;
      sentiment_neutral: number;
    }>;
    days: number;
    product_id?: string;
    marca?: string;
  }> {
    const params = new URLSearchParams();
    if (options.product_id) params.append('product_id', options.product_id);
    if (options.marca) params.append('marca', options.marca);
    if (options.days) params.append('days', options.days.toString());

    const response = await api.get(`/api/reviews/timeline?${params}`);
    return response.data;
  },

  // ===== ENDPOINTS DE COMPATIBILIDAD (MANTENER) =====

  // Obtener producto por ID (endpoint de compatibilidad)
  async getProductLegacy(productId: string): Promise<Product> {
    const response = await api.get(`/api/items/${productId}`);
    return response.data;
  },

  // Obtener reviews de un producto (endpoint de compatibilidad)
  async getProductReviewsLegacy(
    productId: string,
    options: {
      limit?: number;
      offset?: number;
      refresh?: boolean;
    } = {}
  ): Promise<Review[]> {
    const params = new URLSearchParams();
    if (options.limit) params.append('limit', options.limit.toString());
    if (options.offset) params.append('offset', options.offset.toString());
    if (options.refresh) params.append('refresh', 'true');

    const response = await api.get(`/api/items/${productId}/reviews?${params}`);
    return response.data.reviews;
  },

  // Obtener producto con reviews (usando nuevos endpoints)
  async getProductWithReviews(productId: string): Promise<ProductWithReviews> {
    const [product, reviewsData] = await Promise.all([
      this.getProduct(productId),
      this.getProductReviews(productId) // Sin límite para traer todas las reviews
    ]);

    return {
      product,
      reviews: reviewsData.reviews,
      total_reviews: reviewsData.count,
    };
  },

  // Buscar productos (API externa)
  async searchProducts(query: string, limit: number = 10): Promise<any[]> {
    const response = await api.get(`/api/search?q=${encodeURIComponent(query)}&limit=${limit}`);
    return response.data;
  },

  // Obtener estadísticas de sentimiento
  getSentimentStats(reviews: Review[]) {
    const total = reviews.length;
    const positive = reviews.filter(r => r.sentiment_label === 'positive').length;
    const negative = reviews.filter(r => r.sentiment_label === 'negative').length;
    const neutral = reviews.filter(r => r.sentiment_label === 'neutral').length;
    
    const avgSentiment = total > 0 
      ? reviews.reduce((sum, r) => sum + r.sentiment_score, 0) / total 
      : 0;

    const avgRating = total > 0 
      ? reviews.reduce((sum, r) => sum + r.rate, 0) / total 
      : 0;

    return {
      total,
      positive,
      negative,
      neutral,
      avgSentiment,
      avgRating,
      positivePercentage: total > 0 ? (positive / total) * 100 : 0,
      negativePercentage: total > 0 ? (negative / total) * 100 : 0,
      neutralPercentage: total > 0 ? (neutral / total) * 100 : 0,
    };
  },
};

export default api;
