# Báo Cáo Nhóm — Lab Day 10: Data Pipeline & Data Observability

**Tên nhóm:** Nhóm 13 - Lớp 402
**Thành viên:**
| Tên | Vai trò (Day 10) | Email |
|-----|------------------|-------|
| Nguyễn Việt Trung | Ingestion / Raw Owner | - |
| Hà Việt Khánh | Cleaning Owner | - |
| Trần Ngô Hồng Hà | Quality Owner | - |
| Mã Khoa Học | Embed & Idempotency Owner | - |
| Nguyễn Tuấn Kiệt | Monitoring Owner | - |
| Nguyễn Hữu Nam | Docs Owner | - |

**Ngày nộp:** 2026-04-15  
**Repo:** day10/lab  
**Độ dài khuyến nghị:** 600–1000 từ

---

> **Nộp tại:** `reports/group_report.md`  
> **Deadline commit:** xem `SCORING.md` (code/trace sớm; report có thể muộn hơn nếu được phép).  
> Phải có **run_id**, **đường dẫn artifact**, và **bằng chứng before/after** (CSV eval hoặc screenshot).

---

## 1. Pipeline tổng quan (150–200 từ)

Nhóm xây dựng pipeline ETL cho nguồn raw `data/raw/policy_export_dirty.csv`. Entry point nằm ở `etl_pipeline.py`, nơi pipeline đọc CSV, gắn `run_id`, ghi log theo từng bước, sau đó xuất `cleaned_csv`, `quarantine_csv`, `manifest` và log tương ứng trong `artifacts/`. Luồng xử lý end-to-end gồm 4 lớp: ingestion, cleaning, expectation, rồi embed lên Chroma để phục vụ retrieval. Ở lớp clean, dữ liệu được chuẩn hóa schema, lọc `doc_id` theo allowlist, sửa refund stale, kiểm tra ngày tháng, loại trùng và tách các bản ghi lỗi sang quarantine. Ở lớp expectation, nhóm dùng các check bắt buộc để đảm bảo dữ liệu sạch trước khi publish snapshot. Sau đó lớp embed chạy theo chiến lược snapshot mới nhất: `upsert(chunk_id)` cho dữ liệu hợp lệ và prune các `chunk_id` không còn trong cleaned run hiện tại, tránh việc index giữ lại context cũ. Monitoring đọc `manifest_*.json` để kiểm tra freshness dựa trên `latest_exported_at`. Một lệnh chạy điển hình là `python etl_pipeline.py run --run-id sprint3-fix`; toàn bộ artifact của run được truy vết theo `run_id` trong thư mục `artifacts/`.

---

## 2. Cleaning & expectation (150–200 từ)

Phần cleaning và quality là nơi nhóm tập trung nhiều thay đổi nhất để chứng minh pipeline không chỉ chạy được mà còn có khả năng cô lập dữ liệu bẩn. Ngoài baseline rule như allowlist `doc_id`, chuẩn hóa `effective_date`, dedupe theo normalized text và sửa refund stale 14->7 ngày, nhóm bổ sung thêm ba rule mới. Thứ nhất là chuẩn hóa BOM/zero-width trong `chunk_text` để tránh ký tự rác đi vào cleaned snapshot. Thứ hai là quarantine các dòng có `exported_at` sai định dạng với reason `invalid_exported_at`. Thứ ba là quarantine các dòng có `chunk_text` quá ngắn với reason `chunk_text_too_short`, vì đây là loại dữ liệu dễ gây nhiễu retrieval. Ở lớp expectation, nhóm thêm hai check mức **halt** là `no_empty_exported_at` và `chunk_id_unique`. Hai expectation này bảo vệ lineage, freshness và tính đúng đắn của cơ chế upsert idempotent.

### 2a. Bảng metric_impact (bắt buộc — chống trivial)

| Rule / Expectation mới (tên ngắn) | Trước (số liệu) | Sau / khi inject (số liệu) | Chứng cứ (log / CSV / commit) |
|-----------------------------------|------------------|-----------------------------|-------------------------------|
| Rule `invalid_exported_at` quarantine | `run_sprint2`: `raw_records=10`, `quarantine_records=4` | `run_sprint2-inject`: `raw_records=13`, `quarantine_records=6`; xuất hiện `reason=invalid_exported_at` | `artifacts/quarantine/quarantine_sprint2-inject.csv` |
| Rule `chunk_text_too_short` quarantine | Chưa có record ngắn trong run chuẩn | Inject có thêm dòng `reason=chunk_text_too_short`, `chunk_text_normalized=ok` | `artifacts/quarantine/quarantine_sprint2-inject.csv` |
| Rule normalize BOM/zero-width | Chưa có ký tự BOM/zero-width trong raw mẫu | Dòng inject được clean và đi vào cleaned dưới dạng text chuẩn, không còn ký tự rác | `artifacts/cleaned/cleaned_sprint2-inject.csv` |
| Expectation `no_empty_exported_at` | Trước khi thêm chưa có check bắt buộc cho lineage/freshness | Sau khi thêm: `empty_exported_at=0` ở các run chuẩn và inject | `artifacts/logs/run_sprint2.log`, `artifacts/logs/run_sprint2-inject.log` |
| Expectation `chunk_id_unique` | Trước khi thêm chưa có assert uniqueness cho embed | Sau khi thêm: `duplicate_chunk_id=0`, bảo vệ upsert/prune | `artifacts/logs/run_sprint2.log`, `artifacts/logs/run_sprint2-inject.log` |

Một lần fail có chủ đích xảy ra ở run `inject-bad` khi nhóm chạy với `--no-refund-fix --skip-validate`. Khi đó expectation liên quan đến stale refund bị vi phạm để mô phỏng corruption. Sau đó nhóm rerun bản chuẩn `sprint3-fix` để expectation pass lại và publish snapshot sạch.

---

## 3. Before / after ảnh hưởng retrieval hoặc agent (200–250 từ)

Nhóm dùng kịch bản inject corruption để chứng minh chất lượng dữ liệu ảnh hưởng trực tiếp đến retrieval. Ở run `inject-bad`, nhóm cố tình chạy `python etl_pipeline.py run --run-id inject-bad --no-refund-fix --skip-validate`, tức là cho phép một bản ghi refund cũ lọt qua pipeline và vẫn embed vào index. Theo báo cáo của Embed Owner, log của run này có `embed_prune_removed=2` và `embed_upsert count=6`, đồng thời expectation `refund_no_stale_14d_window` fail nhưng pipeline vẫn tiếp tục do đã bật bỏ validate. Hệ quả thể hiện rõ trong `artifacts/eval/after_inject_bad.csv`: với câu `q_refund_window`, hệ thống vẫn trả đúng tài liệu `policy_refund_v4` và `contains_expected=yes`, nhưng `hits_forbidden=yes`. Điều đó có nghĩa là trong top-k vẫn còn chunk chứa ngữ cảnh cũ 14 ngày, nên retrieval chưa an toàn dù top1 nhìn có vẻ đúng.

Sau đó nhóm chạy lại pipeline chuẩn với `run_id=sprint3-fix`. Ở run này, clean snapshot quay về trạng thái hợp lệ, expectation pass trở lại, và cơ chế prune xóa đúng vector stale còn sót lại (`embed_prune_removed=1`). Bằng chứng trong `artifacts/eval/before_after_eval.csv` cho thấy cùng câu `q_refund_window` giữ `contains_expected=yes` nhưng chuyển từ `hits_forbidden=yes` sang `hits_forbidden=no`. Một dòng đối chứng khác là `q_leave_version`, vẫn ổn định ở trạng thái `contains_expected=yes`, `hits_forbidden=no`, `top1_doc_expected=yes`. Đây là bằng chứng before/after rõ ràng rằng tầng clean + expectation + idempotent embed đã làm giảm nhiễu trong top-k và cải thiện chất lượng knowledge base cho agent retrieval.

---

## 4. Freshness & monitoring (100–150 từ)

Nhóm đặt freshness SLA là 24 giờ, đọc từ `contracts/data_contract.yaml` và kiểm tra qua `monitoring/freshness_check.py` dựa trên trường `latest_exported_at` trong manifest. Thành viên Monitoring chọn cách phân biệt rõ lỗi thiếu timestamp với dữ liệu stale: nếu manifest không có timestamp hợp lệ thì xem là lỗi cấu trúc; nếu timestamp có tồn tại nhưng quá hạn SLA thì coi là dữ liệu stale cần cảnh báo vận hành. Trong bối cảnh lab, nhiều run như `sprint1` hoặc `sprint3-fix` vẫn cho freshness `FAIL` vì dữ liệu mẫu có `exported_at=2026-04-10T08:00:00`, cũ hơn ngưỡng 24 giờ. Nhóm xác nhận đây là hành vi đúng theo contract chứ không phải pipeline hỏng. Vì vậy pipeline vẫn `PIPELINE_OK`, còn freshness được dùng như tín hiệu quan sát chất lượng dữ liệu. Cách xử lý vận hành là ghi rõ hiện tượng này trong `docs/runbook.md` và cho phép override SLA bằng cấu hình khi cần demo với snapshot cũ.

---

## 5. Liên hệ Day 09 (50–100 từ)

Có liên hệ trực tiếp. Day 10 đóng vai trò làm sạch, kiểm soát expectation và publish snapshot ổn định trước khi Day 09 truy xuất dữ liệu. Khi retriever ở Day 09 trỏ vào collection đã được publish sau `sprint3-fix`, agent sẽ tránh được lỗi kiểu “câu trả lời đúng tài liệu nhưng lẫn version cũ của context”. Nói cách khác, Day 10 là tầng data quality cho Day 09: nếu pipeline Day 10 kiểm soát tốt stale data, duplicate và malformed rows thì chất lượng retrieval của agent ở Day 09 cũng ổn định hơn.

---

## 6. Rủi ro còn lại & việc chưa làm

- Chưa có alert real-time; hiện nhóm mới dừng ở log, manifest và runbook vận hành.
- Chưa có dashboard tổng hợp trend theo `run_id` cho các reason trong quarantine.
- Chưa benchmark retrieval trên tập câu hỏi lớn hơn bộ câu hỏi nhỏ dùng trong lab.
- Chưa làm incremental ingest; hiện mỗi run vẫn xử lý lại toàn bộ raw snapshot.
- Có thể bổ sung semantic deduplication và script diff eval tự động để phát hiện regression nhanh hơn.
