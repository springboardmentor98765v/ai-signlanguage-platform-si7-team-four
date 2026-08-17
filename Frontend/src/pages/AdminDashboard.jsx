import React, { useState } from 'react';

export default function AdminDashboard() {
  const [users, setUsers] = useState([
    { id: 1, name: 'Parvathy Manoj', role: 'Learner', status: 'Active' },
    { id: 2, name: 'Instructor John', role: 'Instructor', status: 'Active' },
    { id: 3, name: 'Inactive Test User', role: 'Learner', status: 'Inactive' },
  ]);

  const toggleUserStatus = (id) => {
    setUsers(users.map(u => u.id === id ? { ...u, status: u.status === 'Active' ? 'Inactive' : 'Active' } : u));
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
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>User</th>
                <th>Role</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td style={{ fontWeight: 600 }}>{u.name}</td>
                  <td><span className="badge badge-secondary">{u.role}</span></td>
                  <td>
                    <span className={`badge ${u.status === 'Active' ? 'badge-success' : 'badge-warning'}`}>
                      {u.status}
                    </span>
                  </td>
                  <td>
                    <button
                      onClick={() => toggleUserStatus(u.id)}
                      className={u.status === 'Active' ? 'btn-danger-sm' : 'btn-success-sm'}
                    >
                      {u.status === 'Active' ? 'Deactivate' : 'Activate'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
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