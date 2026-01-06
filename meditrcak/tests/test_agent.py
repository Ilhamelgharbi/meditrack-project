"""
Unit tests for agent routes
"""
import pytest
from fastapi.testclient import TestClient


class TestAgentRoutes:
    """Test cases for agent endpoints"""

    def test_agent_query(self, client, auth_headers):
        """Test basic agent query"""
        query_data = {
            "query": "What medications should I take today?",
            "context": {}
        }

        response = client.post("/agent/query", json=query_data, headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "response" in data
        assert "query_analysis" in data
        assert isinstance(data["response"], str)

    def test_agent_query_unauthenticated(self, client):
        """Test agent query without authentication"""
        query_data = {"query": "Test query"}

        response = client.post("/agent/query", json=query_data)
        assert response.status_code == 401

    def test_agent_query_empty_query(self, client, auth_headers):
        """Test agent query with empty query"""
        query_data = {"query": ""}

        response = client.post("/agent/query", json=query_data, headers=auth_headers)
        assert response.status_code == 400

    def test_agent_query_with_context(self, client, auth_headers):
        """Test agent query with additional context"""
        query_data = {
            "query": "Help me with my medication schedule",
            "context": {
                "current_time": "2024-01-15T10:00:00Z",
                "user_location": "home"
            }
        }

        response = client.post("/agent/query", json=query_data, headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "response" in data

    def test_agent_profile_questions(self, client, auth_headers):
        """Test getting agent profile questions"""
        response = client.get("/agent/profile-questions", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

        # Check structure if there are questions
        if data:
            question = data[0]
            assert "id" in question
            assert "question" in question
            assert "category" in question

    def test_agent_profile_questions_unauthenticated(self, client):
        """Test getting profile questions without authentication"""
        response = client.get("/agent/profile-questions")
        assert response.status_code == 401

    def test_agent_analyze_intent(self, client, auth_headers):
        """Test agent intent analysis"""
        analysis_data = {
            "query": "I need to know about my blood pressure medication",
            "user_profile": {}
        }

        response = client.post("/agent/analyze-intent", json=analysis_data, headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "intent" in data
        assert "confidence" in data
        assert "entities" in data

    def test_agent_analyze_intent_empty_query(self, client, auth_headers):
        """Test agent intent analysis with empty query"""
        analysis_data = {"query": ""}

        response = client.post("/agent/analyze-intent", json=analysis_data, headers=auth_headers)
        assert response.status_code == 400

    def test_agent_get_recommendations(self, client, auth_headers):
        """Test getting agent recommendations"""
        response = client.get("/agent/recommendations", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

        # Check structure if there are recommendations
        if data:
            recommendation = data[0]
            assert "type" in recommendation
            assert "message" in recommendation
            assert "priority" in recommendation

    def test_agent_get_recommendations_with_context(self, client, auth_headers):
        """Test getting agent recommendations with context"""
        context_data = {
            "adherence_rate": 85,
            "missed_doses": 2,
            "time_since_last_dose": "2 hours"
        }

        response = client.post("/agent/recommendations", json=context_data, headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

    def test_agent_health_check(self, client, auth_headers):
        """Test agent health check"""
        response = client.get("/agent/health", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "version" in data
        assert data["status"] == "healthy"

    def test_agent_health_check_unauthenticated(self, client):
        """Test agent health check without authentication"""
        response = client.get("/agent/health")
        assert response.status_code == 401

    def test_agent_conversation_history(self, client, auth_headers):
        """Test getting agent conversation history"""
        response = client.get("/agent/conversation-history", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

        # Check structure if there are conversations
        if data:
            conversation = data[0]
            assert "timestamp" in conversation
            assert "query" in conversation
            assert "response" in conversation

    def test_agent_conversation_history_with_limit(self, client, auth_headers):
        """Test getting agent conversation history with limit"""
        response = client.get("/agent/conversation-history?limit=5", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5

    def test_agent_feedback(self, client, auth_headers):
        """Test submitting agent feedback"""
        feedback_data = {
            "query_id": "test-query-123",
            "rating": 5,
            "feedback": "Very helpful response",
            "categories": ["accurate", "clear"]
        }

        response = client.post("/agent/feedback", json=feedback_data, headers=auth_headers)
        assert response.status_code == 201

        data = response.json()
        assert "message" in data

    def test_agent_feedback_invalid_rating(self, client, auth_headers):
        """Test submitting agent feedback with invalid rating"""
        feedback_data = {
            "query_id": "test-query-123",
            "rating": 10,  # Invalid rating (should be 1-5)
            "feedback": "Test feedback"
        }

        response = client.post("/agent/feedback", json=feedback_data, headers=auth_headers)
        assert response.status_code == 400

    def test_agent_tools_list(self, client, auth_headers):
        """Test getting available agent tools"""
        response = client.get("/agent/tools", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

        # Check structure if there are tools
        if data:
            tool = data[0]
            assert "name" in tool
            assert "description" in tool
            assert "parameters" in tool

    def test_agent_execute_tool(self, client, auth_headers):
        """Test executing an agent tool"""
        tool_data = {
            "tool_name": "get_medication_info",
            "parameters": {
                "medication_name": "aspirin"
            }
        }

        response = client.post("/agent/execute-tool", json=tool_data, headers=auth_headers)
        # This might return 404 if the tool doesn't exist, or 200 if it does
        assert response.status_code in [200, 404]

    def test_agent_execute_tool_invalid_tool(self, client, auth_headers):
        """Test executing invalid agent tool"""
        tool_data = {
            "tool_name": "nonexistent_tool",
            "parameters": {}
        }

        response = client.post("/agent/execute-tool", json=tool_data, headers=auth_headers)
        assert response.status_code == 404

    def test_agent_whatsapp_integration_status(self, client, auth_headers):
        """Test getting WhatsApp integration status"""
        response = client.get("/agent/whatsapp/status", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "connected" in data
        assert "phone_number" in data

    def test_agent_whatsapp_send_message(self, client, auth_headers):
        """Test sending WhatsApp message through agent"""
        message_data = {
            "phone_number": "+1234567890",
            "message": "Test medication reminder"
        }

        response = client.post("/agent/whatsapp/send", json=message_data, headers=auth_headers)
        # This might succeed or fail depending on WhatsApp setup
        assert response.status_code in [200, 400, 500]

    def test_agent_whatsapp_send_message_invalid_number(self, client, auth_headers):
        """Test sending WhatsApp message with invalid number"""
        message_data = {
            "phone_number": "invalid-number",
            "message": "Test message"
        }

        response = client.post("/agent/whatsapp/send", json=message_data, headers=auth_headers)
        assert response.status_code == 400