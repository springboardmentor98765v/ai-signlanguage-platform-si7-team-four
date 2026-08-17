# API Reference — AI Sign Language Platform (Milestone 4, Day 3)

Postman-collection stand-in. Captured **live** from `http://127.0.0.1:8000/openapi.json`
on **Day 3 of Milestone 4**: **50 paths / 65 operations**, all covered by
`Backend/test_full_api_pass.py` (109 tests green).

- Swagger UI: `http://127.0.0.1:8000/docs`
- Raw OpenAPI: `http://127.0.0.1:8000/openapi.json`

## Conventions used by every endpoint

- **Auth**: Bearer JWT in `Authorization: Bearer <access_token>`. Register/login
  return short-lived `access_token` + long-lived `refresh_token`.
- **Roles** (RBAC via `verify_token_and_role`): `Learner`, `Instructor`,
  `Accessibility Trainer`, `Admin`. Missing/invalid token → `401`; present token but
  wrong role → `403`, body `{"detail": "..."}`.
- **Admin endpoints do NOT use JWT**: they verify the caller by `admin_email` query
  param (the account must have role `Admin`, else `403`).
- **Error body** (4xx/5xx): `{"detail": "..."}`. **Unique exception: rate limiting**
  returns `429` with `{"message", "error", "detail", "retry_after_seconds"}` + `Retry-After` header.
- **Rate limits**: `/api/auth/register`, `/api/auth/login`, `/api/auth/forgot-password`
  limited to **5/min per email** (429 on exceed).
- **IDs**: modern endpoints use UUID **strings**. Legacy `v1` mock endpoints use
  **integer** user ids — keep them ints when calling `v1` endpoints.
- **Timestamps**: ISO 8601 strings (serialized `datetime`).
- **Malicious-input guard**: title/comment/text fields run `reject_malicious` →
  `422` on script/SQL payloads.

---

## 1. System Health & Status

| Method | Path | Auth | Roles |
|---|---|---|---|
| GET | `/` | No | – |
| GET | `/health` | No | – |

- `GET /` → `200` `{"message": "...", "milestone_tracker": {...}}`
- `GET /health` → `200` `{"status": "healthy", "env_loaded": bool, "api_status": "...", "milestone_tracker": {...}}`

---

## 2. Authentication

| Method | Path | Auth | Roles |
|---|---|---|---|
| POST | `/api/auth/register` | No | – (rate-limited) |
| POST | `/api/auth/login` | No | – (rate-limited) |
| POST | `/api/auth/refresh-token` | No | – |
| POST | `/api/auth/forgot-password` | No | – (rate-limited) |
| GET | `/api/auth/dashboard/learner` | Bearer | `Learner`, `Admin` |
| GET | `/api/auth/dashboard/instructor` | Bearer | `Instructor`, `Admin` |

### POST /api/auth/register → `201`
Request `{"username": "...", "email": "...", "password": "...", "role": "Learner"}`
(`role` optional, default `Learner`, must be in allowed set).
Response `{"message": "User registered successfully.", "user_id": "<uuid>", "role": "..."}`.
Errors: `400` duplicate email, `422` validation, `429` rate limit.

### POST /api/auth/login → `200`
Request `{"email": "...", "password": "..."}`.
Response:
```json
{
  "message": "Login successful.",
  "access_token": "<jwt>", "refresh_token": "<jwt>", "token_type": "bearer",
  "user": {"user_id": "<uuid>", "username": "...", "role": "..."}
}
```
Errors: `401` wrong creds, `429` rate limit.

### POST /api/auth/refresh-token → `200`
Request `{"refresh_token": "<jwt>"}`.
Response `{"access_token": "<jwt>", "token_type": "bearer", "message": "Session successfully extended."}`.
Errors: `401` missing/expired/malformed.

### POST /api/auth/forgot-password → `200`
Request `{"email": "..."}`. Response `{"message": "Password reset link generated and printed to server terminal."}`.
Errors: `404` unknown email, `429` rate limit.

### GET /api/auth/dashboard/learner → `200`
`{"message": "Welcome ...", "accuracy_metric_stub": "91%", "lessons_completed_stub": 18}`. `403` for non-Learner/Admin.

### GET /api/auth/dashboard/instructor → `200`
`{"message": "...", "class_performance_average_stub": "84.5%"}`. `403` for non-Instructor/Admin.

---

## 3. Day 2 Milestone 2 — Profile

| Method | Path | Auth | Roles |
|---|---|---|---|
| PATCH | `/api/users/me` | No | – (acts on first user row) |
| POST | `/api/users/change-password` | No | – (acts on first user row) |

### PATCH /api/users/me → `200`
Request `{"username"?, "email"?}`. Response `{"message": "Profile updated successfully", "username": "...", "email": "..."}`.
> Note: targets `db.query(User).first()` — the oldest user row, not the caller.

### POST /api/users/change-password → `200`
Request `{"current_password", "new_password"}` (min 8 chars). Response `{"message": "Password changed successfully"}`.
> Note: stores `new_password` as provided (plaintext).

---

## 4. Lessons Service

| Method | Path | Auth | Roles |
|---|---|---|---|
| GET | `/api/lessons` | No | – |
| GET | `/api/lessons/advanced` | No | – |
| POST | `/api/lessons/bulk-upload-csv` | No | – |
| GET | `/api/lessons/{lesson_id}` | No | – |
| POST | `/api/lessons` | Bearer | `Instructor`, `Admin` |
| PUT | `/api/lessons/{lesson_id}` | Bearer | `Instructor`, `Admin` |
| DELETE | `/api/lessons/{lesson_id}` | Bearer | `Instructor`, `Admin` |

**LessonResponse** shape: `{"lesson_id", "module_id", "title", "content_description", "expected_gesture", "category", "difficulty"}`.

- `GET /api/lessons?skip=0&limit=10&search=` → `200` `{"skip", "limit", "total", "data": [LessonResponse]}`.
- `GET /api/lessons/advanced` → `200` `{"count", "advanced_lessons": [{...lesson record...}]}`.
- `GET /api/lessons/{lesson_id}` → `200` LessonResponse; `404` unknown id.
- `POST /api/lessons/bulk-upload-csv` body `{"csv_content": "<csv>"}` →
  `201` `{"message", "created_count", "created_lessons", "errors"}`. Header:
  `module_id,title,content_description,expected_gesture,category,difficulty`.
- `POST /api/lessons` body `{"module_id", "title", "content_description"?, "expected_gesture" (≤5 chars), "category"?, "difficulty"?}` → `201` LessonResponse. `403` wrong role.
- `PUT /api/lessons/{lesson_id}` same body → `200` LessonResponse; `404` unknown id.
- `DELETE /api/lessons/{lesson_id}` → `200` `{"message": "..."}`; `404` unknown id.

---

## 5. Course Service

| Method | Path | Auth | Roles |
|---|---|---|---|
| GET | `/api/courses/modules` | No | – |
| GET | `/api/courses/modules/{module_id}/lessons` | No | – |
| POST | `/api/courses/modules` | Bearer | `Instructor`, `Admin` |

- `GET /api/courses/modules` → `200` array of `{"module_id", "course_id", "title", "description", "lessons": [{"lesson_id", "module_id", "title", "content_description", "expected_gesture"}]}`.
- `GET /api/courses/modules/{module_id}/lessons` → `200` array; `404` unknown module.
- `POST /api/courses/modules` body `{"title", "description", "course_id"}` → `201` `{"module_id" (=course_id), "course_id", "title", "description", "lessons": []}`. `403` wrong role.

---

## 6. Admin Management (`?admin_email=<email>` required unless noted)

| Method | Path | Auth |
|---|---|---|
| GET | `/api/admin/users?admin_email=` | email RBAC |
| PATCH | `/api/admin/user-status?admin_email=` | email RBAC |
| PATCH | `/api/admin/user-role?admin_email=` | email RBAC |
| DELETE | `/api/admin/users/{user_id}?admin_email=` | email RBAC (param optional) |
| POST | `/api/admin/users/bulk-delete?admin_email=` | email RBAC (param optional) |
| PATCH | `/api/admin/users/bulk-status?admin_email=` | email RBAC (param optional) |
| PATCH | `/api/admin/users/bulk-role?admin_email=` | email RBAC (param optional) |
| POST | `/api/admin/bulk-user-status?admin_email=` | email RBAC |
| POST | `/api/admin/bulk-upload-lessons?admin_email=` | email RBAC (multipart) |

Common error: `403 {"detail": "Access denied. Admin privileges required."}` when `admin_email` is not an Admin.

**User row** shape: `{"id", "username", "email", "role", "is_active", "created_at"}`.

- `GET /api/admin/users` → `200` array of user rows.
- `PATCH /api/admin/user-status` body `{"target_email", "is_active"}` → `200` `{"message", "email"}`; `404` target not found.
- `PATCH /api/admin/user-role` body `{"target_email", "new_role"∈{Learner, Instructor, Accessibility Trainer, Admin}}` → `200` `{"message", "email"}`; `404` target.
- `DELETE /api/admin/users/{user_id}` → `200` `{"message": "User <id> deleted successfully."}`; `404` not found.
- `POST /api/admin/users/bulk-delete` body `{"user_ids": ["<uuid>", ...]}` → `200` `{"message", "deleted_count", "not_found_ids": [...]}`.
- `PATCH /api/admin/users/bulk-status` body `{"user_ids", "is_active"}` → `200` `{"message", "updated_count"}`.
- `PATCH /api/admin/users/bulk-role` body `{"user_ids", "new_role"}` → `200` `{"message", "updated_count"}`.
- `POST /api/admin/bulk-user-status` body `{"user_ids": ["<uuid>" | "<email>", ...], "is_active"}` →
  `200` `{"message", "is_active", "updated_count", "updated_user_ids", "not_found", "not_found_count"}`.
- `POST /api/admin/bulk-upload-lessons` — **multipart form-data**, field `file` (CSV). Header:
  `title,description,expected_gesture,category,difficulty,module_id` (`module_id` must be a valid UUID).
  → `200` `{"message", "rows_processed", "rows_inserted", "rows_rejected", "rejected_rows": [{"row", "reason"}]}`;
  `400` when required columns are missing.

---

## 7. Instructor-Student Management

| Method | Path | Auth |
|---|---|---|
| POST | `/api/instructor/assign-student` | No |
| GET | `/api/instructor/students/{instructor_email}` | No |

- `POST /api/instructor/assign-student` body `{"instructor_email", "student_email"}` →
  `200` `{"message", "instructor", "student"}`; `404` instructor not found / not an instructor / student not found.
- `GET /api/instructor/students/{instructor_email}` →
  `200` `{"instructor_email", "total_students", "students": [{"student_id", "username", "email", "progress_summary": {"lessons_completed", "average_accuracy", "status"}}]}`; `404` instructor not found.

---

## 8. Notifications

| Method | Path | Auth |
|---|---|---|
| POST | `/api/notifications` | No |
| GET | `/api/notifications/{user_id}` | No |
| PATCH | `/api/notifications/{notification_id}/read` | No |

**NotificationOut**: `{"id", "user_id", "title", "message", "event_type", "is_read", "created_at"}`.

- `POST /api/notifications` body `{"user_id", "title", "message", "event_type"?}` (`event_type` ∈
  `info`, `badge_earned`, `certificate_ready`, `new_recommendation`) → `200/201` NotificationOut.
- `GET /api/notifications/{user_id}` → `200` array of NotificationOut (newest first).
- `PATCH /api/notifications/{notification_id}/read` → `200` updated NotificationOut (`is_read: true`); `404` unknown id.

---

## 9. Practice Service

| Method | Path | Auth |
|---|---|---|
| POST | `/api/practice/start` | No |
| POST | `/api/practice/submit` | No |
| POST | `/api/practice/end` | No |

- `POST /api/practice/start?user_id=<uuid>&lesson_id=<uuid>` → `200` `{"session_id", "user_id", "lesson_id", "status": "in_progress", "attempt_count", "start_time", "end_time", "duration_seconds"}`.
- `POST /api/practice/submit` body `{"session_id"?, "user_id"?, "lesson_id"?, "target_letter"?, "image_data"}` —
  either `session_id` or both `user_id`+`lesson_id` required. `image_data` is a base64 **data URL**
  (`data:image/jpeg;base64,...`). Backend decodes → forwards multipart to the AI service
  (`POST {AI_SERVICE_URL}/predict`, default `http://ai-service:8001`) →
  `200` `{"status": "success", "session_id", "predicted_sign", "confidence", "hand_detected", "correct", "possible_issue"}`.
  Errors: `400` bad base64 / missing ids, `404` unknown session, `502` AI service unreachable.
- `POST /api/practice/end?session_id=<uuid>` → `200` `{"session_id", "status": "completed", "attempt_count", "start_time", "end_time", "duration_seconds"}`; `404` unknown session.

---

## 10. Accessibility Trainer (M4 — all Bearer + role `Accessibility Trainer`)

| Method | Path | Roles |
|---|---|---|
| GET | `/api/trainer/learners` | `Accessibility Trainer` |
| POST | `/api/trainer/assign-learner` | `Accessibility Trainer` |
| GET | `/api/trainer/learners/{learner_id}/engagement` | `Accessibility Trainer` + assigned |
| GET | `/api/trainer/learners/{learner_id}/skill-development` | `Accessibility Trainer` + assigned |
| GET | `/api/trainer/learners/{learner_id}/assessment-analytics` | `Accessibility Trainer` + assigned |
| GET | `/api/trainer/learners/{learner_id}/certification-status` | `Accessibility Trainer` + assigned |

Common errors: `401` no token, `403` wrong role or learner not assigned to this trainer, `404` learner not found.

- `GET /api/trainer/learners` → `200` array of `{"learner_id", "username", "email", "role", "assigned_at"}`.
- `POST /api/trainer/assign-learner` body `{"learner_id"? | "learner_email"?}` →
  `200` `{"message", "trainer_id", "learner_id"}` (idempotent). Errors: `400` neither id nor email / target not a Learner / self-assign; `404` learner not found.
- `GET /api/trainer/learners/{learner_id}/engagement` → `200` `{"learner_id", "engagement_score", "sessions_total", "sessions_completed", "total_attempts", "total_practice_minutes", "last_practiced_at", "formula_owner"}`.
- `GET .../skill-development` → `200` `{"learner_id", "improvement_rate", "trend": [{"week_start", "average_accuracy"}], "weak_letters": [...], "formula_owner"}`.
- `GET .../assessment-analytics` → `200` `{"learner_id", "total_assessments", "average_accuracy", "average_confidence", "correct_count", "correct_percentage", "per_letter": [{"letter", "attempts", "correct", "accuracy"}], "formula_owner"}`.
- `GET .../certification-status` → `200` `{"learner_id", "status" ("passed"/"in_progress"/"not_passed"/"not_attempted"), "level", "overall_score", "certificate_issued_date", "formula_owner"}`.

All metric formulas are placeholders pending Intern 4 (`"formula_owner": "Intern 4 (pending)"`).

---

## 11. v1 Community Feedback

| Method | Path |
|---|---|
| POST | `/api/v1/feedback/submit` |
| GET | `/api/v1/feedback/all` |

- `POST /api/v1/feedback/submit` body `{"user_id": <int>, "category", "rating": 1–5, "comments"}` → `201` `{"id", "user_id", "category", "rating", "comments", "submitted_at" (ISO)}`.
- `GET /api/v1/feedback/all` → `200` array of the shape above.

---

## 12. v1 Translation History & Logs

| Method | Path |
|---|---|
| GET | `/api/v1/translations/history/{user_id}` |
| POST | `/api/v1/translations/log` |

- `GET /api/v1/translations/history/{user_id<int>}` → `200` array of `{"id", "user_id", "translated_text", "confidence_level", "timestamp" (ISO)}`.
- `POST /api/v1/translations/log` body `{"user_id": <int>, "translated_text", "confidence_level": 0–1}` → `200` same shape; `400` out-of-range confidence.

---

## 13. v1 Progress & Analytics

| Method | Path |
|---|---|
| GET | `/api/v1/progress/user/{user_id}` |
| POST | `/api/v1/progress/update` |

- `GET /api/v1/progress/user/{user_id<int>}` → `200` array of `{"id", "user_id", "course_id", "completed_lessons", "total_lessons", "accuracy_score", "last_updated" (ISO)}`.
- `POST /api/v1/progress/update` body `{"user_id": <int>, "course_id": <int>, "completed_lessons", "total_lessons", "accuracy_score": 0–100}` → `200` same shape; `400` out-of-range accuracy.

---

## 14. v1 Sign Dictionary & Vocabulary

| Method | Path |
|---|---|
| GET | `/api/v1/dictionary/signs` |
| GET | `/api/v1/dictionary/signs/{sign_id}` |

Sign shape: `{"id", "sign_name", "category", "difficulty_level", "description", "video_url"}`.

- `GET /api/v1/dictionary/signs?search=` → `200` array of signs (filter by name/category).
- `GET /api/v1/dictionary/signs/{sign_id<int>}` → `200` single sign; `404` `{"detail": "Sign entry not found in the dictionary."}`.

---

## 15. v1 Day 3 Core Features

| Method | Path |
|---|---|
| POST | `/api/v1/day3/evaluate-sign` |
| POST | `/api/v1/day3/upload-gesture-frame` |

- `POST /api/v1/day3/evaluate-sign` body `{"sign_text", "user_id": <int>}` →
  `200` `{"success": true, "confidence_score", "matched_sign", "message"}`; `400` empty sign text.
- `POST /api/v1/day3/upload-gesture-frame` — **multipart**, field `file` (png/webm/mp4) →
  `200` `{"filename", "status": "Uploaded and queued for MediaPipe landmark processing", "saved_path"}`; `500` save failure.

---

## 16. Team Integration Testing

| Method | Path |
|---|---|
| POST | `/api/integration/test-sync` |

Request accepts **both** casings (aliases) — `{"user_id" | "userId", "action_type" | "actionType", "confidence_score" | "confidenceScore"}` →
`200` `{"status": "success", "message": "...", "received_data": {"user_id", "action_type", "confidence_score"}}`.
The response is always **snake_case** to match the rest of the API.

---

## Behavioral notes

- `PATCH /api/users/me` and `POST /api/users/change-password` target the **first user row** in the DB (no auth scoping) — legacy M2 behavior.
- `change-password` stores the new password as-is; bcrypt verification for that account is then invalid.
- All `v1` mock endpoints use **integer** user ids; every modern endpoint uses **UUID strings**.
- `/api/practice/submit` depends on the AI service; without it the endpoint returns `502`.
- Trainer analytics formulas are Intern-4-owned placeholders (field `formula_owner`).