import React, { useState } from 'react';

export default function InstructorDashboard() {
  const [searchTerm, setSearchTerm] = useState('');
  const [lessons, setLessons] = useState([
    { id: 'les_a', title: 'Alphabet Letter A', target: 'A', difficulty: 'Easy' },
    { id: 'les_b', title: 'Alphabet Letter B', target: 'B', difficulty: 'Easy' },
    { id: 'les_c', title: 'Alphabet Letter C', target: 'C', difficulty: 'Easy' },
  ]);

  const students = [
    { name: 'Alex Johnson', email: 'alex@example.com', accuracy: '88%', completed: 12 },
    { name: 'Beatriz Smith', email: 'beatriz@example.com', accuracy: '94%', completed: 15 },
    { name: 'Charlie Brown', email: 'charlie@example.com', accuracy: '72%', completed: 8 },
  ];

  const handleRemoveLesson = (id) => {
    setLessons(lessons.filter(l => l.id !== id));
  };

  const filteredStudents = students.filter(s => s.name.toLowerCase().includes(searchTerm.toLowerCase()));

  return (
    <div>
      <div className="page-header">
        <p className="page-subtitle">Classroom Operations</p>
        <h1 className="page-title">Instructor Dashboard</h1>
      </div>

      {/* Student Register */}
      <div style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '1rem' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-main)' }}>Student Performance Register</h3>
          <input
            type="text"
            placeholder="Search student..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ maxWidth: '250px' }}
          />
        </div>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Student Name</th>
                <th>Email</th>
                <th>Accuracy</th>
                <th>Completed</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredStudents.map((s, idx) => (
                <tr key={idx}>
                  <td style={{ fontWeight: 600 }}>{s.name}</td>
                  <td style={{ color: 'var(--text-muted)' }}>{s.email}</td>
                  <td style={{ color: 'var(--primary)', fontWeight: 700 }}>{s.accuracy}</td>
                  <td>{s.completed}</td>
                  <td>
                    <button className="btn-secondary" style={{ padding: '0.25rem 0.6rem', fontSize: '0.75rem' }}>Details</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Course Management */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-main)' }}>Manage Course Lessons</h3>
          <button className="btn-primary" style={{ padding: '0.4rem 0.85rem', fontSize: '0.8rem' }}>+ Add New Lesson</button>
        </div>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Lesson Title</th>
                <th>Expected Sign</th>
                <th>Difficulty</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {lessons.map((l) => (
                <tr key={l.id}>
                  <td style={{ fontWeight: 600 }}>{l.title}</td>
                  <td><span className="badge badge-primary">{l.target}</span></td>
                  <td><span className="badge badge-success">{l.difficulty}</span></td>
                  <td>
                    <button onClick={() => handleRemoveLesson(l.id)} className="btn-danger-sm">Remove</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}