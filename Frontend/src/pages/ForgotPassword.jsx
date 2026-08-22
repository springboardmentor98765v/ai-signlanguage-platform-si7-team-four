import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { forgotPassword } from '../services/api';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    setLoading(true);
    try {
      const data = await forgotPassword(email);
      setMessage(data.message || 'If that email is registered, a reset link has been sent.');
    } catch (err) {
      setError(err.message || 'Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="form-card">
      <h2 style={{ fontSize: '1.5rem', fontWeight: '800', marginBottom: '1rem', textAlign: 'center', color: 'var(--text-main)' }}>
        Reset Your Password
      </h2>
      <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', textAlign: 'center', marginBottom: '1.5rem' }}>
        Enter the email linked to your account and we'll send you a reset link.
      </p>

      {message && <div className="alert-success">{message}</div>}
      {error && <div className="alert-error">{error}</div>}

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Email Address</label>
          <input
            type="email"
            required
            className="input-control"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
          />
        </div>
        <button type="submit" disabled={loading} className="btn-primary" style={{ width: '100%', marginTop: '0.5rem', padding: '0.75rem', fontWeight: 700 }}>
          {loading ? 'Sending...' : 'Send Reset Link'}
        </button>
      </form>

      <p style={{ marginTop: '1.25rem', textAlign: 'center', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
        Remembered it?{' '}
        <Link to="/login" style={{ color: 'var(--primary)', fontWeight: '600', textDecoration: 'none' }}>
          Back to login
        </Link>
      </p>
    </div>
  );
}