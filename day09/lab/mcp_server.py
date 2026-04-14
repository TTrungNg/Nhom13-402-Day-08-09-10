"""
mcp_server.py — Real MCP Server (Advanced/Bonus)
Sprint 3: Implement real MCP tools using FastMCP.
"""

import os
import sys
import json
from datetime import datetime
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("Internal-Tools-Server")

# Cache for retrieval logic to avoid re-loading models
_cached_retrieval = None

def get_retrieval_logic():
    global _cached_retrieval
    if _cached_retrieval is None:
        try:
            # Set up path to import from workers
            root_path = os.path.dirname(os.path.abspath(__file__))
            if root_path not in sys.path:
                sys.path.insert(0, root_path)
            from workers.retrieval import retrieve_dense
            _cached_retrieval = retrieve_dense
        except Exception:
            return None
    return _cached_retrieval

# ─────────────────────────────────────────────
# Tools
# ─────────────────────────────────────────────

@mcp.tool()
def search_kb(query: str, top_k: int = 3) -> dict:
    """
    Tìm kiếm Knowledge Base bằng semantic search (ChromaDB).
    Trả về top-k chunks liên quan nhất.
    """
    logic = get_retrieval_logic()
    if logic:
        try:
            chunks = logic(query, top_k=top_k)
            sources = list({c["source"] for c in chunks})
            return {
                "chunks": chunks,
                "sources": sources,
                "total_found": len(chunks),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
    
    return {
        "error": "Retrieval logic could not be initialized.",
        "timestamp": datetime.now().isoformat()
    }

@mcp.tool()
def get_ticket_info(ticket_id: str) -> dict:
    """
    Tra cứu thông tin ticket từ hệ thống Jira nội bộ.
    """
    mock_db = {
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
    ticket = mock_db.get(ticket_id.upper())
    if ticket:
        res = ticket.copy()
        res["timestamp"] = datetime.now().isoformat()
        return res
    return {
        "error": f"Ticket '{ticket_id}' không tìm thấy.",
        "timestamp": datetime.now().isoformat()
    }

@mcp.tool()
def check_access_permission(access_level: int, requester_role: str, is_emergency: bool = False) -> dict:
    """
    Kiểm tra điều kiện cấp quyền truy cập theo Access Control SOP.
    """
    can_grant = False
    if access_level <= 1:
        can_grant = True
    elif access_level == 2 and (requester_role in ["admin", "manager"] or is_emergency):
        can_grant = True
    elif access_level == 3 and requester_role == "admin":
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
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    mcp.run()
