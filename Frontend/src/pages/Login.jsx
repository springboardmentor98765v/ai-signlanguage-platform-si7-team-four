import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { loginUser } from '../services/api';

export default function Login({ setUser }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const routeByUserRole = (role) => {
    const normalizedRole = (role || '').trim().toLowerCase();
    if (normalizedRole === 'administrator' || normalizedRole === 'admin') {
      navigate('/admin');
    } else if (normalizedRole === 'accessibility trainer' || normalizedRole === 'trainer') {
      navigate('/trainer-dashboard');
    } else if (normalizedRole === 'instructor') {
      navigate('/instructor');
    } else {
      navigate('/dashboard');
    }
  };

  const handleLogin = async (e) => {
    if (e) e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const data = await loginUser({ email, password });

      const currentUser = data.user || data;
      if (!data.access_token || !currentUser) {
        throw new Error('Invalid login response from server.');
      }

      localStorage.setItem('access_token', data.access_token);
      if (data.refresh_token) localStorage.setItem('refresh_token', data.refresh_token);
      localStorage.setItem('user_info', JSON.stringify(currentUser));
      localStorage.setItem('user', JSON.stringify(currentUser));
      localStorage.setItem('user_id', currentUser.user_id || currentUser.id || '');
      localStorage.setItem('username', currentUser.username || currentUser.name || '');
      localStorage.setItem('user_role', currentUser.role || '');
      if (setUser) setUser(currentUser);
      routeByUserRole(currentUser.role);
    } catch (err) {
      let errMsg = 'Invalid credentials. Please try again.';
      if (typeof err === 'string') {
        errMsg = err;
      } else if (typeof err?.message === 'string') {
        errMsg = err.message;
      } else if (err?.detail) {
        errMsg = typeof err.detail === 'string' ? err.detail : JSON.stringify(err.detail);
      }
      setError(errMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="form-card">
      <h2 style={{ fontSize: '1.5rem', fontWeight: '800', marginBottom: '1.5rem', textAlign: 'center', color: 'var(--text-main)' }}>
        Login to Account
      </h2>

      {error && (
        <div style={{
          padding: '0.75rem',
          borderRadius: 'var(--radius-md)',
          backgroundColor: 'var(--danger-bg)',
          color: 'var(--danger)',
          fontSize: '0.85rem',
          fontWeight: 600,
          marginBottom: '1rem',
          textAlign: 'center'
        }}>
          {error}
        </div>
      )}

      <form onSubmit={handleLogin}>
        <div className="form-group">
          <label>Email Address</label>
          <input
            type="email"
            required
            className="input-control"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>

        <div className="form-group">
          <label>Password</label>
          <input
            type="password"
            required
            className="input-control"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="btn-primary"
          style={{ width: '100%', marginTop: '0.5rem', padding: '0.75rem', fontWeight: 700 }}
        >
          {loading ? 'Authenticating...' : 'Sign In'}
        </button>
      </form>

      <p style={{ marginTop: '0.75rem', textAlign: 'center', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
        <Link to="/forgot-password" style={{ color: 'var(--primary)', fontWeight: '600', textDecoration: 'none' }}>
          Forgot password?
        </Link>
      </p>

      <p style={{ marginTop: '1.25rem', textAlign: 'center', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
        Don't have an account?{' '}
        <Link to="/register" style={{ color: 'var(--primary)', fontWeight: '600', textDecoration: 'none' }}>
          Register here
        </Link>
      </p>
    </div>
  );
}