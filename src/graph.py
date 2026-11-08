"""
LangGraph StateGraph Definition for Student Fee Management and Financial Assistance Agent.
Constructs the complete computational graph with conditional routing, reflection loop,
Human-in-the-Loop approval gate, and memory checkpointing.
"""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from src.state import AgentState
from src.nodes import (
    router_node,
    retrieve_student_node,
    handle_paid_node,
    handle_partial_node,
    handle_overdue_node,
    handle_incomplete_node,
    handle_concession_pending_node,
    summary_report_node,
    search_query_node,
    audit_records_node,
    reflection_node,
    correction_node,
    human_approval_node,
    apply_approval_decision_node,
    finalize_response_node
)

# -------------------------------------------------------------
# Conditional Routing Functions
# -------------------------------------------------------------
def route_initial_query(state: AgentState) -> str:
    """Route from router_node based on query classification."""
    q_type = state.get("query_type", "SUMMARY_QUERY")
    
    if q_type == "STUDENT_QUERY":
        return "retrieve_student_node"
    elif q_type == "SUMMARY_QUERY":
        return "summary_report_node"
    elif q_type in ["SEARCH_OVERDUE", "SEARCH_SCHOLARSHIPS", "SEARCH_OUTSTANDING"]:
        return "search_query_node"
    elif q_type == "AUDIT_QUERY":
        return "audit_records_node"
    elif q_type in ["CONCESSION_APPROVAL", "EXCEPTIONAL_VERIFICATION"]:
        if state.get("student_id"):
            return "retrieve_student_node"
        return "audit_records_node"
    return "summary_report_node"

def route_payment_status(state: AgentState) -> str:
    """Conditional edge routing based on verified payment status."""
    status = state.get("payment_status", "UNKNOWN")
    
    if status == "PAID":
        return "handle_paid_node"
    elif status == "PARTIALLY_PAID":
        return "handle_partial_node"
    elif status == "OVERDUE":
        return "handle_overdue_node"
    elif status == "INCOMPLETE_RECORD":
        return "handle_incomplete_node"
    elif status == "CONCESSION_PENDING":
        return "handle_concession_pending_node"
    return "handle_paid_node"

def route_reflection_outcome(state: AgentState) -> str:
    """Route after reflection: trigger correction if invalid, else check HITL."""
    is_valid = state.get("calculation_validated", True)
    retries = state.get("reflection_retries", 0)

    if not is_valid and retries < 1:
        return "correction_node"
    
    # Check if HITL is needed
    if state.get("requires_human_approval", False):
        return "human_approval_node"
    return "finalize_response_node"

def route_post_correction(state: AgentState) -> str:
    """Route after applying reflection correction."""
    if state.get("requires_human_approval", False):
        return "human_approval_node"
    return "finalize_response_node"

# -------------------------------------------------------------
# Build and Compile StateGraph
# -------------------------------------------------------------
def build_fee_agent_graph(checkpointer: MemorySaver = None):
    """
    Constructs and compiles the StateGraph workflow for the Fee Management Agent.
    """
    builder = StateGraph(AgentState)

    # 1. Add all functional nodes
    builder.add_node("router_node", router_node)
    builder.add_node("retrieve_student_node", retrieve_student_node)
    builder.add_node("handle_paid_node", handle_paid_node)
    builder.add_node("handle_partial_node", handle_partial_node)
    builder.add_node("handle_overdue_node", handle_overdue_node)
    builder.add_node("handle_incomplete_node", handle_incomplete_node)
    builder.add_node("handle_concession_pending_node", handle_concession_pending_node)
    builder.add_node("summary_report_node", summary_report_node)
    builder.add_node("search_query_node", search_query_node)
    builder.add_node("audit_records_node", audit_records_node)
    builder.add_node("reflection_node", reflection_node)
    builder.add_node("correction_node", correction_node)
    builder.add_node("human_approval_node", human_approval_node)
    builder.add_node("apply_approval_decision_node", apply_approval_decision_node)
    builder.add_node("finalize_response_node", finalize_response_node)

    # 2. Entry edge
    builder.add_edge(START, "router_node")

    # 3. Conditional routing from router
    builder.add_conditional_edges(
        "router_node",
        route_initial_query,
        {
            "retrieve_student_node": "retrieve_student_node",
            "summary_report_node": "summary_report_node",
            "search_query_node": "search_query_node",
            "audit_records_node": "audit_records_node"
        }
    )

    # 4. Conditional status routing from retrieve_student_node
    builder.add_conditional_edges(
        "retrieve_student_node",
        route_payment_status,
        {
            "handle_paid_node": "handle_paid_node",
            "handle_partial_node": "handle_partial_node",
            "handle_overdue_node": "handle_overdue_node",
            "handle_incomplete_node": "handle_incomplete_node",
            "handle_concession_pending_node": "handle_concession_pending_node"
        }
    )

    # 5. Handlers transition into reflection
    builder.add_edge("handle_paid_node", "reflection_node")
    builder.add_edge("handle_partial_node", "reflection_node")
    builder.add_edge("handle_overdue_node", "reflection_node")
    builder.add_edge("handle_incomplete_node", "reflection_node")
    builder.add_edge("handle_concession_pending_node", "reflection_node")
    builder.add_edge("summary_report_node", "reflection_node")

    # Direct routes for search and audit roasters
    builder.add_edge("search_query_node", "finalize_response_node")
    builder.add_edge("audit_records_node", "finalize_response_node")

    # 6. Conditional routing from reflection
    builder.add_conditional_edges(
        "reflection_node",
        route_reflection_outcome,
        {
            "correction_node": "correction_node",
            "human_approval_node": "human_approval_node",
            "finalize_response_node": "finalize_response_node"
        }
    )

    # 7. Post-correction edge
    builder.add_conditional_edges(
        "correction_node",
        route_post_correction,
        {
            "human_approval_node": "human_approval_node",
            "finalize_response_node": "finalize_response_node"
        }
    )

    # 8. HITL edges
    builder.add_edge("human_approval_node", "apply_approval_decision_node")
    builder.add_edge("apply_approval_decision_node", "finalize_response_node")

    # 9. Terminal edge
    builder.add_edge("finalize_response_node", END)

    # Checkpointer
    memory = checkpointer or MemorySaver()
    app = builder.compile(checkpointer=memory)
    return app

# Default compiled graph instance
default_checkpointer = MemorySaver()
fee_agent_app = build_fee_agent_graph(default_checkpointer)
