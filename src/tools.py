"""
LangChain Functional Tools for Student Fee Management System.
Implements the 5 core tools plus specialized audit, search, and concession tools.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date
from langchain_core.tools import tool
from data.database import db
from src.config import REFERENCE_DATE, CURRENCY_SYMBOL

@tool
def retrieve_student_record(student_id: str) -> Dict[str, Any]:
    """
    Retrieve the complete financial and academic record for a student by their ID.
    Args:
        student_id: Student ID (e.g. 'STD-2024-001').
    Returns:
        Dictionary containing all financial, academic, installment, and concession details.
    """
    record = db.get_student(student_id)
    if not record:
        return {
            "success": False,
            "error": f"Student with ID '{student_id}' was not found in the database."
        }
    return {
        "success": True,
        "record": record
    }

@tool
def calculate_outstanding_balance(student_id: str, include_pending_concession: bool = False) -> Dict[str, Any]:
    """
    Recalculate and audit the outstanding fee balance for a student.
    Compares the mathematically expected balance against the database record to detect discrepancies.
    
    Args:
        student_id: Student ID (e.g. 'STD-2024-001').
        include_pending_concession: If True, tests balance assuming pending concession is approved.
    Returns:
        Detailed mathematical breakdown including discrepancy analysis.
    """
    record = db.get_student(student_id)
    if not record:
        return {"success": False, "error": f"Student ID '{student_id}' not found."}

    total_fee = float(record["total_semester_fee"])
    amount_paid = float(record["amount_paid"])
    recorded_balance = float(record["outstanding_balance"])
    
    sc = record.get("scholarship_or_concession", {})
    concession_status = sc.get("status", "None")
    concession_amount = float(sc.get("amount", 0.0))
    
    # Calculate approved concession
    applied_concession = 0.0
    if concession_status == "Approved" or (include_pending_concession and concession_status == "Pending Approval"):
        applied_concession = concession_amount

    net_fee = max(0.0, total_fee - applied_concession)
    computed_balance = net_fee - amount_paid
    
    # Check for discrepancy
    discrepancy = round(recorded_balance - computed_balance, 2)
    is_consistent = abs(discrepancy) < 0.01

    diagnosis = "CONSISTENT"
    if not is_consistent:
        if recorded_balance > computed_balance:
            diagnosis = "OVER_RECORDED_BALANCE (Student billed more than mathematical balance)"
        else:
            diagnosis = "UNDER_RECORDED_BALANCE (Student balance lower than mathematical formula)"
    elif computed_balance < 0:
        diagnosis = "NEGATIVE_BALANCE_ANOMALY (Student overpaid)"
    elif computed_balance == 0:
        diagnosis = "FULLY_SETTLED"
    else:
        diagnosis = "OUTSTANDING_ON_RECORD"

    return {
        "success": True,
        "student_id": record["student_id"],
        "student_name": record["name"],
        "total_semester_fee": total_fee,
        "concession_type": sc.get("type", "None"),
        "concession_status": concession_status,
        "concession_applied": applied_concession,
        "net_fee": net_fee,
        "amount_paid": amount_paid,
        "recorded_balance": recorded_balance,
        "computed_balance": computed_balance,
        "discrepancy": discrepancy,
        "is_consistent": is_consistent,
        "diagnosis": diagnosis,
        "currency": CURRENCY_SYMBOL
    }

@tool
def check_payment_status(student_id: str, as_of_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Evaluate the real-time payment status of a student considering due dates, balances, and anomalies.
    
    Args:
        student_id: Student ID (e.g. 'STD-2024-001').
        as_of_date: Reference date formatted as YYYY-MM-DD (defaults to system audit date).
    Returns:
        Status evaluation including status category, days overdue, and action recommendation.
    """
    record = db.get_student(student_id)
    if not record:
        return {"success": False, "error": f"Student ID '{student_id}' not found."}

    ref_date_str = as_of_date or REFERENCE_DATE
    try:
        ref_date = datetime.strptime(ref_date_str, "%Y-%m-%d").date()
    except ValueError:
        ref_date = datetime.strptime(REFERENCE_DATE, "%Y-%m-%d").date()

    balance = float(record["outstanding_balance"])
    due_date_str = record.get("payment_due_date")
    status = record.get("payment_status", "UNKNOWN")
    
    # Audit arithmetic
    calc = calculate_outstanding_balance.invoke({"student_id": student_id})
    is_arithmetic_valid = calc.get("is_consistent", True)

    days_overdue = 0
    is_overdue = False
    
    if due_date_str:
        try:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
            if ref_date > due_date and balance > 0:
                is_overdue = True
                days_overdue = (ref_date - due_date).days
        except ValueError:
            pass

    # Status classification logic
    derived_status = status
    if not is_arithmetic_valid or due_date_str is None or balance < 0:
        derived_status = "INCOMPLETE_RECORD"
    elif record.get("scholarship_or_concession", {}).get("status") == "Pending Approval":
        derived_status = "CONCESSION_PENDING"
    elif balance == 0:
        derived_status = "PAID"
    elif is_overdue:
        derived_status = "OVERDUE"
    elif balance > 0:
        derived_status = "PARTIALLY_PAID"

    action_required = "None"
    if derived_status == "OVERDUE":
        action_required = f"Send payment overdue notice. Fee is overdue by {days_overdue} days."
    elif derived_status == "PARTIALLY_PAID":
        action_required = "Monitor upcoming installment schedule."
    elif derived_status == "INCOMPLETE_RECORD":
        action_required = "Requires audit inspection and Human-in-the-Loop data correction."
    elif derived_status == "CONCESSION_PENDING":
        action_required = "Awaiting Finance Committee Human-in-the-Loop review."

    return {
        "success": True,
        "student_id": record["student_id"],
        "student_name": record["name"],
        "recorded_status": status,
        "verified_status": derived_status,
        "outstanding_balance": balance,
        "payment_due_date": due_date_str,
        "as_of_date": str(ref_date),
        "is_overdue": is_overdue,
        "days_overdue": days_overdue,
        "is_arithmetic_valid": is_arithmetic_valid,
        "action_required": action_required,
        "exceptional_flag": record.get("exceptional_flag", False),
        "verification_status": record.get("verification_status", "Unknown")
    }

@tool
def retrieve_installment_info(student_id: str) -> Dict[str, Any]:
    """
    Retrieve installment plan structure, payment schedule, and upcoming installments.
    
    Args:
        student_id: Student ID (e.g. 'STD-2024-001').
    Returns:
        Installment plan status, schedule details, paid vs remaining installments.
    """
    record = db.get_student(student_id)
    if not record:
        return {"success": False, "error": f"Student ID '{student_id}' not found."}

    inst = record.get("installment_details", {})
    has_plan = inst.get("has_installment_plan", False)
    
    total_inst = inst.get("total_installments", 0)
    paid_inst = inst.get("installments_paid", 0)
    remaining_inst = max(0, total_inst - paid_inst)

    return {
        "success": True,
        "student_id": record["student_id"],
        "student_name": record["name"],
        "has_installment_plan": has_plan,
        "plan_type": inst.get("plan_type", "None"),
        "total_installments": total_inst,
        "installments_paid": paid_inst,
        "installments_remaining": remaining_inst,
        "next_installment_amount": inst.get("next_installment_amount", 0.0),
        "next_installment_due": inst.get("next_installment_due"),
        "total_outstanding_balance": record.get("outstanding_balance", 0.0),
        "currency": CURRENCY_SYMBOL
    }

@tool
def generate_payment_summary(department: Optional[str] = None, semester: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate aggregate financial summaries, fee collection rates, and outstanding balances.
    Can be filtered by specific department or run across the entire university.
    
    Args:
        department: Optional department name filter (e.g. 'Computer Science', 'Business Administration').
        semester: Optional semester filter (e.g. 'Fall 2024').
    Returns:
        Comprehensive financial breakdown with collection percentages and overdue statistics.
    """
    records = db.get_all()
    if department:
        dept_str = department.strip().lower()
        records = [r for r in records if dept_str in r["department"].lower()]
    if semester:
        sem_str = semester.strip().lower()
        records = [r for r in records if sem_str in r["semester"].lower()]

    total_students = len(records)
    if total_students == 0:
        return {
            "success": False,
            "error": f"No student records found matching department='{department}' and semester='{semester}'."
        }

    total_billed = sum(r["total_semester_fee"] for r in records)
    total_collected = sum(r["amount_paid"] for r in records)
    total_outstanding = sum(r["outstanding_balance"] for r in records)
    
    # Concessions awarded (approved only)
    total_concessions = sum(
        r.get("scholarship_or_concession", {}).get("amount", 0.0)
        for r in records
        if r.get("scholarship_or_concession", {}).get("status") == "Approved"
    )

    net_collectible = total_billed - total_concessions
    collection_rate = round((total_collected / net_collectible * 100), 2) if net_collectible > 0 else 0.0

    # Categorize counts
    status_counts = {"PAID": 0, "PARTIALLY_PAID": 0, "OVERDUE": 0, "CONCESSION_PENDING": 0, "INCOMPLETE_RECORD": 0}
    overdue_students = []
    scholarship_recipients = []

    for r in records:
        st = r.get("payment_status", "UNKNOWN")
        if st in status_counts:
            status_counts[st] += 1
        else:
            status_counts[st] = 1

        if st == "OVERDUE" or (r.get("payment_due_date") and r["payment_due_date"] < REFERENCE_DATE and r["outstanding_balance"] > 0):
            overdue_students.append({
                "student_id": r["student_id"],
                "name": r["name"],
                "department": r["department"],
                "outstanding_balance": r["outstanding_balance"],
                "due_date": r["payment_due_date"]
            })

        sc = r.get("scholarship_or_concession", {})
        if sc.get("type", "None") != "None" and sc.get("percentage", 0) > 0:
            scholarship_recipients.append({
                "student_id": r["student_id"],
                "name": r["name"],
                "type": sc.get("type"),
                "percentage": sc.get("percentage"),
                "amount": sc.get("amount"),
                "status": sc.get("status")
            })

    # Department breakdown
    dept_breakdown: Dict[str, Dict[str, float]] = {}
    for r in db.get_all():
        d = r["department"]
        if d not in dept_breakdown:
            dept_breakdown[d] = {"total_students": 0, "billed": 0.0, "collected": 0.0, "outstanding": 0.0}
        dept_breakdown[d]["total_students"] += 1
        dept_breakdown[d]["billed"] += r["total_semester_fee"]
        dept_breakdown[d]["collected"] += r["amount_paid"]
        dept_breakdown[d]["outstanding"] += r["outstanding_balance"]

    return {
        "success": True,
        "scope": f"Department: {department}" if department else "All Departments (University-wide)",
        "total_students": total_students,
        "total_billed_fee": round(total_billed, 2),
        "total_concessions_awarded": round(total_concessions, 2),
        "net_collectible_fee": round(net_collectible, 2),
        "total_amount_collected": round(total_collected, 2),
        "total_outstanding_balance": round(total_outstanding, 2),
        "collection_efficiency_pct": collection_rate,
        "status_distribution": status_counts,
        "overdue_count": len(overdue_students),
        "overdue_students_sample": overdue_students[:10],
        "scholarship_count": len(scholarship_recipients),
        "department_breakdown": dept_breakdown,
        "currency": CURRENCY_SYMBOL
    }

@tool
def search_students_by_criteria(criteria: str, department: Optional[str] = None) -> Dict[str, Any]:
    """
    Search and filter students based on specific query criteria.
    
    Args:
        criteria: One of ['outstanding', 'overdue', 'scholarships', 'inconsistent', 'pending_approval'].
        department: Optional department filter.
    Returns:
        List of students matching the filter criteria.
    """
    records = db.get_all()
    if department:
        dept_str = department.strip().lower()
        records = [r for r in records if dept_str in r["department"].lower()]

    criteria_clean = criteria.strip().lower()
    matched = []

    if "overdue" in criteria_clean:
        for r in records:
            if r["payment_status"] == "OVERDUE" or (r.get("payment_due_date") and r["payment_due_date"] < REFERENCE_DATE and r["outstanding_balance"] > 0):
                matched.append({
                    "student_id": r["student_id"],
                    "name": r["name"],
                    "department": r["department"],
                    "outstanding_balance": r["outstanding_balance"],
                    "due_date": r["payment_due_date"]
                })
    elif "scholarship" in criteria_clean or "concession" in criteria_clean:
        for r in records:
            sc = r.get("scholarship_or_concession", {})
            if sc.get("type", "None") != "None":
                matched.append({
                    "student_id": r["student_id"],
                    "name": r["name"],
                    "department": r["department"],
                    "type": sc.get("type"),
                    "percentage": sc.get("percentage"),
                    "amount": sc.get("amount"),
                    "status": sc.get("status")
                })
    elif "outstanding" in criteria_clean or "unpaid" in criteria_clean or "balance" in criteria_clean:
        for r in records:
            if r["outstanding_balance"] > 0:
                matched.append({
                    "student_id": r["student_id"],
                    "name": r["name"],
                    "department": r["department"],
                    "outstanding_balance": r["outstanding_balance"],
                    "status": r["payment_status"],
                    "due_date": r["payment_due_date"]
                })
    elif "inconsistent" in criteria_clean or "incomplete" in criteria_clean:
        matched = db.get_inconsistent_records()
    elif "pending" in criteria_clean:
        for r in records:
            if r.get("verification_status") in ["Pending_HITL_Approval", "Pending_HITL_Verification"]:
                matched.append({
                    "student_id": r["student_id"],
                    "name": r["name"],
                    "department": r["department"],
                    "verification_status": r["verification_status"],
                    "notes": r.get("notes")
                })

    return {
        "success": True,
        "criteria": criteria,
        "count": len(matched),
        "results": matched
    }

# Export list of functional tools
FUNCTIONAL_TOOLS = [
    retrieve_student_record,
    calculate_outstanding_balance,
    check_payment_status,
    retrieve_installment_info,
    generate_payment_summary,
    search_students_by_criteria
]
