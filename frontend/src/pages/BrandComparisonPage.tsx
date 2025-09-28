import React, { useState, useEffect } from 'react';
import type { Product, Review, ReviewStats, LoadingState } from '../types';
import { apiService } from '../services/api';
import TimelineCharts from '../components/TimelineCharts';

interface BrandData {
  brand: string;
  products: Product[];
  totalReviews: number;
  averageRating: number;
  ratingDistribution: { [key: string]: number };
  sentimentDistribution: { [key: string]: number };
  averagePrice: number;
  totalProducts: number;
}

const BrandComparisonPage: React.FC = () => {
  const [brands, setBrands] = useState<BrandData[]>([]);
  const [selectedBrandLeft, setSelectedBrandLeft] = useState<string>('');
  const [selectedBrandRight, setSelectedBrandRight] = useState<string>('');
  const [brandDataLeft, setBrandDataLeft] = useState<BrandData | null>(null);
  const [brandDataRight, setBrandDataRight] = useState<BrandData | null>(null);
  const [selectedProductLeft, setSelectedProductLeft] = useState<Product | null>(null);
  const [selectedProductRight, setSelectedProductRight] = useState<Product | null>(null);
  const [productReviewsLeft, setProductReviewsLeft] = useState<Review[]>([]);
  const [productReviewsRight, setProductReviewsRight] = useState<Review[]>([]);
  const [loading, setLoading] = useState<LoadingState>({ isLoading: true, error: null });
  const [filterByProduct, setFilterByProduct] = useState<boolean>(false);
  const [timelineDataLeft, setTimelineDataLeft] = useState<any[]>([]);
  const [timelineDataRight, setTimelineDataRight] = useState<any[]>([]);
  const [timelineLoadingLeft, setTimelineLoadingLeft] = useState<boolean>(false);
  const [timelineLoadingRight, setTimelineLoadingRight] = useState<boolean>(false);

  useEffect(() => {
    loadBrandsData();
  }, []);

  useEffect(() => {
    if (selectedProductLeft) {
      loadProductReviews(selectedProductLeft.id, 'left');
    }
  }, [selectedProductLeft]);

  useEffect(() => {
    if (selectedProductRight) {
      loadProductReviews(selectedProductRight.id, 'right');
    }
  }, [selectedProductRight]);

  useEffect(() => {
    // Reset product selection when filter is disabled
    if (!filterByProduct) {
      setSelectedProductLeft(null);
      setSelectedProductRight(null);
      setProductReviewsLeft([]);
      setProductReviewsRight([]);
    }
  }, [filterByProduct]);

  useEffect(() => {
    // Update brand data when selected brands change
    if (selectedBrandLeft && brands.length > 0) {
      const brandData = brands.find(b => b.brand === selectedBrandLeft);
      setBrandDataLeft(brandData || null);
    } else {
      setBrandDataLeft(null);
    }
  }, [selectedBrandLeft, brands]);

  useEffect(() => {
    // Update brand data when selected brands change
    if (selectedBrandRight && brands.length > 0) {
      const brandData = brands.find(b => b.brand === selectedBrandRight);
      setBrandDataRight(brandData || null);
    } else {
      setBrandDataRight(null);
    }
  }, [selectedBrandRight, brands]);

  useEffect(() => {
    // Load timeline data when brand or product selection changes
    if (brandDataLeft) {
      loadTimelineData('left');
    }
  }, [brandDataLeft, filterByProduct, selectedProductLeft]);

  useEffect(() => {
    // Load timeline data when brand or product selection changes
    if (brandDataRight) {
      loadTimelineData('right');
    }
  }, [brandDataRight, filterByProduct, selectedProductRight]);

  const loadBrandsData = async () => {
    try {
      setLoading({ isLoading: true, error: null });

      const productsResponse = await apiService.getProducts();
      const products = productsResponse.products;

      // Filtrar marcas inválidas
      const invalidBrands = ['', 'Aire', 'Split', 'Inverter', 'Frio', 'Calor', 'Wifi', 'Digital'];
      const validProducts = products.filter(product => 
        product.marca && 
        !invalidBrands.includes(product.marca) && 
        product.marca.length >= 3
      );

      // Agrupar por marca
      const brandGroups: { [key: string]: Product[] } = {};
      validProducts.forEach(product => {
        if (!brandGroups[product.marca]) {
          brandGroups[product.marca] = [];
        }
        brandGroups[product.marca].push(product);
      });

      // Procesar cada marca
      const brandDataPromises = Object.entries(brandGroups).map(async ([brand, brandProducts]) => {
        let totalReviews = 0;
        let ratingSum = 0;
        let ratingCount = 0;
        const ratingDistribution: { [key: string]: number } = {};
        const sentimentDistribution: { [key: string]: number } = {};

        for (const product of brandProducts) {
          try {
            const productReviewsResponse = await apiService.getProductReviews(product.id);
            const reviews = productReviewsResponse.reviews;
            
            totalReviews += reviews.length;
            
            reviews.forEach(review => {
              ratingSum += review.rate;
              ratingCount++;
              
              const rating = review.rate.toString();
              ratingDistribution[rating] = (ratingDistribution[rating] || 0) + 1;
              
              const sentiment = review.sentiment_label || 'neutral';
              sentimentDistribution[sentiment] = (sentimentDistribution[sentiment] || 0) + 1;
            });
          } catch (error) {
            console.error(`Error loading reviews for product ${product.id}:`, error);
          }
        }

        const averageRating = ratingCount > 0 ? ratingSum / ratingCount : 0;
        const averagePrice = brandProducts.reduce((sum, p) => sum + p.price, 0) / brandProducts.length;


        return {
          brand,
          products: brandProducts,
          totalReviews,
          averageRating,
          ratingDistribution,
          sentimentDistribution,
          averagePrice,
          totalProducts: brandProducts.length
        };
      });

      const brandsData = await Promise.all(brandDataPromises);
      setBrands(brandsData);
      setLoading({ isLoading: false, error: null });

    } catch (error) {
      console.error('Error loading brands data:', error);
      setLoading({ isLoading: false, error: error instanceof Error ? error.message : 'Error desconocido' });
    }
  };

  const loadProductReviews = async (productId: string, side: 'left' | 'right') => {
    try {
      const reviewsResponse = await apiService.getProductReviews(productId);
      if (side === 'left') {
        setProductReviewsLeft(reviewsResponse.reviews);
      } else {
        setProductReviewsRight(reviewsResponse.reviews);
      }
    } catch (error) {
      console.error(`Error loading reviews for product ${productId}:`, error);
    }
  };

  const loadTimelineData = async (side: 'left' | 'right') => {
    const brandData = side === 'left' ? brandDataLeft : brandDataRight;
    const selectedProduct = side === 'left' ? selectedProductLeft : selectedProductRight;
    
    if (!brandData) return;
    
    if (side === 'left') {
      setTimelineLoadingLeft(true);
    } else {
      setTimelineLoadingRight(true);
    }
    
    try {
      let productId: string | undefined;
      let marca: string | undefined;
      
      if (filterByProduct && selectedProduct) {
        // Si hay un producto específico seleccionado, usar ese
        productId = selectedProduct.id;
        marca = undefined; // No usar marca cuando hay producto específico
      } else {
        // Si no hay producto específico, usar la marca
        productId = undefined;
        marca = brandData.brand;
      }
      
      const response = await apiService.getReviewsTimeline({
        product_id: productId,
        marca: marca,
        days: 30
      });
      
      if (side === 'left') {
        setTimelineDataLeft(response.timeline);
      } else {
        setTimelineDataRight(response.timeline);
      }
    } catch (error) {
      console.error('Error loading timeline data:', error);
      if (side === 'left') {
        setTimelineDataLeft([]);
      } else {
        setTimelineDataRight([]);
      }
    } finally {
      if (side === 'left') {
        setTimelineLoadingLeft(false);
      } else {
        setTimelineLoadingRight(false);
      }
    }
  };

  const handleBrandSelect = (brand: string, side: 'left' | 'right') => {
    if (side === 'left') {
      setSelectedBrandLeft(brand);
    } else {
      setSelectedBrandRight(brand);
    }
  };

  const handleProductSelect = (product: Product, side: 'left' | 'right') => {
    if (side === 'left') {
      setSelectedProductLeft(product);
    } else {
      setSelectedProductRight(product);
    }
  };

  const renderBrandSection = (
    side: 'left' | 'right',
    selectedBrand: string,
    brandData: BrandData | null,
    selectedProduct: Product | null,
    productReviews: Review[],
    timelineData: any[],
    timelineLoading: boolean
  ) => {
    const brandOptions = brands.map(b => b.brand).filter(b => b !== (side === 'left' ? selectedBrandRight : selectedBrandLeft));
    
    
    return (
      <div style={{ flex: 1, margin: '0 15px' }}>
        <div style={{
          background: 'white',
          borderRadius: '12px',
          padding: '24px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          marginBottom: '30px'
        }}>
          <h2 style={{ margin: '0 0 20px 0', color: '#333', textAlign: 'center' }}>
            {side === 'left' ? 'Marca A' : 'Marca B'}
          </h2>
          
          {/* Selector de Marca */}
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', color: '#555' }}>
              Seleccionar Marca:
            </label>
            <select
              value={selectedBrand}
              onChange={(e) => handleBrandSelect(e.target.value, side)}
              style={{
                width: '100%',
                padding: '12px',
                border: '1px solid #ddd',
                borderRadius: '8px',
                fontSize: '16px',
                backgroundColor: 'white'
              }}
            >
              <option value="">-- Seleccionar marca --</option>
              {brandOptions.map(brand => (
                <option key={brand} value={brand}>
                  {brand}
                </option>
              ))}
            </select>
          </div>

          {/* Estadísticas de la marca */}
          {brandData && (
            <div style={{
              background: '#f8f9fa',
              borderRadius: '8px',
              padding: '16px',
              marginBottom: '20px'
            }}>
              <h3 style={{ margin: '0 0 12px 0', color: '#333' }}>{brandData.brand}</h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#2196f3' }}>
                    {brandData.totalReviews}
                  </div>
                  <div style={{ fontSize: '14px', color: '#666' }}>Total Reviews</div>
                </div>
                <div>
                  <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#4caf50' }}>
                    {brandData.averageRating.toFixed(1)}⭐
                  </div>
                  <div style={{ fontSize: '14px', color: '#666' }}>Rating Promedio</div>
                </div>
                <div>
                  <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#ff9800' }}>
                    {brandData.totalProducts}
                  </div>
                  <div style={{ fontSize: '14px', color: '#666' }}>Productos</div>
                </div>
                <div>
                  <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#9c27b0' }}>
                    ${brandData.averagePrice.toLocaleString()}
                  </div>
                  <div style={{ fontSize: '14px', color: '#666' }}>Precio Promedio</div>
                </div>
              </div>
            </div>
          )}

          {/* Filtro por producto */}
          {brandData && (
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <input
                  type="checkbox"
                  checked={filterByProduct}
                  onChange={(e) => setFilterByProduct(e.target.checked)}
                />
                <span style={{ fontWeight: 'bold', color: '#555' }}>
                  Filtrar por producto específico
                </span>
              </label>
            </div>
          )}

          {/* Selector de Producto */}
          {brandData && filterByProduct && (
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', color: '#555' }}>
                Seleccionar Producto:
              </label>
              <select
                value={selectedProduct?.id || ''}
                onChange={(e) => {
                  const product = brandData.products.find(p => p.id === e.target.value);
                  if (product) handleProductSelect(product, side);
                }}
                style={{
                  width: '100%',
                  padding: '12px',
                  border: '1px solid #ddd',
                  borderRadius: '8px',
                  fontSize: '16px',
                  backgroundColor: 'white'
                }}
              >
                <option value="">-- Seleccionar producto --</option>
                {brandData.products.map(product => (
                  <option key={product.id} value={product.id}>
                    {product.title.substring(0, 50)}...
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Distribución de Ratings */}
          {brandData && (
            <div style={{ marginBottom: '20px' }}>
              <h4 style={{ margin: '0 0 12px 0', color: '#333' }}>Distribución de Ratings</h4>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                {[5, 4, 3, 2, 1].map(rating => {
                  const count = brandData.ratingDistribution[rating.toString()] || 0;
                  const percentage = brandData.totalReviews > 0 ? (count / brandData.totalReviews) * 100 : 0;
                  return (
                    <div key={rating} style={{
                      flex: '1',
                      minWidth: '60px',
                      textAlign: 'center',
                      padding: '8px',
                      background: '#f8f9fa',
                      borderRadius: '6px',
                      border: '1px solid #e9ecef'
                    }}>
                      <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#333' }}>
                        {rating}⭐
                      </div>
                      <div style={{ fontSize: '12px', color: '#666' }}>
                        {count} ({percentage.toFixed(1)}%)
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Distribución de Sentimientos */}
          {brandData && (
            <div style={{ marginBottom: '20px' }}>
              <h4 style={{ margin: '0 0 12px 0', color: '#333' }}>Distribución de Sentimientos</h4>
              <div style={{ display: 'flex', gap: '8px' }}>
                {[
                  { label: 'Positivo', key: 'positive', color: '#4caf50' },
                  { label: 'Neutral', key: 'neutral', color: '#ff9800' },
                  { label: 'Negativo', key: 'negative', color: '#f44336' }
                ].map(({ label, key, color }) => {
                  const count = brandData.sentimentDistribution[key] || 0;
                  const percentage = brandData.totalReviews > 0 ? (count / brandData.totalReviews) * 100 : 0;
                  return (
                    <div key={key} style={{
                      flex: '1',
                      textAlign: 'center',
                      padding: '8px',
                      background: color + '20',
                      borderRadius: '6px',
                      border: `1px solid ${color}40`
                    }}>
                      <div style={{ fontSize: '16px', fontWeight: 'bold', color: color }}>
                        {count}
                      </div>
                      <div style={{ fontSize: '12px', color: '#666' }}>
                        {label} ({percentage.toFixed(1)}%)
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Lista de Productos */}
          {brandData && !filterByProduct && (
            <div style={{ marginBottom: '20px' }}>
              <h4 style={{ margin: '0 0 12px 0', color: '#333' }}>Productos de {brandData.brand}</h4>
              <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
                {brandData.products.map(product => (
                  <div key={product.id} style={{
                    padding: '12px',
                    border: '1px solid #e9ecef',
                    borderRadius: '6px',
                    marginBottom: '8px',
                    cursor: 'pointer',
                    transition: 'background-color 0.2s',
                    backgroundColor: selectedProduct?.id === product.id ? '#e3f2fd' : 'white'
                  }}
                  onClick={() => handleProductSelect(product, side)}
                  >
                    <div style={{ fontWeight: 'bold', color: '#333', marginBottom: '4px' }}>
                      {product.title.substring(0, 60)}...
                    </div>
                    <div style={{ fontSize: '14px', color: '#666' }}>
                      ${product.price.toLocaleString()} • {product.sold_quantity} vendidos
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Reviews del Producto Seleccionado */}
          {selectedProduct && filterByProduct && productReviews.length > 0 && (
            <div style={{ marginBottom: '20px' }}>
              <h4 style={{ margin: '0 0 12px 0', color: '#333' }}>
                Reviews de {selectedProduct.title.substring(0, 40)}...
              </h4>
              <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                {productReviews.slice(0, 10).map(review => (
                  <div key={review.id} style={{
                    padding: '12px',
                    border: '1px solid #e9ecef',
                    borderRadius: '6px',
                    marginBottom: '8px',
                    backgroundColor: '#f8f9fa'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <div style={{ fontWeight: 'bold', color: '#333' }}>
                        {review.rate}⭐
                      </div>
                      <div style={{ fontSize: '12px', color: '#666' }}>
                        {review.date_created ? new Date(review.date_created).toLocaleDateString() : 'Sin fecha'}
                      </div>
                    </div>
                    {review.title && (
                      <div style={{ fontWeight: 'bold', color: '#333', marginBottom: '4px' }}>
                        {review.title}
                      </div>
                    )}
                    <div style={{ fontSize: '14px', color: '#555', lineHeight: '1.4' }}>
                      {review.content}
                    </div>
                    <div style={{ marginTop: '8px', fontSize: '12px', color: '#666' }}>
                      Sentimiento: <span style={{
                        color: review.sentiment_label === 'positive' ? '#4caf50' : 
                               review.sentiment_label === 'negative' ? '#f44336' : '#ff9800'
                      }}>
                        {review.sentiment_label} ({review.sentiment_score.toFixed(2)})
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Gráficos de evolución temporal */}
        {brandData && (
          <div>
            {timelineLoading ? (
              <div style={{
                background: 'white',
                borderRadius: '12px',
                padding: '24px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                marginBottom: '30px',
                textAlign: 'center'
              }}>
                <p style={{ color: '#666' }}>Cargando datos temporales...</p>
              </div>
            ) : (
              <TimelineCharts 
                data={timelineData}
                title={filterByProduct && selectedProduct 
                  ? `${brandData.brand} - ${selectedProduct.title}`
                  : brandData.brand
                }
              />
            )}
          </div>
        )}
      </div>
    );
  };

  if (loading.isLoading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <div style={{ fontSize: '18px', color: '#666' }}>Cargando datos de marcas...</div>
      </div>
    );
  }

  if (loading.error) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <div style={{ fontSize: '18px', color: '#f44336' }}>
          Error: {loading.error}
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: '20px', maxWidth: '1400px', margin: '0 auto' }}>
      <div style={{ marginBottom: '30px', textAlign: 'center' }}>
        <h1 style={{ margin: '0 0 10px 0', color: '#333' }}>
          Comparación de Marcas
        </h1>
        <p style={{ margin: '0', color: '#666', fontSize: '16px' }}>
          Compara estadísticas, reviews y evolución temporal entre dos marcas
        </p>
      </div>

      <div style={{ display: 'flex', gap: '30px', alignItems: 'flex-start' }}>
        {renderBrandSection('left', selectedBrandLeft, brandDataLeft, selectedProductLeft, productReviewsLeft, timelineDataLeft, timelineLoadingLeft)}
        
        <div style={{
          width: '2px',
          background: '#e0e0e0',
          margin: '0 15px',
          minHeight: '100vh'
        }}></div>
        
        {renderBrandSection('right', selectedBrandRight, brandDataRight, selectedProductRight, productReviewsRight, timelineDataRight, timelineLoadingRight)}
      </div>
    </div>
  );
};

export default BrandComparisonPage;
