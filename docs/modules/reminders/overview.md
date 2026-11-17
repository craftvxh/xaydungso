# Reminder Module — Tổng quan

Reminder là module độc lập với Excel, liên kết tùy chọn tới hồ sơ CPXD và lưu lịch/ trạng thái gửi trong SQLite.

- Chọn giờ bắt đầu (mặc định lúc tạo, cho phép chỉnh) và thời lượng: 10 giây test, 1 giờ, 12 giờ, 24 giờ hoặc thời lượng hợp lệ được hỗ trợ.
- Domain tính deadline và giờ được phép gửi theo [quy tắc đã chốt](business-rules.md).
- Scheduler không phụ thuộc cửa sổ PyQt6; mục tiêu là tiếp tục nhắc khi Windows đang bật và GUI đóng, nếu tiến trình nhắc nhở vẫn chạy.
- Kênh thông báo: **Telegram + Windows Notification**.
- SQLite giữ lịch nhắc và kết quả gửi từng kênh; chống gửi trùng ở mức tốt nhất có thể, retry riêng kênh lỗi.
- Khi máy tắt/tiến trình dừng, gửi bù một lần trong giờ cho phép lúc hoạt động lại.
- Excel không gửi thông báo và không quản lý lịch.

Triển khai sau khi có nền SQLite và CRUD hồ sơ. Không bổ sung Reminder Engine vào Phase Foundation.
