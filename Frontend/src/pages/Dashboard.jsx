import React, { useState, useEffect } from 'react';
import { 
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend 
} from 'recharts';

export default function Dashboard() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [apiError, setApiError] = useState(null);

  useEffect(() => {
    const fetchDashboardMetrics = async () => {
      setLoading(true);
      setApiError(null);

      const token = localStorage.getItem('access_token');
      const headers = {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` })
      };

      try {
        // Attempt Primary API Endpoint
        let res = await fetch('http://localhost:8000/api/assessment/metrics', { headers });

        // Fallback API Endpoint
        if (res.status === 404) {
          res = await fetch('http://localhost:8000/dashboard', { headers });
        }

        if (!res.ok) {
          throw new Error(`HTTP status ${res.status}`);
        }

        const data = await res.json();
        setMetrics(data);
      } catch (err) {
        console.warn('Backend metrics offline, using fallback dashboard data:', err.message);
        setApiError('Connected in offline mode. Displaying practice progress fallback.');
        setMetrics(getFallbackMetrics());
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardMetrics();
  }, []);

  // Fallback data to keep recharts rendering smoothly offline
  const getFallbackMetrics = () => ({
    total_sessions: 12,
    avg_accuracy: 88.5,
    streak_days: 4,
    accuracy_over_time: [
      { date: 'Day 1', accuracy: 65 },
      { date: 'Day 2', accuracy: 72 },
      { date: 'Day 3', accuracy: 80 },
      { date: 'Day 4', accuracy: 84 },
      { date: 'Day 5', accuracy: 88 },
      { date: 'Day 6', accuracy: 92 },
    ],
    completion_by_category: [
      { category: 'Alphabet', completed: 18, total: 26 },
      { category: 'Numbers', completed: 8, total: 10 },
      { category: 'Phrases', completed: 3, total: 15 },
    ]
  });

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>
        <h3>⌛ Loading Dashboard Progress...</h3>
      </div>
    );
  }

  const accuracyData = metrics?.accuracy_over_time || getFallbackMetrics().accuracy_over_time;
  const categoryData = metrics?.completion_by_category || getFallbackMetrics().completion_by_category;

  return (
    <div style={{ padding: '30px', maxWidth: '1100px', margin: '0 auto', fontFamily: 'sans-serif' }}>
      
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ color: '#0f172a', margin: 0 }}>Learner Analytics Dashboard 📊</h1>
        <p style={{ color: '#64748b', margin: '4px 0 0 0' }}>Track your sign language gesture accuracy and milestone progression.</p>
      </div>

      {apiError && (
        <div style={{ background: '#fffbe3', borderLeft: '4px solid #f59e0b', color: '#b45309', padding: '10px 14px', borderRadius: '6px', marginBottom: '20px', fontSize: '13px' }}>
          ⚠️ {apiError}
        </div>
      )}

      {/* KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '30px' }}>
        <div style={{ background: '#fff', padding: '20px', borderRadius: '10px', border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
          <span style={{ fontSize: '13px', color: '#64748b' }}>Total Practice Sessions</span>
          <h2 style={{ color: '#0f172a', margin: '8px 0 0 0', fontSize: '28px' }}>{metrics?.total_sessions || 12}</h2>
        </div>

        <div style={{ background: '#fff', padding: '20px', borderRadius: '10px', border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
          <span style={{ fontSize: '13px', color: '#64748b' }}>Average Accuracy</span>
          <h2 style={{ color: '#16a34a', margin: '8px 0 0 0', fontSize: '28px' }}>{metrics?.avg_accuracy || 88.5}%</h2>
        </div>

        <div style={{ background: '#fff', padding: '20px', borderRadius: '10px', border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
          <span style={{ fontSize: '13px', color: '#64748b' }}>Current Daily Streak</span>
          <h2 style={{ color: '#2563eb', margin: '8px 0 0 0', fontSize: '28px' }}>🔥 {metrics?.streak_days || 4} Days</h2>
        </div>
      </div>

      {/* Recharts Analytics Section */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))', gap: '24px' }}>
        
        {/* Line Chart: Accuracy Trend */}
        <div style={{ background: '#fff', padding: '20px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
          <h3 style={{ margin: '0 0 20px 0', color: '#0f172a', fontSize: '16px' }}>Accuracy Trend Over Time (%)</h3>
          <div style={{ width: '100%', height: 300 }}>
            <ResponsiveContainer>
              <LineChart data={accuracyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="date" stroke="#94a3b8" />
                <YAxis domain={[0, 100]} stroke="#94a3b8" />
                <Tooltip />
                <Line type="monotone" dataKey="accuracy" stroke="#2563eb" strokeWidth={3} dot={{ r: 5 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Bar Chart: Progress by Category */}
        <div style={{ background: '#fff', padding: '20px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
          <h3 style={{ margin: '0 0 20px 0', color: '#0f172a', fontSize: '16px' }}>Curriculum Completion</h3>
          <div style={{ width: '100%', height: 300 }}>
            <ResponsiveContainer>
              <BarChart data={categoryData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="category" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip />
                <Legend />
                <Bar dataKey="completed" fill="#16a34a" name="Completed" radius={[4, 4, 0, 0]} />
                <Bar dataKey="total" fill="#cbd5e1" name="Total Lessons" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>
    </div>
  );
}