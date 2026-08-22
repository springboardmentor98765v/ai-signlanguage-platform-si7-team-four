import React, { useState } from 'react';
import { useSearchParams, Link, useNavigate } from 'react-router-dom';
import { resetPassword } from '../services/api';

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || '';
  const navigate = useNavigate();

  const [newPass, setNewPass] = useState('');
  const [confirm, setConfirm] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    if (!token) {
      setError('Missing reset token. Use the link from your reset email.');
      return;
    }
    if (newPass !== confirm) {
      setError('Passwords do not match');
      return;
    }
    if (newPass.length < 8) {
      setError('New password must be at least 8 characters');
      return;
    }
    setLoading(true);
    try {
      const data = await resetPassword(token, newPass);
      setMessage(data.message || 'Password reset successfully.');
      setTimeout(() => navigate('/login'), 1500);
    } catch (err) {
      setError(err.message || 'Reset failed. The link may be invalid or expired.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="form-card">
      <h2 style={{ fontSize: '1.5rem', fontWeight: '800', marginBottom: '1rem', textAlign: 'center', color: 'var(--text-main)' }}>
        Choose a New Password
      </h2>

      {message && <div className="alert-success">{message}</div>}
      {error && <div className="alert-error">{error}</div>}

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>New Password (Min 8 chars)</label>
          <input
            type="password"
            required
            className="input-control"
            value={newPass}
            onChange={(e) => setNewPass(e.target.value)}
          />
        </div>
        <div className="form-group">
          <label>Confirm New Password</label>
          <input
            type="password"
            required
            className="input-control"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
          />
        </div>
        <button type="submit" disabled={loading} className="btn-primary" style={{ width: '100%', marginTop: '0.5rem', padding: '0.75rem', fontWeight: 700 }}>
          {loading ? 'Resetting...' : 'Reset Password'}
        </button>
      </form>

      <p style={{ marginTop: '1.25rem', textAlign: 'center', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
        <Link to="/login" style={{ color: 'var(--primary)', fontWeight: '600', textDecoration: 'none' }}>
          Back to login
        </Link>
      </p>
    </div>
  );
}