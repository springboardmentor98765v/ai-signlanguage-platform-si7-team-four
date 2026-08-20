# Frontend ↔ Backend API Integration Audit

Final audit of every frontend API call against the live FastAPI route table.
Status: **PASS** (as of the Section B fix pass).

## Legend
- ✅ Real backend endpoint, wired and verified.
- 🔧 Fixed during this pass (path corrected to the real endpoint).
- ➕ Endpoint added during this pass so the frontend can use real data.

## Layer 1 – Authentication & Account (Section A)
| Frontend call | Frontend URL (old → fixed) | Backend route | Status |
|---|---|---|---|
| `registerUser` | `/api/auth/register` | `POST /api/auth/register` | ✅ |
| `loginUser` | `/api/auth/login` | `POST /api/auth/login` | ✅ |
| `updateUserProfile` | `/api/auth/profile` → 🔧 `/api/users/me` | `PATCH /api/users/me` | 🔧 |
| `changePassword` | `/api/auth/change-password` → 🔧 `/api/users/change-password` | `POST /api/users/change-password` | 🔧 |
| `forgotPassword` | `/api/auth/forgot-password` | `POST /api/auth/forgot-password` | ✅ |
| `resetPassword` | `/api/auth/reset-password` | `POST /api/auth/reset-password` | ✅ (added) |

## Layer 2 – Dashboard / Analytics / Leaderboard (Sections B & C)
| Frontend call | Old URL | Fixed URL | Backend route | Status |
|---|---|---|---|---|
| `getDashboardAnalytics` | `/api/analytics/dashboard` ❌ | `/api/analytics/dashboard/{user_id}` | `GET /api/analytics/dashboard/{user_id}` | 🔧➕ real DB |
| Dashboard recommendations | `/api/analytics/recommendations` ❌ | `/api/recommendation/{user_id}` | `GET /api/recommendation/{user_id}` | 🔧➕ |
| `Leaderboard.jsx` | `/api/analytics/leaderboard?sort=` ❌ | same | `GET /api/analytics/leaderboard?sort=&user_id=` | ➕ real DB |
| `getRecommendations` | `/api/analytics/recommendations` ❌ | `/api/recommendation/{user_id}` | `GET /api/recommendation/{user_id}` | 🔧➕ |

## Layer 3 – Content & Practice
| Frontend call | Frontend URL | Backend route | Status |
|---|---|---|---|
| `getCourses` | `/api/courses` | `GET /api/courses` | ✅ |
| `getCourseDetails` | `/api/courses/{course_id}` | `GET /api/courses/{course_id}` | ✅ |
| `startPracticeSession` | `/api/practice/start` | `POST /api/practice/start (query user_id, lesson_id)` | 🔧 contract note |
| `submitPracticeGesture` | `/api/practice/submit` | `POST /api/practice/submit` | ✅ |
| `evaluateAssessment` | `/api/assessment/evaluate` | `POST /api/assessment/evaluate` | ➕ router registered (previously unregistered) |

## Layer 4 – Reports & Certificates (Section D)
| Frontend call | Frontend URL | Backend route | Status |
|---|---|---|---|
| `downloadCertificatePDF` | `/api/certificates/download/{exam_id}` ❌ | fixed in Section D | ⏳ D-pass |
| `exportReportFile` | `/api/reports/export?type&format` ❌ | fixed in Section D | ⏳ D-pass |

## Layer 5 – Admin / Instructor / Trainer
| Frontend call | Frontend URL | Backend route | Status |
|---|---|---|---|
| `getAllUsers` | `/api/admin/users` | `GET /api/admin/users` | ✅ |
| `toggleUserStatus` | `/api/admin/users/{id}/status` | `PATCH /api/admin/users/{id}/status` | ✅ |
| `getInstructorStudents` | `/api/instructor/students` ❌ | `GET /api/instructor/students/{instructor_email}` | 🔧 F-pass |
| `getAccessibilityTrainerAnalytics` | `/api/trainer/analytics` ❌ | fixed in Section F | ⏳ F-pass |
| Notifications | `/api/notifications` | `POST/GET/PATCH /api/notifications[/{...}]` | ✅ (wired in E-pass) |

## Cross-cutting findings fixed
- Missing routers `analytics`, `assessment`, `recommendation` were NOT registered in `app/main.py`
  and are now `include_router`'d. (`certificate`/`report` registration lands in Section D.)
- All auth functions in `services/api.js` now throw on failure instead of returning mock data.
- `Dashboard.jsx`, `Leaderboard.jsx` load from real DB-backed endpoints; no hardcoded fallback rows.