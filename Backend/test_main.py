import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_gateway_root_and_health_endpoints():
    """Verifies baseline reachability of base system parameters."""
    response = client.get("/")
    assert response.status_code == 200
    assert "milestone_tracker" in response.json()

    health_response = client.get("/health")
    assert health_response.status_code == 200
    assert health_response.json()["status"] == "healthy"

def test_course_seeding_and_retrieval_flow():
    """Verifies that the Alphabet course data seeds automatically load correctly."""
    response = client.get("/api/courses/modules")
    assert response.status_code == 200
    data = response.json()
    
    # Assert that our automatic database seed initialized correctly
    assert len(data) > 0
    assert data[0]["module_id"] == "mod_alphabet_101"
    # Ensure all 26 default alphabet letters generated smoothly
    assert len(data[0]["lessons"]) == 26

def test_unauthenticated_rbac_route_protection():
    """Verifies that unauthorized requests are blocked by the gateway architecture."""
    # Attempting course generation without authentication header badge must trigger block
    response = client.post("/api/courses/modules", json={
        "title": "Hacker Course",
        "description": "Exploiting system parameters"
    })
    # Our dependency system triggers 401 via missing token metadata
    assert response.status_code in [401, 403]