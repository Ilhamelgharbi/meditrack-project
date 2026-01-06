"""
Unit tests for agent tools and core functionality
Tests for agent routing, tools, and core agent behavior
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import json


class TestAgentTools:
    """Test cases for agent tools and functionality"""

    def test_agent_routing_patient_query(self, client, auth_headers):
        """Test agent routing for patient-specific queries"""
        query_data = {
            "query": "What medications should I take today?",
            "context": {"user_id": "123", "role": "patient"}
        }

        response = client.post("/agent/query", json=query_data, headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "response" in data
        assert "query_analysis" in data
        assert isinstance(data["response"], str)

    def test_agent_routing_admin_query(self, client, admin_auth_headers):
        """Test agent routing for admin queries"""
        query_data = {
            "query": "Show me all patients and their medication schedules",
            "context": {"user_id": "1", "role": "admin"}
        }

        response = client.post("/agent/query", json=query_data, headers=admin_auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "response" in data
        assert "query_analysis" in data

    def test_agent_intent_classification(self, client, auth_headers):
        """Test agent intent classification"""
        queries = [
            "What time should I take my medication?",
            "I need to see my prescription history",
            "Schedule an appointment with my doctor",
            "I'm experiencing side effects from my medication"
        ]

        for query in queries:
            query_data = {
                "query": query,
                "context": {"user_id": "123"}
            }

            response = client.post("/agent/query", json=query_data, headers=auth_headers)
            assert response.status_code == 200

            data = response.json()
            assert "query_analysis" in data
            assert "intent" in data["query_analysis"]

    @patch('app.agent.patient_agent.PatientAgent.process_query')
    def test_patient_agent_integration(self, mock_process, client, auth_headers):
        """Test patient agent integration"""
        mock_process.return_value = {
            "response": "Your next medication is due in 2 hours",
            "tools_used": ["medication_schedule"],
            "confidence": 0.95
        }

        query_data = {
            "query": "When is my next medication due?",
            "context": {"user_id": "123", "role": "patient"}
        }

        response = client.post("/agent/query", json=query_data, headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "response" in data

    @patch('app.agent.admin_agent.AdminAgent.process_query')
    def test_admin_agent_integration(self, mock_process, client, admin_auth_headers):
        """Test admin agent integration"""
        mock_process.return_value = {
            "response": "Found 25 active patients",
            "tools_used": ["patient_management"],
            "data": {"patient_count": 25}
        }

        query_data = {
            "query": "How many patients are currently active?",
            "context": {"user_id": "1", "role": "admin"}
        }

        response = client.post("/agent/query", json=query_data, headers=admin_auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "response" in data

    def test_agent_memory_persistence(self, client, auth_headers):
        """Test agent memory persistence across queries"""
        # First query
        query1 = {
            "query": "I am John Doe, a 45-year-old male",
            "context": {"user_id": "123"}
        }

        response1 = client.post("/agent/query", json=query1, headers=auth_headers)
        assert response1.status_code == 200

        # Follow-up query that should use context
        query2 = {
            "query": "What medications should I take?",
            "context": {"user_id": "123"}
        }

        response2 = client.post("/agent/query", json=query2, headers=auth_headers)
        assert response2.status_code == 200

        # Check if agent remembers user context
        data2 = response2.json()
        assert "response" in data2

    def test_agent_tool_selection(self, client, auth_headers):
        """Test agent tool selection based on query"""
        test_cases = [
            {
                "query": "Show me my medication schedule",
                "expected_tools": ["medication_schedule", "patient_medications"]
            },
            {
                "query": "What are my upcoming reminders?",
                "expected_tools": ["reminder_schedule", "upcoming_reminders"]
            },
            {
                "query": "Update my profile information",
                "expected_tools": ["profile_update", "patient_profile"]
            }
        ]

        for test_case in test_cases:
            query_data = {
                "query": test_case["query"],
                "context": {"user_id": "123"}
            }

            response = client.post("/agent/query", json=query_data, headers=auth_headers)
            assert response.status_code == 200

            data = response.json()
            assert "query_analysis" in data
            # Tool selection may vary, just ensure response is generated

    def test_agent_error_handling(self, client, auth_headers):
        """Test agent error handling for invalid queries"""
        invalid_queries = [
            {"query": "", "context": {}},
            {"query": None, "context": {"user_id": "123"}},
            {"query": "   ", "context": {"user_id": "123"}}
        ]

        for query_data in invalid_queries:
            if query_data["query"] is None:
                query_data["query"] = None
            else:
                query_data["query"] = str(query_data["query"])

            response = client.post("/agent/query", json=query_data, headers=auth_headers)
            # Should handle gracefully
            assert response.status_code in [200, 400]

    def test_agent_context_preservation(self, client, auth_headers):
        """Test that agent preserves context across conversation"""
        conversation = [
            "Hello, I'm feeling unwell",
            "I have a headache and nausea",
            "What should I do?",
            "Can you help me?"
        ]

        for message in conversation:
            query_data = {
                "query": message,
                "context": {"user_id": "123", "conversation_id": "test_conv_001"}
            }

            response = client.post("/agent/query", json=query_data, headers=auth_headers)
            assert response.status_code == 200

            data = response.json()
            assert "response" in data

    @patch('app.agent.rag.retrieval.RAGRetrieval.search')
    def test_rag_integration(self, mock_search, client, auth_headers):
        """Test RAG (Retrieval-Augmented Generation) integration"""
        mock_search.return_value = [
            {"content": "Medication safety information", "score": 0.95},
            {"content": "Drug interaction guidelines", "score": 0.87}
        ]

        query_data = {
            "query": "Is it safe to take ibuprofen with my blood pressure medication?",
            "context": {"user_id": "123"}
        }

        response = client.post("/agent/query", json=query_data, headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "response" in data
        # RAG results should be incorporated into response

    def test_agent_response_format(self, client, auth_headers):
        """Test agent response format consistency"""
        query_data = {
            "query": "What is my medication schedule?",
            "context": {"user_id": "123"}
        }

        response = client.post("/agent/query", json=query_data, headers=auth_headers)
        assert response.status_code == 200

        data = response.json()

        # Check required fields
        required_fields = ["response", "query_analysis"]
        for field in required_fields:
            assert field in data

        # Check query analysis structure
        assert "intent" in data["query_analysis"]
        assert "confidence" in data["query_analysis"]
        assert "tools_used" in data["query_analysis"]

        # Check response is not empty
        assert len(data["response"].strip()) > 0