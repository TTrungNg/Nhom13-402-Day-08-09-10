# Data contract — Lab Day 10

> Bắt đầu từ `contracts/data_contract.yaml` — mở rộng và đồng bộ file này.

---

## 1. Nguồn dữ liệu (source map)

| Nguồn | Phương thức ingest | Failure mode chính | Metric / alert |
|-------|-------------------|-------------------|----------------|
| Export policy / IT KB (CSV batch từ hệ nguồn) | Đọc file `data/raw/policy_export_dirty.csv` qua `load_raw_csv` trong pipeline | Trùng `chunk_text`, chunk refund còn text “14 ngày” (sync cũ), `effective_date` thiếu hoặc không ISO | `raw_records`, `cleaned_records`, `quarantine_records`; expectation halt nếu còn stale refund sau clean |
| HR / leave policy (cùng export, `doc_id` = `hr_leave_policy`) | Cùng luồng CSV → `clean_rows` | Hai phiên bản xung đột (10 vs 12 ngày phép), cần cắt bản cũ theo cutoff | `quarantine_records` tăng khi bản HR trước cutoff bị tách; so sánh `cleaned_records` trước/sau rule |
| Catalog legacy / doc_id ngoài allowlist (`legacy_*` trong mẫu) | Cùng CSV | `doc_id` không nằm trong allowlist contract | `quarantine_records` hoặc drop; log + manifest |
| Dataset inject kiểm thử (`policy_export_inject.csv`) | Chạy `python etl_pipeline.py run --raw data/raw/policy_export_inject.csv ...` | `exported_at` sai format, `chunk_text` quá ngắn, ký tự BOM trong text | Kiểm tra `reason=invalid_exported_at`, `reason=chunk_text_too_short` trong quarantine; so sánh before/after eval |

---

## 2. Schema cleaned

| Cột | Kiểu | Bắt buộc | Ghi chú |
|-----|------|----------|---------|
| chunk_id | string | Có | Ổn định sau dedupe / normalize (khóa dòng trong cleaned export) |
| doc_id | string | Có | Phải thuộc allowlist trong `contracts/data_contract.yaml` (trừ khi mở rộng có chủ đích) |
| chunk_text | string | Có | Không rỗng sau clean; độ dài tối thiểu theo expectation |
| effective_date | date | Có | Chuẩn ISO `YYYY-MM-DD` sau khi parse ngày kiểu `DD/MM/YYYY` |
| exported_at | datetime | Có | ISO từ export; dùng cho freshness / lineage |

---

## 3. Quy tắc quarantine vs drop

Record không đạt rule clean sẽ được đưa vào `artifacts/quarantine/quarantine_<run_id>.csv`, **không** đi vào cleaned và không embed.

- **Quarantine (có thể xem xét merge lại):**
  - `missing_effective_date`, `invalid_effective_date_format`
  - `invalid_exported_at`
  - `duplicate_chunk_text`
  - `chunk_text_too_short`
- **Drop logic (không merge lại tự động):**
  - `unknown_doc_id` (ngoài contract/allowlist, cần cập nhật contract + rule trước khi nhận)
- **Approve merge lại:** Cleaning/Quality owner duyệt PR cập nhật rule + evidence trong `reports/group_report.md`.

---

## 4. Phiên bản & canonical

- **Source of truth refund:** `data/docs/policy_refund_v4.txt` (`doc_id=policy_refund_v4`) với cửa sổ hoàn tiền 7 ngày.
- **Canonical HR leave:** `data/docs/hr_leave_policy.txt`; cutoff hiệu lực tối thiểu `2026-01-01`.
- **Nguyên tắc khi xung đột version:** giữ bản `effective_date` mới hơn, bản cũ vào quarantine để truy vết.
