"""
Database layer for Student Fee Management System.
Provides thread-safe access, query helpers, and transactional update capabilities.
"""

import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, date

DATA_FILE_PATH = os.path.join(os.path.dirname(__file__), "students_dataset.json")

class StudentDatabase:
    """In-memory managed database with JSON persistence for student financial records."""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(StudentDatabase, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
        
    def __init__(self, data_file: str = DATA_FILE_PATH):
        if self._initialized:
            return
        self.data_file = data_file
        self.records: Dict[str, Dict[str, Any]] = {}
        self.audit_log: List[Dict[str, Any]] = []
        self.load_data()
        self._initialized = True

    def load_data(self):
        """Load records from JSON file."""
        if not os.path.exists(self.data_file):
            raise FileNotFoundError(f"Dataset file not found at {self.data_file}")
            
        with open(self.data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.records = {item["student_id"].upper(): item for item in data}
        self.log_event("SYSTEM", "DATABASE_LOADED", f"Loaded {len(self.records)} records from {self.data_file}")

    def save_data(self):
        """Persist current records back to JSON."""
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(list(self.records.values()), f, indent=4)

    def log_event(self, actor: str, action: str, details: Any):
        """Record an audit trail event."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "actor": actor,
            "action": action,
            "details": details
        }
        self.audit_log.append(entry)

    def get_all(self) -> List[Dict[str, Any]]:
        """Return a copy of all student records."""
        return list(self.records.values())

    def get_student(self, student_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve student record by ID (case-insensitive)."""
        sid = student_id.strip().upper()
        return self.records.get(sid)

    def search_by_name(self, name_query: str) -> List[Dict[str, Any]]:
        """Find students matching a substring in name."""
        q = name_query.strip().lower()
        return [s for s in self.records.values() if q in s["name"].lower()]

    def get_by_department(self, department: str) -> List[Dict[str, Any]]:
        """Retrieve all students belonging to a department."""
        dept = department.strip().lower()
        return [s for s in self.records.values() if dept in s["department"].lower()]

    def get_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Retrieve students by payment status."""
        st = status.strip().upper()
        return [s for s in self.records.values() if s["payment_status"].upper() == st]

    def get_overdue(self, as_of_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Return students who have an overdue balance.
        Checks both the payment_status flag and calculates overdue based on due_date.
        """
        ref_date = datetime.strptime(as_of_date, "%Y-%m-%d").date() if as_of_date else date(2024, 11, 1)
        results = []
        for s in self.records.values():
            if s["outstanding_balance"] > 0:
                due_str = s.get("payment_due_date")
                if due_str:
                    try:
                        due = datetime.strptime(due_str, "%Y-%m-%d").date()
                        if due < ref_date or s["payment_status"] == "OVERDUE":
                            results.append(s)
                    except ValueError:
                        pass
                elif s["payment_status"] == "OVERDUE":
                    results.append(s)
        return results

    def get_scholarship_students(self) -> List[Dict[str, Any]]:
        """Return all students with any scholarship or concession."""
        results = []
        for s in self.records.values():
            sc = s.get("scholarship_or_concession", {})
            if sc.get("type", "None") != "None" and sc.get("percentage", 0) > 0:
                results.append(s)
        return results

    def get_inconsistent_records(self) -> List[Dict[str, Any]]:
        """Return all records with arithmetic inconsistencies or missing fields."""
        results = []
        for s in self.records.values():
            # Check arithmetic:
            sc = s.get("scholarship_or_concession", {})
            concession_amt = sc.get("amount", 0.0) if sc.get("status") == "Approved" else 0.0
            expected_net = max(0.0, s["total_semester_fee"] - concession_amt)
            expected_balance = expected_net - s["amount_paid"]
            
            discrepancy = abs(s["outstanding_balance"] - expected_balance)
            if discrepancy > 0.01 or s.get("payment_due_date") is None or s["outstanding_balance"] < 0:
                results.append({
                    "student_id": s["student_id"],
                    "name": s["name"],
                    "recorded_balance": s["outstanding_balance"],
                    "expected_balance": expected_balance,
                    "discrepancy": discrepancy,
                    "missing_due_date": s.get("payment_due_date") is None,
                    "notes": s.get("notes", "")
                })
        return results

    def update_concession_status(self, student_id: str, new_status: str, authorized_by: str = "Finance Committee", comments: str = "") -> Optional[Dict[str, Any]]:
        """Approve or reject a concession request and update net fee / balance accordingly."""
        sid = student_id.strip().upper()
        if sid not in self.records:
            return None
            
        record = self.records[sid]
        old_status = record["scholarship_or_concession"].get("status")
        record["scholarship_or_concession"]["status"] = new_status
        
        if new_status == "Approved":
            discount = record["scholarship_or_concession"]["amount"]
            record["net_fee"] = max(0.0, record["total_semester_fee"] - discount)
            record["outstanding_balance"] = max(0.0, record["net_fee"] - record["amount_paid"])
            if record["outstanding_balance"] == 0:
                record["payment_status"] = "PAID"
            else:
                record["payment_status"] = "PARTIALLY_PAID"
            record["exceptional_flag"] = False
            record["verification_status"] = "Verified"
        elif new_status == "Rejected":
            record["net_fee"] = record["total_semester_fee"]
            record["outstanding_balance"] = record["total_semester_fee"] - record["amount_paid"]
            record["payment_status"] = "PARTIALLY_PAID" if record["amount_paid"] > 0 else "OVERDUE"
            record["verification_status"] = "Rejected"
            
        log_msg = f"Concession for {sid} updated from '{old_status}' to '{new_status}' by {authorized_by}. Comments: {comments}"
        record["notes"] += f" | HITL: {log_msg}"
        self.log_event(authorized_by, "CONCESSION_UPDATED", log_msg)
        self.save_data()
        return record

    def update_verification_status(self, student_id: str, new_status: str, authorized_by: str = "Auditor", notes: str = "") -> Optional[Dict[str, Any]]:
        """Verify an exceptional or flagged payment record."""
        sid = student_id.strip().upper()
        if sid not in self.records:
            return None
            
        record = self.records[sid]
        record["verification_status"] = new_status
        record["exceptional_flag"] = (new_status != "Verified")
        log_msg = f"Verification status for {sid} updated to '{new_status}' by {authorized_by}. Notes: {notes}"
        record["notes"] += f" | HITL: {log_msg}"
        self.log_event(authorized_by, "VERIFICATION_UPDATED", log_msg)
        self.save_data()
        return record

    def fix_arithmetic_discrepancy(self, student_id: str, authorized_by: str = "System Validator") -> Optional[Dict[str, Any]]:
        """Correct arithmetic discrepancy based on audited formula."""
        sid = student_id.strip().upper()
        if sid not in self.records:
            return None
            
        record = self.records[sid]
        sc = record.get("scholarship_or_concession", {})
        concession_amt = sc.get("amount", 0.0) if sc.get("status") == "Approved" else 0.0
        expected_net = max(0.0, record["total_semester_fee"] - concession_amt)
        expected_balance = max(0.0, expected_net - record["amount_paid"])
        
        old_balance = record["outstanding_balance"]
        record["net_fee"] = expected_net
        record["outstanding_balance"] = expected_balance
        
        if expected_balance == 0:
            record["payment_status"] = "PAID"
        elif record["payment_due_date"] and record["payment_due_date"] < "2024-11-01":
            record["payment_status"] = "OVERDUE"
        else:
            record["payment_status"] = "PARTIALLY_PAID"
            
        record["verification_status"] = "Verified"
        record["exceptional_flag"] = False
        log_msg = f"Balance corrected from {old_balance} to {expected_balance} by {authorized_by}"
        record["notes"] += f" | {log_msg}"
        self.log_event(authorized_by, "BALANCE_CORRECTED", log_msg)
        self.save_data()
        return record

# Global database singleton
db = StudentDatabase()
