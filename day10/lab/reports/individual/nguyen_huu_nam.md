# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Nguyễn Hữu Nam  
**Vai trò:** Docs Owner
**Ngày nộp:** Nguyễn Hữu Nam  
**Độ dài yêu cầu:** **400–650 từ** (ngắn hơn Day 09 vì rubric slide cá nhân ~10% — vẫn phải đủ bằng chứng)

---

> Viết **"tôi"**, đính kèm **run_id**, **tên file**, **đoạn log** hoặc **dòng CSV** thật.  
> Nếu làm phần clean/expectation: nêu **một số liệu thay đổi** (vd `quarantine_records`, `hits_forbidden`, `top1_doc_expected`) khớp bảng `metric_impact` của nhóm.  
> Lưu: `reports/individual/[ten_ban].md`

---

## 1. Tôi phụ trách phần nào? (80–120 từ)

**File / module:**

- docs/pipeline_architecture.md 
- docs/data_contract.md 
- docs/quality_report.md

**Kết nối với thành viên khác:**

Tôi chịu trách nhiệm mô tả kiến trúc pipeline, định nghĩa data contract (source map, rule, expectation) và tổng hợp quality report dựa trên kết quả chạy ETL. Tôi làm việc chặt chẽ với thành viên phụ trách ETL implementation để đảm bảo các rule/expectation được mô tả đúng với code thực tế. Đồng thời, tôi phối hợp với người phụ trách evaluation để thu thập số liệu before/after, log và kết quả retrieval, từ đó chứng minh tác động của việc clean data trong quality report.

**Bằng chứng (commit / comment trong code):**

05a1c927a045f15383116d103adcec8bb10ff511

---

## 2. Một quyết định kỹ thuật (100–150 từ)

> VD: chọn halt vs warn, chiến lược idempotency, cách đo freshness, format quarantine.

Tôi chọn chiến lược không halt pipeline khi expectation fail, mà chỉ log và cảnh báo (warn). Lý do là trong bối cảnh dữ liệu thực tế có thể luôn tồn tại một mức độ lỗi nhất định, việc halt toàn bộ pipeline sẽ làm gián đoạn hệ thống downstream như embedding hoặc retrieval. Thay vào đó, tôi sử dụng quarantine để tách dữ liệu lỗi ra và vẫn cho phép pipeline tiếp tục với phần dữ liệu sạch. Đồng thời, các expectation được dùng để theo dõi chất lượng dữ liệu qua metric (ví dụ: null rate, invalid date rate), giúp phát hiện xu hướng xấu mà không ảnh hưởng đến tính sẵn sàng của hệ thống.

---

## 3. Một lỗi hoặc anomaly đã xử lý (100–150 từ)

> Mô tả triệu chứng → metric/check nào phát hiện → fix.

Một anomaly là các chunk có nội dung quá ngắn hoặc không đủ thông tin (ví dụ text rỗng hoặc rất ngắn), gây nhiễu retrieval. Triệu chứng là kết quả trả về thiếu context hoặc không liên quan. Tôi thêm rule yêu cầu chunk_text phải có độ dài tối thiểu 20 ký tự. Vấn đề được phát hiện qua kiểm tra phân phối độ dài và quan sát retrieval kém chất lượng. Sau khi áp dụng rule, các chunk ngắn bị loại hoặc đưa vào quarantine, giúp cải thiện độ liên quan của kết quả và giảm nhiễu trong hệ thống.

---

## 4. Bằng chứng trước / sau (80–120 từ)

> Dán ngắn 2 dòng từ `before_after_eval.csv` hoặc tương đương; ghi rõ `run_id`.

Before: q_refund_window → contains_expected=yes, hits_forbidden=no
After inject: q_refund_window → contains_expected=yes, hits_forbidden=yes

Kết quả cho thấy sau khi inject dữ liệu lỗi, hệ thống vẫn tìm đúng thông tin (7 ngày) nhưng đồng thời cũng retrieve cả thông tin sai (14 ngày), thể hiện qua hits_forbidden=yes. Điều này chứng minh retrieval bị nhiễu khi data bẩn. Sau khi áp dụng các rule clean (fix refund, dedupe, min length), hits_forbidden được loại bỏ và kết quả trở nên nhất quán hơn.

---

## 5. Cải tiến tiếp theo (40–80 từ)

> Nếu có thêm 2 giờ — một việc cụ thể (không chung chung).

Nếu có thêm thời gian, tôi sẽ thêm semantic deduplication (dựa trên embedding similarity) thay vì chỉ so khớp text exact. Điều này giúp loại bỏ các chunk gần giống nhau nhưng khác wording, từ đó giảm nhiễu retrieval và cải thiện độ nhất quán của kết quả.
