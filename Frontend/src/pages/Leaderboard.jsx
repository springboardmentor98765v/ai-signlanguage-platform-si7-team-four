import React, { useState } from 'react';

export default function Leaderboard() {
  const [leaderboard] = useState([
    { rank: 1, name: 'Parvathy K Manoj', score: 980, accuracy: 96, streak: 12, badge: '🥇 Gold Signer' },
    { rank: 2, name: 'Aarav Patel', score: 920, accuracy: 92, streak: 9, badge: '🥈 Silver Signer' },
    { rank: 3, name: 'Ananya Sharma', score: 890, accuracy: 89, streak: 7, badge: '🥉 Bronze Signer' },
    { rank: 4, name: 'Rohan Gupta', score: 850, accuracy: 86, streak: 5, badge: '⭐ Fast Learner' },
    { rank: 5, name: 'Meera Nair', score: 790, accuracy: 82, streak: 4, badge: '🚀 Rising Star' },
  ]);

  return (
    <div>
      <div className="page-header">
        <p className="page-subtitle">Global Performance</p>
        <h1 className="page-title">Community Leaderboard</h1>
      </div>

      <div className="card">
        <table className="table" style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border-color)', textAlign: 'left', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
              <th style={{ padding: '0.75rem' }}>RANK</th>
              <th style={{ padding: '0.75rem' }}>LEARNER</th>
              <th style={{ padding: '0.75rem' }}>ACCURACY</th>
              <th style={{ padding: '0.75rem' }}>TOTAL XP</th>
              <th style={{ padding: '0.75rem' }}>STREAK</th>
              <th style={{ padding: '0.75rem' }}>HONORS</th>
            </tr>
          </thead>
          <tbody>
            {leaderboard.map((item) => (
              <tr key={item.rank} style={{ borderBottom: '1px solid var(--border-color)' }}>
                <td style={{ padding: '0.75rem', fontWeight: 800, color: item.rank <= 3 ? 'var(--primary)' : 'var(--text-main)' }}>
                  #{item.rank}
                </td>
                <td style={{ padding: '0.75rem', fontWeight: 700 }}>{item.name}</td>
                <td style={{ padding: '0.75rem', color: 'var(--success)' }}>{item.accuracy}%</td>
                <td style={{ padding: '0.75rem', fontWeight: 700 }}>{item.score} XP</td>
                <td style={{ padding: '0.75rem' }}>🔥 {item.streak}d</td>
                <td style={{ padding: '0.75rem' }}>
                  <span className="badge badge-primary">{item.badge}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}