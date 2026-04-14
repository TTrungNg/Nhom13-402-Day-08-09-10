"""
mcp_server.py — Real MCP Server (Bonus)
Sprint 3: Implement real MCP tools using FastMCP.

Mô phỏng MCP (Model Context Protocol) interface.
Agent (MCP client) gọi qua giao thức MCP thay vì import trực tiếp.
"""

import os
import sys
from datetime import datetime
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("Internal-Tools-Server")

# ─────────────────────────────────────────────
# Helper: Import retrieval logic
# ─────────────────────────────────────────────
def get_retrieval_logic():
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        from workers.retrieval import retrieve_dense
        return retrieve_dense
    except ImportError:
        return None

# ─────────────────────────────────────────────
# Tool Implementations
# ─────────────────────────────────────────────

@mcp.tool()
def search_kb(query: str, top_k: int = 3) -> dict:
    """
    Tìm kiếm Knowledge Base bằng semantic search (ChromaDB).
    Trả về top-k chunks liên quan nhất.
    """
    retrieve_dense = get_retrieval_logic()
    if retrieve_dense:
        try:
            chunks = retrieve_dense(query, top_k=top_k)
            sources = list({c["source"] for c in chunks})
            return {
                "chunks": chunks,
                "sources": sources,
                "total_found": len(chunks),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
             return {"error": f"ChromaDB query failed: {e}"}
    
    # Fallback mock data
    return {
        "chunks": [
            {
                "text": f"[MOCK] Kết quả tìm kiếm cho: {query}",
                "source": "mock_policy.txt",
                "score": 0.95
            }
        ],
        "sources": ["mock_policy.txt"],
        "total_found": 1,
        "timestamp": datetime.now().isoformat()
    }

# Mock ticket database
MOCK_TICKETS = {
    "P1-LATEST": {
        "ticket_id": "IT-9847",
        "priority": "P1",
        "title": "API Gateway down — toàn bộ người dùng không đăng nhập được",
        "status": "in_progress",
        "assignee": "nguyen.van.a@company.internal",
        "created_at": "2026-04-13T22:47:00",
        "sla_deadline": "2026-04-14T02:47:00",
    },
    "IT-1234": {
        "ticket_id": "IT-1234",
        "priority": "P2",
        "title": "Feature login chậm cho một số user",
        "status": "open",
        "assignee": None,
        "created_at": "2026-04-13T09:15:00",
        "sla_deadline": "2026-04-14T09:15:00",
    },
}

@mcp.tool()
def get_ticket_info(ticket_id: str) -> dict:
    """
    Tra cứu thông tin ticket từ hệ thống Jira nội bộ.
    """
    ticket = MOCK_TICKETS.get(ticket_id.upper())
    if ticket:
        ticket["timestamp"] = datetime.now().isoformat()
        return ticket
    return {
        "error": f"Ticket '{ticket_id}' không tìm thấy.",
        "available_mock_ids": list(MOCK_TICKETS.keys()),
        "timestamp": datetime.now().isoformat()
    }

@mcp.tool()
def check_access_permission(access_level: int, requester_role: str, is_emergency: bool = False) -> dict:
    """
    Kiểm tra điều kiện cấp quyền truy cập theo Access Control SOP.
    """
    # Simple logic for demo
    can_grant = False
    if access_level <= 1:
        can_grant = True
    elif access_level == 2 and requester_role in ["admin", "manager"]:
        can_grant = True
    elif is_emergency:
        can_grant = True

    return {
        "access_level": access_level,
        "can_grant": can_grant,
        "requester_role": requester_role,
        "is_emergency": is_emergency,
        "source": "access_control_sop.txt",
        "timestamp": datetime.now().isoformat()
    }

@mcp.tool()
def create_ticket(priority: str, title: str, description: str = "") -> dict:
    """
    Tạo ticket mới trong hệ thống Jira (MOCK).
    """
    mock_id = f"IT-{9900 + hash(title) % 100}"
    return {
        "ticket_id": mock_id,
        "status": "created",
        "priority": priority,
        "title": title,
        "url": f"https://jira.company.internal/browse/{mock_id}",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    # When run directly, start the server
    # Default transport is stdio
    mcp.run()
