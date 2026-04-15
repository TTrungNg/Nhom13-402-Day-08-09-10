# Báo Cáo Nhóm — Lab Day 09: Multi-Agent Orchestration

**Tên nhóm:** Nhóm 13
**Thành viên:**
| Tên | Vai trò | Email |
|-----|---------|-------|
| Nguyễn Việt Trung | Supervisor Owner | trungtomng@gmail.com |
| Trần Ngô Hồng Hà | Worker Owner | bgohonghatran@gmail.com |
| Hà Việt Khánh | MCP Owner | ___ |
| Mã Khoa Học | MCP Owner | tunglamle132@gmail.com |
| Nguyễn Tuấn Kiệt | Trace Owner | junsikkun@gmail.com |
| Nguyễn Hữu Nam | Documentation Owner | 26ai.namnh@vinuni.edu.vn |

**Ngày nộp:** 15/04/2026  
**Repo:** https://github.com/TTrungNg/Nhom13-402-Day-08-09-10

**Độ dài khuyến nghị:** 600–1000 từ

---

> **Hướng dẫn nộp group report:**
> 
> - File này nộp tại: `reports/group_report.md`
> - Deadline: Được phép commit **sau 18:00** (xem SCORING.md)
> - Tập trung vào **quyết định kỹ thuật cấp nhóm** — không trùng lặp với individual reports
> - Phải có **bằng chứng từ code/trace** — không mô tả chung chung
> - Mỗi mục phải có ít nhất 1 ví dụ cụ thể từ code hoặc trace thực tế của nhóm

---

## 1. Kiến trúc nhóm đã xây dựng (150–200 từ)

**Hệ thống tổng quan:**

Hệ thống được thiết kế theo mô hình Multi-Agent, điều phối qua một "bộ não" trung tâm là `Supervisor` (trong `graph.py`). Trạng thái vòng đời truy vấn được lưu trong đối tượng `AgentState`, giúp duy trì context (chunks, tool results, history) bền vững qua từng node xử lý. Hệ thống bao gồm các tác nhân chuyên biệt: `retrieval_worker` lấy context RAG, `policy_tool_worker` tích hợp tool để đánh giá chính sách/quy trình, và `synthesis_worker` tổng hợp đáp án rà soát ảo giác. Sự phân tách module hóa mạnh này (theo như `eval_report.json` xác nhận) cho phép gọi external Tool rành mạch qua MCP mà không làm rối tung core logic RAG.

**Routing logic cốt lõi:**
Logic định tuyến (Router) chuyển sang hướng Deterministic (Rule-based) thay vì xử lý Model Classification. Nó vận hành bằng: **Regex-based Error Detection** (ví dụ: `ERR-\w+`) để bắt exception chọc thẳng qua Human Review (HITL rate 6%). Ngược lại, điều hướng thường diễn ra qua thuật toán **Keywords Matching** (`_POLICY_KEYWORDS`, `_RETRIEVAL_KEYWORDS`). Bằng chứng từ file trace, logic này đem lại "Routing visibility rất rõ ràng", phân bố tới 66% (10/15 test) chọc đúng về `policy_tool_worker`.

**MCP tools đã tích hợp:**
- `search_kb`: Truy vấn trực tiếp vector store (ChromaDB) đặt hẳn trong lòng MCP Server. Thực hiện normalize khoảng cách vector (`_distance_to_score`) thành một tool mượt mà thay vì ôm cứng vào script client.
- `get_ticket_info`: Phục vụ lấy metadata tĩnh SLA của ticket lỗi, móc nối dữ liệu trong policy flow (Ví dụ gq01 gọi tool `get_ticket_info` thành công sau khi khập keyword "ticket").

---

## 2. Quyết định kỹ thuật quan trọng nhất (200–250 từ)

**Quyết định:** Sử dụng Regex và Keyword-based Routing tại Supervisor để thay thế hoàn toàn cho LLM Classification.

**Bối cảnh vấn đề:**
Hệ thống cần phân biệt câu hỏi "Sự cố, P1, rủi ro khẩn" với một "FAQ nghiệp vụ công ty thông thường" để tách luồng cho tool đánh giá hiệu quả. Rõ ràng, một framework Agent mạnh cần quyết định Routing rất nhanh tại trạm biên (Supervisor).

**Các phương án đã cân nhắc:**

| Phương án | Ưu điểm | Nhược điểm |
|-----------|---------|-----------|
| Dùng LLM Router (Classifier) | Phân loại linh hoạt, xử lý được truy vấn mơ hồ. | Overhead quá cao về token và latency. Phán đoán đôi khi dao động (non-deterministic). |
| Regex & Keyword Routing | Độ trễ routing bằng `0ms`. Cự kì minh bạch qua dấu vết `route_reason` khi debug trace. | Routing bị máy móc, dễ chệch hướng nếu từ khóa của Tool trùng lắp ngữ cảnh General Retrieval. |

**Phương án đã chọn và lý do:**
Nhóm ngả về lựa chọn số 2 (Regex + Keyword). Theo `eval_report.json`, đây là điểm mạnh của hệ thống: *"Day 09 có route_reason cho từng câu → hiểu rõ tại sao AI chọn luồng đó."*, giúp chẩn đoán nguyên nhân câu gq01 fail rất dễ chứ không như một hộp đen của LLM Classifier. Với domain IT chuyên trách, keyword dict là đủ sức đáp ứng và tối giản hóa thiết kế phân luồng.

**Bằng chứng từ trace/code:**

```json
# Trace lấy trong vòng đời của grading_run.jsonl (câu gq01):
"supervisor_route": "policy_tool_worker",
"route_reason": "MCP tool keywords detected: ticket",
"mcp_tools_used": ["get_ticket_info"]
```

---

## 3. Kết quả grading questions (150–200 từ)

Phiên test hệ thống tại file `grading_run.jsonl` thu được các quan sát kĩ thuật vượt trội lẫn những hệ luỵ bất thình lình về mặt ngữ cảnh nâng cao: 

**Tổng điểm raw ước tính:** Ghi nhận khoảng ~78/96 điểm. Hệ thống Pass 100% các câu hỏi Retrieval căn bản (`gq03, gq04, gq05...`) nhưng vấp lỗi context ở câu `gq02`, `gq01` và `gq09`. 

**Câu pipeline xử lý tốt nhất:**
- ID: **gq07** (Hỏi mức phạt SLA khi vi phạm 4 giờ trễ). 
  Lý do tốt: Đây là bài test Anti-hallucination. Agent đã Abstain triệt để: *"Không đủ thông tin trong tài liệu nội bộ"*. Thuật toán LLM-As-A-Judge chấm độ tin cậy xuống chỉ còn `Confidence: 0.3`.
- ID: **gq10** (Hoàn tiền cho Flash Sale bị hỏng). Đủ năng lực phát hiện Override Policy (Lỗi NSX nhưng hàng Flash sale thì theo Rule là cấm đụng).

**Câu pipeline fail hoặc partial:**
- ID: **gq02** (Quy chiếu mốc thời gian của Policy - Temporal Policy). Lấy điều kiện policy trước 1/2/2026.  
  Fail ở đâu: Agent kết luận "Có hoàn tiền" nhưng không nhận thức được việc User mua ở mốc thời gian thuộc v3 Policy.  
  Root cause: Không có Worker nhận thức "Temporal Scoping". Retrieval đâm đầu đẩy chunk của version v4.
- ID: **gq01, gq09**: Trả lời sót ngách Notification Channel "PagerDuty", và nhận dạng sai Approval Rule. Trừ điểm nặng tại `grading_criteria` đa thành phần (multi-hop rác).

**Câu gq07 (abstain):** Nhóm xử lý thế nào?
Từ `grading_run.jsonl`, `route_reason` chĩa vào `retrieval_worker`, gắp chunks -> `synthesis_worker` (báo confidence 0.3) -> Phát ngôn Abstain tự nhiên mà không cần chặn Exception.

**Câu gq09 (multi-hop khó nhất):** Trace ghi được 2 workers không? Kết quả thế nào?
Có! Bất chấp test multi-hop khó 16 điểm, `grading_run.jsonl` ghi nhận cụm: `workers_called: ["retrieval_worker", "policy_tool_worker", "synthesis_worker"]` đồng thời gọi tool `"get_ticket_info"`. Điều này chứng tỏ Supervisor nối context node rẽ nhánh xuất sắc, không hề đánh rơi "retrieval chunk" khi điều chuyển luồng.

---

## 4. So sánh Day 08 vs Day 09 — Điều nhóm quan sát được (150–200 từ)

**Metric thay đổi rõ nhất (có số liệu):**
Báo cáo lưu vết `eval_report.json` phản ánh rõ 2 luồng phản ứng trái ngược:
1. **Confidence Trung bình** có mức bùng nổ lên **0.617** nhờ cơ cấu LLM chấm chéo, đẩy `Multi-hop Accuracy` và `Abstain Rate` lên mức ổn định hơn Day 08.
2. Tuy nhiên **Latency trung bình vọt lên tận 4609ms (+207.3%)** so với mốc Single Agent 1500m/s khi xưa. Sự đánh đổi giữa bảo an (Tránh Halucination) và tốc độ vận hành là vô cùng đắt.

**Điều nhóm bất ngờ nhất khi chuyển từ single sang multi-agent:**
Khả năng "Debuggability" cô lập lỗi của Graph (Isolate). Khi một Agent gục, ta biết rõ nó gục ở "Policy Worker" hay "Retrieval". Hơn nữa, việc móc nối thêm API mở (Tool) cũng không phá vỡ vòng đời RAG lõi.

**Trường hợp multi-agent KHÔNG giúp ích hoặc làm chậm hệ thống:**
Sự mù quáng của hard-keyword routing! Điển hình ở câu `gq01`: Latency lên rát mức **8672ms!!!**. Do có chữ "ticket", query bị ngáng sang `policy_tool_worker` thừa thãi rồi mới tổng hợp đáp án thay vì đi 1 shot `retrieval` đơn giản.

---

## 5. Phân công và đánh giá nhóm (100–150 từ)

**Phân công thực tế:**

| Thành viên | Phần đã làm | Sprint |
|------------|-------------|--------|
| Nguyễn Việt Trung | Xây dựng pipeline `graph.py` tổng, Routing strategy, xử lý state bugs. | 1 |
| Trần Ngô Hồng Hà | Triển khai workers (`retrieval`, `policy_tool`, `synthesis`) & logic Rule exception. | 2 |
| Hà Việt Khánh | Thiết kế `AgentState` workflow tổng hợp, fix luân chuyển payload State. | 3 |
| Mã Khoa Học | Xây dựng `mcp_server.py`, tích hợp Vector query (ChromaDB) trong tool, JSON Schema validation. | 3 |
| Nguyễn Tuấn Kiệt | Kiến trúc Eval-Tracing, xuất jsonl metrics, đối chiếu Score Data. | 4 |
| Nguyễn Hữu Nam | Tập hợp báo cáo và tài liệu, hoàn thiện `routing_decisions.md`; `single_vs_multi_comparison.md` và `system_architecture.md` | 4 |


**Điều nhóm làm tốt:**
Debuggability cực tốt dựa vào `route_reason` và `workers_called` log. Thiết kế phân mảnh MCP đảm bảo việc add thêm tool IT hoàn toàn độc lập, chập nối theo JSON chuẩn mực.

**Điều nhóm làm chưa tốt hoặc gặp vấn đề về phối hợp:**
Nghẽn nhịp độ (Bottleneck) khi làm việc: Nhóm front (Workers) khựng lại khá nặng vào Sprint đầu lúc chờ AgentState pipeline `graph.py` định hình. 

**Nếu làm lại, nhóm sẽ thay đổi gì trong cách tổ chức?**
Khai báo cấu trúc Mocking Contract 100% trước khi chia nhau dev, để hai nhóm routing nhánh và nhánh logic tools xử lý song hành.

---

## 6. Nếu có thêm 1 ngày, nhóm sẽ làm gì? (50–100 từ)

1. **Routing thông minh hơn (Score-based)**: Ở bản cập nhật sau, Supervisor sẽ không cắm luồng qua 1 check `policy matched` boolean. Chấm điểm Weighted Tfidf (1-10) sẽ loại bỏ triệt để nhược điểm *8000ms delay* vì định tuyến thừa worker. 
2. **Triển khai Temporal Context Scope**: Ở mảng Retrieve, xử lý lỗi Abstain version quá cũ như test case `gq02`. Nếu database chỉ có v4 policy, RAG Worker phải phát hiện metadata `Version V.3` của query để né tránh việc chập thông tin mốc thời gian. 

---

*File này lưu tại: `reports/group_report.md`*  
*Commit sau 18:00 được phép theo SCORING.md*
