"""
graph.py — Supervisor Orchestrator
Sprint 1: Implement AgentState, supervisor_node, route_decision và kết nối graph.

Kiến trúc:
    Input → Supervisor → [retrieval_worker | policy_tool_worker | human_review] → synthesis → Output

Chạy thử:
    python graph.py
"""

import json
import os
import re
from datetime import datetime
from typing import TypedDict, Literal, Optional

# Uncomment nếu dùng LangGraph:
# from langgraph.graph import StateGraph, END

# ─────────────────────────────────────────────
# 1. Shared State — dữ liệu đi xuyên toàn graph
# ─────────────────────────────────────────────

class AgentState(TypedDict):
    # Input
    task: str                           # Câu hỏi đầu vào từ user

    # Supervisor decisions
    route_reason: str                   # Lý do route sang worker nào
    risk_high: bool                     # True → cần HITL hoặc human_review
    needs_tool: bool                    # True → cần gọi external tool qua MCP
    hitl_triggered: bool                # True → đã pause cho human review

    # Worker outputs
    retrieved_chunks: list              # Output từ retrieval_worker
    retrieved_sources: list             # Danh sách nguồn tài liệu
    policy_result: dict                 # Output từ policy_tool_worker
    mcp_tools_used: list                # Danh sách MCP tools đã gọi

    # Final output
    final_answer: str                   # Câu trả lời tổng hợp
    sources: list                       # Sources được cite
    confidence: float                   # Mức độ tin cậy (0.0 - 1.0)

    # Trace & history
    history: list                       # Lịch sử các bước đã qua
    workers_called: list                # Danh sách workers đã được gọi
    supervisor_route: str               # Worker được chọn bởi supervisor
    latency_ms: Optional[int]           # Thời gian xử lý (ms)
    run_id: str                         # ID của run này


def make_initial_state(task: str) -> AgentState:
    """Khởi tạo state cho một run mới."""
    return {
        "task": task,
        "route_reason": "",
        "risk_high": False,
        "needs_tool": False,
        "hitl_triggered": False,
        "retrieved_chunks": [],
        "retrieved_sources": [],
        "policy_result": {},
        "mcp_tools_used": [],
        "final_answer": "",
        "sources": [],
        "confidence": 0.0,
        "history": [],
        "workers_called": [],
        "supervisor_route": "",
        "latency_ms": None,
        "run_id": f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
    }


# ─────────────────────────────────────────────
# 2. Supervisor Node — quyết định route
# ─────────────────────────────────────────────

# Routing keyword groups
_POLICY_KEYWORDS = [
    "hoàn tiền", "hoàn lại tiền", "refund",
    "flash sale",
    "license", "bản quyền",
    "cấp quyền", "xin quyền", "phê duyệt quyền",
    "access level", "access permission",
    "quyền truy cập", "level 3", "level 2",
    "kích hoạt", "activated",
    "sản phẩm số", "digital product", "subscription",
]

_RETRIEVAL_KEYWORDS = [
    "p1", "sla",
    "ticket", "escalation", "leo thang",
    "sự cố", "incident",
    "faq", "hướng dẫn", "quy trình",
    "nghỉ phép", "leave", "remote work", "làm từ xa",
    "helpdesk", "it support",
]

_RISK_KEYWORDS = [
    "emergency", "khẩn cấp",
    "2am", "ngoài giờ",
    "không rõ",
    "lỗi bí ẩn",
]

_TOOL_KEYWORDS = [
    "cấp quyền", "xin quyền", "access level", "level 3", "level 2",
    "access permission", "quyền truy cập",
    "ticket", "tạo ticket",
    "check", "kiểm tra",
]

# Regex để nhận mã lỗi dạng ERR-xxx
_ERR_CODE_PATTERN = re.compile(r"\berr[-_]\w+\b", re.IGNORECASE)


def supervisor_node(state: AgentState) -> AgentState:
    """
    Supervisor phân tích task và quyết định:
    1. Route sang worker nào
    2. Có cần MCP tool không
    3. Có risk cao cần HITL không
    """
    task = state["task"]
    task_lower = task.lower()
    state["history"].append(f"[supervisor] received task: {task[:80]}")

    route = "retrieval_worker"
    route_reasons = []
    needs_tool = False
    risk_high = False

    # ── Kiểm tra mã lỗi không rõ (ERR-xxx) ──────────────────────────────
    has_err_code = bool(_ERR_CODE_PATTERN.search(task_lower))

    # ── Risk assessment ──────────────────────────────────────────────────
    triggered_risk = [kw for kw in _RISK_KEYWORDS if kw in task_lower]
    if triggered_risk or has_err_code:
        risk_high = True
        risk_desc = ", ".join(triggered_risk) if triggered_risk else ""
        if has_err_code:
            risk_desc += (" | " if risk_desc else "") + "unknown error code detected"
        route_reasons.append(f"risk_high: {risk_desc}")

    # ── Human review: mã lỗi lạ + risk_high ─────────────────────────────
    if risk_high and has_err_code:
        route = "human_review"
        route_reasons.append("unknown error code + risk_high → human_review")

    # ── Policy/Tool worker ───────────────────────────────────────────────
    elif any(kw in task_lower for kw in _POLICY_KEYWORDS):
        triggered = [kw for kw in _POLICY_KEYWORDS if kw in task_lower]
        route = "policy_tool_worker"
        route_reasons.append(f"policy keyword matched: {', '.join(triggered)}")
        # Kiểm tra có cần gọi MCP tool không
        if any(kw in task_lower for kw in _TOOL_KEYWORDS):
            tool_triggered = [kw for kw in _TOOL_KEYWORDS if kw in task_lower]
            needs_tool = True
            route_reasons.append(f"MCP tool needed: {', '.join(tool_triggered)}")

    # ── Retrieval worker ─────────────────────────────────────────────────
    elif any(kw in task_lower for kw in _RETRIEVAL_KEYWORDS):
        triggered = [kw for kw in _RETRIEVAL_KEYWORDS if kw in task_lower]
        route = "retrieval_worker"
        route_reasons.append(f"retrieval keyword matched: {', '.join(triggered)}")

    # ── Default ──────────────────────────────────────────────────────────
    else:
        route = "retrieval_worker"
        route_reasons.append("no specific keyword matched → default retrieval")

    route_reason = " | ".join(route_reasons) if route_reasons else "default retrieval route"

    state["supervisor_route"] = route
    state["route_reason"] = route_reason
    state["needs_tool"] = needs_tool
    state["risk_high"] = risk_high
    state["history"].append(
        f"[supervisor] route={route} needs_tool={needs_tool} risk_high={risk_high} reason={route_reason}"
    )

    return state


# ─────────────────────────────────────────────
# 3. Route Decision — conditional edge
# ─────────────────────────────────────────────

def route_decision(state: AgentState) -> Literal["retrieval_worker", "policy_tool_worker", "human_review"]:
    """
    Trả về tên worker tiếp theo dựa vào supervisor_route trong state.
    Đây là conditional edge của graph.
    """
    route = state.get("supervisor_route", "retrieval_worker")
    return route  # type: ignore


# ─────────────────────────────────────────────
# 4. Human Review Node — HITL placeholder
# ─────────────────────────────────────────────

def human_review_node(state: AgentState) -> AgentState:
    """
    HITL node: pause và chờ human approval.
    Trong lab này, implement dưới dạng placeholder (in ra warning).
    """
    state["hitl_triggered"] = True
    state["history"].append("[human_review] HITL triggered — awaiting human input")
    state["workers_called"].append("human_review")

    print(f"\n⚠️  HITL TRIGGERED")
    print(f"   Task: {state['task']}")
    print(f"   Reason: {state['route_reason']}")
    print(f"   Action: Auto-approving in lab mode (set hitl_triggered=True)\n")

    # Sau khi human approve, route về retrieval để lấy evidence
    state["supervisor_route"] = "retrieval_worker"
    state["route_reason"] += " | human approved → retrieval"

    return state


# ─────────────────────────────────────────────
# 5. Import Workers
# ─────────────────────────────────────────────

try:
    from workers.retrieval import run as retrieval_run
    from workers.policy_tool import run as policy_tool_run
    from workers.synthesis import run as synthesis_run
    _WORKERS_AVAILABLE = True
except ImportError as _import_err:
    _WORKERS_AVAILABLE = False
    _IMPORT_ERROR = str(_import_err)


def retrieval_worker_node(state: AgentState) -> AgentState:
    """Wrapper gọi retrieval worker."""
    state["history"].append("[retrieval_worker] called")

    if _WORKERS_AVAILABLE:
        # run() trong worker tự append vào workers_called
        state = retrieval_run(state)
    else:
        # Fallback placeholder khi workers chưa cài dependencies
        print(f"⚠️  retrieval worker unavailable ({_IMPORT_ERROR}), using placeholder")
        state["workers_called"].append("retrieval_worker")
        state["retrieved_chunks"] = [
            {"text": "SLA P1: phản hồi 15 phút, xử lý 4 giờ.", "source": "sla_p1_2026.txt", "score": 0.92}
        ]
        state["retrieved_sources"] = ["sla_p1_2026.txt"]

    state["history"].append(f"[retrieval_worker] retrieved {len(state['retrieved_chunks'])} chunks")
    return state


def policy_tool_worker_node(state: AgentState) -> AgentState:
    """Wrapper gọi policy/tool worker."""
    state["history"].append("[policy_tool_worker] called")

    if _WORKERS_AVAILABLE:
        # run() trong worker tự append vào workers_called
        state = policy_tool_run(state)
    else:
        # Fallback placeholder
        print(f"⚠️  policy_tool worker unavailable ({_IMPORT_ERROR}), using placeholder")
        state["workers_called"].append("policy_tool_worker")
        state["policy_result"] = {
            "policy_applies": True,
            "policy_name": "refund_policy_v4",
            "exceptions_found": [],
            "source": "policy_refund_v4.txt",
        }

    state["history"].append("[policy_tool_worker] policy check complete")
    return state


def synthesis_worker_node(state: AgentState) -> AgentState:
    """Wrapper gọi synthesis worker."""
    state["history"].append("[synthesis_worker] called")

    if _WORKERS_AVAILABLE:
        # run() trong worker tự append vào workers_called
        state = synthesis_run(state)
    else:
        # Fallback placeholder
        print(f"⚠️  synthesis worker unavailable ({_IMPORT_ERROR}), using placeholder")
        state["workers_called"].append("synthesis_worker")
        chunks = state.get("retrieved_chunks", [])
        sources = state.get("retrieved_sources", [])
        state["final_answer"] = f"[PLACEHOLDER] Câu trả lời được tổng hợp từ {len(chunks)} chunks."
        state["sources"] = sources
        state["confidence"] = 0.75

    state["history"].append(f"[synthesis_worker] answer generated, confidence={state['confidence']}")
    return state


# ─────────────────────────────────────────────
# 6. Build Graph
# ─────────────────────────────────────────────

def build_graph():
    """
    Xây dựng graph với supervisor-worker pattern.
    Option A (đơn giản — Python thuần): Dùng if/else, không cần LangGraph.
    """
    def run(state: AgentState) -> AgentState:
        import time
        start = time.time()

        # Step 1: Supervisor decides route
        state = supervisor_node(state)

        # Step 2: Route to appropriate worker
        route = route_decision(state)

        if route == "human_review":
            state = human_review_node(state)
            # After human approval, continue with retrieval
            state = retrieval_worker_node(state)

        elif route == "policy_tool_worker":
            # Policy worker cần retrieval context trước để phân tích đúng
            state = retrieval_worker_node(state)
            state = policy_tool_worker_node(state)

        else:
            # Default: retrieval_worker
            state = retrieval_worker_node(state)

        # Step 3: Always synthesize
        state = synthesis_worker_node(state)

        state["latency_ms"] = int((time.time() - start) * 1000)
        state["history"].append(f"[graph] completed in {state['latency_ms']}ms")
        return state

    return run


# ─────────────────────────────────────────────
# 7. Public API
# ─────────────────────────────────────────────

_graph = build_graph()


def run_graph(task: str) -> AgentState:
    """
    Entry point: nhận câu hỏi, trả về AgentState với full trace.

    Args:
        task: Câu hỏi từ user

    Returns:
        AgentState với final_answer, trace, routing info, v.v.
    """
    state = make_initial_state(task)
    result = _graph(state)
    return result


def save_trace(state: AgentState, output_dir: str = "./artifacts/traces") -> str:
    """Lưu trace ra file JSON."""
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{output_dir}/{state['run_id']}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    return filename


# ─────────────────────────────────────────────
# 8. Manual Test
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("Day 09 Lab — Supervisor-Worker Graph")
    print("=" * 60)

    test_queries = [
        "SLA xử lý ticket P1 là bao lâu?",
        "Khách hàng Flash Sale yêu cầu hoàn tiền vì sản phẩm lỗi — được không?",
        "Cần cấp quyền Level 3 để khắc phục P1 khẩn cấp. Quy trình là gì?",
        "Gặp lỗi ERR-5520 lúc 2am, không rõ nguyên nhân, ảnh hưởng toàn hệ thống.",
        "Nhân viên xin nghỉ phép năm còn lại bao nhiêu ngày?",
    ]

    for query in test_queries:
        print(f"\n▶ Query: {query}")
        result = run_graph(query)
        print(f"  Route   : {result['supervisor_route']}")
        print(f"  Reason  : {result['route_reason']}")
        print(f"  Risk    : {result['risk_high']} | needs_tool={result['needs_tool']}")
        print(f"  Workers : {result['workers_called']}")
        answer = result['final_answer']
        print(f"  Answer  : {answer[:120]}{'...' if len(answer) > 120 else ''}")
        print(f"  Confidence: {result['confidence']}")
        print(f"  Latency : {result['latency_ms']}ms")

        trace_file = save_trace(result)
        print(f"  Trace saved → {trace_file}")

    print("\n✅ graph.py test complete.")
