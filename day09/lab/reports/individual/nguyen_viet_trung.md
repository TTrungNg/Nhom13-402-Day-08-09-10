# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Nguyễn Việt Trung  
**Vai trò trong nhóm:** Supervisor Owner  
**Ngày nộp:** 14/04/2026  
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi phụ trách phần nào? (100–150 từ)

Trong lab này tôi đảm nhận vai trò **Supervisor Owner**, chịu trách nhiệm toàn bộ file `graph.py` — điểm vào duy nhất của pipeline và là bộ não điều phối toàn hệ thống.

**Module/file tôi chịu trách nhiệm:**

- File chính: `day09/lab/graph.py`
- Functions tôi implement: `supervisor_node()`, `human_review_node()`, `retrieval_worker_node()`, `policy_tool_worker_node()`, `synthesis_worker_node()`, `build_graph()`

Ngoài `graph.py`, tôi còn tham gia fix bug trực tiếp trong `workers/retrieval.py` (commit `ada0a3b`) và quản lý git: merge các nhánh `day09-workers-feat`, `day09-trace-feat` vào `stag` rồi tổng hợp lên `main`.

**Cách công việc của tôi kết nối với phần của thành viên khác:**

`graph.py` là điểm kết nối duy nhất giữa tất cả workers. Supervisor gọi các hàm `run()` của Retrieval, Policy Tool (Worker Owner), tổng hợp qua Synthesis, và đẩy kết quả cho Trace Owner (Nguyễn Tuấn Kiệt) ghi vào `artifacts/traces/`. MCP Owner (Mã Khoa Học) cung cấp `dispatch_tool()` mà `policy_tool_worker_node` sử dụng gián tiếp qua `workers/policy_tool.py`.

**Bằng chứng:**

- Commit `691d683` — `feat: init graph.py` (145 insertions)
- Commit `ada0a3b` — `fix: error zero chunks` (sửa `retrieval.py`)
- Merge PR #9 (`ef2c3a0`), PR #11 (`4ad7c29`), merge `day09-workers-feat` vào stag (`011c5b9`)

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (150–200 từ)

**Quyết định:** Dùng keyword-based routing trong `supervisor_node()` thay vì gọi LLM để phân loại câu hỏi.

**Lý do:**

Tôi xem xét hai phương án:

- **LLM classification**: gọi API để phân loại intent, linh hoạt hơn với câu hỏi mơ hồ, nhưng thêm ~500–800ms latency và tốn thêm chi phí API cho mỗi request.
- **Keyword routing**: dùng danh sách từ khóa theo domain (`_POLICY_KEYWORDS`, `_RETRIEVAL_KEYWORDS`, `_RISK_KEYWORDS`) kết hợp regex cho mã lỗi (`ERR-\w+`), chi phí gần như 0ms, hoàn toàn xác định (deterministic).

Với 5 loại tài liệu nội bộ có domain rõ ràng (SLA, refund policy, access control, IT FAQ, HR), từ khóa là signal đủ mạnh và chính xác. LLM routing chỉ cần thiết khi intent thực sự mơ hồ — trường hợp đó pipeline đã có fallback `default → retrieval_worker`.

**Trade-off đã chấp nhận:**

Keyword routing không xử lý được các cách diễn đạt hoàn toàn mới không chứa từ khóa đã định nghĩa. Chấp nhận điều này vì bộ câu hỏi lab có domain hẹp và có thể mở rộng danh sách từ khóa dần dần.

**Bằng chứng từ trace/code:**

```
# trace run_20260414_164526 (q02)
"supervisor_route": "policy_tool_worker",
"route_reason": "policy keyword matched: hoàn tiền",
"latency_ms": 3858,
"risk_high": false,
"needs_tool": false

# trace run_20260414_164534 (q04)
"supervisor_route": "retrieval_worker",
"route_reason": "no specific keyword matched → default retrieval",
"latency_ms": 4090
```

---

## 3. Tôi đã sửa một lỗi gì? (150–200 từ)

**Lỗi:** `workers_called` bị ghi trùng lặp — mỗi worker xuất hiện 2 lần trong danh sách.

**Symptom (pipeline làm gì sai?):**

Sau khi kết nối workers thực vào graph, chạy thử thấy trace ghi:

```
"workers_called": ["retrieval_worker", "retrieval_worker", "synthesis_worker", "synthesis_worker"]
```

Thay vì đúng là `["retrieval_worker", "synthesis_worker"]`. Trace bị sai khiến `eval_trace.py` (Nguyễn Tuấn Kiệt) tính metrics worker call count không chính xác.

**Root cause:**

Cả hai nơi đều append vào `workers_called`:

1. Wrapper node trong `graph.py` (`retrieval_worker_node`) tự append trước khi gọi worker.
2. Hàm `run()` bên trong `workers/retrieval.py` cũng append `WORKER_NAME` vào `state["workers_called"]`.

**Cách sửa:**

Xóa dòng `state["workers_called"].append(...)` trong cả ba wrapper node của `graph.py`. Để worker's `run()` tự quản lý việc ghi nhận tên mình vào `workers_called`. Wrapper node chỉ ghi vào `history` để trace flow.

**Bằng chứng trước/sau:**

```python
# TRƯỚC — graph.py retrieval_worker_node:
state["workers_called"].append("retrieval_worker")  # duplicate
state = retrieval_run(state)  # run() cũng append

# SAU — graph.py retrieval_worker_node:
state["history"].append("[retrieval_worker] called")
state = retrieval_run(state)  # run() tự append, không bị duplicate
```

```
# TRƯỚC (output):
"workers_called": ["retrieval_worker", "retrieval_worker", "synthesis_worker", "synthesis_worker"]

# SAU (output):
"workers_called": ["retrieval_worker", "synthesis_worker"]
```

---

## 4. Tôi tự đánh giá đóng góp của mình (100–150 từ)

**Tôi làm tốt nhất ở điểm nào?**

Thiết kế routing rõ ràng, có đủ các nhánh quan trọng (policy, retrieval, human review), và `route_reason` luôn cụ thể, không bao giờ là chuỗi rỗng. Việc quản lý git — tạo nhánh, merge PR theo đúng flow `feature → stag → main` — giúp nhóm làm việc song song mà không xung đột.

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**

Routing hiện tại ưu tiên theo thứ tự cứng (policy trước, retrieval sau). Câu hỏi chứa đồng thời cả "ticket" và "hoàn tiền" sẽ luôn route sang `policy_tool_worker` bất kể ngữ cảnh chính là SLA hay refund. Chưa có cơ chế tính điểm tổng hợp.

**Nhóm phụ thuộc vào tôi ở đâu?**

`graph.py` là entry point duy nhất. Nếu chưa xong, toàn bộ pipeline — bao gồm cả eval của Nguyễn Tuấn Kiệt — bị block hoàn toàn.

**Phần tôi phụ thuộc vào thành viên khác:**

Cần Worker Owner cung cấp hàm `run()` đúng contract để kết nối thực; cần MCP Owner hoàn thiện `dispatch_tool()` để policy worker gọi được tool.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50–100 từ)

Tôi sẽ thêm **score-based routing** thay cho priority ordering cứng hiện tại. Trace `run_20260414_164517` (q01 — "SLA xử lý ticket P1") cho thấy câu hỏi bị route sang `policy_tool_worker` vì từ khóa "ticket" khớp `_TOOL_KEYWORDS`, dẫn đến latency 8501ms (gấp đôi so với pure retrieval 4090ms ở q04) dù câu hỏi chỉ cần tìm SLA document. Với score-based routing, mỗi nhánh tích lũy điểm theo số từ khóa khớp, supervisor chọn nhánh điểm cao nhất thay vì nhánh khớp đầu tiên.

---
