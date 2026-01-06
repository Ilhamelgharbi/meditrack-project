#!/usr/bin/env python3
# tests/agent/test_live_agent.py
"""
Live Agent Tests - Tests against running server at localhost:8000

Tests real scenarios:
- Memory persistence
- Allergy updates and queries
- Conversation context
- Action verification

Usage:
    python tests/agent/test_live_agent.py
    python tests/agent/test_live_agent.py --email user@example.com --password password123
"""

import requests
import json
import time
import argparse
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ConversationTurn:
    """Single turn in a conversation."""
    query: str
    response: str
    latency_ms: float
    success: bool
    error: Optional[str] = None


@dataclass
class TestResult:
    """Result of a single test case."""
    test_name: str
    passed: bool
    conversation: List[ConversationTurn] = field(default_factory=list)
    notes: str = ""


class LiveAgentTester:
    """Test agent against live server."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.token: Optional[str] = None
        self.headers: Dict[str, str] = {}
        self.results: List[TestResult] = []
        
    def login(self, email: str, password: str) -> bool:
        """Login and get authentication token."""
        try:
            response = requests.post(
                f"{self.base_url}/auth/login",
                data={"username": email, "password": password},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.headers = {"Authorization": f"Bearer {self.token}"}
                print(f"✅ Logged in as {email}")
                return True
            else:
                print(f"❌ Login failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def query_agent(self, query: str, thread_id: Optional[str] = None) -> ConversationTurn:
        """Send a query to the agent."""
        start_time = time.time()
        
        try:
            payload = {"query": query}
            if thread_id:
                payload["thread_id"] = thread_id
                
            response = requests.post(
                f"{self.base_url}/agent/query",
                json=payload,
                headers=self.headers,
                timeout=30
            )
            
            latency = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                return ConversationTurn(
                    query=query,
                    response=data.get("response", ""),
                    latency_ms=latency,
                    success=True
                )
            else:
                return ConversationTurn(
                    query=query,
                    response="",
                    latency_ms=latency,
                    success=False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return ConversationTurn(
                query=query,
                response="",
                latency_ms=latency,
                success=False,
                error=str(e)
            )
    
    def print_turn(self, turn: ConversationTurn):
        """Print a conversation turn."""
        status = "✅" if turn.success else "❌"
        print(f"\n{status} Query: {turn.query}")
        print(f"   Latency: {turn.latency_ms:.0f}ms")
        if turn.success:
            # Truncate long responses
            resp = turn.response[:500] + "..." if len(turn.response) > 500 else turn.response
            print(f"   Response: {resp}")
        else:
            print(f"   Error: {turn.error}")
    
    # ==========================================================================
    # TEST CASES
    # ==========================================================================
    
    def test_allergy_memory(self) -> TestResult:
        """
        Test: Memory persistence for allergies
        1. Ask about current allergies
        2. Say "I have an allergy to cats"
        3. Ask again "what allergies do I have?"
        4. Verify cats is mentioned
        """
        print("\n" + "="*60)
        print("TEST: Allergy Memory Persistence")
        print("="*60)
        
        result = TestResult(test_name="Allergy Memory")
        
        # Step 1: Ask about current allergies
        turn1 = self.query_agent("What allergies do I have?")
        self.print_turn(turn1)
        result.conversation.append(turn1)
        
        if not turn1.success:
            result.passed = False
            result.notes = "Failed to query initial allergies"
            return result
        
        # Step 2: Update with cat allergy
        turn2 = self.query_agent("I have an allergy to cats")
        self.print_turn(turn2)
        result.conversation.append(turn2)
        
        if not turn2.success:
            result.passed = False
            result.notes = "Failed to update allergy"
            return result
        
        # Small delay to ensure update is processed
        time.sleep(1)
        
        # Step 3: Ask about allergies again
        turn3 = self.query_agent("What allergies do I have now?")
        self.print_turn(turn3)
        result.conversation.append(turn3)
        
        if not turn3.success:
            result.passed = False
            result.notes = "Failed to query allergies after update"
            return result
        
        # Step 4: Verify cats is mentioned
        if "cat" in turn3.response.lower():
            result.passed = True
            result.notes = "✅ Agent remembered cat allergy!"
        else:
            result.passed = False
            result.notes = "❌ Agent did NOT remember cat allergy in response"
        
        return result
    
    def test_profile_update(self) -> TestResult:
        """
        Test: Profile update and verification
        1. Ask about profile
        2. Update weight
        3. Verify weight was updated
        """
        print("\n" + "="*60)
        print("TEST: Profile Update")
        print("="*60)
        
        result = TestResult(test_name="Profile Update")
        
        # Step 1: Get current profile
        turn1 = self.query_agent("What is my current weight?")
        self.print_turn(turn1)
        result.conversation.append(turn1)
        
        # Step 2: Update weight
        turn2 = self.query_agent("Update my weight to 75 kg")
        self.print_turn(turn2)
        result.conversation.append(turn2)
        
        time.sleep(1)
        
        # Step 3: Verify update
        turn3 = self.query_agent("What is my weight now?")
        self.print_turn(turn3)
        result.conversation.append(turn3)
        
        if turn3.success and "75" in turn3.response:
            result.passed = True
            result.notes = "✅ Weight updated and verified!"
        else:
            result.passed = False
            result.notes = "❌ Weight update not verified in response"
        
        return result
    
    def test_medication_query(self) -> TestResult:
        """
        Test: Medication queries
        """
        print("\n" + "="*60)
        print("TEST: Medication Query")
        print("="*60)
        
        result = TestResult(test_name="Medication Query")
        
        turn1 = self.query_agent("What medications am I taking?")
        self.print_turn(turn1)
        result.conversation.append(turn1)
        
        if turn1.success and len(turn1.response) > 20:
            result.passed = True
            result.notes = "✅ Got medication list"
        else:
            result.passed = False
            result.notes = "❌ No proper medication response"
        
        return result
    
    def test_reminder_set_and_verify(self) -> TestResult:
        """
        Test: Set reminder and verify it was actually created
        """
        print("\n" + "="*60)
        print("TEST: Reminder Set and Verify")
        print("="*60)
        
        result = TestResult(test_name="Reminder Set and Verify")
        
        # Step 1: Set a reminder
        turn1 = self.query_agent("Set a reminder for my medication at 9 AM")
        self.print_turn(turn1)
        result.conversation.append(turn1)
        
        time.sleep(1)
        
        # Step 2: Check reminders
        turn2 = self.query_agent("What reminders do I have?")
        self.print_turn(turn2)
        result.conversation.append(turn2)
        
        # Check if reminder claims were verified
        claims_set = any(word in turn1.response.lower() for word in ["set", "scheduled", "created", "done"])
        has_9am = "9" in turn2.response
        
        if turn1.success and turn2.success:
            if claims_set and has_9am:
                result.passed = True
                result.notes = "✅ Reminder set and verified!"
            elif claims_set and not has_9am:
                result.passed = False
                result.notes = "⚠️ Agent CLAIMED to set reminder but not found - POSSIBLE HALLUCINATION"
            else:
                result.passed = True
                result.notes = "Agent response received"
        else:
            result.passed = False
            result.notes = "❌ Query failed"
        
        return result
    
    def test_vitals_query(self) -> TestResult:
        """
        Test: Vitals query
        """
        print("\n" + "="*60)
        print("TEST: Vitals Query")
        print("="*60)
        
        result = TestResult(test_name="Vitals Query")
        
        turn1 = self.query_agent("What are my vital signs?")
        self.print_turn(turn1)
        result.conversation.append(turn1)
        
        # Check for expected vitals keywords
        vitals_keywords = ["height", "weight", "bmi", "blood pressure", "cm", "kg"]
        found_keywords = [kw for kw in vitals_keywords if kw in turn1.response.lower()]
        
        if turn1.success and len(found_keywords) >= 2:
            result.passed = True
            result.notes = f"✅ Got vitals with keywords: {found_keywords}"
        else:
            result.passed = False
            result.notes = f"❌ Missing vital signs info. Found: {found_keywords}"
        
        return result
    
    def test_adherence_stats(self) -> TestResult:
        """
        Test: Adherence statistics query
        """
        print("\n" + "="*60)
        print("TEST: Adherence Stats")
        print("="*60)
        
        result = TestResult(test_name="Adherence Stats")
        
        turn1 = self.query_agent("How well am I taking my medications?")
        self.print_turn(turn1)
        result.conversation.append(turn1)
        
        adherence_keywords = ["adherence", "compliance", "%", "rate", "doses", "taken"]
        found = [kw for kw in adherence_keywords if kw in turn1.response.lower()]
        
        if turn1.success and len(found) >= 1:
            result.passed = True
            result.notes = f"✅ Got adherence info"
        else:
            result.passed = False
            result.notes = "❌ No adherence info"
        
        return result
    
    def test_conversation_memory(self) -> TestResult:
        """
        Test: Does agent remember earlier in conversation?
        """
        print("\n" + "="*60)
        print("TEST: Conversation Memory")
        print("="*60)
        
        result = TestResult(test_name="Conversation Memory")
        
        # Ask about medications
        turn1 = self.query_agent("What is my first medication?")
        self.print_turn(turn1)
        result.conversation.append(turn1)
        
        # Follow up question
        turn2 = self.query_agent("What is the dosage for that one?")
        self.print_turn(turn2)
        result.conversation.append(turn2)
        
        # Check if it understood the context
        if turn2.success and ("mg" in turn2.response.lower() or "dosage" in turn2.response.lower()):
            result.passed = True
            result.notes = "✅ Agent understood context"
        else:
            result.passed = False
            result.notes = "❌ Agent may have lost context"
        
        return result
    
    def run_all_tests(self) -> None:
        """Run all test cases."""
        print("\n" + "="*60)
        print("LIVE AGENT TEST SUITE")
        print(f"Server: {self.base_url}")
        print(f"Time: {datetime.now().isoformat()}")
        print("="*60)
        
        tests = [
            self.test_medication_query,
            self.test_vitals_query,
            self.test_allergy_memory,
            self.test_profile_update,
            self.test_reminder_set_and_verify,
            self.test_adherence_stats,
            self.test_conversation_memory,
        ]
        
        for test_func in tests:
            try:
                result = test_func()
                self.results.append(result)
            except Exception as e:
                print(f"❌ Test {test_func.__name__} crashed: {e}")
                self.results.append(TestResult(
                    test_name=test_func.__name__,
                    passed=False,
                    notes=f"Exception: {e}"
                ))
        
        self.print_summary()
    
    def print_summary(self) -> None:
        """Print test summary."""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        
        for result in self.results:
            status = "✅ PASS" if result.passed else "❌ FAIL"
            print(f"{status}: {result.test_name}")
            if result.notes:
                print(f"       {result.notes}")
        
        print("-"*60)
        print(f"TOTAL: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
        
        # Calculate average latency
        all_latencies = []
        for r in self.results:
            for turn in r.conversation:
                if turn.latency_ms > 0:
                    all_latencies.append(turn.latency_ms)
        
        if all_latencies:
            avg_latency = sum(all_latencies) / len(all_latencies)
            print(f"Average Response Time: {avg_latency:.0f}ms")
        
        print("="*60)


def main():
    parser = argparse.ArgumentParser(description="Run live agent tests")
    parser.add_argument("--url", default="http://localhost:8000", help="Server URL")
    parser.add_argument("--email", default="patient@example.com", help="Login email")
    parser.add_argument("--password", default="password123", help="Login password")
    args = parser.parse_args()
    
    tester = LiveAgentTester(base_url=args.url)
    
    if not tester.login(args.email, args.password):
        print("\n⚠️ Could not login. Make sure the server is running and credentials are correct.")
        print("Try: python tests/agent/test_live_agent.py --email YOUR_EMAIL --password YOUR_PASSWORD")
        return
    
    tester.run_all_tests()


if __name__ == "__main__":
    main()
