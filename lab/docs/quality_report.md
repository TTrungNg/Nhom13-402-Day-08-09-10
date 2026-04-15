# Quality report — Lab Day 10 (nhóm)

**run_id before (inject):** inject-bad  
**run_id after (fix):** sprint3-fix  
**Ngày:** 2026-04-15

---

## 1. Tóm tắt số liệu

| Chỉ số | Trước (inject-bad) | Sau (sprint3-fix) | Ghi chú |
|--------|---------------------|----------------------|---------|
| raw_records | 10 | 10 | Cùng 1 raw export mẫu |
| cleaned_records | 6 | 6 | Rule clean ổn định giữa các lần run |
| quarantine_records | 4 | 4 | Chủ yếu do duplicate/missing/unknown/stale |
| Expectation halt? | Có (`refund_no_stale_14d_window`) | Không | Inject bật `--no-refund-fix --skip-validate` |
| embed_prune_removed | 2 | 1 | Thể hiện snapshot index được cập nhật giữa 2 run |

---

## 2. Before / after retrieval (bắt buộc)

**Nguồn chứng cứ:**  
- `artifacts/eval/after_inject_bad.csv`  
- `artifacts/eval/before_after_eval.csv`

**Câu hỏi then chốt:** refund window (`q_refund_window`)  
**Trước (inject):** `contains_expected=yes`, nhưng `hits_forbidden=yes` trong `after_inject_bad.csv` (top-k vẫn dính chunk stale).  
**Sau (fix):** `contains_expected=yes` và `hits_forbidden=no` trong `before_after_eval.csv`.

**Merit (khuyến nghị):** versioning HR — `q_leave_version` (`contains_expected`, `hits_forbidden`, `top1_doc_expected`)  
**Trước:** `contains_expected=yes`, `hits_forbidden=no`, `top1_doc_expected=yes`.  
**Sau:** giữ ổn định `contains_expected=yes`, `hits_forbidden=no`, `top1_doc_expected=yes`.

---

## 3. Freshness & monitor

`freshness_check=FAIL` trên dataset lab mẫu vì `latest_exported_at` cũ hơn SLA 24h. Đây là fail đúng theo contract (không phải pipeline crash). Với dữ liệu production hoặc export mới hơn, kỳ vọng PASS khi age <= SLA.

---

## 4. Corruption inject (Sprint 3)

Inject dùng lệnh:

`python etl_pipeline.py run --run-id inject-bad --no-refund-fix --skip-validate`

Mục tiêu: cố ý bỏ rule fix refund để expectation phát hiện stale policy; vẫn embed để đo ảnh hưởng retrieval trước khi khôi phục. Kết quả log `run_inject-bad.log` ghi `refund_no_stale_14d_window FAIL (violations=1)` và vẫn `PIPELINE_OK` do bật `--skip-validate`.

---

## 5. Hạn chế & việc chưa làm

- Chưa tích hợp dashboard theo dõi freshness/expectation theo thời gian.
- Chưa mở rộng eval set > 3 câu hỏi golden cho nhiều phân đoạn nghiệp vụ.
