import { useState, useEffect } from 'react';
import { apiRequest } from '../services/api';

const BADGES = ['🥇 Gold Signer', '🥈 Silver Signer', '🥉 Bronze Signer'];

const badgeFor = (rank) =>
  BADGES[rank - 1] || (rank <= 10 ? '⭐ Top 10' : '🚀 Rising Star');

export default function Leaderboard() {
  const [entries, setEntries] = useState([]);
  const [sortBy, setSortBy] = useState('accuracy');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;

    async function loadLeaderboard() {
      setLoading(true);
      setError('');
      try {
        // Live class metrics (accuracy/streak) computed from persisted
        // practice records. Refetched on every visit to this page.
        const currentUserId =
          JSON.parse(localStorage.getItem('user_info') || localStorage.getItem('user') || '{}')
            .user_id || localStorage.getItem('user_id') || '';
        const rows = await apiRequest(
          `/api/analytics/leaderboard?sort=${sortBy}&user_id=${encodeURIComponent(currentUserId)}`
        );
        if (cancelled) return;
        setEntries(Array.isArray(rows) ? rows : []);
      } catch (err) {
        if (cancelled) return;
        setError(err.message || 'Could not load the leaderboard.');
        setEntries([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadLeaderboard();
    return () => { cancelled = true; };
  }, [sortBy]);

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <p className="page-subtitle">Global Performance</p>
          <h1 className="page-title">Community Leaderboard</h1>
        </div>
        <select
          className="input-control"
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          style={{ width: '180px' }}
          aria-label="Sort leaderboard by"
        >
          <option value="accuracy">Sort: Accuracy</option>
          <option value="streak">Sort: Streak</option>
        </select>
      </div>

      {loading ? (
        <div className="card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          Loading live rankings...
        </div>
      ) : error ? (
        <div className="card" style={{ padding: '2rem', textAlign: 'center', color: 'var(--danger)', fontWeight: 600 }}>
          {error}
        </div>
      ) : entries.length === 0 ? (
        <div className="card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          No ranked learners yet — complete a practice session to appear here!
        </div>
      ) : (
        <div className="card">
          <table className="table" style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-color)', textAlign: 'left', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                <th style={{ padding: '0.75rem' }}>RANK</th>
                <th style={{ padding: '0.75rem' }}>LEARNER</th>
                <th style={{ padding: '0.75rem' }}>ACCURACY</th>
                <th style={{ padding: '0.75rem' }}>STREAK</th>
                <th style={{ padding: '0.75rem' }}>HONORS</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((item) => (
                <tr
                  key={item.user_id}
                  style={{
                    borderBottom: '1px solid var(--border-color)',
                    backgroundColor: item.is_user ? 'var(--table-header-bg, rgba(99,102,241,0.08))' : 'transparent',
                  }}
                >
                  <td style={{ padding: '0.75rem', fontWeight: 800, color: item.rank <= 3 ? 'var(--primary)' : 'var(--text-main)' }}>
                    #{item.rank}
                  </td>
                  <td style={{ padding: '0.75rem', fontWeight: 700 }}>
                    {item.name}{item.is_user ? ' (you)' : ''}
                  </td>
                  <td style={{ padding: '0.75rem', color: 'var(--success)' }}>{Number(item.accuracy || 0).toFixed(1)}%</td>
                  <td style={{ padding: '0.75rem' }}>🔥 {item.streak || 0}d</td>
                  <td style={{ padding: '0.75rem' }}>
                    <span className="badge badge-primary">{badgeFor(item.rank)}</span>
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
