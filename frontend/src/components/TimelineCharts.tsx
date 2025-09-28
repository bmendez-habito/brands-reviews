import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar
} from 'recharts';

interface TimelineData {
  date: string;
  total_reviews: number;
  avg_rating: number;
  sentiment_positive: number;
  sentiment_negative: number;
  sentiment_neutral: number;
}

interface TimelineChartsProps {
  data: TimelineData[];
  title: string;
}

const TimelineCharts: React.FC<TimelineChartsProps> = ({ data, title }) => {
  if (!data || data.length === 0) {
    return (
      <div style={{
        background: 'white',
        borderRadius: '12px',
        padding: '24px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        marginBottom: '30px'
      }}>
        <h3 style={{ margin: '0 0 20px 0', color: '#333' }}>
          {title} - Evolución Temporal
        </h3>
        <p style={{ color: '#666', textAlign: 'center', padding: '40px' }}>
          No hay datos suficientes para mostrar la evolución temporal
        </p>
      </div>
    );
  }

  return (
    <div style={{
      background: 'white',
      borderRadius: '12px',
      padding: '24px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
      marginBottom: '30px'
    }}>
      <h3 style={{ margin: '0 0 20px 0', color: '#333' }}>
        {title} - Evolución Temporal
      </h3>

      {/* Gráfico 1: Cantidad de Reviews */}
      <div style={{ marginBottom: '40px' }}>
        <h4 style={{ margin: '0 0 16px 0', color: '#555' }}>Cantidad de Reviews por Día</h4>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="date" 
              tick={{ fontSize: 12 }}
              angle={-45}
              textAnchor="end"
              height={80}
            />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip 
              labelFormatter={(value) => `Fecha: ${value}`}
              formatter={(value: number, name: string) => [
                value, 
                name === 'total_reviews' ? 'Reviews' : name
              ]}
            />
            <Bar 
              dataKey="total_reviews" 
              fill="#1976d2" 
              name="Reviews"
              radius={[2, 2, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Gráfico 2: Rating Promedio */}
      <div style={{ marginBottom: '40px' }}>
        <h4 style={{ margin: '0 0 16px 0', color: '#555' }}>Rating Promedio por Día</h4>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="date" 
              tick={{ fontSize: 12 }}
              angle={-45}
              textAnchor="end"
              height={80}
            />
            <YAxis 
              domain={[0, 5]}
              tick={{ fontSize: 12 }}
            />
            <Tooltip 
              labelFormatter={(value) => `Fecha: ${value}`}
              formatter={(value: number, name: string) => [
                `${value.toFixed(2)} ⭐`, 
                name === 'avg_rating' ? 'Rating Promedio' : name
              ]}
            />
            <Line 
              type="monotone" 
              dataKey="avg_rating" 
              stroke="#4caf50" 
              strokeWidth={3}
              dot={{ fill: '#4caf50', strokeWidth: 2, r: 4 }}
              name="Rating Promedio"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Gráfico 3: Evolución del Sentimiento */}
      <div>
        <h4 style={{ margin: '0 0 16px 0', color: '#555' }}>Evolución del Sentimiento (%)</h4>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="date" 
              tick={{ fontSize: 12 }}
              angle={-45}
              textAnchor="end"
              height={80}
            />
            <YAxis 
              domain={[0, 100]}
              tick={{ fontSize: 12 }}
              label={{ value: '%', angle: 0, position: 'insideLeft' }}
            />
            <Tooltip 
              labelFormatter={(value) => `Fecha: ${value}`}
              formatter={(value: number, name: string) => [
                `${value.toFixed(1)}%`, 
                name === 'sentiment_positive' ? 'Positivo' :
                name === 'sentiment_negative' ? 'Negativo' :
                name === 'sentiment_neutral' ? 'Neutral' : name
              ]}
            />
            <Legend />
            <Area
              type="monotone"
              dataKey="sentiment_positive"
              stackId="1"
              stroke="#4caf50"
              fill="#4caf50"
              fillOpacity={0.6}
              name="Positivo"
            />
            <Area
              type="monotone"
              dataKey="sentiment_neutral"
              stackId="1"
              stroke="#ff9800"
              fill="#ff9800"
              fillOpacity={0.6}
              name="Neutral"
            />
            <Area
              type="monotone"
              dataKey="sentiment_negative"
              stackId="1"
              stroke="#f44336"
              fill="#f44336"
              fillOpacity={0.6}
              name="Negativo"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default TimelineCharts;
