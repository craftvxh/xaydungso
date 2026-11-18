# Xây Dựng Số — Mục lục tài liệu

Thư mục này là nguồn chính thức cho đặc tả đã duyệt. [README](../README.md) giới thiệu và
hướng dẫn chạy; [AGENTS.md](../AGENTS.md) là quy tắc làm việc cho AI agent;
[CONTEXT.md](../CONTEXT.md) tóm tắt các quyết định; [process.md](../process.md) là nhật ký bàn giao.

| Khi làm việc với | Đọc |
|---|---|
| Kiến trúc, layer, luồng dữ liệu | [Kiến trúc](architecture/overview.md), [Luồng dữ liệu](architecture/data-flow.md) |
| Viết / review code, kiểm thử | [Coding standards](development/coding-standards.md), [Testing](development/testing.md) |
| Giao diện (màu, icon, từng trang) | [UI design](ui/design-guidelines.md) |
| Tổng quan (Dashboard) | [Bố cục](modules/dashboard/overview.md), [Chỉ số](modules/dashboard/metrics.md) |
| Hồ sơ (CPXD) | [Quy tắc & workflow](modules/cpxd/overview.md), [Schema SQLite](modules/cpxd/schema.md) |
| Sổ Excel | [Ghi sổ có sẵn](modules/excel/overview.md), [Mapping 14 cột](modules/excel/field-mapping.md) |
| Nhắc nhở, mẫu thông báo | [Quy tắc](modules/reminders/business-rules.md), [Vận hành](modules/reminders/operations.md) |
| Cài đặt (SQLite, Telegram, Excel) | [Cài đặt](modules/settings/overview.md) |
| Phạm vi, tiến độ | [Lộ trình](roadmap/overview.md) |

Mẫu sổ làm việc: [`modules/excel/templates/so_theo_doi.xlsx`](modules/excel/templates/so_theo_doi.xlsx)
(cũng là file làm việc mặc định của ứng dụng).

## Quy tắc bảo trì

- Mỗi quy tắc chỉ định nghĩa ở **một** file; file khác liên kết tới đó.
- Cập nhật tài liệu cùng lúc với thay đổi hành vi, dữ liệu, schema hoặc kiến trúc.
- Không tự điền quy tắc nghiệp vụ còn thiếu: ghi rõ "chưa có đặc tả" hoặc **TBD**.
- Ghi ngày và nguồn (người dùng duyệt, bản thiết kế) khi một quyết định thay thế quyết định cũ.
- Tạo `docs/modules/<module>/` chỉ khi có module độc lập được phê duyệt.
- Nhật ký phiên làm việc và kết quả test ghi vào `process.md`, không thêm file trạng thái trong `docs/`.
