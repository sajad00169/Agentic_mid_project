"""
Reflection Engine for Student Fee Management Agent.
Performs rigorous mathematical validation, date audit checks, and consistency critiques
on drafted responses and generated financial reports.
"""

from typing import Dict, Any, Tuple
from datetime import datetime
from src.config import REFERENCE_DATE

class ReflectionEngine:
    """
    Automated validator and reflection agent.
    Audits arithmetic, policy compliance, and data consistency.
    """

    @staticmethod
    def validate_student_record(student_record: Dict[str, Any], calc_details: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate individual student financial record for arithmetic consistency.
        """
        if not student_record:
            return True, "No student record to validate."

        total_fee = float(student_record.get("total_semester_fee", 0.0))
        amount_paid = float(student_record.get("amount_paid", 0.0))
        recorded_balance = float(student_record.get("outstanding_balance", 0.0))
        due_date_str = student_record.get("payment_due_date")
        
        sc = student_record.get("scholarship_or_concession", {})
        concession_status = sc.get("status", "None")
        concession_amount = float(sc.get("amount", 0.0))
        
        applied_concession = concession_amount if concession_status == "Approved" else 0.0
        expected_net = max(0.0, total_fee - applied_concession)
        expected_balance = expected_net - amount_paid

        # 1. Missing due date check
        if due_date_str is None:
            return False, "CRITIQUE: Record is missing mandatory payment_due_date. Status must be INCOMPLETE_RECORD."

        # 2. Negative balance anomaly check
        if recorded_balance < 0 or expected_balance < 0:
            return False, f"CRITIQUE: Detected negative balance anomaly ({recorded_balance} PKR). Student overpaid by {abs(recorded_balance)} PKR. Requires refund or carry-forward review."

        # 3. Arithmetic balance discrepancy check
        discrepancy = round(recorded_balance - expected_balance, 2)
        if abs(discrepancy) > 0.01:
            return False, (
                f"CRITIQUE: Arithmetic Discrepancy Detected! "
                f"Recorded outstanding balance ({recorded_balance} PKR) does not match "
                f"mathematical formula [Total Fee ({total_fee}) - Approved Concession ({applied_concession}) - Amount Paid ({amount_paid}) = {expected_balance} PKR]. "
                f"Discrepancy: {discrepancy:+} PKR. Record must be audited and corrected."
            )

        # 4. Overdue status check
        ref_date = datetime.strptime(REFERENCE_DATE, "%Y-%m-%d").date()
        try:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
            if ref_date > due_date and recorded_balance > 0 and student_record.get("payment_status") != "OVERDUE":
                return False, f"CRITIQUE: Due date ({due_date}) has passed with unpaid balance ({recorded_balance} PKR). Record should be classified as OVERDUE."
        except ValueError:
            return False, f"CRITIQUE: Invalid due date format '{due_date_str}'."

        # 5. Premature concession deduction check
        if concession_status == "Pending Approval" and abs(student_record.get("net_fee", total_fee) - (total_fee - concession_amount)) < 0.01:
            return False, "CRITIQUE: Unapproved concession was prematurely deducted from net_fee before Human-in-the-Loop authorization."

        return True, "VALIDATION_PASSED: All arithmetic formulas, dates, and concession states verified."

    @staticmethod
    def validate_summary_report(report_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate aggregated financial report totals and balance reconciliations.
        """
        if not report_data or not report_data.get("success", False):
            return True, "No summary report to validate."

        billed = report_data.get("total_billed_fee", 0.0)
        concessions = report_data.get("total_concessions_awarded", 0.0)
        net = report_data.get("net_collectible_fee", 0.0)
        collected = report_data.get("total_amount_collected", 0.0)
        outstanding = report_data.get("total_outstanding_balance", 0.0)

        # Check net math
        if abs(net - (billed - concessions)) > 1.0:
            return False, f"CRITIQUE: Report net collectible fee ({net}) does not equal billed ({billed}) - concessions ({concessions})."

        # Check collection math (allowing for minor uncollected/installment timing)
        if collected + outstanding < net - 100.0:
            return False, f"CRITIQUE: Sum of collected ({collected}) and outstanding ({outstanding}) does not reconcile with net fee ({net})."

        return True, "VALIDATION_PASSED: Department and university financial summary figures successfully reconciled."
