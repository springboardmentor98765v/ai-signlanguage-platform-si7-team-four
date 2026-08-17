# Backend Integration Notes - Milestone 3 (Day 9)

Cross-team contract for **Intern 1 (Frontend)** and **Intern 4 (Business Logic)**.
Every shape below was captured from the live backend on Day 9 (pytest suite: 84 passing).
The authoritative machine-readable source of truth is the OpenAPI spec at:

- Swagger UI: `http://127.0.0.1:8000/docs`
- Raw JSON:  `http://127.0.0.1:8000/openapi.json`

Conventions used everywhere in this repo:

- Auth tokens are returned as `access_token` (short-lived, default 30 min) and
  `refresh_token`. Protected endpoints expect the header
  `Authorization: Bearer <access_token>`.
- Admin endpoints verify privilege by the caller's **email** passed as a query
  parameter, e.g. `?admin_email=admin@example.com` (403 if the account is not `Admin`).
- Error bodies follow FastAPI's standard `{"detail": "..."}` for 4xx/5xx, EXCEPT rate
  limiting, which uses the dedicated 429 body below.
- IDs are UUIDs (strings). Always send/read them as strings.

---

## 1. Notifications (Intern 1: UI; Intern 4: emit events)

Three endpoints under `/api/notifications`.

### 1a. Create a notification - `POST /api/notifications`

Intended for service-to-service / server-side hooks (Intern 4). Internal event hooks
(`badge_earned`, `certificate_ready`, `new_recommendation`) should call the helper
`app/services/notification_service.py::create_notification(...)` directly instead of
this HTTP endpoint when running inside the backend process.

Request body (`Content-Type: application/json`):

```json
{
  "user_id": "5cabd7a4-fd5b-476c-9989-3e7c750b4dbf",
  "title": "Badge Earned",
  "message": "You correctly signed the letter 'A'.",
  "event_type": "badge_earned"
}
```

`event_type` must be one of: `badge_earned`, `certificate_ready`, `new_recommendation`,
`info` (default). `title`/`message` reject malicious/script payloads (400).

Success `201 Created`:

```json
{
  "id": "3e3796cb-51c6-4fdf-beac-ed25837f31c1",
  "user_id": "5cabd7a4-fd5b-476c-9989-3e7c750b4dbf",
  "title": "Badge Earned",
  "message": "You correctly signed the letter 'A'.",
  "event_type": "badge_earned",
  "is_read": false,
  "created_at": "2026-08-07T18:54:44.478441"
}
```

### 1b. List a user's notifications - `GET /api/notifications/{user_id}`

No auth header required. Newest first.

`200 OK` returns a JSON array (empty array `[]` when there are none):

```json
[
  {
    "id": "3e3796cb-51c6-4fdf-beac-ed25837f31c1",
    "user_id": "5cabd7a4-fd5b-476c-9989-3e7c750b4dbf",
    "title": "Badge Earned",
    "message": "You correctly signed the letter 'A'.",
    "event_type": "badge_earned",
    "is_read": false,
    "created_at": "2026-08-07T18:54:44.478441"
  }
]
```

### 1c. Mark as read - `PATCH /api/notifications/{notification_id}/read`

`200 OK` returns the updated notification with `"is_read": true` (same shape as above).
`404 {"detail": "Notification with id '<id>' not found."}` if the id does not exist.

---

## 2. Bulk user status (Intern 1: Admin UI)

`POST /api/admin/bulk-user-status?admin_email=<admin email>`

Request body (`Content-Type: application/json`). Each identifier is matched by UUID
first, then by email:

```json
{
  "user_ids": ["5cabd7a4-fd5b-476c-9989-3e7c750b4dbf", "someone@example.com"],
  "is_active": false
}
```

`200 OK`:

```json
{
  "message": "Bulk status update completed. Updated 1 user(s) to active=False.",
  "is_active": false,
  "updated_count": 1,
  "updated_user_ids": ["5cabd7a4-fd5b-476c-9989-3e7c750b4dbf"],
  "not_found": ["someone@example.com"],
  "not_found_count": 1
}
```

Errors: `403 {"detail": "Access denied. Admin privileges required."}` if
`admin_email` is not an Admin. No `400` here - unmatched ids simply appear in
`not_found` (never an exception).

Related single-user admin calls (Intern 1: Admin UI):

- `GET /api/admin/users?admin_email=<email>` -> array of user rows
  (`id, username, email, role, is_active, created_at`).
- `PATCH /api/admin/user-status?admin_email=<email>` body `{"target_email": "...", "is_active": true}` -> `{"message": "...", "email": "..."}`.
- `PATCH /api/admin/user-role?admin_email=<email>` body `{"target_email": "...", "new_role": "Instructor"}` -> `{"message": "...", "email": "..."}`.
  `new_role` must be one of `Learner`, `Instructor`, `Admin`.

---

## 3. Bulk upload lessons via CSV (Intern 1: Admin UI)

`POST /api/admin/bulk-upload-lessons?admin_email=<email>`

This is a **multipart form-data** request (NOT JSON), with a single field `file`:

- Header row (exact names, in this order): `title,description,expected_gesture,category,difficulty,module_id`
- `expected_gesture` max length 5 chars.
- `category` must be one of: `alphabet`, `general`, `greetings`, `numbers`, `phrases`, `words`.
- `difficulty` must be one of: `easy`, `medium`, `hard`.
- `module_id` must be a valid UUID.

Example CSV:

```csv
title,description,expected_gesture,category,difficulty,module_id
Sign Hello,Greeting gesture,HELLO,greetings,easy,9f7f2c5e-4b3a-4d6b-9f8e-1a2b3c4d5e6f
```

`200 OK` - every row is reported as inserted or rejected (never silently dropped):

```json
{
  "message": "CSV bulk upload complete: 1 lesson(s) inserted.",
  "rows_processed": 1,
  "rows_inserted": 1,
  "rows_rejected": 0,
  "rejected_rows": []
}
```

With rejected rows, `rejected_rows` carries the 1-based CSV line number and reason:

```json
{
  "message": "CSV bulk upload complete: 0 lesson(s) inserted.",
  "rows_processed": 2,
  "rows_inserted": 0,
  "rows_rejected": 2,
  "rejected_rows": [
    {
      "row": 1,
      "reason": "expected_gesture too long (8 > 5)"
    },
    {
      "row": 2,
      "reason": "missing title; category 'badgesture' not in allowed set: ['alphabet', 'general', 'greetings', 'numbers', 'phrases', 'words']"
    }
  ]
}
```

`400 {"detail": "CSV is missing required column(s): [...] Expected: [...]"}` if the
header row is wrong. `403` if `admin_email` is not an Admin.

> Alternative (simpler for a text payload): `POST /api/lessons/bulk-upload-csv` takes a
> JSON body `{"csv_content": "<csv string>"}` and inserts into the in-memory lessons
> catalog used by `GET /api/lessons`. Different header set:
> `module_id,title,content_description,expected_gesture,category,difficulty`.

---

## 4. Rate-limit 429 responses (all clients)

Register, login, and forgot-password are rate limited to **5 requests per minute per
email**. When exceeded, the backend returns `429 Too Many Requests` with a custom body
and a `Retry-After` header (seconds):

```json
{
  "message": "Too many requests. Please slow down and try again shortly.",
  "error": "rate_limit_exceeded",
  "detail": "Too many login attempts for this account. Please wait a minute and try again.",
  "retry_after_seconds": 59
}
```

HTTP headers:

```
HTTP/1.1 429 Too Many Requests
Retry-After: 59
```

Frontend guidance: on `429`, surface the `message` and disable the submit button for
`retry_after_seconds` (from body or `Retry-After` header). Use distinct user emails in
tests/integration to avoid tripping the per-email limit.

---

## Appendix - auth flow (needed to call the above)

`POST /api/auth/register` body `{"username": "...", "email": "...", "password": "...", "role": "Learner"}`
-> `201 {"message": "...", "user_id": "<uuid>", "role": "Learner"}`.

`POST /api/auth/login` body `{"email": "...", "password": "..."}` -> `200`:

```json
{
  "message": "Login successful.",
  "access_token": "<jwt>",
  "refresh_token": "<jwt>",
  "token_type": "bearer",
  "user": {
    "user_id": "5cabd7a4-fd5b-476c-9989-3e7c750b4dbf",
    "username": "alice",
    "role": "Learner"
  }
}
```

`POST /api/auth/refresh-token` body `{"refresh_token": "<jwt>"}` ->
`200 {"access_token": "<new jwt>", "token_type": "bearer", "message": "Session successfully extended."}`.
Use `401` handling for expired/invalid refresh tokens.
