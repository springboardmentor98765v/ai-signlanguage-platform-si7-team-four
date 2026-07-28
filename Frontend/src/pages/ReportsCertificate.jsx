import React, { useState, useEffect } from 'react';

export default function ReportsCertificate() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/reports/certificate')
      .then((res) => res.json())
      .then((data) => {
        setStats(data);
        setLoading(false);
      })
      .catch(() => {
        setStats({
          completedLessons: 18,
          averageScore: 91,
          weakLetters: ['Z', 'J'],
          learnerName: 'Parvathy K Manoj',
          issueDate: new Date().toLocaleDateString(),
        });
        setLoading(false);
      });
  }, []);

  if (loading) return <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>Loading Certificate...</div>;

  return (
    <div>
      {/* Header & Print Action Button */}
      <div className="page-header print-hidden" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <p className="page-subtitle">Achievements & Analytics</p>
          <h1 className="page-title">Progress Report & Certificate</h1>
        </div>
        <button onClick={() => window.print()} className="btn-primary" style={{ backgroundColor: 'var(--success)' }}>
          Download / Print Certificate
        </button>
      </div>

      {/* Progress Cards */}
      <div className="grid-3 print-hidden" style={{ marginBottom: '2rem' }}>
        <div className="card">
          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Lessons Completed</span>
          <p style={{ fontSize: '1.875rem', fontWeight: 800, color: 'var(--primary)', marginTop: '0.25rem' }}>{stats.completedLessons}</p>
        </div>
        <div className="card">
          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Average Score</span>
          <p style={{ fontSize: '1.875rem', fontWeight: 800, color: 'var(--success)', marginTop: '0.25rem' }}>{stats.averageScore}%</p>
        </div>
        <div className="card">
          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Weak Signs Focus</span>
          <p style={{ fontSize: '1.875rem', fontWeight: 800, color: 'var(--warning)', marginTop: '0.25rem' }}>{stats.weakLetters.join(', ')}</p>
        </div>
      </div>

      {/* Printable Certificate Frame */}
      <div style={{
        backgroundColor: '#fffdf5',
        border: '4px double #fde047',
        borderRadius: 'var(--radius-lg)',
        padding: '3rem 2rem',
        textAlign: 'center',
        boxShadow: 'var(--shadow-md)',
        maxWidth: '800px',
        margin: '0 auto'
      }}>
        <p style={{ fontSize: '0.75rem', uppercase: 'uppercase', letterSpacing: '0.15em', fontWeight: 800, color: '#92400e', marginBottom: '0.5rem' }}>
          CERTIFICATE OF COMPLETION
        </p>
        
        <h2 style={{ fontSize: '2rem', fontFamily: 'Georgia, serif', fontWeight: 'bold', color: 'var(--text-main)', marginBottom: '1rem' }}>
          AI Sign Language Platform
        </h2>

        <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>This certifies that</p>
        
        <p style={{ fontSize: '1.75rem', fontWeight: '800', color: 'var(--primary-text)', borderBottom: '2px solid #fde047', display: 'inline-block', paddingBottom: '0.25rem', marginBottom: '1.25rem' }}>
          {stats.learnerName}
        </p>

        <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', maxWidth: '520px', margin: '0 auto 2rem auto', lineHeight: '1.6' }}>
          has successfully completed the required curriculum and demonstrated proficiency in American Sign Language gesture recognition modules.
        </p>

        <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: '1px solid #fef08a', paddingTop: '1rem', fontSize: '0.8rem', color: 'var(--text-muted)', maxWidth: '520px', margin: '0 auto' }}>
          <span>Date: <strong style={{ color: 'var(--text-main)' }}>{stats.issueDate}</strong></span>
          <span>Verified by: <strong style={{ color: 'var(--text-main)' }}>AI Assessor</strong></span>
        </div>
      </div>
    </div>
  );
}