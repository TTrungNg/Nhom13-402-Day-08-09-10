# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Mã Khoa Học
**Vai trò:** Embed Owner  
**Ngày nộp:** 2026-04-15  
**Độ dài yêu cầu:** 400–650 từ

---

## 1. Tôi phụ trách phần nào? (80–120 từ)

Tôi phụ trách phần embed và phần đo kết quả retrieval sau khi publish dữ liệu. Mục tiêu của tôi là đảm bảo dữ liệu trong Chroma luôn là bản mới nhất, không bị lẫn dữ liệu cũ sau khi chạy lại pipeline. Tôi làm chính ở 3 file: `etl_pipeline.py` (embed + manifest), `eval_retrieval.py` (xuất file so sánh before/after), và `grading_run.py` (xuất file JSONL để chấm). Tôi làm việc cùng bạn Cleaning/Quality để chọn các run cần so sánh (`inject-bad`, `sprint3-fix`) và gửi kết quả cho bạn phụ trách docs để đưa vào báo cáo nhóm.

**File / module:**

- `etl_pipeline.py` (embed upsert/prune + manifest fields)
- `eval_retrieval.py`
- `grading_run.py`

**Kết nối với thành viên khác:**

Tôi nhận cleaned output từ owner Cleaning/Quality, sau đó chạy embed và eval để cung cấp evidence định lượng cho owner Monitoring/Docs.

**Bằng chứng (commit / comment trong code):**

Luồng embed trong log có các dòng `embed_prune_removed=...` và `embed_upsert count=...`; eval có `after_inject_bad.csv` và `before_after_eval.csv`.

---

## 2. Một quyết định kỹ thuật (100–150 từ)

Quyết định quan trọng nhất của tôi là dùng cách embed theo “snapshot mới nhất”, không cộng dồn mù quáng. Cụ thể: trước khi upsert, pipeline sẽ tìm các `chunk_id` cũ không còn trong file cleaned hiện tại và xóa chúng (`embed_prune_removed`). Sau đó mới chạy `upsert`. Cách này giúp tránh việc dữ liệu cũ vẫn nằm trong top-k dù nhóm đã sửa dữ liệu ở run mới. Nếu chỉ upsert mà không prune, run sửa lỗi có thể vẫn trả ra context stale từ run inject trước đó. Vì bài lab yêu cầu chứng minh before/after rõ ràng, cách làm này giúp kết quả eval phản ánh đúng chất lượng dữ liệu ở thời điểm publish.

---

## 3. Một lỗi hoặc anomaly đã xử lý (100–150 từ)

Lỗi tôi gặp là khi chạy `grading_run.py` thì script báo thiếu file `data/grading_questions.json` và dừng luôn. Kết quả là không tạo được `artifacts/eval/grading_run.jsonl`. Tôi phát hiện lỗi này khi chạy chuỗi lệnh cuối sprint: eval chạy được nhưng đến grading thì fail. Cách xử lý của tôi là sửa `grading_run.py` để có fallback: nếu chưa có file grading chính thức thì dùng tạm `data/test_questions.json` và in cảnh báo cho người chạy biết. Sau khi sửa, lệnh `python grading_run.py --out artifacts/eval/grading_run.jsonl` chạy thành công. Nhờ đó nhóm vẫn test được full luồng trước thời điểm giảng viên public bộ câu grading.

---

## 4. Bằng chứng trước / sau (80–120 từ)

Ở run inject `run_id=inject-bad`, log có dòng `refund_no_stale_14d_window FAIL ... violations=1`, nhưng pipeline vẫn embed vì dùng `--skip-validate`. Log cũng có `embed_prune_removed=2` và `embed_upsert count=6`. Trong file `artifacts/eval/after_inject_bad.csv`, câu `q_refund_window` có `contains_expected=yes` và `top1_doc_id=policy_refund_v4`, nhưng `hits_forbidden=yes`. Nghĩa là top1 nhìn vẫn đúng, nhưng trong toàn bộ top-k vẫn còn chunk stale nên kết quả chưa an toàn.

Sau khi chạy lại bản chuẩn `run_id=sprint3-fix`, log cho thấy expectation đã pass lại và embed vẫn ổn định (`embed_prune_removed=1`, `embed_upsert count=6`). Trong `artifacts/eval/before_after_eval.csv`, câu `q_refund_window` giữ `contains_expected=yes` nhưng chuyển từ `hits_forbidden=yes` sang `hits_forbidden=no`. Đây là bằng chứng trực tiếp rằng bước fix đã làm sạch ngữ cảnh retrieval trong top-k.


---

## 5. Cải tiến tiếp theo (40–80 từ)

Nếu có thêm 2 giờ, tôi sẽ viết một script nhỏ để so sánh tự động hai file eval (inject và fix), rồi in ra các câu hỏi bị xấu đi. Nhờ vậy nhóm sẽ phát hiện regression nhanh hơn, không cần mở CSV kiểm tra thủ công từng dòng.
