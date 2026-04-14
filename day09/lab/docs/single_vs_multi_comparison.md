# Single Agent vs Multi-Agent Comparison — Lab Day 09

**Nhóm:** 13 - E402  
**Ngày:** 14/04/2026

> **Hướng dẫn:** So sánh Day 08 (single-agent RAG) với Day 09 (supervisor-worker).
> Phải có **số liệu thực tế** từ trace — không ghi ước đoán.
> Chạy cùng test questions cho cả hai nếu có thể.

---

## 1. Metrics Comparison

> Điền vào bảng sau. Lấy số liệu từ:
> - Day 08: chạy `python eval.py` từ Day 08 lab
> - Day 09: chạy `python eval_trace.py` từ lab này

| Metric                | Day 08 (Single Agent) | Day 09 (Multi-Agent) | Delta    | Ghi chú                     |
| --------------------- | --------------------- | -------------------- | -------- | --------------------------- |
| Avg confidence        | N/A                   | 0.617                | N/A      | Day 08 không log confidence |
| Avg latency (ms)      | 1500                  | 4609                 | +3109    | +207% do multi-step         |
| Abstain rate (%)      | 10%                   | 6%                   | -4%      | Giảm nhờ routing + policy   |
| Multi-hop accuracy    | Thấp                  | Trung bình           | ↑        | Có cải thiện                |
| Routing visibility    | ✗ Không có            | ✓ Có route_reason    | N/A      |                             |
| Debug time (estimate) | 30 phút               | 10 phút              | -20 phút |                             |
| MCP usage rate        | N/A                   | 33%                  | N/A      | Chỉ có ở Day 09             |


> **Lưu ý:** Nếu không có Day 08 kết quả thực tế, ghi "N/A" và giải thích.

---

## 2. Phân tích theo loại câu hỏi

### 2.1 Câu hỏi đơn giản (single-document)

| Nhận xét    | Day 08                  | Day 09                           |
| ----------- | ----------------------- | -------------------------------- |
| Accuracy    | Cao                     | Cao                              |
| Latency     | Thấp (~1.5s)            | Cao (~4.6s)                      |
| Observation | Trả lời trực tiếp từ KB | Bị overhead do routing + workers |


**Kết luận:** Multi-agent có cải thiện không? Tại sao có/không?

Không cải thiện đáng kể. Multi-agent gây overhead không cần thiết cho query đơn giản.

### 2.2 Câu hỏi multi-hop (cross-document)

| Nhận xét         | Day 08           | Day 09                         |
| ---------------- | ---------------- | ------------------------------ |
| Accuracy         | Thấp             | Trung bình                     |
| Routing visible? | ✗                | ✓                              |
| Observation      | Dễ thiếu context | Có thể combine từ nhiều worker |


**Kết luận:**

Có cải thiện. Multi-agent giúp xử lý multi-step tốt hơn và dễ debug khi sai.

### 2.3 Câu hỏi cần abstain

| Nhận xét            | Day 08           | Day 09                            |
| ------------------- | ---------------- | --------------------------------- |
| Abstain rate        | 10%              | 6%                                |
| Hallucination cases | Nhiều hơn        | Ít hơn                            |
| Observation         | Hay trả lời đoán | Có policy check trước khi trả lời |


**Kết luận:**

Multi-agent giảm hallucination nhờ policy layer và routing rõ ràng hơn.

---

## 3. Debuggability Analysis

> Khi pipeline trả lời sai, mất bao lâu để tìm ra nguyên nhân?

### Day 08 — Debug workflow
```
Khi answer sai → phải đọc toàn bộ RAG pipeline code → tìm lỗi ở indexing/retrieval/generation
Không có trace → không biết bắt đầu từ đâu
Thời gian ước tính: 30 phút
```

### Day 09 — Debug workflow
```
Khi answer sai → đọc trace → xem supervisor_route + route_reason
  → Nếu route sai → sửa supervisor routing logic
  → Nếu retrieval sai → test retrieval_worker độc lập
  → Nếu synthesis sai → test synthesis_worker độc lập
Thời gian ước tính: 10 phút
```

**Câu cụ thể nhóm đã debug:** _(Mô tả 1 lần debug thực tế trong lab)_

Câu hỏi về SLA P1 bị route sang policy_tool_worker do keyword “ticket”, dẫn đến gọi MCP tool không cần thiết => Do nhóm dùng keyword-match để gọi MCP.

---

## 4. Extensibility Analysis

> Dễ extend thêm capability không?

| Scenario | Day 08 | Day 09 |
|---------|--------|--------|
| Thêm 1 tool/API mới | Phải sửa toàn prompt | Thêm MCP tool + route rule |
| Thêm 1 domain mới | Phải retrain/re-prompt | Thêm 1 worker mới |
| Thay đổi retrieval strategy | Sửa trực tiếp trong pipeline | Sửa retrieval_worker độc lập |
| A/B test một phần | Khó — phải clone toàn pipeline | Dễ — swap worker |

**Nhận xét:**

Multi-agent linh hoạt hơn rõ rệt. Có thể thêm worker/tool độc lập mà không ảnh hưởng toàn hệ thống, trong khi single-agent dễ bị “prompt bloat” và khó maintain khi scale.

---

## 5. Cost & Latency Trade-off

> Multi-agent thường tốn nhiều LLM calls hơn. Nhóm đo được gì?

| Scenario | Day 08 calls | Day 09 calls |
|---------|-------------|-------------|
| Simple query | 1 LLM call | 2-3 LLM calls |
| Complex query | 1 LLM call | 3-4 LLM calls |
| MCP tool call | N/A | 1+ LLM calls |

**Nhận xét về cost-benefit:**

Multi-agent tốn nhiều latency và LLM calls hơn, nhưng đổi lại tăng khả năng kiểm soát, giảm hallucination và cải thiện debugability — phù hợp cho production system phức tạp hơn.

---

## 6. Kết luận

> **Multi-agent tốt hơn single agent ở điểm nào?**

1. Dễ debug và quan sát
2. Dễ mở rộng và tích hợp tool

> **Multi-agent kém hơn hoặc không khác biệt ở điểm nào?**

1. Latency và cost cao hơn, không cải thiện nhiều cho query đơn giản

> **Khi nào KHÔNG nên dùng multi-agent?**

Khi bài toán đơn giản (single-step Q&A, không cần tool/reasoning phức tạp) vì overhead không đáng.

> **Nếu tiếp tục phát triển hệ thống này, nhóm sẽ thêm gì?**

Nâng cấp routing bằng LLM/semantic classifier + cải thiện route_reason (thêm confidence, intent) để giảm misroute và gọi tool dư thừa.
