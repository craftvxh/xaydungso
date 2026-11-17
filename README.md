# Xây Dựng Số (`xaydungso`)

Ứng dụng desktop Windows hỗ trợ quản lý hồ sơ xây dựng và theo dõi quá trình xử lý, hướng tới thao tác đơn giản cho một người dùng.

> **Trạng thái:** Đã triển khai giao diện quản lý hồ sơ, CRUD SQLite, xuất sổ Excel và lịch nhắc với tiến trình nền. Kiểm thử tự động và giao diện đã chạy trên Linux; notification thật và bản đóng gói Windows chưa được kiểm chứng. Word và tính toán xây dựng chuyên ngành được hoãn.

## Chức năng hiện có

- Dashboard mở mặc định: tổng hồ sơ, hai trạng thái, lịch nhắc hôm nay/sắp tới; dữ liệu SQLite qua Application.
- Quản lý danh sách hồ sơ xây dựng; thêm, chỉnh sửa, xóa vĩnh viễn và tìm kiếm.
- Theo dõi các trường thông tin của hồ sơ trên giao diện desktop.
- Tạo/sửa/hủy lịch nhắc, chọn giờ bắt đầu và thời lượng; theo dõi kết quả Telegram và Windows Notification riêng từng kênh.
- Xuất sổ theo dõi Excel theo mẫu chính thức `so_theo_doi.xlsx` từ dữ liệu SQLite.

## Công nghệ

Python 3.12 · PyQt6 · PyQt6-Fluent-Widgets · SQLite · Astral uv · pytest · Ruff.

Thiết kế **local-first, single-user**, theo kiến trúc Modular Monolith phân lớp.

## Bắt đầu phát triển

Dùng Python 3.12 và uv; không khởi tạo lại dự án:

```bash
uv sync --locked
uv run xaydungso
# Hoặc: uv run python -m xaydungso
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Ứng dụng mở vào **Tổng quan (Dashboard)** với số hồ sơ và lịch nhắc từ SQLite.
Chọn **Quản lý hồ sơ** để tới trang **Hồ sơ**, rồi **Thêm hồ sơ**, nhập mã và họ tên; các trường
theo dõi khác có thể nhập sau. Chọn dòng để mở **Chi tiết / sửa**, **Xóa hồ sơ**
hoặc **Tạo nhắc cho hồ sơ**. Xóa luôn cần xác nhận.

SQLite và file xuất `so_theo_doi.xlsx` nằm trong thư mục dữ liệu người dùng:
`%LOCALAPPDATA%/xaydungso` trên Windows, `$XDG_DATA_HOME/xaydungso` hoặc
`~/.local/share/xaydungso` trên Linux. Có thể dùng `XAYDUNGSO_DATA_DIR` để chọn
thư mục dữ liệu khác. Không dùng thư mục template làm thư mục dữ liệu.

Sau khi lưu/sửa/xóa, ứng dụng xuất lại toàn bộ Excel. Nếu Excel bị khóa hoặc xuất
lỗi, hồ sơ vẫn đã lưu trong SQLite; chọn **Xuất lại Excel** để thử lại. **Mở sổ Excel**
mở bản xuất, không mở mẫu gốc.

Trong trang **Nhắc nhở**, chọn **Bật nhắc nền** để gửi các lịch đến hạn. Tiến trình
này tiếp tục khi đóng GUI; máy vẫn phải đang bật. **Dừng nhắc nền** yêu cầu dừng
tiến trình, không xóa lịch đã lưu. Cấu hình Telegram và hướng dẫn chạy riêng:
[Vận hành nhắc nhở](docs/modules/reminders/operations.md).

Đóng gói trên Windows: `uv run python packaging/build_windows.py`.
Xem [trạng thái kiểm chứng](docs/development/implementation-status.md) và
[tiến độ bàn giao](process.md). Chưa có installer hoặc cấu hình tự chạy khi đăng nhập.

## Tài liệu

- [Mục lục tài liệu](docs/README.md)
- [Kiến trúc](docs/architecture/overview.md)
- [Mẫu sổ Excel](docs/modules/excel/overview.md)
- [Lộ trình](docs/roadmap/overview.md)
- [Quy tắc Codex](AGENTS.md)
