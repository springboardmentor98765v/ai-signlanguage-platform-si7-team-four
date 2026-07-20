# Milestone 2 - Backend API Specification Plan

## 1. Update Profile API
* **Endpoint:** `PATCH /api/users/me`
* **Purpose:** Allows authenticated users to update their profile information (username or email).

## 2. Reset Password APIs
* **Endpoint:** `POST /api/auth/forgot-password`
* **Endpoint:** `POST /api/auth/reset-password`
* **Purpose:** Handles secure user password recovery workflows via token generation.

## 3. Instructor-Student List API
* **Endpoint:** `GET /api/instructors/students`
* **Purpose:** Fetches the filtered roster of students assigned to a specific instructor.

## 4. Admin User Management APIs
* **Endpoint:** `GET /api/admin/users`
* **Endpoint:** `DELETE /api/admin/users/{user_id}`
* **Purpose:** Grants admin-level control to view user accounts and remove unauthorized users.

## 5. Expanded Lesson Content API
* **Endpoint:** `GET /api/lessons/advanced`
* **Purpose:** Fetches extended or advanced multi-tier lesson schemas for the course catalog.