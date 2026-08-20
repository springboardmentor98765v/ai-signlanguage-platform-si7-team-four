import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { loginUser } from '../services/api';

export default function Login({ setUser }) {
  const [email, setEmail] = useState('student@example.com');
  const [password, setPassword] = useState('SecurePassword123');
  const [selectedRole, setSelectedRole] = useState('Learner');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const routeByUserRole = (role) => {
    if (role === 'Administrator') {
      navigate('/admin');
    } else if (role === 'Accessibility Trainer') {
      navigate('/trainer-dashboard');
    } else if (role === 'Instructor') {
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

      const token = data.access_token || 'mock_bearer_token';
      const currentUser = data.user || {
        username: email.split('@')[0],
        role: selectedRole,
        email,
      };

      localStorage.setItem('access_token', token);
      localStorage.setItem('user', JSON.stringify(currentUser));
      if (setUser) setUser(currentUser);
      routeByUserRole(currentUser.role || selectedRole);
    } catch (err) {
      setError(err.message || 'Invalid credentials. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // 1-Click Quick Login Preset for Day 4 QA & Demos
  const handleQuickLogin = (role, demoEmail) => {
    setSelectedRole(role);
    setEmail(demoEmail);
    const userData = {
      username: demoEmail.split('@')[0],
      role: role,
      email: demoEmail,
    };
    localStorage.setItem('access_token', 'mock_bearer_token');
    localStorage.setItem('user', JSON.stringify(userData));
    if (setUser) setUser(userData);
    routeByUserRole(role);
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

        <div className="form-group">
          <label>Login As (Testing Role)</label>
          <select
            className="input-control"
            value={selectedRole}
            onChange={(e) => setSelectedRole(e.target.value)}
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
          style={{ width: '100%', marginTop: '0.5rem', padding: '0.75rem', fontWeight: 700 }}
        >
          {loading ? 'Authenticating...' : 'Sign In'}
        </button>
      </form>

      {/* 1-Click Role Testing Preset Grid */}
      <div style={{ marginTop: '1.5rem', borderTop: '1px solid var(--border-color)', paddingTop: '1rem' }}>
        <p style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.5rem', textAlign: 'center' }}>
          ⚡ 1-Click Role Testing Switcher
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.4rem' }}>
          <button
            type="button"
            onClick={() => handleQuickLogin('Learner', 'learner@platform.org')}
            className="btn-secondary"
            style={{ fontSize: '0.75rem', padding: '0.4rem' }}
          >
            👤 Learner
          </button>
          <button
            type="button"
            onClick={() => handleQuickLogin('Instructor', 'instructor@platform.org')}
            className="btn-secondary"
            style={{ fontSize: '0.75rem', padding: '0.4rem' }}
          >
            🧑‍🏫 Instructor
          </button>
          <button
            type="button"
            onClick={() => handleQuickLogin('Accessibility Trainer', 'trainer@platform.org')}
            className="btn-secondary"
            style={{ fontSize: '0.75rem', padding: '0.4rem' }}
          >
            🧏 Trainer
          </button>
          <button
            type="button"
            onClick={() => handleQuickLogin('Administrator', 'admin@platform.org')}
            className="btn-secondary"
            style={{ fontSize: '0.75rem', padding: '0.4rem' }}
          >
            🛡️ Admin
          </button>
        </div>
      </div>

      <p style={{ marginTop: '1.25rem', textAlign: 'center', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
        Don't have an account?{' '}
        <Link to="/register" style={{ color: 'var(--primary)', fontWeight: '600', textDecoration: 'none' }}>
          Register here
        </Link>
      </p>
    </div>
  );
}