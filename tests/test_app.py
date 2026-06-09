from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

client = TestClient(app)
initial_activities = deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset in-memory activity state before each test."""
    activities.clear()
    activities.update(deepcopy(initial_activities))
    yield
    activities.clear()
    activities.update(deepcopy(initial_activities))


def test_get_activities_returns_activity_data():
    response = client.get("/activities")

    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert "Programming Class" in data
    assert isinstance(data["Chess Club"]["participants"], list)
    assert data["Chess Club"]["max_participants"] == 12


def test_signup_adds_new_participant():
    new_email = "newstudent@mergington.edu"
    response = client.post(
        f"/activities/Chess%20Club/signup?email={new_email}"
    )

    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {new_email} for Chess Club"

    activities_response = client.get("/activities").json()
    assert new_email in activities_response["Chess Club"]["participants"]


def test_signup_duplicate_returns_400():
    existing_email = "michael@mergington.edu"
    response = client.post(
        f"/activities/Chess%20Club/signup?email={existing_email}"
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"

    activities_response = client.get("/activities").json()
    assert activities_response["Chess Club"]["participants"].count(existing_email) == 1


def test_unregister_participant_removes_email():
    email_to_remove = "daniel@mergington.edu"
    response = client.delete(
        f"/activities/Chess%20Club/participants?email={email_to_remove}"
    )

    assert response.status_code == 200
    assert response.json()["message"] == f"Removed {email_to_remove} from Chess Club"

    activities_response = client.get("/activities").json()
    assert email_to_remove not in activities_response["Chess Club"]["participants"]


def test_unregister_missing_participant_returns_404():
    email_to_remove = "nobody@mergington.edu"
    response = client.delete(
        f"/activities/Chess%20Club/participants?email={email_to_remove}"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found in activity"


def test_activity_not_found_for_signup_and_unregister():
    signup_response = client.post(
        "/activities/Nonexistent%20Club/signup?email=test@mergington.edu"
    )
    assert signup_response.status_code == 404
    assert signup_response.json()["detail"] == "Activity not found"

    unregister_response = client.delete(
        "/activities/Nonexistent%20Club/participants?email=test@mergington.edu"
    )
    assert unregister_response.status_code == 404
    assert unregister_response.json()["detail"] == "Activity not found"
