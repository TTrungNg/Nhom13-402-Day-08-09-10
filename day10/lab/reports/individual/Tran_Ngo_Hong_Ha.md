# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Trần Ngô Hồng Hà 
**Vai trò:** Quality Owner 
**Ngày nộp:** 15/04/2026 
**Độ dài yêu cầu:** **400–650 từ** (ngắn hơn Day 09 vì rubric slide cá nhân ~10% — vẫn phải đủ bằng chứng)

---

> Viết **"tôi"**, đính kèm **run_id**, **tên file**, **đoạn log** hoặc **dòng CSV** thật.  
> Nếu làm phần clean/expectation: nêu **một số liệu thay đổi** (vd `quarantine_records`, `hits_forbidden`, `top1_doc_expected`) khớp bảng `metric_impact` của nhóm.  
> Lưu: `reports/individual/[ten_ban].md`

---

## 1. Tôi phụ trách phần nào? (80–120 từ)

**File / module:**

- expectations.py, /artifacts/quarantine

**Kết nối với thành viên khác:**

- Tôi phụ trách bổ sung các expectation mới nhằm đảm bảo chất lượng dữ liệu trước khi indexing: exported_at không được rỗng để phục vụ kiểm tra freshness và lineage, và chunk_id phải unique để đảm bảo quá trình upsert idempotent hoạt động chính xác. Phần công việc của tôi nằm giữa bước data cleaning và indexing, giúp phát hiện lỗi dữ liệu sớm trước khi ảnh hưởng đến retrieval hoặc evaluation. Các expectation này hỗ trợ thành viên phụ trách indexing tránh ghi đè sai dữ liệu, đồng thời giúp nhóm evaluation đảm bảo tính nhất quán giữa các lần chạy.

**Bằng chứng (commit / comment trong code):**

commit_id: 9a1a18d65fb161ba4d1809b4c506e94b3bcf3094

---

## 2. Một quyết định kỹ thuật (100–150 từ)

> Một quyết định quan trọng của tôi là đặt hai expectation mới (no_empty_exported_at và chunk_id_unique) ở mức độ halt thay vì warn. Lý do là cả hai điều kiện này đều ảnh hưởng trực tiếp đến tính nhất quán của pipeline. Nếu exported_at bị thiếu, hệ thống sẽ không thể xác định freshness hoặc lineage của dữ liệu, dẫn đến khó khăn trong việc debug hoặc rollback. Tương tự, nếu chunk_id không unique, quá trình upsert có thể ghi đè dữ liệu sai, gây lỗi retrieval hoặc làm sai kết quả evaluation.

_________________

---

## 3. Một lỗi hoặc anomaly đã xử lý (100–150 từ)

- Trong quá trình kiểm tra dữ liệu, tôi phát hiện một anomaly khi một số row không có trường thuộc tính exported_at. Triệu chứng là các lần chạy evaluation cho kết quả không ổn định, khó xác định dữ liệu nào được sử dụng trong mỗi run. Tôi thêm expectation no_empty_exported_at để phát hiện các dòng thiếu thông tin này.

_________________

---

## 4. Bằng chứng trước / sau (80–120 từ)

> Dán ngắn 2 dòng từ `before_after_eval.csv` hoặc tương đương; ghi rõ `run_id`.

q_refund_window	Khách hàng có bao nhiêu ngày để yêu cầu hoàn tiền kể từ khi xác nhận đơn?	policy_refund_v4	Yêu cầu được gửi trong vòng 7 ngày làm việc kể từ thời điểm xác nhận đơn hàng.	yes	no		3
q_p1_sla	SLA phản hồi đầu tiên cho ticket P1 là bao lâu?	sla_p1_2026	Ticket P1 có SLA phản hồi ban đầu 15 phút và resolution trong 4 giờ.	yes	no		3

---

## 5. Cải tiến tiếp theo (40–80 từ)

> Nếu có thêm 2 giờ — một việc cụ thể (không chung chung).

tôi sẽ bổ sung thêm expectation kiểm tra định dạng exported_at theo chuẩn ISO 8601. Điều này giúp đảm bảo tính nhất quán về thời gian và hỗ trợ tốt hơn cho việc tracking lineage và freshness. Ngoài ra, tôi cũng sẽ thêm logging chi tiết để dễ dàng truy vết các lỗi dữ liệu.
