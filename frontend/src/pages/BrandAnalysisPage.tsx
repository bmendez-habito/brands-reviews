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

const BrandAnalysisPage: React.FC = () => {
  const [brands, setBrands] = useState<BrandData[]>([]);
  const [selectedBrand, setSelectedBrand] = useState<string>('');
  const [selectedBrandData, setSelectedBrandData] = useState<BrandData | null>(null);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [productReviews, setProductReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState<LoadingState>({ isLoading: true, error: null });
  const [filterByProduct, setFilterByProduct] = useState<boolean>(false);
  const [timelineData, setTimelineData] = useState<any[]>([]);
  const [timelineLoading, setTimelineLoading] = useState<boolean>(false);

  useEffect(() => {
    loadBrandsData();
  }, []);

  useEffect(() => {
    if (selectedProduct) {
      loadProductReviews(selectedProduct.id);
    }
  }, [selectedProduct]);

  useEffect(() => {
    // Reset product selection when filter is disabled
    if (!filterByProduct) {
      setSelectedProduct(null);
      setProductReviews([]);
    }
  }, [filterByProduct]);

  useEffect(() => {
    // Update selectedBrandData when selectedBrand or brands change
    if (selectedBrand && brands.length > 0) {
      const brandData = brands.find(b => b.brand === selectedBrand);
      setSelectedBrandData(brandData || null);
    } else {
      setSelectedBrandData(null);
    }
  }, [selectedBrand, brands]);

  useEffect(() => {
    // Load timeline data when brand or product selection changes
    if (selectedBrandData) {
      loadTimelineData();
    }
  }, [selectedBrandData, filterByProduct, selectedProduct]);

  const loadBrandsData = async () => {
    try {
      setLoading({ isLoading: true, error: null });
      
      // Obtener todos los productos (sin límite)
      const productsResponse = await apiService.getProducts();
      const allProducts = productsResponse.products;
      
      // Agrupar por marca (filtrar marcas inválidas)
      const brandMap = new Map<string, Product[]>();
      const invalidBrands = ['Aire', 'Split', 'Inverter', 'Color', 'Blanco', 'Negro', 'Portátil', 'Frío', 'Calor'];
      
      allProducts.forEach(product => {
        if (product.marca && !invalidBrands.includes(product.marca) && product.marca.length > 2) {
          if (!brandMap.has(product.marca)) {
            brandMap.set(product.marca, []);
          }
          brandMap.get(product.marca)!.push(product);
        }
      });

      // Obtener datos de reviews para cada marca
      const brandsData: BrandData[] = [];
      
      for (const [brand, products] of brandMap) {
        const brandData: BrandData = {
          brand,
          products,
          totalReviews: 0,
          averageRating: 0,
          ratingDistribution: { '1_stars': 0, '2_stars': 0, '3_stars': 0, '4_stars': 0, '5_stars': 0 },
          sentimentDistribution: { positive: 0, negative: 0, neutral: 0 },
          averagePrice: 0,
          totalProducts: products.length
        };

        // Calcular precio promedio
        brandData.averagePrice = products.reduce((sum, p) => sum + p.price, 0) / products.length;

        // Obtener reviews para cada producto de la marca
        let totalRating = 0;
        let reviewCount = 0;
        
        for (const product of products) {
          try {
            const reviewsResponse = await apiService.getProductReviews(product.id); // Sin límite para traer todas las reviews
            const reviews = reviewsResponse.reviews;
            
            brandData.totalReviews += reviews.length;
            
            // Calcular distribución de ratings
            reviews.forEach(review => {
              const ratingKey = `${review.rate}_stars` as keyof typeof brandData.ratingDistribution;
              if (brandData.ratingDistribution[ratingKey] !== undefined) {
                brandData.ratingDistribution[ratingKey]++;
              }
              
              // Calcular distribución de sentimientos
              const sentimentKey = review.sentiment_label as keyof typeof brandData.sentimentDistribution;
              if (brandData.sentimentDistribution[sentimentKey] !== undefined) {
                brandData.sentimentDistribution[sentimentKey]++;
              }
              
              totalRating += review.rate;
              reviewCount++;
            });
          } catch (error) {
            console.warn(`Error cargando reviews para producto ${product.id}:`, error);
          }
        }

        // Calcular rating promedio
        if (reviewCount > 0) {
          brandData.averageRating = totalRating / reviewCount;
        }

        brandsData.push(brandData);
      }

      // Ordenar por número de reviews (más populares primero)
      brandsData.sort((a, b) => b.totalReviews - a.totalReviews);
      
      setBrands(brandsData);
      
      // Seleccionar la primera marca por defecto
      if (brandsData.length > 0) {
        setSelectedBrand(brandsData[0].brand);
      }
      
    } catch (error) {
      setLoading({ isLoading: false, error: 'Error al cargar datos de marcas' });
      console.error('Error loading brands data:', error);
    } finally {
      setLoading({ isLoading: false, error: null });
    }
  };

  const loadProductReviews = async (productId: string) => {
    try {
      const reviewsResponse = await apiService.getProductReviews(productId); // Sin límite para traer todas las reviews
      setProductReviews(reviewsResponse.reviews);
    } catch (error) {
      console.error('Error loading product reviews:', error);
      setProductReviews([]);
    }
  };

  const loadTimelineData = async () => {
    if (!selectedBrandData) return;
    
    setTimelineLoading(true);
    try {
      const productId = filterByProduct && selectedProduct ? selectedProduct.id : undefined;
      const response = await apiService.getReviewsTimeline({
        product_id: productId,
        days: 30
      });
      setTimelineData(response.timeline);
    } catch (error) {
      console.error('Error loading timeline data:', error);
      setTimelineData([]);
    } finally {
      setTimelineLoading(false);
    }
  };

  // Helper function to get current stats (brand or product specific)
  const getCurrentStats = () => {
    if (filterByProduct && selectedProduct && productReviews.length > 0) {
      // Product-specific stats
      const totalReviews = productReviews.length;
      const averageRating = productReviews.reduce((sum, r) => sum + r.rate, 0) / totalReviews;
      const totalProducts = 1;
      const averagePrice = selectedProduct.price;
      
      return {
        totalReviews,
        averageRating,
        totalProducts,
        averagePrice,
        reviewStats: apiService.getSentimentStats(productReviews)
      };
    } else {
      // Brand-wide stats
      return {
        totalReviews: selectedBrandData?.totalReviews || 0,
        averageRating: selectedBrandData?.averageRating || 0,
        totalProducts: selectedBrandData?.totalProducts || 0,
        averagePrice: selectedBrandData?.averagePrice || 0,
        reviewStats: selectedBrandData?.reviewStats || null
      };
    }
  };

  const getRatingColor = (rating: number) => {
    if (rating >= 4) return '#4caf50';
    if (rating >= 3) return '#ff9800';
    return '#f44336';
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'positive': return '#4caf50';
      case 'negative': return '#f44336';
      case 'neutral': return '#ff9800';
      default: return '#9e9e9e';
    }
  };

  const renderStars = (rating: number) => {
    const stars = [];
    for (let i = 1; i <= 5; i++) {
      stars.push(
        <span
          key={i}
          style={{
            color: i <= rating ? '#ffc107' : '#e0e0e0',
            fontSize: '20px'
          }}
        >
          ★
        </span>
      );
    }
    return stars;
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
        Cargando análisis de marcas...
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
        Análisis por Marca
      </h1>

      {/* Selector de marca */}
      <div style={{ marginBottom: '30px' }}>
        <h3 style={{ margin: '0 0 16px 0', color: '#333' }}>Seleccionar Marca:</h3>
        
        <select
          value={selectedBrand}
          onChange={(e) => {
            setSelectedBrand(e.target.value);
            setFilterByProduct(false); // Reset product filter when brand changes
            setSelectedProduct(null);
          }}
          style={{
            padding: '12px',
            fontSize: '16px',
            border: '2px solid #e0e0e0',
            borderRadius: '8px',
            outline: 'none',
            backgroundColor: 'white',
            minWidth: '250px'
          }}
          disabled={brands.length === 0}
        >
          {brands.length === 0 ? (
            <option value="">Cargando marcas...</option>
          ) : (
            brands.map(brand => (
              <option key={brand.brand} value={brand.brand}>
                {brand.brand} ({brand.totalReviews} reviews)
              </option>
            ))
          )}
        </select>
      </div>

      {/* Selector de producto (opcional) */}
      {selectedBrandData && (
        <div style={{ marginBottom: '30px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '16px' }}>
            <label style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '8px', 
              cursor: 'pointer',
              fontSize: '16px',
              color: '#333'
            }}>
              <input
                type="checkbox"
                checked={filterByProduct}
                onChange={(e) => setFilterByProduct(e.target.checked)}
                style={{ transform: 'scale(1.2)' }}
              />
              Filtrar por producto específico
            </label>
          </div>

          {filterByProduct && (
            <>
              <h3 style={{ margin: '0 0 16px 0', color: '#333' }}>Seleccionar Producto:</h3>
              
              <select
                value={selectedProduct?.id || ''}
                onChange={(e) => {
                  const productId = e.target.value;
                  const product = selectedBrandData.products.find(p => p.id === productId);
                  setSelectedProduct(product || null);
                }}
                style={{
                  padding: '12px',
                  fontSize: '16px',
                  border: '2px solid #e0e0e0',
                  borderRadius: '8px',
                  outline: 'none',
                  backgroundColor: 'white',
                  minWidth: '400px'
                }}
              >
                <option value="">Seleccionar un producto...</option>
                {selectedBrandData.products.map(product => (
                  <option key={product.id} value={product.id}>
                    {product.title.length > 60 
                      ? `${product.title.substring(0, 60)}...` 
                      : product.title
                    } - ${product.price.toLocaleString()}
                  </option>
                ))}
              </select>
            </>
          )}
        </div>
      )}

      {selectedBrandData && (
        <>
          {/* Estadísticas de la marca */}
          <div style={{
            background: 'white',
            borderRadius: '12px',
            padding: '24px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            marginBottom: '30px'
          }}>
            <h2 style={{ margin: '0 0 20px 0', color: '#333' }}>
              {filterByProduct && selectedProduct 
                ? `${selectedBrandData.brand} - ${selectedProduct.title}`
                : selectedBrandData.brand
              }
            </h2>
            
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '20px',
              marginBottom: '20px'
            }}>
              {(() => {
                const stats = getCurrentStats();
                return (
                  <>
                    <div style={{ textAlign: 'center' }}>
                      <h4 style={{ margin: '0 0 8px 0', color: '#666' }}>Total Reviews</h4>
                      <p style={{ margin: 0, fontSize: '24px', fontWeight: 'bold', color: '#1976d2' }}>
                        {stats.totalReviews.toLocaleString()}
                      </p>
                    </div>
                    
                    <div style={{ textAlign: 'center' }}>
                      <h4 style={{ margin: '0 0 8px 0', color: '#666' }}>Rating Promedio</h4>
                      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px' }}>
                        {renderStars(Math.round(stats.averageRating))}
                        <span style={{
                          fontSize: '24px',
                          fontWeight: 'bold',
                          color: getRatingColor(stats.averageRating)
                        }}>
                          {stats.averageRating.toFixed(2)}
                        </span>
                      </div>
                    </div>
                    
                    <div style={{ textAlign: 'center' }}>
                      <h4 style={{ margin: '0 0 8px 0', color: '#666' }}>Productos</h4>
                      <p style={{ margin: 0, fontSize: '24px', fontWeight: 'bold', color: '#1976d2' }}>
                        {stats.totalProducts}
                      </p>
                    </div>
                    
                    <div style={{ textAlign: 'center' }}>
                      <h4 style={{ margin: '0 0 8px 0', color: '#666' }}>Precio Promedio</h4>
                      <p style={{ margin: 0, fontSize: '24px', fontWeight: 'bold', color: '#1976d2' }}>
                        ${stats.averagePrice.toLocaleString()}
                      </p>
                    </div>
                  </>
                );
              })()}
            </div>

            {/* Distribución de ratings */}
            <div style={{ marginBottom: '20px' }}>
              <h4 style={{ margin: '0 0 12px 0', color: '#333' }}>Distribución de Ratings</h4>
              <div style={{ display: 'grid', gap: '8px' }}>
                {(() => {
                  const stats = getCurrentStats();
                  const ratingDistribution = stats.reviewStats?.rating_distribution || {};
                  return Object.entries(ratingDistribution).map(([rating, count]) => {
                    const ratingNum = parseInt(rating.split('_')[0]);
                    const percentage = stats.totalReviews > 0 
                      ? (count / stats.totalReviews) * 100 
                      : 0;
                  
                  return (
                    <div key={rating} style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span style={{ minWidth: '80px', fontSize: '14px' }}>
                        {renderStars(ratingNum)} ({count})
                      </span>
                      <div style={{
                        flex: 1,
                        height: '20px',
                        background: '#e0e0e0',
                        borderRadius: '10px',
                        overflow: 'hidden'
                      }}>
                        <div style={{
                          width: `${percentage}%`,
                          height: '100%',
                          background: getRatingColor(ratingNum),
                          transition: 'width 0.3s ease'
                        }} />
                      </div>
                      <span style={{ minWidth: '40px', fontSize: '12px', textAlign: 'right' }}>
                        {percentage.toFixed(1)}%
                      </span>
                    </div>
                  );
                  });
                })()}
              </div>
            </div>

            {/* Distribución de sentimientos */}
            <div>
              <h4 style={{ margin: '0 0 12px 0', color: '#333' }}>Análisis de Sentimiento</h4>
              <div style={{ display: 'grid', gap: '12px' }}>
                {(() => {
                  const stats = getCurrentStats();
                  const sentimentDistribution = stats.reviewStats?.sentiment_distribution || {};
                  return Object.entries(sentimentDistribution).map(([sentiment, count]) => {
                    const percentage = stats.totalReviews > 0 
                      ? (count / stats.totalReviews) * 100 
                      : 0;
                  
                  return (
                    <div key={sentiment} style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '10px',
                      padding: '10px',
                      background: '#f8f9fa',
                      borderRadius: '8px'
                    }}>
                      <span style={{
                        minWidth: '80px',
                        fontSize: '14px',
                        fontWeight: 'bold',
                        textTransform: 'capitalize',
                        color: getSentimentColor(sentiment)
                      }}>
                        {sentiment}
                      </span>
                      <div style={{
                        flex: 1,
                        height: '16px',
                        background: '#e0e0e0',
                        borderRadius: '8px',
                        overflow: 'hidden'
                      }}>
                        <div style={{
                          width: `${percentage}%`,
                          height: '100%',
                          background: getSentimentColor(sentiment),
                          transition: 'width 0.3s ease'
                        }} />
                      </div>
                      <span style={{ minWidth: '60px', fontSize: '12px', textAlign: 'right' }}>
                        {count} ({percentage.toFixed(1)}%)
                      </span>
                    </div>
                  );
                  });
                })()}
              </div>
            </div>
          </div>

          {/* Lista de productos de la marca - solo si no está filtrando por producto */}
          {!filterByProduct && (
            <div style={{
              background: 'white',
              borderRadius: '12px',
              padding: '24px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
              marginBottom: '30px'
            }}>
              <h3 style={{ margin: '0 0 20px 0', color: '#333' }}>
                Productos de {selectedBrandData.brand}
              </h3>
            
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
              gap: '16px'
            }}>
              {selectedBrandData.products.map(product => (
                <div
                  key={product.id}
                  onClick={() => setSelectedProduct(product)}
                  style={{
                    padding: '16px',
                    border: selectedProduct?.id === product.id ? '2px solid #1976d2' : '1px solid #e0e0e0',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    backgroundColor: selectedProduct?.id === product.id ? '#f3e5f5' : 'white'
                  }}
                  onMouseOver={(e) => {
                    if (selectedProduct?.id !== product.id) {
                      e.currentTarget.style.backgroundColor = '#f5f5f5';
                    }
                  }}
                  onMouseOut={(e) => {
                    if (selectedProduct?.id !== product.id) {
                      e.currentTarget.style.backgroundColor = 'white';
                    }
                  }}
                >
                  <h4 style={{ margin: '0 0 8px 0', fontSize: '16px', color: '#333' }}>
                    {product.title}
                  </h4>
                  <p style={{ margin: '0 0 8px 0', fontSize: '18px', fontWeight: 'bold', color: '#1976d2' }}>
                    ${product.price.toLocaleString()}
                  </p>
                  {product.modelo && (
                    <p style={{ margin: '0 0 8px 0', fontSize: '14px', color: '#666' }}>
                      Modelo: {product.modelo}
                    </p>
                  )}
                  <p style={{ margin: 0, fontSize: '12px', color: '#999' }}>
                    ID: {product.id}
                  </p>
                </div>
              ))}
            </div>
            </div>
          )}

          {/* Reviews del producto seleccionado */}
          {selectedProduct && productReviews.length > 0 && (
            <div style={{
              background: 'white',
              borderRadius: '12px',
              padding: '24px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
            }}>
              <h3 style={{ margin: '0 0 20px 0', color: '#333' }}>
                Reviews de: {selectedProduct.title}
              </h3>
              
              {productReviews.length > 0 ? (
                <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
                  {productReviews.slice(0, 10).map(review => (
                    <div key={review.id} style={{
                      padding: '12px',
                      borderBottom: '1px solid #e0e0e0',
                      marginBottom: '8px'
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          {renderStars(review.rate)}
                          <span style={{ fontWeight: 'bold', color: getRatingColor(review.rate) }}>
                            {review.rate}/5
                          </span>
                        </div>
                        <span style={{
                          padding: '4px 8px',
                          borderRadius: '12px',
                          backgroundColor: '#f5f5f5',
                          fontSize: '12px',
                          color: getSentimentColor(review.sentiment_label)
                        }}>
                          {review.sentiment_label}
                        </span>
                      </div>
                      
                      {review.title && (
                        <h5 style={{ margin: '0 0 4px 0', fontSize: '14px', fontWeight: 'bold' }}>
                          {review.title}
                        </h5>
                      )}
                      
                      <p style={{ margin: '0 0 8px 0', fontSize: '14px', color: '#555' }}>
                        {review.content}
                      </p>
                      
                      <p style={{ margin: 0, fontSize: '12px', color: '#999' }}>
                        {new Date(review.date_created).toLocaleDateString('es-AR')}
                      </p>
                    </div>
                  ))}
                  
                  {productReviews.length > 10 && (
                    <p style={{ textAlign: 'center', color: '#666', fontSize: '14px' }}>
                      Mostrando 10 de {productReviews.length} reviews
                    </p>
                  )}
                </div>
              ) : (
                <p style={{ textAlign: 'center', color: '#666' }}>
                  No hay reviews disponibles para este producto
                </p>
              )}
            </div>
          )}

          {/* Gráficos de evolución temporal */}
          {selectedBrandData && (
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
                    ? `${selectedBrandData.brand} - ${selectedProduct.title}`
                    : selectedBrandData.brand
                  }
                />
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default BrandAnalysisPage;
