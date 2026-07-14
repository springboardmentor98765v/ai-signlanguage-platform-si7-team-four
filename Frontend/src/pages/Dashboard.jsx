import React, { useState, useEffect } from 'react';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const token = localStorage.getItem('access_token');
        const response = await fetch('http://localhost:8000/api/analytics/dashboard', {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (!response.ok) throw new Error('Failed to retrieve dashboard metric analytics records.');
        const data = await response.json();
        setStats(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  if (loading) return <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>Pulling live platform dataset logs...</div>;
  if (error) return <div style={{ padding: '40px', color: '#ef4444', textAlign: 'center' }}>⚠️ Network Error: {error}</div>;

  return (
    <div style={{ padding: '40px', maxWidth: '1200px', margin: '0 auto' }}>
      <h1 style={{ marginBottom: '20px', color: '#0f172a' }}>Learner Metrics Dashboard 📊</h1>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px', marginTop: '20px' }}>
        <div style={{ padding: '25px', background: '#fff', borderRadius: '12px', boxShadow: '0 4px 6px rgba(0,0,0,0.02)', borderLeft: '5px solid #2563eb' }}>
          <h4 style={{ margin: '0 0 10px 0', color: '#64748b' }}>Overall Accuracy</h4>
          <h2 style={{ color: '#0f172a', margin: 0 }}>{stats?.overall_accuracy_percentage}%</h2>
        </div>
        <div style={{ padding: '25px', background: '#fff', borderRadius: '12px', boxShadow: '0 4px 6px rgba(0,0,0,0.02)', borderLeft: '5px solid #10b981' }}>
          <h4 style={{ margin: '0 0 10px 0', color: '#64748b' }}>Lessons Completed</h4>
          <h2 style={{ color: '#0f172a', margin: 0 }}>{stats?.lessons_completed}</h2>
        </div>
        <div style={{ padding: '25px', background: '#fff', borderRadius: '12px', boxShadow: '0 4px 6px rgba(0,0,0,0.02)', borderLeft: '5px solid #f59e0b' }}>
          <h4 style={{ margin: '0 0 10px 0', color: '#64748b' }}>Practice Time</h4>
          <h2 style={{ color: '#0f172a', margin: 0 }}>{stats?.practice_hours} hrs</h2>
        </div>
      </div>
    </div>
  );
}