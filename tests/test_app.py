"""Comprehensive tests for the Mergington High School API."""
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


class TestRootEndpoint:
    """Tests for the root endpoint."""
    
    def test_root_redirects_to_index(self, client):
        """Test that root endpoint redirects to static index.html."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for the GET /activities endpoint."""
    
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that GET /activities returns all activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 9  # There are 9 activities
        assert "Chess Club" in data
        assert "Programming Class" in data
    
    def test_get_activities_includes_required_fields(self, client, reset_activities):
        """Test that each activity includes required fields."""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)
    
    def test_get_activities_chess_club_initial_state(self, client, reset_activities):
        """Test that Chess Club has expected initial state."""
        response = client.get("/activities")
        data = response.json()
        
        chess_club = data["Chess Club"]
        assert chess_club["max_participants"] == 12
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]
        assert len(chess_club["participants"]) == 2


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_new_participant(self, client, reset_activities):
        """Test signing up a new participant for an activity."""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "alice@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "alice@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]
        
        # Verify participant was added
        assert "alice@mergington.edu" in activities["Chess Club"]["participants"]
    
    def test_signup_duplicate_participant_fails(self, client, reset_activities):
        """Test that duplicate signup is rejected."""
        # First signup
        client.post(
            "/activities/Chess Club/signup",
            params={"email": "bob@mergington.edu"}
        )
        
        # Try duplicate signup
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "bob@mergington.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()
    
    def test_signup_nonexistent_activity_fails(self, client, reset_activities):
        """Test that signup for nonexistent activity fails."""
        response = client.post(
            "/activities/Fake Activity/signup",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_signup_with_special_characters_in_email(self, client, reset_activities):
        """Test signup with email containing special characters."""
        email = "test+tag@mergington.edu"
        response = client.post(
            "/activities/Programming Class/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        assert email in activities["Programming Class"]["participants"]
    
    def test_signup_multiple_participants_same_activity(self, client, reset_activities):
        """Test signing up multiple different participants to same activity."""
        emails = ["user1@mergington.edu", "user2@mergington.edu", "user3@mergington.edu"]
        
        for email in emails:
            response = client.post(
                "/activities/Art Studio/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify all were added
        for email in emails:
            assert email in activities["Art Studio"]["participants"]


class TestUnregisterFromActivity:
    """Tests for the DELETE /activities/{activity_name}/unregister endpoint."""
    
    def test_unregister_existing_participant(self, client, reset_activities):
        """Test unregistering an existing participant."""
        # Verify participant exists
        assert "michael@mergington.edu" in activities["Chess Club"]["participants"]
        
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        
        # Verify participant was removed
        assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]
    
    def test_unregister_nonexistent_participant_fails(self, client, reset_activities):
        """Test that unregistering nonexistent participant fails."""
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": "notasignedupuser@mergington.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"].lower()
    
    def test_unregister_from_nonexistent_activity_fails(self, client, reset_activities):
        """Test that unregistering from nonexistent activity fails."""
        response = client.delete(
            "/activities/Fake Activity/unregister",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_unregister_then_signup_again(self, client, reset_activities):
        """Test that participant can sign up again after unregistering."""
        email = "test@mergington.edu"
        
        # Sign up
        client.post(
            "/activities/Tennis Club/signup",
            params={"email": email}
        )
        assert email in activities["Tennis Club"]["participants"]
        
        # Unregister
        response = client.delete(
            "/activities/Tennis Club/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        assert email not in activities["Tennis Club"]["participants"]
        
        # Sign up again
        response = client.post(
            "/activities/Tennis Club/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        assert email in activities["Tennis Club"]["participants"]
    
    def test_unregister_multiple_participants(self, client, reset_activities):
        """Test unregistering multiple participants from an activity."""
        # Add multiple participants
        emails = ["u1@mergington.edu", "u2@mergington.edu"]
        for email in emails:
            client.post(
                "/activities/Music Band/signup",
                params={"email": email}
            )
        
        # Unregister first participant
        response = client.delete(
            "/activities/Music Band/unregister",
            params={"email": emails[0]}
        )
        assert response.status_code == 200
        assert emails[0] not in activities["Music Band"]["participants"]
        assert emails[1] in activities["Music Band"]["participants"]
        
        # Unregister second participant
        response = client.delete(
            "/activities/Music Band/unregister",
            params={"email": emails[1]}
        )
        assert response.status_code == 200
        assert emails[1] not in activities["Music Band"]["participants"]


class TestEdgeCases:
    """Tests for edge cases and error scenarios."""
    
    def test_activity_name_with_spaces_is_encoded(self, client, reset_activities):
        """Test that activity names with spaces are handled correctly."""
        response = client.post(
            "/activities/Basketball Team/signup",
            params={"email": "player@mergington.edu"}
        )
        assert response.status_code == 200
        assert "player@mergington.edu" in activities["Basketball Team"]["participants"]
    
    def test_empty_email_parameter(self, client, reset_activities):
        """Test signup with empty email."""
        response = client.post(
            "/activities/Debate Team/signup",
            params={"email": ""}
        )
        # Empty email is technically valid for the API
        assert response.status_code == 200
    
    def test_case_sensitivity_in_email(self, client, reset_activities):
        """Test that emails are treated case-sensitively."""
        email1 = "Test@mergington.edu"
        email2 = "test@mergington.edu"
        
        # Sign up with email1
        response1 = client.post(
            "/activities/Science Club/signup",
            params={"email": email1}
        )
        assert response1.status_code == 200
        
        # Sign up with email2 (different case)
        response2 = client.post(
            "/activities/Science Club/signup",
            params={"email": email2}
        )
        # API treats them as different emails
        assert response2.status_code == 200
        assert email1 in activities["Science Club"]["participants"]
        assert email2 in activities["Science Club"]["participants"]
    
    def test_max_participants_limit_not_enforced(self, client, reset_activities):
        """Test that max participants limit is not enforced by API."""
        activity = "Gym Class"
        max_participants = activities[activity]["max_participants"]
        
        # Add more participants than max
        for i in range(max_participants + 5):
            email = f"user{i}@mergington.edu"
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            # API allows exceeding max_participants
            assert response.status_code == 200
        
        # Verify we exceeded the limit
        assert len(activities[activity]["participants"]) > max_participants


class TestResponseFormats:
    """Tests for response format and structure."""
    
    def test_success_signup_response_format(self, client, reset_activities):
        """Test that signup response has correct format."""
        response = client.post(
            "/activities/Art Studio/signup",
            params={"email": "format@mergington.edu"}
        )
        data = response.json()
        assert isinstance(data, dict)
        assert "message" in data
        assert isinstance(data["message"], str)
    
    def test_success_unregister_response_format(self, client, reset_activities):
        """Test that unregister response has correct format."""
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": "daniel@mergington.edu"}
        )
        data = response.json()
        assert isinstance(data, dict)
        assert "message" in data
        assert isinstance(data["message"], str)
    
    def test_error_response_format(self, client, reset_activities):
        """Test that error responses have correct format."""
        response = client.post(
            "/activities/Nonexistent/signup",
            params={"email": "test@mergington.edu"}
        )
        data = response.json()
        assert isinstance(data, dict)
        assert "detail" in data
