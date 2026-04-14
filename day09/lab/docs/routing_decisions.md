# Routing Decisions Log — Lab Day 09

**Nhóm:** 13 - E402  
**Ngày:** 14/04/2026

> **Hướng dẫn:** Ghi lại ít nhất **3 quyết định routing** thực tế từ trace của nhóm.
> Không ghi giả định — phải từ trace thật (`artifacts/traces/`).
> 
> Mỗi entry phải có: task đầu vào → worker được chọn → route_reason → kết quả thực tế.

---

## Routing Decision #1

**Task đầu vào:**
> Ticket P1 được tạo lúc 22:47. Ai sẽ nhận thông báo đầu tiên và qua kênh nào? Escalation xảy ra lúc mấy giờ?

**Worker được chọn:** `policy_tool_worker`  
**Route reason (từ trace):** `MCP tool keywords detected: ticket`  
**MCP tools được gọi:** `get_ticket_info`
**Workers called sequence:** retrieval_worker → policy_tool_worker → synthesis_worker

**Kết quả thực tế:**
- final_answer (ngắn): On-call engineer nhận thông báo qua Slack + email; escalation lúc 22:57
- confidence: 0.66
- Correct routing? Yes

**Nhận xét:** Routing này là hợp lý. Câu hỏi yêu cầu thông tin vừa từ policy (SLA, escalation rule) vừa từ dữ liệu thực tế (timestamp ticket), nên cần gọi MCP tool.

_________________

---

## Routing Decision #2

**Task đầu vào:**
> Khách hàng có thể yêu cầu hoàn tiền trong bao nhiêu ngày?

**Worker được chọn:** `policy_tool_worker`  
**Route reason (từ trace):** `policy keyword matched: hoàn tiền`  
**MCP tools được gọi:** Không có  
**Workers called sequence:** retrieval_worker → policy_tool_worker → synthesis_worker

**Kết quả thực tế:**
- final_answer (ngắn): 7 ngày làm việc kể từ khi xác nhận đơn hàng
- confidence: 0.64
- Correct routing? Yes

**Nhận xét:**

Routing này là hợp lý vì câu hỏi liên quan trực tiếp đến policy hoàn tiền. policy_tool_worker giúp xác nhận policy áp dụng và đảm bảo answer đúng theo quy định, không cần gọi MCP tool.

---

## Routing Decision #3

**Task đầu vào:**
> SLA xử lý ticket P1 là bao lâu?

**Worker được chọn:** `policy_tool_worker`  
**Route reason (từ trace):** `MCP tool keywords detected: ticket`  
**MCP tools được gọi:** get_ticket_info  
**Workers called sequence:** retrieval_worker → policy_tool_worker → synthesis_worker

**Kết quả thực tế:**
- final_answer (ngắn): 15 phút phản hồi, 4 giờ xử lý, escalation sau 10 phút
- confidence: 0.68
- Correct routing? Yes

**Nhận xét:**

Routing đúng nhưng chưa tối ưu, do implement keyword-based matching nên supervisor tự động route theo keyword "ticket", thực tế không cần dùng MCP tool.

---

## Routing Decision #4 (tuỳ chọn — bonus)

**Task đầu vào:**
> _________________

**Worker được chọn:** `___________________`  
**Route reason:** `___________________`

**Nhận xét: Đây là trường hợp routing khó nhất trong lab. Tại sao?**

_________________

---

## Tổng kết

### Routing Distribution

| Worker | Số câu được route | % tổng |
|--------|------------------|--------|
| retrieval_worker | 5 | 33% |
| policy_tool_worker | 10 | 66% |
| human_review | 1 | 6% |

### Routing Accuracy

> Trong số X câu nhóm đã chạy, bao nhiêu câu supervisor route đúng?

- Câu route đúng: 10 / 15
- Câu route sai (đã sửa bằng cách nào?): 5 - điều chỉnh routing logic
- Câu trigger HITL: 1

### Lesson Learned về Routing

> Quyết định kỹ thuật quan trọng nhất nhóm đưa ra về routing logic là gì?  
> (VD: dùng keyword matching vs LLM classifier, threshold confidence cho HITL, v.v.)

1. Sử dụng keyword matching đơn giản dễ implement nhưng dễ route sai => cần nâng cấp lên hybrid
2. Cần phân biệt rõ giữa query cần tool (dynamic data) và query chỉ cần retrieval (static KB) để tránh gọi MCP dư thừa.

### Route Reason Quality

> Nhìn lại các `route_reason` trong trace — chúng có đủ thông tin để debug không?  
> Nếu chưa, nhóm sẽ cải tiến format route_reason thế nào?

Các route_reason hiện tại còn khá chung chung (VD: “keyword detected”), chưa đủ để debug sâu. Cải tiến bằng cách bổ sung thông tin chi tiết hơn như: matched keyword, confidence score, và lý do chọn worker, etc.
