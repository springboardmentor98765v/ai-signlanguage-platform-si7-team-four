import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [captchaChallenge, setCaptchaChallenge] = useState({ num1: 0, num2: 0, result: 0 });
  const [captchaInput, setCaptchaInput] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const generateCaptcha = () => {
    const num1 = Math.floor(Math.random() * 10) + 1;
    const num2 = Math.floor(Math.random() * 10) + 1;
    setCaptchaChallenge({ num1, num2, result: num1 + num2 });
    setCaptchaInput('');
  };

  useEffect(() => {
    generateCaptcha();
  }, []);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');

    // Architectural password rules verification
    const passwordRegex = /^(?=.*[A-Za-z]|\d|[-_!@#$%^&*()_+=\[\]{};':"\\|,.<>\/?]).{8,}$/;
    if (!passwordRegex.test(password)) {
      setError('Security Rule Violation: Password must be at least 8 characters long and feature combinations of letters, digits, or symbols.');
      return;
    }

    if (parseInt(captchaInput, 10) !== captchaChallenge.result) {
      setError('Security Verification Failed: Incorrect CAPTCHA calculation.');
      generateCaptcha();
      return;
    }

    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Invalid email or password credentials.');
      }

      // Secure local application storage payload parsing
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('username', data.user.username);
      localStorage.setItem('user_id', data.user.user_id);
      localStorage.setItem('user_role', data.user.role);
      
      navigate('/dashboard');
      window.location.reload();
    } catch (err) {
      setError(err.message || 'Failed to connect to the authentication server.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '85vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }}>
      <div style={{ width: '100%', maxWidth: '440px', background: '#ffffff', borderRadius: '16px', boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.05)', border: '1px solid #f1f5f9', padding: '40px' }}>
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <h2 style={{ fontSize: '28px', fontWeight: '700', color: '#0f172a', margin: '0 0 8px 0' }}>Welcome Back</h2>
          <p style={{ fontSize: '14px', color: '#64748b', margin: 0 }}>Access your live workspace platform</p>
        </div>

        {error && (
          <div style={{ display: 'flex', gap: '8px', background: '#fef2f2', borderLeft: '4px solid #ef4444', color: '#991b1b', padding: '12px 16px', borderRadius: '6px', marginBottom: '24px', fontSize: '13px' }}>
            <span>⚠️</span> <div>{error}</div>
          </div>
        )}

        <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', color: '#334155', marginBottom: '6px' }}>Email Address</label>
            <input type="email" required disabled={loading} placeholder="student@example.com" style={{ width: '100%', padding: '12px 14px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '14px', outline: 'none', boxSizing: 'border-box' }} value={email} onChange={e => setEmail(e.target.value)} />
          </div>
          
          <div>
            <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', color: '#334155', marginBottom: '6px' }}>Password</label>
            <input type="password" required disabled={loading} placeholder="••••••••" style={{ width: '100%', padding: '12px 14px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '14px', outline: 'none', boxSizing: 'border-box' }} value={password} onChange={e => setPassword(e.target.value)} />
          </div>

          <div style={{ background: '#f8fafc', padding: '16px', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <span style={{ fontSize: '14px', fontWeight: '600', color: '#475569' }}>
                Security Check: What is <span style={{ color: '#2563eb', fontWeight: '700', background: '#e2e8f0', padding: '2px 8px', borderRadius: '4px' }}>{captchaChallenge.num1} + {captchaChallenge.num2}</span> ?
              </span>
              <button type="button" onClick={generateCaptcha} style={{ background: 'none', border: 'none', color: '#2563eb', cursor: 'pointer', fontSize: '12px', fontWeight: '600' }}>🔄 Reload</button>
            </div>
            <input type="number" required placeholder="Enter answer" style={{ width: '100%', padding: '10px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px', outline: 'none', boxSizing: 'border-box' }} value={captchaInput} onChange={e => setCaptchaInput(e.target.value)} />
          </div>
          
          <button type="submit" disabled={loading} style={{ width: '100%', background: loading ? '#94a3b8' : '#2563eb', color: '#ffffff', padding: '14px', border: 'none', borderRadius: '8px', cursor: loading ? 'not-allowed' : 'pointer', fontSize: '14px', fontWeight: '600', marginTop: '8px' }}>
            {loading ? 'Verifying Link...' : 'Sign In to Dashboard'}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: '28px', fontSize: '14px', color: '#64748b' }}>
          New to the platform?{' '}
          <button onClick={() => navigate('/register')} style={{ background: 'none', border: 'none', color: '#2563eb', cursor: 'pointer', fontWeight: '600', padding: 0 }}>Create an account</button>
        </div>
      </div>
    </div>
  );
}