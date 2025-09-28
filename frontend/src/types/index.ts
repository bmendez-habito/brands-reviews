// Re-exportar tipos de la API
export type { 
  Product, 
  Review, 
  ProductWithReviews,
  ProductStats,
  ReviewStats,
  ProductsResponse,
  ReviewsResponse
} from '../services/api';

// Tipos adicionales para el frontend
export interface SentimentStats {
  total: number;
  positive: number;
  negative: number;
  neutral: number;
  avgSentiment: number;
  avgRating: number;
  positivePercentage: number;
  negativePercentage: number;
  neutralPercentage: number;
}

export interface LoadingState {
  isLoading: boolean;
  error: string | null;
}

export interface ProductCardProps {
  product: import('../services/api').Product;
  onClick?: (product: import('../services/api').Product) => void;
}

export interface ReviewCardProps {
  review: import('../services/api').Review;
  showProductInfo?: boolean;
}

export interface SentimentChartProps {
  stats: SentimentStats;
}

export interface SearchFilters {
  minRating?: number;
  maxRating?: number;
  sentiment?: 'positive' | 'negative' | 'neutral';
  dateFrom?: string;
  dateTo?: string;
}

export interface SearchParams {
  query: string;
  filters?: SearchFilters;
  limit?: number;
  offset?: number;
}
