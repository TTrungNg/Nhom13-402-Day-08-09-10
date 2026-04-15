# Báo Cáo Nhóm — Lab Day 10: Data Pipeline & Data Observability

**Tên nhóm:** aicb_day10_team  
**Thành viên:**
| Tên | Vai trò (Day 10) | Email |
|-----|------------------|-------|
| ___ | Ingestion / Raw Owner | ___ |
| ___ | Cleaning & Quality Owner | ___ |
| ___ | Embed & Idempotency Owner | ___ |
| ___ | Monitoring / Docs Owner | ___ |

**Ngày nộp:** 2026-04-15  
**Repo:** day10/lab  
**Độ dài khuyến nghị:** 600–1000 từ

---

> **Nộp tại:** `reports/group_report.md`  
> **Deadline commit:** xem `SCORING.md` (code/trace sớm; report có thể muộn hơn nếu được phép).  
> Phải có **run_id**, **đường dẫn artifact**, và **bằng chứng before/after** (CSV eval hoặc screenshot).

---

## 1. Pipeline tổng quan (150–200 từ)

> Nguồn raw là gì (CSV mẫu / export thật)? Chuỗi lệnh chạy end-to-end? `run_id` lấy ở đâu trong log?

**Tóm tắt luồng:**

Pipeline đọc `data/raw/policy_export_dirty.csv`, áp rule clean để chuẩn hoá schema và tách quarantine, sau đó chạy expectation suite để quyết định halt/warn trước khi embed lên Chroma. Mỗi lần chạy có `run_id` để trace toàn bộ artifact (`cleaned`, `quarantine`, `manifest`, `log`). Embed sử dụng `upsert(chunk_id)` và prune id không còn trong cleaned để đảm bảo index phản ánh đúng trạng thái publish gần nhất.

**Lệnh chạy một dòng (copy từ README thực tế của nhóm):**

`python etl_pipeline.py run --run-id sprint4-good`

---

## 2. Cleaning & expectation (150–200 từ)

> Baseline đã có nhiều rule (allowlist, ngày ISO, HR stale, refund, dedupe…). Nhóm thêm **≥3 rule mới** + **≥2 expectation mới**. Khai báo expectation nào **halt**.

### 2a. Bảng metric_impact (bắt buộc — chống trivial)

| Rule / Expectation mới (tên ngắn) | Trước (số liệu) | Sau / khi inject (số liệu) | Chứng cứ (log / CSV / commit) |
|-----------------------------------|------------------|-----------------------------|-------------------------------|
| Rule `invalid_exported_at` quarantine | `run_sprint2`: `raw=10`, `quarantine=4` | `run_sprint2-inject`: `raw=13`, `quarantine=6`; có `reason=invalid_exported_at` | `artifacts/quarantine/quarantine_sprint2-inject.csv` |
| Rule `chunk_text_too_short` quarantine | Chưa có record ngắn để kích hoạt | Inject có `reason=chunk_text_too_short` (`chunk_text=ok`) | `artifacts/quarantine/quarantine_sprint2-inject.csv` |
| Rule normalize BOM/zero-width | Chưa có dòng BOM trong raw mẫu | Inject thêm dòng BOM và vào cleaned dưới dạng text chuẩn, không còn ký tự lạ | `artifacts/cleaned/cleaned_sprint2-inject.csv` |
| Expectation `no_empty_exported_at` | Trước khi thêm expectation chưa có check bắt buộc | Sau khi thêm: `empty_exported_at=0` ở cả run chuẩn/inject; chứng minh clean đã chặn record lỗi trước validate | `artifacts/logs/run_sprint2.log`, `run_sprint2-inject.log` |
| Expectation `chunk_id_unique` | Trước khi thêm expectation chưa có assert uniqueness | Sau khi thêm: `duplicate_chunk_id=0`; kiểm soát an toàn cho upsert idempotent | `artifacts/logs/run_sprint2.log`, `run_sprint2-inject.log` |

**Rule chính (baseline + mở rộng):**

- Allowlist `doc_id`, normalize `effective_date`, quarantine HR cũ, dedupe theo normalized chunk.
- Fix stale refund 14→7 (trừ khi bật inject `--no-refund-fix`).
- Mở rộng: normalize BOM/zero-width, quarantine `invalid_exported_at`, quarantine `chunk_text_too_short`.

**Ví dụ 1 lần expectation fail (nếu có) và cách xử lý:**

Run inject (`--no-refund-fix --skip-validate`) làm `refund_no_stale_14d_window` fail có chủ đích. Sau đó chạy lại pipeline chuẩn để expectation pass và refresh index snapshot.

---

## 3. Before / after ảnh hưởng retrieval hoặc agent (200–250 từ)

> Bắt buộc: inject corruption (Sprint 3) — mô tả + dẫn `artifacts/eval/…` hoặc log.

**Kịch bản inject:**

Chạy `python etl_pipeline.py run --run-id inject-bad --no-refund-fix --skip-validate`, sau đó eval để quan sát top-k chứa ngữ cảnh stale về refund.

**Kết quả định lượng (từ CSV / bảng):**

`artifacts/eval/after_inject_bad.csv` cho thấy quality retrieval giảm (xuất hiện context cũ), và `artifacts/eval/before_after_eval.csv` sau khi rerun chuẩn cho thấy `contains_expected=yes`, `hits_forbidden=no` ở các câu chính.

---

## 4. Freshness & monitoring (100–150 từ)

SLA chọn 24h tại boundary publish. Với dữ liệu lab mẫu (`latest_exported_at` cũ), freshness thường `FAIL` là đúng theo contract. Nếu môi trường demo dùng snapshot cũ, nhóm chấp nhận FAIL có giải thích trong runbook; khi có export mới thì kỳ vọng PASS.
Nhóm kiểm tra freshness bằng lệnh `python etl_pipeline.py freshness --manifest ...` sau mỗi run quan trọng (sprint2, inject-bad, sprint3-fix). Trường `latest_exported_at` lấy từ cleaned snapshot trong manifest giúp tách bạch lỗi dữ liệu stale với lỗi pipeline runtime. Trong lab này, pipeline vẫn `PIPELINE_OK` dù freshness `FAIL`, vì đây là cảnh báo chất lượng dữ liệu theo SLA chứ không phải crash hệ thống. Hướng vận hành: nếu `FAIL` ở môi trường thật thì yêu cầu refresh export hoặc tăng tần suất ingest; nếu chỉ demo với snapshot cũ thì phải ghi chú rõ trong runbook để tránh hiểu nhầm kết quả.

---

## 5. Liên hệ Day 09 (50–100 từ)

Có. Day 09 có thể dùng trực tiếp collection `day10_kb` để truy xuất knowledge đã qua clean/validate của Day 10. Việc tách pipeline giúp giảm lỗi “trả lời đúng ngôn ngữ nhưng sai version data”.
Trong thực tế nhóm chạy Sprint 3 theo vòng inject rồi fix để chứng minh tầng dữ liệu ảnh hưởng trực tiếp tới retrieval quality của agent. Khi chuyển sang Day 09, chỉ cần trỏ retriever vào collection đã publish bởi Day 10 là có thể tái sử dụng kết quả clean/quality mà không đổi flow orchestration.

---

## 6. Rủi ro còn lại & việc chưa làm

- Chưa có alert real-time (mới log local và manifest check).
- Chưa benchmark retrieval trên tập câu hỏi lớn hơn 3 câu golden.
