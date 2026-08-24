import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiRequest } from '../services/api';

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const user = JSON.parse(localStorage.getItem('user_info') || localStorage.getItem('user') || '{}');

  useEffect(() => {
    async function loadDashboard() {
      try {
        // Live per-learner metrics computed from persisted practice records.
        const res = await apiRequest('/api/auth/dashboard/learner');
        setData(res);
      } catch (err) {
        console.warn('Dashboard load failed:', err);
        setError('Could not load your dashboard. Please try refreshing.');
        setData(null);
      } finally {
        setLoading(false);
      }
    }
    loadDashboard();
  }, [user.username]);

  if (loading) {
    return <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>Loading Dashboard...</div>;
  }

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <p className="page-subtitle">Welcome back, {user.username || 'Learner'}!</p>
          <h1 className="page-title">Learner Overview</h1>
        </div>
        <button onClick={() => navigate('/practice')} className="btn-primary" style={{ padding: '0.6rem 1.25rem' }}>
          🚀 Resume Practice
        </button>
      </div>

      {error && <div className="alert-error" style={{ marginBottom: '1rem', padding: '0.75rem' }}>{error}</div>}

      <div className="grid-3" style={{ marginBottom: '2rem' }}>
        <div className="card">
          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Overall Accuracy</span>
          <p style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--primary)', marginTop: '0.25rem' }}>
            {data?.accuracy_average ?? 0}%
          </p>
        </div>
        <div className="card">
          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Lessons Completed</span>
          <p style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--success, #10b981)', marginTop: '0.25rem' }}>
            {data?.completed_lessons ?? 0}
          </p>
        </div>
        <div className="card">
          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Daily Streak</span>
          <p style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--warning, #f59e0b)', marginTop: '0.25rem' }}>
            🔥 {data?.current_streak_days ?? 0} Days
          </p>
        </div>
      </div>

      <div className="card">
        <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem' }}>Recent Practice Sessions</h3>
        <table className="table" style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border-color)', textAlign: 'left', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
              <th style={{ padding: '0.75rem' }}>SIGN / GESTURE</th>
              <th style={{ padding: '0.75rem' }}>SCORE</th>
              <th style={{ padding: '0.75rem' }}>DATE</th>
              <th style={{ padding: '0.75rem', textAlign: 'right' }}>ACTION</th>
            </tr>
          </thead>
          <tbody>
            {(data?.recent_activities || []).length === 0 ? (
              <tr>
                <td colSpan={4} style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                  No practice attempts yet — head to Practice to start your first sign!
                </td>
              </tr>
            ) : (
              data.recent_activities.map((act) => (
                <tr key={act.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                  <td style={{ padding: '0.75rem', fontWeight: 700 }}>Sign '{act.sign}'</td>
                  <td style={{ padding: '0.75rem', color: act.score >= 85 ? 'var(--success)' : 'var(--warning)' }}>{act.score}%</td>
                  <td style={{ padding: '0.75rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>{act.date}</td>
                  <td style={{ padding: '0.75rem', textAlign: 'right' }}>
                    <button onClick={() => navigate('/practice')} className="btn-secondary" style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}>
                      Retry
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}