# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Nguyễn Việt Trung  
**Vai trò:** Ingestion Owner  
**Ngày nộp:** 2026-04-15  
**Độ dài yêu cầu:** **400–650 từ**

---

## 1. Tôi phụ trách phần nào? (80–120 từ)

Tôi đảm nhận vai trò **Ingestion Owner**: thiết kế và triển khai entrypoint chạy toàn bộ pipeline (`cmd_run` trong `etl_pipeline.py`), chịu trách nhiệm đọc file CSV raw, ghi log từng bước với `run_id`, và xuất **manifest JSON** cuối run.

**File / module:**

- `etl_pipeline.py` — hàm `cmd_run` (dòng 49–136): load raw, gọi `clean_rows`, gọi `run_expectations`, gọi embed, ghi manifest
- `contracts/data_contract.yaml` — khai báo schema, `quality_rules`, `freshness.sla_hours`, `canonical_sources`

**Kết nối với thành viên khác:**

Sau khi tôi ghi `cleaned_csv` và `quarantine_csv`, thành viên phụ trách Cleaning đọc lại để kiểm tra; thành viên Monitoring đọc manifest (`manifest_*.json`) để chạy `freshness_check`. Tôi phối hợp trực tiếp để đảm bảo cấu trúc manifest đủ trường (`latest_exported_at`, `quarantine_records`) mà Monitoring cần.

**Bằng chứng (commit / comment trong code):**

- Commit `0245b4a` — `feat: add etl pipeline and data contract`
- Comment dòng 163 `etl_pipeline.py`: `# Tránh "mồi cũ" trong top-k: xóa id không còn trong cleaned run này (index = snapshot publish).`

---

## 2. Một quyết định kỹ thuật (100–150 từ)

**Chiến lược idempotency cho embed: upsert + prune thay vì delete-all-and-reinsert.**

Ban đầu có thể xoá toàn bộ collection rồi insert lại — đơn giản nhưng gây downtime: trong khoảng trống giữa xóa và upsert, query sẽ trả rỗng. Tôi chọn cách **upsert theo `chunk_id`** (Chroma `col.upsert`) kết hợp **prune**: lấy danh sách id hiện có trong collection, tính `prev_ids - set(ids)` rồi `col.delete(ids=drop)`. Cách này đảm bảo collection luôn có dữ liệu hiệu lực; vector cũ bị xoá chính xác theo từng id không còn trong cleaned run — không bao giờ xoá nhầm. Bằng chứng thực tế: `run_sprint3-fix.log` ghi `embed_prune_removed=1`, tức một vector stale từ run inject đã được dọn đúng cách mà không cần xoá collection.

---

## 3. Một lỗi hoặc anomaly đã xử lý (100–150 từ)

**Triệu chứng:** Mọi run đều kết thúc bằng `freshness_check=FAIL` dù `PIPELINE_OK`, khiến nhóm lo ngại pipeline bị lỗi.

**Metric / check phát hiện:** `check_manifest_freshness` so sánh `latest_exported_at` (lấy từ max của cột `exported_at` trong cleaned rows) với `datetime.now(UTC)`. Log `run_sprint1` ghi: `freshness_check=FAIL {"latest_exported_at": "2026-04-10T08:00:00", "age_hours": 121.548, "sla_hours": 24.0, "reason": "freshness_sla_exceeded"}`.

**Root cause:** Dữ liệu test cố định `exported_at=2026-04-10T08:00:00` — cũ hơn SLA 24 giờ. Đây là hành vi **đúng**: freshness check đang làm việc, phát hiện data stale thật.

**Fix:** Tôi xác nhận đây là môi trường lab (data demo cố định); bổ sung env `FRESHNESS_SLA_HOURS` để nhóm có thể override ngưỡng mà không sửa code — khai báo rõ trong `data_contract.yaml` (`freshness.sla_hours: 24`). Pipeline không halt vì freshness là warning-level, không phải halt.

---

## 4. Bằng chứng trước / sau (80–120 từ)

Dưới đây là hai dòng từ `artifacts/eval/before_after_eval.csv` — chạy sau `run_id=sprint3-fix`:

```
question_id,top1_doc_id,contains_expected,hits_forbidden,top1_doc_expected
q_refund_window,policy_refund_v4,yes,no,
q_leave_version,hr_leave_policy,yes,no,yes
```

`run_id=sprint3-fix`: `raw_records=10`, `cleaned_records=6`, `quarantine_records=4`, `embed_prune_removed=1`.  
Trước đó, ở `run_id=sprint2-inject` (`--no-refund-fix --skip-validate`), vector chứa cửa sổ 14 ngày sai lẫn vào index; sau khi prune + upsert với fix, `contains_expected=yes` và `hits_forbidden=no` trên câu hỏi refund — xác nhận pipeline sạch data hoạt động đúng.

---

## 5. Cải tiến tiếp theo (40–80 từ)

Nếu có thêm 2 giờ, tôi sẽ thêm **incremental ingest**: so sánh `latest_exported_at` trong manifest mới nhất với `exported_at` của từng row raw, chỉ đưa vào clean+embed các row thực sự mới hơn. Hiện tại mỗi run xử lý lại toàn bộ 10 row — với corpus lớn (vài trăm nghìn chunk), chiến lược này sẽ giảm đáng kể thời gian chạy và tải cho Chroma upsert.
