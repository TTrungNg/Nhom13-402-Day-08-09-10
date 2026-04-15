# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Member 01  
**Vai trò:** Cleaning & Quality  
**Ngày nộp:** 2026-04-15  
**Độ dài yêu cầu:** 400–650 từ

---

## 1. Tôi phụ trách phần nào? (80–120 từ)

Tôi phụ trách hai module chính là `transform/cleaning_rules.py` và `quality/expectations.py`. Ở tầng cleaning, tôi mở rộng các quy tắc xử lý dữ liệu bẩn để tăng khả năng phát hiện lỗi từ nguồn export trước khi đẩy vào embedding. Ở tầng quality, tôi bổ sung expectation để đảm bảo các trường quan trọng phục vụ freshness và idempotent không bị bỏ sót. Tôi phối hợp với bạn phụ trách embed để kiểm tra rằng dữ liệu sau clean vẫn tương thích với `chunk_id` upsert trên Chroma, đồng thời phối hợp với bạn phụ trách docs để đưa số liệu vào bảng `metric_impact`.

**File / module:**

- `transform/cleaning_rules.py`
- `quality/expectations.py`
- `reports/group_report.md` (bảng metric impact)

---

## 2. Một quyết định kỹ thuật (100–150 từ)

Quyết định kỹ thuật quan trọng nhất là dùng mô hình “chặn sớm ở clean trước khi validate” cho các lỗi dữ liệu có thể gây nhiễu retrieval, thay vì để expectation fail toàn cục. Cụ thể, tôi quarantine các record có `invalid_exported_at` và `chunk_text_too_short` ở bước clean, sau đó expectation `no_empty_exported_at` đóng vai trò lớp bảo vệ cuối. Cách này giúp pipeline vừa an toàn vừa ổn định: dữ liệu xấu bị loại ra sớm, còn expectation vẫn theo dõi chất lượng tổng thể để phát hiện regression. Ngoài ra, expectation `chunk_id_unique` được đặt ở mức `halt` để ngăn nguy cơ nhập nhằng định danh khi upsert vector, phù hợp yêu cầu idempotent của sprint.

---

## 3. Một lỗi hoặc anomaly đã xử lý (100–150 từ)

Anomaly tôi gặp là run chuẩn Sprint 1 và Sprint 2 cho ra số liệu gần như giống nhau, khiến khó chứng minh tác động của rule mới theo rubric chống trivial. Để xử lý, tôi tạo thêm dữ liệu inject (`data/raw/policy_export_inject.csv`) với các dòng cố ý sai `exported_at` và `chunk_text` quá ngắn. Sau đó chạy `run_id=sprint2-inject`, log thay đổi rõ từ `raw=10, quarantine=4` sang `raw=13, quarantine=6`, đồng thời `quarantine_sprint2-inject.csv` xuất hiện các reason mới: `invalid_exported_at`, `chunk_text_too_short`. Điều này giúp chứng minh rule mới có tác động đo được và có thể truy vết trực tiếp trên artifact.

---

## 4. Bằng chứng trước / sau (80–120 từ)

Trước inject (`run_sprint2.log`): `raw_records=10`, `cleaned_records=6`, `quarantine_records=4`.  
Sau inject (`run_sprint2-inject.log`): `raw_records=13`, `cleaned_records=7`, `quarantine_records=6`.

Trong `artifacts/quarantine/quarantine_sprint2-inject.csv`, tôi ghi nhận thêm:
- `reason=invalid_exported_at` (dòng `exported_at=not-a-time`)
- `reason=chunk_text_too_short` (dòng `chunk_text=ok`)

Expectation mới vẫn an toàn:
- `expectation[no_empty_exported_at] OK ... empty_exported_at=0`
- `expectation[chunk_id_unique] OK ... duplicate_chunk_id=0`

---

## 5. Cải tiến tiếp theo (40–80 từ)

Nếu có thêm 2 giờ, tôi sẽ thêm báo cáo phân phối `reason` theo run vào manifest hoặc một file stats riêng để đội vận hành theo dõi trend chất lượng dữ liệu nhanh hơn. Đồng thời tôi muốn tách ngưỡng `chunk_text_too_short` ra `.env` để dễ tuning theo từng nguồn dữ liệu mà không cần sửa code.
