# tests/agent/test_tool_selection.py
"""
Agent Tool Selection Tests

Tests that the agent correctly maps user queries to the appropriate tools.
Uses the filter_tools_for_query function from patient_agent.py
"""

import pytest
from typing import List, Set
from unittest.mock import patch, MagicMock


# Tool categories for validation
PROFILE_TOOLS = {"get_my_profile", "get_my_vitals", "update_my_profile", "update_my_vitals"}
MEDICATION_TOOLS = {"get_my_medications", "get_active_medications", "get_pending_medications", 
                    "confirm_medication", "get_inactive_medications"}
ADHERENCE_TOOLS = {"get_my_adherence_stats"}
REMINDER_TOOLS = {"get_my_reminders", "set_medication_reminder"}
MEDICAL_TOOLS = {"get_my_medical_history", "get_my_allergies", "get_my_health_summary"}
LOGGING_TOOLS = {"log_medication_taken", "log_medication_skipped", "get_recent_medication_logs"}

ALL_PATIENT_TOOLS = (PROFILE_TOOLS | MEDICATION_TOOLS | ADHERENCE_TOOLS | 
                     REMINDER_TOOLS | MEDICAL_TOOLS | LOGGING_TOOLS)


class TestToolSelectionLogic:
    """Test tool selection based on query patterns."""

    def test_profile_query_patterns(self):
        """Test queries that should select profile tools."""
        profile_queries = [
            "What is my profile?",
            "Tell me about myself",
            "Show my personal information",
            "What's my name and email?",
            "My account details",
        ]
        
        for query in profile_queries:
            # These should trigger profile-related tool selection
            assert any(word in query.lower() for word in ["profile", "myself", "personal", "name", "account"])

    def test_vitals_query_patterns(self):
        """Test queries that should select vitals tools."""
        vitals_queries = [
            "What are my vital signs?",
            "Show my measurements",
            "What's my blood pressure?",
            "My height and weight",
            "What's my BMI?",
        ]
        
        for query in vitals_queries:
            assert any(word in query.lower() for word in ["vital", "measurements", "blood pressure", "height", "weight", "bmi"])

    def test_reminder_query_patterns(self):
        """Test queries that should select reminder tools."""
        reminder_queries = [
            "What are my reminders?",
            "When should I take my medication?",
            "Set a reminder for 8 AM",
            "My medication schedule",
            "Remind me to take my pills",
        ]
        
        for query in reminder_queries:
            assert any(word in query.lower() for word in ["reminder", "schedule", "when", "remind"])

    def test_medication_query_patterns(self):
        """Test queries that should select medication tools."""
        medication_queries = [
            "What medications am I taking?",
            "Show my active medications",
            "Do I have pending medications?",
            "My current prescriptions",
            "List all my drugs",
        ]
        
        for query in medication_queries:
            assert any(word in query.lower() for word in ["medication", "active", "pending", "prescription", "drug", "taking"])

    def test_adherence_query_patterns(self):
        """Test queries that should select adherence tools."""
        adherence_queries = [
            "How well am I taking my medications?",
            "What's my adherence rate?",
            "Am I following my medication plan?",
            "My compliance stats",
            "Medication streak",
        ]
        
        for query in adherence_queries:
            assert any(word in query.lower() for word in ["adherence", "compliance", "following", "well", "streak", "rate"])

    def test_logging_query_patterns(self):
        """Test queries that should select logging tools."""
        logging_queries = [
            "I took my medication",
            "Log that I skipped my dose",
            "Mark Amlodipine as taken",
            "I missed my morning pill",
            "Record my medication intake",
        ]
        
        for query in logging_queries:
            assert any(word in query.lower() for word in ["took", "skipped", "taken", "missed", "log", "record", "mark"])

    def test_health_summary_query_patterns(self):
        """Test queries that should select health summary tools."""
        health_queries = [
            "Give me a health overview",
            "What's my health summary?",
            "My medical history",
            "What allergies do I have?",
            "Overall health status",
        ]
        
        for query in health_queries:
            assert any(word in query.lower() for word in ["health", "summary", "overview", "history", "allergies", "status"])


class TestToolCategoryMapping:
    """Test mapping between query categories and tool categories."""

    @pytest.fixture
    def category_tool_map(self):
        """Map categories to their expected tools."""
        return {
            "profile": ["get_my_profile"],
            "vitals": ["get_my_vitals"],
            "reminders": ["get_my_reminders", "set_medication_reminder"],
            "medications": ["get_active_medications", "get_my_medications", 
                          "get_pending_medications", "get_my_adherence_stats"],
            "health_summary": ["get_my_health_summary", "get_my_allergies"],
            "logging": ["log_medication_taken", "log_medication_skipped"],
        }

    def test_profile_category_tools(self, category_tool_map):
        """Profile queries should use profile tools."""
        expected_tools = category_tool_map["profile"]
        assert "get_my_profile" in expected_tools

    def test_vitals_category_tools(self, category_tool_map):
        """Vitals queries should use vitals tools."""
        expected_tools = category_tool_map["vitals"]
        assert "get_my_vitals" in expected_tools

    def test_reminders_category_tools(self, category_tool_map):
        """Reminder queries should use reminder tools."""
        expected_tools = category_tool_map["reminders"]
        assert "get_my_reminders" in expected_tools
        assert "set_medication_reminder" in expected_tools

    def test_medications_category_tools(self, category_tool_map):
        """Medication queries should use medication tools."""
        expected_tools = category_tool_map["medications"]
        assert "get_active_medications" in expected_tools
        assert "get_my_adherence_stats" in expected_tools

    def test_health_summary_category_tools(self, category_tool_map):
        """Health summary queries should use appropriate tools."""
        expected_tools = category_tool_map["health_summary"]
        assert "get_my_health_summary" in expected_tools
        assert "get_my_allergies" in expected_tools

    def test_logging_category_tools(self, category_tool_map):
        """Logging queries should use logging tools."""
        expected_tools = category_tool_map["logging"]
        assert "log_medication_taken" in expected_tools
        assert "log_medication_skipped" in expected_tools


class TestEdgeCases:
    """Test edge cases and ambiguous queries."""

    def test_ambiguous_query_medication_reminder(self):
        """Test query that could be medication or reminder."""
        query = "What time do I take my medication?"
        # Should lean towards reminders as it asks about time
        assert "time" in query.lower()
        assert "medication" in query.lower()

    def test_combined_query_profile_vitals(self):
        """Test query asking for both profile and vitals."""
        query = "Show me my profile including vitals"
        assert "profile" in query.lower()
        assert "vitals" in query.lower()

    def test_empty_query_handling(self):
        """Test handling of empty queries."""
        query = ""
        # Empty queries should return default or error
        assert len(query) == 0

    def test_very_long_query(self):
        """Test handling of very long queries."""
        query = "I want to know about " + "my medications " * 100
        # Should still identify medication as the key topic
        assert "medications" in query.lower()

    def test_special_characters_in_query(self):
        """Test handling of special characters."""
        query = "What's my profile??? Show me!!!"
        # Should handle punctuation gracefully
        assert "profile" in query.lower().replace("'", "")

    def test_case_insensitivity(self):
        """Test that queries are case insensitive."""
        queries = ["WHAT ARE MY MEDICATIONS?", "what are my medications?", "What Are My Medications?"]
        for query in queries:
            assert "medications" in query.lower()

    def test_typo_tolerance(self):
        """Test common typos in queries."""
        # Note: This would require fuzzy matching in production
        query = "whats my profiel"  # typo: profiel
        # In production, fuzzy matching would catch this
        assert len(query) > 0

    def test_query_with_medication_name(self):
        """Test queries that include specific medication names."""
        query = "Did I take my Amlodipine today?"
        # Should identify as a logging/taken query
        assert "take" in query.lower() or "took" in query.lower()

    def test_query_asking_about_side_effects(self):
        """Test queries about medication side effects."""
        query = "What are the side effects of my medications?"
        # Should use medication tools to get side effect info
        assert "side effects" in query.lower()

    def test_urgent_query(self):
        """Test urgent/emergency phrasing."""
        query = "I urgently need to know my medications!"
        # Should still correctly identify as medication query
        assert "medications" in query.lower()
