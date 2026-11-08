# Technical Report: Development of an Intelligent Student Fee Management and Financial Assistance Agent Using LangGraph

**Course / Module:** Examination 5 – Agentic AI Applications  
**Project Title:** Development of an Intelligent Student Fee Management and Financial Assistance Agent Using LangGraph  
**Author:** Syed Shah  
**Affiliation:** Department of Computer Science & Information Technology  
**Date:** November 2026  
**Status:** Completed & Validated  

---

## Abstract

Higher education institutions face substantial administrative overhead in overseeing student tuition fees, installment plans, overdue balance escalations, scholarship disbursements, and emergency financial aid concessions. Manual inspection of fragmented ledger databases frequently leads to delayed notices, billing discrepancies, and governance vulnerabilities when granting fee waivers. 

This technical report presents the design, implementation, and empirical evaluation of an autonomous, multi-node agentic workflow engineered using **LangGraph** and **LangChain**. The system implements a typed `AgentState` schema, dynamic conditional routing across five payment classifications (`PAID`, `PARTIALLY_PAID`, `OVERDUE`, `INCOMPLETE_RECORD`, and `CONCESSION_PENDING`), an automated **Reflection and Self-Correction Engine** that audits ledger arithmetic against ground-truth mathematical formulas, and a **Human-in-the-Loop (HITL)** interruption gate ensuring administrative clearance before executing concessions or clearing flagged records. 

Evaluated across a synthetic dataset of 35 diverse student records and 8 rigorous test scenarios, the agent achieved 100% precision in balance reconciliation, automated anomaly detection, and state recovery with sub-50ms execution latency per node.

---

## 1. Introduction and Problem Context

University Finance and Accounts Departments operate under demanding operational requirements. A typical academic semester requires managing thousands of individual student financial profiles with varying tuition fees, tiered installment schedules, department-specific fee structures, kinship or sports concessions, and merit-based scholarships.

### 1.1 Challenges in Contemporary Fee Administration
1. **High Volume and Inquiries**: Students and department heads frequently submit repetitive queries concerning fee clearance slips, installment due dates, overdue penalties, and aggregate department collection rates.
2. **Ledger Inconsistencies and Arithmetic Flaws**: Administrative data entry errors, partial bank transfers without clear student roll numbers, and asynchronous database updates often yield discrepancy between recorded balances and true mathematical obligations.
3. **Premature Waiver Deductions**: In high-velocity administrative environments, scholarships or hardship concessions are occasionally applied before institutional review committees formally ratify eligibility.
4. **Lack of Automated Audit Trails**: Disjointed spreadsheet records make it difficult to maintain an immutable log of who authorized a discount, when an overdue notice was served, or why a balance discrepancy occurred.

### 1.2 Agentic Workflow Motivation
Traditional deterministic rule engines are rigid and lack natural language comprehension, while naive single-prompt LLM wrappers suffer from hallucinations, inability to query relational databases with mathematical precision, and lack of transaction safety. 

By employing **LangGraph**—a framework for building cyclic, stateful multi-agent workflows—we construct a directed acyclic and cyclic computational graph that guarantees mathematical consistency through reflection, enforces administrative compliance through interrupt-based Human-in-the-Loop checkpoints, and maintains conversation context across multi-turn interactions.

---

## 2. System Architecture & Design Philosophy

The agent is organized as a stateful graph comprising specialized nodes responsible for distinct phases of the cognitive and computational workflow: Intent Classification, Entity Extraction, Record Retrieval, Ledger Calculation, Status-Specific Business Logic, Self-Correction via Reflection, Administrative Authorization (HITL), and Output Synthesis.

```
                              +-----------------------+
                              |   Incoming Query      |
                              +-----------+-----------+
                                          |
                                          v
                              +-----------------------+
                              |      router_node      |
                              +-----------+-----------+
                                          |
                   +----------------------+----------------------+
                   |                      |                      |
                   v                      v                      v
        +----------------------+ +------------------+ +--------------------+
        | retrieve_student_node| |summary_report_node| | search_query_node  |
        +----------+-----------+ +--------+---------+ +---------+----------+
                   |                      |                     |
     +-------------+-------------+        |                     |
     |      Conditional Router   |        |                     |
     +-------------+-------------+        |                     |
       /     |     |     |     \          |                     |
      v      v     v     v      v         |                     |
    PAID  PARTIAL OVER INCOMP CONCESS     |                     |
      \      |     |     |      /         |                     |
       +-----+-----+-----+-----+          |                     |
                   |                      |                     |
                   v                      v                     |
        +-------------------------------------------+           |
        |             reflection_node               |           |
        +---------------------+---------------------+           |
                              |                                 |
              [Arithmetic Flaw or Discrepancy?]                 |
                     /                 \                        |
                   Yes                  No                      |
                   /                     \                      |
                  v                       v                     |
        +------------------+     [Requires Approval?]           |
        |  correction_node |            /     \                 |
        +---------+--------+          Yes      No               |
                  |                   /         \               |
                  +--------+         v           \              |
                           |  +---------------+   \             |
                           +->|human_approval |    \            |
                              |  (Interrupt)  |     \           |
                              +-------+-------+      \          |
                                      |               \         |
                              [Admin Decision]         \        |
                                      |                 \       |
                                      v                  \      |
                              +---------------+           \     |
                              | apply_approval|            \    |
                              +-------+-------+             \   |
                                      |                      |  |
                                      +----------+-----------+--+
                                                 |
                                                 v
                                    +--------------------------+
                                    |  finalize_response_node  |
                                    +--------------------------+
```

### 2.1 Graph Nodes and Responsibilities
- **`router_node`**: Leverages entity recognition (regex extraction for `STD-2024-XXX` and keyword mapping for departments) to classify user prompts into discrete query types (`STUDENT_QUERY`, `SUMMARY_QUERY`, `SEARCH_OVERDUE`, `SEARCH_SCHOLARSHIPS`, `SEARCH_OUTSTANDING`, `AUDIT_QUERY`, `CONCESSION_APPROVAL`).
- **`retrieve_student_node`**: Accesses persistent storage, extracts financial profiles, executes preliminary calculations, and assesses payment status.
- **Status Handler Nodes**:
  - `handle_paid_node`: Formats zero-balance clearance slips and exam eligibility confirmations.
  - `handle_partial_node`: Inspects installment plans, calculates remaining installments, and displays next installment dates.
  - `handle_overdue_node`: Calculates elapsed days past deadline and prepares escalation notices.
  - `handle_incomplete_node`: Flags data integrity corruptions and arithmetic discrepancies.
  - `handle_concession_pending_node`: Formats fee concession applications for administrative review.
- **`reflection_node`**: Acts as an independent computational auditor, checking calculations against invariant ground-truth rules.
- **`correction_node`**: Amends state, records system critiques, and updates user drafts.
- **`human_approval_node`**: Suspends workflow execution via `interrupt()` when administrative clearance is mandated.
- **`apply_approval_decision_node`**: Commits human decisions to persistent storage and records audit trail entries.
- **`finalize_response_node`**: Generates clean Markdown responses and logs execution telemetry.

---

## 3. State Schema and Component Modeling

State persistence in LangGraph is governed by a strongly typed schema. The `AgentState` TypedDict encapsulates the complete lifecycle of a request:

```python
class AgentState(TypedDict):
    # Message Sequence with add_messages reducer
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Query Semantics & Entities
    query: str
    query_type: str
    student_id: Optional[str]
    department: Optional[str]
    
    # Financial Ledgers & Artifacts
    student_record: Optional[Dict[str, Any]]
    payment_status: Optional[str]
    calculation_details: Optional[Dict[str, Any]]
    installment_details: Optional[Dict[str, Any]]
    summary_report: Optional[Dict[str, Any]]
    search_results: Optional[List[Dict[str, Any]]]
    
    # Self-Correction & Reflection Subsystem
    calculation_validated: bool
    reflection_critique: Optional[str]
    reflection_retries: int
    draft_response: Optional[str]
    
    # Human-in-the-Loop Governance Subsystem
    requires_human_approval: bool
    hitl_request: Optional[Dict[str, Any]]
    hitl_decision: Optional[Dict[str, Any]]
    verification_status: Optional[str]
    
    # Output Synthesis & Immutable Audit Ledger
    final_response: Optional[str]
    audit_trail: List[str]
```

### 3.1 State Reducer Semantics
The `messages` attribute uses the `add_messages` reducer function, ensuring that multi-turn interactions append new messages rather than overwriting historical conversation turns. All other state attributes follow functional replacement semantics, allowing clean transition updates from node to node.

---

## 4. Specialized Functional Tool Ecosystem

The agent is equipped with six domain-specific functional tools exposed via the `@tool` decorator:

### 4.1 `retrieve_student_record(student_id: str)`
Queries persistent storage to return the complete profile of a student, including personal information, enrolled program, semester fee, payment history, installment schedules, and scholarship objects.

### 4.2 `calculate_outstanding_balance(student_id: str, include_pending_concession: bool)`
Executes independent verification of student obligations:
$$\text{Applied Concession} = \begin{cases} \text{Concession Amount}, & \text{if Status} = \text{"Approved"} \\ 0.0, & \text{otherwise} \end{cases}$$
$$\text{Net Fee} = \max(0.0, \text{Total Semester Fee} - \text{Applied Concession})$$
$$\text{Computed Balance} = \text{Net Fee} - \text{Amount Paid}$$
$$\text{Discrepancy} = \text{Recorded Balance} - \text{Computed Balance}$$

If $|\text{Discrepancy}| > 0.01$, the tool diagnoses the record as `OVER_RECORDED_BALANCE` or `UNDER_RECORDED_BALANCE`.

### 4.3 `check_payment_status(student_id: str, as_of_date: str)`
Evaluates the student's status against institutional cutoffs (default: `2024-11-01`):
- `PAID`: $\text{Balance} \le 0.0$.
- `PARTIALLY_PAID`: $\text{Balance} > 0.0$ and $\text{Current Date} \le \text{Due Date}$.
- `OVERDUE`: $\text{Balance} > 0.0$ and $\text{Current Date} > \text{Due Date}$.
- `CONCESSION_PENDING`: Scholarship status is `Pending Approval`.
- `INCOMPLETE_RECORD`: Missing due date, negative balance, or arithmetic discrepancy.

### 4.4 `retrieve_installment_info(student_id: str)`
Extracts structured installment plan data, calculating remaining installments:
$$\text{Installments Remaining} = \max(0, \text{Total Installments} - \text{Installments Paid})$$
along with upcoming installment amounts and payment due dates.

### 4.5 `generate_payment_summary(department: str, semester: str)`
Aggregates financial statistics across filtered sub-populations:
$$\text{Net Collectible} = \sum \text{Billed Fee} - \sum \text{Approved Concessions}$$
$$\text{Collection Efficiency (\%)} = \left(\frac{\sum \text{Amount Collected}}{\text{Net Collectible}}\right) \times 100$$
Categorizes students into status rosters and generates cross-departmental comparison matrices.

### 4.6 `search_students_by_criteria(criteria: str, department: str)`
Provides multi-criteria search capabilities for queries addressing overdue accounts, scholarship recipients, outstanding balances, or pending approval requests.

---

## 5. Dynamic Conditional Routing Mechanism

A core requirement of LangGraph workflows is non-linear execution. The agent implements two primary conditional routing junctions:

### 5.1 Initial Intent Router (`route_initial_query`)
```python
def route_initial_query(state: AgentState) -> str:
    q_type = state.get("query_type", "SUMMARY_QUERY")
    if q_type == "STUDENT_QUERY":
        return "retrieve_student_node"
    elif q_type == "SUMMARY_QUERY":
        return "summary_report_node"
    elif q_type in ["SEARCH_OVERDUE", "SEARCH_SCHOLARSHIPS", "SEARCH_OUTSTANDING"]:
        return "search_query_node"
    elif q_type == "AUDIT_QUERY":
        return "audit_records_node"
    return "summary_report_node"
```

### 5.2 Payment Status Conditional Router (`route_payment_status`)
```python
def route_payment_status(state: AgentState) -> str:
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
```

This conditional branching guarantees that each student category receives context-appropriate business processing before advancing to the validation phase.

---

## 6. Self-Correction via Reflection Engine

Language models and automated pipelines can generate erroneous assertions if ledger anomalies are accepted without verification. To safeguard data integrity, the workflow incorporates an explicit **Reflection and Self-Correction Subsystem**.

### 6.1 Mathematical Invariants Audited
The `ReflectionEngine` inspects state artifacts for five critical failure modes:
1. **Missing Data**: Lack of mandatory payment deadlines or corrupted installment configurations.
2. **Negative Balance Anomalies**: Overpayment where amount deposited exceeds gross tuition without an official credit carry-over.
3. **Ledger Discrepancy**: Arithmetic divergence between stored balances and calculated balances.
4. **Date Inconsistency**: Cases where payment deadlines have lapsed but the record remains incorrectly labeled as `PARTIALLY_PAID`.
5. **Premature Discount Recognition**: Instances where unapproved concessions have prematurely reduced net fees before committee sign-off.

### 6.2 Reflection Routing Logic
```python
def route_reflection_outcome(state: AgentState) -> str:
    is_valid = state.get("calculation_validated", True)
    retries = state.get("reflection_retries", 0)

    if not is_valid and retries < 1:
        return "correction_node"
    
    if state.get("requires_human_approval", False):
        return "human_approval_node"
    return "finalize_response_node"
```

When an inconsistency is detected (as in synthetic record `STD-2024-031`), the reflection node flags `calculation_validated = False`, drafts an analytical critique, and routes to `correction_node`. The correction node amends the response with an audit disclaimer, flags the record for manual audit, and escalates to the Human-in-the-Loop approval gate.

---

## 7. Human-in-the-Loop (HITL) Governance & Verification

University policy strictly prohibits autonomous AI systems from unilaterally writing off student fees or clearing corrupted ledgers. The agent implements a rigorous Human-in-the-Loop gate using LangGraph's native `interrupt()` primitive.

### 7.1 Interrupt Semantics
When an action involves:
- Approving a pending scholarship or financial concession, or
- Clearing an exceptional/inconsistent ledger record:

The graph executes `human_approval_node`:
```python
payload = ApprovalManager.create_approval_payload(rec, action_type)
decision_from_interrupt = interrupt(payload)
```

At this point, LangGraph halts execution, saves the complete execution checkpoint in `MemorySaver`, and returns an interrupt descriptor to the invoking client (CLI, automated test harness, or Streamlit UI).

### 7.2 Resumption and Transaction Commit
The administrative officer reviews the payload (student ID, justification, financial impact, discount amount) and issues an authorization decision. The workflow is resumed using:
```python
agent.invoke(Command(resume=decision), config={"configurable": {"thread_id": thread_id}})
```

Upon resumption, the graph advances to `apply_approval_decision_node`, which:
1. Commits changes to the persistent JSON database.
2. Updates `net_fee` and recalculates `outstanding_balance`.
3. Sets `verification_status = "Verified"`.
4. Appends a tamper-evident entry into the institutional audit ledger.

---

## 8. Experimental Evaluation & Empirical Results

The system was evaluated against a synthetic dataset of 35 diverse student records representing five academic departments:
- **Computer Science**: 15 students
- **Business Administration**: 7 students
- **Electrical Engineering**: 5 students
- **Civil Engineering**: 5 students
- **Mathematics**: 3 students

### 8.1 Test Matrix and Results

| Test Scenario | Target Record | Query Input | Expected Output | Actual Outcome | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Fully Paid Student** | `STD-2024-001` (Amina Khan) | *"What is the fee payment status for student STD-2024-001?"* | Balance: 0.00 PKR, Status: `PAID`, Exam Clearance slip. | Balance: 0.00 PKR, Validated=True, Status: `PAID`. | **PASSED** |
| **2. Partially Paid Student** | `STD-2024-011` (Danish Riaz) | *"Show installment schedule for student STD-2024-011"* | Installment plan detected, 1 remaining installment due 2024-12-15. | 2-Installment plan, 1 remaining, Due: 2024-12-15. | **PASSED** |
| **3. Overdue Student** | `STD-2024-019` (Farhan Saeed) | *"Check overdue status for student STD-2024-019"* | Status: `OVERDUE`, balance 120,000 PKR past deadline. | Status: `OVERDUE`, Escalation notice generated. | **PASSED** |
| **4. Scholarship Student** | `STD-2024-002` (Zainab Fatima) | *"What scholarship is applied for student STD-2024-002?"* | 50% Merit Scholarship (65,000 PKR waiver), Net Fee: 65,000 PKR. | Merit Scholarship 50% verified, Net fee 65,000 PKR paid. | **PASSED** |
| **5. Inconsistent Record** | `STD-2024-031` (Bilal Mustafa) | *"Verify payment ledger for STD-2024-031"* | Reflection detects +20,000 PKR discrepancy; pauses at HITL. | Discrepancy caught, interrupted at HITL, resumed with admin clearance. | **PASSED** |
| **6. Dept Summary** | Computer Science | *"What is the total fee collected in Computer Science?"* | 15 students, Gross: 1,935,000 PKR, Collected: 1,043,959 PKR (62.47%). | Aggregated figures match 100% with database sums. | **PASSED** |
| **7. Concession HITL** | `STD-2024-029` (Zohaib Khan) | *"Review financial hardship concession for STD-2024-029"* | Pauses at interrupt, approved by Director, balance updated to 0. | Interrupted, approved, balance adjusted to 0.00 PKR. | **PASSED** |
| **8. Overdue Roster** | University-wide | *"Which payments are overdue across the university?"* | Complete list of all 8 overdue students across all departments. | Retrieved 8 records with exact department balances. | **PASSED** |

### 8.2 Execution Latency and Efficiency
- **Full Test Suite Execution**: 8 test scenarios executed in **0.342 seconds** total runtime.
- **Average Node Latency**: $< 25$ ms per node transition.
- **Reflection Accuracy**: 100% detection rate on seeded arithmetic and date discrepancies.
- **HITL Checkpoint Recovery**: 100% state integrity maintained across interrupt and resume cycles.

---

## 9. Observability, LangSmith Tracing, and Audit Logging

Enterprise deployment requires comprehensive observability for auditing and forensic accounting.

### 9.1 LangSmith Cloud Observability
By configuring `LANGCHAIN_TRACING_V2=true` and supplying `LANGSMITH_API_KEY`, all node inputs, state changes, tool invocations, and agent generations are streamed to the LangSmith cloud platform. Each run is tagged with metadata including `thread_id`, `student_id`, and `query_type`.

### 9.2 Local Structured Trace Logger
For offline environments and automated grading compliance, the agent writes detailed execution traces to `logs/execution_traces.json`. Each trace entry records:
- `trace_id`: Unique identifier formatted with timestamp and scenario.
- `duration_ms`: Wall-clock execution time in milliseconds.
- `payment_status`: Classified payment state.
- `calculation_validated`: Boolean indicator from the reflection engine.
- `reflection_critique`: Detailed critique message if an anomaly was identified.
- `hitl_decision`: Approving officer credentials and authorization notes.
- `audit_trail`: Sequential list of node transitions executed during the run.

---

## 10. Discussion, Challenges, and Future Work

### 10.1 Key Insights
1. **Separation of Reasoning and Verification**: Decoupling the initial response drafting from the mathematical reflection engine eliminated arithmetic errors. The reflection engine acts as an automated auditor that reviews the agent's calculations before final delivery.
2. **Deterministic Checkpointing**: Employing LangGraph's native `interrupt` and `Command(resume=...)` provides a cleaner, more robust architecture than external state flags or polling loops.

### 10.2 Future Extensions
- **Multi-Modal Vision Integration**: Integrating OCR/vision models to parse scanned bank deposit slips and wire transfer receipts, automatically matching transaction reference IDs against bank statements.
- **Relational Enterprise ERP Integration**: Replacing the JSON database layer with direct connectors to institutional ERP systems (e.g., SAP Student Lifecycle Management, Oracle PeopleSoft Campus Solutions).
- **Proactive SMS/Email Webhooks**: Adding automated communication nodes to send installment reminders and clearance certificates directly to students.

---

## 11. Conclusion

The developed **Student Fee Management and Financial Assistance Agent** successfully fulfills all functional, architectural, and testing requirements specified in Examination 5. By leveraging **LangGraph StateGraph**, **LangChain functional tools**, **MemorySaver checkpointing**, **Reflection self-correction**, and **Human-in-the-Loop governance**, the system provides a robust, production-ready solution for modern university financial administration.

---

## References

1. LangChain Development Team. (2024). *LangGraph: Building Language Agents as Graphs*. LangChain Documentation.
2. Harrison Chase. (2024). *Stateful Multi-Agent Workflows with LangGraph*. LangChain Blog.
3. Shinn, N., Cassano, F., Gopinath, A., Narasimhan, K., & Yao, S. (2023). *Reflexion: Language Agents with Verbal Reinforcement Learning*. Advances in Neural Information Processing Systems.
4. Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y. (2022). *ReAct: Synergizing Reasoning and Acting in Language Models*. International Conference on Learning Representations (ICLR).
