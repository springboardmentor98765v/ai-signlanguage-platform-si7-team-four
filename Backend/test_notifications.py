"""
Milestone 3 Day 7: Notification endpoint coverage.

Covers the Day-2 notification service APIs (create / list / mark-as-read) using
the shared TestClient pattern. All rows are written to the isolated temp test
database provided by `conftest.py`, so `Backend/app_data.db` is never touched.
"""

import uuid

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _unique_user_id() -> str:
    return str(uuid.uuid4())


def _create_notification(user_id: str, title: str = "Test Title", message: str = "Test message."):
    return client.post("/api/notifications", json={
        "user_id": user_id,
        "title": title,
        "message": message,
        "event_type": "info",
    })


def test_create_notification_success():
    """POST /api/notifications persists a new unread notification."""
    user_id = _unique_user_id()
    res = _create_notification(user_id, "Welcome", "Your account is ready.")
    assert res.status_code == 201, res.text

    body = res.json()
    assert body["user_id"] == user_id
    assert body["title"] == "Welcome"
    assert body["message"] == "Your account is ready."
    assert body["event_type"] == "info"
    assert body["is_read"] is False
    assert "id" in body


def test_create_notification_rejects_empty_title():
    """Creating a notification with an empty title is rejected."""
    res = client.post("/api/notifications", json={
        "user_id": _unique_user_id(),
        "title": "   ",
        "message": "Should fail.",
    })
    assert res.status_code in (400, 422)


def test_list_notifications_for_user():
    """GET /api/notifications/{user_id} returns only that user's notifications."""
    user_id = _unique_user_id()
    other_user_id = _unique_user_id()

    _create_notification(user_id, "Mine 1", "for user")
    _create_notification(user_id, "Mine 2", "for user")
    _create_notification(other_user_id, "Not Mine", "for other user")

    res = client.get(f"/api/notifications/{user_id}")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert all(n["user_id"] == user_id for n in data)
    assert len(data) == 2


def test_list_notifications_newest_first():
    """Notifications are returned newest first."""
    user_id = _unique_user_id()
    _create_notification(user_id, "Older", "first")
    _create_notification(user_id, "Newer", "second")

    data = client.get(f"/api/notifications/{user_id}").json()
    assert data[0]["title"] == "Newer"


def test_list_notifications_empty_for_unknown_user():
    """An unknown user id returns an empty list, not an error."""
    res = client.get(f"/api/notifications/{_unique_user_id()}")
    assert res.status_code == 200
    assert res.json() == []


def test_mark_notification_as_read():
    """PATCH /api/notifications/{id}/read flips is_read to True."""
    user_id = _unique_user_id()
    notif_id = _create_notification(user_id, "Mark me", "please").json()["id"]

    res = client.patch(f"/api/notifications/{notif_id}/read")
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["id"] == notif_id
    assert body["is_read"] is True

    # Persisted: the same notification shows as read via the list endpoint.
    listed = client.get(f"/api/notifications/{user_id}").json()
    found = next(n for n in listed if n["id"] == notif_id)
    assert found["is_read"] is True


def test_mark_notification_as_read_unknown_id_404():
    """Marking a non-existent notification returns 404."""
    res = client.patch(f"/api/notifications/{_unique_user_id()}/read")
    assert res.status_code == 404
