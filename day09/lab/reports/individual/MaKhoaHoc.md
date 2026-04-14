# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Mã Khoa Học  
**Vai trò trong nhóm:** MCP Owner  
**Ngày nộp:** 14/04/2026  
**Độ dài:** ~650 từ

---

## 1. Tôi phụ trách phần nào? (100–150 từ)

Trong lab này, tôi phụ trách nâng cấp file `lab/mcp_server.py`. Trọng tâm của tôi là nâng phần retrieval trong MCP server từ mức "delegate sang worker" lên mức server tự truy vấn vector store. Cụ thể, tôi thêm các hàm `_get_embedding_fn`, `_get_collection`, `_ensure_docs_indexed`, `_distance_to_score` và sửa `tool_search_kb` để query ChromaDB trực tiếp. Bên cạnh đó, tôi cũng bổ sung kiểm tra input cho `dispatch_tool` bằng `_validate_input_schema` và check kiểu dữ liệu `tool_input` trước khi gọi tool.

**Module/file tôi chịu trách nhiệm:**
- File chính: `lab/mcp_server.py`
- Functions tôi thêm/sửa: `_get_embedding_fn`, `_get_collection`, `_ensure_docs_indexed`, `_distance_to_score`, `tool_search_kb`, `_validate_input_schema`, `dispatch_tool`

**Cách công việc của tôi kết nối với phần của thành viên khác:**

Sau khi tôi sửa, worker/supervisor chỉ cần gọi tool qua MCP như cũ, nhưng chất lượng retrieval và khả năng bắt lỗi input tốt hơn, giảm phụ thuộc vào `workers/retrieval.py`.

**Bằng chứng (commit hash, file có comment tên bạn, v.v.):**

Bằng chứng nằm ngay trong diff thực tế `mcp_server.py`: thêm import `hashlib`, `Path`, `load_dotenv`; thêm cụm helper cho embedding/indexing; và thay logic trong `tool_search_kb` + `dispatch_tool`.

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (150–200 từ)

**Quyết định:** Tôi quyết định chuyển `tool_search_kb` từ cách gọi `retrieve_dense` (delegate retrieval worker) sang truy vấn ChromaDB trực tiếp ngay trong MCP server.

**Lý do:**

Ở bản gốc `mcp_server.py`, `tool_search_kb` import `workers.retrieval` và gọi `retrieve_dense(query, top_k=top_k)`. Cách này hoạt động nhanh để demo, nhưng MCP server vẫn phụ thuộc vào module ngoài nên khó đóng gói độc lập và khó kiểm soát fallback khi môi trường thiếu dependency. Ở bản mới `mcp_server.py`, tôi gom retrieval vào cùng một lớp MCP bằng chuỗi xử lý rõ ràng: lấy embedding (`_get_embedding_fn`) -> mở collection (`_get_collection`) -> index tài liệu khi rỗng (`_ensure_docs_indexed`) -> query -> chuẩn hóa score bằng `_distance_to_score`. Cách này giúp server tự chủ hơn, phản ánh đúng vai trò "tool provider" của MCP.

**Trade-off đã chấp nhận:**

Trade-off là file `mcp_server.py` dài và phức tạp hơn bản gốc, đồng thời có thêm dependency runtime (SentenceTransformers/OpenAI/ChromaDB). Tôi chấp nhận điều này để đổi lấy khả năng chạy retrieval trực tiếp và rõ ràng hơn khi debug.

**Bằng chứng từ trace/code:**

```python
# mcp_server.py (gốc)
from workers.retrieval import retrieve_dense
chunks = retrieve_dense(query, top_k=top_k)

# mcp_server.py (đã sửa)
embed = _get_embedding_fn()
collection = _get_collection()
_ensure_docs_indexed(collection, embed)
results = collection.query(
    query_embeddings=[embed(query)],
    n_results=top_k,
    include=["documents", "distances", "metadatas"],
)
```

---

## 3. Tôi đã sửa một lỗi gì? (150–200 từ)

**Lỗi:** Thiếu validation input ở boundary của `dispatch_tool`, dễ gây lỗi gọi hàm khi payload từ client không đúng kiểu hoặc thiếu trường bắt buộc.

**Symptom (pipeline làm gì sai?):**

Ở bản gốc, `dispatch_tool` gọi thẳng `tool_fn(**tool_input)` mà chưa kiểm tra `tool_input` có phải dict không, cũng chưa kiểm tra required fields theo schema. Nếu payload sai format, hệ thống báo `TypeError` muộn và thông điệp khó thống nhất giữa các tool.

**Root cause (lỗi nằm ở đâu — indexing, routing, contract, worker logic?):**

Root cause nằm ở contract layer giữa client/worker và MCP server: schema đã khai báo trong `TOOL_SCHEMAS` nhưng chưa được dùng để validate trước khi execute.

**Cách sửa:**

Tôi thêm hàm `_validate_input_schema` để kiểm tra required fields theo từng tool; thêm check `isinstance(tool_input, dict)` trong `dispatch_tool`; và trả về `schema` ngay trong response lỗi để client biết cách sửa payload. Điều này biến lỗi "runtime không rõ nguyên nhân" thành lỗi contract rõ ràng, nhất quán.

**Bằng chứng trước/sau:**
> Dán trace/log/output trước khi sửa và sau khi sửa.

Trước sửa (`mcp_server.py`): chưa có `_validate_input_schema`, không có check kiểu `tool_input`.  
Sau sửa (`mcp_server.py`): có đủ 2 lớp guard trước khi execute:
- Check `tool_input must be a JSON object (dict)`.
- Check thiếu trường bắt buộc qua `_validate_input_schema`.

---

## 4. Tôi tự đánh giá đóng góp của mình (100–150 từ)

**Tôi làm tốt nhất ở điểm nào?**

Tôi làm tốt ở việc nâng cấp từ bản mock đơn giản sang bản MCP server có retrieval thực tế hơn và có lớp validation rõ ràng. Sự khác biệt giữa `mcp_server.py`cũ và `mcp_server.py`mới cho thấy tôi không chỉ thêm chức năng mà còn củng cố contract của hệ thống.

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**

Tôi chưa tối ưu hóa đầy đủ cho production: validation mới dừng ở required fields, chưa validate sâu kiểu dữ liệu/enum theo JSON Schema; ngoài ra fallback random embedding chỉ phù hợp test.

**Nhóm phụ thuộc vào tôi ở đâu?** _(Phần nào của hệ thống bị block nếu tôi chưa xong?)_

Nếu tôi chưa xong phần này, luồng gọi tool retrieval dễ bị phụ thuộc worker cũ và lỗi input từ worker khó truy vết, ảnh hưởng tốc độ tích hợp supervisor-worker.

**Phần tôi phụ thuộc vào thành viên khác:** _(Tôi cần gì từ ai để tiếp tục được?)_

Tôi cần thành viên phụ trách worker/supervisor gửi các payload thực tế để tôi kiểm thử các case sai input, và cần trace owner cung cấp các trace lỗi để tôi hoàn thiện validation.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50–100 từ)

Tôi sẽ nâng `_validate_input_schema` thành validation đầy đủ type/enum/default theo `TOOL_SCHEMAS`, vì diff hiện tại cho thấy tôi mới giải quyết lớp lỗi "thiếu field" và "sai kiểu tổng quát". Cải tiến này giúp `dispatch_tool` trả lỗi chính xác hơn (ví dụ `access_level` phải là integer, `priority` phải thuộc enum), giảm lỗi vòng lặp khi worker gọi tool sai format.

---

*Gợi ý cuối: bạn chỉ cần điền tên thật vào dòng "Họ và tên" trước khi nộp.*
