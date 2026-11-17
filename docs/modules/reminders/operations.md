# Vận hành nhắc nhở

## Dùng trên giao diện

1. Từ Hồ sơ, chọn một dòng → **Tạo nhắc cho hồ sơ**; hoặc mở trang Nhắc nhở → **Tạo lịch nhắc** để tạo lịch độc lập.
2. Chọn thời điểm bắt đầu theo giờ Việt Nam và thời lượng. Nếu không chỉnh giờ bắt đầu,
   ứng dụng dùng đúng thời điểm lưu/tạo lịch; có thể chọn giờ khác trong form.
   Preset có 10 giây test, 1 giờ, 12 giờ, 24 giờ; hỗ trợ số giây nguyên dương khác.
3. Lưu lịch. Xem deadline và giờ gửi đã điều chỉnh trong bảng; không thay đổi cột H theo dõi của hồ sơ.
4. Chọn **Bật nhắc nền**. Tiến trình Python riêng đọc SQLite và kiểm tra mỗi giây;
   không cần Qt hoặc GUI còn mở. Có khóa hệ điều hành để chỉ một worker chạy cho mỗi thư mục dữ liệu.
5. Mỗi kênh có trạng thái riêng. Kênh lỗi tự thử lại sau 5, 10, 20… giây, tối đa 300 giây giữa các lần;
   luôn kiểm tra khung 07:00–23:00 trước khi gửi. Không gửi lại kênh đã thành công.
6. **Dừng nhắc nền** yêu cầu dừng sau lần xử lý đang chạy. Không xóa lịch. Bật lại để tiếp tục/gửi bù.

Chỉ sửa lịch chưa có kênh thành công và không đang được gửi. Sửa tính lại deadline/notify.
Hủy lịch hoặc xóa hồ sơ ngăn các lần gửi chưa bắt đầu; không thu hồi thông báo đã gửi.
Lệnh hủy có thể đến đúng lúc một lệnh gửi bên ngoài đã bắt đầu: không thể thu hồi việc gửi đó.

Worker không tự cài Windows Service, Task Scheduler hoặc tự chạy khi đăng nhập.
Sau khi khởi động lại máy, cần bật lại worker. Máy tắt thì không gửi được; lịch bỏ
lỡ được gửi bù một lần khi worker hoạt động trong khung giờ cho phép.

## Telegram

Cần bot token và chat ID hợp lệ. Trong PowerShell dùng để khởi chạy GUI/worker:

```powershell
$env:XAYDUNGSO_TELEGRAM_BOT_TOKEN = '<bot-token>'
$env:XAYDUNGSO_TELEGRAM_CHAT_ID = '<chat-id>'
uv run xaydungso
```

Sau đó bật nhắc nền trên UI. Worker kế thừa môi trường lúc được khởi chạy; nếu đổi
cấu hình, dừng worker cũ và khởi chạy lại từ môi trường đã cập nhật. Không lưu token
trong repository, SQLite hoặc log. Không gửi thông báo thật trong automated tests.

Adapter gọi HTTPS `sendMessage` với timeout 10 giây và kiểm tra phản hồi `ok`;
không dùng parse mode, không biến nội dung người dùng thành HTML.
Nguồn API: [Telegram Bot API](https://core.telegram.org/bots/api#sendmessage).

## Windows Notification

Adapter dùng Windows PowerShell 5.1 có sẵn và WinRT `ToastNotificationManager`.
Đăng ký tên hiển thị `xaydungso` trong HKCU, không cần quyền admin. Nội dung XML
được escape và mã hóa trước khi chuyển cho PowerShell; không nội suy văn bản hồ
sơ thành lệnh. Kiểm tra exit code, timeout 20 giây và thiết lập notification.

`sent` nghĩa là API/kênh đã chấp nhận gửi, không phải bằng chứng người dùng đã đọc
hoặc Windows chắc chắn hiển thị popup. Cần kiểm tra thực tế trên Windows, bao gồm
Notifications/Focus Assist, tên ứng dụng và bản đóng gói. Không có fallback giả
thành công trên Linux; kênh Windows báo thất bại và có thể retry.
Nguồn: [Microsoft ToastNotificationManager](https://learn.microsoft.com/en-us/uwp/api/windows.ui.notifications.toastnotificationmanager).

## Chạy riêng, không mở GUI

```bash
uv run xaydungso-reminders
# Hoặc:
uv run python -m xaydungso.worker
# Xử lý một lượt rồi thoát:
uv run xaydungso-reminders --once
# Chọn cùng thư mục dữ liệu với GUI:
uv run xaydungso-reminders --data-dir /path/to/data
```

Cũng có thể đặt `XAYDUNGSO_DATA_DIR` cho cả GUI và worker. Bản đóng gói:
`XayDungSo.exe --reminder-worker --data-dir <thư-mục>`.
Log kỹ thuật `reminders.log` ở thư mục dữ liệu có giới hạn kích thước; không ghi
nội dung hồ sơ hoặc credentials. UI kiểm tra trạng thái qua khóa tiến trình.

## Giới hạn chống trùng

SQLite lưu claim riêng từng kênh với lease 60 giây và token. Nếu tiến trình chết
trước khi ghi nhận kết quả, lease hết hạn cho phép thử lại. Nếu transport đã nhận
thông báo nhưng tiến trình chết trước khi commit `sent`, lần phục hồi có thể gửi
trùng. Không có transaction phân tán với Telegram/Windows; không tuyên bố exactly-once.
ID lịch được đính kèm nội dung để nhận biết các lần gửi cùng lịch.
