import React, { useState, useEffect } from 'react';

export default function InstructorDashboard() {
  const [searchTerm, setSearchTerm] = useState('');
  const [students, setStudents] = useState([]);
  const [lessons, setLessons] = useState([]);
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [showAddLessonModal, setShowAddLessonModal] = useState(false);
  const [newLesson, setNewLesson] = useState({ title: '', description: '', expected_gesture: 'A', difficulty: 'Easy' });

  useEffect(() => {
    // Initial data load
    setStudents([
      { id: 1, name: 'Alex Johnson', email: 'alex@example.com', accuracy: 88, completedLessons: 12, weakLetters: ['Z', 'J'] },
      { id: 2, name: 'Beatriz Smith', email: 'beatriz@example.com', accuracy: 94, completedLessons: 15, weakLetters: ['Q'] },
      { id: 3, name: 'Charlie Brown', email: 'charlie@example.com', accuracy: 72, completedLessons: 8, weakLetters: ['X', 'R'] },
    ]);

    setLessons([
      { id: 101, title: 'Alphabet Letter A', expected_gesture: 'A', difficulty: 'Easy' },
      { id: 102, title: 'Alphabet Letter B', expected_gesture: 'B', difficulty: 'Easy' },
      { id: 103, title: 'Alphabet Letter C', expected_gesture: 'C', difficulty: 'Easy' },
    ]);
  }, []);

  const handleAddLesson = (e) => {
    e.preventDefault();
    if (!newLesson.title) return;

    const created = { id: Date.now(), ...newLesson };
    setLessons([...lessons, created]);
    setNewLesson({ title: '', description: '', expected_gesture: 'A', difficulty: 'Easy' });
    setShowAddLessonModal(false);
  };

  const handleDeleteLesson = (id) => {
    setLessons(lessons.filter((l) => l.id !== id));
  };

  const filteredStudents = students.filter((s) => s.name.toLowerCase().includes(searchTerm.toLowerCase()));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Student Progress Register */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '1rem' }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>Student Performance Register</h2>
          <input
            type="text"
            placeholder="Search student..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ padding: '0.5rem 0.75rem', borderRadius: '0.5rem', border: '1px solid #cbd5e1', outline: 'none' }}
          />
        </div>

        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
          <thead>
            <tr style={{ backgroundColor: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
              <th style={{ padding: '0.75rem' }}>Student Name</th>
              <th style={{ padding: '0.75rem' }}>Email</th>
              <th style={{ padding: '0.75rem' }}>Accuracy</th>
              <th style={{ padding: '0.75rem' }}>Completed</th>
              <th style={{ padding: '0.75rem' }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {filteredStudents.map((s) => (
              <tr key={s.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                <td style={{ padding: '0.75rem', fontWeight: '600' }}>{s.name}</td>
                <td style={{ padding: '0.75rem', color: '#64748b' }}>{s.email}</td>
                <td style={{ padding: '0.75rem', fontWeight: 'bold', color: '#4f46e5' }}>{s.accuracy}%</td>
                <td style={{ padding: '0.75rem' }}>{s.completedLessons}</td>
                <td style={{ padding: '0.75rem' }}>
                  <button onClick={() => setSelectedStudent(s)} style={{ padding: '0.25rem 0.75rem', backgroundColor: '#e0e7ff', color: '#4338ca', border: 'none', borderRadius: '0.375rem', fontWeight: '600', cursor: 'pointer' }}>
                    Details
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Lesson Management Section (Add / Remove Lessons) */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>Manage Course Lessons</h2>
          <button onClick={() => setShowAddLessonModal(true)} className="btn-submit" style={{ width: 'auto', padding: '0.5rem 1rem' }}>
            + Add New Lesson
          </button>
        </div>

        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
          <thead>
            <tr style={{ backgroundColor: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
              <th style={{ padding: '0.75rem' }}>Lesson Title</th>
              <th style={{ padding: '0.75rem' }}>Expected Sign</th>
              <th style={{ padding: '0.75rem' }}>Difficulty</th>
              <th style={{ padding: '0.75rem' }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {lessons.map((lesson) => (
              <tr key={lesson.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                <td style={{ padding: '0.75rem', fontWeight: '600' }}>{lesson.title}</td>
                <td style={{ padding: '0.75rem' }}>{lesson.expected_gesture}</td>
                <td style={{ padding: '0.75rem' }}>{lesson.difficulty}</td>
                <td style={{ padding: '0.75rem' }}>
                  <button onClick={() => handleDeleteLesson(lesson.id)} style={{ padding: '0.25rem 0.75rem', backgroundColor: '#fee2e2', color: '#991b1b', border: 'none', borderRadius: '0.375rem', fontWeight: '600', cursor: 'pointer' }}>
                    Remove
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Add Lesson Modal */}
      {showAddLessonModal && (
        <div style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem', zIndex: 100 }}>
          <div className="form-card" style={{ margin: 0, width: '100%', maxWidth: '450px' }}>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 'bold', marginBottom: '1rem' }}>Add New Lesson</h3>
            <form onSubmit={handleAddLesson}>
              <div className="form-group">
                <label>Lesson Title</label>
                <input type="text" required value={newLesson.title} onChange={(e) => setNewLesson({ ...newLesson, title: e.target.value })} />
              </div>
              <div className="form-group">
                <label>Expected Sign</label>
                <input type="text" required value={newLesson.expected_gesture} onChange={(e) => setNewLesson({ ...newLesson, expected_gesture: e.target.value })} />
              </div>
              <div className="form-group">
                <label>Difficulty</label>
                <select value={newLesson.difficulty} onChange={(e) => setNewLesson({ ...newLesson, difficulty: e.target.value })}>
                  <option value="Easy">Easy</option>
                  <option value="Medium">Medium</option>
                  <option value="Hard">Hard</option>
                </select>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button type="submit" className="btn-submit">Save Lesson</button>
                <button type="button" onClick={() => setShowAddLessonModal(false)} style={{ padding: '0.75rem', backgroundColor: '#e2e8f0', color: '#475569', border: 'none', borderRadius: '0.5rem', cursor: 'pointer', fontWeight: '600' }}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Student Details Modal */}
      {selectedStudent && (
        <div style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem', zIndex: 100 }}>
          <div className="card" style={{ maxWidth: '400px', width: '100%' }}>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>{selectedStudent.name}</h3>
            <p style={{ color: '#64748b', fontSize: '0.875rem', marginBottom: '1rem' }}>{selectedStudent.email}</p>
            <div style={{ borderTop: '1px solid #e2e8f0', borderBottom: '1px solid #e2e8f0', padding: '1rem 0', marginBottom: '1rem', lineHeight: '1.8' }}>
              <p><strong>Overall Accuracy:</strong> {selectedStudent.accuracy}%</p>
              <p><strong>Lessons Done:</strong> {selectedStudent.completedLessons}</p>
              <p><strong>Weak Signs:</strong> {selectedStudent.weakLetters.join(', ')}</p>
            </div>
            <button onClick={() => setSelectedStudent(null)} className="btn-submit">Close</button>
          </div>
        </div>
      )}
    </div>
  );
}