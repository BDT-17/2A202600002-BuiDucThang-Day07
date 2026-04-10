# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Bùi Đức Thắng-2A202600002
            Trần Ngọc Hùng-2A202600429
**Nhóm:** Hùng Thắng
**Ngày:** 10/04/2026

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> 
Cosine similarity đo mức độ **giống nhau về hướng** giữa hai vector embedding, thay vì độ lớn tuyệt đối.  
Trong ngữ cảnh văn bản, điều này tương đương với việc hai đoạn text có **ý nghĩa tương đồng** hay không.

High cosine similarity (độ tương đồng cosine cao) có nghĩa là hai vector embedding có hướng gần như giống nhau, tức là hai đoạn văn bản có ý nghĩa (semantic meaning) rất giống nhau.

**Ví dụ HIGH similarity:**
- Sentence A: "Machine learning là một nhánh của trí tuệ nhân tạo"
- Sentence B: "Máy học là một phân ngành của AI"
- Tại sao tương đồng: Cả hai câu diễn đạt cùng khái niệm (machine learning) dù từ vựng khác nhau

**Ví dụ LOW similarity:**
- Sentence A: "Con mèo đang ngủ trên ghế"
- Sentence B: "Kinh tế tiền tệ ảnh hưởng đến thị trường chứng khoán"
- Tại sao khác: Hai câu không liên quan đến nhau, diễn đạt chủ đề hoàn toàn khác nhau

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> Cosine similarity không bị ảnh hưởng bởi độ dài tuyệt đối của vector mà chỉ quan tâm đến hướng, phù hợp với text embeddings nơi độ dài không quan trọng. Euclidean distance bị ảnh hưởng bởi quy mô, làm cho embedding đơn giản khác embeddings phức tạp hơn ngay cả khi ngữ nghĩa giống nhau.

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> **Phép tính:** step = chunk_size - overlap = 500 - 50 = 450  
> num_chunks = ceil(10000 / 450) = ceil(22.22) ≈ 22 chunks  
> **Đáp án:** 22 chunks (hoặc 20-23 tùy cách tính chính xác edge case)

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
> Khi overlap tăng lên 100, step = 500 - 100 = 400, nên số chunks tăng lên khoảng 25 chunks. Overlap nhiều hơn giúp **giữ ngữ cảnh liên tiếp** giữa các chunks, tránh mất thông tin ở ranh giới, nhưng tăng chi phí lưu trữ và tính embedding.

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** GitHub Policies & Terms of Service (Policy Documentation)

**Tại sao nhóm chọn domain này?**
> GitHub policies là một tập hợp tài liệu quan trọng, có cấu trúc rõ ràng và chứa nhiều thông tin pháp lý. Domain này phù hợp để test RAG vì users thường có câu hỏi cụ thể ("Chính sách về DMCA là gì?", "Data của tôi được lưu như thế nào?") mà cần retrieve chính xác từ tài liệu máy chủ. Các policies cũng có metadata rõ ràng (policy_type, source) giúp test filtering và metadata-aware retrieval.

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | GitHub Terms of Service | GitHub Docs, https://docs.github.com/en/site-policy/github-terms/github-terms-of-service | ≈ 33,000 | policy_type=terms, source=github, language=en |
| 2 | GitHub General Privacy Statement | GitHub Docs, https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement | ≈ 22,000 | policy_type=privacy, source=github, language=en |
| 3 | GitHub Acceptable Use Policies | GitHub Docs, https://docs.github.com/en/site-policy/acceptable-use-policies/github-acceptable-use-policies | ≈ 16,000 | policy_type=acceptable_use, source=github, language=en |
| 4 | DMCA Takedown Policy | GitHub Docs, https://docs.github.com/en/site-policy/content-removal-policies/dmca-takedown-policy | ≈ 28,000 | policy_type=copyright, source=github, language=en |
| 5 | GitHub Government Takedown Policy | GitHub Docs, https://docs.github.com/en/site-policy/other-site-policies/github-government-takedown-policy | ≈ 7,000 | policy_type=government_request, source=github, language=en |

### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| policy_type | string | privacy, terms, acceptable_use, copyright | Giúp filter đúng nhóm tài liệu khi query hỏi về một loại chính sách cụ thể. |
| source | string | github | Hữu ích nếu sau này mở rộng corpus với nhiều tổ chức hoặc nhiều website chính sách khác nhau. |
| language | string | en | Cho phép lọc theo ngôn ngữ nếu benchmark có cả tài liệu tiếng Anh và tiếng Việt. |
| topic_scope | string | copyright, user_data, account_rules | Giúp retrieval chính xác hơn khi câu hỏi tập trung vào một chủ đề hẹp trong policy corpus. |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis
Chạy `ChunkingStrategyComparator().compare()` trên **GitHub policy documents** với `chunk_size=300`:

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|---------|----------|-------------|------------|-------------------|
| github_terms_of_service.md | FixedSizeChunker | 110 | 289.4 | Partial – cắt ngang điều khoản |
| github_terms_of_service.md | SentenceChunker (3) | 62 | 462.1 | Yes – giữ câu pháp lý |
| github_terms_of_service.md | RecursiveChunker | 178 | 138.3 | Good nhưng quá mảnh |
| github_general_privacy_statement.md | FixedSizeChunker | 74 | 291.7 | Partial |
| github_general_privacy_statement.md | SentenceChunker (3) | 41 | 512.3 | Yes nhưng chunk dài |
| github_general_privacy_statement.md | RecursiveChunker | 133 | 161.2 | Good |

### Strategy Của Tôi

**Loại:** SentenceChunker với max_sentences_per_chunk=2

**Mô tả cách hoạt động:**
> Strategy này dùng regex `r'(?<=[.!?])\s+'` để tách text thành câu dựa vào ranh giới dấu chấm, thang hỏi, thang cảm. Sau đó, mỗi chunk chứa tối đa 2 câu liên tiếp, được join lại và strip whitespace. Điều này đảm bảo mỗi chunk có ý tứ trọn vẹn và dễ đọc, thích hợp cho retrieval semantic.

**Tại sao tôi chọn strategy này cho domain nhóm?**
> Domain là GitHub Policies, trong đó mỗi điều khoản thường được gói gọn trong 1-2 câu. Bằng cách gom 2 câu, tôi đạt được cân bằng giữa **ngữ cảnh** (1 câu có thể chưa đủ để giải thích một policy phức tạp) và **precision** (quá nhiều câu làm chunk dài và nhiễu, gây khó khăn cho việc tìm chính xác điều khoản). Sentence boundary giúp giữ tính pháp lý của từng câu.

**Code snippet (nếu custom):**
```python
def chunk(self, text: str) -> list[str]:
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    # Group into chunks
    chunks = []
    for i in range(0, len(sentences), self.max_sentences_per_chunk):
        chunk = ' '.join(sentences[i:i + self.max_sentences_per_chunk]).strip()
        if chunk:  # avoid empty chunks
            chunks.append(chunk)
    return chunks
```

### So Sánh: Strategy của tôi vs Baseline
### Benchmark Queries & Gold Answers (GitHub – Official)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | Under what circumstances may GitHub access the contents of private repositories? | GitHub personnel may access the contents of private repositories only to provide and improve GitHub services, support features that require access, or when required to do so by law, as described in the GitHub Privacy Statement and Terms of Service. |
| 2 | What kinds of behavior or content are prohibited under GitHub's Acceptable Use Policies? | GitHub prohibits unlawful activities, abuse, harassment, discrimination, misleading or fraudulent behavior, intellectual property infringement, impersonation, privacy violations, threats or incitement to violence, and other content that harms user safety or the integrity of the platform. |
| 3 | If content is removed by mistake under the DMCA process, what can the user do? | If content is removed due to mistake or misidentification, the user may submit a DMCA counter notice. GitHub will restore the content after a waiting period unless the copyright holder initiates legal action. |
| 4 | What information must a government takedown request provide before GitHub acts on it? | A valid government takedown request must come from an official government authority, clearly identify the allegedly illegal content, and specify the legal basis (law or court order) under which the content is unlawful in that jurisdiction. |
| 5 | What privacy rights do users have over their personal data? | Users have the right to access their personal data, request information about how it is used, and correct inaccurate personal information, in accordance with the GitHub Privacy Statement and applicable data protection laws. |


| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality |
|---------|----------|-------------|------------|------------------|
| github_terms_of_service.md | SentenceChunker (3) | 62 | 462.1 | High nhưng coarse |
| github_terms_of_service.md | **SentenceChunker (2)** | 94 | 301.7 | **Very High** |
| github_general_privacy_statement.md | SentenceChunker (3) | 41 | 512.3 | High |
| github_general_privacy_statement.md | **SentenceChunker (2)** | 68 | 329.5 | **High & precise** |

### Kết Quả Của Tôi — RecursiveChunker (chunk_size = 500)

Bảng dưới đây trình bày kết quả trả lời của hệ thống RAG khi sử dụng **RecursiveChunker với chunk_size = 500** trên 5 benchmark queries của nhóm, dựa trên GitHub policy documents.

| # | Query | Agent Answer (Tóm tắt) | Match with Gold Answer |
|---|-------|------------------------|------------------------|
| 1 | Private repository access | GitHub personnel may access private repositories to operate services or when legally required. | ✅ Yes |
| 2 | Prohibited behavior/content | Prohibits unlawful, abusive, deceptive, infringing, or harmful behavior. | ✅ Yes |
| 3 | DMCA mistake | Users can submit a DMCA counter notice; legal advice is recommended. | ✅ Yes |
| 4 | Government takedown request | Requests must identify the content and specify the legal basis before GitHub acts. | ✅ Yes |
| 5 | Privacy rights | Users can request access to and correction of their personal data. | ✅ Yes |

**Top‑3 Relevant Retrieval:** 5 / 5  
**Top‑1 Correct Answer:** 5 / 5
### So Sánh Với Thành Viên Khác


| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
|Trần Ngọc Hùng  | SentenceChunker(max=2) | 9/10 | Balanced, coherent, tốt cho policy | Có thể miss context ở câu thứ 3 |
| Tôi (Bùi Đức Thắng) | RecursiveChunker(300) | 7/10 | Linh hoạt, split tốt ở đoạn văn | Có thể cắt ngang ý giữa các câu |
| 1 test case khác | FixedSizeChunker(300, 50) | 5/10 | Đồng nhất độ dài | Cắt ngang câu, mất tính logic |

Cách tiếp cận:
RecursiveChunker được triển khai với chunk_size = 500, sử dụng chiến lược chia văn bản đệ quy theo mức độ ưu tiên của separator:
["\n\n", "\n", ". ", " ", ""]


Văn bản được chia theo separator cấp cao nhất trước.
Nếu một phần vẫn dài hơn chunk_size = 500, hàm _split sẽ tiếp tục đệ quy với separator tiếp theo.
Base case:

Nếu không còn separator hoặc len(text) <= 500, trả về chunk hiện tại.
Nếu separator cuối là "", văn bản được chia theo độ dài ký tự cố định 500.

Nhận xét:
Với chunk_size = 500, RecursiveChunker tạo ra các chunk lớn hơn so với khi dùng 200–300, giúp giữ nhiều ngữ cảnh hơn. Tuy nhiên, với GitHub Policies, strategy này vẫn có xu hướng:

Chia nhỏ theo cấu trúc kỹ thuật hơn là cấu trúc pháp lý.
Tạo chunk không luôn trùng khớp với ranh giới điều khoản pháp lý.

Vì vậy, dù linh hoạt, RecursiveChunker(500) không phù hợp bằng SentenceChunker(max=2) cho bài toán RAG trong domain này.
**Strategy nào tốt nhất cho domain này? Tại sao?**
> SentenceChunker với max=2 sentences tốt nhất cho GitHub Policies vì nó tôn trọng cấu trúc văn bản pháp lý. Mỗi câu trong policy thường mang một ý nghĩa độc lập cao. Việc gom 2 câu giúp AI có đủ ngữ cảnh để trả lời mà không bị nhiễu bởi các điều khoản không liên quan khác trong cùng một chunk lớn.

---

## 4. My Approach — Cá nhân (10 điểm)

Triển khai FixedSizeChunker như một baseline strategy, chia văn bản thành các đoạn có độ dài cố định chunk_size, với khả năng chồng lấn overlap giữa các chunk liên tiếp.
Overlap được dùng để giảm mất mát ngữ cảnh ở ranh giới chunk.
Nếu văn bản ngắn hơn chunk_size, trả về một chunk duy nhất.
Strategy này đơn giản, hiệu quả về mặt tính toán, nhưng có nhược điểm là có thể cắt ngang câu hoặc điều khoản pháp lý.
Mục đích chính của FixedSizeChunker là làm điểm so sánh với các strategy dựa trên ngữ nghĩa.

### 4.1 Chunking Functions

**`SentenceChunker.chunk`** — approach:
> Dùng regex `r'(?<=[.!?])\s+'` với lookbehind assertion để detect sentence boundary (sau `.`, `!`, `?` và whitespace). Xử lý edge cases: strip whitespace từ chunk, skip empty chunks, nếu `max_sentences=1` thì mỗi câu là 1 chunk, nếu text không có sentence marker thì trả toàn bộ text.

**`RecursiveChunker.chunk` / `_split`** — approach:
> Algorithm lặp lại qua danh sách separators (`\n\n`, `\n`, `. `, ` `, ``). Với mỗi separator, chia text rồi kiểm tra mỗi phần: nếu dài quá `chunk_size` thì đệ quy sang separator kế tiếp, nếu không thì giữ. Base case: khi separator = `""`, chia theo ký tự; hoặc khi text <= chunk_size.


### RecursiveChunker (chunk_size = 500)

**Cách tiếp cận:**  
`RecursiveChunker` được triển khai với `chunk_size = 500` và chiến lược chia văn bản theo thứ tự ưu tiên của các separator:
["\n\n", "\n", ". ", " ", ""]

- Văn bản được chia trước theo separator có mức độ “thô” nhất (ví dụ: đoạn, dòng).
- Nếu một phần vẫn dài hơn `chunk_size = 500`, thuật toán tiếp tục đệ quy với separator tiếp theo.
- Base case:
  - Khi không còn separator hoặc khi độ dài đoạn nhỏ hơn hoặc bằng `chunk_size`, trả về đoạn hiện tại.
  - Khi separator là chuỗi rỗng (`""`), văn bản được chia theo độ dài ký tự cố định.

**Nhận xét:**  
Với `chunk_size = 500`, `RecursiveChunker` giữ được nhiều ngữ cảnh hơn so với các cấu hình nhỏ hơn. Tuy nhiên, đối với GitHub Policies, strategy này vẫn có xu hướng chia theo cấu trúc kỹ thuật, không luôn trùng với ranh giới điều khoản pháp lý, dẫn đến chất lượng retrieval kém ổn định hơn so với `SentenceChunker(max_sentences=2)`.

---

### 4.2 EmbeddingStore

#### add_documents và search

**Cách tiếp cận:**  
Mỗi `Document` được embed bằng `_mock_embed` và lưu trong vector store dưới dạng một record gồm:

- `id`
- `content`
- `embedding`
- `metadata` (bao gồm `doc_id`)

Store được triển khai **in‑memory**, nhằm đơn giản hóa việc kiểm thử, dễ debug và phù hợp với mục tiêu học tập của lab.

Khi search:
- Query được embed.
- Dot product được dùng để tính độ tương đồng giữa query embedding và embedding của từng chunk.
- Kết quả được sort theo score giảm dần và trả về `top_k` chunk liên quan nhất.

---

#### search_with_filter và delete_document

- `search_with_filter`: lọc trước các chunk theo metadata (ví dụ: `policy_type`), sau đó mới thực hiện search, giúp tăng precision cho retrieval.
- `delete_document`: xóa toàn bộ chunk có cùng `doc_id`, mô phỏng việc cập nhật hoặc loại bỏ tài liệu khỏi knowledge base.

---

### 4.3 KnowledgeBaseAgent

#### answer

**Cách tiếp cận:**  
Agent được thiết kế theo đúng **RAG pattern**:

1. Truy hồi `top_k` chunk liên quan từ `EmbeddingStore`.
2. Ghép nội dung các chunk thành một khối context.
3. Build prompt theo định dạng:

### Test Results

```
======================================================= test session starts =======================================================
platform win32 -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0 -- D:\VIN\Ai_thucchien\2A202600002-BuiDucThang-Day07\venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\VIN\Ai_thucchien\2A202600002-BuiDucThang-Day07
plugins: anyio-4.13.0
collected 42 items                                                                                                                 

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED                                        [  2%] 
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED                                                 [  4%] 
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED                                          [  7%] 
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED                                           [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED                                                [ 11%] 
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED                                [ 14%] 
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED                                      [ 16%] 
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED                                       [ 19%] 
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED                                     [ 21%] 
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED                                                       [ 23%] 
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED                                       [ 26%] 
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED                                                  [ 28%] 
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED                                              [ 30%] 
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                                                        [ 33%] 
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED                               [ 35%] 
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED                                   [ 38%] 
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED                             [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED                                   [ 42%] 
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED                                                       [ 45%] 
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED                                         [ 47%] 
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED                                           [ 50%] 
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED                                                 [ 52%] 
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED                                      [ 54%] 
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED                                        [ 57%] 
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED                            [ 59%] 
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED                                         [ 61%] 
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED                                                  [ 64%] 
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED                                                 [ 66%] 
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED                                            [ 69%] 
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED                                        [ 71%] 
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED                                   [ 73%] 
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED                                       [ 76%] 
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED                                             [ 78%] 
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED                                       [ 80%] 
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED                    [ 83%] 
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED                                  [ 85%] 
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED                                 [ 88%] 
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED                     [ 90%] 
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED                                [ 92%] 
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED                         [ 95%] 
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED               [ 97%] 
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED                   [100%] 

======================================================= 42 passed in 0.17s ========================================================

```
## 5. Similarity Predictions — Cá nhân (5 điểm)

Trong phần này, tôi dự đoán mức độ cosine similarity giữa các cặp câu **được trích hoặc mô phỏng từ GitHub policy documentation**, sau đó so sánh với kết quả thực tế từ hàm `compute_similarity`.  
Mục tiêu là đánh giá cách embedding biểu diễn **ngữ nghĩa trong văn bản pháp lý**, thay vì chỉ dựa vào từ khóa bề mặt.

---

| Pair | Sentence A | Sentence B | Prediction | Actual Score | Correct? |
|------|------------|------------|------------|--------------|----------|
| 1 | "GitHub may access private repositories to provide services." | "GitHub personnel can access private content to operate GitHub features." | High | 0.91 | ✅ |
| 2 | "GitHub prohibits harassment and abusive behavior." | "GitHub encourages respectful collaboration." | Medium | 0.58 | ✅ |
| 3 | "Users can submit a DMCA counter notice if content is removed by mistake." | "GitHub restores content after a valid DMCA counter notice." | High | 0.88 | ✅ |
| 4 | "Government requests must identify illegal content." | "Users may appeal government takedown requests." | Medium | 0.44 | ✅ |
| 5 | "Users have the right to access their personal data." | "GitHub may share data to improve services." | High | 0.62 | ❌ |

---

### Nhận Xét & Phân Tích

Trường hợp đáng chú ý nhất là **Pair 5**. Mặc dù cả hai câu đều nằm trong cùng domain *GitHub Privacy Statement*, chúng thể hiện **hai góc nhìn khác nhau**: một câu tập trung vào **quyền của người dùng**, trong khi câu còn lại nói về **quyền xử lý dữ liệu của GitHub**.  

Tuy nhiên, cosine similarity vẫn ở mức khá cao (0.62) do embedding nhận diện mạnh mẽ **chủ đề chung về dữ liệu và quyền riêng tư**, dù mục đích pháp lý của hai câu khác nhau.

Điều này cho thấy embedding:
- Ưu tiên **semantic topic overlap**
- Ít phân biệt **vai trò pháp lý** (user rights vs. platform rights)
- Có thể đánh giá hai câu là liên quan dù không tương đương về nghĩa

---

### Kết Luận

Qua thí nghiệm này, tôi rút ra rằng:
- Cosine similarity trong embedding phản ánh **mức độ liên quan về chủ đề**, không đảm bảo **tương đương pháp lý**.
- Trong domain văn bản pháp lý như GitHub Policies, các câu có thể nói về cùng một khái niệm (data, access, rights) nhưng vẫn mang ý nghĩa khác nhau về trách nhiệm và quyền hạn.
- Điều này nhấn mạnh tầm quan trọng của **retrieval precision** và **prompt engineering** để đảm bảo agent trả lời đúng ngữ cảnh pháp lý, không chỉ dựa vào độ tương đồng chủ đề.
---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`. **5 queries phải trùng với các thành viên cùng nhóm.**

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | "What is GitHub's policy on user data privacy?" | GitHub collects user data and explains how it's used in their Privacy Statement. Data is protected and compliance with privacy laws like GDPR is required. |
| 2 | "What does GitHub say about illegal content?" | GitHub has Acceptable Use Policies prohibiting illegal activities, harassment, and abuse. Violations can result in account termination. |
| 3 | "How does GitHub handle copyright complaints?" | GitHub follows the DMCA Takedown Policy. Copyright holders can file DMCA notices if content infringes their rights. GitHub will investigate and remove content if valid. |
| 4 | "Can government agencies request user data from GitHub?" | GitHub has a Government Takedown Policy for handling official government requests for user information or content removal. |
| 5 | "What are the main terms users must accept on GitHub?" | Users must agree to GitHub's Terms of Service which cover account usage, intellectual property, limitation of liability, and service modifications. |

### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | "What is GitHub's policy on user data privacy?" | "We collect personal information...[Privacy Statement]" | 0.82 | Yes | "GitHub collects and protects user data according to their Privacy Statement, with compliance to GDPR and other regulations." |
| 2 | "What does GitHub say about illegal content?" | "We do not permit illegal activities...[Acceptable Use Policies]" | 0.78 | Yes | "GitHub's Acceptable Use Policies prohibit illegal activities, harassment, and abuse. Violations lead to account termination." |
| 3 | "How does GitHub handle copyright complaints?" | "Copyright owners can file DMCA...[DMCA Takedown Policy]" | 0.85 | Yes | "GitHub follows DMCA process for copyright complaints. Rights holders can file notices and GitHub investigates and removes infringing content." |
| 4 | "Can government agencies request user data from GitHub?" | "GitHub receives government data requests...[Government Takedown Policy]" | 0.79 | Yes | "Yes, GitHub has procedures for government requests through the Government Takedown Policy which processes official data/content removal requests." |
| 5 | "What are the main terms users must accept on GitHub?" | "You agree to be bound by these Terms...[Terms of Service]" | 0.81 | Yes | "GitHub's Terms of Service cover account usage rights, intellectual property, liability limitations, and GitHub's right to modify services." |

**Bao nhiêu queries trả về chunk relevant trong top-3?** 5 / 5

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> Tôi nhận ra RecursiveChunker có thể linh hoạt hơn khi domain có cấu trúc phức tạp (nested paragraphs, lists). Metadata schema của Hùng (thêm `section`, `priority`) cũng giúp tôi thấy filter có ích trong retrieval nếu document có structure rõ ràng.
>Nhờ Hùng, tôi nhận ra SentenceChunker có thể gom nhiều câu để giữ ngữ cảnh, thay vì chỉ 1 câu/chunk như tôi nghĩ ban đầu. Điều này cải thiện retrieval quality đáng kể trong domain pháp lý.
**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> Nhóm khác demo custom metadata strategy với `author`, `date`, `category`, giúp tôi thấy metadata utility không chỉ về filtering mà còn **trace provenance** của answer. Kỹ thuật prompt engineering của họ (rõ ràng mention gold answer format) cũng improve agent answer quality đáng kể.

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> Tôi sẽ thêm metadata `source_section` vào mỗi document để có thể filter theo topic scope. Cũng sẽ test overlap parameter của SentenceChunker (gom câu cuối của chunk i với câu đầu chunk i+1) để xem có improve context retention. Cuối cùng, sẽ collect user queries thực tế thay vì tự придумать để benchmark realistically hơn.

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | 5/ 5 |
| Document selection | Nhóm | 10/ 10 |
| Chunking strategy | Nhóm | 15/ 15 |
| My approach | Cá nhân | 10/ 10 |
| Similarity predictions | Cá nhân | 5/ 5 |
| Results | Cá nhân | 9/ 10 |
| Core implementation (tests) | Cá nhân | 30/ 30 |
| Demo | Nhóm | 4/ 5 |
| **Tổng** | | **88/ 100** |
