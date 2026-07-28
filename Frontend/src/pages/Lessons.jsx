import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export default function Lessons() {
  const [lessons, setLessons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchLessons = async () => {
      setLoading(true);
      setError(null);
      
      const token = localStorage.getItem('access_token');
      const headers = {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` })
      };

      try {
        // Primary Attempt: Try fetching directly from http://localhost:8000/lessons
        let res = await fetch('http://localhost:8000/lessons', { headers });

        // Fallback Attempt: If 404, try http://localhost:8000/api/lessons
        if (res.status === 404) {
          res = await fetch('http://localhost:8000/api/lessons', { headers });
        }

        if (!res.ok) {
          throw new Error(`Server returned HTTP status ${res.status}`);
        }

        const data = await res.json();
        
        // Handle array response or nested object responses like { lessons: [...] }
        const lessonList = Array.isArray(data) ? data : (data.lessons || []);
        
        if (lessonList.length > 0) {
          setLessons(lessonList);
        } else {
          // Default curriculum items if backend database table is currently empty
          setLessons(getFallbackLessons());
        }
      } catch (err) {
        console.warn('Backend fetch failed, loading default local curriculum:', err.message);
        setError('Connected in offline/demo mode. Displaying default curriculum.');
        setLessons(getFallbackLessons());
      } finally {
        setLoading(false);
      }
    };

    fetchLessons();
  }, []);

  // Fallback curriculum items to prevent blank screens when FastAPI is offline
  const getFallbackLessons = () => [
    { lesson_id: 'les_letter_a', title: "Alphabet 'A'", level: 'Beginner', description: 'Master hand positioning for the letter A.', expected: 'A' },
    { lesson_id: 'les_letter_b', title: "Alphabet 'B'", level: 'Beginner', description: 'Master finger extension for the letter B.', expected: 'B' },
    { lesson_id: 'les_letter_c', title: "Alphabet 'C'", level: 'Intermediate', description: 'Practice curved hand shapes for the letter C.', expected: 'C' },
  ];

  const handleStartPractice = (lesson) => {
    navigate('/practice', {
      state: {
        lessonId: lesson.lesson_id || lesson.id,
        title: lesson.title || lesson.name,
        expected: lesson.expected || lesson.title?.split("'")[1] || 'A'
      }
    });
  };

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>
        <h3>⌛ Loading Curriculum from Backend...</h3>
      </div>
    );
  }

  return (
    <div style={{ padding: '40px', maxWidth: '1000px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ color: '#0f172a', margin: 0 }}>Sign Language Curriculum 📚</h1>
          <p style={{ color: '#64748b', margin: '4px 0 0 0' }}>Select a lesson to begin real-time camera practice and gesture analysis.</p>
        </div>
      </div>

      {error && (
        <div style={{ background: '#fffbe3', borderLeft: '4px solid #f59e0b', color: '#b45309', padding: '12px 16px', borderRadius: '6px', marginBottom: '24px', fontSize: '14px' }}>
          ⚠️ {error}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px' }}>
        {lessons.map((lesson, idx) => (
          <div 
            key={lesson.lesson_id || lesson.id || idx}
            style={{ background: '#fff', padding: '24px', borderRadius: '12px', border: '1px solid #e2e8f0', boxShadow: '0 2px 4px rgba(0,0,0,0.02)', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}
          >
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <span style={{ fontSize: '12px', fontWeight: 'bold', padding: '4px 8px', borderRadius: '4px', background: '#e0f2fe', color: '#0369a1' }}>
                  {lesson.level || 'Standard'}
                </span>
                <span style={{ fontSize: '12px', color: '#94a3b8' }}>
                  ID: {lesson.lesson_id || lesson.id}
                </span>
              </div>
              <h3 style={{ color: '#0f172a', margin: '0 0 8px 0' }}>{lesson.title || lesson.name}</h3>
              <p style={{ color: '#64748b', fontSize: '14px', margin: '0 0 20px 0', lineHeight: '1.5' }}>
                {lesson.description || 'Practice gesture recognition and accuracy.'}
              </p>
            </div>

            <button
              onClick={() => handleStartPractice(lesson)}
              style={{ width: '100%', background: '#2563eb', color: '#fff', border: 'none', padding: '12px', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer', transition: 'background 0.2s' }}
            >
              ▶️ Start Practice
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}