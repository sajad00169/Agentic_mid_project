"""
Automated Test Suite for Student Fee Management and Financial Assistance Agent.
Validates all 6 examination scenarios plus bonus HITL and university-level queries.
Captures detailed execution traces to logs/execution_traces.json.
"""

import sys
import os
import time
import unittest
from langgraph.types import Command

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.graph import build_fee_agent_graph
from langgraph.checkpoint.memory import MemorySaver
from data.database import db
from src.logger import tracer

class TestFeeManagementAgent(unittest.TestCase):
    """Test suite covering required fee management scenarios."""

    @classmethod
    def setUpClass(cls):
        # Reset DB to ensure fresh dataset
        db.load_data()

    def setUp(self):
        # Reset in-memory database records to ensure 100% test isolation
        from data.generate_dataset import DATASET
        import json
        db.records = {item["student_id"].upper(): json.loads(json.dumps(item)) for item in DATASET}
        self.checkpointer = MemorySaver()
        self.agent = build_fee_agent_graph(self.checkpointer)

    def test_scenario_1_fully_paid_student(self):
        """Scenario 1: A student with fully paid fees (STD-2024-001)."""
        print("\n" + "="*70)
        print("RUNNING SCENARIO 1: Fully Paid Student (STD-2024-001 - Amina Khan)")
        print("="*70)

        query = "What is the fee payment status and balance for student STD-2024-001?"
        thread_id = "test-scenario-1"
        config = {"configurable": {"thread_id": thread_id}}

        t0 = time.time()
        result = self.agent.invoke({"query": query}, config=config)
        duration = round((time.time() - t0) * 1000, 2)

        tracer.record_run("SCENARIO_1_FULLY_PAID", query, {}, result, duration_ms=duration)

        # Assertions
        self.assertEqual(result["payment_status"], "PAID")
        self.assertEqual(result["student_record"]["outstanding_balance"], 0.0)
        self.assertTrue(result["calculation_validated"])
        self.assertFalse(result.get("requires_human_approval", False))
        self.assertIn("Fully Paid", result["final_response"])
        print("[PASSED] Scenario 1: Fully paid status confirmed, zero balance verified.")

    def test_scenario_2_partially_paid_student(self):
        """Scenario 2: A student with partially paid fees on installment (STD-2024-011)."""
        print("\n" + "="*70)
        print("RUNNING SCENARIO 2: Partially Paid Student (STD-2024-011 - Danish Riaz)")
        print("="*70)

        query = "Show installment schedule and remaining balance for student STD-2024-011"
        thread_id = "test-scenario-2"
        config = {"configurable": {"thread_id": thread_id}}

        t0 = time.time()
        result = self.agent.invoke({"query": query}, config=config)
        duration = round((time.time() - t0) * 1000, 2)

        tracer.record_run("SCENARIO_2_PARTIALLY_PAID", query, {}, result, duration_ms=duration)

        # Assertions
        self.assertEqual(result["payment_status"], "PARTIALLY_PAID")
        self.assertGreater(result["student_record"]["outstanding_balance"], 0.0)
        self.assertTrue(result["installment_details"]["has_installment_plan"])
        self.assertEqual(result["installment_details"]["installments_remaining"], 1)
        self.assertIn("Partially Paid", result["final_response"])
        print("[PASSED] Scenario 2: Installment plan detected, remaining installment accurate.")

    def test_scenario_3_overdue_student(self):
        """Scenario 3: A student with overdue fees (STD-2024-019)."""
        print("\n" + "="*70)
        print("RUNNING SCENARIO 3: Overdue Student (STD-2024-019 - Farhan Saeed)")
        print("="*70)

        query = "Check if fee is overdue for student STD-2024-019"
        thread_id = "test-scenario-3"
        config = {"configurable": {"thread_id": thread_id}}

        t0 = time.time()
        result = self.agent.invoke({"query": query}, config=config)
        duration = round((time.time() - t0) * 1000, 2)

        tracer.record_run("SCENARIO_3_OVERDUE", query, {}, result, duration_ms=duration)

        # Assertions
        self.assertEqual(result["payment_status"], "OVERDUE")
        self.assertGreater(result["student_record"]["outstanding_balance"], 0.0)
        self.assertIn("OVERDUE", result["final_response"])
        print("[PASSED] Scenario 3: Overdue status flagged and penalty notice formatted.")

    def test_scenario_4_scholarship_concession_student(self):
        """Scenario 4: A student with a scholarship or concession (STD-2024-002)."""
        print("\n" + "="*70)
        print("RUNNING SCENARIO 4: Scholarship Student (STD-2024-002 - Zainab Fatima)")
        print("="*70)

        query = "What scholarship is applied to student STD-2024-002 and what was their net fee?"
        thread_id = "test-scenario-4"
        config = {"configurable": {"thread_id": thread_id}}

        t0 = time.time()
        result = self.agent.invoke({"query": query}, config=config)
        duration = round((time.time() - t0) * 1000, 2)

        tracer.record_run("SCENARIO_4_SCHOLARSHIP", query, {}, result, duration_ms=duration)

        # Assertions
        sc = result["student_record"]["scholarship_or_concession"]
        self.assertEqual(sc["type"], "Merit Scholarship")
        self.assertEqual(sc["percentage"], 50.0)
        self.assertEqual(sc["status"], "Approved")
        self.assertEqual(result["student_record"]["net_fee"], 65000.0)
        self.assertTrue(result["calculation_validated"])
        print("[PASSED] Scenario 4: Merit scholarship verified, net fee deduction validated.")

    def test_scenario_5_inconsistent_record_reflection_and_hitl(self):
        """Scenario 5: An incomplete or inconsistent payment record (STD-2024-031)."""
        print("\n" + "="*70)
        print("RUNNING SCENARIO 5: Inconsistent Record with Reflection & HITL (STD-2024-031)")
        print("="*70)

        query = "Verify payment ledger and calculate exact balance for STD-2024-031"
        thread_id = "test-scenario-5"
        config = {"configurable": {"thread_id": thread_id}}

        # Phase 1: Agent processes query, reflection detects arithmetic flaw, graph halts at interrupt
        t0 = time.time()
        result1 = self.agent.invoke({"query": query}, config=config)
        duration1 = round((time.time() - t0) * 1000, 2)

        self.assertIn("__interrupt__", result1, "Graph must pause at Human-in-the-Loop interrupt.")
        interrupt_payload = result1["__interrupt__"][0].value

        tracer.record_run(
            "SCENARIO_5_INCONSISTENT_PAUSE",
            query,
            {},
            result1,
            interrupted=True,
            interrupt_payload=interrupt_payload,
            duration_ms=duration1
        )

        # Verify reflection caught the arithmetic mismatch
        self.assertEqual(result1["payment_status"], "INCOMPLETE_RECORD")
        self.assertIn("Arithmetic Discrepancy Detected", result1["reflection_critique"])
        self.assertIn("REQ-AUDIT-STD-2024-031", interrupt_payload["request_id"])
        print("--> Interruption verified! Reflection caught discrepancy:", result1["reflection_critique"][:85])

        # Phase 2: Administrator reviews and provides HITL clearance
        decision = {
            "approved": True,
            "authorized_by": "Senior Financial Auditor",
            "comments": "Reviewed bank deposit slips and cleared record."
        }
        t1 = time.time()
        result2 = self.agent.invoke(Command(resume=decision), config=config)
        duration2 = round((time.time() - t1) * 1000, 2)

        tracer.record_run(
            "SCENARIO_5_INCONSISTENT_RESUMED",
            query,
            result1,
            result2,
            hitl_decision=decision,
            duration_ms=duration2
        )

        self.assertNotIn("__interrupt__", result2)
        self.assertEqual(result2["verification_status"], "Verified")
        self.assertIn("Human-in-the-Loop Approval Decision", result2["final_response"])
        print("[PASSED] Scenario 5: Reflection detected flaw, HITL paused graph, and resumed after clearance.")

    def test_scenario_6_department_level_fee_summary(self):
        """Scenario 6: A department-level fee collection query."""
        print("\n" + "="*70)
        print("RUNNING SCENARIO 6: Department-Level Fee Summary (Computer Science)")
        print("="*70)

        query = "What is the total fee collected and outstanding in the Computer Science department?"
        thread_id = "test-scenario-6"
        config = {"configurable": {"thread_id": thread_id}}

        t0 = time.time()
        result = self.agent.invoke({"query": query}, config=config)
        duration = round((time.time() - t0) * 1000, 2)

        tracer.record_run("SCENARIO_6_DEPT_SUMMARY", query, {}, result, duration_ms=duration)

        summary = result["summary_report"]
        self.assertTrue(summary["success"])
        self.assertGreater(summary["total_amount_collected"], 0)
        self.assertGreater(summary["total_outstanding_balance"], 0)
        self.assertEqual(summary["scope"], "Department: Computer Science")
        self.assertIn("Financial Summary Report", result["final_response"])
        print(f"[PASSED] Scenario 6: CS Department summary generated. Collection rate: {summary['collection_efficiency_pct']}%.")

    def test_scenario_7_concession_approval_workflow(self):
        """Bonus Scenario 7: Concession Approval HITL Workflow (STD-2024-029)."""
        print("\n" + "="*70)
        print("RUNNING SCENARIO 7: Concession Approval HITL Workflow (STD-2024-029)")
        print("="*70)

        query = "Review pending financial hardship concession for student STD-2024-029"
        thread_id = "test-scenario-7"
        config = {"configurable": {"thread_id": thread_id}}

        result1 = self.agent.invoke({"query": query}, config=config)
        self.assertIn("__interrupt__", result1)
        self.assertEqual(result1["payment_status"], "CONCESSION_PENDING")

        # Administrator approves concession
        decision = {
            "approved": True,
            "authorized_by": "Director Financial Aid",
            "comments": "Eligible based on household income documentation."
        }
        result2 = self.agent.invoke(Command(resume=decision), config=config)
        
        self.assertEqual(result2["student_record"]["scholarship_or_concession"]["status"], "Approved")
        self.assertEqual(result2["student_record"]["outstanding_balance"], 0.0) # 110k - 55k discount - 55k paid = 0
        self.assertEqual(result2["student_record"]["payment_status"], "PAID")
        print("[PASSED] Scenario 7: Concession approved via HITL, balance recalculated to 0.00 PKR.")

    def test_scenario_8_university_overdue_roster_query(self):
        """Bonus Scenario 8: University-wide overdue list query."""
        print("\n" + "="*70)
        print("RUNNING SCENARIO 8: University-wide Overdue Query")
        print("="*70)

        query = "Which payments are overdue across the university?"
        thread_id = "test-scenario-8"
        config = {"configurable": {"thread_id": thread_id}}

        result = self.agent.invoke({"query": query}, config=config)
        self.assertEqual(result["query_type"], "SEARCH_OVERDUE")
        self.assertGreater(len(result["search_results"]), 0)
        self.assertIn("Overdue Payment Roster", result["final_response"])
        print(f"[PASSED] Scenario 8: Successfully retrieved {len(result['search_results'])} overdue students.")

if __name__ == "__main__":
    unittest.main()
