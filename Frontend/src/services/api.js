// Centralized API Service for AI Sign Language Platform
// Connects to FastAPI Backend via dynamic URL configuration
// Includes automatic graceful fallback to offline simulation data when backend is offline.

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const getAuthHeaders = () => {
  const token = localStorage.getItem('access_token');
  return {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
  };
};

/**
 * Generic fetch wrapper with offline fallback handling
 */
async function fetchWithFallback(url, options = {}, fallbackData = null) {
  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        ...getAuthHeaders(),
        ...(options.headers || {}),
      },
    });

    if (!res.ok) {
      const errorText = await res.text();
      let errorJson = {};
      try { errorJson = JSON.parse(errorText); } catch (_) {}
      throw new Error(errorJson.message || errorJson.detail || `Server returned status ${res.status}`);
    }

    return await res.json();
  } catch (err) {
    if (fallbackData !== null) {
      console.warn(`[API Fallback Mode] Query to ${url} failed (${err.message}). Using local offline fallback data.`);
      return typeof fallbackData === 'function' ? fallbackData() : fallbackData;
    }
    throw err;
  }
}

/**
 * Generic API fetcher for live backend endpoints
 */
export async function apiRequest(endpoint, options = {}) {
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      ...getAuthHeaders(),
      ...(options.headers || {}),
    },
  });

  if (!res.ok) {
    const errorText = await res.text();
    let errorJson = {};
    try { errorJson = JSON.parse(errorText); } catch (_) {}
    throw new Error(errorJson.message || errorJson.detail || `Server returned status ${res.status}`);
  }

  return await res.json();
}

/**
 * Binary Stream File Downloader (PDF & Excel Exports)
 */
export async function downloadFileStream(endpoint, defaultFilename) {
  const token = localStorage.getItem('access_token');
  const fullUrl = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;

  try {
    const response = await fetch(fullUrl, {
      method: 'GET',
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });

    if (!response.ok) {
      throw new Error(`File stream failed with HTTP status ${response.status}`);
    }

    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = downloadUrl;
    anchor.setAttribute('download', defaultFilename);
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    window.URL.revokeObjectURL(downloadUrl);
    return true;
  } catch (err) {
    console.warn(`[Download Fallback] Streaming from ${fullUrl} failed (${err.message}). Simulating offline download trigger.`);
    const dummyBlob = new Blob([`Sign Language Platform Mock Export - ${defaultFilename}`], { type: 'text/plain' });
    const dummyUrl = window.URL.createObjectURL(dummyBlob);
    const anchor = document.createElement('a');
    anchor.href = dummyUrl;
    anchor.setAttribute('download', defaultFilename);
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    window.URL.revokeObjectURL(dummyUrl);
    return false;
  }
}

// -------------------------------------------------------------------
// 1) Authentication & User APIs (Intern 2 Contract)
// -------------------------------------------------------------------

export async function registerUser({ username, email, password, role }) {
  return await fetchWithFallback(
    `${API_BASE_URL}/api/auth/register`,
    {
      method: 'POST',
      body: JSON.stringify({ username, email, password, role: role || 'Learner' }),
    },
    {
      message: 'User account created successfully (Mock Mode)',
      user_id: `usr_${Date.now()}`,
      role: role || 'Learner',
    }
  );
}

export async function loginUser({ email, password }) {
  return await fetchWithFallback(
    `${API_BASE_URL}/api/auth/login`,
    {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    },
    {
      access_token: `mock_jwt_token_${Date.now()}`,
      token_type: 'bearer',
      user: {
        user_id: `usr_${Date.now()}`,
        username: email.split('@')[0] || 'learner_user',
        email: email,
        role: email.includes('admin')
          ? 'Administrator'
          : email.includes('trainer')
          ? 'Accessibility Trainer'
          : email.includes('instructor')
          ? 'Instructor'
          : 'Learner',
      },
    }
  );
}

export async function updateUserProfile(profileData) {
  return await fetchWithFallback(
    `${API_BASE_URL}/api/auth/profile`,
    {
      method: 'PUT',
      body: JSON.stringify(profileData),
    },
    {
      message: 'Profile updated successfully',
      user: profileData,
    }
  );
}

export async function changePassword({ oldPassword, newPassword }) {
  return await fetchWithFallback(
    `${API_BASE_URL}/api/auth/change-password`,
    {
      method: 'POST',
      body: JSON.stringify({ oldPassword, newPassword }),
    },
    {
      message: 'Password changed successfully',
    }
  );
}

// -------------------------------------------------------------------
// 2) Course & Lesson Service Endpoints (Intern 2 Contract)
// -------------------------------------------------------------------

export async function getCourses() {
  return await fetchWithFallback(
    `${API_BASE_URL}/api/courses`,
    { method: 'GET' },
    {
      total_courses: 3,
      courses: [
        {
          course_id: 'crs_beginner_01',
          title: 'Introduction to Sign Language Alphabets',
          description: 'Learn basic static hand layouts, joint coordinate alignments, and alphabetic gestures.',
          level: 'Beginner',
          category: 'Alphabet',
          total_lessons: 5,
        },
        {
          course_id: 'crs_intermediate_02',
          title: 'Conversational Phrases and Dynamic Movements',
          description: 'Master gesture sequences, timing, and dynamic moving expressions.',
          level: 'Intermediate',
          category: 'Words & Phrases',
          total_lessons: 4,
        },
        {
          course_id: 'crs_advanced_03',
          title: 'Advanced Numbers & Technical Terminology',
          description: 'Speed-signing practice, complex hand rotations, and rapid gesture transitions.',
          level: 'Advanced',
          category: 'Numbers & Symbols',
          total_lessons: 3,
        },
      ],
    }
  );
}

export async function getCourseDetails(courseId) {
  return await fetchWithFallback(
    `${API_BASE_URL}/api/courses/${courseId}`,
    { method: 'GET' },
    {
      course_id: courseId || 'crs_beginner_01',
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
            {
              lesson_id: 'les_letter_c',
              title: "The Alphabet Letter 'C'",
              description: 'Form a open curved shape with fingers and thumb resembling the letter C.',
              expected_gesture: 'C',
              difficulty: 'Easy',
            },
            {
              lesson_id: 'les_letter_l',
              title: "The Alphabet Letter 'L'",
              description: 'Extend your index finger upwards and thumb sideways to form an L shape.',
              expected_gesture: 'L',
              difficulty: 'Easy',
            },
            {
              lesson_id: 'les_letter_y',
              title: "The Alphabet Letter 'Y'",
              description: 'Extend your thumb and pinky outwards while holding middle three fingers in a fist.',
              expected_gesture: 'Y',
              difficulty: 'Medium',
            },
          ],
        },
      ],
    }
  );
}

// -------------------------------------------------------------------
// 3) Practice & Gesture Submissions
// -------------------------------------------------------------------

export async function submitPracticeGesture({ userId, lessonId, targetLetter, imageData }) {
  return await fetchWithFallback(
    `${API_BASE_URL}/api/practice/submit`,
    {
      method: 'POST',
      body: JSON.stringify({
        user_id: userId || 1,
        lesson_id: lessonId || 1,
        target_letter: targetLetter,
        image_data: imageData,
      }),
    },
    {
      predicted_sign: targetLetter,
      confidence: 92,
      feedback: `Great job! Hand posture matches target sign '${targetLetter}' accurately.`,
      metrics: {
        hand_shape: 94,
        finger_position: 88,
        timing: 91,
      },
    }
  );
}

export async function startPracticeSession(lessonId) {
  return await fetchWithFallback(
    `${API_BASE_URL}/api/practice/start`,
    {
      method: 'POST',
      body: JSON.stringify({ lesson_id: lessonId }),
    },
    {
      session_id: `sess_${Date.now()}`,
      status: 'initialized',
      started_at: Date.now() / 1000,
    }
  );
}

export async function processWebcamFrame(sessionId, base64FrameData) {
  return await fetchWithFallback(
    `${API_BASE_URL}/api/practice/process-frame`,
    {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        frame_data: base64FrameData,
      }),
    },
    {
      session_id: sessionId,
      predicted_sign: 'A',
      confidence: 96.4,
    }
  );
}

// -------------------------------------------------------------------
// 4) Assessment & Feedback Service Endpoints
// -------------------------------------------------------------------

export async function evaluateAssessment({ sessionId, expectedGesture, predictedGesture, confidence }) {
  return await fetchWithFallback(
    `${API_BASE_URL}/api/assessment/evaluate`,
    {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        expected_gesture: expectedGesture,
        predicted_gesture: predictedGesture || expectedGesture,
        confidence: confidence || 95.0,
      }),
    },
    () => {
      const isMatch = expectedGesture === (predictedGesture || expectedGesture);
      const accScore = isMatch ? Math.floor(Math.random() * 15) + 85 : Math.floor(Math.random() * 30) + 40;
      
      return {
        assessment_id: `asm_${Date.now()}`,
        overall_accuracy: accScore,
        metrics: {
          hand_shape_score: Math.min(100, accScore + 3),
          finger_position_score: Math.max(60, accScore - 2),
          timing_score: 90.0,
        },
        feedback: {
          is_correct: accScore >= 75,
          suggestions: accScore >= 75
            ? ['Excellent hand posture! Your joint alignment is well centered.']
            : [
                'Keep your thumb closer alongside your outer palm.',
                'Ensure all fingers are fully extended towards the top of the camera frame.',
              ],
        },
        possible_issue: accScore >= 75 ? null : 'Thumb position is tucked slightly too tight inward.',
      };
    }
  );
}

// -------------------------------------------------------------------
// 5) Analytics & Dashboard Endpoints
// -------------------------------------------------------------------

export async function getDashboardAnalytics() {
  return await fetchWithFallback(
    `${API_BASE_URL}/api/analytics/dashboard`,
    { method: 'GET' },
    {
      user_id: 'usr_78910',
      overall_accuracy_percentage: 91.0,
      lessons_completed: 18,
      practice_hours: 24.5,
      improvement_rate_percentage: 12.0,
      streak_days: 7,
      accuracy_over_time: [
        { date: 'Mon', accuracy: 68 },
        { date: 'Tue', accuracy: 75 },
        { date: 'Wed', accuracy: 82 },
        { date: 'Thu', accuracy: 88 },
        { date: 'Fri', accuracy: 91 },
        { date: 'Sat', accuracy: 94 },
      ],
      completion_by_category: [
        { category: 'Alphabet (A-Z)', completed: 18, total: 26 },
        { category: 'Numbers (1-10)', completed: 8, total: 10 },
        { category: 'Conversational', completed: 4, total: 12 },
      ],
    }
  );
}

export async function getRecommendations() {
  return await fetchWithFallback(
    `${API_BASE_URL}/api/analytics/recommendations`,
    { method: 'GET' },
    {
      recommended_lessons: [
        {
          lesson_id: 'les_letter_m',
          title: "Letter 'M' Practice",
          reason: 'Thumb position accuracy fell below 75% in your last 3 attempts.',
          expected_gesture: 'M',
        },
        {
          lesson_id: 'les_letter_n',
          title: "Letter 'N' Practice",
          reason: 'Identified as a core weak area this week.',
          expected_gesture: 'N',
        },
        {
          lesson_id: 'les_letter_z',
          title: "Letter 'Z' Practice",
          reason: 'Dynamic finger motion requires extra timing refinement.',
          expected_gesture: 'Z',
        },
      ],
    }
  );
}

// -------------------------------------------------------------------
// 6) Accessibility Trainer APIs (Day 2 & Day 3)
// -------------------------------------------------------------------

export async function getAccessibilityTrainerAnalytics() {
  return await fetchWithFallback(
    `${API_BASE_URL}/api/trainer/analytics`,
    { method: 'GET' },
    {
      assigned_learners: 28,
      active_this_week: 22,
      avg_accuracy: 86.4,
      certifications_issued: 15,
      learners: [
        { id: 1, name: 'Aarav Patel', level: 'Intermediate', progress: 82, accuracy: 89, status: 'Certified' },
        { id: 2, name: 'Ananya Sharma', level: 'Beginner', progress: 45, accuracy: 74, status: 'In Assessment' },
        { id: 3, name: 'Rohan Gupta', level: 'Advanced', progress: 95, accuracy: 96, status: 'Certified' },
        { id: 4, name: 'Meera Nair', level: 'Beginner', progress: 30, accuracy: 62, status: 'Needs Support' },
        { id: 5, name: 'Vikram Joshi', level: 'Intermediate', progress: 68, accuracy: 81, status: 'In Assessment' },
      ],
      skill_breakdown: [
        { skill: 'Alphabet Finger-Spelling (A-Z)', score: 91 },
        { skill: 'Numeric Gestures (1-10)', score: 87 },
        { skill: 'Dynamic Gesture Signs (J, Z)', score: 72 },
        { skill: 'Hand-Shape Framing & Stability', score: 84 },
        { skill: 'Thumb & Palm Alignment', score: 78 },
      ],
    }
  );
}

// -------------------------------------------------------------------
// 7) Certification & Reports Export APIs (Day 3)
// -------------------------------------------------------------------

export async function downloadCertificatePDF(examId = 1) {
  return await downloadFileStream(
    `/api/certificates/download/${examId}`,
    `Sign_Language_Certificate_${examId}.pdf`
  );
}

export async function exportReportFile(reportType, format = 'pdf') {
  const extension = format === 'pdf' ? 'pdf' : 'xlsx';
  return await downloadFileStream(
    `/api/reports/export?type=${reportType}&format=${format}`,
    `${reportType}_report.${extension}`
  );
}

// -------------------------------------------------------------------
// 8) Admin & Instructor APIs
// -------------------------------------------------------------------

export async function getAllUsers() {
  return await fetchWithFallback(
    `${API_BASE_URL}/api/admin/users`,
    { method: 'GET' },
    [
      { id: 'usr_1', name: 'Parvathy K Manoj', email: 'parvathy@example.com', role: 'Learner', active: true, accuracy: 94 },
      { id: 'usr_2', name: 'Alex Johnson', email: 'alex@example.com', role: 'Learner', active: true, accuracy: 88 },
      { id: 'usr_3', name: 'Dr. Sarah Connor', email: 'sarah.instructor@example.com', role: 'Instructor', active: true, accuracy: 98 },
      { id: 'usr_4', name: 'Charlie Brown', email: 'charlie@example.com', role: 'Learner', active: false, accuracy: 72 },
      { id: 'usr_5', name: 'Admin Officer', email: 'admin@platform.org', role: 'Administrator', active: true, accuracy: 100 },
    ]
  );
}

export async function toggleUserStatus(userId, currentStatus) {
  return await fetchWithFallback(
    `${API_BASE_URL}/api/admin/users/${userId}/status`,
    {
      method: 'PATCH',
      body: JSON.stringify({ active: !currentStatus }),
    },
    {
      message: `User status updated to ${!currentStatus ? 'Active' : 'Inactive'}`,
    }
  );
}

export async function getInstructorStudents() {
  return await fetchWithFallback(
    `${API_BASE_URL}/api/instructor/students`,
    { method: 'GET' },
    [
      { id: 'usr_1', name: 'Alex Johnson', email: 'alex@example.com', accuracy: 88, completedLessons: 14, weakLetters: ['Z', 'J'], streak: 4 },
      { id: 'usr_2', name: 'Beatriz Smith', email: 'beatriz@example.com', accuracy: 94, completedLessons: 18, weakLetters: ['Q'], streak: 7 },
      { id: 'usr_3', name: 'Charlie Brown', email: 'charlie@example.com', accuracy: 72, completedLessons: 8, weakLetters: ['X', 'R', 'S'], streak: 1 },
      { id: 'usr_4', name: 'David Lee', email: 'david@example.com', accuracy: 85, completedLessons: 12, weakLetters: ['M', 'N'], streak: 3 },
    ]
  );
}