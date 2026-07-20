# Milestone 2: API Planning

## 1. Update Profile
- **Endpoint**: `PATCH /api/users/me`
- **Purpose**: Allow users to update their username/email.

## 2. Password Recovery
- **Endpoint**: `POST /api/auth/forgot-password`
- **Endpoint**: `POST /api/auth/reset-password`
- **Purpose**: Handle email-based password resets.

## 3. Instructor-Student Management
- **Endpoint**: `GET /api/instructors/students`
- **Purpose**: List all students currently assigned to the instructor.

## 4. Admin Management
- **Endpoint**: `GET /api/admin/users`
- **Endpoint**: `DELETE /api/admin/users/{user_id}`
- **Purpose**: Admin tools to manage and remove users.

## 5. Advanced Lesson Content
- **Endpoint**: `GET /api/lessons/{lesson_id}`
- **Purpose**: Retrieve full details of an advanced lesson.