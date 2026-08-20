import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getCourses, getCourseDetails } from '../services/api';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function Lessons() {
  const [courses, setCourses] = useState([]);
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDifficulty, setSelectedDifficulty] = useState('All');
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const fetchCourseData = async (courseId) => {
    setLoading(true);
    try {
      const data = await getCourseDetails(courseId);
      setSelectedCourse(data);
    } catch (err) {
      console.warn("Could not load course details, using fallback:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
 feature/frontend-day4-clean
    async function loadInitialCourses() {
      try {
        const data = await getCourses();
        const courseList = data.courses || data || [];
        setCourses(courseList);
        if (courseList.length > 0) {
          await fetchCourseData(courseList[0].course_id);
        } else {
          setLoading(false);
        }
      } catch (err) {
        console.warn("Could not load courses:", err);

    const token = localStorage.getItem('access_token');
    fetch(`${API_BASE_URL}/api/courses`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => res.json())
      .then((data) => {
        setCourses(data.courses || []);
        if (data.courses && data.courses.length > 0) {
          fetchCourseDetails(data.courses[0].course_id);
        } else {
          setLoading(false);
        }
      })
      .catch(() => {
        const fallbackCourses = [
          {
            course_id: 'crs_beginner_01',
            title: 'Introduction to Sign Language Alphabets',
            description: 'Learn basic static hand layouts, joint coordinate alignments, and alphabetic gestures.',
            level: 'Beginner',
          },
          {
            course_id: 'crs_intermediate_02',
            title: 'Conversational Phrases and Dynamic Movements',
            description: 'Master gesture sequences, timing, and dynamic moving expressions.',
            level: 'Intermediate',
          },
        ];
        setCourses(fallbackCourses);
        fetchCourseDetails('crs_beginner_01');
      });
  }, []);

  const fetchCourseDetails = (courseId) => {
    setLoading(true);
    const token = localStorage.getItem('access_token');
    fetch(`${API_BASE_URL}/api/courses/${courseId}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => res.json())
      .then((data) => {
        setSelectedCourse(data);
        setLoading(false);
      })
      .catch(() => {
        setSelectedCourse({
          course_id: courseId,
          title: 'Introduction to Sign Language Alphabets',
          level: 'Beginner',
          modules: [
            {
              module_id: 'mod_alph_01',
              module_name: 'Static Handshapes (A-E)',
              lessons: [
                {
                  lesson_id: 'les_letter_a',
                  title: "The Alphabet Letter 'A'",
                  description: 'Practice holding a closed fist posture with the thumb resting alongside the outer hand.',
                  expected_gesture: 'A',
                  difficulty: 'Easy',
                },
                {
                  lesson_id: 'les_letter_b',
                  title: "The Alphabet Letter 'B'",
                  description: 'Practice holding an open, flat palm posture with your thumb tucked inwards across your front palm.',
                  expected_gesture: 'B',
                  difficulty: 'Easy',
                },
              ],
            },
          ],
        });
 main
        setLoading(false);
      }
    }
    loadInitialCourses();
  }, []);

  const handleStartPractice = (lesson) => {
    navigate(`/practice?lesson_id=${lesson.lesson_id}`);
  };

  const allLessons = selectedCourse?.modules?.flatMap((m) =>
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
            placeholder="Search lessons or gestures..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ flex: 1, minWidth: '200px' }}
          />
          <select
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

      {/* Lesson Grid */}
      {loading ? (
        <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          Loading course lessons...
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