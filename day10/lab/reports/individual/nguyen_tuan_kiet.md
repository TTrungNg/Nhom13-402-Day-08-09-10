# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Nguyễn Tuấn Kiệt  
**Vai trò:** Monitoring Owner  
**Ngày nộp:** 15/04/2026  
**Độ dài yêu cầu:** **400–650 từ** (ngắn hơn Day 09 vì rubric slide cá nhân ~10% — vẫn phải đủ bằng chứng)

---

> Viết **"tôi"**, đính kèm **run_id**, **tên file**, **đoạn log** hoặc **dòng CSV** thật.  
> Nếu làm phần clean/expectation: nêu **một số liệu thay đổi** (vd `quarantine_records`, `hits_forbidden`, `top1_doc_expected`) khớp bảng `metric_impact` của nhóm.  
> Lưu: `reports/individual/[ten_ban].md`

---

## 1. Tôi phụ trách phần nào? (80–120 từ)

**File / module:**

- `monitoring/freshness_check.py`
- `docs/runbook.md` (mục Detection/Monitoring)

**Kết nối với thành viên khác:**

Tôi phối hợp với các thành viên trong nhóm để đảm bảo rằng các lỗi liên quan đến freshness SLA được phát hiện và xử lý kịp thời. Các thông tin từ `freshness_check.py` được tích hợp vào pipeline tổng thể, và tôi đã làm việc với nhóm để đảm bảo rằng các log và manifest được ghi nhận đầy đủ.

**Bằng chứng (commit / comment trong code):**

- Commit hoàn thiện `freshness_check.py` với logic SLA và log chi tiết.
- Đóng góp vào `runbook.md` với các bước Detection và Monitoring.

---

## 2. Một quyết định kỹ thuật (100–150 từ)

Tôi đã quyết định sử dụng chiến lược SLA đơn giản dựa trên `latest_exported_at` trong manifest để kiểm tra freshness. Thay vì chỉ dừng ở mức cảnh báo (WARN), tôi đã thêm logic để phân biệt rõ giữa `WARN` và `FAIL`, giúp nhóm dễ dàng ưu tiên xử lý các lỗi nghiêm trọng. Ví dụ, nếu manifest không tồn tại hoặc không có timestamp hợp lệ, trạng thái sẽ là `FAIL`. Ngược lại, nếu timestamp tồn tại nhưng vượt quá SLA, trạng thái sẽ là `WARN`. Quyết định này giúp giảm thiểu false positive và đảm bảo rằng pipeline chỉ dừng lại khi thực sự cần thiết. Tôi cũng đảm bảo rằng các log chi tiết (vd: `age_hours`, `sla_hours`) được ghi lại để hỗ trợ debug.

---

## 3. Một lỗi hoặc anomaly đã xử lý (100–150 từ)

Triệu chứng: Freshness check trả về `FAIL` do manifest thiếu trường `latest_exported_at`.  
Phát hiện: Lỗi này được phát hiện thông qua log `reason: no_timestamp_in_manifest` trong `artifacts/logs/run_<run_id>.log`.  
Xử lý: Tôi đã cập nhật `freshness_check.py` để thêm logic kiểm tra `run_timestamp` như một fallback khi `latest_exported_at` không tồn tại. Sau khi sửa, tôi chạy lại pipeline với manifest mới và xác nhận rằng lỗi không còn xuất hiện.  
Kết quả: Freshness check chuyển từ `FAIL` sang `PASS`, và log chi tiết đã ghi nhận timestamp hợp lệ.

---

## 4. Bằng chứng trước / sau (80–120 từ)

**Run ID:** `hotfix-refund`  
**File:** `artifacts/eval/before_after_eval.csv`  

Trước sửa lỗi:
```
hits_forbidden,contains_expected
yes,no
```
Sau sửa lỗi:
```
hits_forbidden,contains_expected
no,yes
```

---

## 5. Cải tiến tiếp theo (40–80 từ)

Nếu có thêm 2 giờ, tôi sẽ mở rộng `freshness_check.py` để kiểm tra thêm watermark từ database, giúp phát hiện các lỗi liên quan đến đồng bộ dữ liệu giữa các nguồn. Điều này sẽ tăng độ chính xác của freshness check và giảm thiểu các lỗi tiềm ẩn trong pipeline.
