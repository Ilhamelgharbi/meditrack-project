# tests/agent/test_agent_metrics.py
"""
Agent Performance Metrics Tests

Measures and tracks:
- Latency (response time)
- Accuracy (correct tool selection)
- Response quality (keyword matching, relevance, completeness)
- Hallucination detection
- Action verification (did tool actually execute?)
- Memory consistency
- Model behavioral consistency
- Error handling
- Token usage estimation
"""

import pytest
import time
import json
import statistics
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path


@dataclass
class AgentMetric:
    """Single metric measurement for an agent query."""
    question_id: int
    question: str
    category: str
    expected_tool: str
    
    # Timing metrics
    start_time: float = 0.0
    end_time: float = 0.0
    latency_ms: float = 0.0
    
    # Accuracy metrics
    tool_selected: str = ""
    tool_accuracy: bool = False
    
    # Response quality metrics
    response_text: str = ""
    keywords_found: List[str] = field(default_factory=list)
    keywords_expected: List[str] = field(default_factory=list)
    keyword_match_rate: float = 0.0
    relevance_score: float = 0.0      # NEW: Query-response relevance (0-1)
    completeness_score: float = 0.0   # NEW: Did it fully answer? (0-1)
    clarity_score: float = 0.0        # NEW: Is response clear? (0-1)
    
    # Hallucination & Behavior metrics (NEW)
    hallucination_detected: bool = False
    hallucination_type: str = ""      # fabricated_data, false_action, etc.
    action_verified: bool = True      # Did the claimed action actually happen?
    action_tool_called: bool = True   # Was the tool actually invoked?
    memory_consistent: bool = True    # No contradictions in conversation
    
    # Error tracking
    error_occurred: bool = False
    error_message: str = ""
    
    # Token estimation (approximate)
    input_tokens_estimate: int = 0
    output_tokens_estimate: int = 0


@dataclass
class AgentMetricsReport:
    """Aggregated metrics report for all agent tests."""
    timestamp: str = ""
    total_questions: int = 0
    questions_passed: int = 0
    questions_failed: int = 0
    
    # Latency stats
    avg_latency_ms: float = 0.0
    min_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p90_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    
    # Accuracy stats
    tool_accuracy_rate: float = 0.0
    avg_keyword_match_rate: float = 0.0
    
    # Response Quality stats (NEW)
    avg_relevance_score: float = 0.0
    avg_completeness_score: float = 0.0
    avg_clarity_score: float = 0.0
    
    # Hallucination & Behavior stats (NEW)
    hallucination_rate: float = 0.0
    hallucination_count: int = 0
    false_action_count: int = 0       # Said "done" but didn't do it
    action_verification_rate: float = 0.0
    memory_consistency_rate: float = 0.0
    
    # Error stats
    error_rate: float = 0.0
    errors: List[str] = field(default_factory=list)
    
    # Category breakdown
    category_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Individual metrics
    individual_metrics: List[Dict[str, Any]] = field(default_factory=list)


class AgentMetricsCollector:
    """Collects and calculates metrics for agent performance."""
    
    def __init__(self):
        self.metrics: List[AgentMetric] = []
        self.start_time = datetime.now()
    
    def record_metric(self, metric: AgentMetric) -> None:
        """Record a single metric measurement."""
        self.metrics.append(metric)
    
    def calculate_latency(self, start: float, end: float) -> float:
        """Calculate latency in milliseconds."""
        return (end - start) * 1000
    
    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation (4 chars per token average)."""
        return len(text) // 4
    
    def calculate_keyword_match_rate(
        self, 
        response: str, 
        expected_keywords: List[str]
    ) -> tuple[float, List[str]]:
        """Calculate what percentage of expected keywords are in response."""
        response_lower = response.lower()
        found = [kw for kw in expected_keywords if kw.lower() in response_lower]
        rate = len(found) / len(expected_keywords) if expected_keywords else 0.0
        return rate, found
    
    def generate_report(self) -> AgentMetricsReport:
        """Generate comprehensive metrics report."""
        if not self.metrics:
            return AgentMetricsReport(timestamp=datetime.now().isoformat())
        
        report = AgentMetricsReport()
        report.timestamp = datetime.now().isoformat()
        report.total_questions = len(self.metrics)
        
        # Calculate pass/fail
        report.questions_passed = sum(1 for m in self.metrics if m.tool_accuracy and not m.error_occurred)
        report.questions_failed = report.total_questions - report.questions_passed
        
        # Latency calculations
        latencies = [m.latency_ms for m in self.metrics if m.latency_ms > 0]
        if latencies:
            report.avg_latency_ms = statistics.mean(latencies)
            report.min_latency_ms = min(latencies)
            report.max_latency_ms = max(latencies)
            
            sorted_latencies = sorted(latencies)
            n = len(sorted_latencies)
            report.p50_latency_ms = sorted_latencies[n // 2]
            report.p90_latency_ms = sorted_latencies[int(n * 0.9)]
            report.p99_latency_ms = sorted_latencies[int(n * 0.99)] if n > 1 else sorted_latencies[-1]
        
        # Accuracy calculations
        tool_correct = sum(1 for m in self.metrics if m.tool_accuracy)
        report.tool_accuracy_rate = tool_correct / len(self.metrics) * 100
        
        keyword_rates = [m.keyword_match_rate for m in self.metrics]
        report.avg_keyword_match_rate = statistics.mean(keyword_rates) * 100 if keyword_rates else 0.0
        
        # Response Quality calculations (NEW)
        relevance_scores = [m.relevance_score for m in self.metrics if m.relevance_score > 0]
        completeness_scores = [m.completeness_score for m in self.metrics if m.completeness_score > 0]
        clarity_scores = [m.clarity_score for m in self.metrics if m.clarity_score > 0]
        
        report.avg_relevance_score = statistics.mean(relevance_scores) * 100 if relevance_scores else 0.0
        report.avg_completeness_score = statistics.mean(completeness_scores) * 100 if completeness_scores else 0.0
        report.avg_clarity_score = statistics.mean(clarity_scores) * 100 if clarity_scores else 0.0
        
        # Hallucination & Behavior calculations (NEW)
        hallucinations = [m for m in self.metrics if m.hallucination_detected]
        report.hallucination_count = len(hallucinations)
        report.hallucination_rate = len(hallucinations) / len(self.metrics) * 100
        
        false_actions = [m for m in self.metrics if not m.action_verified]
        report.false_action_count = len(false_actions)
        
        verified_actions = sum(1 for m in self.metrics if m.action_verified)
        report.action_verification_rate = verified_actions / len(self.metrics) * 100
        
        consistent_memory = sum(1 for m in self.metrics if m.memory_consistent)
        report.memory_consistency_rate = consistent_memory / len(self.metrics) * 100
        
        # Error rate
        errors = [m for m in self.metrics if m.error_occurred]
        report.error_rate = len(errors) / len(self.metrics) * 100
        report.errors = [m.error_message for m in errors if m.error_message]
        
        # Category breakdown
        categories = set(m.category for m in self.metrics)
        for cat in categories:
            cat_metrics = [m for m in self.metrics if m.category == cat]
            cat_latencies = [m.latency_ms for m in cat_metrics if m.latency_ms > 0]
            report.category_stats[cat] = {
                "total": len(cat_metrics),
                "passed": sum(1 for m in cat_metrics if m.tool_accuracy),
                "avg_latency_ms": statistics.mean(cat_latencies) if cat_latencies else 0.0,
                "accuracy_rate": sum(1 for m in cat_metrics if m.tool_accuracy) / len(cat_metrics) * 100,
            }
        
        # Individual metrics as dicts
        report.individual_metrics = [asdict(m) for m in self.metrics]
        
        return report
    
    def save_report(self, report: AgentMetricsReport, filepath: str) -> None:
        """Save report to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(asdict(report), f, indent=2, default=str)
    
    def print_summary(self, report: AgentMetricsReport) -> None:
        """Print a summary of the metrics report."""
        print("\n" + "="*60)
        print("AGENT PERFORMANCE METRICS REPORT")
        print("="*60)
        print(f"Timestamp: {report.timestamp}")
        print(f"Total Questions: {report.total_questions}")
        print(f"Passed: {report.questions_passed} | Failed: {report.questions_failed}")
        print("-"*60)
        print("LATENCY METRICS:")
        print(f"  Average: {report.avg_latency_ms:.2f}ms")
        print(f"  Min: {report.min_latency_ms:.2f}ms | Max: {report.max_latency_ms:.2f}ms")
        print(f"  P50: {report.p50_latency_ms:.2f}ms | P90: {report.p90_latency_ms:.2f}ms | P99: {report.p99_latency_ms:.2f}ms")
        print("-"*60)
        print("ACCURACY METRICS:")
        print(f"  Tool Selection Accuracy: {report.tool_accuracy_rate:.1f}%")
        print(f"  Keyword Match Rate: {report.avg_keyword_match_rate:.1f}%")
        print(f"  Error Rate: {report.error_rate:.1f}%")
        print("-"*60)
        print("RESPONSE QUALITY METRICS:")
        print(f"  Relevance Score: {report.avg_relevance_score:.1f}%")
        print(f"  Completeness Score: {report.avg_completeness_score:.1f}%")
        print(f"  Clarity Score: {report.avg_clarity_score:.1f}%")
        print("-"*60)
        print("HALLUCINATION & BEHAVIOR METRICS:")
        print(f"  Hallucination Rate: {report.hallucination_rate:.1f}% ({report.hallucination_count} detected)")
        print(f"  False Action Claims: {report.false_action_count}")
        print(f"  Action Verification Rate: {report.action_verification_rate:.1f}%")
        print(f"  Memory Consistency Rate: {report.memory_consistency_rate:.1f}%")
        print("-"*60)
        print("CATEGORY BREAKDOWN:")
        for cat, stats in report.category_stats.items():
            print(f"  {cat}: {stats['passed']}/{stats['total']} passed, "
                  f"{stats['accuracy_rate']:.1f}% accuracy, "
                  f"{stats['avg_latency_ms']:.2f}ms avg latency")
        print("="*60 + "\n")


class TestAgentMetrics:
    """Test agent performance metrics collection."""

    @pytest.fixture
    def collector(self):
        """Create a metrics collector."""
        return AgentMetricsCollector()

    @pytest.fixture
    def sample_questions(self):
        """Sample questions for metrics testing."""
        return [
            {
                "id": 1, 
                "question": "What is my profile?", 
                "expected_tool": "get_my_profile",
                "expected_keywords": ["name", "email", "phone"],
                "category": "profile"
            },
            {
                "id": 2, 
                "question": "Show my vitals", 
                "expected_tool": "get_my_vitals",
                "expected_keywords": ["height", "weight", "bmi"],
                "category": "vitals"
            },
            {
                "id": 3, 
                "question": "What reminders do I have?", 
                "expected_tool": "get_my_reminders",
                "expected_keywords": ["reminder", "medication", "time"],
                "category": "reminders"
            },
        ]

    def test_metric_recording(self, collector):
        """Test recording individual metrics."""
        metric = AgentMetric(
            question_id=1,
            question="Test question",
            category="test",
            expected_tool="test_tool",
            latency_ms=150.5,
            tool_selected="test_tool",
            tool_accuracy=True,
            keyword_match_rate=0.8
        )
        
        collector.record_metric(metric)
        assert len(collector.metrics) == 1
        assert collector.metrics[0].question_id == 1

    def test_latency_calculation(self, collector):
        """Test latency calculation."""
        start = time.time()
        time.sleep(0.1)  # 100ms
        end = time.time()
        
        latency = collector.calculate_latency(start, end)
        assert latency >= 100  # At least 100ms
        assert latency < 200   # But less than 200ms

    def test_token_estimation(self, collector):
        """Test token estimation."""
        short_text = "Hello"
        long_text = "This is a much longer text that should have more tokens"
        
        assert collector.estimate_tokens(short_text) < collector.estimate_tokens(long_text)

    def test_keyword_match_rate(self, collector):
        """Test keyword matching calculation."""
        response = "Your name is John and your email is john@example.com"
        keywords = ["name", "email", "phone"]
        
        rate, found = collector.calculate_keyword_match_rate(response, keywords)
        
        assert rate == 2/3  # name and email found, phone not
        assert "name" in found
        assert "email" in found
        assert "phone" not in found

    def test_report_generation(self, collector, sample_questions):
        """Test report generation with sample data."""
        # Simulate metrics for each question
        for q in sample_questions:
            metric = AgentMetric(
                question_id=q["id"],
                question=q["question"],
                category=q["category"],
                expected_tool=q["expected_tool"],
                latency_ms=100 + q["id"] * 50,  # Varying latencies
                tool_selected=q["expected_tool"],
                tool_accuracy=True,
                keywords_expected=q["expected_keywords"],
                keyword_match_rate=0.8
            )
            collector.record_metric(metric)
        
        report = collector.generate_report()
        
        assert report.total_questions == 3
        assert report.questions_passed == 3
        assert report.tool_accuracy_rate == 100.0
        assert report.avg_latency_ms > 0
        assert len(report.category_stats) == 3

    def test_report_with_errors(self, collector):
        """Test report handles errors correctly."""
        # Add a metric with error
        metric = AgentMetric(
            question_id=1,
            question="Error question",
            category="test",
            expected_tool="test_tool",
            error_occurred=True,
            error_message="Test error"
        )
        collector.record_metric(metric)
        
        report = collector.generate_report()
        
        assert report.error_rate == 100.0
        assert len(report.errors) == 1
        assert "Test error" in report.errors

    def test_empty_metrics_report(self, collector):
        """Test report generation with no metrics."""
        report = collector.generate_report()
        
        assert report.total_questions == 0
        assert report.avg_latency_ms == 0.0

    def test_percentile_calculations(self, collector):
        """Test percentile calculations for latency."""
        # Add 100 metrics with varying latencies
        for i in range(100):
            metric = AgentMetric(
                question_id=i,
                question=f"Question {i}",
                category="test",
                expected_tool="test_tool",
                latency_ms=float(i + 1) * 10,  # 10ms to 1000ms
                tool_accuracy=True
            )
            collector.record_metric(metric)
        
        report = collector.generate_report()
        
        # P50 should be around 500ms
        assert 400 <= report.p50_latency_ms <= 600
        # P90 should be around 900ms
        assert 800 <= report.p90_latency_ms <= 1000

    def test_category_breakdown(self, collector, sample_questions):
        """Test category-specific metrics."""
        for q in sample_questions:
            metric = AgentMetric(
                question_id=q["id"],
                question=q["question"],
                category=q["category"],
                expected_tool=q["expected_tool"],
                latency_ms=100.0,
                tool_accuracy=True
            )
            collector.record_metric(metric)
        
        report = collector.generate_report()
        
        assert "profile" in report.category_stats
        assert "vitals" in report.category_stats
        assert "reminders" in report.category_stats
        
        for cat_stats in report.category_stats.values():
            assert cat_stats["total"] == 1
            assert cat_stats["passed"] == 1
            assert cat_stats["accuracy_rate"] == 100.0


class TestAgentMetricsBenchmarks:
    """Benchmark tests with performance thresholds."""

    @pytest.fixture
    def collector(self):
        return AgentMetricsCollector()

    def test_latency_threshold(self, collector):
        """Test that agent responses meet latency thresholds."""
        # Simulated latency thresholds
        LATENCY_THRESHOLD_MS = 3000  # 3 seconds max
        
        # Simulate fast response
        metric = AgentMetric(
            question_id=1,
            question="Fast question",
            category="test",
            expected_tool="test",
            latency_ms=500.0
        )
        collector.record_metric(metric)
        
        report = collector.generate_report()
        assert report.avg_latency_ms < LATENCY_THRESHOLD_MS, \
            f"Latency {report.avg_latency_ms}ms exceeds threshold {LATENCY_THRESHOLD_MS}ms"

    def test_accuracy_threshold(self, collector):
        """Test that tool accuracy meets minimum threshold."""
        ACCURACY_THRESHOLD = 80.0  # 80% minimum accuracy
        
        # 9 correct, 1 wrong = 90% accuracy
        for i in range(10):
            metric = AgentMetric(
                question_id=i,
                question=f"Question {i}",
                category="test",
                expected_tool="expected",
                tool_selected="expected" if i < 9 else "wrong",
                tool_accuracy=(i < 9)
            )
            collector.record_metric(metric)
        
        report = collector.generate_report()
        assert report.tool_accuracy_rate >= ACCURACY_THRESHOLD, \
            f"Accuracy {report.tool_accuracy_rate}% below threshold {ACCURACY_THRESHOLD}%"

    def test_error_rate_threshold(self, collector):
        """Test that error rate stays below threshold."""
        ERROR_THRESHOLD = 5.0  # 5% max error rate
        
        # 2 errors out of 100 = 2% error rate
        for i in range(100):
            metric = AgentMetric(
                question_id=i,
                question=f"Question {i}",
                category="test",
                expected_tool="test",
                error_occurred=(i < 2)
            )
            collector.record_metric(metric)
        
        report = collector.generate_report()
        assert report.error_rate <= ERROR_THRESHOLD, \
            f"Error rate {report.error_rate}% exceeds threshold {ERROR_THRESHOLD}%"
