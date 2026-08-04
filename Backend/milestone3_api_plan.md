# Milestone 3 - Day 1 Backend API Specification & Milestone Review Plan

## 1. Executive Summary & Audit of Milestone 1 & 2 APIs
As part of the Day 1 "Stock Check", all APIs built across Milestone 1 and Milestone 2 were audited, re-tested, and verified for baseline compatibility:

| Component | Endpoints | Status |
| :--- | :--- | :--- |
| **Auth Service** | `POST /api/auth/register`<br>`POST /api/auth/login`<br>`POST /api/auth/refresh-token`<br>`POST /api/auth/forgot-password` | Verified & Re-tested |
| **Profile Service** | `PATCH /api/users/me`<br>`POST /api/users/change-password` | Verified & Re-tested |
| **Admin User Mgmt** | `GET /api/admin/users`<br>`PATCH /api/admin/user-status`<br>`PATCH /api/admin/user-role`<br>`DELETE /api/admin/users/{id}` | Verified & Re-tested |
| **Instructor-Student** | `POST /api/instructor/assign-student`<br>`GET /api/instructor/students/{instructor_email}` | Verified & Re-tested |
| **Course & Lessons** | `GET /api/courses/modules`<br>`GET /api/lessons`<br>`GET /api/lessons/{id}`<br>`POST /api/lessons` | Verified & Re-tested |
| **Gesture & Progress**| `POST /api/v1/day3/evaluate-sign`<br>`GET /api/v1/progress/user/{user_id}` | Verified & Re-tested |

---

## 2. Milestone 3 New API Additions

### A. Notification Service
* **Endpoint:** `GET /api/notifications`
  * **Description:** Retrieve paginated user notifications with optional `unread_only` filtering.
* **Endpoint:** `GET /api/notifications/unread-count`
  * **Description:** Returns total unread notification count for badge rendering.
* **Endpoint:** `POST /api/notifications`
  * **Description:** Dispatch new notifications to target user accounts.
* **Endpoint:** `PATCH /api/notifications/{notification_id}/read`
  * **Description:** Update notification read status.
* **Endpoint:** `DELETE /api/notifications/{notification_id}`
  * **Description:** Remove notification entry.

### B. Bulk Admin Actions
* **Endpoint:** `POST /api/admin/users/bulk-delete`
  * **Description:** Delete multiple users simultaneously via array of user IDs.
* **Endpoint:** `PATCH /api/admin/users/bulk-status`
  * **Description:** Bulk update active/inactive state across user list.
* **Endpoint:** `PATCH /api/admin/users/bulk-role`
  * **Description:** Bulk update user roles (e.g. promoting accounts to Instructor).

### C. CSV Bulk Lesson Upload
* **Endpoint:** `POST /api/lessons/bulk-upload-csv`
  * **Description:** Parses CSV formatted strings or file uploads to create curriculum lessons in batch.
  * **CSV Columns:** `module_id,title,content_description,expected_gesture,category,difficulty`

### D. Deeper Security Checks
* **Security Headers Middleware:** Response headers enforced (`X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Strict-Transport-Security`).
* **RBAC Role Verification:** JWT role validation (`Learner`, `Instructor`, `Admin`).

### E. Automated Test Suite
* **Test Suite Files:** `Backend/test_main.py` and `Backend/test_milestone3_day1.py`.
* **Execution:** `pytest Backend/test_main.py Backend/test_milestone3_day1.py` (11/11 tests passing).

---

## 3. Daily Stand-up Approval Confirmation
- **Plan Status:** Approved in Daily Stand-up.
- **Implementation Status:** Fully implemented and checked in.
