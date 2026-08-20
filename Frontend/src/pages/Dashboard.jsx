import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { getDashboardAnalytics, getRecommendations } from '../services/api';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [accuracyData, setAccuracyData] = useState([]);
  const [lessonsData, setLessonsData] = useState([]);
  const [badges, setBadges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const userId = localStorage.getItem('user_id');
    if (!userId) {
      setError('No learner session found. Please sign in again.');
      setLoading(false);
      return;
    }

    Promise.all([getDashboardAnalytics(userId), getRecommendations(userId)])
      .then(([dashData, recData]) => {
        setStats(dashData);
        setRecommendations(recData.recommended_lessons || dashData.recommended_lessons || []);
        setAccuracyData(
          (dashData.accuracy_over_time || []).map((p) => ({ day: p.day, accuracy: p.accuracy }))
        );
        setLessonsData(
          (dashData.completion_by_category || []).map((c) => ({ week: c.category, count: c.completed }))
        );

        const streak = dashData.current_streak || 0;
        const lessons = dashData.lessons_completed || 0;
        const accuracy = dashData.overall_accuracy_percentage || 0;
        setBadges([
          { id: 1, title: '🔥 7-Day Streak', desc: 'Practiced 7 days in a row', unlocked: streak >= 7 },
          { id: 2, title: '🔤 Alphabet Master', desc: 'Scored >80% on all letters A-Z', unlocked: lessons >= 26 },
          { id: 3, title: '🎯 Sharp Shooter', desc: 'Reached 95% single-gesture confidence', unlocked: accuracy >= 95 },
          { id: 4, title: '⚡ Speed Learner', desc: 'Completed 5 lessons in 1 day', unlocked: lessons >= 5 },
          { id: 5, title: '🏆 Top 3 Ranking', desc: 'Ranked in top 3 on class leaderboard', unlocked: false },
        ]);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to load dashboard data.');
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>Loading Learner Dashboard...</div>;
  }

  if (!stats) {
    return (
      <div className="card" style={{ padding: '2rem', textAlign: 'center' }}>
        <p style={{ color: 'var(--danger)', fontWeight: 600 }}>{error || 'Unable to load dashboard.'}</p>
      </div>
    );
  }

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <p className="page-subtitle">Welcome Back</p>
          <h1 className="page-title">Learner Overview</h1>
        </div>
        <div className="streak-pill card-pop">
          🔥 <strong>{stats?.current_streak || 0} Day Practice Streak!</strong>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid-4" style={{ marginBottom: '1.5rem' }}>
        <div className="card">
          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Overall Accuracy</span>
          <p style={{ fontSize: '1.875rem', fontWeight: 800, color: 'var(--primary)', marginTop: '0.25rem' }}>{stats.overall_accuracy_percentage}%</p>
        </div>
        <div className="card">
          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Lessons Completed</span>
          <p style={{ fontSize: '1.875rem', fontWeight: 800, color: 'var(--success)', marginTop: '0.25rem' }}>{stats.lessons_completed}</p>
        </div>
        <div className="card">
          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Practice Hours</span>
          <p style={{ fontSize: '1.875rem', fontWeight: 800, color: 'var(--warning)', marginTop: '0.25rem' }}>{stats.practice_hours} hrs</p>
        </div>
        <div className="card">
          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Improvement Rate</span>
          <p style={{ fontSize: '1.875rem', fontWeight: 800, color: '#10b981', marginTop: '0.25rem' }}>+{stats.improvement_rate_percentage}%</p>
        </div>
      </div>

      {/* Achievements & Badges Grid */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ fontSize: '1.125rem', fontWeight: 700, marginBottom: '1rem', color: 'var(--text-main)' }}>
          Achievement Badges
        </h3>
        <div className="grid-3">
          {badges.map((b) => (
            <div key={b.id} className={`badge-card ${b.unlocked ? 'unlocked card-pop' : 'locked'}`}>
              <div style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.25rem' }}>{b.title}</div>
              <div style={{ fontSize: '0.8rem', color: b.unlocked ? '#1e1b4b' : 'var(--text-light)' }}>{b.desc}</div>
              <span className={`badge ${b.unlocked ? 'badge-success' : 'badge-secondary'}`} style={{ marginTop: '0.5rem' }}>
                {b.unlocked ? 'Unlocked' : 'Locked'}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Analytics Charts */}
      <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
        <div className="card">
          <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem', color: 'var(--text-main)' }}>Accuracy Progress</h3>
          <div style={{ height: '220px', width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={accuracyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="day" stroke="#94a3b8" fontSize={12} />
                <YAxis domain={[0, 100]} stroke="#94a3b8" fontSize={12} />
                <Tooltip />
                <Line type="monotone" dataKey="accuracy" stroke="#4f46e5" strokeWidth={3} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card">
          <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem', color: 'var(--text-main)' }}>Weekly Lesson Completion</h3>
          <div style={{ height: '220px', width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={lessonsData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="week" stroke="#94a3b8" fontSize={12} />
                <YAxis stroke="#94a3b8" fontSize={12} />
                <Tooltip />
                <Bar dataKey="count" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Practice Recommendations */}
      <div className="card">
        <h3 style={{ fontSize: '1.125rem', fontWeight: 700, marginBottom: '1rem' }}>Personalized Practice Recommendations</h3>
        <div className="grid-2">
          {recommendations.map((item) => (
            <div key={item.lesson_id} style={{ padding: '1rem', backgroundColor: 'var(--warning-bg)', borderRadius: 'var(--radius-md)', border: '1px solid #fde68a' }}>
              <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#92400e' }}>{item.title}</h4>
              <p style={{ fontSize: '0.85rem', color: '#b45309', marginTop: '0.25rem' }}>{item.reason}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}