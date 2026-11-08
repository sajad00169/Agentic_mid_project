"""
Interactive Streamlit Dashboard & Chat UI for Student Fee Management Agent.
Provides:
  - Interactive LangGraph Chat Agent with Memory
  - Live Student Financial Records Explorer
  - Financial Analytics & Collection KPI Dashboard
  - Human-in-the-Loop Administrative Approval Queue
  - Audit Trail & Reflection Log Inspector
"""

import streamlit as st
import pandas as pd
import json
import time
from langgraph.types import Command
from langgraph.checkpoint.memory import MemorySaver

from src.graph import build_fee_agent_graph
from data.database import db
from src.config import REFERENCE_DATE, CURRENCY_SYMBOL

st.set_page_config(
    page_title="Student Fee Management Agent",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session State
if "checkpointer" not in st.session_state:
    st.session_state.checkpointer = MemorySaver()
    st.session_state.agent = build_fee_agent_graph(st.session_state.checkpointer)
    st.session_state.thread_id = f"st-session-{int(time.time())}"
    st.session_state.messages = []
    st.session_state.pending_interrupt = None

# Custom CSS styling
st.markdown("""
<style>
    .main-title { font-size: 2.2rem; font-weight: 700; color: #1E3A8A; margin-bottom: 0.2rem; }
    .sub-title { font-size: 1rem; color: #4B5563; margin-bottom: 1.5rem; }
    .metric-card { background-color: #F8FAFC; border-radius: 8px; padding: 15px; border-left: 4px solid #3B82F6; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    .status-paid { color: #059669; font-weight: 600; }
    .status-partial { color: #D97706; font-weight: 600; }
    .status-overdue { color: #DC2626; font-weight: 600; }
    .status-flagged { color: #7C3AED; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# Sidebar Navigation
st.sidebar.image("https://img.icons8.com/fluency/96/graduation-cap.png", width=70)
st.sidebar.title("Finance & Accounts")
st.sidebar.markdown(f"**Audit Date:** `{REFERENCE_DATE}`")
st.sidebar.markdown(f"**Active Session:** `{st.session_state.thread_id}`")

nav_choice = st.sidebar.radio(
    "Navigation",
    ["💬 AI Fee Assistant", "📊 Financial Dashboard", "📋 Student Records", "🛡️ HITL Approval Queue", "🔍 Audit & Reflection Logs"]
)

# -------------------------------------------------------------
# TAB 1: AI Fee Assistant (Chat)
# -------------------------------------------------------------
if nav_choice == "💬 AI Fee Assistant":
    st.markdown('<div class="main-title">Autonomous Fee Management Agent</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Powered by LangGraph StateGraph with Reflection and HITL Approval Gates</div>', unsafe_allow_html=True)

    # Example Query Chips
    st.markdown("**Quick Prompts:**")
    col1, col2, col3, col4 = st.columns(4)
    if col1.button("📌 Check STD-2024-001 (Fully Paid)"):
        st.session_state.quick_query = "What is the fee status of student STD-2024-001?"
    if col2.button("📌 Check STD-2024-019 (Overdue)"):
        st.session_state.quick_query = "Is student STD-2024-019 overdue on payments?"
    if col3.button("📌 Audit STD-2024-031 (Inconsistent)"):
        st.session_state.quick_query = "Audit student STD-2024-031 and check ledger discrepancy"
    if col4.button("📌 CS Department Summary"):
        st.session_state.quick_query = "What is the total fee collected in Computer Science?"

    # Display Chat History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "audit_trail" in msg and msg["audit_trail"]:
                with st.expander("🛠️ View Execution Audit Trail & State Steps"):
                    for step in msg["audit_trail"]:
                        st.caption(f"• {step}")

    # Pending Interrupt Banner
    if st.session_state.pending_interrupt:
        int_data = st.session_state.pending_interrupt
        st.warning("⚠️ **Workflow Paused: Human-in-the-Loop Authorization Gate**")
        st.info(f"**Action:** `{int_data.get('action_type')}`\n\n**Prompt:** {int_data.get('prompt')}")
        
        c_app, c_rej, c_actor = st.columns([1, 1, 2])
        officer = c_actor.text_input("Approving Officer:", value="Finance Director", key="officer_name")
        comments = st.text_input("Officer Justification/Notes:", value="Reviewed and authorized via web dashboard.", key="officer_notes")

        if c_app.button("✅ Approve Request", type="primary"):
            decision = {"approved": True, "authorized_by": officer, "comments": comments}
            config = {"configurable": {"thread_id": st.session_state.thread_id}}
            with st.spinner("Resuming agent workflow with approval..."):
                res = st.session_state.agent.invoke(Command(resume=decision), config=config)
                st.session_state.pending_interrupt = None
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": res.get("final_response") or res.get("draft_response"),
                    "audit_trail": res.get("audit_trail", [])
                })
                st.rerun()

        if c_rej.button("❌ Reject Request"):
            decision = {"approved": False, "authorized_by": officer, "comments": comments}
            config = {"configurable": {"thread_id": st.session_state.thread_id}}
            with st.spinner("Resuming agent workflow with rejection..."):
                res = st.session_state.agent.invoke(Command(resume=decision), config=config)
                st.session_state.pending_interrupt = None
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": res.get("final_response") or res.get("draft_response"),
                    "audit_trail": res.get("audit_trail", [])
                })
                st.rerun()

    # Chat Input Box
    query_input = st.chat_input("Ask any student fee, installment, scholarship, or department collection query...")
    active_query = query_input or st.session_state.pop("quick_query", None)

    if active_query:
        st.session_state.messages.append({"role": "user", "content": active_query})
        with st.chat_message("user"):
            st.markdown(active_query)

        config = {"configurable": {"thread_id": st.session_state.thread_id}}
        with st.chat_message("assistant"):
            with st.spinner("Agent evaluating fee ledger, checking dates, and reflecting..."):
                res = st.session_state.agent.invoke({"query": active_query}, config=config)

                if "__interrupt__" in res:
                    st.session_state.pending_interrupt = res["__interrupt__"][0].value
                    st.rerun()
                else:
                    ans = res.get("final_response") or res.get("draft_response")
                    st.markdown(ans)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": ans,
                        "audit_trail": res.get("audit_trail", [])
                    })
                    st.rerun()

# -------------------------------------------------------------
# TAB 2: Financial Analytics Dashboard
# -------------------------------------------------------------
elif nav_choice == "📊 Financial Dashboard":
    st.markdown('<div class="main-title">Financial Analytics & KPI Overview</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Real-time aggregation across all academic programs and departments</div>', unsafe_allow_html=True)

    records = db.get_all()
    total_billed = sum(r["total_semester_fee"] for r in records)
    total_concessions = sum(r.get("scholarship_or_concession", {}).get("amount", 0.0) for r in records if r.get("scholarship_or_concession", {}).get("status") == "Approved")
    net_collectible = total_billed - total_concessions
    total_collected = sum(r["amount_paid"] for r in records)
    total_outstanding = sum(r["outstanding_balance"] for r in records)
    efficiency = round((total_collected / net_collectible * 100), 2) if net_collectible else 0

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Enrolled", len(records))
    m2.metric("Gross Billed", f"{total_billed:,.0f} {CURRENCY_SYMBOL}")
    m3.metric("Fee Collected", f"{total_collected:,.0f} {CURRENCY_SYMBOL}")
    m4.metric("Outstanding Balance", f"{total_outstanding:,.0f} {CURRENCY_SYMBOL}")
    m5.metric("Collection Efficiency", f"{efficiency}%")

    st.divider()

    # Department Breakdown Table & Charts
    dept_stats = []
    for dept in ["Computer Science", "Business Administration", "Electrical Engineering", "Civil Engineering", "Mathematics"]:
        d_recs = [r for r in records if r["department"] == dept]
        if d_recs:
            b = sum(r["total_semester_fee"] for r in d_recs)
            c = sum(r["amount_paid"] for r in d_recs)
            o = sum(r["outstanding_balance"] for r in d_recs)
            eff = round((c / (b) * 100), 1) if b else 0
            dept_stats.append({
                "Department": dept,
                "Students": len(d_recs),
                "Billed (PKR)": b,
                "Collected (PKR)": c,
                "Outstanding (PKR)": o,
                "Recovery %": eff
            })
    df_dept = pd.DataFrame(dept_stats)

    col_left, col_right = st.columns([3, 2])
    with col_left:
        st.subheader("Departmental Collections vs. Outstanding")
        st.bar_chart(df_dept.set_index("Department")[["Collected (PKR)", "Outstanding (PKR)"]])
    with col_right:
        st.subheader("Department Comparison Table")
        st.dataframe(df_dept, use_container_width=True)

# -------------------------------------------------------------
# TAB 3: Student Financial Records Explorer
# -------------------------------------------------------------
elif nav_choice == "📋 Student Records":
    st.markdown('<div class="main-title">Student Financial Records Explorer</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Search, filter, and inspect individual student accounts</div>', unsafe_allow_html=True)

    records = db.get_all()
    
    f1, f2, f3 = st.columns([2, 2, 2])
    search_q = f1.text_input("🔍 Search by Student ID or Name:")
    dept_filter = f2.selectbox("Filter Department:", ["All"] + sorted(list({r["department"] for r in records})))
    status_filter = f3.selectbox("Filter Payment Status:", ["All", "PAID", "PARTIALLY_PAID", "OVERDUE", "CONCESSION_PENDING", "INCOMPLETE_RECORD"])

    filtered = records
    if search_q:
        q = search_q.strip().lower()
        filtered = [r for r in filtered if q in r["student_id"].lower() or q in r["name"].lower()]
    if dept_filter != "All":
        filtered = [r for r in filtered if r["department"] == dept_filter]
    if status_filter != "All":
        filtered = [r for r in filtered if r["payment_status"] == status_filter]

    st.write(f"Showing **{len(filtered)}** of {len(records)} records")

    rows = []
    for r in filtered:
        rows.append({
            "Student ID": r["student_id"],
            "Name": r["name"],
            "Department": r["department"],
            "Semester": r["semester"],
            "Total Fee": f"{r['total_semester_fee']:,.0f}",
            "Paid": f"{r['amount_paid']:,.0f}",
            "Outstanding": f"{r['outstanding_balance']:,.0f}",
            "Due Date": r.get("payment_due_date") or "N/A",
            "Status": r["payment_status"],
            "Scholarship": r.get("scholarship_or_concession", {}).get("type", "None"),
            "Verification": r.get("verification_status", "N/A")
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True)

# -------------------------------------------------------------
# TAB 4: Human-in-the-Loop Approval Queue
# -------------------------------------------------------------
elif nav_choice == "🛡️ HITL Approval Queue":
    st.markdown('<div class="main-title">Human-in-the-Loop Governance Queue</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Pending Concessions and Exceptional Record Audits Requiring Clearance</div>', unsafe_allow_html=True)

    records = db.get_all()
    pending = [r for r in records if r.get("exceptional_flag") or r.get("verification_status") in ["Pending_HITL_Approval", "Pending_HITL_Verification", "Flagged_Inconsistent"]]

    if not pending:
        st.success("🎉 All exceptional records and concession requests have been cleared. Zero items in queue.")
    else:
        st.info(f"📋 **{len(pending)}** item(s) currently awaiting administrative clearance.")

        for r in pending:
            sid = r["student_id"]
            sc = r.get("scholarship_or_concession", {})
            is_concession = sc.get("status") == "Pending Approval"
            
            with st.expander(f"⚠️ {sid} - {r['name']} ({'Concession Request' if is_concession else 'Exceptional/Flagged Record'})", expanded=True):
                c1, c2 = st.columns([3, 2])
                with c1:
                    st.markdown(f"**Program:** {r['program']} ({r['department']})")
                    st.markdown(f"**Total Fee:** {r['total_semester_fee']:,.2f} {CURRENCY_SYMBOL} | **Amount Paid:** {r['amount_paid']:,.2f} {CURRENCY_SYMBOL}")
                    st.markdown(f"**Recorded Balance:** {r['outstanding_balance']:,.2f} {CURRENCY_SYMBOL}")
                    if is_concession:
                        st.markdown(f"**Requested Concession:** {sc.get('type')} ({sc.get('percentage')}%, Discount: {sc.get('amount'):,.2f} {CURRENCY_SYMBOL})")
                    st.markdown(f"**Audit Notes:** `{r.get('notes')}`")
                
                with c2:
                    st.markdown("#### Authorization Action")
                    officer = st.text_input("Approving Officer Name:", value="Finance Director", key=f"officer_{sid}")
                    comments = st.text_input("Administrative Remarks:", value="Authorized based on institutional review.", key=f"comm_{sid}")
                    
                    b_app, b_rej = st.columns(2)
                    if b_app.button(f"Approve {sid}", key=f"app_{sid}", type="primary"):
                        if is_concession:
                            db.update_concession_status(sid, "Approved", officer, comments)
                        else:
                            db.update_verification_status(sid, "Verified", officer, comments)
                        st.success(f"Cleared {sid} successfully!")
                        time.sleep(1)
                        st.rerun()

                    if b_rej.button(f"Reject {sid}", key=f"rej_{sid}"):
                        if is_concession:
                            db.update_concession_status(sid, "Rejected", officer, comments)
                        else:
                            db.update_verification_status(sid, "Audit_Rejected", officer, comments)
                        st.error(f"Rejected {sid}.")
                        time.sleep(1)
                        st.rerun()

# -------------------------------------------------------------
# TAB 5: Audit & Reflection Logs
# -------------------------------------------------------------
elif nav_choice == "🔍 Audit & Reflection Logs":
    st.markdown('<div class="main-title">Audit Trail & Reflection Engine Inspector</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">System-wide transaction ledger and execution traces</div>', unsafe_allow_html=True)

    t1, t2 = st.tabs(["📝 Database Audit Trail", "⚡ LangGraph Execution Traces"])

    with t1:
        st.subheader("Database Mutation Events")
        if db.audit_log:
            st.dataframe(pd.DataFrame(db.audit_log), use_container_width=True)
        else:
            st.write("No database mutation events logged yet.")

    with t2:
        st.subheader("Execution Traces (logs/execution_traces.json)")
        trace_path = "logs/execution_traces.json"
        try:
            with open(trace_path, "r", encoding="utf-8") as f:
                traces = json.load(f)
            st.write(f"Loaded **{len(traces)}** execution traces.")
            for t in reversed(traces):
                with st.expander(f"{t.get('trace_id')} | Scenario: {t.get('scenario')} | Duration: {t.get('duration_ms')}ms"):
                    st.json(t)
        except Exception as e:
            st.warning(f"Could not load traces: {e}")
