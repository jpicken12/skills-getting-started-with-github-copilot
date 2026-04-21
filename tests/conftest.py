"""Pytest configuration and fixtures for FastAPI tests."""
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Provide a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to known state before each test."""
    # Store original state
    original_activities = {
        k: {"participants": v["participants"].copy() if "participants" in v else []}
        for k, v in activities.items()
    }
    
    yield activities
    
    # Restore original state after test
    for activity_name, activity_data in activities.items():
        if "participants" in activity_data:
            activity_data["participants"] = original_activities[activity_name]["participants"]
