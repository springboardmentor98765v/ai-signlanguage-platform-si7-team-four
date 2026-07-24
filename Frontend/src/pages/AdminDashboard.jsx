import React, { useState, useEffect } from 'react';

export default function AdminDashboard() {
  const [users, setUsers] = useState([]);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch('http://localhost:8000/api/admin/users', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      setUsers(data.users || [
        { user_id: 'usr_1', username: 'srilalitha_dev', role: 'Learner', is_active: true },
        { user_id: 'usr_2', username: 'instructor_john', role: 'Instructor', is_active: true }
      ]);
    } catch (err) { console.error(err); }
  };

  const toggleUserStatus = async (userId, currentStatus) => {
    const token = localStorage.getItem('access_token');
    await fetch(`http://localhost:8000/api/admin/users/${userId}/status`, {
      method: 'PATCH',
      headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_active: !currentStatus })
    });
    setUsers(users.map(u => u.user_id === userId ? { ...u, is_active: !currentStatus } : u));
  };

  return (
    <div style={{ padding: '40px', maxWidth: '1000px', margin: '0 auto' }}>
      <h1 style={{ color: '#0f172a', marginBottom: '8px' }}>Admin Workspace Control ⚙️</h1>
      <p style={{ color: '#64748b', marginBottom: '24px' }}>Platform user access, roles, and course catalogue overview.</p>

      <div style={{ background: '#fff', borderRadius: '12px', border: '1px solid #e2e8f0', overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
          <thead style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
            <tr>
              <th style={{ padding: '14px' }}>User ID</th>
              <th style={{ padding: '14px' }}>Username</th>
              <th style={{ padding: '14px' }}>Role</th>
              <th style={{ padding: '14px' }}>Status</th>
              <th style={{ padding: '14px' }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {users.map(u => (
              <tr key={u.user_id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                <td style={{ padding: '14px', fontSize: '12px', color: '#64748b' }}>{u.user_id}</td>
                <td style={{ padding: '14px', fontWeight: '600' }}>{u.username}</td>
                <td style={{ padding: '14px' }}>{u.role}</td>
                <td style={{ padding: '14px' }}>
                  <span style={{ padding: '4px 8px', borderRadius: '4px', fontSize: '12px', fontWeight: 'bold', background: u.is_active ? '#ecfdf5' : '#fef2f2', color: u.is_active ? '#065f46' : '#991b1b' }}>
                    {u.is_active ? 'Active' : 'Disabled'}
                  </span>
                </td>
                <td style={{ padding: '14px' }}>
                  <button onClick={() => toggleUserStatus(u.user_id, u.is_active)} style={{ padding: '6px 12px', borderRadius: '4px', border: 'none', cursor: 'pointer', background: u.is_active ? '#ef4444' : '#10b981', color: '#fff' }}>
                    {u.is_active ? 'Deactivate' : 'Activate'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}