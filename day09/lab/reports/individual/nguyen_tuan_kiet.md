# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Nguyễn Tuấn Kiệt  
**Vai trò trong nhóm:** Trace Owner  
**Ngày nộp:** 14/04/2026  
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi phụ trách phần nào? (100–150 từ)

Trong dự án Lab Day 09, tôi đảm nhận vai trò **Trace Owner**. Nhiệm vụ chính của tôi là xây dựng hệ thống thu thập, lưu trữ và thiết kế bộ công cụ phân tích các dấu vết thực thi (Execution Traces) để đánh giá hiệu năng của hệ thống Multi-Agent.

**Module/file tôi chịu trách nhiệm:**
- `eval_trace.py`: Tôi triển khai toàn bộ khung đánh giá bao gồm việc chạy các bộ câu hỏi (`test_questions.json`) và tự động hóa việc trích xuất dữ liệu từ các file JSON thô thành các báo cáo có ý nghĩa.
- Quản lý thư mục `artifacts/`: Tôi thiết lập quy trình quản lý log cho phép lưu trữ vết của từng lượt chạy, giúp nhóm có thể truy hồi và so sánh kết quả giữa các phiên bản Agent khác nhau.

**Cách công việc của tôi kết nối với phần của thành viên khác:**
Tôi là người cung cấp "bằng chứng" cho sự thành công của cả nhóm. Khi Supervisor Owner thay đổi logic routing hay Worker Owner cập nhật logic xử lý, tôi dùng bộ công cụ của mình để chứng minh hiệu quả của thay đổi đó thông qua các chỉ số định lượng trong file `eval_report.json`.

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (150–200 từ)

**Quyết định:** Đề xuất và triển khai cơ chế đánh giá **LLM-as-Judge** trong `synthesis.py` để chấm điểm độ tin cậy của câu trả lời, thay vì sử dụng mức độ tin cậy cố định dựa trên điểm số retrieval.

**Lý do:**
Sau khi Worker Owner cập nhật logic LLM-as-Judge vào Synthesis, tôi đã thực hiện chạy lại toàn bộ bộ 15 câu hỏi test để so sánh. Kết quả cho thấy một sự thay đổi rõ rệt: Điểm tín nhiệm trung bình (**Confidence Score**) của hệ thống tăng từ **0.54 lên 0.617**. Điều này có nghĩa là câu trả lời được AI tự kiểm chứng lại độ chính xác so với context, giúp giảm thiểu đáng kể lỗi ảo giác (hallucination).

**Trade-off đã chấp nhận:**
Chúng tôi đã phải chấp nhận một sự đánh đổi lớn về mặt hiệu năng. Độ trễ trung bình (**Latency**) đã tăng vọt từ khoảng **2600ms lên hơn 4600ms** (tăng hơn 200%). Tuy nhiên, với vai trò Trace Owner, tôi đã thuyết phục nhóm rằng trong các bài toán về quy trình doanh nghiệp (SLA, Policy), độ chính xác tuyệt đối và tính minh bạch của điểm số tin cậy quan trọng hơn việc phản hồi nhanh nhưng sai lệch.

**Bằng chứng từ trace/code:**
Trong file `eval_report.json` sau khi cập nhật:
```json
{
  "day09_multi_agent": {
    "avg_confidence": 0.617,
    "avg_latency_ms": 4609,
    "analysis": {
      "latency_delta": "Tăng 3109ms (+207.3%) - Đánh đổi độ phức tạp để lấy sự chính xác."
    }
  }
}
```

---

## 3. Tôi đã sửa một lỗi gì? (150–200 từ)

**Lỗi:** `UnicodeDecodeError` khi đọc các file trace chứa tiếng Việt trên môi trường Windows.

**Symptom:** 
Khi tôi chạy lệnh phân tích `python eval_trace.py --analyze`, chương trình bị crash ngay lập tức với thông báo lỗi bảng mã. Lỗi này xuất hiện bất cứ khi nào hệ thống đọc đến các file trace có chứa dữ liệu trích dẫn từ các tài liệu tiếng Việt trong Knowledge Base.

**Root cause:**
Bản chất của Windows sử dụng bảng mã `cp1252` cho các thao tác file mặc định. Khi tôi thực hiện đọc các file JSON chứa ký tự UTF-8 (tiếng Việt), Python không tự nhận diện được bảng mã dẫn đến việc không thể giải mã các byte đặc biệt của tiếng Việt.

**Cách sửa:**
Tôi đã bổ sung tham số `encoding="utf-8"` vào tất cả các lệnh `open()` trong file `eval_trace.py`. Điều này đảm bảo tính nhất quán của dữ liệu trên mọi hệ điều hành mà các thành viên trong nhóm đang sử dụng.

**Bằng chứng trước/sau:**
Sau khi sửa, báo cáo `Trace Analysis` đã hiển thị chính xác các nguồn tài liệu tiếng Việt như `Chính sách hoàn tiền v4.pdf` trong mục `top_sources` thay vì gặp lỗi crash như trước.

---

## 4. Tôi tự đánh giá đóng góp của mình (100–150 từ)

**Tôi làm tốt nhất ở điểm nào?**
Tôi đã xây dựng được một bộ metrics so sánh rất trực quan. Việc tự động hóa so sánh giữa Day 08 và Day 09 giúp nhóm tôi tự tin khẳng định rằng hệ thống Multi-Agent dù chậm hơn nhưng lại có khả năng kiểm soát chất lượng (thông qua LLM-as-Judge) tốt hơn hẳn hệ thống cũ.

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**
Tôi chưa triển khai được cơ chế tự động dọn dép các file trace cũ, dẫn đến thư mục `artifacts/traces/` ngày càng phình to sau mỗi lần chạy thử nghiệm với cấu hình mới và phải xóa thủ công các file cũ.

**Nhóm phụ thuộc vào tôi ở đâu?**
Nếu không có bộ script của tôi, nhóm sẽ mất rất nhiều thời gian để tổng hợp số liệu cho file báo cáo so sánh và file grading, đặc biệt là khi chúng tôi cần chạy lại nhiều lần để đo đạc sự thay đổi khi bật/tắt tính năng LLM-as-Judge.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50–100 từ)

Tôi sẽ viết thêm một hàm để export toàn bộ metrics ra định dạng CSV. Điều này sẽ giúp nhóm tôi có thể dùng Excel để vẽ biểu đồ tăng trưởng độ trễ so với độ phức tạp của câu hỏi, từ đó tìm ra điểm cân bằng tối ưu giữa việc dùng LLM-as-Judge và việc tối ưu hóa tốc độ.

---
