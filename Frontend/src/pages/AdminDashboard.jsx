import React, { useState, useEffect } from 'react';

export default function AdminDashboard() {
  const [users, setUsers] = useState([]);
  const [lessons, setLessons] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch('http://localhost:8000/api/admin/users').then((res) => res.json()),
      fetch('http://localhost:8000/api/admin/lessons').then((res) => res.json()),
    ])
      .then(([userData, lessonData]) => {
        setUsers(userData);
        setLessons(lessonData);
        setLoading(false);
      })
      .catch(() => {
        setUsers([
          { id: 1, name: 'Parvathy Manoj', role: 'Learner', active: true },
          { id: 2, name: 'Instructor John', role: 'Instructor', active: true },
          { id: 3, name: 'Inactive Test User', role: 'Learner', active: false },
        ]);
        setLessons([
          { id: 101, title: 'Alphabet Basics (A-E)', level: 'Beginner', totalLearners: 42 },
          { id: 102, title: 'Numbers (1-10)', level: 'Beginner', totalLearners: 35 },
          { id: 103, title: 'Common Phrases', level: 'Intermediate', totalLearners: 18 },
        ]);
        setLoading(false);
      });
  }, []);

  const toggleStatus = async (id, currentStatus) => {
    try {
      await fetch(`http://localhost:8000/api/admin/users/${id}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ active: !currentStatus }),
      });
    } catch {
      console.log('Toggled status in state');
    }
    setUsers(users.map((u) => (u.id === id ? { ...u, active: !u.active } : u)));
  };

  if (loading) return <div className="p-6 text-center text-gray-500">Loading Admin Dashboard...</div>;

  return (
    <div className="max-w-6xl mx-auto p-4 sm:p-6 space-y-8">
      <h1 className="text-3xl font-bold text-gray-800">Admin Dashboard</h1>

      <div className="bg-white p-6 rounded-xl border shadow-sm space-y-4">
        <h2 className="text-xl font-semibold text-gray-700">User Management</h2>
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-gray-50 border-b text-sm font-semibold text-gray-600">
              <th className="p-3">User</th>
              <th className="p-3">Role</th>
              <th className="p-3">Status</th>
              <th className="p-3">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {users.map((u) => (
              <tr key={u.id}>
                <td className="p-3 font-medium text-gray-800">{u.name}</td>
                <td className="p-3 text-sm text-gray-600">{u.role}</td>
                <td className="p-3">
                  <span className={`px-2 py-1 text-xs font-semibold rounded-full ${u.active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                    {u.active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td className="p-3">
                  <button onClick={() => toggleStatus(u.id, u.active)} className={`px-3 py-1 text-xs font-semibold rounded transition ${u.active ? 'bg-red-50 text-red-600 hover:bg-red-100' : 'bg-green-50 text-green-600 hover:bg-green-100'}`}>
                    {u.active ? 'Deactivate' : 'Activate'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="bg-white p-6 rounded-xl border shadow-sm space-y-4">
        <h2 className="text-xl font-semibold text-gray-700">System Lessons Catalogue</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {lessons.map((l) => (
            <div key={l.id} className="p-4 border rounded-lg bg-gray-50">
              <p className="font-bold text-gray-800">{l.title}</p>
              <p className="text-xs text-indigo-600 font-semibold mt-1">Level: {l.level}</p>
              <p className="text-xs text-gray-500 mt-2">Active Learners: {l.totalLearners}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}