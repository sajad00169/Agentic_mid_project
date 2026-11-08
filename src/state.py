"""
State Schema for the Student Fee Management Agent using LangGraph.
Defines the typed dictionary and helper classes that track state transitions across graph nodes.
"""

from typing import Annotated, Dict, Any, List, Optional
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """
    State definition for the LangGraph Fee Management & Financial Assistance Workflow.
    Preserved across node transitions and checkpointed by MemorySaver.
    """
    # Core conversation messages
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Query understanding
    query: str
    query_type: str
    student_id: Optional[str]
    department: Optional[str]
    
    # Retrieved & processed data
    student_record: Optional[Dict[str, Any]]
    payment_status: Optional[str]
    calculation_details: Optional[Dict[str, Any]]
    installment_details: Optional[Dict[str, Any]]
    summary_report: Optional[Dict[str, Any]]
    search_results: Optional[List[Dict[str, Any]]]
    
    # Reflection & validation mechanism
    calculation_validated: bool
    reflection_critique: Optional[str]
    reflection_retries: int
    draft_response: Optional[str]
    
    # Human-in-the-Loop (HITL) gate
    requires_human_approval: bool
    hitl_request: Optional[Dict[str, Any]]
    hitl_decision: Optional[Dict[str, Any]]
    verification_status: Optional[str]
    
    # Final output and traceability
    final_response: Optional[str]
    audit_trail: List[str]
