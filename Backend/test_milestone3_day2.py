"""
Milestone 3 - Day 2: Notification System Test Suite
----------------------------------------------------
Verifies all four Day 2 checkpoints:
  [x] Notifications table created (with Intern 5)
  [x] 'Create notification' API working
  [x] 'Get my notifications' API working
  [x] 'Mark as read' API working
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# ─────────────────────────────────────────────────────────
# Helper – create a notification and return the response JSON
# ─────────────────────────────────────────────────────────

def _create_notification(user_id: str, title: str = "Test Title", message: str = "Test message."):
    return client.post("/api/notifications", json={
        "user_id": user_id,
        "title": title,
        "message": message,
        "notification_type": "info",
    })


# ─────────────────────────────────────────────────────────
# Checkpoint 1: Notifications table created
# (verified by successful DB operations below without errors)
# ─────────────────────────────────────────────────────────

def test_checkpoint1_notifications_table_exists():
    """
    Checkpoint 1: Notifications table exists and is accessible.
    Creating a record proves the table was created in the database.
    """
    user_id = "table_test_user_01"
    res = _create_notification(user_id, "Table Existence Check", "If this works, the table exists.")
    assert res.status_code == 201, f"Expected 201, got {res.status_code}: {res.text}"
    data = res.json()
    # The record was persisted, so the table clearly exists
    assert "id" in data
    assert data["user_id"] == user_id


# ─────────────────────────────────────────────────────────
# Checkpoint 2: 'Create notification' API working
# ─────────────────────────────────────────────────────────

def test_checkpoint2_create_notification_success():
    """Checkpoint 2: Create notification saves to DB with correct fields."""
    user_id = "create_test_user_02"
    res = _create_notification(user_id, "Welcome!", "Your account is ready.")
    assert res.status_code == 201
    data = res.json()
    assert data["user_id"] == user_id
    assert data["title"] == "Welcome!"
    assert data["message"] == "Your account is ready."
    assert data["notification_type"] == "info"
    assert data["is_read"] is False
    assert "id" in data
    assert "created_at" in data


def test_checkpoint2_create_notification_all_types():
    """Checkpoint 2: Create notifications for all valid types."""
    user_id = "types_test_user_02"
    for notif_type in ["info", "success", "warning", "alert"]:
        res = client.post("/api/notifications", json={
            "user_id": user_id,
            "title": f"Type {notif_type}",
            "message": f"This is a {notif_type} notification.",
            "notification_type": notif_type,
        })
        assert res.status_code == 201, f"Failed for type '{notif_type}': {res.text}"
        assert res.json()["notification_type"] == notif_type


def test_checkpoint2_create_notification_empty_user_id_rejected():
    """Checkpoint 2: Creating a notification with empty user_id is rejected."""
    res = client.post("/api/notifications", json={
        "user_id": "  ",
        "title": "Bad Request",
        "message": "Should fail.",
    })
    assert res.status_code == 400


def test_checkpoint2_create_notification_empty_title_rejected():
    """Checkpoint 2: Creating a notification with empty title is rejected."""
    res = client.post("/api/notifications", json={
        "user_id": "some_user",
        "title": "",
        "message": "Should fail.",
    })
    assert res.status_code == 400


# ─────────────────────────────────────────────────────────
# Checkpoint 3: 'Get my notifications' API working
# ─────────────────────────────────────────────────────────

def test_checkpoint3_get_my_notifications_returns_correct_user():
    """Checkpoint 3: /me endpoint returns only the queried user's notifications."""
    user_id = "get_test_user_03"
    other_user_id = "other_user_03"

    # Create notifications for both users
    _create_notification(user_id, "My Notification 1", "For get_test_user_03")
    _create_notification(user_id, "My Notification 2", "For get_test_user_03")
    _create_notification(other_user_id, "Other Notification", "For other_user_03")

    res = client.get(f"/api/notifications/me?user_id={user_id}")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    # All returned notifications must belong to user_id
    for notif in data:
        assert notif["user_id"] == user_id
    # Must contain at least the 2 we just created
    titles = [n["title"] for n in data]
    assert "My Notification 1" in titles
    assert "My Notification 2" in titles


def test_checkpoint3_get_my_notifications_unread_filter():
    """Checkpoint 3: unread_only=true returns only unread notifications."""
    user_id = "unread_test_user_03"

    # Create two notifications
    r1 = _create_notification(user_id, "Unread Notif", "Should appear")
    r2 = _create_notification(user_id, "Will be read", "Will be marked read")
    assert r1.status_code == 201
    assert r2.status_code == 201
    notif_id_to_read = r2.json()["id"]

    # Mark one as read
    mark_res = client.patch(f"/api/notifications/{notif_id_to_read}/read")
    assert mark_res.status_code == 200

    # Fetch unread only
    res = client.get(f"/api/notifications/me?user_id={user_id}&unread_only=true")
    assert res.status_code == 200
    data = res.json()
    for notif in data:
        assert notif["is_read"] is False


def test_checkpoint3_get_my_notifications_pagination():
    """Checkpoint 3: Pagination (skip, limit) works correctly."""
    user_id = "pagination_test_user_03"
    for i in range(5):
        _create_notification(user_id, f"Paginated Notif {i}", f"Message {i}")

    # Fetch 2 with skip=0
    res = client.get(f"/api/notifications/me?user_id={user_id}&limit=2&skip=0")
    assert res.status_code == 200
    assert len(res.json()) <= 2

    # Fetch 2 with skip=2
    res2 = client.get(f"/api/notifications/me?user_id={user_id}&limit=2&skip=2")
    assert res2.status_code == 200


def test_checkpoint3_get_my_notifications_empty_for_unknown_user():
    """Checkpoint 3: Unknown user ID returns an empty list (not an error)."""
    res = client.get("/api/notifications/me?user_id=nobody_user_xyz_999")
    assert res.status_code == 200
    assert res.json() == []


# ─────────────────────────────────────────────────────────
# Checkpoint 4: 'Mark as read' API working
# ─────────────────────────────────────────────────────────

def test_checkpoint4_mark_as_read_success():
    """Checkpoint 4: Marking an unread notification updates is_read to True in DB."""
    user_id = "markread_test_user_04"
    create_res = _create_notification(user_id, "Mark Me Read", "This should be marked.")
    assert create_res.status_code == 201
    notif_id = create_res.json()["id"]
    assert create_res.json()["is_read"] is False

    # Mark as read
    patch_res = client.patch(f"/api/notifications/{notif_id}/read")
    assert patch_res.status_code == 200
    patch_data = patch_res.json()
    assert patch_data["notification_id"] == notif_id
    assert patch_data["is_read"] is True

    # Verify in the DB via get-my-notifications
    get_res = client.get(f"/api/notifications/me?user_id={user_id}")
    assert get_res.status_code == 200
    found = next((n for n in get_res.json() if n["id"] == notif_id), None)
    assert found is not None
    assert found["is_read"] is True


def test_checkpoint4_mark_as_read_idempotent():
    """Checkpoint 4: Marking an already-read notification is safe and returns success."""
    user_id = "idempotent_user_04"
    create_res = _create_notification(user_id, "Already Read", "Already read notification.")
    notif_id = create_res.json()["id"]

    # Mark as read twice
    res1 = client.patch(f"/api/notifications/{notif_id}/read")
    res2 = client.patch(f"/api/notifications/{notif_id}/read")
    assert res1.status_code == 200
    assert res2.status_code == 200
    assert res2.json()["is_read"] is True


def test_checkpoint4_mark_as_read_invalid_id():
    """Checkpoint 4: Marking a non-existent notification returns 404."""
    res = client.patch("/api/notifications/nonexistent-id-99999/read")
    assert res.status_code == 404


# ─────────────────────────────────────────────────────────
# Supporting endpoint tests
# ─────────────────────────────────────────────────────────

def test_unread_count_endpoint():
    """Unread count reflects actual DB state correctly."""
    user_id = "count_test_user_05"
    _create_notification(user_id, "Count Test 1", "Msg 1")
    _create_notification(user_id, "Count Test 2", "Msg 2")

    count_res = client.get(f"/api/notifications/unread-count?user_id={user_id}")
    assert count_res.status_code == 200
    assert count_res.json()["unread_count"] >= 2
    assert count_res.json()["user_id"] == user_id


def test_delete_notification_endpoint():
    """Delete removes notification from DB and subsequent fetch returns 404."""
    user_id = "delete_test_user_06"
    create_res = _create_notification(user_id, "Delete Me", "This will be deleted.")
    notif_id = create_res.json()["id"]

    del_res = client.delete(f"/api/notifications/{notif_id}")
    assert del_res.status_code == 200

    # Verify it no longer exists
    get_res = client.get(f"/api/notifications/me?user_id={user_id}")
    ids = [n["id"] for n in get_res.json()]
    assert notif_id not in ids
