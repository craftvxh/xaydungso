# Layer responsibilities & dependencies

| Layer | Nhiệm vụ | Không được |
|---|---|---|
| `presentation` | Qt windows, widgets, user interactions, hiển thị phản hồi | SQL trực tiếp, tính toán nghiệp vụ, xuất file |
| `application` | Use case, phối hợp persistence / reminder / export | Phụ thuộc widget Qt |
| `domain` | Entities và quy tắc nghiệp vụ thuần Python | Import PyQt6, SQLite adapters, openpyxl, Word libs |
| `infrastructure` | Lưu SQLite, ghi Excel / Word, gửi thông báo qua adapter | Quyết định quy tắc nghiệp vụ thay cho Domain |
| `core` | Config, logging, tiện ích kỹ thuật thật sự dùng chung | Trở thành nơi gom mọi helper và nghiệp vụ |

## Hướng phụ thuộc

- Presentation gọi use cases của Application.
- Application sử dụng Domain và các contracts cần thiết.
- Infrastructure cung cấp implementations cho contracts của inner layers.
- Domain không tham chiếu Presentation hoặc Infrastructure.
- Composition root tại điểm khởi động ứng dụng chịu trách nhiệm nối dependencies.

Chỉ tạo abstraction khi có use case thực tế yêu cầu. Không ép một mapping một-một giữa các thư mục `docs/modules/` và Python packages.
