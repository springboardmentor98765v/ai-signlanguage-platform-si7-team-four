import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';

export default function Login({ setUser }) {
  const [email, setEmail] = useState('student@example.com');
  const [password, setPassword] = useState('SecurePassword123');
  const [selectedRole, setSelectedRole] = useState('Learner');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:8000/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (response.ok) {
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        if (setUser) setUser(data.user);
        navigate('/dashboard');
      } else {
        setError(data.message || 'Invalid credentials');
      }
    } catch {
      const userData = { username: email.split('@')[0], role: selectedRole, email };
      localStorage.setItem('access_token', 'mock_bearer_token');
      localStorage.setItem('user', JSON.stringify(userData));
      if (setUser) setUser(userData);
      navigate('/dashboard');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="form-card">
      <h2 style={{ fontSize: '1.5rem', fontWeight: '800', marginBottom: '1.5rem', textAlign: 'center', color: 'var(--text-main)' }}>
        Login to Account
      </h2>
      
      {error && <div className="alert-error">{error}</div>}
      
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
          <select value={selectedRole} onChange={(e) => setSelectedRole(e.target.value)}>
            <option value="Learner">Learner</option>
            <option value="Instructor">Instructor</option>
            <option value="Administrator">Administrator</option>
          </select>
        </div>

        <button type="submit" disabled={loading} className="btn-primary" style={{ width: '100%', marginTop: '0.5rem', padding: '0.75rem' }}>
          {loading ? 'Authenticating...' : 'Sign In'}
        </button>
      </form>

      <p style={{ marginTop: '1.25rem', textAlign: 'center', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
        Don't have an account? <Link to="/register" style={{ color: 'var(--primary)', fontWeight: '600', textDecoration: 'none' }}>Register here</Link>
      </p>
    </div>
  );
}