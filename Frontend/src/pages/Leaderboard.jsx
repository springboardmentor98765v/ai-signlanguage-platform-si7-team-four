import React, { useState, useEffect } from 'react';
import { apiRequest } from '../services/api';

export default function Leaderboard() {
  const [sortMetric, setSortMetric] = useState('accuracy'); // 'accuracy' or 'streak'
  const [learners, setLearners] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const userId = localStorage.getItem('user_id');
    apiRequest(`/api/analytics/leaderboard?sort=${sortMetric}${userId ? `&user_id=${encodeURIComponent(userId)}` : ''}`, { method: 'GET' })
      .then((data) => {
        const rows = Array.isArray(data) ? data : data.leaderboard || [];
        setLearners(rows.map((r) => ({
          rank: r.rank,
          name: r.name,
          accuracy: r.accuracy,
          streak: r.streak,
          isUser: Boolean(r.is_user),
        })));
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to load leaderboard.');
        setLoading(false);
      });
  }, [sortMetric]);

  const sorted = [...learners].sort((a, b) => b[sortMetric] - a[sortMetric]);

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <p className="page-subtitle">Classroom Friendly Ranking</p>
          <h1 className="page-title">Learner Leaderboard</h1>
        </div>

        {/* Sorting Toggles */}
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            onClick={() => setSortMetric('accuracy')}
            className={sortMetric === 'accuracy' ? 'btn-primary' : 'btn-secondary'}
          >
            Sort by Accuracy %
          </button>
          <button
            onClick={() => setSortMetric('streak')}
            className={sortMetric === 'streak' ? 'btn-primary' : 'btn-secondary'}
          >
            Sort by Streak 🔥
          </button>
        </div>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
          Loading leaderboard...
        </div>
      ) : (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Rank</th>
                <th>Learner Name</th>
                <th>Overall Accuracy</th>
                <th>Practice Streak</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((item, idx) => (
                <tr key={idx} style={item.isUser ? { backgroundColor: 'var(--primary-light)', fontWeight: 'bold' } : {}}>
                  <td style={{ fontSize: '1rem' }}>
                    {idx === 0 ? '🥇 1' : idx === 1 ? '🥈 2' : idx === 2 ? '🥉 3' : `#${idx + 1}`}
                  </td>
                  <td>{item.name} {item.isUser && '(You)'}</td>
                  <td style={{ color: 'var(--primary)', fontWeight: 700 }}>{item.accuracy}%</td>
                  <td>🔥 {item.streak} days</td>
                  <td>
                    <span className={`badge ${item.isUser ? 'badge-primary' : 'badge-secondary'}`}>
                      {item.isUser ? 'Your Rank' : 'Learner'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}