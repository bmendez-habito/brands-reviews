import React, { useState, useEffect } from 'react';
import type { Product, LoadingState, ProductStats } from '../types';
import ProductCard from '../components/ProductCard';
import { apiService } from '../services/api';

const ProductsPage: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState<LoadingState>({ isLoading: true, error: null });
  const [searchQuery, setSearchQuery] = useState('');
  const [brandFilter, setBrandFilter] = useState('');
  const [stats, setStats] = useState<ProductStats | null>(null);
  const [availableBrands, setAvailableBrands] = useState<string[]>([]);

  useEffect(() => {
    loadProducts();
    loadStats();
  }, []);

  const loadProducts = async () => {
    try {
      setLoading({ isLoading: true, error: null });
      
      const response = await apiService.getProducts({ 
        limit: 50,
        marca: brandFilter || undefined 
      });
      
      setProducts(response.products);
      
      // Extraer marcas únicas para el filtro
      const brands = [...new Set(response.products.map(p => p.marca).filter(m => m))];
      setAvailableBrands(brands);
      
    } catch (error) {
      setLoading({ isLoading: false, error: 'Error al cargar productos' });
      console.error('Error loading products:', error);
    } finally {
      setLoading({ isLoading: false, error: null });
    }
  };

  const loadStats = async () => {
    try {
      const statsData = await apiService.getProductsStats();
      setStats(statsData);
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  useEffect(() => {
    loadProducts();
  }, [brandFilter]);

  const handleProductClick = (product: Product) => {
    // Navegar a la página de detalles del producto
    window.location.href = `/product/${product.id}`;
  };

  const filteredProducts = products.filter(product =>
    product.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    product.marca.toLowerCase().includes(searchQuery.toLowerCase()) ||
    product.modelo.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading.isLoading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '200px',
        fontSize: '18px'
      }}>
        Cargando productos...
      </div>
    );
  }

  if (loading.error) {
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
        Productos MercadoLibre
      </h1>

      {/* Estadísticas */}
      {stats && (
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
          gap: '16px', 
          marginBottom: '30px' 
        }}>
          <div style={{ 
            background: '#f5f5f5', 
            padding: '16px', 
            borderRadius: '8px',
            textAlign: 'center'
          }}>
            <h3 style={{ margin: '0 0 8px 0', color: '#1976d2' }}>Total Productos</h3>
            <p style={{ margin: 0, fontSize: '24px', fontWeight: 'bold' }}>{stats.total_products}</p>
          </div>
          <div style={{ 
            background: '#f5f5f5', 
            padding: '16px', 
            borderRadius: '8px',
            textAlign: 'center'
          }}>
            <h3 style={{ margin: '0 0 8px 0', color: '#1976d2' }}>Con Reviews</h3>
            <p style={{ margin: 0, fontSize: '24px', fontWeight: 'bold' }}>{stats.products_with_reviews}</p>
          </div>
          <div style={{ 
            background: '#f5f5f5', 
            padding: '16px', 
            borderRadius: '8px',
            textAlign: 'center'
          }}>
            <h3 style={{ margin: '0 0 8px 0', color: '#1976d2' }}>Marcas Únicas</h3>
            <p style={{ margin: 0, fontSize: '24px', fontWeight: 'bold' }}>{stats.unique_brands}</p>
          </div>
          <div style={{ 
            background: '#f5f5f5', 
            padding: '16px', 
            borderRadius: '8px',
            textAlign: 'center'
          }}>
            <h3 style={{ margin: '0 0 8px 0', color: '#1976d2' }}>Precio Promedio</h3>
            <p style={{ margin: 0, fontSize: '24px', fontWeight: 'bold' }}>
              ${stats.average_price.toLocaleString()}
            </p>
          </div>
        </div>
      )}

      {/* Filtros */}
      <div style={{ 
        display: 'flex', 
        gap: '16px', 
        marginBottom: '20px',
        flexWrap: 'wrap',
        alignItems: 'center'
      }}>
        <input
          type="text"
          placeholder="Buscar productos por título, marca o modelo..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{
            flex: '1',
            minWidth: '300px',
            padding: '12px',
            fontSize: '16px',
            border: '2px solid #e0e0e0',
            borderRadius: '8px',
            outline: 'none',
            transition: 'border-color 0.2s ease'
          }}
          onFocus={(e) => {
            e.target.style.borderColor = '#1976d2';
          }}
          onBlur={(e) => {
            e.target.style.borderColor = '#e0e0e0';
          }}
        />
        
        <select
          value={brandFilter}
          onChange={(e) => setBrandFilter(e.target.value)}
          style={{
            padding: '12px',
            fontSize: '16px',
            border: '2px solid #e0e0e0',
            borderRadius: '8px',
            outline: 'none',
            backgroundColor: 'white',
            minWidth: '150px'
          }}
        >
          <option value="">Todas las marcas</option>
          {availableBrands.map(brand => (
            <option key={brand} value={brand}>{brand}</option>
          ))}
        </select>
      </div>

      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', 
        gap: '16px' 
      }}>
        {filteredProducts.map((product) => (
          <ProductCard
            key={product.id}
            product={product}
            onClick={handleProductClick}
          />
        ))}
      </div>

      {filteredProducts.length === 0 && searchQuery && (
        <div style={{ 
          textAlign: 'center', 
          padding: '40px',
          color: '#666',
          fontSize: '18px'
        }}>
          No se encontraron productos que coincidan con "{searchQuery}"
        </div>
      )}

      {filteredProducts.length === 0 && !searchQuery && (
        <div style={{ 
          textAlign: 'center', 
          padding: '40px',
          color: '#666',
          fontSize: '18px'
        }}>
          No hay productos disponibles
        </div>
      )}
    </div>
  );
};

export default ProductsPage;
