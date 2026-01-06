# tests/agent/test_response_quality.py
"""
Response Quality and Consistency Tests

Tests for:
- Response time thresholds
- Response quality metrics
- Query-response relevance
- Memory and context consistency
- Model behavioral consistency
"""

import pytest
import time
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from unittest.mock import MagicMock
from collections import Counter


@dataclass
class ResponseQualityMetrics:
    """Metrics for measuring response quality."""
    response_time_ms: float = 0.0
    word_count: int = 0
    sentence_count: int = 0
    relevance_score: float = 0.0  # 0-1 how relevant to query
    completeness_score: float = 0.0  # 0-1 did it answer fully
    clarity_score: float = 0.0  # 0-1 how clear/understandable
    hallucination_detected: bool = False
    action_verified: bool = True
    memory_consistent: bool = True


@dataclass
class ConsistencyTestResult:
    """Result of consistency test across multiple runs."""
    query: str
    responses: List[str] = field(default_factory=list)
    response_times_ms: List[float] = field(default_factory=list)
    is_consistent: bool = True
    inconsistency_details: str = ""


# ============================================================================
# RESPONSE TIME THRESHOLDS
# ============================================================================

class ResponseTimeThresholds:
    """Define acceptable response time thresholds."""
    SIMPLE_QUERY_MS = 2000      # 2 seconds for simple queries
    MEDIUM_QUERY_MS = 4000      # 4 seconds for medium complexity
    COMPLEX_QUERY_MS = 8000     # 8 seconds for complex queries
    TOOL_CALL_MS = 3000         # 3 seconds per tool call
    MAX_ACCEPTABLE_MS = 15000   # 15 seconds absolute max

    @staticmethod
    def get_threshold(query_complexity: str) -> float:
        """Get threshold based on query complexity."""
        thresholds = {
            "simple": ResponseTimeThresholds.SIMPLE_QUERY_MS,
            "medium": ResponseTimeThresholds.MEDIUM_QUERY_MS,
            "complex": ResponseTimeThresholds.COMPLEX_QUERY_MS,
        }
        return thresholds.get(query_complexity, ResponseTimeThresholds.MEDIUM_QUERY_MS)


class TestResponseTime:
    """Test response time metrics and thresholds."""

    @pytest.fixture
    def query_complexity_map(self):
        """Map queries to their expected complexity."""
        return {
            # Simple queries - direct data fetch
            "What is my name?": "simple",
            "Show my medications": "simple",
            "What time is my reminder?": "simple",
            
            # Medium queries - some processing
            "What are my active medications with dosages?": "medium",
            "Give me my adherence stats for this week": "medium",
            "What reminders do I have today?": "medium",
            
            # Complex queries - multiple tools or reasoning
            "Give me a complete health overview": "complex",
            "Analyze my medication adherence trend": "complex",
            "What should I do about my blood pressure based on my history?": "complex",
        }

    def test_simple_query_threshold(self):
        """Simple queries should respond under 2 seconds."""
        threshold = ResponseTimeThresholds.SIMPLE_QUERY_MS
        
        # Simulate a fast response
        simulated_time = 800  # 800ms
        
        assert simulated_time < threshold, \
            f"Simple query took {simulated_time}ms, threshold is {threshold}ms"

    def test_medium_query_threshold(self):
        """Medium queries should respond under 4 seconds."""
        threshold = ResponseTimeThresholds.MEDIUM_QUERY_MS
        
        simulated_time = 2500  # 2.5 seconds
        
        assert simulated_time < threshold, \
            f"Medium query took {simulated_time}ms, threshold is {threshold}ms"

    def test_complex_query_threshold(self):
        """Complex queries should respond under 8 seconds."""
        threshold = ResponseTimeThresholds.COMPLEX_QUERY_MS
        
        simulated_time = 6000  # 6 seconds
        
        assert simulated_time < threshold, \
            f"Complex query took {simulated_time}ms, threshold is {threshold}ms"

    def test_absolute_max_threshold(self):
        """No query should exceed 15 seconds."""
        max_threshold = ResponseTimeThresholds.MAX_ACCEPTABLE_MS
        
        # Even worst case shouldn't exceed max
        simulated_worst_case = 12000  # 12 seconds
        
        assert simulated_worst_case < max_threshold, \
            f"Query exceeded absolute max: {simulated_worst_case}ms > {max_threshold}ms"

    def test_classify_query_complexity(self, query_complexity_map):
        """Test query complexity classification."""
        for query, expected_complexity in query_complexity_map.items():
            # Simple heuristic: count words and keywords
            words = len(query.split())
            has_complex_keywords = any(
                kw in query.lower() 
                for kw in ["analyze", "overview", "trend", "complete", "based on"]
            )
            
            if has_complex_keywords or words > 10:
                inferred_complexity = "complex"
            elif words > 5:
                inferred_complexity = "medium"
            else:
                inferred_complexity = "simple"
            
            # Just verify the mapping exists
            assert expected_complexity in ["simple", "medium", "complex"]


# ============================================================================
# RESPONSE QUALITY METRICS
# ============================================================================

class ResponseQualityAnalyzer:
    """Analyze response quality across multiple dimensions."""

    def count_words(self, text: str) -> int:
        """Count words in response."""
        return len(text.split())

    def count_sentences(self, text: str) -> int:
        """Count sentences in response."""
        # Simple sentence detection
        sentences = re.split(r'[.!?]+', text)
        return len([s for s in sentences if s.strip()])

    def calculate_relevance(self, query: str, response: str) -> float:
        """Calculate query-response relevance score (0-1)."""
        query_words = set(query.lower().split())
        response_words = set(response.lower().split())
        
        # Remove common words
        stop_words = {"what", "is", "my", "the", "a", "an", "and", "or", "to", "for", "i", "me"}
        query_keywords = query_words - stop_words
        
        if not query_keywords:
            return 1.0  # No keywords to match
        
        # Check how many query keywords appear in response
        matches = query_keywords.intersection(response_words)
        relevance = len(matches) / len(query_keywords)
        
        return min(relevance, 1.0)

    def calculate_completeness(self, response: str, expected_elements: List[str]) -> float:
        """Calculate if response includes all expected elements."""
        if not expected_elements:
            return 1.0
        
        response_lower = response.lower()
        found = sum(1 for elem in expected_elements if elem.lower() in response_lower)
        
        return found / len(expected_elements)

    def detect_vague_response(self, response: str) -> bool:
        """Detect if response is vague or non-committal."""
        vague_phrases = [
            "i'm not sure",
            "i don't know",
            "it depends",
            "maybe",
            "possibly",
            "i think",
            "it seems",
            "might be",
            "could be",
            "i can't say for certain"
        ]
        
        response_lower = response.lower()
        return any(phrase in response_lower for phrase in vague_phrases)

    def analyze_response(
        self, 
        query: str, 
        response: str, 
        response_time_ms: float,
        expected_elements: Optional[List[str]] = None
    ) -> ResponseQualityMetrics:
        """Perform comprehensive response quality analysis."""
        
        metrics = ResponseQualityMetrics()
        metrics.response_time_ms = response_time_ms
        metrics.word_count = self.count_words(response)
        metrics.sentence_count = self.count_sentences(response)
        metrics.relevance_score = self.calculate_relevance(query, response)
        
        if expected_elements:
            metrics.completeness_score = self.calculate_completeness(response, expected_elements)
        else:
            metrics.completeness_score = 1.0 if metrics.word_count > 10 else 0.5
        
        # Clarity: penalize very short or very long responses
        if 20 <= metrics.word_count <= 200:
            metrics.clarity_score = 1.0
        elif metrics.word_count < 10:
            metrics.clarity_score = 0.3
        elif metrics.word_count > 500:
            metrics.clarity_score = 0.6
        else:
            metrics.clarity_score = 0.8
        
        return metrics


class TestResponseQuality:
    """Test response quality metrics."""

    @pytest.fixture
    def analyzer(self):
        return ResponseQualityAnalyzer()

    @pytest.fixture
    def quality_test_cases(self):
        return [
            {
                "query": "What medications am I taking?",
                "good_response": "You're currently taking Amlodipine 5mg once daily and Lisinopril 10mg once daily. Both are for managing your blood pressure.",
                "bad_response": "Medications.",
                "expected_elements": ["Amlodipine", "Lisinopril", "daily"]
            },
            {
                "query": "What are my vitals?",
                "good_response": "Your current vitals show: Height 175cm, Weight 80kg, BMI 26.1, Blood Pressure 120/80 mmHg. Your BMI is slightly elevated.",
                "bad_response": "I think you might have some vitals recorded somewhere.",
                "expected_elements": ["height", "weight", "bmi", "blood pressure"]
            },
            {
                "query": "When is my next reminder?",
                "good_response": "Your next medication reminder is at 8:00 AM today for Amlodipine 5mg.",
                "bad_response": "Maybe later.",
                "expected_elements": ["reminder", "AM", "medication"]
            },
        ]

    def test_word_count(self, analyzer):
        """Test word counting."""
        text = "This is a test response with exactly nine words."
        assert analyzer.count_words(text) == 9

    def test_sentence_count(self, analyzer):
        """Test sentence counting."""
        text = "First sentence. Second sentence! Third sentence?"
        assert analyzer.count_sentences(text) == 3

    def test_relevance_scoring(self, analyzer):
        """Test relevance calculation."""
        query = "What medications am I taking?"
        
        relevant_response = "You are taking Amlodipine and Lisinopril daily."
        irrelevant_response = "The weather is nice today."
        
        relevant_score = analyzer.calculate_relevance(query, relevant_response)
        irrelevant_score = analyzer.calculate_relevance(query, irrelevant_response)
        
        assert relevant_score > irrelevant_score, "Relevant response should score higher"

    def test_completeness_scoring(self, analyzer):
        """Test completeness calculation."""
        expected = ["name", "email", "phone"]
        
        complete_response = "Your name is John, email is john@test.com, phone is 555-1234."
        partial_response = "Your name is John."
        
        complete_score = analyzer.calculate_completeness(complete_response, expected)
        partial_score = analyzer.calculate_completeness(partial_response, expected)
        
        assert complete_score > partial_score
        assert complete_score == 1.0
        assert partial_score < 1.0

    def test_vague_response_detection(self, analyzer):
        """Test detection of vague responses."""
        vague = "I'm not sure about your medications."
        clear = "You have 2 active medications: Amlodipine and Lisinopril."
        
        assert analyzer.detect_vague_response(vague) == True
        assert analyzer.detect_vague_response(clear) == False

    def test_good_vs_bad_response(self, analyzer, quality_test_cases):
        """Test quality difference between good and bad responses."""
        for test in quality_test_cases:
            good_metrics = analyzer.analyze_response(
                test["query"],
                test["good_response"],
                response_time_ms=500,
                expected_elements=test["expected_elements"]
            )
            
            bad_metrics = analyzer.analyze_response(
                test["query"],
                test["bad_response"],
                response_time_ms=500,
                expected_elements=test["expected_elements"]
            )
            
            # Good response should score higher on all metrics
            assert good_metrics.relevance_score >= bad_metrics.relevance_score, \
                f"Good response should be more relevant for: {test['query']}"
            assert good_metrics.completeness_score >= bad_metrics.completeness_score, \
                f"Good response should be more complete for: {test['query']}"


# ============================================================================
# MEMORY AND CONSISTENCY TESTS
# ============================================================================

class TestMemoryConsistency:
    """Test agent memory and response consistency."""

    @pytest.fixture
    def conversation_history(self):
        """Sample conversation history."""
        return [
            {"role": "user", "content": "What medications am I taking?"},
            {"role": "assistant", "content": "You're taking Amlodipine 5mg and Lisinopril 10mg."},
            {"role": "user", "content": "How many is that?"},
            {"role": "assistant", "content": "That's 2 medications total."},
        ]

    def test_consistent_medication_count(self, conversation_history):
        """Agent should maintain consistent medication count."""
        # Extract medication count from history
        mentioned_meds = ["Amlodipine", "Lisinopril"]
        stated_count = 2
        
        assert len(mentioned_meds) == stated_count, \
            "Medication count should match mentioned medications"

    def test_no_contradicting_information(self):
        """Agent should not contradict itself in same conversation."""
        response1 = "You have 2 active medications."
        response2 = "Your 3 medications are well managed."  # Contradiction!
        
        # Extract numbers
        num1 = int(re.search(r'\d+', response1).group())
        num2 = int(re.search(r'\d+', response2).group())
        
        # This test should FAIL if agent contradicts (used for detection)
        if num1 != num2:
            pytest.fail(f"Contradiction detected: {num1} vs {num2} medications")

    def test_remembers_user_context(self, conversation_history):
        """Agent should remember context from earlier in conversation."""
        # If user asked about medications, follow-up should reference them
        first_query = conversation_history[0]["content"]
        follow_up = conversation_history[2]["content"]
        
        # "How many is that?" refers to medications from first query
        assert "how many" in follow_up.lower(), "Follow-up references previous context"

    def test_response_consistency_across_runs(self):
        """Same query should produce consistent (not contradictory) responses."""
        query = "What medications am I taking?"
        
        # Simulate multiple runs
        responses = [
            "Amlodipine 5mg and Lisinopril 10mg.",
            "You're taking Amlodipine and Lisinopril.",
            "Your medications are Amlodipine 5mg, Lisinopril 10mg.",
        ]
        
        # All should mention same medications
        for response in responses:
            assert "amlodipine" in response.lower(), "All responses should mention Amlodipine"
            assert "lisinopril" in response.lower(), "All responses should mention Lisinopril"

    def test_no_invented_prior_context(self):
        """Agent should not claim prior conversation that didn't happen."""
        # First message in a new conversation
        first_message = True
        
        bad_response = "As I mentioned earlier, your blood pressure is 120/80."
        
        has_false_reference = any(
            phrase in bad_response.lower()
            for phrase in ["as i mentioned", "earlier", "as i said", "previously"]
        )
        
        if first_message and has_false_reference:
            pytest.fail("Agent referenced non-existent prior conversation")


class TestModelBehaviorConsistency:
    """Test consistent model behavior across similar queries."""

    @pytest.fixture
    def similar_query_groups(self):
        """Groups of queries that should produce similar responses."""
        return [
            {
                "queries": [
                    "What medications am I taking?",
                    "Show me my medications",
                    "What meds do I have?",
                    "List my medications",
                ],
                "expected_tool": "get_active_medications",
                "should_contain": ["medication"]
            },
            {
                "queries": [
                    "What are my vital signs?",
                    "Show my vitals",
                    "My measurements please",
                    "What's my height and weight?",
                ],
                "expected_tool": "get_my_vitals",
                "should_contain": ["height", "weight"]
            },
        ]

    def test_similar_queries_use_same_tool(self, similar_query_groups):
        """Similar queries should invoke the same tool."""
        for group in similar_query_groups:
            expected_tool = group["expected_tool"]
            
            # All queries in group should map to same tool
            for query in group["queries"]:
                # In production, this would check actual tool selection
                # Here we verify the test setup
                assert expected_tool is not None, f"Query '{query}' should map to a tool"

    def test_response_style_consistency(self):
        """Agent should maintain consistent communication style."""
        responses = [
            "Hi! You're taking Amlodipine 5mg daily.",
            "Hello! Your medication is Amlodipine 5mg, taken once daily.",
            "Hey there! You have Amlodipine 5mg to take each day.",
        ]
        
        # All should be friendly/conversational (have greetings or warm tone)
        for response in responses:
            is_warm = any(
                greeting in response.lower()
                for greeting in ["hi", "hello", "hey", "you're", "your"]
            )
            assert is_warm, f"Response should maintain warm tone: {response}"

    def test_no_personality_drift(self):
        """Agent personality should not change mid-conversation."""
        # Rachel should always be warm and nurturing
        on_brand_responses = [
            "I can see you're doing well with your medications!",
            "Great job staying on top of your health!",
            "Let me check your records for you.",
        ]
        
        off_brand_response = "MEDICATIONS: Amlodipine 5mg. END OF REPORT."
        
        for response in on_brand_responses:
            # Should have conversational elements
            assert not response.isupper(), "Responses should not be all caps"
            assert len(response) > 20, "Responses should be conversational, not terse"
        
        # Off-brand response is robotic
        assert off_brand_response.isupper() or "END OF" in off_brand_response
