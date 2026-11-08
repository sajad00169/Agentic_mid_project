"""
Interactive Demonstration CLI for Student Fee Management and Financial Assistance Agent.
Allows interactive multi-turn chatting, quick scenario replay, and real-time HITL approvals.
"""

import sys
import os
import time
from typing import Dict, Any
from langgraph.types import Command
from langgraph.checkpoint.memory import MemorySaver

from src.graph import build_fee_agent_graph
from data.database import db

def print_banner():
    banner = r"""
=============================================================================
   STUDENT FEE MANAGEMENT & FINANCIAL ASSISTANCE AGENT (LANGGRAPH)
   Examination 5 - Finance & Accounts Department Autonomous Agent
=============================================================================
  * Multi-turn Conversation & Checkpointing
  * Conditional Routing (PAID, PARTIALLY_PAID, OVERDUE, INCOMPLETE, CONCESSION)
  * Reflection Engine & Arithmetic Validator
  * Human-in-the-Loop (HITL) Administrative Authorization Gate
=============================================================================
"""
    print(banner)

def run_scenario(agent, name: str, query: str, thread_id: str, hitl_auto_decision: Dict[str, Any] = None):
    print(f"\n{'='*75}")
    print(f">> DEMO SCENARIO: {name}")
    print(f">> QUERY: \"{query}\"")
    print(f"{'='*75}")

    config = {"configurable": {"thread_id": thread_id}}
    res = agent.invoke({"query": query}, config=config)

    # Check for HITL Interruption
    if "__interrupt__" in res:
        payload = res["__interrupt__"][0].value
        print("\n [!] HUMAN-IN-THE-LOOP APPROVAL REQUIRED")
        print(f"     Action: {payload.get('action_type')}")
        print(f"     Student: {payload.get('student_id')} - {payload.get('student_name')}")
        print(f"     Prompt: {payload.get('prompt')}")
        
        if hitl_auto_decision:
            print(f"     --> [Automated HITL Decision] Approving as: {hitl_auto_decision['authorized_by']}")
            print(f"     --> Comments: {hitl_auto_decision['comments']}")
            res = agent.invoke(Command(resume=hitl_auto_decision), config=config)
        else:
            print("     --> Workflow paused awaiting administrative decision.")

    print("\n--- AGENT RESPONSE ---")
    print(res.get("final_response") or res.get("draft_response"))
    print("\n--- AUDIT TRAIL ---")
    for step in res.get("audit_trail", []):
        print(f"  * {step}")

def interactive_loop():
    print_banner()
    db.load_data()
    checkpointer = MemorySaver()
    agent = build_fee_agent_graph(checkpointer)
    session_thread = f"cli-session-{int(time.time())}"
    config = {"configurable": {"thread_id": session_thread}}

    print("Options:")
    print(" 1. Run Automated Test Tour (All 6 Scenarios)")
    print(" 2. Interactive Natural Language Chat")
    print(" 3. Exit")

    choice = input("\nSelect option (1-3) [default: 1]: ").strip()
    if choice == "2":
        print(f"\nEntering interactive chat mode (Thread: {session_thread}). Type 'exit' to quit.\n")
        while True:
            try:
                user_input = input("\nYou: ").strip()
                if not user_input or user_input.lower() in ["exit", "quit", "q"]:
                    print("Exiting interactive mode. Goodbye!")
                    break

                res = agent.invoke({"query": user_input}, config=config)
                
                # Check for interruption
                if "__interrupt__" in res:
                    payload = res["__interrupt__"][0].value
                    print(f"\n[!] Human-in-the-Loop Approval Required:")
                    print(f"    Prompt: {payload.get('prompt')}")
                    dec_input = input("    Approve request? (y/n) [default: y]: ").strip().lower()
                    approved = dec_input != "n"
                    officer_name = input("    Authorized Officer Name [Finance Director]: ").strip() or "Finance Director"
                    notes = input("    Audit Comments: ").strip() or "Approved via CLI interactive session."

                    decision = {
                        "approved": approved,
                        "authorized_by": officer_name,
                        "comments": notes
                    }
                    res = agent.invoke(Command(resume=decision), config=config)

                print("\nAgent:")
                print(res.get("final_response") or res.get("draft_response"))

            except KeyboardInterrupt:
                print("\nSession interrupted.")
                break
    elif choice == "3":
        print("Goodbye!")
        sys.exit(0)
    else:
        # Run automated tour
        print("\nStarting automated tour of scenarios...")
        run_scenario(
            agent,
            "1. Fully Paid Student",
            "What is the payment status for student STD-2024-001?",
            "tour-1"
        )
        run_scenario(
            agent,
            "2. Partially Paid Student with Installment Plan",
            "Show installment breakdown for student STD-2024-011",
            "tour-2"
        )
        run_scenario(
            agent,
            "3. Overdue Student Alert",
            "Check overdue status for student STD-2024-019",
            "tour-3"
        )
        run_scenario(
            agent,
            "4. Scholarship Recipient Record",
            "What scholarship is applied for student STD-2024-002?",
            "tour-4"
        )
        run_scenario(
            agent,
            "5. Inconsistent Record (Reflection + HITL Verification)",
            "Verify balance and audit student STD-2024-031",
            "tour-5",
            hitl_auto_decision={
                "approved": True,
                "authorized_by": "Chief Financial Auditor",
                "comments": "Audited bank statements. Cleared discrepancy."
            }
        )
        run_scenario(
            agent,
            "6. Department-Level Fee Collection Summary",
            "What is the total fee collected and outstanding in Computer Science?",
            "tour-6"
        )
        print("\n" + "="*75)
        print("Tour complete! All scenarios successfully demonstrated.")
        print("="*75)

if __name__ == "__main__":
    interactive_loop()
