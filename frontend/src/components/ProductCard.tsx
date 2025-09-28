import React from 'react';
import type { ProductCardProps } from '../types';

const ProductCard: React.FC<ProductCardProps> = ({ product, onClick }) => {
  const handleClick = () => {
    if (onClick) {
      onClick(product);
    }
  };

  return (
    <div 
      className="product-card"
      onClick={handleClick}
      style={{
        border: '1px solid #e0e0e0',
        borderRadius: '8px',
        padding: '16px',
        margin: '8px',
        cursor: onClick ? 'pointer' : 'default',
        backgroundColor: '#fff',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        transition: 'box-shadow 0.2s ease',
      }}
      onMouseEnter={(e) => {
        if (onClick) {
          e.currentTarget.style.boxShadow = '0 4px 8px rgba(0,0,0,0.15)';
        }
      }}
      onMouseLeave={(e) => {
        if (onClick) {
          e.currentTarget.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
        }
      }}
    >
      <div style={{ marginBottom: '12px' }}>
        <h3 style={{ 
          margin: '0 0 8px 0', 
          fontSize: '18px', 
          fontWeight: '600',
          color: '#333',
          lineHeight: '1.4'
        }}>
          {product.title}
        </h3>
        
        <div style={{ 
          fontSize: '24px', 
          fontWeight: 'bold', 
          color: '#2e7d32',
          marginBottom: '8px'
        }}>
          ${product.price.toLocaleString('es-AR')}
        </div>
      </div>

      <div style={{ 
        display: 'flex', 
        flexDirection: 'column', 
        gap: '4px',
        fontSize: '14px',
        color: '#666'
      }}>
        {product.marca && (
          <div>
            <strong>Marca:</strong> {product.marca}
          </div>
        )}
        
        {product.modelo && (
          <div>
            <strong>Modelo:</strong> {product.modelo}
          </div>
        )}
        
        <div>
          <strong>ID:</strong> {product.id}
        </div>
        
        <div>
          <strong>Vendidos:</strong> {product.sold_quantity}
        </div>
        
        <div>
          <strong>Disponibles:</strong> {product.available_quantity}
        </div>
      </div>

      {product.ml_additional_info?.url && (
        <div style={{ 
          marginTop: '12px', 
          fontSize: '12px',
          color: '#888'
        }}>
          <a 
            href={product.ml_additional_info.url} 
            target="_blank" 
            rel="noopener noreferrer"
            style={{ 
              color: '#1976d2',
              textDecoration: 'none'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            Ver en MercadoLibre →
          </a>
        </div>
      )}
    </div>
  );
};

export default ProductCard;
