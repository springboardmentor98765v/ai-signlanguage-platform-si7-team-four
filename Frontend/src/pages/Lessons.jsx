import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export default function Lessons() {
  const navigate = useNavigate();
  const [courseData, setCourseData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchLessons = async () => {
      try {
        const token = localStorage.getItem('access_token');
        const response = await fetch('http://localhost:8000/api/courses/crs_beginner_01', {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (!response.ok) throw new Error('Could not synchronize system curriculum items.');
        const data = await response.json();
        setCourseData(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchLessons();
  }, []);

  if (loading) return <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>Synchronizing available modules...</div>;
  if (error) return <div style={{ padding: '40px', color: '#ef4444', textAlign: 'center' }}>⚠️ Network Error: {error}</div>;

  return (
    <div style={{ padding: '40px', maxWidth: '900px', margin: '0 auto' }}>
      <h1 style={{ textAlign: 'center', marginBottom: '10px', color: '#0f172a' }}>📚 {courseData?.title}</h1>
      <p style={{ textAlign: 'center', color: '#64748b', marginBottom: '30px' }}>Level: {courseData?.level}</p>
      
      {courseData?.modules?.map((mod) => (
        <div key={mod.module_id} style={{ marginBottom: '40px' }}>
          <h2 style={{ borderBottom: '2px solid #e2e8f0', paddingBottom: '8px', marginBottom: '20px', color: '#1e293b' }}>{mod.module_name}</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {mod.lessons?.map((les) => (
              <div key={les.lesson_id} style={{ padding: '25px', background: '#fff', borderRadius: '12px', boxShadow: '0 4px 6px rgba(0,0,0,0.03)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <h3 style={{ margin: '0 0 8px 0', color: '#1e293b' }}>{les.title}</h3>
                  <p style={{ margin: 0, fontSize: '14px', color: '#64748b' }}>{les.description}</p>
                </div>
                <button 
                  onClick={() => navigate('/practice', { state: { lessonId: les.lesson_id, title: les.title, expected: les.expected_gesture } })} 
                  style={{ background: '#10b981', color: '#fff', border: 'none', padding: '12px 20px', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}
                >
                  Practice
                </button>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}