import React, { useState, useEffect } from 'react';

export default function InstructorDashboard() {
  const [students, setStudents] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStudents = async () => {
      try {
        const token = localStorage.getItem('access_token');
        const res = await fetch('http://localhost:8000/api/instructor/students', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();
        setStudents(data.students || [
          { user_id: 'usr_1', username: 'alex_dev', email: 'alex@test.com', accuracy: 88, completed: 12 },
          { user_id: 'usr_2', username: 'maria_k', email: 'maria@test.com', accuracy: 94, completed: 18 }
        ]);
      } catch (err) {
        console.error(err);
      } finally { setLoading(false); }
    };
    fetchStudents();
  }, []);

  const filteredStudents = students.filter(s => s.username.toLowerCase().includes(search.toLowerCase()));

  return (
    <div style={{ padding: '40px', maxWidth: '1000px', margin: '0 auto' }}>
      <h1 style={{ color: '#0f172a', marginBottom: '8px' }}>Instructor Dashboard 👩‍🏫</h1>
      <p style={{ color: '#64748b', marginBottom: '24px' }}>Monitor assigned student accuracy performance and completions.</p>

      <input 
        type="text" 
        placeholder="🔍 Search student by name..." 
        value={search} 
        onChange={e => setSearch(e.target.value)} 
        style={{ width: '100%', padding: '12px', borderRadius: '8px', border: '1px solid #cbd5e1', marginBottom: '20px', boxSizing: 'border-box' }}
      />

      <div style={{ background: '#fff', borderRadius: '12px', border: '1px solid #e2e8f0', overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
          <thead style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
            <tr>
              <th style={{ padding: '14px' }}>Student</th>
              <th style={{ padding: '14px' }}>Email</th>
              <th style={{ padding: '14px' }}>Accuracy Rate</th>
              <th style={{ padding: '14px' }}>Completed Lessons</th>
            </tr>
          </thead>
          <tbody>
            {filteredStudents.map(s => (
              <tr key={s.user_id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                <td style={{ padding: '14px', fontWeight: '600' }}>{s.username}</td>
                <td style={{ padding: '14px', color: '#64748b' }}>{s.email}</td>
                <td style={{ padding: '14px', color: '#2563eb', fontWeight: 'bold' }}>{s.accuracy}%</td>
                <td style={{ padding: '14px' }}>{s.completed}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}