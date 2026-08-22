import React, { useState, useEffect } from 'react';
import { getAllUsers, toggleUserStatus } from '../services/api';

export default function AdminDashboard() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    async function loadAdminUsers() {
      setLoading(true);
      setError('');
      try {
        const data = await getAllUsers();
        const formatted = (Array.isArray(data) ? data : []).map((u) => ({
          id: u.id || u.user_id,
          name: u.name || u.username || 'User',
          email: u.email,
          role: u.role || 'Learner',
          active: typeof u.active === 'boolean' ? u.active : u.status === 'Active',
        }));
        setUsers(formatted);
      } catch (err) {
        setError(err.message || 'Failed to load admin users.');
      } finally {
        setLoading(false);
      }
    }

    loadAdminUsers();
  }, []);

  const handleToggleStatus = async (user) => {
    setActionLoading(user.id);
    try {
      await toggleUserStatus(user.id, user.active);
      setUsers((prev) =>
        prev.map((u) => (u.id === user.id ? { ...u, active: !u.active } : u))
      );
    } catch (err) {
      setError(err.message || 'Failed to update user status.');
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div>
      <div className="page-header">
        <p className="page-subtitle">Platform Governance</p>
        <h1 className="page-title">Admin Dashboard</h1>
      </div>

      {/* User Management Section */}
      <div style={{ marginBottom: '2rem' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem', color: 'var(--text-main)' }}>
          User Account Management
        </h3>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
            Loading platform accounts...
          </div>
        ) : error ? (
          <div className="card" style={{ padding: '2rem', textAlign: 'center', color: 'var(--danger)', fontWeight: 600 }}>
            {error}
          </div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>User</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id}>
                    <td style={{ fontWeight: 600 }}>{u.name}</td>
                    <td style={{ color: 'var(--text-muted)' }}>{u.email}</td>
                    <td><span className="badge badge-secondary">{u.role}</span></td>
                    <td>
                      <span className={`badge ${u.active ? 'badge-success' : 'badge-warning'}`}>
                        {u.active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td>
                      <button
                        onClick={() => handleToggleStatus(u)}
                        disabled={actionLoading === u.id}
                        className={u.active ? 'btn-danger-sm' : 'btn-success-sm'}
                      >
                        {actionLoading === u.id
                          ? 'Updating...'
                          : u.active
                          ? 'Deactivate'
                          : 'Activate'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* System Lessons Catalogue */}
      <div>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem', color: 'var(--text-main)' }}>
          System Lessons Catalogue
        </h3>
        <div className="grid-3">
          <div className="card">
            <span className="badge badge-primary" style={{ marginBottom: '0.5rem' }}>Beginner</span>
            <h4 style={{ fontSize: '1rem', fontWeight: 700 }}>Alphabet Basics (A-E)</h4>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Active Learners: 42</p>
          </div>
          <div className="card">
            <span className="badge badge-primary" style={{ marginBottom: '0.5rem' }}>Beginner</span>
            <h4 style={{ fontSize: '1rem', fontWeight: 700 }}>Numbers (1-10)</h4>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Active Learners: 35</p>
          </div>
          <div className="card">
            <span className="badge badge-primary" style={{ marginBottom: '0.5rem' }}>Intermediate</span>
            <h4 style={{ fontSize: '1rem', fontWeight: 700 }}>Common Phrases</h4>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Active Learners: 18</p>
          </div>
        </div>
      </div>
    </div>
  );
}