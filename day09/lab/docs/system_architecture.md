# System Architecture — Lab Day 09

**Nhóm:** 13 - E402  
**Ngày:** 14/04/2026  
**Version:** 1.0

---

## 1. Tổng quan kiến trúc

> Mô tả ngắn hệ thống của nhóm: chọn pattern gì, gồm những thành phần nào.

**Pattern đã chọn:** Supervisor-Worker  
**Lý do chọn pattern này (thay vì single agent):**

> Tách nhiệm vụ rõ ràng, dễ mở rộng và debug hơn single-agent, đồng thời hỗ trợ tool integration và tracing tốt hơn.
---

## 2. Sơ đồ Pipeline

**Sơ đồ thực tế của nhóm:**

``` mermaid
graph LR
    %% Luồng chính
    Input([User Input]) --> Supervisor{<b>Supervisor Node</b><br/>Keyword & Risk Analysis}

    %% Quyết định của Supervisor
    Supervisor -- "Normal FAQ" --> Retrieval[Retrieval Worker<br/>ChromaDB]
    Supervisor -- "Policy/Tool Need" --> Policy[Policy & Tool Worker<br/>MCP Server Integration]
    Supervisor -- "Unknown/High Risk" --> HITL[Human Review Node<br/>HITL Placeholder]

    %% Kết nối logic
    HITL --> Retrieval
    Policy --> Synthesis
    Retrieval --> Synthesis

    %% Đầu ra
    Synthesis[Synthesis Worker<br/>LLM Response Gen] --> Output([Final Answer + Trace JSON])

    %% Chú thích
    subgraph Workers Layer
        Retrieval
        Policy
        HITL
    end
```

---

## 3. Vai trò từng thành phần

### Supervisor (`graph.py`)

| Thuộc tính | Mô tả |
|-----------|-------|
| **Nhiệm vụ** | Phân tích input từ user để quyết định route đến worker phù hợp, đồng thời đánh giá risk và nhu cầu sử dụng tool |
| **Input** | task (câu hỏi từ user) + context trong AgentState |
| **Output** | supervisor_route, route_reason, risk_high, needs_tool |
| **Routing logic** | Rule-based keyword matching |
| **HITL condition** | risk_high = True và phát hiện error code |

### Retrieval Worker (`workers/retrieval.py`)

| Thuộc tính | Mô tả |
|-----------|-------|
| **Nhiệm vụ** | Thực hiện dense retrieval, truy vấn ChromaDB và trả về top-k chunks liên quan cùng nguồn |
| **Embedding model** | OpenAI text-embedding-3-small |
| **Top-k** | 3 |
| **Stateless?** | Yes |

### Policy Tool Worker (`workers/policy_tool.py`)

| Thuộc tính | Mô tả |
|-----------|-------|
| **Nhiệm vụ** | Phân tích policy dựa trên context, xác định policy có áp dụng hay không, đồng thời gọi MCP tools khi cần |
| **MCP tools gọi** | `search_kb`, `get_ticket_info` |
| **Exception cases xử lý** | Flash Sale, sản phẩm kỹ thuật số (license/subscription), sản phẩm đã kích hoạt, đơn hàng trước 01/02/2026 (policy v3) |

### Synthesis Worker (`workers/synthesis.py`)

| Thuộc tính | Mô tả |
|-----------|-------|
| **LLM model** | gpt-4o-mini |
| **Temperature** | 0.1 |
| **Grounding strategy** | Context injection + strict system prompt |
| **Abstain condition** | Khi không có hoặc không đủ context |

### MCP Server (`mcp_server.py`)

| Tool | Input | Output |
|------|-------|--------|
| search_kb | query, top_k | chunks, sources |
| get_ticket_info | ticket_id | ticket details |
| check_access_permission | access_level, requester_role | can_grant, approvers |
| create_ticket | priority, title, description | ticket_id, url, created_at |

---

## 4. Shared State Schema

> Liệt kê các fields trong AgentState và ý nghĩa của từng field.

| Field             | Type          | Mô tả                             | Ai đọc/ghi                     |
| ----------------- | ------------- | --------------------------------- | ------------------------------ |
| task              | str           | Câu hỏi đầu vào                   | supervisor đọc                 |
| supervisor_route  | str           | Worker được chọn                  | supervisor ghi                 |
| route_reason      | str           | Lý do route                       | supervisor ghi                 |
| risk_high         | bool          | Có cần human review không         | supervisor ghi                 |
| needs_tool        | bool          | Có cần gọi MCP tool không         | supervisor ghi                 |
| hitl_triggered    | bool          | Đã trigger Human-in-the-loop chưa | supervisor ghi / system ghi    |
| retrieved_chunks  | list          | Evidence từ retrieval             | retrieval ghi, synthesis đọc   |
| retrieved_sources | list          | Nguồn tài liệu từ retrieval       | retrieval ghi, synthesis đọc   |
| policy_result     | dict          | Kết quả kiểm tra policy           | policy_tool ghi, synthesis đọc |
| mcp_tools_used    | list          | Tool calls đã thực hiện           | policy_tool ghi                |
| final_answer      | str           | Câu trả lời cuối                  | synthesis ghi                  |
| sources           | list          | Sources được cite trong answer    | synthesis ghi                  |
| confidence        | float         | Mức tin cậy                       | synthesis ghi                  |
| history           | list          | Log chi tiết các bước (trace)     | tất cả workers ghi             |
| workers_called    | list          | Danh sách worker đã chạy          | system / supervisor ghi        |
| latency_ms        | Optional[int] | Thời gian xử lý                   | system ghi                     |
| run_id            | str           | ID của request/run                | system ghi                     |


---

## 5. Lý do chọn Supervisor-Worker so với Single Agent (Day 08)

| Tiêu chí | Single Agent (Day 08) | Supervisor-Worker (Day 09) |
|----------|----------------------|--------------------------|
| Debug khi sai | Khó — không rõ lỗi ở đâu | Dễ hơn — test từng worker độc lập |
| Thêm capability mới | Phải sửa toàn prompt | Thêm worker/MCP tool riêng |
| Routing visibility | Không có | Có route_reason trong trace |
| Scalability | Khó scale khi logic phức tạp | Dễ mở rộng nhiều worker chuyên biệt |
| Reliability | Dễ hallucinate do god agent | Giảm lỗi nhờ tách nhiệm vụ + grounding |

**Nhóm điền thêm quan sát từ thực tế lab:**

Supervisor-Worker giúp tách biệt rõ ràng các bước reasoning, giảm coupling giữa các thành phần và tăng khả năng kiểm soát, debug và mở rộng hệ thống so với kiến trúc single-agent.

---

## 6. Giới hạn và điểm cần cải tiến

> Nhóm mô tả những điểm hạn chế của kiến trúc hiện tại.

1. Routing còn rule-based, chưa tối ưu
2. Chưa có cơ chế retry / error handling mạnh
3. Chưa tối ưu latency
