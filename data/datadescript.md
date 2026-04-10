
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
| policy_type | string | privacy, terms, acceptable_use | Giúp filter đúng nhóm tài liệu khi query hỏi về một loại chính sách cụ thể. |
| source | string | github | Hữu ích nếu sau này mở rộng corpus với nhiều tổ chức hoặc nhiều website chính sách khác nhau. |
| language | string | en | Cho phép lọc theo ngôn ngữ nếu benchmark có cả tài liệu tiếng Anh và tiếng Việt. |
| topic_scope | string | copyright, user_data, account_rules | Giúp retrieval chính xác hơn khi câu hỏi tập trung vào một chủ đề hẹp trong policy corpus. |

---
docs.github.com
