# Data Flow — SQLite as Source of Truth

## Hồ sơ

`UI → Application validation / Domain rules → SQLite commit`.

- Thao tác tạo, sửa, xóa hồ sơ đều thực hiện qua ứng dụng.
- Không lấy Excel làm nguồn dữ liệu cập nhật.
- Xóa hồ sơ là xóa vĩnh viễn sau khi xác nhận phù hợp trong UI.

## Xuất sổ theo dõi

`SQLite (committed records) → Excel Exporter → generated .xlsx`

- Xuất lại toàn bộ danh sách sau các thay đổi liên quan đến sổ, dùng [mẫu Excel](../modules/excel/overview.md).
- Lỗi xuất Excel **không** hoàn tác dữ liệu SQLite đã commit.
- File mẫu gốc không bao giờ bị ghi đè.
- Ghi tệp đầu ra qua file tạm và thay thế an toàn khi có thể.

## Nhắc nhở

`SQLite reminder data → Scheduler → Time rules → Notification channel`.

- Tính toán nhắc nhở độc lập với Excel; Excel không điều khiển scheduler.
- Quy tắc thời gian: [Reminder business rules](../modules/reminders/business-rules.md).
- Phương thức gửi và cơ chế chạy nền là phần triển khai tương lai, không có trong Foundation.

## Văn bản Word

`SQLite / Domain calculation → Document generation → Word file` (tương lai; mapping theo mẫu Word sẽ được đặc tả riêng).
