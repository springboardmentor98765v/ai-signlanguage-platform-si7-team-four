import React, { useState } from 'react';

export default function Profile() {
  const [user] = useState(() => {
    const stored = localStorage.getItem('user');
    return stored ? JSON.parse(stored) : { username: 'Parvathy K Manoj', email: 'parvathy@example.com', role: 'Learner' };
  });

  const [passwords, setPasswords] = useState({ old: '', newPass: '', confirm: '' });
  const [msg, setMsg] = useState('');

  const handlePasswordChange = (e) => {
    e.preventDefault();
    if (passwords.newPass !== passwords.confirm) {
      setMsg('New passwords do not match');
      return;
    }
    setMsg('Password updated successfully!');
    setPasswords({ old: '', newPass: '', confirm: '' });
  };

  return (
    <div style={{ maxWidth: '700px', margin: '0 auto' }}>
      <div className="page-header">
        <p className="page-subtitle">User Settings</p>
        <h1 className="page-title">User Profile</h1>
      </div>

      {/* Account Info Card */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
          Account Information
        </h3>
        
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <div>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Full Name</span>
            <p style={{ fontWeight: 700, fontSize: '1rem', marginTop: '0.2rem' }}>{user.username}</p>
          </div>
          <div>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Email Address</span>
            <p style={{ fontWeight: 600, color: 'var(--text-main)', marginTop: '0.2rem' }}>{user.email}</p>
          </div>
          <div>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Assigned System Role</span>
            <div style={{ marginTop: '0.25rem' }}>
              <span className="badge badge-primary">{user.role}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Security Card */}
      <div className="card">
        <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
          Security & Password
        </h3>

        {msg && (
          <div style={{ padding: '0.75rem', borderRadius: 'var(--radius-md)', backgroundColor: msg.includes('successfully') ? 'var(--success-bg)' : 'var(--danger-bg)', color: msg.includes('successfully') ? 'var(--success)' : 'var(--danger)', fontSize: '0.85rem', fontWeight: 600, marginBottom: '1rem' }}>
            {msg}
          </div>
        )}

        <form onSubmit={handlePasswordChange}>
          <div className="form-group">
            <label>Old Password</label>
            <input
              type="password"
              required
              placeholder="••••••••"
              value={passwords.old}
              onChange={(e) => setPasswords({ ...passwords, old: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label>New Password (Min 6 chars)</label>
            <input
              type="password"
              required
              placeholder="••••••••"
              value={passwords.newPass}
              onChange={(e) => setPasswords({ ...passwords, newPass: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label>Confirm New Password</label>
            <input
              type="password"
              required
              placeholder="••••••••"
              value={passwords.confirm}
              onChange={(e) => setPasswords({ ...passwords, confirm: e.target.value })}
            />
          </div>

          <button type="submit" className="btn-primary" style={{ marginTop: '0.5rem' }}>
            Update Password
          </button>
        </form>
      </div>
    </div>
  );
}