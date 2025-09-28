import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useParams, Link, useLocation } from 'react-router-dom';
import ProductsPage from './pages/ProductsPage';
import ProductDetailPage from './pages/ProductDetailPage';
import ReviewsPage from './pages/ReviewsPage';
import { apiService } from './services/api';
import './App.css';

// Componente para enlaces de navegación
const NavigationLink: React.FC<{ to: string; label: string }> = ({ to, label }) => {
  const location = useLocation();
  const isActive = location.pathname === to;
  
  return (
    <Link
      to={to}
      style={{
        padding: '16px 0',
        textDecoration: 'none',
        color: isActive ? '#1976d2' : '#666',
        fontWeight: isActive ? 'bold' : 'normal',
        borderBottom: isActive ? '3px solid #1976d2' : '3px solid transparent',
        transition: 'all 0.2s ease',
        fontSize: '16px'
      }}
    >
      {label}
    </Link>
  );
};

// Componente wrapper para ProductDetailPage
const ProductDetailWrapper: React.FC = () => {
  const { productId } = useParams<{ productId: string }>();
  
  if (!productId) {
    return <div>ID de producto no válido</div>;
  }
  
  return <ProductDetailPage productId={productId} />;
};

const App: React.FC = () => {
  const [isApiConnected, setIsApiConnected] = useState<boolean | null>(null);

  useEffect(() => {
    checkApiConnection();
  }, []);

  const checkApiConnection = async () => {
    try {
      const connected = await apiService.healthCheck();
      setIsApiConnected(connected);
    } catch (error) {
      setIsApiConnected(false);
    }
  };

  return (
    <Router>
      <div className="App">
        {/* Header */}
        <header style={{
          backgroundColor: '#1976d2',
          color: 'white',
          padding: '16px 20px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            maxWidth: '1200px',
            margin: '0 auto'
          }}>
            <h1 style={{ 
              margin: 0, 
              fontSize: '24px',
              fontWeight: 'bold'
            }}>
              ML Reviews Analyzer
            </h1>
            
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <div style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '8px',
                fontSize: '14px'
              }}>
                <div style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  backgroundColor: isApiConnected === true ? '#4caf50' : 
                                 isApiConnected === false ? '#f44336' : '#ff9800'
                }} />
                {isApiConnected === true ? 'API Conectada' :
                 isApiConnected === false ? 'API Desconectada' : 'Verificando...'}
              </div>
              
              {isApiConnected === false && (
                <button 
                  onClick={checkApiConnection}
                  style={{
                    padding: '4px 8px',
                    backgroundColor: 'rgba(255,255,255,0.2)',
                    color: 'white',
                    border: '1px solid rgba(255,255,255,0.3)',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '12px'
                  }}
                >
                  Reintentar
                </button>
              )}
            </div>
          </div>
        </header>

        {/* Navigation */}
        <nav style={{
          backgroundColor: 'white',
          borderBottom: '1px solid #e0e0e0',
          padding: '0 20px'
        }}>
          <div style={{
            maxWidth: '1200px',
            margin: '0 auto',
            display: 'flex',
            gap: '32px'
          }}>
            <NavigationLink to="/" label="Productos" />
            <NavigationLink to="/reviews" label="Reviews" />
          </div>
        </nav>

        {/* Main content */}
        <main style={{ 
          minHeight: 'calc(100vh - 120px)',
          backgroundColor: '#f5f5f5'
        }}>
          <Routes>
            <Route path="/" element={<ProductsPage />} />
            <Route path="/reviews" element={<ReviewsPage />} />
            <Route path="/product/:productId" element={<ProductDetailWrapper />} />
          </Routes>
        </main>

        {/* Footer */}
        <footer style={{
          backgroundColor: '#333',
          color: 'white',
          padding: '20px',
          textAlign: 'center',
          fontSize: '14px'
        }}>
          <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
            <p style={{ margin: 0 }}>
              ML Reviews Analyzer - Análisis de productos y reviews de MercadoLibre
            </p>
            <p style={{ margin: '8px 0 0 0', opacity: 0.7 }}>
              Backend: FastAPI + PostgreSQL | Frontend: React + TypeScript
            </p>
          </div>
        </footer>
      </div>
    </Router>
  );
};

export default App;