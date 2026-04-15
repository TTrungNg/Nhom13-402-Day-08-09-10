# Runbook — Lab Day 10 (incident tối giản)

---

## Symptom

- Agent trả lời sai “hoàn tiền trong 14 ngày” thay vì 7 ngày.
- Freshness trên manifest báo `FAIL` hoặc expectation `refund_no_stale_14d_window` fail.
- Retrieval kết quả `hits_forbidden=yes` ở câu `q_refund_window`.

---

## Detection

- `expectation[refund_no_stale_14d_window] FAIL` trong `artifacts/logs/run_<run_id>.log`.
- `artifacts/eval/*.csv` có `hits_forbidden=yes`.
- `freshness_check=FAIL` trong log hoặc `python etl_pipeline.py freshness --manifest ...` trả về FAIL.
- Evidence gần nhất của nhóm: `run_inject-bad.log` (FAIL có chủ đích) và `run_sprint3-fix.log` (đã pass lại).

---

## Diagnosis

| Bước | Việc làm | Kết quả mong đợi |
|------|----------|------------------|
| 1 | Kiểm tra `artifacts/manifests/*.json` | Xác định run gần nhất, `latest_exported_at`, cờ `no_refund_fix` |
| 2 | Mở `artifacts/quarantine/*.csv` | Kiểm tra lý do loại record (`duplicate`, `unknown_doc_id`, `invalid_exported_at`) |
| 3 | Chạy `python eval_retrieval.py --out artifacts/eval/recheck.csv` | Xác nhận `contains_expected=yes`, `hits_forbidden=no` |

---

## Mitigation

- Chạy lại pipeline chuẩn: `python etl_pipeline.py run --run-id hotfix-refund` (không dùng `--skip-validate`).
- Nếu vừa chạy inject demo, rerun bản chuẩn để overwrite index snapshot.
- Nếu freshness `FAIL` do data snapshot cũ, nới SLA theo bối cảnh lab hoặc cập nhật export mới trước khi publish.
- Sau mitigation, chạy lại eval: `python eval_retrieval.py --out artifacts/eval/before_after_eval.csv` để xác nhận `hits_forbidden=no` cho `q_refund_window`.

---

## Prevention

- Duy trì expectation halt cho refund stale + exported_at rỗng.
- Gắn owner và alert channel trong `contracts/data_contract.yaml`.
- Giữ pipeline ở chế độ idempotent (upsert + prune) để tránh stale chunk còn nằm trong top-k.
