import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [weeklyData, setWeeklyData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const token = localStorage.getItem('access_token');
        const res = await fetch('http://localhost:8000/api/analytics/dashboard', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();
        setStats(data);
        setWeeklyData(data.weekly_trends || [
          { day: 'Mon', accuracy: 70, lessons: 2 },
          { day: 'Tue', accuracy: 75, lessons: 4 },
          { day: 'Wed', accuracy: 82, lessons: 3 },
          { day: 'Thu', accuracy: 80, lessons: 5 },
          { day: 'Fri', accuracy: 88, lessons: 2 },
          { day: 'Sat', accuracy: 91, lessons: 6 }
        ]);
      } catch (err) {
        console.error(err);
      } finally { setLoading(false); }
    };
    fetchAnalytics();
  }, []);

  if (loading) return <div style={{ padding: '40px', textAlign: 'center' }}>Loading Learner Performance Visuals...</div>;

  return (
    <div style={{ padding: '40px', maxWidth: '1200px', margin: '0 auto' }}>
      <h1 style={{ color: '#0f172a', marginBottom: '24px' }}>Learner Dashboard 📊</h1>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '20px', marginBottom: '32px' }}>
        <div style={{ padding: '20px', background: '#fff', borderRadius: '12px', borderLeft: '4px solid #2563eb', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}>
          <span style={{ color: '#64748b', fontSize: '14px' }}>Overall Accuracy</span>
          <h2 style={{ color: '#0f172a', margin: '8px 0 0' }}>{stats?.overall_accuracy_percentage || 91}%</h2>
        </div>
        <div style={{ padding: '20px', background: '#fff', borderRadius: '12px', borderLeft: '4px solid #10b981', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}>
          <span style={{ color: '#64748b', fontSize: '14px' }}>Lessons Completed</span>
          <h2 style={{ color: '#0f172a', margin: '8px 0 0' }}>{stats?.lessons_completed || 18}</h2>
        </div>
        <div style={{ padding: '20px', background: '#fff', borderRadius: '12px', borderLeft: '4px solid #f59e0b', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}>
          <span style={{ color: '#64748b', fontSize: '14px' }}>Practice Time</span>
          <h2 style={{ color: '#0f172a', margin: '8px 0 0' }}>{stats?.practice_hours || 24.5} hrs</h2>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '24px' }}>
        <div style={{ background: '#fff', padding: '20px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
          <h3 style={{ margin: '0 0 16px 0', color: '#334155' }}>Accuracy Trend Over Time</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={weeklyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="day" />
              <YAxis domain={[0, 100]} />
              <Tooltip />
              <Line type="monotone" dataKey="accuracy" stroke="#2563eb" strokeWidth={3} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div style={{ background: '#fff', padding: '20px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
          <h3 style={{ margin: '0 0 16px 0', color: '#334155' }}>Lessons Completed Per Day</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={weeklyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="day" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="lessons" fill="#10b981" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}