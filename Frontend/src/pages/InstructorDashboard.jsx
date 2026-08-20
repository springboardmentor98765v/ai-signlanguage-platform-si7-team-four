import React, { useState, useEffect } from 'react';
import { getInstructorStudents, apiRequest } from '../services/api';

export default function InstructorDashboard() {
  const [searchTerm, setSearchTerm] = useState('');
  const [students, setStudents] = useState([]);
  const [lessons, setLessons] = useState([
    { id: 'les_a', title: 'Alphabet Letter A', target: 'A', difficulty: 'Easy' },
    { id: 'les_b', title: 'Alphabet Letter B', target: 'B', difficulty: 'Easy' },
    { id: 'les_c', title: 'Alphabet Letter C', target: 'C', difficulty: 'Easy' },
  ]);
  const [loading, setLoading] = useState(true);
  const [instructorEmail, setInstructorEmail] = useState('');

  useEffect(() => {
    async function loadInstructorData() {
      setLoading(true);
      const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
      const email = currentUser.email || 'instructor@platform.org';
      setInstructorEmail(email);

      try {
        const studentData = await getInstructorStudents(email);
        setStudents(Array.isArray(studentData) ? studentData : []);
      } catch (err) {
        console.warn('Failed to fetch instructor students from backend:', err);
        setStudents([
          { id: 'usr_1', name: 'Alex Johnson', email: 'alex@example.com', accuracy: 88, completedLessons: 12 },
          { id: 'usr_2', name: 'Beatriz Smith', email: 'beatriz@example.com', accuracy: 94, completedLessons: 15 },
          { id: 'usr_3', name: 'Charlie Brown', email: 'charlie@example.com', accuracy: 72, completedLessons: 8 },
        ]);
      } finally {
        setLoading(false);
      }
    }

    loadInstructorData();
  }, []);

  const handleRemoveLesson = async (id) => {
    try {
      await apiRequest(`/api/lessons/${id}`, { method: 'DELETE' });
    } catch (_) {
      // In offline/mock fallback mode
    }
    setLessons((prev) => prev.filter((l) => l.id !== id));
  };

  const filteredStudents = students.filter(
    (s) =>
      s.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.email?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div>
      <div className="page-header">
        <p className="page-subtitle">Classroom Operations & Performance</p>
        <h1 className="page-title">Instructor Dashboard</h1>
      </div>

      {/* Student Register */}
      <div style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
              Student Performance Register
            </h3>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Instructor: {instructorEmail}</span>
          </div>
          <input
            type="text"
            placeholder="Search student..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ maxWidth: '250px' }}
          />
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
            Loading students...
          </div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Student Name</th>
                  <th>Email</th>
                  <th>Accuracy</th>
                  <th>Completed Lessons</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredStudents.map((s, idx) => (
                  <tr key={s.id || idx}>
                    <td style={{ fontWeight: 600 }}>{s.name}</td>
                    <td style={{ color: 'var(--text-muted)' }}>{s.email}</td>
                    <td style={{ color: 'var(--primary)', fontWeight: 700 }}>
                      {typeof s.accuracy === 'number' ? `${s.accuracy}%` : s.accuracy}
                    </td>
                    <td>{s.completedLessons || s.completed || 0}</td>
                    <td>
                      <button className="btn-secondary" style={{ padding: '0.25rem 0.6rem', fontSize: '0.75rem' }}>
                        Details
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Course Management */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
            Manage Course Lessons
          </h3>
          <button className="btn-primary" style={{ padding: '0.4rem 0.85rem', fontSize: '0.8rem' }}>
            + Add New Lesson
          </button>
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
                    <button onClick={() => handleRemoveLesson(l.id)} className="btn-danger-sm">
                      Remove
                    </button>
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