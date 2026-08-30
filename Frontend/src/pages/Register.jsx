import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { registerUser } from '../services/api';

export default function Register() {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    role: 'Learner',
  });
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    setLoading(true);

    try {
      const data = await registerUser(formData);
      setMessage(data.message || 'Account created successfully!');
      // Registration is never auto-login: route the user to the login page.
      setTimeout(() => navigate('/login'), 1500);
    } catch (err) {
      let errMsg = 'Unable to reach the server. Please check your connection and try again.';
      if (typeof err === 'string') {
        errMsg = err;
      } else if (err?.message && typeof err.message === 'string') {
        errMsg = err.message;
      } else if (err?.detail) {
        if (typeof err.detail === 'string') {
          errMsg = err.detail;
        } else if (Array.isArray(err.detail)) {
          errMsg = err.detail.map((d) => d.msg || JSON.stringify(d)).join(', ');
        } else if (typeof err.detail === 'object') {
          errMsg = JSON.stringify(err.detail);
        }
      }
      setError(errMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="form-card">
      <h2 style={{ fontSize: '1.5rem', fontWeight: '800', marginBottom: '1.5rem', textAlign: 'center', color: 'var(--text-main)' }}>
        Create Account
      </h2>

      {message && (
        <div
          className="alert-success"
          style={{
            padding: '0.75rem',
            borderRadius: 'var(--radius-md)',
            backgroundColor: 'var(--success-bg)',
            color: 'var(--success)',
            marginBottom: '1rem',
            fontSize: '0.875rem',
            textAlign: 'center',
          }}
        >
          {message}
        </div>
      )}
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

      <form onSubmit={handleRegister}>
        <div className="form-group">
          <label>Username</label>
          <input
            type="text"
            required
            className="input-control"
            placeholder="Enter username"
            value={formData.username}
            onChange={(e) => setFormData({ ...formData, username: e.target.value })}
          />
        </div>

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
            minLength={8}
            className="input-control"
            placeholder="••••••••"
            value={formData.password}
            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
          />
        </div>

        <div className="form-group">
          <label>System Role</label>
          <select
            className="input-control"
            value={formData.role}
            onChange={(e) => setFormData({ ...formData, role: e.target.value })}
          >
            <option value="Learner">Learner</option>
            <option value="Instructor">Instructor</option>
            <option value="Accessibility Trainer">Accessibility Trainer</option>
            <option value="Administrator">Administrator</option>
          </select>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="btn-primary"
          style={{ width: '100%', marginTop: '0.5rem', padding: '0.75rem' }}
        >
          {loading ? 'Creating Account...' : 'Create Account'}
        </button>
      </form>

      <p style={{ marginTop: '1.25rem', textAlign: 'center', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
        Already registered?{' '}
        <Link to="/login" style={{ color: 'var(--primary)', fontWeight: '600', textDecoration: 'none' }}>
          Login here
        </Link>
      </p>
    </div>
  );
}