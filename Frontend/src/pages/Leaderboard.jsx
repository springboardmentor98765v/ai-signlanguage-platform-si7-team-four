import React, { useState, useEffect } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function Leaderboard() {
  const [sortMetric, setSortMetric] = useState('accuracy'); // 'accuracy' or 'streak'
  const [learners, setLearners] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/analytics/leaderboard?sort=${sortMetric}`)
      .then((res) => res.json())
      .then((data) => {
        setLearners(data);
        setLoading(false);
      })
      .catch(() => {
        setLearners([
          { rank: 1, name: 'Beatriz Smith', accuracy: 96, streak: 14, isUser: false },
          { rank: 2, name: 'Parvathy K Manoj', accuracy: 91, streak: 7, isUser: true },
          { rank: 3, name: 'Alex Johnson', accuracy: 88, streak: 5, isUser: false },
          { rank: 4, name: 'Charlie Brown', accuracy: 78, streak: 3, isUser: false },
          { rank: 5, name: 'David Lee', accuracy: 74, streak: 1, isUser: false },
        ]);
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
    </div>
  );
}