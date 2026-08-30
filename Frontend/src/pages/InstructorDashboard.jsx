import { useState, useEffect } from 'react';
import {
  getInstructorStudents,
  getAllLessons,
  createLesson,
  deleteLesson,
} from '../services/api';

const EMPTY_FORM = {
  title: '',
  module_id: '',
  expected_gesture: '',
  category: 'Alphabet',
  difficulty: 'Easy',
  content_description: '',
};

export default function InstructorDashboard() {
  const [searchTerm, setSearchTerm] = useState('');
  const [students, setStudents] = useState([]);
  const [lessons, setLessons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lessonsLoading, setLessonsLoading] = useState(true);
  const [instructorEmail, setInstructorEmail] = useState('');

  const [expandedStudent, setExpandedStudent] = useState(null);

  const [showLessonForm, setShowLessonForm] = useState(false);
  const [lessonForm, setLessonForm] = useState(EMPTY_FORM);
  const [lessonFormMsg, setLessonFormMsg] = useState(null);

  useEffect(() => {
    async function loadInstructorData() {
      setLoading(true);
      const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
      const email = currentUser.email || 'instructor@platform.org';
      setInstructorEmail(email);

      try {
        const response = await getInstructorStudents(email);
        const list = response?.students || (Array.isArray(response) ? response : []);
        setStudents(list);
      } catch (err) {
        console.warn('Failed to fetch instructor students:', err);
        setStudents([]);
      } finally {
        setLoading(false);
      }
    }
    loadInstructorData();
  }, []);

  useEffect(() => {
    loadLessons();
  }, []);

  async function loadLessons() {
    setLessonsLoading(true);
    try {
      const data = await getAllLessons();
      const list = data?.lessons || (Array.isArray(data) ? data : []);
      setLessons(list);
    } catch (err) {
      console.warn('Failed to fetch lessons:', err);
      setLessons([]);
    } finally {
      setLessonsLoading(false);
    }
  }

  async function handleDeleteLesson(id) {
    if (!window.confirm('Delete this lesson?')) return;
    try {
      await deleteLesson(id);
      setLessons((prev) => prev.filter((l) => l.id !== id && l.lesson_id !== id));
    } catch (err) {
      alert(err.message || 'Failed to delete lesson.');
    }
  }

  async function handleCreateLesson(e) {
    e.preventDefault();
    setLessonFormMsg(null);
    try {
      const payload = {
        title: lessonForm.title,
        module_id: lessonForm.module_id.trim() || 'mod_general_01',
        description: lessonForm.content_description || `Practice gesture for sign '${lessonForm.expected_gesture}'`,
        content_description: lessonForm.content_description,
        expected_gesture: (lessonForm.expected_gesture || '').toUpperCase(),
        category: lessonForm.category,
        difficulty: lessonForm.difficulty,
      };

      const newLesson = await createLesson(payload);
      setLessonFormMsg({ type: 'success', text: 'Lesson created successfully.' });
      setLessonForm(EMPTY_FORM);
      setShowLessonForm(false);
      
      if (newLesson) {
        setLessons((prev) => [newLesson, ...prev.filter((l) => (l.id || l.lesson_id) !== (newLesson.id || newLesson.lesson_id))]);
      } else {
        loadLessons();
      }
    } catch (err) {
      setLessonFormMsg({ type: 'error', text: err.message || 'Failed to create lesson.' });
    }
  }

  function updateLessonField(field, value) {
    setLessonForm((prev) => ({ ...prev, [field]: value }));
  }

  const filteredStudents = students.filter(
    (s) =>
      (s.username || s.name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (s.email || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  const inputStyle = {
    width: '100%',
    padding: '0.45rem 0.75rem',
    border: '1px solid var(--border-color)',
    borderRadius: 'var(--radius-md)',
    background: 'var(--bg-card, #fff)',
    color: 'var(--text-main)',
    fontSize: '0.85rem',
    outline: 'none',
  };

  const labelStyle = {
    display: 'block',
    fontSize: '0.78rem',
    fontWeight: 600,
    color: 'var(--text-muted)',
    marginBottom: '0.25rem',
  };

  const formRowStyle = {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '0.75rem',
  };

  return (
    <div>
      <div className="page-header">
        <p className="page-subtitle">Classroom Operations &amp; Performance</p>
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
            style={{ maxWidth: '250px', padding: '0.4rem 0.75rem', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', fontSize: '0.85rem', outline: 'none' }}
          />
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
            Loading students...
          </div>
        ) : filteredStudents.length === 0 ? (
          <div className="card" style={{ textAlign: 'center', padding: '2.5rem 1rem', color: 'var(--text-muted)' }}>
            <p style={{ fontSize: '0.95rem', margin: 0 }}>No students assigned yet.</p>
          </div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Student Name</th>
                  <th>Email</th>
                  <th>Avg Accuracy</th>
                  <th>Lessons Completed</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredStudents.map((s, idx) => {
                  const sid = s.student_id || s.id || idx;
                  const ps = s.progress_summary || {};
                  const isExpanded = expandedStudent === sid;
                  const accuracy = s.accuracy ?? ps.average_accuracy ?? s.average_accuracy ?? '—';
                  const completed = s.completedLessons ?? ps.lessons_completed ?? s.lessons_completed ?? 0;
                  const status = ps.status || s.status || 'Active';

                  return (
                    <tr key={sid} style={{ background: isExpanded ? 'var(--table-header-bg, #f9fafb)' : undefined }}>
                      <td style={{ fontWeight: 600 }}>{s.username || s.name || 'Learner'}</td>
                      <td style={{ color: 'var(--text-muted)' }}>{s.email}</td>
                      <td style={{ color: 'var(--primary)', fontWeight: 700 }}>
                        {typeof accuracy === 'number' ? `${accuracy}%` : accuracy}
                      </td>
                      <td>{completed}</td>
                      <td>
                        <span
                          className={`badge ${status.toLowerCase() === 'active' ? 'badge-success' : 'badge-primary'}`}
                          style={{ fontSize: '0.7rem', textTransform: 'capitalize' }}
                        >
                          {status}
                        </span>
                      </td>
                      <td>
                        <button
                          className="btn-secondary"
                          style={{ padding: '0.25rem 0.6rem', fontSize: '0.75rem' }}
                          onClick={() => setExpandedStudent(isExpanded ? null : sid)}
                        >
                          {isExpanded ? 'Close' : 'Details'}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>

            {expandedStudent !== null && (() => {
              const s = filteredStudents.find((s, idx) => (s.student_id || s.id || idx) === expandedStudent);
              if (!s) return null;
              const ps = s.progress_summary || {};
              const accuracy = s.accuracy ?? ps.average_accuracy ?? s.average_accuracy ?? '—';
              const completed = s.completedLessons ?? ps.lessons_completed ?? s.lessons_completed ?? 0;
              const status = ps.status || s.status || 'Active';

              return (
                <div
                  style={{
                    padding: '1rem 1.25rem',
                    borderTop: '1px solid var(--border-color)',
                    background: 'var(--table-header-bg, #f9fafb)',
                    borderRadius: '0 0 var(--radius-md) var(--radius-md)',
                  }}
                >
                  <h4 style={{ margin: '0 0 0.6rem', fontSize: '0.9rem', color: 'var(--text-main)' }}>
                    {s.username || s.name || 'Learner'} — Progress Summary
                  </h4>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '0.75rem', fontSize: '0.85rem' }}>
                    <div className="card" style={{ padding: '0.75rem' }}>
                      <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', marginBottom: '0.2rem' }}>Email</div>
                      <div style={{ fontWeight: 600 }}>{s.email || '—'}</div>
                    </div>
                    <div className="card" style={{ padding: '0.75rem' }}>
                      <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', marginBottom: '0.2rem' }}>Lessons Completed</div>
                      <div style={{ fontWeight: 600, color: 'var(--primary)' }}>{completed}</div>
                    </div>
                    <div className="card" style={{ padding: '0.75rem' }}>
                      <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', marginBottom: '0.2rem' }}>Average Accuracy</div>
                      <div style={{ fontWeight: 600, color: 'var(--success, #22c55e)' }}>
                        {typeof accuracy === 'number' ? `${accuracy}%` : accuracy}
                      </div>
                    </div>
                    <div className="card" style={{ padding: '0.75rem' }}>
                      <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', marginBottom: '0.2rem' }}>Status</div>
                      <div style={{ fontWeight: 600, textTransform: 'capitalize' }}>{status}</div>
                    </div>
                  </div>
                </div>
              );
            })()}
          </div>
        )}
      </div>

      {/* Course Management */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
            Manage Course Lessons
          </h3>
          <button
            className="btn-primary"
            style={{ padding: '0.4rem 0.85rem', fontSize: '0.8rem' }}
            onClick={() => {
              setShowLessonForm((v) => !v);
              setLessonFormMsg(null);
            }}
          >
            {showLessonForm ? 'Cancel' : '+ Add New Lesson'}
          </button>
        </div>

        {showLessonForm && (
          <div
            className="card"
            style={{ padding: '1.25rem', marginBottom: '1.25rem', border: '1px solid var(--border-color)' }}
          >
            <h4 style={{ margin: '0 0 1rem', fontSize: '0.95rem', color: 'var(--text-main)' }}>
              New Lesson
            </h4>
            <form onSubmit={handleCreateLesson}>
              <div style={formRowStyle}>
                <div>
                  <label style={labelStyle}>Title *</label>
                  <input
                    required
                    type="text"
                    placeholder="e.g. Alphabet Letter Q"
                    value={lessonForm.title}
                    onChange={(e) => updateLessonField('title', e.target.value)}
                    style={inputStyle}
                  />
                </div>
                <div>
                  <label style={labelStyle}>Module ID (Optional)</label>
                  <input
                    type="text"
                    placeholder="e.g. mod_general_01 (default applied if blank)"
                    value={lessonForm.module_id}
                    onChange={(e) => updateLessonField('module_id', e.target.value)}
                    style={inputStyle}
                  />
                </div>
                <div>
                  <label style={labelStyle}>Expected Gesture (max 5 chars) *</label>
                  <input
                    required
                    type="text"
                    maxLength={5}
                    placeholder="e.g. Q"
                    value={lessonForm.expected_gesture}
                    onChange={(e) => updateLessonField('expected_gesture', e.target.value.toUpperCase())}
                    style={inputStyle}
                  />
                </div>
                <div>
                  <label style={labelStyle}>Category</label>
                  <select
                    value={lessonForm.category}
                    onChange={(e) => updateLessonField('category', e.target.value)}
                    style={inputStyle}
                  >
                    <option value="Alphabet">Alphabet</option>
                    <option value="Number">Number</option>
                    <option value="Word">Word</option>
                  </select>
                </div>
                <div>
                  <label style={labelStyle}>Difficulty</label>
                  <select
                    value={lessonForm.difficulty}
                    onChange={(e) => updateLessonField('difficulty', e.target.value)}
                    style={inputStyle}
                  >
                    <option value="Easy">Easy</option>
                    <option value="Medium">Medium</option>
                    <option value="Hard">Hard</option>
                  </select>
                </div>
              </div>
              <div style={{ marginTop: '0.75rem' }}>
                <label style={labelStyle}>Description</label>
                <textarea
                  rows={3}
                  placeholder="Describe the lesson content..."
                  value={lessonForm.content_description}
                  onChange={(e) => updateLessonField('content_description', e.target.value)}
                  style={{ ...inputStyle, resize: 'vertical' }}
                />
              </div>

              {lessonFormMsg && (
                <div
                  style={{
                    marginTop: '0.75rem',
                    padding: '0.5rem 0.75rem',
                    borderRadius: 'var(--radius-md)',
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    background: lessonFormMsg.type === 'success' ? 'var(--success, #dcfce7)' : 'var(--danger, #fee2e2)',
                    color: lessonFormMsg.type === 'success' ? 'var(--text-main)' : 'var(--danger, #b91c1c)',
                  }}
                >
                  {lessonFormMsg.text}
                </div>
              )}

              <div style={{ marginTop: '1rem' }}>
                <button type="submit" className="btn-primary" style={{ padding: '0.45rem 1.2rem', fontSize: '0.85rem' }}>
                  Create Lesson
                </button>
              </div>
            </form>
          </div>
        )}

        {lessonsLoading ? (
          <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
            Loading lessons...
          </div>
        ) : lessons.length === 0 ? (
          <div className="card" style={{ textAlign: 'center', padding: '2.5rem 1rem', color: 'var(--text-muted)' }}>
            <p style={{ fontSize: '0.95rem', margin: 0 }}>No lessons available.</p>
          </div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Lesson Title</th>
                  <th>Expected Sign</th>
                  <th>Category</th>
                  <th>Difficulty</th>
                  <th>Module</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {lessons.map((l) => (
                  <tr key={l.id || l.lesson_id}>
                    <td style={{ fontWeight: 600 }}>{l.title}</td>
                    <td><span className="badge badge-primary">{l.expected_gesture || l.target || '—'}</span></td>
                    <td style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>{l.category || '—'}</td>
                    <td><span className="badge badge-success">{l.difficulty || 'Easy'}</span></td>
                    <td style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                      {l.module_id ? (l.module_id.length > 10 ? l.module_id.slice(0, 8) + '…' : l.module_id) : '—'}
                    </td>
                    <td>
                      <button
                        onClick={() => handleDeleteLesson(l.id || l.lesson_id)}
                        className="btn-danger-sm"
                      >
                        Remove
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}