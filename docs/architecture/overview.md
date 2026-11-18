# Kiến trúc

## Mục tiêu

Ứng dụng desktop **local-first cho một người dùng**, mục tiêu Windows 11. Không có backend
server, đăng nhập, API nhiều người dùng, cloud hay backup/restore. Luồng dữ liệu:
[data-flow.md](data-flow.md).

## Modular Monolith + Layered Architecture

Phân tách trách nhiệm vừa đủ; không tạo class, interface hay service rỗng để dự phòng.

| Layer (`src/xaydungso/…`) | Nhiệm vụ | Không được |
|---|---|---|
| `presentation` | Cửa sổ Fluent, các trang, hộp thoại, widget dùng chung, theme/icon/animation | SQL trực tiếp, quy tắc nghiệp vụ, ghi file |
| `application` | Use case: hồ sơ, nhắc nhở + engine gửi, mẫu thông báo, Dashboard, cài đặt; các cổng (ports) | Phụ thuộc widget Qt |
| `domain` | Mô hình và quy tắc thuần Python: hồ sơ, giờ nhắc, mẫu thông báo | Import PyQt6, SQLite, thư viện tài liệu |
| `infrastructure` | SQLite (migration, repository, diagnostics chỉ đọc), ghi Excel, Telegram, Windows toast, cấu hình DPAPI, quản lý tiến trình worker | Quyết định quy tắc nghiệp vụ thay Domain |
| `core` | Cấu hình ứng dụng, logging, đường dẫn dữ liệu | Trở thành nơi gom helper/nghiệp vụ |

Hướng phụ thuộc: Presentation → Application → Domain; Infrastructure hiện thực các cổng của
lớp trong. Composition root là `app.py` (GUI) và `worker.py` (nhắc nền) — nơi duy nhất nối
dependencies. Không ép mapping một-một giữa `docs/modules/` và Python packages.

## Thành phần chính

- **GUI** (`uv run xaydungso`): `FluentWindow` với Tổng quan, Quản lý hồ sơ, Nhắc nhở (+ màn
  hình Cấu hình mẫu), Cài đặt. Tác vụ I/O chạy ngoài Qt event loop qua `presentation/tasks.py`.
- **Worker** (`uv run xaydungso-reminders`): tiến trình riêng không cần Qt, đọc SQLite và gửi
  thông báo; một worker cho mỗi thư mục dữ liệu (khóa hệ điều hành).
- **Dữ liệu** (thư mục dữ liệu người dùng): `xaydungso.sqlite3` (nguồn chính duy nhất),
  `settings.json`, `reminders.log`, `launcher.log`, file khóa/dừng worker.
- **Excel**: đầu ra một chiều vào sổ làm việc có sẵn; không bao giờ là nguồn dữ liệu.

## Stack

Python 3.12, Astral uv (`uv.lock`), PyQt6 + PyQt6-Fluent-Widgets, SQLite (thư viện chuẩn),
pytest, Ruff. Icon: Fluent UI System Icons (MIT, đi kèm repository). Đóng gói: PyInstaller
(`packaging/build_windows.py`, chưa nghiệm thu).

## Thay đổi kiến trúc

Mọi quyết định đổi ranh giới layer, nguồn dữ liệu chính hoặc hướng dữ liệu phải được ghi vào
tài liệu trước khi đổi code.
