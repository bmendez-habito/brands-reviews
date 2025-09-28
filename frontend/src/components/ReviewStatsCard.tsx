import React from 'react';
import type { ReviewStats } from '../types';

interface ReviewStatsCardProps {
  stats: ReviewStats;
  title?: string;
}

const ReviewStatsCard: React.FC<ReviewStatsCardProps> = ({ stats, title = "Estadísticas de Reviews" }) => {
  const getRatingColor = (rating: number) => {
    if (rating >= 4) return '#4caf50'; // Verde
    if (rating >= 3) return '#ff9800'; // Naranja
    return '#f44336'; // Rojo
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'positive': return '#4caf50';
      case 'negative': return '#f44336';
      case 'neutral': return '#ff9800';
      default: return '#9e9e9e';
    }
  };

  const getSentimentEmoji = (sentiment: string) => {
    switch (sentiment) {
      case 'positive': return '😊';
      case 'negative': return '😞';
      case 'neutral': return '😐';
      default: return '❓';
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
            fontSize: '18px'
          }}
        >
          ★
        </span>
      );
    }
    return stars;
  };

  return (
    <div style={{
      background: 'white',
      borderRadius: '12px',
      padding: '24px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
      marginBottom: '20px'
    }}>
      <h2 style={{
        margin: '0 0 20px 0',
        fontSize: '24px',
        fontWeight: 'bold',
        color: '#333',
        textAlign: 'center'
      }}>
        {title}
      </h2>

      {/* Rating promedio */}
      <div style={{
        textAlign: 'center',
        marginBottom: '30px',
        padding: '20px',
        background: '#f8f9fa',
        borderRadius: '8px'
      }}>
        <h3 style={{ margin: '0 0 10px 0', color: '#333' }}>Rating Promedio</h3>
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '10px' }}>
          {renderStars(Math.round(stats.average_rating))}
          <span style={{
            fontSize: '32px',
            fontWeight: 'bold',
            color: getRatingColor(stats.average_rating)
          }}>
            {stats.average_rating.toFixed(2)}
          </span>
        </div>
      </div>

      {/* Distribución de ratings */}
      <div style={{ marginBottom: '30px' }}>
        <h3 style={{ margin: '0 0 15px 0', color: '#333', fontSize: '18px' }}>Distribución de Ratings</h3>
        <div style={{ display: 'grid', gap: '8px' }}>
          {Object.entries(stats.rating_distribution).map(([rating, count]) => {
            const ratingNum = parseInt(rating.split('_')[0]);
            const percentage = (count / stats.total_reviews) * 100;
            
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
          })}
        </div>
      </div>

      {/* Distribución de sentimientos */}
      <div>
        <h3 style={{ margin: '0 0 15px 0', color: '#333', fontSize: '18px' }}>Análisis de Sentimiento</h3>
        <div style={{ display: 'grid', gap: '12px' }}>
          {Object.entries(stats.sentiment_distribution).map(([sentiment, count]) => {
            const percentage = (count / stats.total_reviews) * 100;
            
            return (
              <div key={sentiment} style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                padding: '10px',
                background: '#f8f9fa',
                borderRadius: '8px'
              }}>
                <span style={{ fontSize: '20px' }}>
                  {getSentimentEmoji(sentiment)}
                </span>
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
          })}
        </div>
      </div>

      {/* Resumen */}
      <div style={{
        marginTop: '20px',
        padding: '15px',
        background: '#e3f2fd',
        borderRadius: '8px',
        textAlign: 'center'
      }}>
        <p style={{ margin: 0, fontSize: '14px', color: '#1976d2' }}>
          Total de reviews analizadas: <strong>{stats.total_reviews.toLocaleString()}</strong>
        </p>
      </div>
    </div>
  );
};

export default ReviewStatsCard;
