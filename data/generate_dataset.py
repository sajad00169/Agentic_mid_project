"""
Script to generate synthetic student financial records for the Fee Management System.
Generates at least 35 realistic records covering all academic, financial, and edge-case scenarios.
"""

import json
import csv
from datetime import datetime, date

DATASET = [
    # --- Group 1: Fully Paid Students (No scholarship or Full payment) ---
    {
        "student_id": "STD-2024-001",
        "name": "Amina Khan",
        "program": "BS Computer Science",
        "department": "Computer Science",
        "semester": "Fall 2024",
        "total_semester_fee": 120000.0,
        "scholarship_or_concession": {
            "type": "None",
            "percentage": 0.0,
            "amount": 0.0,
            "status": "None"
        },
        "net_fee": 120000.0,
        "amount_paid": 120000.0,
        "outstanding_balance": 0.0,
        "payment_due_date": "2024-10-15",
        "installment_details": {
            "has_installment_plan": False,
            "plan_type": "Lump Sum",
            "total_installments": 1,
            "installments_paid": 1,
            "next_installment_amount": 0.0,
            "next_installment_due": None
        },
        "payment_status": "PAID",
        "exceptional_flag": False,
        "verification_status": "Verified",
        "notes": "Full fee paid in single transaction on 2024-10-10."
    },
    {
        "student_id": "STD-2024-002",
        "name": "Zainab Fatima",
        "program": "BS Computer Science",
        "department": "Computer Science",
        "semester": "Fall 2024",
        "total_semester_fee": 130000.0,
        "scholarship_or_concession": {
            "type": "Merit Scholarship",
            "percentage": 50.0,
            "amount": 65000.0,
            "status": "Approved"
        },
        "net_fee": 65000.0,
        "amount_paid": 65000.0,
        "outstanding_balance": 0.0,
        "payment_due_date": "2024-10-15",
        "installment_details": {
            "has_installment_plan": False,
            "plan_type": "Lump Sum",
            "total_installments": 1,
            "installments_paid": 1,
            "next_installment_amount": 0.0,
            "next_installment_due": None
        },
        "payment_status": "PAID",
        "exceptional_flag": False,
        "verification_status": "Verified",
        "notes": "Merit scholarship 50% approved. Remaining net fee paid in full."
    },
    {
        "student_id": "STD-2024-003",
        "name": "Usman Tariq",
        "program": "BS Software Engineering",
        "department": "Computer Science",
        "semester": "Fall 2024",
        "total_semester_fee": 125000.0,
        "scholarship_or_concession": {
            "type": "None",
            "percentage": 0.0,
            "amount": 0.0,
            "status": "None"
        },
        "net_fee": 125000.0,
        "amount_paid": 125000.0,
        "outstanding_balance": 0.0,
        "payment_due_date": "2024-10-15",
        "installment_details": {
            "has_installment_plan": False,
            "plan_type": "Lump Sum",
            "total_installments": 1,
            "installments_paid": 1,
            "next_installment_amount": 0.0,
            "next_installment_due": None
        },
        "payment_status": "PAID",
        "exceptional_flag": False,
        "verification_status": "Verified",
        "notes": "Paid online banking."
    },
    {
        "student_id": "STD-2024-004",
        "name": "Sarah Malik",
        "program": "BBA",
        "department": "Business Administration",
        "semester": "Fall 2024",
        "total_semester_fee": 110000.0,
        "scholarship_or_concession": {
            "type": "Sports Concession",
            "percentage": 100.0,
            "amount": 110000.0,
            "status": "Approved"
        },
        "net_fee": 0.0,
        "amount_paid": 0.0,
        "outstanding_balance": 0.0,
        "payment_due_date": "2024-10-15",
        "installment_details": {
            "has_installment_plan": False,
            "plan_type": "None",
            "total_installments": 0,
            "installments_paid": 0,
            "next_installment_amount": 0.0,
            "next_installment_due": None
        },
        "payment_status": "PAID",
        "exceptional_flag": False,
        "verification_status": "Verified",
        "notes": "National Badminton champion, 100% sports scholarship approved."
    },
    {
        "student_id": "STD-2024-005",
        "name": "Hamza Ali",
        "program": "BS Electrical Engineering",
        "department": "Electrical Engineering",
        "semester": "Fall 2024",
        "total_semester_fee": 140000.0,
        "scholarship_or_concession": {
            "type": "None",
            "percentage": 0.0,
            "amount": 0.0,
            "status": "None"
        },
        "net_fee": 140000.0,
        "amount_paid": 140000.0,
        "outstanding_balance": 0.0,
        "payment_due_date": "2024-10-15",
        "installment_details": {
            "has_installment_plan": False,
            "plan_type": "Lump Sum",
            "total_installments": 1,
            "installments_paid": 1,
            "next_installment_amount": 0.0,
            "next_installment_due": None
        },
        "payment_status": "PAID",
        "exceptional_flag": False,
        "verification_status": "Verified",
        "notes": "Paid in full via bank draft."
    },
    {
        "student_id": "STD-2024-006",
        "name": "Maryam Siddiqui",
        "program": "BS Civil Engineering",
        "department": "Civil Engineering",
        "semester": "Fall 2024",
        "total_semester_fee": 115000.0,
        "scholarship_or_concession": {
            "type": "Need-Based Financial Aid",
            "percentage": 30.0,
            "amount": 34500.0,
            "status": "Approved"
        },
        "net_fee": 80500.0,
        "amount_paid": 80500.0,
        "outstanding_balance": 0.0,
        "payment_due_date": "2024-10-15",
        "installment_details": {
            "has_installment_plan": False,
            "plan_type": "Lump Sum",
            "total_installments": 1,
            "installments_paid": 1,
            "next_installment_amount": 0.0,
            "next_installment_due": None
        },
        "payment_status": "PAID",
        "exceptional_flag": False,
        "verification_status": "Verified",
        "notes": "Need-based aid approved by committee."
    },
    {
        "student_id": "STD-2024-007",
        "name": "Bilal Ahmed",
        "program": "BS Data Science",
        "department": "Computer Science",
        "semester": "Fall 2024",
        "total_semester_fee": 135000.0,
        "scholarship_or_concession": {
            "type": "None",
            "percentage": 0.0,
            "amount": 0.0,
            "status": "None"
        },
        "net_fee": 135000.0,
        "amount_paid": 135000.0,
        "outstanding_balance": 0.0,
        "payment_due_date": "2024-10-15",
        "installment_details": {
            "has_installment_plan": True,
            "plan_type": "2-Installment Plan",
            "total_installments": 2,
            "installments_paid": 2,
            "next_installment_amount": 0.0,
            "next_installment_due": None
        },
        "payment_status": "PAID",
        "exceptional_flag": False,
        "verification_status": "Verified",
        "notes": "Both installments completed early."
    },
    {
        "student_id": "STD-2024-008",
        "name": "Fatima Noor",
        "program": "BBA",
        "department": "Business Administration",
        "semester": "Fall 2024",
        "total_semester_fee": 105000.0,
        "scholarship_or_concession": {
            "type": "Kinship Concession",
            "percentage": 20.0,
            "amount": 21000.0,
            "status": "Approved"
        },
        "net_fee": 84000.0,
        "amount_paid": 84000.0,
        "outstanding_balance": 0.0,
        "payment_due_date": "2024-10-15",
        "installment_details": {
            "has_installment_plan": False,
            "plan_type": "Lump Sum",
            "total_installments": 1,
            "installments_paid": 1,
            "next_installment_amount": 0.0,
            "next_installment_due": None
        },
        "payment_status": "PAID",
        "exceptional_flag": False,
        "verification_status": "Verified",
        "notes": "Kinship fee concession applied."
    },
    {
        "student_id": "STD-2024-009",
        "name": "Omer Farooq",
        "program": "BS Mathematics",
        "department": "Mathematics",
        "semester": "Fall 2024",
        "total_semester_fee": 95000.0,
        "scholarship_or_concession": {
            "type": "None",
            "percentage": 0.0,
            "amount": 0.0,
            "status": "None"
        },
        "net_fee": 95000.0,
        "amount_paid": 95000.0,
        "outstanding_balance": 0.0,
        "payment_due_date": "2024-10-15",
        "installment_details": {
            "has_installment_plan": False,
            "plan_type": "Lump Sum",
            "total_installments": 1,
            "installments_paid": 1,
            "next_installment_amount": 0.0,
            "next_installment_due": None
        },
        "payment_status": "PAID",
        "exceptional_flag": False,
        "verification_status": "Verified",
        "notes": "Paid on time."
    },
    {
        "student_id": "STD-2024-010",
        "name": "Khadija Bibi",
        "program": "MS Computer Science",
        "department": "Computer Science",
        "semester": "Fall 2024",
        "total_semester_fee": 150000.0,
        "scholarship_or_concession": {
            "type": "Graduate Research Fellowship",
            "percentage": 50.0,
            "amount": 75000.0,
            "status": "Approved"
        },
        "net_fee": 75000.0,
        "amount_paid": 75000.0,
        "outstanding_balance": 0.0,
        "payment_due_date": "2024-10-15",
        "installment_details": {
            "has_installment_plan": False,
            "plan_type": "Lump Sum",
            "total_installments": 1,
            "installments_paid": 1,
            "next_installment_amount": 0.0,
            "next_installment_due": None
        },
        "payment_status": "PAID",
        "exceptional_flag": False,
        "verification_status": "Verified",
        "notes": "Research fellowship applied."
    },

    # --- Group 2: Partially Paid Students (Installment Plans, On-Track, Not Overdue) ---
    {
        "student_id": "STD-2024-011",
        "name": "Danish Riaz",
        "program": "BS Computer Science",
        "department": "Computer Science",
        "semester": "Fall 2024",
        "total_semester_fee": 120000.0,
        "scholarship_or_concession": {
            "type": "None",
            "percentage": 0.0,
            "amount": 0.0,
            "status": "None"
        },
        "net_fee": 120000.0,
        "amount_paid": 60000.0,
        "outstanding_balance": 60000.0,
        "payment_due_date": "2024-12-15",
        "installment_details": {
            "has_installment_plan": True,
            "plan_type": "2-Installment Plan",
            "total_installments": 2,
            "installments_paid": 1,
            "next_installment_amount": 60000.0,
            "next_installment_due": "2024-12-15"
        },
        "payment_status": "PARTIALLY_PAID",
        "exceptional_flag": False,
        "verification_status": "Verified",
        "notes": "Installment 1 paid. Installment 2 due in December."
    },
    {
        "student_id": "STD-2024-012",
        "name": "Ayesha Zubair",
        "program": "BBA",
        "department": "Business Administration",
        "semester": "Fall 2024",
        "total_semester_fee": 110000.0,
        "scholarship_or_concession": {
            "type": "None",
            "percentage": 0.0,
            "amount": 0.0,
            "status": "None"
        },
        "net_fee": 110000.0,
        "amount_paid": 36666.0,
        "outstanding_balance": 73334.0,
        "payment_due_date": "2024-11-20",
        "installment_details": {
            "has_installment_plan": True,
            "plan_type": "3-Installment Plan",
            "total_installments": 3,
            "installments_paid": 1,
            "next_installment_amount": 36667.0,
            "next_installment_due": "2024-11-20"
        },
        "payment_status": "PARTIALLY_PAID",
        "exceptional_flag": False,
        "verification_status": "Verified",
        "notes": "3 installments agreed. 1st installment paid."
    },
    {
        "student_id": "STD-2024-013",
        "name": "Saad Qureshi",
        "program": "BS Electrical Engineering",
        "department": "Electrical Engineering",
        "semester": "Fall 2024",
        "total_semester_fee": 140000.0,
        "scholarship_or_concession": {
            "type": "Need-Based Financial Aid",
            "percentage": 25.0,
            "amount": 35000.0,
            "status": "Approved"
        },
        "net_fee": 105000.0,
        "amount_paid": 52500.0,
        "outstanding_balance": 52500.0,
        "payment_due_date": "2024-12-01",
        "installment_details": {
            "has_installment_plan": True,
            "plan_type": "2-Installment Plan",
            "total_installments": 2,
            "installments_paid": 1,
            "next_installment_amount": 52500.0,
            "next_installment_due": "2024-12-01"
        },
        "payment_status": "PARTIALLY_PAID",
        "exceptional_flag": False,
        "verification_status": "Verified",
        "notes": "25% concession factored. 1st half cleared."
    },
    {
        "student_id": "STD-2024-014",
        "name": "Hira Hassan",
        "program": "BS Software Engineering",
        "department": "Computer Science",
        "semester": "Fall 2024",
        "total_semester_fee": 125000.0,
        "scholarship_or_concession": {
            "type": "None",
            "percentage": 0.0,
            "amount": 0.0,
            "status": "None"
        },
        "net_fee": 125000.0,
        "amount_paid": 83334.0,
        "outstanding_balance": 41666.0,
        "payment_due_date": "2024-12-15",
        "installment_details": {
            "has_installment_plan": True,
            "plan_type": "3-Installment Plan",
            "total_installments": 3,
            "installments_paid": 2,
            "next_installment_amount": 41666.0,
            "next_installment_due": "2024-12-15"
        },
        "payment_status": "PARTIALLY_PAID",
        "exceptional_flag": False,
        "verification_status": "Verified",
        "notes": "Two installments paid on time."
    },
    {
        "student_id": "STD-2024-015",
        "name": "Noman Bashir",
        "program": "BS Civil Engineering",
        "department": "Civil Engineering",
        "semester": "Fall 2024",
        "total_semester_fee": 115000.0,
        "scholarship_or_concession": {
            "type": "None",
            "percentage": 0.0,
            "amount": 0.0,
            "status": "None"
        },
        "net_fee": 115000.0,
        "amount_paid": 57500.0,
        "outstanding_balance": 57500.0,
        "payment_due_date": "2024-11-25",
        "installment_details": {
            "has_installment_plan": True,
            "plan_type": "2-Installment Plan",
            "total_installments": 2,
            "installments_paid": 1,
            "next_installment_amount": 57500.0,
            "next_installment_due": "2024-11-25"
        },
        "payment_status": "PARTIALLY_PAID",
        "exceptional_flag": False,
        "verification_status": "Verified",
        "notes": "First installment paid."
    },
    {
        "student_id": "STD-2024-016",
        "name": "Tayyaba Anum",
        "program": "BS Mathematics",
        "department": "Mathematics",
        "semester": "Fall 2024",
        "total_semester_fee": 95000.0,
        "scholarship_or_concession": {
            "type": "None",
            "percentage": 0.0,
            "amount": 0.0,
            "status": "None"
        },
        "net_fee": 95000.0,
        "amount_paid": 47500.0,
        "outstanding_balance": 47500.0,
        "payment_due_date": "2024-11-30",
        "installment_details": {
            "has_installment_plan": True,
            "plan_type": "2-Installment Plan",
            "total_installments": 2,
            "installments_paid": 1,
            "next_installment_amount": 47500.0,
            "next_installment_due": "2024-11-30"
        },
        "payment_status": "PARTIALLY_PAID",
        "exceptional_flag": False,
        "verification_status": "Verified",
        "notes": "First installment received."
    },
    {
        "student_id": "STD-2024-017",
        "name": "Waleed Khalid",
        "program": "BS Data Science",
        "department": "Computer Science",
        "semester": "Fall 2024",
        "total_semester_fee": 135000.0,
        "scholarship_or_concession": {
            "type": "Merit Scholarship",
            "percentage": 25.0,
            "amount": 33750.0,
            "status": "Approved"
        },
        "net_fee": 101250.0,
        "amount_paid": 50625.0,
        "outstanding_balance": 50625.0,
        "payment_due_date": "2024-12-10",
        "installment_details": {
            "has_installment_plan": True,
            "plan_type": "2-Installment Plan",
            "total_installments": 2,
            "installments_paid": 1,
            "next_installment_amount": 50625.0,
            "next_installment_due": "2024-12-10"
        },
        "payment_status": "PARTIALLY_PAID",
        "exceptional_flag": False,
        "verification_status": "Verified",
        "notes": "Quarter merit scholarship applied. 1st half paid."
    },
    {
        "student_id": "STD-2024-018",
        "name": "Zubair Shah",
        "program": "BBA",
        "department": "Business Administration",
        "semester": "Fall 2024",
        "total_semester_fee": 110000.0,
        "scholarship_or_concession": {
            "type": "None",
            "percentage": 0.0,
            "amount": 0.0,
            "status": "None"
        },
        "net_fee": 110000.0,
        "amount_paid": 55000.0,
        "outstanding_balance": 55000.0,
        "payment_due_date": "2024-12-05",
        "installment_details": {
            "has_installment_plan": True,
            "plan_type": "2-Installment Plan",
            "total_installments": 2,
            "installments_paid": 1,
            "next_installment_amount": 55000.0,
            "next_installment_due": "2024-12-05"
        },
        "payment_status": "PARTIALLY_PAID",
        "exceptional_flag": False,
        "verification_status": "Verified",
        "notes": "Half fee received."
    },

    # --- Group 3: Overdue Students (Passed due date with outstanding balance) ---
    # Reference date is assumed to be 2024-11-01 (or current). Due dates below are 2024-10-15 or earlier.
    {
        "student_id": "STD-2024-019",
        "name": "Farhan Saeed",
        "program": "BS Computer Science",
        "department": "Computer Science",
        "semester": "Fall 2024",
        "total_semester_fee": 120000.0,
        "scholarship_or_concession": {
            "type": "None",
            "percentage": 0.0,
            "amount": 0.0,
            "status": "None"
        },
        "net_fee": 120000.0,
        "amount_paid": 0.0,
        "outstanding_balance": 120000.0,
        "payment_due_date": "2024-10-15",
        "installment_details": {
            "has_installment_plan": False,
            "plan_type": "Lump Sum",
            "total_installments": 1,
            "installments_paid": 0,
            "next_installment_amount": 120000.0,
            "next_installment_due": "2024-10-15"
        },
        "payment_status": "OVERDUE",
        "exceptional_flag": False,
        "verification_status": "Verified",
        "notes": "No payment made. Overdue by 17+ days."
    },
    {
        "student_id": "STD-2024-020",
        "name": "Iqra Jamil",
        "program": "BBA",
        "department": "Business Administration",
        "semester": "Fall 2024",
        "total_semester_fee": 110000.0,
        "scholarship_or_concession": {
            "type": "None",
            "percentage": 0.0,
            "amount": 0.0,
            "status": "None"
        },
        "net_fee": 110000.0,
        "amount_paid": 30000.0,
        "outstanding_balance": 80000.0,
        "payment_due_date": "2024-10-20",
        "installment_details": {
            "has_installment_plan": True,
            "plan_type": "2-Installment Plan",
            "total_installments": 2,
            "installments_paid": 1,
            "next_installment_amount": 80000.0,
            "next_installment_due": "2024-10-20"
        },
        "payment_status": "OVERDUE",
        "exceptional_flag": False,
        "verification_status": "Verified",
        "notes": "Installment 2 was due on 2024-10-20. Balance overdue."
    },
    {
        "student_id": "STD-2024-021",
        "name": "Kamran Akmal",
        "program": "BS Electrical Engineering",
        "department": "Electrical Engineering",
        "semester": "Fall 2024",
        "total_semester_fee": 140000.0,
        "scholarship_or_concession": {
            "type": "None",
            "percentage": 0.0,
            "amount": 0.0,
            "status": "None"
        },
        "net_fee": 140000.0,
        "amount_paid": 40000.0,
        "outstanding_balance": 100000.0,
        "payment_due_date": "2024-10-15",
        "installment_details": {
            "has_installment_plan": False,
            "plan_type": "Lump Sum",
            "total_installments": 1,
            "installments_paid": 0,
            "next_installment_amount": 100000.0,
            "next_installment_due": "2024-10-15"
        },
        "payment_status": "OVERDUE",
        "exceptional_flag": False,
        "verification_status": "Verified",
        "notes": "Partial deposit made but overdue balance remains."
    },
    {
        "student_id": "STD-2024-022",
        "name": "Mehwish Hayat",
        "program": "BS Civil Engineering",
        "department": "Civil Engineering",
        "semester": "Fall 2024",
        "total_semester_fee": 115000.0,
        "scholarship_or_concession": {
            "type": "None",
            "percentage": 0.0,
            "amount": 0.0,
            "status": "None"
        },
        "net_fee": 115000.0,
        "amount_paid": 0.0,
        "outstanding_balance": 115000.0,
        "payment_due_date": "2024-10-15",
        "installment_details": {
            "has_installment_plan": False,
            "plan_type": "Lump Sum",
            "total_installments": 1,
            "installments_paid": 0,
            "next_installment_amount": 115000.0,
            "next_installment_due": "2024-10-15"
        },
        "payment_status": "OVERDUE",
        "exceptional_flag": False,
        "verification_status": "Verified",
        "notes": "Overdue notice served."
    },
    {
        "student_id": "STD-2024-023",
        "name": "Rashid Latif",
        "program": "BS Software Engineering",
        "department": "Computer Science",
        "semester": "Fall 2024",
        "total_semester_fee": 125000.0,
        "scholarship_or_concession": {
            "type": "None",
            "percentage": 0.0,
            "amount": 0.0,
            "status": "None"
        },
        "net_fee": 125000.0,
        "amount_paid": 25000.0,
        "outstanding_balance": 100000.0,
        "payment_due_date": "2024-10-15",
        "installment_details": {
            "has_installment_plan": False,
            "plan_type": "Lump Sum",
            "total_installments": 1,
            "installments_paid": 0,
            "next_installment_amount": 100000.0,
            "next_installment_due": "2024-10-15"
        },
        "payment_status": "OVERDUE",
        "exceptional_flag": False,
        "verification_status": "Verified",
        "notes": "Payment overdue. Exam slip blocked."
    },
    {
        "student_id": "STD-2024-024",
        "name": "Sana Mir",
        "program": "BS Mathematics",
        "department": "Mathematics",
        "semester": "Fall 2024",
        "total_semester_fee": 95000.0,
        "scholarship_or_concession": {
            "type": "None",
            "percentage": 0.0,
            "amount": 0.0,
            "status": "None"
        },
        "net_fee": 95000.0,
        "amount_paid": 0.0,
        "outstanding_balance": 95000.0,
        "payment_due_date": "2024-10-15",
        "installment_details": {
            "has_installment_plan": False,
            "plan_type": "Lump Sum",
            "total_installments": 1,
            "installments_paid": 0,
            "next_installment_amount": 95000.0,
            "next_installment_due": "2024-10-15"
        },
        "payment_status": "OVERDUE",
        "exceptional_flag": False,
        "verification_status": "Verified",
        "notes": "Second reminder issued."
    },
    {
        "student_id": "STD-2024-025",
        "name": "Taimur Baig",
        "program": "MS Computer Science",
        "department": "Computer Science",
        "semester": "Fall 2024",
        "total_semester_fee": 150000.0,
        "scholarship_or_concession": {
            "type": "None",
            "percentage": 0.0,
            "amount": 0.0,
            "status": "None"
        },
        "net_fee": 150000.0,
        "amount_paid": 50000.0,
        "outstanding_balance": 100000.0,
        "payment_due_date": "2024-10-10",
        "installment_details": {
            "has_installment_plan": True,
            "plan_type": "3-Installment Plan",
            "total_installments": 3,
            "installments_paid": 1,
            "next_installment_amount": 50000.0,
            "next_installment_due": "2024-10-10"
        },
        "payment_status": "OVERDUE",
        "exceptional_flag": False,
        "verification_status": "Verified",
        "notes": "Installment 2 missed on 2024-10-10."
    },

    # --- Group 4: Scholarship / Concession Focused (Approved and Pending HITL) ---
    {
        "student_id": "STD-2024-026",
        "name": "Umer Gul",
        "program": "BS Computer Science",
        "department": "Computer Science",
        "semester": "Fall 2024",
        "total_semester_fee": 120000.0,
        "scholarship_or_concession": {
            "type": "Merit Scholarship",
            "percentage": 75.0,
            "amount": 90000.0,
            "status": "Approved"
        },
        "net_fee": 30000.0,
        "amount_paid": 30000.0,
        "outstanding_balance": 0.0,
        "payment_due_date": "2024-10-15",
        "installment_details": {
            "has_installment_plan": False,
            "plan_type": "Lump Sum",
            "total_installments": 1,
            "installments_paid": 1,
            "next_installment_amount": 0.0,
            "next_installment_due": None
        },
        "payment_status": "PAID",
        "exceptional_flag": False,
        "verification_status": "Verified",
        "notes": "High merit scholarship 75% awarded by Dean."
    },
    {
        "student_id": "STD-2024-027",
        "name": "Wajiha Naqvi",
        "program": "BS Civil Engineering",
        "department": "Civil Engineering",
        "semester": "Fall 2024",
        "total_semester_fee": 115000.0,
        "scholarship_or_concession": {
            "type": "Need-Based Financial Aid",
            "percentage": 50.0,
            "amount": 57500.0,
            "status": "Approved"
        },
        "net_fee": 57500.0,
        "amount_paid": 57500.0,
        "outstanding_balance": 0.0,
        "payment_due_date": "2024-10-15",
        "installment_details": {
            "has_installment_plan": False,
            "plan_type": "Lump Sum",
            "total_installments": 1,
            "installments_paid": 1,
            "next_installment_amount": 0.0,
            "next_installment_due": None
        },
        "payment_status": "PAID",
        "exceptional_flag": False,
        "verification_status": "Verified",
        "notes": "Endowment fund covered 50%."
    },
    {
        "student_id": "STD-2024-028",
        "name": "Yasir Shah",
        "program": "BS Electrical Engineering",
        "department": "Electrical Engineering",
        "semester": "Fall 2024",
        "total_semester_fee": 140000.0,
        "scholarship_or_concession": {
            "type": "Kinship Concession",
            "percentage": 25.0,
            "amount": 35000.0,
            "status": "Approved"
        },
        "net_fee": 105000.0,
        "amount_paid": 70000.0,
        "outstanding_balance": 35000.0,
        "payment_due_date": "2024-11-28",
        "installment_details": {
            "has_installment_plan": True,
            "plan_type": "3-Installment Plan",
            "total_installments": 3,
            "installments_paid": 2,
            "next_installment_amount": 35000.0,
            "next_installment_due": "2024-11-28"
        },
        "payment_status": "PARTIALLY_PAID",
        "exceptional_flag": False,
        "verification_status": "Verified",
        "notes": "Kinship discount with 3 installment plan."
    },
    {
        "student_id": "STD-2024-029",
        "name": "Zohaib Khan",
        "program": "BBA",
        "department": "Business Administration",
        "semester": "Fall 2024",
        "total_semester_fee": 110000.0,
        "scholarship_or_concession": {
            "type": "Financial Hardship Concession",
            "percentage": 50.0,
            "amount": 55000.0,
            "status": "Pending Approval"
        },
        "net_fee": 110000.0, # Not deducted until approved
        "amount_paid": 55000.0,
        "outstanding_balance": 55000.0,
        "payment_due_date": "2024-11-15",
        "installment_details": {
            "has_installment_plan": False,
            "plan_type": "Lump Sum",
            "total_installments": 1,
            "installments_paid": 0,
            "next_installment_amount": 55000.0,
            "next_installment_due": "2024-11-15"
        },
        "payment_status": "CONCESSION_PENDING",
        "exceptional_flag": True,
        "verification_status": "Pending_HITL_Approval",
        "notes": "Student submitted emergency financial assistance request. Awaiting Finance Director HITL approval."
    },
    {
        "student_id": "STD-2024-030",
        "name": "Ali Raza",
        "program": "BS Software Engineering",
        "department": "Computer Science",
        "semester": "Fall 2024",
        "total_semester_fee": 125000.0,
        "scholarship_or_concession": {
            "type": "Special Sports Concession",
            "percentage": 40.0,
            "amount": 50000.0,
            "status": "Pending Approval"
        },
        "net_fee": 125000.0,
        "amount_paid": 75000.0,
        "outstanding_balance": 50000.0,
        "payment_due_date": "2024-11-20",
        "installment_details": {
            "has_installment_plan": False,
            "plan_type": "Lump Sum",
            "total_installments": 1,
            "installments_paid": 0,
            "next_installment_amount": 50000.0,
            "next_installment_due": "2024-11-20"
        },
        "payment_status": "CONCESSION_PENDING",
        "exceptional_flag": True,
        "verification_status": "Pending_HITL_Approval",
        "notes": "Sports director recommended 40% waiver. Awaiting Human-in-the-Loop clearance."
    },

    # --- Group 5: Incomplete / Inconsistent Records & Exceptional Edge Cases ---
    {
        "student_id": "STD-2024-031",
        "name": "Bilal Mustafa",
        "program": "BS Computer Science",
        "department": "Computer Science",
        "semester": "Fall 2024",
        "total_semester_fee": 120000.0,
        "scholarship_or_concession": {
            "type": "None",
            "percentage": 0.0,
            "amount": 0.0,
            "status": "None"
        },
        "net_fee": 120000.0,
        "amount_paid": 90000.0,
        "outstanding_balance": 50000.0, # INCONSISTENCY: 120000 - 90000 should be 30000, not 50000!
        "payment_due_date": "2024-10-15",
        "installment_details": {
            "has_installment_plan": False,
            "plan_type": "Lump Sum",
            "total_installments": 1,
            "installments_paid": 0,
            "next_installment_amount": 50000.0,
            "next_installment_due": "2024-10-15"
        },
        "payment_status": "INCOMPLETE_RECORD",
        "exceptional_flag": True,
        "verification_status": "Flagged_Inconsistent",
        "notes": "ARITHMETIC DISCREPANCY: Recorded balance (50,000) does not match total fee (120,000) minus paid (90,000). Needs reflection detection and HITL audit."
    },
    {
        "student_id": "STD-2024-032",
        "name": "Dua Zehra",
        "program": "BS Data Science",
        "department": "Computer Science",
        "semester": "Fall 2024",
        "total_semester_fee": 135000.0,
        "scholarship_or_concession": {
            "type": "None",
            "percentage": 0.0,
            "amount": 0.0,
            "status": "None"
        },
        "net_fee": 135000.0,
        "amount_paid": 60000.0,
        "outstanding_balance": 75000.0,
        "payment_due_date": None, # MISSING MANDATORY FIELD: due date is null
        "installment_details": {
            "has_installment_plan": True,
            "plan_type": "Corrupted Record",
            "total_installments": 0, # Inconsistent: plan is True but 0 total installments
            "installments_paid": 1,
            "next_installment_amount": 0.0,
            "next_installment_due": None
        },
        "payment_status": "INCOMPLETE_RECORD",
        "exceptional_flag": True,
        "verification_status": "Flagged_Incomplete",
        "notes": "INCOMPLETE DATA: Missing payment due date and corrupt installment configuration."
    },
    {
        "student_id": "STD-2024-033",
        "name": "Ehtisham Ul Haq",
        "program": "BS Electrical Engineering",
        "department": "Electrical Engineering",
        "semester": "Fall 2024",
        "total_semester_fee": 140000.0,
        "scholarship_or_concession": {
            "type": "None",
            "percentage": 0.0,
            "amount": 0.0,
            "status": "None"
        },
        "net_fee": 140000.0,
        "amount_paid": 155000.0, # OVERPAYMENT ANOMALY: Paid more than total fee
        "outstanding_balance": -15000.0,
        "payment_due_date": "2024-10-15",
        "installment_details": {
            "has_installment_plan": False,
            "plan_type": "Lump Sum",
            "total_installments": 1,
            "installments_paid": 1,
            "next_installment_amount": 0.0,
            "next_installment_due": None
        },
        "payment_status": "INCOMPLETE_RECORD",
        "exceptional_flag": True,
        "verification_status": "Flagged_Overpayment",
        "notes": "NEGATIVE BALANCE ANOMALY: Student overpaid by PKR 15,000. Requires refund or semester carry-forward adjustment."
    },
    {
        "student_id": "STD-2024-034",
        "name": "Faiza Rehman",
        "program": "BBA",
        "department": "Business Administration",
        "semester": "Fall 2024",
        "total_semester_fee": 110000.0,
        "scholarship_or_concession": {
            "type": "Dean Merit Concession",
            "percentage": 30.0,
            "amount": 33000.0,
            "status": "Pending Approval"
        },
        "net_fee": 110000.0,
        "amount_paid": 40000.0,
        "outstanding_balance": 70000.0,
        "payment_due_date": "2024-11-18",
        "installment_details": {
            "has_installment_plan": True,
            "plan_type": "2-Installment Plan",
            "total_installments": 2,
            "installments_paid": 1,
            "next_installment_amount": 37000.0,
            "next_installment_due": "2024-11-18"
        },
        "payment_status": "CONCESSION_PENDING",
        "exceptional_flag": True,
        "verification_status": "Pending_HITL_Approval",
        "notes": "30% concession submitted with recommendation letter. Pending Finance Admin approval."
    },
    {
        "student_id": "STD-2024-035",
        "name": "Ghulam Mustafa",
        "program": "BS Civil Engineering",
        "department": "Civil Engineering",
        "semester": "Fall 2024",
        "total_semester_fee": 115000.0,
        "scholarship_or_concession": {
            "type": "None",
            "percentage": 0.0,
            "amount": 0.0,
            "status": "None"
        },
        "net_fee": 115000.0,
        "amount_paid": 115000.0,
        "outstanding_balance": 0.0,
        "payment_due_date": "2024-10-15",
        "installment_details": {
            "has_installment_plan": False,
            "plan_type": "Lump Sum",
            "total_installments": 1,
            "installments_paid": 1,
            "next_installment_amount": 0.0,
            "next_installment_due": None
        },
        "payment_status": "PAID",
        "exceptional_flag": True, # Marked exceptional due to unverified wire transfer
        "verification_status": "Pending_HITL_Verification",
        "notes": "EXCEPTIONAL PAYMENT RECORD: Wire transfer deposited without university roll number in reference. Marked for Human Verification."
    }
]

def generate_files():
    # Save JSON
    json_path = "data/students_dataset.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(DATASET, f, indent=4)
    print(f"Saved {len(DATASET)} records to {json_path}")

    # Save CSV (flattened for easy spreadsheet reading)
    csv_path = "data/students_dataset.csv"
    fieldnames = [
        "student_id", "name", "program", "department", "semester",
        "total_semester_fee", "scholarship_type", "scholarship_percentage",
        "scholarship_amount", "scholarship_status", "net_fee", "amount_paid",
        "outstanding_balance", "payment_due_date", "has_installment_plan",
        "installment_plan_type", "total_installments", "installments_paid",
        "next_installment_amount", "next_installment_due", "payment_status",
        "exceptional_flag", "verification_status", "notes"
    ]

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in DATASET:
            flat_row = {
                "student_id": r["student_id"],
                "name": r["name"],
                "program": r["program"],
                "department": r["department"],
                "semester": r["semester"],
                "total_semester_fee": r["total_semester_fee"],
                "scholarship_type": r["scholarship_or_concession"]["type"],
                "scholarship_percentage": r["scholarship_or_concession"]["percentage"],
                "scholarship_amount": r["scholarship_or_concession"]["amount"],
                "scholarship_status": r["scholarship_or_concession"]["status"],
                "net_fee": r["net_fee"],
                "amount_paid": r["amount_paid"],
                "outstanding_balance": r["outstanding_balance"],
                "payment_due_date": r["payment_due_date"] or "N/A",
                "has_installment_plan": r["installment_details"]["has_installment_plan"],
                "installment_plan_type": r["installment_details"]["plan_type"],
                "total_installments": r["installment_details"]["total_installments"],
                "installments_paid": r["installment_details"]["installments_paid"],
                "next_installment_amount": r["installment_details"]["next_installment_amount"],
                "next_installment_due": r["installment_details"]["next_installment_due"] or "N/A",
                "payment_status": r["payment_status"],
                "exceptional_flag": r["exceptional_flag"],
                "verification_status": r["verification_status"],
                "notes": r["notes"]
            }
            writer.writerow(flat_row)
    print(f"Saved {len(DATASET)} records to {csv_path}")

if __name__ == "__main__":
    generate_files()
