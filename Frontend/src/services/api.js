// Centralized API Service for AI Sign Language Platform.
// Connects to the FastAPI backend via a single configurable base URL.
// All functions call the real backend and throw on any failure — there is
// no offline/mock fallback data anywhere in this module.

// VITE_API_URL always wins. In local dev we default to same-origin (the Vite
// dev server proxies /api to the local backend), so the site works even when
// the browser cannot resolve external hosts; production builds default to the
// deployed Render backend.
export const API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  (import.meta.env.DEV ? '' : 'https://signlang-backend-6epi.onrender.com');

const getAuthHeaders = (extra = {}) => {
  const token = localStorage.getItem('access_token');
  return {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
    ...extra,
  };
};

/**
 * Generic JSON fetcher for live backend endpoints. Throws on non-2xx.
 */
export async function apiRequest(endpoint, options = {}) {
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;
  const res = await fetch(url, {
    ...options,
    headers: getAuthHeaders(options.headers || {}),
  });

  if (!res.ok) {
    const errorText = await res.text();
    let errorJson = {};
    try { errorJson = JSON.parse(errorText); } catch (_) {}
    throw new Error(errorJson.message || errorJson.detail || `Server returned status ${res.status}`);
  }

  if (res.status === 204) return null;
  return await res.json();
}

/**
 * Binary stream downloader (PDF/Excel exports). Throws on failure.
 */
export async function downloadFileStream(endpoint, defaultFilename) {
  const fullUrl = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;
  const token = localStorage.getItem('access_token');

  const response = await fetch(fullUrl, {
    method: 'GET',
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    let errorJson = {};
    try { errorJson = JSON.parse(errorText); } catch (_) {}
    throw new Error(errorJson.detail || errorJson.message || `File stream failed with HTTP status ${response.status}`);
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
}

// -------------------------------------------------------------------
// 1) Authentication & User APIs
// -------------------------------------------------------------------

export async function registerUser({ username, email, password, role }) {
  return await apiRequest('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify({ username, email, password, role: role || 'Learner' }),
  });
}

export async function loginUser({ email, password }) {
  const data = await apiRequest('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  if (!data.access_token || !data.user) {
    throw new Error('Invalid login response from server.');
  }
  return data;
}

export async function updateUserProfile(profileData) {
  return await apiRequest('/api/users/me', {
    method: 'PATCH',
    body: JSON.stringify(profileData),
  });
}

export async function changePassword({ oldPassword, newPassword }) {
  return await apiRequest('/api/users/change-password', {
    method: 'POST',
    body: JSON.stringify({ current_password: oldPassword, new_password: newPassword }),
  });
}

export async function forgotPassword(email) {
  return await apiRequest('/api/auth/forgot-password', {
    method: 'POST',
    body: JSON.stringify({ email }),
  });
}

export async function resetPassword(token, newPassword) {
  return await apiRequest('/api/auth/reset-password', {
    method: 'POST',
    body: JSON.stringify({ token, new_password: newPassword }),
  });
}

// -------------------------------------------------------------------
// 2) Course & Lesson Service Endpoints
// -------------------------------------------------------------------

export async function getCourses() {
  const data = await apiRequest('/api/courses', { method: 'GET' });
  return data.courses || data || [];
}

export async function getCourseModules() {
  const data = await apiRequest('/api/courses/modules', { method: 'GET' });
  return Array.isArray(data) ? data : data.modules || [];
}

export async function getCourseDetails(courseId) {
  return await apiRequest(`/api/courses/${encodeURIComponent(courseId)}`, { method: 'GET' });
}

// -------------------------------------------------------------------
// 3) Practice & Gesture Submissions
// -------------------------------------------------------------------

export async function startPracticeSession({ userId, lessonId }) {
  const params = new URLSearchParams();
  if (userId) params.set('user_id', userId);
  if (lessonId) params.set('lesson_id', lessonId);
  return await apiRequest(`/api/practice/start?${params.toString()}`, { method: 'POST' });
}

export async function endPracticeSession(sessionId) {
  return await apiRequest(`/api/practice/end?session_id=${encodeURIComponent(sessionId)}`, { method: 'POST' });
}

export async function submitPracticeGesture({ userId, lessonId, sessionId, targetLetter, imageData }) {
  return await apiRequest('/api/practice/submit', {
    method: 'POST',
    body: JSON.stringify({
      user_id: userId,
      lesson_id: lessonId,
      session_id: sessionId,
      target_letter: targetLetter,
      image_data: imageData,
    }),
  });
}

export async function evaluateSignDay3({ sign, image_base64 }) {
  return await apiRequest('/api/v1/day3/evaluate-sign', {
    method: 'POST',
    body: JSON.stringify({ sign, image_base64 }),
  });
}

// -------------------------------------------------------------------
// 4) Accessibility Trainer APIs
// -------------------------------------------------------------------

export async function getTrainerLearners() {
  return await apiRequest('/api/trainer/learners', { method: 'GET' });
}

export async function getLearnerTrainerDetail(learnerId, metricType) {
  return await apiRequest(
    `/api/trainer/learners/${encodeURIComponent(learnerId)}/${encodeURIComponent(metricType)}`,
    { method: 'GET' }
  );
}

export async function getAccessibilityTrainerAnalytics() {
  return await apiRequest('/api/trainer/analytics', { method: 'GET' });
}

// -------------------------------------------------------------------
// 5) Analytics, Dashboard & Recommendations
// -------------------------------------------------------------------

export async function getDashboardAnalytics(userId) {
  if (!userId) {
    throw new Error('Cannot load dashboard: missing user id.');
  }
  return await apiRequest(`/api/analytics/dashboard/${encodeURIComponent(userId)}`, { method: 'GET' });
}

export async function getLearnerAnalyticsSummary(userId) {
  if (!userId) {
    throw new Error('Cannot load learner analytics: missing user id.');
  }
  return await apiRequest(`/api/analytics/${encodeURIComponent(userId)}`, { method: 'GET' });
}

export async function getRecommendations(userId) {
  if (!userId) {
    throw new Error('Cannot load recommendations: missing user id.');
  }
  return await apiRequest(`/api/recommendation/${encodeURIComponent(userId)}`, { method: 'GET' });
}

// -------------------------------------------------------------------
// 6) Notifications
// -------------------------------------------------------------------

export async function getMyNotifications(userId) {
  if (!userId) {
    throw new Error('Cannot load notifications: missing user id.');
  }
  return await apiRequest(`/api/notifications/${encodeURIComponent(userId)}`, { method: 'GET' });
}

export async function markNotificationRead(notificationId) {
  return await apiRequest(`/api/notifications/${encodeURIComponent(notificationId)}/read`, { method: 'PATCH' });
}

// -------------------------------------------------------------------
// 7) Certification & Reports Export APIs
// -------------------------------------------------------------------

/**
 * Issues (or returns the already-issued) certificate for a completed task.
 * Requires score >= the backend threshold; throws with the server's message
 * otherwise.
 */
export async function issueTaskCertificate({ lessonId, score }) {
  return await apiRequest('/api/certificates/issue', {
    method: 'POST',
    body: JSON.stringify({ lesson_id: lessonId || null, score }),
  });
}

/**
 * Downloads a certificate as 'pdf' or 'excel'. Returns true on success.
 */
export async function downloadCertificateFile(certificateId, format = 'pdf') {
  const extension = format === 'excel' ? 'xlsx' : 'pdf';
  return await downloadFileStream(
    `/api/certificates/${certificateId}/download?format=${format}`,
    `Sign_Language_Certificate_${String(certificateId).slice(0, 8)}.${extension}`
  );
}

export async function downloadCertificatePDF(certificateId) {
  return await downloadCertificateFile(certificateId, 'pdf');
}

export async function getMyCertificates() {
  const data = await apiRequest('/api/certificates/my-certificates', { method: 'GET' });
  return data?.certificates || [];
}

export async function exportReportFile(reportType, format = 'pdf') {
  const extension = format === 'pdf' ? 'pdf' : 'xlsx';
  return await downloadFileStream(
    `/api/reports/${encodeURIComponent(reportType)}/export?format=${format}`,
    `${reportType}_report.${extension}`
  );
}

// -------------------------------------------------------------------
// 8) Admin & Instructor APIs
// -------------------------------------------------------------------

export async function getAllUsers() {
  return await apiRequest('/api/admin/users', { method: 'GET' });
}

export async function toggleUserStatus(userId, currentStatus) {
  return await apiRequest(`/api/admin/users/${encodeURIComponent(userId)}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ active: !currentStatus }),
  });
}

export async function getInstructorStudents(instructorEmail) {
  return await apiRequest(
    `/api/instructor/students/${encodeURIComponent(instructorEmail)}`,
    { method: 'GET' }
  );
}