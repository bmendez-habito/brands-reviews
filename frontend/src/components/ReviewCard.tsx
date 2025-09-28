import React from 'react';
import type { Review } from '../types';

interface ReviewCardProps {
  review: Review;
}

const ReviewCard: React.FC<ReviewCardProps> = ({ review }) => {
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
            fontSize: '16px'
          }}
        >
          ★
        </span>
      );
    }
    return stars;
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('es-AR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    } catch {
      return dateString;
    }
  };

  return (
    <div style={{
      background: 'white',
      borderRadius: '12px',
      padding: '20px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
      marginBottom: '16px',
      border: '1px solid #e0e0e0'
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        marginBottom: '12px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {renderStars(review.rate)}
          <span style={{
            fontSize: '18px',
            fontWeight: 'bold',
            color: getRatingColor(review.rate)
          }}>
            {review.rate}/5
          </span>
        </div>
        
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          fontSize: '14px',
          color: '#666'
        }}>
          <span style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            padding: '4px 8px',
            borderRadius: '12px',
            backgroundColor: '#f5f5f5'
          }}>
            <span>{getSentimentEmoji(review.sentiment_label)}</span>
            <span style={{
              color: getSentimentColor(review.sentiment_label),
              fontWeight: 'bold'
            }}>
              {review.sentiment_label}
            </span>
          </span>
          {review.date_created && (
            <span>{formatDate(review.date_created)}</span>
          )}
        </div>
      </div>

      {/* Título */}
      {review.title && (
        <h4 style={{
          margin: '0 0 8px 0',
          fontSize: '16px',
          fontWeight: 'bold',
          color: '#333'
        }}>
          {review.title}
        </h4>
      )}

      {/* Contenido */}
      <p style={{
        margin: '0 0 12px 0',
        fontSize: '14px',
        lineHeight: '1.5',
        color: '#555'
      }}>
        {review.content}
      </p>

      {/* Footer con interacciones */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        fontSize: '12px',
        color: '#666'
      }}>
        <div style={{ display: 'flex', gap: '16px' }}>
          {review.likes > 0 && (
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              👍 {review.likes}
            </span>
          )}
          {review.dislikes > 0 && (
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              👎 {review.dislikes}
            </span>
          )}
        </div>
        
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          {review.sentiment_score > 0 && (
            <span style={{
              padding: '2px 6px',
              borderRadius: '8px',
              backgroundColor: '#e3f2fd',
              color: '#1976d2',
              fontSize: '11px'
            }}>
              Sentiment: {(review.sentiment_score * 100).toFixed(0)}%
            </span>
          )}
          {review.source && (
            <span style={{
              padding: '2px 6px',
              borderRadius: '8px',
              backgroundColor: '#f3e5f5',
              color: '#7b1fa2',
              fontSize: '11px'
            }}>
              {review.source}
            </span>
          )}
        </div>
      </div>

      {/* Reviewer ID (si está disponible) */}
      {review.reviewer_id && (
        <div style={{
          marginTop: '8px',
          padding: '4px 8px',
          backgroundColor: '#f5f5f5',
          borderRadius: '6px',
          fontSize: '11px',
          color: '#666'
        }}>
          Reviewer: {review.reviewer_id}
        </div>
      )}
    </div>
  );
};

export default ReviewCard;