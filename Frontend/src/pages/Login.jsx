import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { loginUser } from '../services/api';

export default function Login() {
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const data = await loginUser(formData);
      
      const token = data.access_token || data.token;
      if (!token) {
        throw new Error('Authentication failed: No access token received from server.');
      }

      localStorage.setItem('access_token', token);
      localStorage.setItem('token', token);

      const user = data.user || {
        id: data.user_id || 'usr_default',
        email: formData.email,
        username: formData.email.split('@')[0],
        role: data.role || 'Learner',
      };
      localStorage.setItem('user', JSON.stringify(user));

      // Role-based redirect routing
      const userRole = (user.role || '').toLowerCase();
      if (userRole.includes('admin')) {
        navigate('/admin');
      } else if (userRole.includes('trainer')) {
        navigate('/trainer');
      } else if (userRole.includes('instructor')) {
        navigate('/instructor');
      } else {
        navigate('/dashboard');
      }
    } catch (err) {
      setError(err.message || 'Invalid email or password. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="form-card">
      <h2 style={{ fontSize: '1.5rem', fontWeight: '800', marginBottom: '1.5rem', textAlign: 'center', color: 'var(--text-main)' }}>
        Welcome Back
      </h2>

      {error && (
        <div
          className="alert-error"
          style={{
            padding: '0.75rem',
            borderRadius: 'var(--radius-md)',
            backgroundColor: 'var(--danger-bg)',
            color: 'var(--danger)',
            marginBottom: '1rem',
            fontSize: '0.875rem',
            textAlign: 'center',
          }}
        >
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
            placeholder="name@example.com"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
          />
        </div>

        <div className="form-group">
          <label>Password</label>
          <input
            type="password"
            required
            className="input-control"
            placeholder="••••••••"
            value={formData.password}
            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="btn-primary"
          style={{ width: '100%', marginTop: '0.5rem', padding: '0.75rem' }}
        >
          {loading ? 'Authenticating...' : 'Sign In'}
        </button>
      </form>

      <p style={{ marginTop: '1.25rem', textAlign: 'center', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
        Don't have an account?{' '}
        <Link to="/register" style={{ color: 'var(--primary)', fontWeight: '600', textDecoration: 'none' }}>
          Register here
        </Link>
      </p>
    </div>
  );
}