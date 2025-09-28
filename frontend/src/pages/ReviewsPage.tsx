import React, { useState, useEffect } from 'react';
import type { Review, ReviewStats, LoadingState } from '../types';
import ReviewCard from '../components/ReviewCard';
import ReviewStatsCard from '../components/ReviewStatsCard';
import { apiService } from '../services/api';

const ReviewsPage: React.FC = () => {
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState<LoadingState>({ isLoading: true, error: null });
  const [stats, setStats] = useState<ReviewStats | null>(null);
  const [filters, setFilters] = useState({
    rating: '',
    sentiment: '',
    recent: false
  });
  const [pagination, setPagination] = useState({
    limit: 20,
    offset: 0
  });

  useEffect(() => {
    loadReviews();
    loadStats();
  }, [filters, pagination]);

  const loadReviews = async () => {
    try {
      setLoading({ isLoading: true, error: null });
      
      const response = await apiService.getReviews({
        limit: pagination.limit,
        offset: pagination.offset,
        rating: filters.rating ? parseInt(filters.rating) : undefined,
        sentiment: filters.sentiment || undefined,
        recent: filters.recent
      });
      
      setReviews(response.reviews);
    } catch (error) {
      setLoading({ isLoading: false, error: 'Error al cargar reviews' });
      console.error('Error loading reviews:', error);
    } finally {
      setLoading({ isLoading: false, error: null });
    }
  };

  const loadStats = async () => {
    try {
      const statsData = await apiService.getReviewsStats();
      setStats(statsData);
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  const handleFilterChange = (key: string, value: string | boolean) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPagination(prev => ({ ...prev, offset: 0 })); // Reset pagination when filtering
  };

  const handleLoadMore = () => {
    setPagination(prev => ({
      ...prev,
      offset: prev.offset + prev.limit
    }));
  };

  const handleResetFilters = () => {
    setFilters({ rating: '', sentiment: '', recent: false });
    setPagination({ limit: 20, offset: 0 });
  };

  if (loading.isLoading && reviews.length === 0) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '200px',
        fontSize: '18px'
      }}>
        Cargando reviews...
      </div>
    );
  }

  if (loading.error && reviews.length === 0) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '200px',
        fontSize: '18px',
        color: '#d32f2f'
      }}>
        Error: {loading.error}
      </div>
    );
  }

  return (
    <div style={{ padding: '20px' }}>
      <h1 style={{ 
        fontSize: '32px', 
        fontWeight: 'bold', 
        marginBottom: '20px',
        color: '#333'
      }}>
        Reviews MercadoLibre
      </h1>

      {/* Estadísticas */}
      {stats && (
        <ReviewStatsCard stats={stats} />
      )}

      {/* Filtros */}
      <div style={{
        background: 'white',
        borderRadius: '12px',
        padding: '20px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        marginBottom: '20px'
      }}>
        <h3 style={{ margin: '0 0 16px 0', color: '#333' }}>Filtros</h3>
        
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '16px',
          alignItems: 'end'
        }}>
          {/* Filtro por rating */}
          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: 'bold' }}>
              Rating:
            </label>
            <select
              value={filters.rating}
              onChange={(e) => handleFilterChange('rating', e.target.value)}
              style={{
                width: '100%',
                padding: '8px',
                border: '2px solid #e0e0e0',
                borderRadius: '6px',
                fontSize: '14px'
              }}
            >
              <option value="">Todos los ratings</option>
              <option value="5">5 estrellas</option>
              <option value="4">4 estrellas</option>
              <option value="3">3 estrellas</option>
              <option value="2">2 estrellas</option>
              <option value="1">1 estrella</option>
            </select>
          </div>

          {/* Filtro por sentimiento */}
          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: 'bold' }}>
              Sentimiento:
            </label>
            <select
              value={filters.sentiment}
              onChange={(e) => handleFilterChange('sentiment', e.target.value)}
              style={{
                width: '100%',
                padding: '8px',
                border: '2px solid #e0e0e0',
                borderRadius: '6px',
                fontSize: '14px'
              }}
            >
              <option value="">Todos los sentimientos</option>
              <option value="positive">😊 Positivo</option>
              <option value="negative">😞 Negativo</option>
              <option value="neutral">😐 Neutral</option>
            </select>
          </div>

          {/* Filtro recientes */}
          <div>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px' }}>
              <input
                type="checkbox"
                checked={filters.recent}
                onChange={(e) => handleFilterChange('recent', e.target.checked)}
                style={{ transform: 'scale(1.2)' }}
              />
              Solo reviews recientes
            </label>
          </div>

          {/* Botón reset */}
          <div>
            <button
              onClick={handleResetFilters}
              style={{
                width: '100%',
                padding: '8px 16px',
                backgroundColor: '#f5f5f5',
                border: '2px solid #e0e0e0',
                borderRadius: '6px',
                fontSize: '14px',
                cursor: 'pointer',
                transition: 'background-color 0.2s ease'
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.backgroundColor = '#e0e0e0';
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.backgroundColor = '#f5f5f5';
              }}
            >
              Limpiar Filtros
            </button>
          </div>
        </div>
      </div>

      {/* Lista de reviews */}
      <div>
        <h3 style={{ margin: '0 0 16px 0', color: '#333' }}>
          Reviews ({reviews.length})
        </h3>
        
        {reviews.map((review) => (
          <ReviewCard key={review.id} review={review} />
        ))}

        {/* Botón cargar más */}
        {reviews.length > 0 && (
          <div style={{ textAlign: 'center', marginTop: '20px' }}>
            <button
              onClick={handleLoadMore}
              disabled={loading.isLoading}
              style={{
                padding: '12px 24px',
                backgroundColor: '#1976d2',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                fontSize: '16px',
                cursor: loading.isLoading ? 'not-allowed' : 'pointer',
                opacity: loading.isLoading ? 0.6 : 1,
                transition: 'background-color 0.2s ease'
              }}
              onMouseOver={(e) => {
                if (!loading.isLoading) {
                  e.currentTarget.style.backgroundColor = '#1565c0';
                }
              }}
              onMouseOut={(e) => {
                if (!loading.isLoading) {
                  e.currentTarget.style.backgroundColor = '#1976d2';
                }
              }}
            >
              {loading.isLoading ? 'Cargando...' : 'Cargar Más Reviews'}
            </button>
          </div>
        )}

        {reviews.length === 0 && !loading.isLoading && (
          <div style={{
            textAlign: 'center',
            padding: '40px',
            color: '#666',
            fontSize: '18px'
          }}>
            No se encontraron reviews con los filtros aplicados
          </div>
        )}
      </div>
    </div>
  );
};

export default ReviewsPage;
