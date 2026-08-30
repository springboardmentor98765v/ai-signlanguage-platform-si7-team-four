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

  // Bulletproof error message extractor to prevent [object Object]
  const extractErrorMessage = (err) => {
    if (!err) return 'Registration failed. Please try again.';
    
    // If it's a plain string
    if (typeof err === 'string') return err;

    // Check error message property
    let candidate = err.message || err.detail || err.error;

    if (candidate) {
      if (typeof candidate === 'string') return candidate;
      if (Array.isArray(candidate)) {
        return candidate.map((d) => d.msg || d.message || JSON.stringify(d)).join(', ');
      }
      if (typeof candidate === 'object') {
        // If candidate has a message inside it
        if (candidate.message) return candidate.message;
        if (candidate.detail) {
          return typeof candidate.detail === 'string' ? candidate.detail : JSON.stringify(candidate.detail);
        }
        return JSON.stringify(candidate);
      }
    }

    // Fallback if err.detail is an array directly on err
    if (Array.isArray(err.detail)) {
      return err.detail.map((d) => d.msg || JSON.stringify(d)).join(', ');
    }

    if (typeof err === 'object') {
      try {
        return JSON.stringify(err);
      } catch {
        return 'An unexpected error occurred during registration.';
      }
    }

    return String(err);
  };

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
      const parsedError = extractErrorMessage(err);
      
      // Friendly handling if public backend blocks admin creation
      if (formData.role === 'Administrator' && parsedError.toLowerCase().includes('admin')) {
        setError('Administrator accounts cannot be self-registered publicly. Please use standard administrative credentials or contact system support.');
      } else {
        setError(parsedError);
      }
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