import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# ==============================================================================
# CHECKPOINT 2: RE-TESTING OLD MILESTONE 1 & 2 APIS
# ==============================================================================

def test_milestone1_2_health_and_root_endpoints():
    """Verify system health, root endpoint, and milestone tracker."""
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert "milestone_tracker" in res_root.json()

    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "healthy"

def test_milestone1_2_auth_and_profile_flow():
    """Verify user registration, login, refresh token, and profile update."""
    email = "test_day1_user@example.com"
    
    # 1. Register User
    reg_res = client.post("/api/auth/register", json={
        "username": "day1user",
        "email": email,
        "password": "SecurePassword123!",
        "role": "Learner"
    })
    assert reg_res.status_code in [201, 400] # 201 or 400 if already exists

    # 2. Login User
    login_res = client.post("/api/auth/login", json={
        "email": email,
        "password": "SecurePassword123!"
    })
    assert login_res.status_code == 200
    tokens = login_res.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    # 3. Refresh Token Session Extension
    ref_res = client.post("/api/auth/refresh-token", json={
        "refresh_token": tokens["refresh_token"]
    })
    assert ref_res.status_code == 200
    assert "access_token" in ref_res.json()

    # 4. Profile Update
    prof_res = client.patch("/api/users/me", json={
        "username": "day1user_updated"
    })
    assert prof_res.status_code == 200
    assert prof_res.json()["username"] == "day1user_updated"

def test_milestone1_2_courses_and_lessons_flow():
    """Verify course modules, single lesson, and advanced lesson retrieval."""
    mod_res = client.get("/api/courses/modules")
    assert mod_res.status_code == 200
    modules = mod_res.json()
    assert len(modules) > 0

    les_res = client.get("/api/lessons")
    assert les_res.status_code == 200
    assert "data" in les_res.json()

    adv_res = client.get("/api/lessons/advanced")
    assert adv_res.status_code == 200
    assert "advanced_lessons" in adv_res.json()

def test_milestone1_2_gesture_and_progress():
    """Verify sign gesture evaluation and user progress retrieval."""
    eval_res = client.post("/api/v1/day3/evaluate-sign", json={
        "sign_text": "HELLO",
        "user_id": 101
    })
    assert eval_res.status_code == 200
    assert eval_res.json()["success"] is True

    prog_res = client.get("/api/v1/progress/user/101")
    assert prog_res.status_code == 200
    assert len(prog_res.json()) > 0

# ==============================================================================
# CHECKPOINT 1 & MILESTONE 3 NEW API ADDITIONS
# ==============================================================================

def test_milestone3_notification_service():
    """Test Notification Service: Create, List, Unread Count, Mark Read, Delete."""
    user_id = "test_notif_user_99"

    # 1. Create Notification
    create_res = client.post("/api/notifications", json={
        "user_id": user_id,
        "title": "Day 1 Standup Alert",
        "message": "Milestone 3 plan approved by team.",
        "notification_type": "info"
    })
    assert create_res.status_code == 201
    notif = create_res.json()
    notif_id = notif["notification_id"]
    assert notif["is_read"] is False

    # 2. Get Unread Count
    count_res = client.get(f"/api/notifications/unread-count?user_id={user_id}")
    assert count_res.status_code == 200
    assert count_res.json()["unread_count"] >= 1

    # 3. List Notifications
    list_res = client.get(f"/api/notifications?user_id={user_id}")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # 4. Mark Read
    read_res = client.patch(f"/api/notifications/{notif_id}/read")
    assert read_res.status_code == 200
    assert read_res.json()["notification_id"] == notif_id

    # 5. Delete Notification
    del_res = client.delete(f"/api/notifications/{notif_id}")
    assert del_res.status_code == 200

def test_milestone3_bulk_admin_actions():
    """Test Bulk Admin Actions: Bulk Status, Bulk Role, Bulk Delete."""
    # 1. Bulk Status Update
    status_res = client.patch("/api/admin/users/bulk-status", json={
        "user_ids": ["dummy_u1", "dummy_u2"],
        "is_active": False
    })
    assert status_res.status_code == 200
    assert "updated_count" in status_res.json()

    # 2. Bulk Role Update
    role_res = client.patch("/api/admin/users/bulk-role", json={
        "user_ids": ["dummy_u1", "dummy_u2"],
        "new_role": "Instructor"
    })
    assert role_res.status_code == 200
    assert "updated_count" in role_res.json()

    # 3. Bulk Delete
    del_res = client.post("/api/admin/users/bulk-delete", json={
        "user_ids": ["dummy_u1", "dummy_u2"]
    })
    assert del_res.status_code == 200
    assert "deleted_count" in del_res.json()

def test_milestone3_csv_bulk_lesson_upload():
    """Test CSV Bulk Lesson Upload feature."""
    csv_payload = (
        "module_id,title,content_description,expected_gesture,category,difficulty\n"
        "mod_alphabet_101,Bulk CSV Test 1,Test Description 1,GESTURE_1,Phrases,Easy\n"
        "mod_alphabet_101,Bulk CSV Test 2,Test Description 2,GESTURE_2,Phrases,Hard\n"
    )

    upload_res = client.post("/api/lessons/bulk-upload-csv", json={
        "csv_content": csv_payload
    })
    assert upload_res.status_code == 201
    res_data = upload_res.json()
    assert res_data["created_count"] == 2
    assert len(res_data["created_lessons"]) == 2

def test_milestone3_deeper_security_checks():
    """Verify security headers middleware enforcement on responses."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    assert "Strict-Transport-Security" in response.headers
