# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Nguyễn Hữu Nam  
**Vai trò trong nhóm:** Docs Owner  
**Ngày nộp:** 14/04/2026  
**Độ dài yêu cầu:** 500–800 từ

---

> **Lưu ý quan trọng:**
> - Viết ở ngôi **"tôi"**, gắn với chi tiết thật của phần bạn làm
> - Phải có **bằng chứng cụ thể**: tên file, đoạn code, kết quả trace, hoặc commit
> - Nội dung phân tích phải khác hoàn toàn với các thành viên trong nhóm
> - Deadline: Được commit **sau 18:00** (xem SCORING.md)
> - Lưu file với tên: `reports/individual/[ten_ban].md` (VD: `nguyen_van_a.md`)

---

## 1. Tôi phụ trách phần nào? (100–150 từ)

> Mô tả cụ thể module, worker, contract, hoặc phần trace bạn trực tiếp làm.
> Không chỉ nói "tôi làm Sprint X" — nói rõ file nào, function nào, quyết định nào.

**Module/file tôi chịu trách nhiệm:**
- File chính: `day09/lab/docs`
- Functions tôi implement: Document của System architecture, Routing decisions, Single vs Multi comparison

**Cách công việc của tôi kết nối với phần của thành viên khác:**

Phần tôi phụ trách tập trung vào việc xây dựng tài liệu cho hệ thống, bao gồm mô tả kiến trúc tổng thể, luồng routing giữa các worker và so sánh giữa single-agent và multi-agent. Công việc này đóng vai trò như một “cầu nối” giúp các thành viên khác hiểu rõ cách các module của họ tương tác với nhau, đặc biệt là giữa supervisor và các worker như retrieval hay policy tool.

Tôi thường phải trao đổi với các bạn phụ trách code để đảm bảo tài liệu phản ánh đúng implementation thực tế, đồng thời chuẩn hóa lại các quyết định thiết kế để nhóm có thể thống nhất cách hiểu. Nhờ đó, phần docs giúp giảm hiểu nhầm và hỗ trợ việc debug, review cũng như trình bày hệ thống sau này.

**Bằng chứng (commit hash, file có comment tên bạn, v.v.):**

f111154d1223819164ac6c5550e0323a796412ee

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (150–200 từ)

> Chọn **1 quyết định** bạn trực tiếp đề xuất hoặc implement trong phần mình phụ trách.
> Giải thích:
> - Quyết định là gì?
> - Các lựa chọn thay thế là gì?
> - Tại sao bạn chọn cách này?
> - Bằng chứng từ code/trace cho thấy quyết định này có effect gì?

**Quyết định:** Sử dụng keyword-based matching trong `supervisor_node` để quyết định khi nào cần gọi MCP tool.

**Ví dụ:**
> "Tôi chọn dùng keyword-based routing trong supervisor_node thay vì gọi LLM để classify.
>  Lý do: keyword routing nhanh hơn (~5ms vs ~800ms) và đủ chính xác cho 5 categories.
>  Bằng chứng: trace gq01 route_reason='task contains P1 SLA keyword', latency=45ms."

**Lý do:**

Trong quá trình thực nghiệm, agent ban đầu gần như không gọi MCP tool dù câu hỏi có liên quan đến các thực thể như “ticket” hoặc “SLA”. Điều này cho thấy việc dựa hoàn toàn vào LLM reasoning trong routing chưa đủ ổn định. Vì vậy, tôi đề xuất bổ sung một lớp rule-based đơn giản dựa trên keyword để đảm bảo các trường hợp rõ ràng sẽ được route đúng sang policy_tool_worker và kích hoạt tool tương ứng.

**Trade-off đã chấp nhận:**

Cách tiếp cận này làm tăng nguy cơ misrouting, đặc biệt với các câu hỏi chỉ mang tính tra cứu tĩnh nhưng vẫn chứa keyword (ví dụ “ticket”), dẫn đến việc gọi tool không cần thiết và tăng latency.

**Bằng chứng từ trace/code:**
`day09/lab/artifacts/traces/run_20260414_164517.json`
```
{
  "task": "SLA xử lý ticket P1 là bao lâu?",
  "route_reason": "MCP tool keywords detected: ticket",
  "risk_high": false,
  "needs_tool": true,
  "hitl_triggered": false,
  "retrieved_chunks": [
    {
      "text": "P1 — CRITICAL (Khẩn cấp):\nĐịnh nghĩa: Sự cố ảnh hưởng toàn bộ hệ thống production, không có workaround.\nVí dụ: Database sập, API gateway down, toàn bộ người dùng không thể đăng nhập.\n\nTicket P1:\n- Phản hồi ban đầu (first response): 15 phút kể từ khi ticket được tạo.\n- Xử lý và khắc phục (resolution): 4 giờ.\n- Escalation: Tự động escalate lên Senior Engineer nếu không có phản hồi trong 10 phút.\n- Thông báo stakeholder: Ngay khi nhận ticket, update mỗi 30 phút cho đến khi resolve.",
      "metadata": {
        "source": "support/sla-p1-2026.pdf",
        "chunk_type": "Priority-Group",
        "section_title": "P1 Info",
        "language": "vi",
        "effective_date": "2026-01-15",
        "total_chunks": 6,
        "access_level": "internal",
        "access": "internal",
        "char_count": 483,
        "department": "IT",
        "doc_id": "sla_p1_2026",
        "chunk_id": "sla_p1_2026_c00",
        "next_chunk_id": "sla_p1_2026_c01",
        "version": "v1.0",
        "chunk_index": 0
      },
      "score": 0.5972788333892822
    },
    {
      "text": "Context SLA P1:\n- Escalation: Tự động escalate lên Senior Engineer nếu không có phản hồi trong 10 phút.\n- Thông báo stakeholder: Ngay khi nhận ticket, update mỗi 30 phút cho đến khi resolve.\n\nQuy trình:\nBước 1: Tiếp nhận\nOn-call engineer nhận alert hoặc ticket, xác nhận severity trong 5 phút.\n\nBước 2: Thông báo\nGửi thông báo tới Slack #incident-p1 và email incident@company.internal ngay lập tức.\n\nBước 3: Triage và phân công\nLead Engineer phân công engineer xử lý trong 10 phút.\n\nBước 4: Xử lý\nEngineer cập nhật tiến độ lên ticket mỗi 30 phút. Nếu cần hỗ trợ thêm, escalate ngay.\n\nBước 5: Resolution\nSau khi khắc phục, viết incident report trong vòng 24 giờ.",
      "metadata": {
        "char_count": 661,
        "section_title": "Quy trình P1",
        "chunk_type": "Process",
        "chunk_id": "sla_p1_2026_c03",
        "next_chunk_id": "sla_p1_2026_c04",
        "version": "v1.0",
        "source": "support/sla-p1-2026.pdf",
        "department": "IT",
        "overlap_with": "P1 Info",
        "access": "internal",
        "doc_id": "sla_p1_2026",
        "chunk_index": 3,
        "access_level": "internal",
        "prev_chunk_id": "sla_p1_2026_c02",
        "effective_date": "2026-01-15",
        "language": "vi",
        "total_chunks": 6
      },
      "score": 0.5740603804588318
    },
    {
      "text": "P3 — MEDIUM (Trung bình):\nĐịnh nghĩa: Lỗi ảnh hưởng không đáng kể, người dùng vẫn làm việc được.\nP4 — LOW (Thấp):\nĐịnh nghĩa: Yêu cầu cải tiến, gợi ý, hoặc lỗi giao diện nhỏ.\n\nTicket P3:\n- Phản hồi ban đầu: 1 ngày làm việc.\n- Xử lý và khắc phục: 5 ngày làm việc.\nTicket P4:\n- Phản hồi ban đầu: 3 ngày làm việc.\n- Xử lý và khắc phục: Theo sprint cycle (thông thường 2-4 tuần).",
      "metadata": {
        "department": "IT",
        "access": "internal",
        "section_title": "P3/P4 Info",
        "prev_chunk_id": "sla_p1_2026_c01",
        "doc_id": "sla_p1_2026",
        "chunk_id": "sla_p1_2026_c02",
        "effective_date": "2026-01-15",
        "chunk_index": 2,
        "source": "support/sla-p1-2026.pdf",
        "chunk_type": "Priority-Group",
        "next_chunk_id": "sla_p1_2026_c03",
        "total_chunks": 6,
        "access_level": "internal",
        "language": "vi",
        "char_count": 375,
        "version": "v1.0"
      },
      "score": 0.5719126462936401
    }
  ],
  "retrieved_sources": [
    "support/sla-p1-2026.pdf"
  ],
  "policy_result": {
    "policy_applies": true,
    "policy_name": "refund_policy_v4",
    "exceptions_found": [],
    "source": [
      "unknown"
    ],
    "policy_version_note": "",
    "explanation": "Analyze using rule-based checks based on task and retrieved chunks. Exceptions are identified if certain keywords are present in either the task or the context chunks."
  },
  "mcp_tools_used": [
    {
      "tool": "get_ticket_info",
      "input": {
        "ticket_id": "P1-LATEST"
      },
      "output": {
        "ticket_id": "IT-9847",
        "priority": "P1",
        "title": "API Gateway down — toàn bộ người dùng không đăng nhập được",
        "status": "in_progress",
        "assignee": "nguyen.van.a@company.internal",
        "created_at": "2026-04-13T22:47:00",
        "sla_deadline": "2026-04-14T02:47:00",
        "escalated": true,
        "escalated_to": "senior_engineer_team",
        "notifications_sent": [
          "slack:#incident-p1",
          "email:incident@company.internal",
          "pagerduty:oncall"
        ]
      },
      "error": null,
      "timestamp": "2026-04-14T16:45:19.316979"
    }
  ],
  "final_answer": "SLA xử lý ticket P1 là như sau:\n\n1. **Phản hồi ban đầu (first response)**: 15 phút kể từ khi ticket được tạo.\n2. **Xử lý và khắc phục (resolution)**: 4 giờ.\n3. **Escalation**: Tự động escalate lên Senior Engineer nếu không có phản hồi trong 10 phút.\n4. **Thông báo stakeholder**: Ngay khi nhận ticket, update mỗi 30 phút cho đến khi resolve. [1]",
  "sources": [
    "unknown"
  ],
  "confidence": 0.68,
  "history": [
    "[supervisor] received task: SLA xử lý ticket P1 là bao lâu?",
    "[supervisor] route=policy_tool_worker needs_tool=True risk_high=False reason=MCP tool keywords detected: ticket",
    "[retrieval_worker] called",
    "[retrieval_worker] retrieved 3 chunks from ['support/sla-p1-2026.pdf']",
    "[retrieval_worker] retrieved 3 chunks",
    "[policy_tool_worker] called",
    "[policy_tool_worker] called MCP get_ticket_info",
    "[policy_tool_worker] policy_applies=True, exceptions=0",
    "[policy_tool_worker] policy check complete",
    "[synthesis_worker] called",
    "[synthesis_worker] answer generated, confidence=0.68, sources=['unknown']",
    "[synthesis_worker] answer generated, confidence=0.68",
    "[graph] completed in 8501ms"
  ],
  "workers_called": [
    "retrieval_worker",
    "policy_tool_worker",
    "synthesis_worker"
  ],
  "supervisor_route": "policy_tool_worker",
  "latency_ms": 8501,
  "run_id": "run_20260414_164517",
  "worker_io_logs": [
    {
      "worker": "retrieval_worker",
      "input": {
        "task": "SLA xử lý ticket P1 là bao lâu?",
        "top_k": 3
      },
      "output": {
        "chunks_count": 3,
        "sources": [
          "support/sla-p1-2026.pdf"
        ]
      },
      "error": null
    },
    {
      "worker": "policy_tool_worker",
      "input": {
        "task": "SLA xử lý ticket P1 là bao lâu?",
        "chunks_count": 3,
        "needs_tool": true
      },
      "output": {
        "policy_applies": true,
        "exceptions_count": 0,
        "mcp_calls": 1
      },
      "error": null
    },
    {
      "worker": "synthesis_worker",
      "input": {
        "task": "SLA xử lý ticket P1 là bao lâu?",
        "chunks_count": 3,
        "has_policy": true
      },
      "output": {
        "answer_length": 345,
        "sources": [
          "unknown"
        ],
        "confidence": 0.68
      },
      "error": null
    }
  ],
  "question_id": "q01"
}
```

---

## 3. Tôi đã sửa một lỗi gì? (150–200 từ)

> Mô tả 1 bug thực tế bạn gặp và sửa được trong lab hôm nay.
> Phải có: mô tả lỗi, symptom, root cause, cách sửa, và bằng chứng trước/sau.

**Lỗi:** Agent không gọi MCP tool trong các câu hỏi rõ ràng cần dữ liệu từ hệ thống (ví dụ liên quan đến “ticket”, “SLA”).

**Symptom (pipeline làm gì sai?):**

Dù câu hỏi có chứa các từ khóa liên quan đến hệ thống vận hành, pipeline vẫn chỉ đi qua retrieval_worker và synthesis_worker, bỏ qua policy_tool_worker. Kết quả là câu trả lời thiếu thông tin động hoặc không đúng với expected behavior của system có tích hợp tool.

**Root cause (lỗi nằm ở đâu — indexing, routing, contract, worker logic?):**

Lỗi nằm ở routing logic trong supervisor_node. Supervisor phụ thuộc hoàn toàn vào LLM để quyết định route, nhưng prompt chưa đủ mạnh để trigger việc sử dụng tool, dẫn đến việc agent “ngại” gọi MCP.

**Cách sửa:**

Thêm keyword-based matching vào supervisor_node để detect các từ như “ticket”, “SLA” và ép route sang policy_tool_worker. Sau khi sửa, các câu hỏi phù hợp đã được route đúng và MCP tool được kích hoạt, thể hiện rõ trong trace.

---

## 4. Tôi tự đánh giá đóng góp của mình (100–150 từ)

> Trả lời trung thực — không phải để khen ngợi bản thân.

**Tôi làm tốt nhất ở điểm nào?**

Điểm mạnh nhất của tôi là viết và tổ chức tài liệu. Tôi có thể tổng hợp các ý tưởng rời rạc từ nhiều thành viên thành một bản mô tả rõ ràng, dễ hiểu và có cấu trúc. Điều này giúp cả nhóm có cái nhìn thống nhất về hệ thống thay vì mỗi người hiểu một kiểu.

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**

Tôi chưa đóng góp nhiều vào phần code, một phần do nhóm có khá đông thành viên nên việc phân chia task thiên về specialization. Điều này khiến tôi chưa nắm sâu implementation chi tiết như một số bạn khác.

**Nhóm phụ thuộc vào tôi ở đâu?** _(Phần nào của hệ thống bị block nếu tôi chưa xong?)_

Nhóm phụ thuộc vào phần tài liệu để hiểu tổng thể hệ thống. Nếu phần docs chưa hoàn thiện, việc review, debug hoặc trình bày solution sẽ bị chậm lại đáng kể.

**Phần tôi phụ thuộc vào thành viên khác:** _(Tôi cần gì từ ai để tiếp tục được?)_

Tôi phụ thuộc vào các bạn phụ trách code để nắm rõ logic implementation và cập nhật tài liệu cho đúng. Nếu code thay đổi mà không được communicate rõ, phần docs cũng dễ bị lệch so với thực tế.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50–100 từ)

> Nêu **đúng 1 cải tiến** với lý do có bằng chứng từ trace hoặc scorecard.
> Không phải "làm tốt hơn chung chung" — phải là:
> *"Tôi sẽ thử X vì trace của câu gq___ cho thấy Y."*

Tôi sẽ cải thiện logic gọi MCP tool bằng cách chuyển từ keyword-based sang hybrid (keyword + semantic). Trace cho thấy nhiều câu chỉ cần retrieval nhưng vẫn bị route do keyword “ticket”, gây gọi tool dư thừa. Vì vậy, cần thêm bước classify intent để giảm misroute.

---

*Lưu file này với tên: `reports/individual/[ten_ban].md`*  
*Ví dụ: `reports/individual/nguyen_van_a.md`*
