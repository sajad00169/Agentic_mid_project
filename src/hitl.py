"""
Human-in-the-Loop (HITL) Approval Module.
Enforces administrative oversight for financial concessions and verification of exceptional payment records.
"""

from typing import Dict, Any, Optional
from data.database import db

class ApprovalManager:
    """Manages HITL approval payloads and authorization checks."""

    @staticmethod
    def should_require_approval(student_record: Optional[Dict[str, Any]], query_type: str) -> bool:
        """Determine if current workflow requires administrative HITL clearance."""
        if not student_record:
            return False

        # 1. Any record with an exceptional flag
        if student_record.get("exceptional_flag", False):
            return True

        # 2. Concession pending approval
        sc = student_record.get("scholarship_or_concession", {})
        if sc.get("status") == "Pending Approval":
            return True

        # 3. Pending verification
        if student_record.get("verification_status") in ["Pending_HITL_Approval", "Pending_HITL_Verification"]:
            return True

        # 4. Inconsistent records requiring clearance
        if student_record.get("payment_status") == "INCOMPLETE_RECORD":
            return True

        return False

    @staticmethod
    def create_approval_payload(student_record: Dict[str, Any], action_type: str, custom_reason: str = "") -> Dict[str, Any]:
        """Construct the approval payload shown to the human decision-maker."""
        student_id = student_record["student_id"]
        sc = student_record.get("scholarship_or_concession", {})
        
        if action_type == "CONCESSION_APPROVAL":
            amount = sc.get("amount", 0.0)
            c_type = sc.get("type", "Financial Assistance")
            pct = sc.get("percentage", 0.0)
            return {
                "request_id": f"REQ-CONCESSION-{student_id}",
                "action_type": "CONCESSION_APPROVAL",
                "student_id": student_id,
                "student_name": student_record["name"],
                "department": student_record["department"],
                "concession_type": c_type,
                "concession_percentage": pct,
                "discount_amount": amount,
                "new_net_fee": max(0.0, student_record["total_semester_fee"] - amount),
                "justification": custom_reason or student_record.get("notes", "Financial hardship concession request."),
                "prompt": f"Authorize {c_type} of {amount} PKR ({pct}%) for student {student_id} ({student_record['name']})?"
            }

        # Verification of exceptional payment record
        return {
            "request_id": f"REQ-AUDIT-{student_id}",
            "action_type": "EXCEPTIONAL_RECORD_VERIFICATION",
            "student_id": student_id,
            "student_name": student_record["name"],
            "department": student_record["department"],
            "verification_status": student_record.get("verification_status"),
            "outstanding_balance": student_record.get("outstanding_balance"),
            "discrepancy_details": custom_reason or student_record.get("notes", "Payment record flagged for manual audit."),
            "prompt": f"Authorize clearance and mark payment record as Verified for student {student_id} ({student_record['name']})?"
        }

    @staticmethod
    def apply_decision(
        student_id: str,
        action_type: str,
        approved: bool,
        authorized_by: str = "Finance Director",
        comments: str = ""
    ) -> Dict[str, Any]:
        """Apply approved or rejected decision directly to the database."""
        if action_type == "CONCESSION_APPROVAL":
            new_status = "Approved" if approved else "Rejected"
            updated = db.update_concession_status(student_id, new_status, authorized_by, comments)
            return {
                "success": bool(updated),
                "action_type": action_type,
                "student_id": student_id,
                "status": new_status,
                "authorized_by": authorized_by,
                "comments": comments,
                "updated_record": updated
            }
        else: # Exceptional record verification
            new_status = "Verified" if approved else "Audit_Rejected"
            updated = db.update_verification_status(student_id, new_status, authorized_by, comments)
            return {
                "success": bool(updated),
                "action_type": action_type,
                "student_id": student_id,
                "status": new_status,
                "authorized_by": authorized_by,
                "comments": comments,
                "updated_record": updated
            }
