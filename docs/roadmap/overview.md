# Roadmap — Xây Dựng Số

Triển khai theo các module độc lập và theo thứ tự phụ thuộc. Mỗi giai đoạn có test và review; kế hoạch không được dùng để suy diễn nghiệp vụ còn thiếu.

| Phase | Nội dung | Trạng thái |
|---|---|---|
| 01 | Foundation, PyQt6/QFluentWidgets, logging, tests, docs | Đã triển khai và kiểm tra trên Linux |
| 02 | SQLite schema, domain models, repository | Đã triển khai, có test migration và CRUD |
| 03 | UI danh sách/chi tiết hồ sơ | Đã triển khai, có test thao tác giao diện |
| 04 | CRUD và các trường tiến độ | Đã triển khai; chờ người dùng nghiệm thu |
| 05 | Reminder Engine, Telegram + Windows notifications | Đã triển khai; transport được mock trong test, cần kiểm chứng gửi thật |
| 05-D | Dashboard sau interface SQLite và Reminder | Đã triển khai, test SQLite/UI và desktop Linux đạt; chờ nghiệm thu Windows theo [đặc tả](../modules/dashboard/overview.md) |
| 06 | Excel Export theo template `so_theo_doi.xlsx` | Đã nối CRUD và retry; cần kiểm tra Excel/khóa file thật trên Windows |
| 07 | Kiểm thử tích hợp và đóng gói Windows | Test Linux đạt; cấu hình build có sẵn, chưa build trên Windows |
| Later | Word generation, tính toán xây dựng chuyên ngành | Hoãn |

Không tạo một Phase 01.2 không có scope độc lập đã chốt. Dashboard phụ thuộc dữ liệu hồ sơ và lịch nhắc; chỉ triển khai sau khi interface của Phase 02 và 05 đã có. Phạm vi không gồm analytics/biểu đồ, trạng thái mới hoặc Word Generation.
