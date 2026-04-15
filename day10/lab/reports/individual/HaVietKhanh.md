# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** ___________  
**Vai trò:** Ingestion / Cleaning / Embed / Monitoring — Cleaning & Quality Owner  
**Ngày nộp:** 15/04/2026  
**Độ dài yêu cầu:** **400–650 từ**

---

## 1. Tôi phụ trách phần nào? (80–120 từ)

Tôi phụ trách phần cleaning và expectation, tập trung vào hai module `transform/cleaning_rules.py` và `quality/expectations.py`. Trong `cleaning_rules.py`, tôi bổ sung các rule để chặn dữ liệu nhiễu trước khi embed: chuẩn hóa `chunk_text`, kiểm tra `exported_at` đúng ISO datetime, và đưa vào quarantine nếu `chunk_text` quá ngắn. Trong `expectations.py`, tôi thêm hai expectation halt là `no_empty_exported_at` và `chunk_id_unique` để đảm bảo lineage và idempotency. Tôi kết nối trực tiếp với bạn Embed Owner (đầu ra clean ảnh hưởng đến upsert/prune) và Monitoring Owner (dùng `exported_at` để tính freshness). Bằng chứng commit: `f22eda7` và `27b9ec6`.

---

## 2. Một quyết định kỹ thuật (100–150 từ)

Quyết định kỹ thuật quan trọng nhất của tôi là đặt kiểm tra `exported_at` ở cả hai lớp: clean-time và expectation-time. Ở lớp clean (`clean_rows`), tôi quarantine ngay các dòng có `exported_at` sai định dạng để dữ liệu xấu không đi vào embedding. Ở lớp expectation (`run_expectations`), tôi thêm `no_empty_exported_at` mức `halt` để chặn các trường hợp mất timestamp do lỗi transform hoặc merge sau này. Tôi chọn cách này vì kiểm tra một lớp là chưa đủ: chỉ clean thì lỗi hồi quy có thể lọt qua, còn chỉ expectation thì pipeline phát hiện quá muộn. Log xác nhận ở `run_sprint2-inject.log`: `expectation[no_empty_exported_at] OK (halt) :: empty_exported_at=0`.

---

## 3. Một lỗi hoặc anomaly đã xử lý (100–150 từ)

Anomaly tôi xử lý nằm ở run inject có dữ liệu bẩn mở rộng. Triệu chứng là số quarantine tăng bất thường và xuất hiện reason mới ngoài baseline. Ở `run_id=sprint2-inject`, log ghi `raw_records=13`, `cleaned_records=7`, `quarantine_records=6`, trong khi run fix ghi `raw_records=10`, `cleaned_records=6`, `quarantine_records=4`. Khi soi `artifacts/quarantine/quarantine_sprint2-inject.csv`, tôi thấy hai bản ghi bị loại bởi rule mới: `reason=invalid_exported_at` với `exported_at_raw=not-a-time`, và `reason=chunk_text_too_short` với `chunk_text_normalized=ok`. Sau khi nhóm quay về dữ liệu fix (`sprint3-fix`), hai lỗi này biến mất khỏi quarantine, đồng thời expectation halt vẫn pass toàn bộ. Tôi xác nhận anomaly đã được cô lập ở tầng clean thay vì lan sang retrieval.

---

## 4. Bằng chứng trước / sau (80–120 từ)

Tôi dùng cặp run trước/sau để chứng minh tác động lên retrieval: trước sửa lấy từ `artifacts/eval/after_inject_bad.csv` (run inject-bad), sau sửa lấy từ `artifacts/eval/before_after_eval.csv` (run sprint3-fix).

- Trước (inject-bad):  
`q_refund_window,...,contains_expected=yes,hits_forbidden=yes,...`
- Sau (sprint3-fix):  
`q_refund_window,...,contains_expected=yes,hits_forbidden=no,...`

Dòng đối chứng ổn định:  
`q_leave_version,...,contains_expected=yes,hits_forbidden=no,top1_doc_expected=yes,...`

Metric tôi chịu trách nhiệm thay đổi theo bảng impact của nhóm là giảm rủi ro ngữ cảnh bẩn trong top-k (`hits_forbidden` từ `yes` về `no`) và phản ánh chất lượng đầu vào qua `quarantine_records` (từ 6 về 4 khi bỏ inject).

---

## 5. Cải tiến tiếp theo (40–80 từ)

Nếu có thêm 2 giờ, tôi sẽ thêm một báo cáo tổng hợp reason theo run_id (ví dụ `invalid_exported_at`, `chunk_text_too_short`, `unknown_doc_id`) dưới dạng CSV pivot trong `artifacts/eval/`. Việc này giúp nhìn xu hướng chất lượng dữ liệu theo thời gian và phát hiện nhanh rule cần siết hoặc nới, thay vì đọc quarantine thủ công từng file.
