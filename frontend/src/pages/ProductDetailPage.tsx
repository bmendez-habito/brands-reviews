import React, { useState, useEffect } from 'react';
import type { ProductWithReviews, SentimentStats, LoadingState } from '../types';
import { apiService } from '../services/api';
import ReviewCard from '../components/ReviewCard';

interface ProductDetailPageProps {
  productId: string;
}

const ProductDetailPage: React.FC<ProductDetailPageProps> = ({ productId }) => {
  const [productData, setProductData] = useState<ProductWithReviews | null>(null);
  const [loading, setLoading] = useState<LoadingState>({ isLoading: true, error: null });
  const [sentimentStats, setSentimentStats] = useState<SentimentStats | null>(null);

  useEffect(() => {
    if (productId) {
      loadProductData();
    }
  }, [productId]);

  const loadProductData = async () => {
    try {
      setLoading({ isLoading: true, error: null });
      
      const data = await apiService.getProductWithReviews(productId);
      setProductData(data);
      
      const stats = apiService.getSentimentStats(data.reviews);
      setSentimentStats(stats);
    } catch (error) {
      setLoading({ isLoading: false, error: 'Error al cargar el producto' });
      console.error('Error loading product:', error);
    } finally {
      setLoading({ isLoading: false, error: null });
    }
  };

  const handleRefreshReviews = async () => {
    if (!productData) return;
    
    try {
      setLoading({ isLoading: true, error: null });
      
      const reviews = await apiService.getProductReviews(productId, { 
        limit: 100, 
        refresh: true 
      });
      
      const updatedData = { ...productData, reviews, total_reviews: reviews.length };
      setProductData(updatedData);
      
      const stats = apiService.getSentimentStats(reviews);
      setSentimentStats(stats);
    } catch (error) {
      setLoading({ isLoading: false, error: 'Error al actualizar reviews' });
      console.error('Error refreshing reviews:', error);
    } finally {
      setLoading({ isLoading: false, error: null });
    }
  };

  if (loading.isLoading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '200px',
        fontSize: '18px'
      }}>
        Cargando producto...
      </div>
    );
  }

  if (loading.error) {
    return (
      <div style={{ 
        display: 'flex', 
        flexDirection: 'column',
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '200px',
        fontSize: '18px',
        color: '#d32f2f'
      }}>
        <div>Error: {loading.error}</div>
        <button 
          onClick={loadProductData}
          style={{
            marginTop: '16px',
            padding: '8px 16px',
            backgroundColor: '#1976d2',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Reintentar
        </button>
      </div>
    );
  }

  if (!productData) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '200px',
        fontSize: '18px',
        color: '#666'
      }}>
        Producto no encontrado
      </div>
    );
  }

  const { product, reviews } = productData;

  return (
    <div style={{ padding: '20px' }}>
      {/* Botón de regreso */}
      <button 
        onClick={() => window.history.back()}
        style={{
          marginBottom: '20px',
          padding: '8px 16px',
          backgroundColor: '#f5f5f5',
          border: '1px solid #ddd',
          borderRadius: '4px',
          cursor: 'pointer'
        }}
      >
        ← Volver
      </button>

      {/* Información del producto */}
      <div style={{
        backgroundColor: '#fff',
        border: '1px solid #e0e0e0',
        borderRadius: '8px',
        padding: '24px',
        marginBottom: '24px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
      }}>
        <h1 style={{ 
          fontSize: '28px', 
          fontWeight: 'bold', 
          marginBottom: '16px',
          color: '#333'
        }}>
          {product.title}
        </h1>

        <div style={{ 
          fontSize: '32px', 
          fontWeight: 'bold', 
          color: '#2e7d32',
          marginBottom: '20px'
        }}>
          ${product.price.toLocaleString('es-AR')}
        </div>

        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
          gap: '16px',
          marginBottom: '20px'
        }}>
          <div>
            <strong>Marca:</strong> {product.marca || 'N/A'}
          </div>
          <div>
            <strong>Modelo:</strong> {product.modelo || 'N/A'}
          </div>
          <div>
            <strong>ID:</strong> {product.id}
          </div>
          <div>
            <strong>Vendidos:</strong> {product.sold_quantity}
          </div>
          <div>
            <strong>Disponibles:</strong> {product.available_quantity}
          </div>
          <div>
            <strong>Moneda:</strong> {product.currency_id}
          </div>
        </div>

        {product.ml_additional_info?.url && (
          <a 
            href={product.ml_additional_info.url} 
            target="_blank" 
            rel="noopener noreferrer"
            style={{ 
              color: '#1976d2',
              textDecoration: 'none',
              fontSize: '16px'
            }}
          >
            Ver en MercadoLibre →
          </a>
        )}
      </div>

      {/* Estadísticas de reviews */}
      {sentimentStats && sentimentStats.total > 0 && (
        <div style={{
          backgroundColor: '#f8f9fa',
          border: '1px solid #e0e0e0',
          borderRadius: '8px',
          padding: '20px',
          marginBottom: '24px'
        }}>
          <h2 style={{ 
            fontSize: '24px', 
            fontWeight: 'bold', 
            marginBottom: '16px',
            color: '#333'
          }}>
            Estadísticas de Reviews
          </h2>

          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', 
            gap: '16px',
            marginBottom: '16px'
          }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#333' }}>
                {sentimentStats.total}
              </div>
              <div style={{ fontSize: '14px', color: '#666' }}>Total Reviews</div>
            </div>
            
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#2e7d32' }}>
                {sentimentStats.positive}
              </div>
              <div style={{ fontSize: '14px', color: '#666' }}>Positivos</div>
            </div>
            
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#d32f2f' }}>
                {sentimentStats.negative}
              </div>
              <div style={{ fontSize: '14px', color: '#666' }}>Negativos</div>
            </div>
            
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#f57c00' }}>
                {sentimentStats.neutral}
              </div>
              <div style={{ fontSize: '14px', color: '#666' }}>Neutrales</div>
            </div>
            
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#1976d2' }}>
                {sentimentStats.avgRating.toFixed(1)}
              </div>
              <div style={{ fontSize: '14px', color: '#666' }}>Rating Promedio</div>
            </div>
          </div>

          <button 
            onClick={handleRefreshReviews}
            disabled={loading.isLoading}
            style={{
              padding: '8px 16px',
              backgroundColor: '#1976d2',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: loading.isLoading ? 'not-allowed' : 'pointer',
              opacity: loading.isLoading ? 0.6 : 1
            }}
          >
            {loading.isLoading ? 'Actualizando...' : 'Actualizar Reviews'}
          </button>
        </div>
      )}

      {/* Lista de reviews */}
      <div>
        <h2 style={{ 
          fontSize: '24px', 
          fontWeight: 'bold', 
          marginBottom: '16px',
          color: '#333'
        }}>
          Reviews ({reviews.length})
        </h2>

        {reviews.length === 0 ? (
          <div style={{ 
            textAlign: 'center', 
            padding: '40px',
            color: '#666',
            fontSize: '18px'
          }}>
            No hay reviews disponibles para este producto
          </div>
        ) : (
          <div>
            {reviews.map((review) => (
              <ReviewCard
                key={review.id}
                review={review}
                showProductInfo={false}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ProductDetailPage;
