import React, { useState, useEffect } from 'react';

export default function Profile() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [role, setRole] = useState('');
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setUsername(localStorage.getItem('username') || 'srilalitha_dev');
    setEmail(localStorage.getItem('user_email') || 'student@example.com');
    setRole(localStorage.getItem('user_role') || 'Learner');
  }, []);

  const handleProfileUpdate = async (e) => {
    e.preventDefault();
    setMessage(''); setError(''); setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch('http://localhost:8000/api/user/profile', {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email })
      });
      if (!res.ok) throw new Error('Profile update failed.');
      localStorage.setItem('username', username);
      setMessage('Profile updated successfully!');
    } catch (err) {
      setError(err.message);
    } finally { setLoading(false); }
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    setMessage(''); setError('');
    if (newPassword.length < 6) {
      setError('New password must be at least 6 characters long.');
      return;
    }
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch('http://localhost:8000/api/user/change-password', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ old_password: oldPassword, new_password: newPassword })
      });
      if (!res.ok) throw new Error('Password change failed. Check your old password.');
      setMessage('Password updated successfully!');
      setOldPassword(''); setNewPassword('');
    } catch (err) {
      setError(err.message);
    } finally { setLoading(false); }
  };

  return (
    <div style={{ padding: '40px', maxWidth: '600px', margin: '0 auto' }}>
      <h2 style={{ color: '#0f172a', marginBottom: '20px' }}>User Account & Profile</h2>
      {message && <div style={{ background: '#ecfdf5', color: '#065f46', padding: '12px', borderRadius: '6px', marginBottom: '15px' }}>{message}</div>}
      {error && <div style={{ background: '#fef2f2', color: '#991b1b', padding: '12px', borderRadius: '6px', marginBottom: '15px' }}>{error}</div>}

      <form onSubmit={handleProfileUpdate} style={{ background: '#fff', padding: '24px', borderRadius: '12px', border: '1px solid #e2e8f0', marginBottom: '24px' }}>
        <h3 style={{ margin: '0 0 16px 0', color: '#334155' }}>Profile Info</h3>
        <label style={{ display: 'block', margin: '10px 0 4px', fontSize: '14px', fontWeight: '600' }}>Username</label>
        <input type="text" value={username} onChange={e => setUsername(e.target.value)} required style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid #cbd5e1' }} />
        <label style={{ display: 'block', margin: '10px 0 4px', fontSize: '14px', fontWeight: '600' }}>Email</label>
        <input type="email" value={email} onChange={e => setEmail(e.target.value)} required style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid #cbd5e1' }} />
        <label style={{ display: 'block', margin: '10px 0 4px', fontSize: '14px', fontWeight: '600' }}>Assigned System Role</label>
        <input type="text" value={role} disabled style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid #cbd5e1', background: '#f1f5f9' }} />
        <button type="submit" disabled={loading} style={{ marginTop: '16px', background: '#2563eb', color: '#fff', border: 'none', padding: '10px 16px', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}>
          Save Profile
        </button>
      </form>

      <form onSubmit={handlePasswordChange} style={{ background: '#fff', padding: '24px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
        <h3 style={{ margin: '0 0 16px 0', color: '#334155' }}>Security Settings</h3>
        <label style={{ display: 'block', margin: '10px 0 4px', fontSize: '14px', fontWeight: '600' }}>Old Password</label>
        <input type="password" value={oldPassword} onChange={e => setOldPassword(e.target.value)} required style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid #cbd5e1' }} />
        <label style={{ display: 'block', margin: '10px 0 4px', fontSize: '14px', fontWeight: '600' }}>New Password</label>
        <input type="password" value={newPassword} onChange={e => setNewPassword(e.target.value)} required style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid #cbd5e1' }} />
        <button type="submit" disabled={loading} style={{ marginTop: '16px', background: '#10b981', color: '#fff', border: 'none', padding: '10px 16px', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}>
          Update Password
        </button>
      </form>
    </div>
  );
}