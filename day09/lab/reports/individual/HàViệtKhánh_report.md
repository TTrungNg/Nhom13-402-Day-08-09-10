# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Khanh Ha V  
**Vai trò trong nhóm:** Supervisor Owner  
**Ngày nộp:** 14/04/2026  
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi phụ trách phần nào? (100–150 từ)

Trong Lab Day 09, tôi chịu trách nhiệm chính về module **Orchestration** của hệ thống Multi-Agent. Đây là "bộ não" điều phối toàn bộ luồng xử lý thông tin từ đầu vào đến đầu ra. Công việc của tôi tập trung vào việc quản lý trạng thái (State Management) và định tuyến (Routing) giữa các worker chuyên biệt.

**Module/file tôi chịu trách nhiệm:**
- File chính: `day09/lab/graph.py`
- Functions tôi implement: `supervisor_node`, `route_decision`, `human_review_node`, `build_graph`, `make_initial_state`.

**Cách công việc của tôi kết nối với phần của thành viên khác:**
Tôi đóng vai trò trung tâm kết nối:
1. Nhận input từ User và phân tích ban đầu.
2. Định tuyến sang `retrieval_worker` (do Worker Owner quản lý) để lấy dữ liệu từ ChromaDB.
3. Chuyển tiếp kết quả sang `policy_tool_worker` (kết nối với MCP Server của MCP Owner) nếu cần kiểm tra quy trình hoặc gọi tool.
4. Cuối cùng chuyển sang `synthesis_worker` để tổng hợp câu trả lời. Tôi phải đảm bảo `AgentState` luôn mang đầy đủ context (chunks, tool results, history) qua từng chặng để worker sau có đủ thông tin làm việc.

**Bằng chứng (commit hash, file có comment tên bạn, v.v.):**
- Code trong `graph.py` định nghĩa cấu trúc `AgentState` và logic `supervisor_node`.
- Commit commit 575d3aab... (fix chunk feat) và e96f428f... (feat(rag): metadata&chunk) liên quan đến việc đồng nhất dữ liệu giữa retrieval và supervisor.

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (150–200 từ)

**Quyết định:** Sử dụng **Regex-based Error Detection** kết hợp với **Keywords Routing** thay vì dùng LLM hoàn toàn để phân loại task ban đầu.

**Lý do:**
Ban đầu, nhóm có ý định dùng một LLM prompt ("Router LLM") để quyết định task thuộc phân loại nào. Tuy nhiên, sau khi trace thử các câu hỏi dạng technical (mã lỗi), tôi nhận thấy LLM đôi khi nhầm lẫn giữa "câu hỏi FAQ" và "sự cố khẩn cấp". Tôi quyết định bổ sung một lớp định tuyến cứng bằng Regex và Keywords.
- **Tốc độ:** Xử lý regex mất <1ms, trong khi LLM tốn 500-1000ms.
- **Độ tin cậy:** Với các mã lỗi dạng `ERR-xxx`, hệ thống cần phải kích hoạt `risk_high` ngay lập tức để yêu cầu `human_review` (HITL). Logic deterministic này giúp đảm bảo không bỏ sót các sự cố P1 nhạy cảm.

**Trade-off đã chấp nhận:**
Hệ thống sẽ kém linh hoạt với những câu hỏi có cấu trúc ngôn ngữ quá phức tạp hoặc dùng từ mượn không nằm trong bộ keyword. Tuy nhiên, với domain của Helpdesk IT, bộ keyword mà tôi xây dựng (`_POLICY_KEYWORDS`, `_RETRIEVAL_KEYWORDS`) đã bao phủ được >90% test cases trong `eval_trace.py`.

**Bằng chứng từ trace/code:**
Đoạn code định nghĩa Regex và logic ưu tiên xử lý rủi ro trong `graph.py`:

```python
# Regex để nhận mã lỗi dạng ERR-xxx
_ERR_CODE_PATTERN = re.compile(r"\berr[-_]\w+\b", re.IGNORECASE)

def supervisor_node(state: AgentState) -> AgentState:
    # ... logic detection ...
    has_err_code = bool(_ERR_CODE_PATTERN.search(task_lower))
    
    # Ưu tiên Risk assessment đầu tiên
    triggered_risk = [kw for kw in _RISK_KEYWORDS if kw in task_lower]
    if triggered_risk or has_err_code:
        risk_high = True
        # ... logic định tuyến sang human_review ...
        if has_err_code:
            route = "human_review"
            route_reasons.append("unknown error code + risk_high → human_review")
```

---

## 3. Tôi đã sửa một lỗi gì? (150–200 từ)

**Lỗi:** Mất dữ liệu Context khi chuyển từ Retrieval sang Policy Tool trong luồng xử lý phức tạp.

**Symptom (pipeline làm gì sai?):**
Khi Supervisor định tuyến task sang `policy_tool_worker`, worker này thường báo lỗi "No context available" hoặc phân tích sai do không có `retrieved_chunks`. Nguyên nhân là do Supervisor nhảy thẳng tới `policy_tool_worker` mà bỏ qua bước `retrieval_worker`.

**Root cause (lỗi nằm ở đâu — indexing, routing, contract, worker logic?):**
Lỗi nằm ở cấu trúc Graph trong `build_graph`. Tôi đã thiết kế các node là các nhánh độc lập, nhưng thực tế `policy_tool_worker` phụ thuộc vào dữ liệu mà `retrieval_worker` cung cấp. Do đó, nếu chỉ nhảy vào node Policy, state sẽ thiếu dữ liệu từ DB.

**Cách sửa:**
Tôi đã cập nhật lại logic chuyển đổi trạng thái trong `build_graph`. Đối với route "policy_tool_worker", tôi thực hiện một chuỗi gọi node tuần tự: `retrieval_worker_node` -> `policy_tool_worker_node`. Điều này đảm bảo state luôn được "lấp đầy" dữ liệu trước khi thực hiện phân tích policy.

**Bằng chứng trước/sau:**
*Trước khi sửa:* Trace báo `retrieved_chunks: []` dù query liên quan đến Refund.
*Sau khi sửa (trong `graph.py`):*
```python
        elif route == "policy_tool_worker":
            # Policy worker cần retrieval context trước để phân tích đúng
            state = retrieval_worker_node(state)  # Gọi retrieval trước
            state = policy_tool_worker_node(state) # Sau đó mới gọi policy
```
Trace ID `run_20260414_181502` cho thấy: 
- `history`: ["... [retrieval_worker] retrieved 3 chunks", "... [policy_tool_worker] policy check complete"]
- `policy_result['policy_applies']`: `False` (đã nhận diện được Flash Sale từ context).

---

## 4. Tôi tự đánh giá đóng góp của mình (100–150 từ)

**Tôi làm tốt nhất ở điểm nào?**
Tôi thiết kế được một bộ `AgentState` rất chi tiết, bao gồm cả `worker_io_logs` và `history`, giúp việc debug và tracing trở nên cực kỳ dễ dàng. Việc tách biệt logic Routing ra khỏi logic thực thi của Worker giúp hệ thống dễ mở rộng hơn (Modular Design).

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**
Phần code `human_review_node` hiện tại mới chỉ là placeholder (mô phỏng). Tôi chưa kịp implement cơ chế tạm dừng thực sự (wait for external signal) mà chỉ mới set flag `hitl_triggered`.

**Nhóm phụ thuộc vào tôi ở đâu?** _(Phần nào của hệ thống bị block nếu tôi chưa xong?)_
Toàn bộ pipeline sẽ bị block nếu Supervisor không định hướng đúng. Nếu tôi không hoàn thiện `AgentState` contract, các thành viên làm Worker sẽ không biết lấy dữ liệu `task` hay `chunks` từ đâu.

**Phần tôi phụ thuộc vào thành viên khác:** _(Tôi cần gì từ ai để tiếp tục được?)_
Tôi phụ thuộc vào **MCP Owner** để cung cấp đúng interface `dispatch_tool` để tích hợp vào worker, và **Worker Owner** để đảm bảo code trong `run()` của họ không làm thay đổi cấu trúc của `AgentState` gốc.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50–100 từ)

Tôi sẽ thực hiện **LLM-as-a-judge** ngay tại Node Supervisor để gán điểm rủi ro (Risk Score) từ 1-10 thay vì chỉ dùng boolean `risk_high`. Lý do là qua trace của câu hỏi *"Gặp lỗi ERR-5520 lúc 2am"*, hệ thống chỉ báo true/false nhưng không phân loại được mức độ ưu tiên xử lý. Nếu có điểm số, tôi có thể route sang các kênh thông báo khác nhau (Slack/SMS) tùy theo độ nghiêm trọng.

---

*Lưu file này với tên: `reports/individual/khanh_ha_v.md`*  
