"""
Milestone 3 - Day 2: Notification System Test Suite
----------------------------------------------------
Verifies all four Day 2 checkpoints against the spec-compliant API surface:
  [x] Notifications table created
  [x] 'Create notification' API working          -> POST /api/notifications
  [x] 'Get my notifications' API working         -> GET /api/notifications/{user_id}
  [x] 'Mark as read' API working                 -> PATCH /api/notifications/{id}/read

Agreed event types: "badge_earned", "certificate_ready", "new_recommendation".
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
        "event_type": "info",
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
    assert data["event_type"] == "info"
    assert data["is_read"] is False
    assert "id" in data
    assert "created_at" in data


def test_checkpoint2_create_notification_all_types():
    """Checkpoint 2: Create notifications for all agreed event types."""
    user_id = "types_test_user_02"
    for event_type in ["info", "badge_earned", "certificate_ready", "new_recommendation"]:
        res = client.post("/api/notifications", json={
            "user_id": user_id,
            "title": f"Event {event_type}",
            "message": f"This is a {event_type} notification.",
            "event_type": event_type,
        })
        assert res.status_code == 201, f"Failed for type '{event_type}': {res.text}"
        assert res.json()["event_type"] == event_type


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
    # 422 (Pydantic min_length) or 400 (handler strip check) both reject it.
    assert res.status_code in (400, 422)


# ─────────────────────────────────────────────────────────
# Checkpoint 3: 'Get my notifications' API working
# ─────────────────────────────────────────────────────────

def test_checkpoint3_get_my_notifications_returns_correct_user():
    """Checkpoint 3: GET /{user_id} returns only the queried user's notifications."""
    user_id = "get_test_user_03"
    other_user_id = "other_user_03"

    # Create notifications for both users
    _create_notification(user_id, "My Notification 1", "For get_test_user_03")
    _create_notification(user_id, "My Notification 2", "For get_test_user_03")
    _create_notification(other_user_id, "Other Notification", "For other_user_03")

    res = client.get(f"/api/notifications/{user_id}")
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


def test_checkpoint3_get_my_notifications_newest_first():
    """Checkpoint 3: Notifications are returned newest first."""
    user_id = "order_test_user_03"
    _create_notification(user_id, "Older", "First created")
    _create_notification(user_id, "Newer", "Second created")

    res = client.get(f"/api/notifications/{user_id}")
    assert res.status_code == 200
    data = res.json()
    assert data[0]["title"] == "Newer"


def test_checkpoint3_get_my_notifications_empty_for_unknown_user():
    """Checkpoint 3: Unknown user ID returns an empty list (not an error)."""
    res = client.get("/api/notifications/nobody_user_xyz_999")
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
    assert patch_data["id"] == notif_id
    assert patch_data["is_read"] is True

    # Verify in the DB via get-my-notifications
    get_res = client.get(f"/api/notifications/{user_id}")
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
