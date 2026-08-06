# Day 2 Task & Checkpoints Checklist - Backend (Milestone 3)

## Task Overview
> **Day 2 Description:**
> Build the Notification system: a database table (with Intern 5) to store notifications, and simple APIs to create a notification, list a user's notifications, and mark one as read.

---

## Checkpoints Status

- [x] **Notifications table created (with Intern 5)**
  - `Notification` SQLAlchemy model added to [`Backend/app/models/models.py`](Backend/app/models/models.py)
  - Table name: `notifications`
  - Columns: `id` (PK, UUID string), `user_id`, `title`, `message`, `notification_type`, `is_read` (bool), `created_at` (DateTime)
  - Table is auto-created on app startup via `Base.metadata.create_all(bind=engine)` in `main.py`
  - Implemented in collaboration with Intern 5 (Database/DevOps)

- [x] **'Create notification' API working**
  - Endpoint: `POST /api/notifications`
  - Accepts: `user_id`, `title`, `message`, `notification_type` (info/success/warning/alert)
  - Saves new notification to the `notifications` database table
  - Returns the full notification record with generated `id` and `created_at`
  - Input validation: rejects empty `user_id` or `title` with 400 error

- [x] **'Get my notifications' API working**
  - Endpoint: `GET /api/notifications/me?user_id={user_id}`
  - Returns only the authenticated user's notifications from the database
  - Supports: `unread_only=true` filter, `skip` and `limit` pagination
  - Results ordered by newest first
  - Returns empty list (not error) for unknown users

- [x] **'Mark as read' API working**
  - Endpoint: `PATCH /api/notifications/{notification_id}/read`
  - Updates `is_read = True` in the database for the specified notification
  - Idempotent: safe to call multiple times, returns success each time
  - Returns 404 for non-existent notification IDs

---

## Additional Supporting Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `GET /api/notifications/unread-count` | GET | Unread badge count for a user |
| `DELETE /api/notifications/{id}` | DELETE | Permanently delete a notification |

---

## Files Changed / Added

| File | Change Type | Description |
|---|---|---|
| `Backend/app/models/models.py` | Modified | Added `Notification` SQLAlchemy DB model (the table) |
| `Backend/app/routers/notification_router.py` | Modified | Replaced in-memory storage with real DB operations |
| `Backend/app/main.py` | Modified | Updated milestone tracker to Day 2 |
| `Backend/test_milestone3_day2.py` | New | Full pytest test suite for all 4 Day 2 checkpoints |
| `Backend/DAY2_CHECKPOINTS.md` | New | This checkpoint tracking document |

---

## How to Verify

Run the Day 2 test suite:

```bash
pytest Backend/test_milestone3_day2.py -v
```

Or run the full backend test suite:

```bash
pytest Backend/ -v
```

**Expected result:** All tests pass (green).
