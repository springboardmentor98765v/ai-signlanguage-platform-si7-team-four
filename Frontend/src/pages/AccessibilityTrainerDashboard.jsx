import React, { useState, useEffect } from 'react';
import { getAccessibilityTrainerAnalytics } from '../services/api';

export default function AccessibilityTrainerDashboard() {
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState('');
  const [trainerData, setTrainerData] = useState({
    assignedLearners: 0,
    activeThisWeek: 0,
    avgAccuracy: 0,
    certificationsIssued: 0,
    learners: [],
    skillBreakdown: [],
  });

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      setErrorMsg('');
      try {
        const data = await getAccessibilityTrainerAnalytics();
        setTrainerData({
          assignedLearners: data.assigned_learners ?? data.assignedLearners ?? 0,
          activeThisWeek: data.active_this_week ?? data.activeThisWeek ?? 0,
          avgAccuracy: data.avg_accuracy ?? data.avgAccuracy ?? 0,
          certificationsIssued: data.certifications_issued ?? data.certificationsIssued ?? 0,
          learners: data.learners || [],
          skillBreakdown: data.skill_breakdown || data.skillBreakdown || [],
        });
      } catch (err) {
        setErrorMsg(err.message || 'Unable to load trainer analytics.');
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  const getStatusBadgeStyle = (status) => {
    switch (status) {
      case 'Certified':
        return { backgroundColor: 'var(--success-bg)', color: 'var(--success)', border: '1px solid var(--border-color)' };
      case 'Needs Support':
        return { backgroundColor: 'var(--danger-bg)', color: 'var(--danger)', border: '1px solid var(--border-color)' };
      default:
        return { backgroundColor: 'var(--warning-bg)', color: 'var(--warning)', border: '1px solid var(--border-color)' };
    }
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '1rem 0' }}>
      {/* Top Header */}
      <div className="page-header" style={{ marginBottom: '1.5rem' }}>
        <p className="page-subtitle">Accessibility Track Analytics & Mentorship</p>
        <h1 className="page-title">Accessibility Trainer Dashboard</h1>
        {errorMsg && (
          <span className="badge badge-secondary" style={{ marginTop: '0.5rem', display: 'inline-block' }}>
            ℹ️ {errorMsg}
          </span>
        )}
      </div>

      {/* 4 Summary Stat Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
        <div className="card" style={{ padding: '1.25rem' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            Assigned Learners
          </span>
          <h2 style={{ fontSize: '2.25rem', fontWeight: 800, color: 'var(--primary)', margin: '0.25rem 0' }}>
            {loading ? '...' : trainerData.assignedLearners}
          </h2>
          <small style={{ color: 'var(--text-muted)' }}>Assigned to your cohort</small>
        </div>

        <div className="card" style={{ padding: '1.25rem' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            Active This Week
          </span>
          <h2 style={{ fontSize: '2.25rem', fontWeight: 800, color: 'var(--success)', margin: '0.25rem 0' }}>
            {loading ? '...' : trainerData.activeThisWeek}
          </h2>
          <small style={{ color: 'var(--text-muted)' }}>Engagement rate</small>
        </div>

        <div className="card" style={{ padding: '1.25rem' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            Avg Posture Accuracy
          </span>
          <h2 style={{ fontSize: '2.25rem', fontWeight: 800, color: 'var(--warning)', margin: '0.25rem 0' }}>
            {loading ? '...' : `${trainerData.avgAccuracy}%`}
          </h2>
          <small style={{ color: 'var(--text-muted)' }}>Across all gesture tests</small>
        </div>

        <div className="card" style={{ padding: '1.25rem' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            Certifications Issued
          </span>
          <h2 style={{ fontSize: '2.25rem', fontWeight: 800, color: 'var(--primary-text)', margin: '0.25rem 0' }}>
            {loading ? '...' : trainerData.certificationsIssued}
          </h2>
          <small style={{ color: 'var(--text-muted)' }}>Verified through exams</small>
        </div>
      </div>

      {/* Main Grid: Learner Monitoring Table & Skill Development Breakdown */}
      <div className="grid-2" style={{ gap: '1.5rem', marginBottom: '1.5rem' }}>
        {/* Left: Learner Monitoring Table */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Learner Progress & Certification</h3>
            <span className="badge badge-primary">{trainerData.learners.length} Active Learners</span>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '0.6rem 0.5rem' }}>Learner</th>
                  <th style={{ padding: '0.6rem 0.5rem' }}>Level</th>
                  <th style={{ padding: '0.6rem 0.5rem' }}>Progress</th>
                  <th style={{ padding: '0.6rem 0.5rem' }}>Accuracy</th>
                  <th style={{ padding: '0.6rem 0.5rem' }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {trainerData.learners.map((learner) => (
                  <tr key={learner.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                    <td style={{ padding: '0.75rem 0.5rem', fontWeight: 600 }}>{learner.name}</td>
                    <td style={{ padding: '0.75rem 0.5rem', color: 'var(--text-muted)' }}>{learner.level}</td>
                    <td style={{ padding: '0.75rem 0.5rem' }}>{learner.progress}%</td>
                    <td style={{ padding: '0.75rem 0.5rem', fontWeight: 700, color: 'var(--primary)' }}>{learner.accuracy}%</td>
                    <td style={{ padding: '0.75rem 0.5rem' }}>
                      <span
                        style={{
                          padding: '0.25rem 0.55rem',
                          borderRadius: 'var(--radius-full)',
                          fontSize: '0.725rem',
                          fontWeight: 700,
                          ...getStatusBadgeStyle(learner.status),
                        }}
                      >
                        {learner.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right: Skill Development Breakdown */}
        <div className="card">
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem' }}>
            Skill Development Analytics
          </h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
            Real-time cohort gesture competency across key assessment areas:
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {trainerData.skillBreakdown.map((item, idx) => (
              <div key={idx}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                  <span>{item.skill}</span>
                  <span style={{ color: 'var(--primary)' }}>{item.score}%</span>
                </div>
                <div style={{ width: '100%', height: '8px', backgroundColor: 'var(--table-header-bg)', borderRadius: '999px', overflow: 'hidden' }}>
                  <div
                    style={{
                      width: `${item.score}%`,
                      height: '100%',
                      backgroundColor: item.score > 85 ? 'var(--primary)' : 'var(--warning)',
                      borderRadius: '999px',
                      transition: 'width 0.4s ease',
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}