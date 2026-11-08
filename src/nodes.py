"""
Graph Nodes implementation for Student Fee Management Agent.
Implements router, status handlers, reflection, HITL gates, and response synthesizers.
"""

import re
from typing import Dict, Any, List
from datetime import datetime
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.types import interrupt

from src.state import AgentState
from src.tools import (
    retrieve_student_record,
    calculate_outstanding_balance,
    check_payment_status,
    retrieve_installment_info,
    generate_payment_summary,
    search_students_by_criteria
)
from data.database import db
from src.reflection import ReflectionEngine
from src.hitl import ApprovalManager
from src.config import REFERENCE_DATE, CURRENCY_SYMBOL

# -------------------------------------------------------------
# 1. Router & Intent Classifier
# -------------------------------------------------------------
def router_node(state: AgentState) -> Dict[str, Any]:
    """Parse query intent, extract student ID or department, and set initial state."""
    query = state.get("query", "")
    if not query and state.get("messages"):
        last_human = next((m.content for m in reversed(state["messages"]) if isinstance(m, HumanMessage)), "")
        query = str(last_human)

    q = query.lower()
    audit_trail = list(state.get("audit_trail", []))
    audit_trail.append(f"router_node: Received query '{query[:60]}...'")

    # Extract Student ID
    match_id = re.search(r"std[-_ ]?2024[-_ ]?\d{3}", q, re.IGNORECASE)
    student_id = match_id.group(0).upper().replace("_", "-").replace(" ", "-") if match_id else None

    # Extract Department
    department = None
    for d in ["computer science", "business administration", "electrical engineering", "civil engineering", "mathematics"]:
        if d in q:
            department = d.title()
            break

    # Determine Query Type
    if "approve" in q and ("concession" in q or "scholarship" in q or "record" in q):
        query_type = "CONCESSION_APPROVAL"
    elif "verify" in q and ("record" in q or "exceptional" in q or "wire" in q):
        query_type = "EXCEPTIONAL_VERIFICATION"
    elif "inconsistent" in q or "audit" in q or "discrepancy" in q or "incomplete" in q:
        query_type = "AUDIT_QUERY"
    elif "overdue" in q and not student_id:
        query_type = "SEARCH_OVERDUE"
    elif ("scholarship" in q or "concession" in q or "financial assistance" in q) and not student_id:
        query_type = "SEARCH_SCHOLARSHIPS"
    elif "outstanding" in q and not student_id and ("students" in q or "who" in q or "which" in q):
        query_type = "SEARCH_OUTSTANDING"
    elif "summary" in q or "collected" in q or "total fee" in q or "report" in q or department:
        if student_id:
            query_type = "STUDENT_QUERY"
        else:
            query_type = "SUMMARY_QUERY"
    elif student_id:
        query_type = "STUDENT_QUERY"
    else:
        query_type = "GENERAL_QUERY"

    audit_trail.append(f"router_node: Classified as '{query_type}' (student_id={student_id}, dept={department})")

    return {
        "query": query,
        "query_type": query_type,
        "student_id": student_id,
        "department": department,
        "audit_trail": audit_trail,
        "reflection_retries": state.get("reflection_retries", 0)
    }

# -------------------------------------------------------------
# 2. Student Record Retrieval & Calculation Node
# -------------------------------------------------------------
def retrieve_student_node(state: AgentState) -> Dict[str, Any]:
    """Retrieve full record, run balance calculation, check status, and inspect installment info."""
    student_id = state.get("student_id")
    audit_trail = list(state.get("audit_trail", []))
    
    if not student_id:
        audit_trail.append("retrieve_student_node: No student_id found in state.")
        return {
            "payment_status": "UNKNOWN",
            "audit_trail": audit_trail
        }

    rec_res = retrieve_student_record.invoke({"student_id": student_id})
    if not rec_res.get("success", False):
        audit_trail.append(f"retrieve_student_node: Student {student_id} not found.")
        return {
            "student_record": None,
            "payment_status": "NOT_FOUND",
            "audit_trail": audit_trail
        }

    student_record = rec_res["record"]
    calc_res = calculate_outstanding_balance.invoke({"student_id": student_id})
    status_res = check_payment_status.invoke({"student_id": student_id})
    inst_res = retrieve_installment_info.invoke({"student_id": student_id})

    # Determine status
    payment_status = status_res.get("verified_status", student_record.get("payment_status", "UNKNOWN"))
    
    # Check if HITL approval required
    requires_approval = ApprovalManager.should_require_approval(student_record, state.get("query_type", ""))

    audit_trail.append(
        f"retrieve_student_node: Retrieved {student_id} ({student_record['name']}) -> "
        f"Status: {payment_status}, Balance: {student_record['outstanding_balance']}, Requires HITL: {requires_approval}"
    )

    return {
        "student_record": student_record,
        "calculation_details": calc_res,
        "payment_status": payment_status,
        "installment_details": inst_res,
        "requires_human_approval": requires_approval,
        "audit_trail": audit_trail
    }

# -------------------------------------------------------------
# 3. Status Specialized Handlers
# -------------------------------------------------------------
def handle_paid_node(state: AgentState) -> Dict[str, Any]:
    """Process fully settled records, generate clearance confirmation."""
    audit_trail = list(state.get("audit_trail", []))
    audit_trail.append("handle_paid_node: Processing paid clearance.")
    rec = state.get("student_record", {})
    
    draft = (
        f"### Fee Status: Fully Paid & Cleared\n\n"
        f"- **Student ID:** `{rec.get('student_id')}`\n"
        f"- **Name:** **{rec.get('name')}**\n"
        f"- **Program:** {rec.get('program')} ({rec.get('department')})\n"
        f"- **Semester:** {rec.get('semester')}\n"
        f"- **Total Fee:** {rec.get('total_semester_fee'):,.2f} {CURRENCY_SYMBOL}\n"
        f"- **Scholarship/Concession:** {rec.get('scholarship_or_concession', {}).get('type')} "
        f"({rec.get('scholarship_or_concession', {}).get('percentage')}%, Discount: {rec.get('scholarship_or_concession', {}).get('amount'):,.2f} {CURRENCY_SYMBOL})\n"
        f"- **Amount Paid:** {rec.get('amount_paid'):,.2f} {CURRENCY_SYMBOL}\n"
        f"- **Outstanding Balance:** **0.00 {CURRENCY_SYMBOL}**\n"
        f"- **Verification Status:** `{rec.get('verification_status')}`\n\n"
        f"**Clearance Notice:** Fee obligations for {rec.get('semester')} are 100% fulfilled. Student is eligible for examination slips and course registration."
    )
    return {"draft_response": draft, "audit_trail": audit_trail}

def handle_partial_node(state: AgentState) -> Dict[str, Any]:
    """Process partially paid records with active installment schedule."""
    audit_trail = list(state.get("audit_trail", []))
    audit_trail.append("handle_partial_node: Processing active installment schedule.")
    rec = state.get("student_record", {})
    inst = state.get("installment_details", {})

    draft = (
        f"### Fee Status: Partially Paid (On-Track Installment Plan)\n\n"
        f"- **Student ID:** `{rec.get('student_id')}`\n"
        f"- **Name:** **{rec.get('name')}**\n"
        f"- **Program:** {rec.get('program')} ({rec.get('department')})\n"
        f"- **Total Semester Fee:** {rec.get('total_semester_fee'):,.2f} {CURRENCY_SYMBOL}\n"
        f"- **Amount Paid:** {rec.get('amount_paid'):,.2f} {CURRENCY_SYMBOL}\n"
        f"- **Outstanding Balance:** **{rec.get('outstanding_balance'):,.2f} {CURRENCY_SYMBOL}**\n\n"
        f"#### Installment Schedule Details\n"
        f"- **Plan Type:** {inst.get('plan_type')}\n"
        f"- **Total Installments:** {inst.get('total_installments')}\n"
        f"- **Installments Paid:** {inst.get('installments_paid')} of {inst.get('total_installments')}\n"
        f"- **Remaining Installments:** {inst.get('installments_remaining')}\n"
        f"- **Next Installment Due:** **{inst.get('next_installment_due')}**\n"
        f"- **Next Installment Amount:** **{inst.get('next_installment_amount'):,.2f} {CURRENCY_SYMBOL}**\n\n"
        f"**Advisory:** The student is compliant with the approved installment schedule. Please ensure the next installment is deposited by the due date."
    )
    return {"draft_response": draft, "audit_trail": audit_trail}

def handle_overdue_node(state: AgentState) -> Dict[str, Any]:
    """Process overdue fee records, calculate days elapsed, and issue penalty notices."""
    audit_trail = list(state.get("audit_trail", []))
    audit_trail.append("handle_overdue_node: Processing overdue escalation notice.")
    rec = state.get("student_record", {})
    calc = state.get("calculation_details", {})
    
    due_date = rec.get("payment_due_date")
    balance = rec.get("outstanding_balance", 0.0)

    draft = (
        f"### Fee Status: OVERDUE PAYMENT ALERT\n\n"
        f"**URGENT FINANCIAL NOTICE:** The payment deadline for student `{rec.get('student_id')}` has passed.\n\n"
        f"- **Student ID:** `{rec.get('student_id')}`\n"
        f"- **Name:** **{rec.get('name')}**\n"
        f"- **Program:** {rec.get('program')} ({rec.get('department')})\n"
        f"- **Semester:** {rec.get('semester')}\n"
        f"- **Original Fee:** {rec.get('total_semester_fee'):,.2f} {CURRENCY_SYMBOL}\n"
        f"- **Amount Paid:** {rec.get('amount_paid'):,.2f} {CURRENCY_SYMBOL}\n"
        f"- **Overdue Balance:** **{balance:,.2f} {CURRENCY_SYMBOL}**\n"
        f"- **Official Due Date:** `{due_date}` (As-of Audit Date: `{REFERENCE_DATE}`)\n\n"
        f"**System Recommendation:** Immediate payment required. Late fee surcharges may apply. Portal access for exam registration is temporarily suspended until balance clearance."
    )
    return {"draft_response": draft, "audit_trail": audit_trail}

def handle_incomplete_node(state: AgentState) -> Dict[str, Any]:
    """Process incomplete or mathematically inconsistent student records."""
    audit_trail = list(state.get("audit_trail", []))
    audit_trail.append("handle_incomplete_node: Flagged inconsistent record for audit.")
    rec = state.get("student_record", {})
    calc = state.get("calculation_details", {})

    discrepancy = calc.get("discrepancy", 0.0)
    diagnosis = calc.get("diagnosis", "DATA_INTEGRITY_ANOMALY")

    draft = (
        f"### Audit Flag: INCONSISTENT / INCOMPLETE RECORD\n\n"
        f"**DATA INTEGRITY ALERT:** Discrepancy detected in financial ledger for `{rec.get('student_id')}`.\n\n"
        f"- **Student ID:** `{rec.get('student_id')}`\n"
        f"- **Name:** **{rec.get('name')}**\n"
        f"- **Department:** {rec.get('department')}\n"
        f"- **Diagnosis:** `{diagnosis}`\n"
        f"- **Total Semester Fee:** {rec.get('total_semester_fee'):,.2f} {CURRENCY_SYMBOL}\n"
        f"- **Amount Paid:** {rec.get('amount_paid'):,.2f} {CURRENCY_SYMBOL}\n"
        f"- **Recorded Balance in DB:** {rec.get('outstanding_balance'):,.2f} {CURRENCY_SYMBOL}\n"
        f"- **Mathematically Computed Balance:** **{calc.get('computed_balance'):,.2f} {CURRENCY_SYMBOL}**\n"
        f"- **Ledger Discrepancy:** **{discrepancy:+.2f} {CURRENCY_SYMBOL}**\n"
        f"- **Payment Due Date:** `{rec.get('payment_due_date') or 'MISSING'}`\n"
        f"- **Audit Notes:** {rec.get('notes')}\n\n"
        f"**Action Required:** Record flagged for Finance Auditor reconciliation via Human-in-the-Loop clearance."
    )
    return {
        "draft_response": draft,
        "requires_human_approval": True,
        "audit_trail": audit_trail
    }

def handle_concession_pending_node(state: AgentState) -> Dict[str, Any]:
    """Process records with pending financial concession / scholarship requests."""
    audit_trail = list(state.get("audit_trail", []))
    audit_trail.append("handle_concession_pending_node: Routing to HITL concession review.")
    rec = state.get("student_record", {})
    sc = rec.get("scholarship_or_concession", {})

    draft = (
        f"### Financial Assistance Request: PENDING HITL APPROVAL\n\n"
        f"- **Student ID:** `{rec.get('student_id')}`\n"
        f"- **Name:** **{rec.get('name')}**\n"
        f"- **Department:** {rec.get('department')}\n"
        f"- **Concession Type:** **{sc.get('type')}**\n"
        f"- **Requested Percentage:** {sc.get('percentage')}%\n"
        f"- **Requested Concession Amount:** **{sc.get('amount'):,.2f} {CURRENCY_SYMBOL}**\n"
        f"- **Current Total Fee:** {rec.get('total_semester_fee'):,.2f} {CURRENCY_SYMBOL}\n"
        f"- **Current Amount Paid:** {rec.get('amount_paid'):,.2f} {CURRENCY_SYMBOL}\n"
        f"- **Current Outstanding Balance:** {rec.get('outstanding_balance'):,.2f} {CURRENCY_SYMBOL}\n"
        f"- **Prospective Balance If Approved:** **{max(0.0, (rec.get('total_semester_fee') - sc.get('amount')) - rec.get('amount_paid')):,.2f} {CURRENCY_SYMBOL}**\n\n"
        f"**Governance Requirement:** University policy mandates Human-in-the-Loop Finance Committee authorization before applying any fee waiver."
    )
    return {
        "draft_response": draft,
        "requires_human_approval": True,
        "audit_trail": audit_trail
    }

# -------------------------------------------------------------
# 4. Summary & Search Query Handlers
# -------------------------------------------------------------
def summary_report_node(state: AgentState) -> Dict[str, Any]:
    """Generate department-level or university-wide financial collection summary."""
    audit_trail = list(state.get("audit_trail", []))
    dept = state.get("department")
    audit_trail.append(f"summary_report_node: Generating report for '{dept or 'University'}'")

    summary = generate_payment_summary.invoke({"department": dept})
    
    if not summary.get("success", False):
        draft = f"Error generating summary: {summary.get('error')}"
        return {"draft_response": draft, "summary_report": summary, "audit_trail": audit_trail}

    dist = summary.get("status_distribution", {})
    draft = (
        f"## Financial Summary Report ({summary.get('scope')})\n\n"
        f"| Metric | Value |\n"
        f"| :--- | :--- |\n"
        f"| **Total Enrolled Students** | **{summary.get('total_students')}** |\n"
        f"| **Total Gross Billed Fee** | {summary.get('total_billed_fee'):,.2f} {CURRENCY_SYMBOL} |\n"
        f"| **Total Concessions & Scholarships** | -{summary.get('total_concessions_awarded'):,.2f} {CURRENCY_SYMBOL} |\n"
        f"| **Net Collectible Fee** | {summary.get('net_collectible_fee'):,.2f} {CURRENCY_SYMBOL} |\n"
        f"| **Total Fee Collected to Date** | **{summary.get('total_amount_collected'):,.2f} {CURRENCY_SYMBOL}** |\n"
        f"| **Total Outstanding Balance** | **{summary.get('total_outstanding_balance'):,.2f} {CURRENCY_SYMBOL}** |\n"
        f"| **Fee Collection Efficiency** | **{summary.get('collection_efficiency_pct')}%** |\n\n"
        f"### Payment Status Distribution\n"
        f"- **Fully Paid:** {dist.get('PAID', 0)} students\n"
        f"- **Partially Paid (Installments):** {dist.get('PARTIALLY_PAID', 0)} students\n"
        f"- **Overdue Accounts:** {dist.get('OVERDUE', 0)} students\n"
        f"- **Pending Concession Requests:** {dist.get('CONCESSION_PENDING', 0)} students\n"
        f"- **Flagged Inconsistent Records:** {dist.get('INCOMPLETE_RECORD', 0)} students\n"
    )

    if not dept and "department_breakdown" in summary:
        draft += "\n### Department Breakdown\n\n| Department | Students | Billed Fee | Collected | Outstanding |\n| :--- | :--- | :--- | :--- | :--- |\n"
        for dname, stats in summary["department_breakdown"].items():
            draft += f"| {dname} | {stats['total_students']} | {stats['billed']:,.0f} | {stats['collected']:,.0f} | {stats['outstanding']:,.0f} |\n"

    return {
        "summary_report": summary,
        "draft_response": draft,
        "audit_trail": audit_trail
    }

def search_query_node(state: AgentState) -> Dict[str, Any]:
    """Execute search queries for overdue students, scholarship recipients, or outstanding balances."""
    audit_trail = list(state.get("audit_trail", []))
    q_type = state.get("query_type", "")
    dept = state.get("department")

    criteria = "outstanding"
    if q_type == "SEARCH_OVERDUE":
        criteria = "overdue"
    elif q_type == "SEARCH_SCHOLARSHIPS":
        criteria = "scholarships"

    audit_trail.append(f"search_query_node: Executing search for '{criteria}' (dept={dept})")
    res = search_students_by_criteria.invoke({"criteria": criteria, "department": dept})

    results = res.get("results", [])
    count = res.get("count", 0)

    if criteria == "overdue":
        draft = f"### Overdue Payment Roster ({count} Students Identified)\n\n"
        draft += "| Student ID | Student Name | Department | Outstanding Balance | Due Date |\n| :--- | :--- | :--- | :--- | :--- |\n"
        for s in results:
            draft += f"| `{s['student_id']}` | **{s['name']}** | {s['department']} | {s['outstanding_balance']:,.2f} {CURRENCY_SYMBOL} | `{s['due_date']}` |\n"
    elif criteria == "scholarships":
        draft = f"### Scholarship & Financial Assistance Recipients ({count} Students)\n\n"
        draft += "| Student ID | Student Name | Department | Scholarship Type | Waiver % | Amount | Status |\n| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
        for s in results:
            draft += f"| `{s['student_id']}` | **{s['name']}** | {s['department']} | {s['type']} | {s['percentage']}% | {s['amount']:,.0f} | `{s['status']}` |\n"
    else: # outstanding
        draft = f"### Outstanding Fee Balances ({count} Students)\n\n"
        draft += "| Student ID | Student Name | Department | Outstanding Balance | Status | Due Date |\n| :--- | :--- | :--- | :--- | :--- | :--- |\n"
        for s in results[:15]:
            draft += f"| `{s['student_id']}` | **{s['name']}** | {s['department']} | {s['outstanding_balance']:,.2f} {CURRENCY_SYMBOL} | `{s['status']}` | `{s.get('due_date', 'N/A')}` |\n"
        if count > 15:
            draft += f"\n*...and {count - 15} additional records.*"

    return {
        "search_results": results,
        "draft_response": draft,
        "audit_trail": audit_trail
    }

def audit_records_node(state: AgentState) -> Dict[str, Any]:
    """Identify and display all inconsistent or incomplete financial records."""
    audit_trail = list(state.get("audit_trail", []))
    audit_trail.append("audit_records_node: Querying database for ledger discrepancies.")
    
    inconsistent = db.get_inconsistent_records()
    draft = f"### Audit Investigation: Incomplete and Inconsistent Records ({len(inconsistent)} Flagged)\n\n"
    draft += "| Student ID | Student Name | Recorded Balance | Computed Balance | Discrepancy | Audit Reason |\n| :--- | :--- | :--- | :--- | :--- | :--- |\n"
    for r in inconsistent:
        draft += (
            f"| `{r['student_id']}` | **{r['name']}** | {r['recorded_balance']:,.2f} {CURRENCY_SYMBOL} | "
            f"{r['expected_balance']:,.2f} {CURRENCY_SYMBOL} | {r['discrepancy']:+.2f} {CURRENCY_SYMBOL} | {r['notes']} |\n"
        )
    draft += "\n**Corrective Action:** These records require Human-in-the-Loop review before balance finalization."
    
    return {
        "search_results": inconsistent,
        "draft_response": draft,
        "audit_trail": audit_trail
    }

# -------------------------------------------------------------
# 5. Reflection & Validation Mechanism
# -------------------------------------------------------------
def reflection_node(state: AgentState) -> Dict[str, Any]:
    """
    Self-correction & reflection engine.
    Audits arithmetic calculations, formulas, and report totals before final presentation.
    """
    audit_trail = list(state.get("audit_trail", []))
    retries = state.get("reflection_retries", 0)
    
    student_record = state.get("student_record")
    calc_details = state.get("calculation_details", {})
    summary_report = state.get("summary_report")

    is_valid = True
    critique = "All validation checks passed."

    if student_record:
        is_valid, critique = ReflectionEngine.validate_student_record(student_record, calc_details)
    elif summary_report:
        is_valid, critique = ReflectionEngine.validate_summary_report(summary_report)

    audit_trail.append(f"reflection_node: Validated={is_valid} | Critique: {critique[:80]}...")

    return {
        "calculation_validated": is_valid,
        "reflection_critique": critique,
        "audit_trail": audit_trail
    }

def correction_node(state: AgentState) -> Dict[str, Any]:
    """
    Apply automated mathematical correction and critique annotations when reflection fails.
    """
    audit_trail = list(state.get("audit_trail", []))
    critique = state.get("reflection_critique", "")
    retries = state.get("reflection_retries", 0) + 1
    audit_trail.append(f"correction_node: Applying self-correction (attempt {retries}).")

    student_id = state.get("student_id")
    student_rec = state.get("student_record")
    draft = state.get("draft_response", "")

    # Append reflection critique and correction notice to draft
    correction_banner = (
        f"\n\n---\n"
        f"**Reflection & Self-Correction Note:**\n"
        f"> **System Critique:** {critique}\n"
        f"> **Correction Applied:** Highlighted discrepancy for administrative audit. Flagged status as `INCOMPLETE_RECORD`."
    )
    new_draft = draft + correction_banner

    return {
        "draft_response": new_draft,
        "reflection_retries": retries,
        "calculation_validated": True, # Marked resolved after appending audit disclaimer
        "requires_human_approval": True, # Discrepancy requires HITL
        "audit_trail": audit_trail
    }

# -------------------------------------------------------------
# 6. Human-in-the-Loop (HITL) Gate & Decision Application
# -------------------------------------------------------------
def human_approval_node(state: AgentState) -> Dict[str, Any]:
    """
    Human-in-the-Loop interruption node.
    Pauses graph execution using interrupt() when approval is required and no decision has been recorded yet.
    """
    audit_trail = list(state.get("audit_trail", []))
    rec = state.get("student_record", {})
    student_id = rec.get("student_id", state.get("student_id", "N/A"))
    action_type = "CONCESSION_APPROVAL" if rec.get("scholarship_or_concession", {}).get("status") == "Pending Approval" else "EXCEPTIONAL_RECORD_VERIFICATION"

    decision = state.get("hitl_decision")

    # If decision is already provided (e.g. state resumed or supplied), proceed
    if decision:
        audit_trail.append(f"human_approval_node: Decision detected for {student_id} -> Approved={decision.get('approved')}")
        return {
            "audit_trail": audit_trail
        }

    # Prepare interrupt payload
    payload = ApprovalManager.create_approval_payload(rec, action_type)
    audit_trail.append(f"human_approval_node: Initiating HITL interrupt for {student_id} ({action_type})")

    # LangGraph modern interrupt
    decision_from_interrupt = interrupt(payload)

    audit_trail.append(f"human_approval_node: Resumed from interrupt with decision={decision_from_interrupt}")
    return {
        "hitl_decision": decision_from_interrupt,
        "audit_trail": audit_trail
    }

def apply_approval_decision_node(state: AgentState) -> Dict[str, Any]:
    """
    Commit the Human-in-the-Loop administrative decision to the database and update state.
    """
    audit_trail = list(state.get("audit_trail", []))
    student_id = state.get("student_id")
    decision = state.get("hitl_decision", {})
    rec = state.get("student_record", {})

    approved = decision.get("approved", False)
    authorized_by = decision.get("authorized_by", "Finance Committee")
    comments = decision.get("comments", "Administrative review completed.")
    action_type = "CONCESSION_APPROVAL" if rec.get("scholarship_or_concession", {}).get("status") == "Pending Approval" else "EXCEPTIONAL_RECORD_VERIFICATION"

    audit_trail.append(f"apply_approval_decision_node: Applying decision (Approved={approved}) by {authorized_by}")
    
    result = ApprovalManager.apply_decision(
        student_id=student_id,
        action_type=action_type,
        approved=approved,
        authorized_by=authorized_by,
        comments=comments
    )

    updated_rec = result.get("updated_record", rec)
    
    hitl_status_text = (
        f"\n\n### Human-in-the-Loop Approval Decision\n"
        f"- **Action Type:** `{action_type}`\n"
        f"- **Decision:** **{'APPROVED' if approved else 'REJECTED'}**\n"
        f"- **Authorized By:** {authorized_by}\n"
        f"- **Comments:** {comments}\n"
        f"- **Updated Outstanding Balance:** **{updated_rec.get('outstanding_balance'):,.2f} {CURRENCY_SYMBOL}**\n"
        f"- **Updated Payment Status:** `{updated_rec.get('payment_status')}`\n"
        f"- **Verification Status:** `{updated_rec.get('verification_status')}`"
    )

    current_draft = state.get("draft_response", "")
    new_draft = current_draft + hitl_status_text

    return {
        "student_record": updated_rec,
        "verification_status": updated_rec.get("verification_status"),
        "draft_response": new_draft,
        "audit_trail": audit_trail
    }

# -------------------------------------------------------------
# 7. Finalize & Response Node
# -------------------------------------------------------------
def finalize_response_node(state: AgentState) -> Dict[str, Any]:
    """Construct the final response message and audit log entry."""
    audit_trail = list(state.get("audit_trail", []))
    draft = state.get("draft_response", "Request processed successfully.")
    audit_trail.append("finalize_response_node: Workflow completed successfully.")

    ai_message = AIMessage(content=draft)

    return {
        "final_response": draft,
        "messages": [ai_message],
        "audit_trail": audit_trail
    }
