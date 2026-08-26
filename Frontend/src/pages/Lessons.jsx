import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getCourses, getCourseDetails, getCompletionSummary, getUserCompletions } from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function Lessons() {
  const { user } = useAuth();
  const [courses, setCourses] = useState([]);
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDifficulty, setSelectedDifficulty] = useState('All');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [completionSummary, setCompletionSummary] = useState(null);
  const [completedLessonIds, setCompletedLessonIds] = useState(new Set());
  const [completions, setCompletions] = useState([]);
  const navigate = useNavigate();

  const bestScoreForLesson = (lessonId) => {
    const matching = completions.filter((c) => c.lesson_id === lessonId);
    if (matching.length === 0) return null;
    return Math.max(...matching.map((c) => c.score ?? 0));
  };

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

  const fetchCompletions = async (userId) => {
    try {
      const summary = await getCompletionSummary(userId);
      setCompletionSummary(summary);
      const comps = await getUserCompletions(userId);
      setCompletions(comps.completions || []);
      setCompletedLessonIds(new Set((comps.completions || []).map((c) => c.lesson_id)));
    } catch (_) {
      // Silently ignore — completion data is non-critical
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
        if (user?.user_id) {
          await fetchCompletions(user.user_id);
        }
      } catch (err) {
        if (cancelled) return;
        setError(err.message || 'Failed to load courses.');
        setLoading(false);
      }
    }
    loadInitialCourses();
    return () => { cancelled = true; };
  }, [user]);

  const handleStartPractice = (lesson) => {
    const gesture = lesson.expected_gesture ? `&gesture=${encodeURIComponent(lesson.expected_gesture)}` : '';
    navigate(`/practice?lesson_id=${lesson.lesson_id}${gesture}`);
  };

  const allLessons =
    selectedCourse?.modules?.flatMap((m) =>
      m.lessons.map((l) => ({ ...l, module_name: m.module_name || m.title }))
    ) || [];

  const filteredLessons = allLessons.filter((l) => {
    const term = searchTerm.toLowerCase().trim();
    const matchesSearch =
      !term ||
      l.title?.toLowerCase().includes(term) ||
      l.module_name?.toLowerCase().includes(term) ||
      (l.description && l.description.toLowerCase().includes(term)) ||
      (l.expected_gesture && l.expected_gesture.toLowerCase().includes(term)) ||
      (l.difficulty && l.difficulty.toLowerCase().includes(term));

    const matchesDifficulty =
      selectedDifficulty === 'All' ||
      (l.difficulty && l.difficulty.toLowerCase() === selectedDifficulty.toLowerCase());

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

      {/* Progress Counter */}
      {completionSummary && (
        <div className="card" style={{ padding: '1rem 1.25rem', marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontWeight: '600', fontSize: '0.95rem', color: 'var(--text-main)' }}>
              {completionSummary.completed} of {completionSummary.total_lessons} lessons completed ({completionSummary.percentage}%)
            </span>
            <span className="badge badge-success" style={{ fontSize: '0.8rem' }}>
              {completionSummary.percentage >= 100 ? 'All Done!' : 'In Progress'}
            </span>
          </div>
          <div style={{ width: '100%', height: '8px', backgroundColor: 'var(--border-color)', borderRadius: '4px', overflow: 'hidden' }}>
            <div style={{
              width: `${completionSummary.percentage}%`,
              height: '100%',
              backgroundColor: completionSummary.percentage >= 100 ? 'var(--success)' : 'var(--primary)',
              borderRadius: '4px',
              transition: 'width 0.4s ease',
            }} />
          </div>
        </div>
      )}

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
          {filteredLessons.map((lesson) => {
            const isCompleted = completedLessonIds.has(lesson.lesson_id);
            const score = bestScoreForLesson(lesson.lesson_id);
            return (
              <div
                key={lesson.lesson_id}
                className="card"
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  borderColor: isCompleted ? 'var(--success)' : undefined,
                  borderWidth: isCompleted ? '1.5px' : undefined,
                }}
              >
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                    <span className="badge badge-primary">{lesson.module_name}</span>
                    <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                      {isCompleted ? (
                        <span className="badge badge-success" style={{ fontSize: '0.75rem', whiteSpace: 'nowrap' }}>&#10003; Completed</span>
                      ) : (
                        <span className="badge" style={{ fontSize: '0.75rem', backgroundColor: 'var(--surface-2)', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>Not completed</span>
                      )}
                      <span className="badge badge-warning">Target Sign: {lesson.expected_gesture}</span>
                    </div>
                  </div>
                  <h3 style={{ fontSize: '1.125rem', fontWeight: '700', marginBottom: '0.5rem', color: 'var(--text-main)' }}>
                    {lesson.title}
                  </h3>
                  <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '1.25rem', lineHeight: '1.5' }}>
                    {lesson.description}
                  </p>
                  {isCompleted && score !== null && (
                    <p style={{ fontSize: '0.8rem', color: 'var(--success)', fontWeight: '600', marginBottom: '1rem' }}>
                      Best Score: {score}%
                    </p>
                  )}
                </div>

                <button
                  onClick={() => handleStartPractice(lesson)}
                  className={isCompleted ? 'btn-secondary' : 'btn-primary'}
                  style={{ width: '100%' }}
                >
                  {isCompleted ? 'Practice Again' : 'Practice Lesson'}
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
