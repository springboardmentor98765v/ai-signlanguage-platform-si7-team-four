import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function Register() {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [role, setRole] = useState('Learner');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');

    const passwordRegex = /^(?=.*[A-Za-z]|\d|[-_!@#$%^&*()_+=\[\]{};':"\\|,.<>\/?]).{8,}$/;
    if (!passwordRegex.test(password)) {
      setError('Validation Error: Password must be 8+ characters long and include combinations of letters, digits, or symbols.');
      return;
    }

    if (password !== confirmPassword) {
      setError('Validation Error: Second validation confirmation password mismatch.');
      return;
    }

    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password, role })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Registration request processing failure.');
      }

      alert('Workspace registration successful!');
      navigate('/');
    } catch (err) {
      setError(err.message || 'Failed to connect to the registration server.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '90vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }}>
      <div style={{ width: '100%', maxWidth: '480px', background: '#ffffff', borderRadius: '16px', boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.05)', border: '1px solid #f1f5f9', padding: '40px' }}>
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <h2 style={{ fontSize: '28px', fontWeight: '700', color: '#0f172a', margin: '0 0 6px 0' }}>Get Started</h2>
          <p style={{ fontSize: '14px', color: '#64748b', margin: 0 }}>Register your workspace access profile</p>
        </div>

        {error && (
          <div style={{ display: 'flex', gap: '8px', background: '#fef2f2', borderLeft: '4px solid #ef4444', color: '#991b1b', padding: '12px 16px', borderRadius: '6px', marginBottom: '20px', fontSize: '13px' }}>
            <span>⚠️</span> <div>{error}</div>
          </div>
        )}

        <form onSubmit={handleRegister} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', color: '#334155', marginBottom: '6px' }}>Username</label>
            <input type="text" required disabled={loading} placeholder="srilalitha_dev" style={{ width: '100%', padding: '12px 14px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '14px', outline: 'none', boxSizing: 'border-box' }} value={username} onChange={e => setUsername(e.target.value)} />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', color: '#334155', marginBottom: '6px' }}>Email Address</label>
            <input type="email" required disabled={loading} placeholder="student@example.com" style={{ width: '100%', padding: '12px 14px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '14px', outline: 'none', boxSizing: 'border-box' }} value={email} onChange={e => setEmail(e.target.value)} />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', color: '#334155', marginBottom: '6px' }}>Platform Access Role</label>
            <select value={role} disabled={loading} onChange={e => setRole(e.target.value)} style={{ width: '100%', padding: '12px 14px', borderRadius: '8px', border: '1px solid #cbd5e1', background: '#ffffff', fontSize: '14px', outline: 'none', cursor: 'pointer', boxSizing: 'border-box' }}>
              <option value="Learner">Learner</option>
              <option value="Instructor">Instructor</option>
              <option value="Accessibility Trainer">Accessibility Trainer</option>
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', color: '#334155', marginBottom: '6px' }}>Password</label>
            <input type="password" required disabled={loading} placeholder="Minimum 8 characters" style={{ width: '100%', padding: '12px 14px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '14px', outline: 'none', boxSizing: 'border-box' }} value={password} onChange={e => setPassword(e.target.value)} />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', color: '#334155', marginBottom: '6px' }}>Confirm Password</label>
            <input type="password" required disabled={loading} placeholder="••••••••" style={{ width: '100%', padding: '12px 14px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '14px', outline: 'none', boxSizing: 'border-box' }} value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} />
          </div>

          <button type="submit" disabled={loading} style={{ width: '100%', background: loading ? '#94a3b8' : '#10b981', color: '#ffffff', padding: '14px', border: 'none', borderRadius: '8px', cursor: loading ? 'not-allowed' : 'pointer', fontSize: '14px', fontWeight: '600', marginTop: '10px' }}>
            {loading ? 'Sending Data...' : 'Register Workspace Profile'}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: '24px', fontSize: '14px', color: '#64748b' }}>
          Already possess credentials?{' '}
          <button onClick={() => navigate('/')} style={{ background: 'none', border: 'none', color: '#2563eb', cursor: 'pointer', fontWeight: '600', padding: 0 }}>Sign in instead</button>
        </div>
      </div>
    </div>
  );
}