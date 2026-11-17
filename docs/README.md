# Xây Dựng Số — Documentation Index

This folder is the source of truth for approved design and business specifications. The root [README](../README.md) introduces the project; [AGENTS.md](../AGENTS.md) provides AI-agent working rules.

| Khi thực hiện | Đọc tài liệu |
|---|---|
| Kiến trúc tổng thể | [Architecture overview](architecture/overview.md), [Layers](architecture/layers.md), [Data flow](architecture/data-flow.md) |
| Viết / review code | [Coding standards](development/coding-standards.md), [Testing](development/testing.md) |
| Trạng thái triển khai / bàn giao | [Implementation status](development/implementation-status.md), [Tiến độ](../process.md) |
| Xây dựng giao diện | [UI design](ui/design-guidelines.md) |
| Dashboard / trang mở mặc định | [Overview](modules/dashboard/overview.md), [Metrics](modules/dashboard/metrics.md) |
| Xử lý hồ sơ | [CPXD overview](modules/cpxd/overview.md), [Workflow](modules/cpxd/workflow.md), [Schema](modules/cpxd/schema.md) |
| Xuất sổ Excel | [Excel overview](modules/excel/overview.md), [Field mapping](modules/excel/field-mapping.md), [Export workflow](modules/excel/export-workflow.md) |
| Nhắc nhở | [Reminder overview](modules/reminders/overview.md), [Business rules](modules/reminders/business-rules.md), [Vận hành](modules/reminders/operations.md) |
| Lập kế hoạch / nghiệm thu | [Roadmap](roadmap/overview.md), [Phase 01](roadmap/phase-01.md) |

## Quy tắc bảo trì

- Mỗi đặc tả chi tiết chỉ có **một** nơi định nghĩa chính thức; các file khác liên kết đến đó.
- Cập nhật tài liệu cùng thay đổi có ảnh hưởng đến hành vi, dữ liệu hoặc kiến trúc.
- Không tự điền quy tắc nghiệp vụ còn thiếu: đánh dấu **TBD**.
- Tạo module tài liệu mới dưới `docs/modules/<module>/` khi có module độc lập được phê duyệt.
- Đọc đúng tài liệu liên quan; không cần tải toàn bộ tài liệu cho mọi tác vụ.

**Trạng thái:** Tài liệu v1.0; các mục `TBD` chưa phải yêu cầu đã chốt.

## Quyết định cập nhật

Ưu tiên hiện tại: Dashboard mở mặc định, quản lý hồ sơ SQLite, nhắc nhở hai kênh, xuất sổ Excel. Dashboard chỉ đọc SQLite qua Application, không dùng Excel làm nguồn dữ liệu. Word Generation hoãn đến khi cung cấp đủ mẫu.
