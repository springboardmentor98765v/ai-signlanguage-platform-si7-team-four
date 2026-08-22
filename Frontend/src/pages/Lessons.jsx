import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getCourses, getCourseDetails } from '../services/api';

export default function Lessons() {
  const [courses, setCourses] = useState([]);
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDifficulty, setSelectedDifficulty] = useState('All');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const fetchCourseData = async (courseId) => {
    setLoading(true);
    setError('');
    try {
      const data = await getCourseDetails(courseId);
      setSelectedCourse(data);
    } catch (err) {
      setError(err.message || 'Failed to load course details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let cancelled = false;
    async function loadInitialCourses() {
      setLoading(true);
      setError('');
      try {
        const courseList = (await getCourses()) || [];
        if (cancelled) return;
        setCourses(courseList);
        if (courseList.length > 0) {
          await fetchCourseData(courseList[0].course_id);
        } else {
          setLoading(false);
        }
      } catch (err) {
        if (cancelled) return;
        setError(err.message || 'Failed to load courses.');
        setLoading(false);
      }
    }
    loadInitialCourses();
    return () => { cancelled = true; };
  }, []);

  const handleStartPractice = (lesson) => {
    navigate(`/practice?lesson_id=${lesson.lesson_id}`);
  };

  const allLessons =
    selectedCourse?.modules?.flatMap((m) =>
      m.lessons.map((l) => ({ ...l, module_name: m.module_name || m.title }))
    ) || [];

  const filteredLessons = allLessons.filter((l) => {
    const matchesSearch =
      l.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (l.description && l.description.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (l.expected_gesture && l.expected_gesture.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesDifficulty =
      selectedDifficulty === 'All' || (l.difficulty && l.difficulty === selectedDifficulty);

    return matchesSearch && matchesDifficulty;
  });

  return (
    <div>
      {/* Header Section */}
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <p className="page-subtitle">Sign Language Curriculum</p>
          <h1 className="page-title">Course & Lesson Catalogue</h1>
        </div>

        {/* Filter Controls */}
        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', minWidth: '320px' }}>
          <input
            type="text"
            className="input-control"
            placeholder="Search lessons or gestures..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ flex: 1, minWidth: '200px' }}
          />
          <select
            className="input-control"
            value={selectedDifficulty}
            onChange={(e) => setSelectedDifficulty(e.target.value)}
            style={{ width: '140px' }}
          >
            <option value="All">All Levels</option>
            <option value="Easy">Easy</option>
            <option value="Medium">Medium</option>
            <option value="Hard">Hard</option>
          </select>
        </div>
      </div>

      {/* Course Tabs */}
{courses.length > 0 && (
        <div style={{ display: 'flex', gap: '0.75rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.75rem', marginBottom: '1.5rem', overflowX: 'auto' }}>
          {courses.map((course) => (
            <button
              key={course.course_id}
              onClick={() => fetchCourseData(course.course_id)}
              className={selectedCourse?.course_id === course.course_id ? "btn-primary" : "btn-secondary"}
              style={{ fontSize: '0.85rem', whiteSpace: 'nowrap' }}
            >
              {course.title} ({course.level || 'All Levels'})
            </button>
          ))}
        </div>
      )}

      {/* Lesson Grid */}
      {loading ? (
        <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          Loading course lessons...
        </div>
      ) : error ? (
        <div className="card" style={{ padding: '2rem', textAlign: 'center', color: 'var(--danger)', fontWeight: 600 }}>
          {error}
        </div>
      ) : filteredLessons.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '3rem' }}>
          No lessons found matching your filters.
        </div>
      ) : (
        <div className="grid-2">
          {filteredLessons.map((lesson) => (
            <div key={lesson.lesson_id} className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                  <span className="badge badge-primary">{lesson.module_name}</span>
                  <span className="badge badge-warning">Target Sign: {lesson.expected_gesture}</span>
                </div>
                <h3 style={{ fontSize: '1.125rem', fontWeight: '700', marginBottom: '0.5rem', color: 'var(--text-main)' }}>
                  {lesson.title}
                </h3>
                <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '1.25rem', lineHeight: '1.5' }}>
                  {lesson.description}
                </p>
              </div>

              <button
                onClick={() => handleStartPractice(lesson)}
                className="btn-primary"
                style={{ width: '100%' }}
              >
                Practice Lesson
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}