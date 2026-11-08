"""
Trace Logger for Fee Management Agent.
Records full execution traces, state transitions, tool invocations, and reflection cycles
to local JSON files for evaluation and submission compliance.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List
from src.config import LOGS_DIR

TRACE_FILE = os.path.join(LOGS_DIR, "execution_traces.json")

class ExecutionTracer:
    """Manages recording and exporting of LangGraph execution traces."""

    def __init__(self, trace_file: str = TRACE_FILE):
        self.trace_file = trace_file
        self.traces: List[Dict[str, Any]] = []
        self._load_existing()

    def _load_existing(self):
        if os.path.exists(self.trace_file):
            try:
                with open(self.trace_file, "r", encoding="utf-8") as f:
                    self.traces = json.load(f)
            except Exception:
                self.traces = []

    def record_run(
        self,
        scenario_id: str,
        query: str,
        initial_state: Dict[str, Any],
        final_state: Dict[str, Any],
        interrupted: bool = False,
        interrupt_payload: Any = None,
        hitl_decision: Any = None,
        duration_ms: float = 0.0
    ):
        """Append an execution run trace."""
        entry = {
            "trace_id": f"TRACE-{datetime.now().strftime('%Y%m%d%H%M%S')}-{scenario_id}",
            "scenario": scenario_id,
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "duration_ms": duration_ms,
            "query_type": final_state.get("query_type"),
            "student_id": final_state.get("student_id"),
            "payment_status": final_state.get("payment_status"),
            "calculation_validated": final_state.get("calculation_validated"),
            "reflection_critique": final_state.get("reflection_critique"),
            "requires_human_approval": final_state.get("requires_human_approval"),
            "interrupted": interrupted,
            "interrupt_payload": str(interrupt_payload) if interrupt_payload else None,
            "hitl_decision": hitl_decision,
            "audit_trail": final_state.get("audit_trail", []),
            "final_response": final_state.get("final_response") or final_state.get("draft_response")
        }
        self.traces.append(entry)
        self._save()
        return entry

    def _save(self):
        with open(self.trace_file, "w", encoding="utf-8") as f:
            json.dump(self.traces, f, indent=2)

tracer = ExecutionTracer()
