# Nhắc nhở — Vận hành và khắc phục sự cố

Quy tắc: [business-rules.md](business-rules.md).

## Trên giao diện

1. **Nhắc nhở → Tạo nhắc nhở**, hoặc nút chuông trong khung **Chi tiết hồ sơ**.
2. Chọn hồ sơ liên quan (hoặc để lịch độc lập), kiểm tra hạn xử lý, chọn khoảng báo trước.
   Muốn thử nhanh: đặt hạn gần hiện tại cộng khoảng báo trước và xem
   **Thời điểm gửi thông báo dự kiến**.
3. Chọn mẫu thông báo (mặc định chọn sẵn) hoặc tự nhập; xem trước nội dung sẽ gửi → **Lưu lịch nhắc**.
4. Mặc định form bật nhắc nền sau khi lưu. Có thể bật/dừng bằng nút **Bật nhắc nền / Dừng nhắc nền**;
   chip trên tiêu đề cho biết đang chạy hay dừng. Bật thất bại thì lịch vẫn giữ và giao diện báo rõ.
5. Bảng lịch: tìm kiếm, lọc trạng thái, sắp xếp Mới nhất/Cũ nhất theo giờ gửi, phân trang 14 dòng.
   Cột **Kênh gửi** cho trạng thái từng kênh; di chuột để xem lỗi (đã loại thông tin bí mật).
   Thao tác mỗi dòng: Sửa (lịch chưa gửi), Hủy, Xóa; tick nhiều dòng để xóa hàng loạt.
6. **Cấu hình** mở màn hình quản lý mẫu nội dung; **← Quay lại Nhắc nhở** để trở về.

Hủy hoặc xóa chỉ ngăn các lần gửi chưa bắt đầu; không thu hồi tin đã gửi hoặc lệnh gửi đã bắt đầu.

## Worker (nhắc nền)

- Tiến trình Python riêng, đọc SQLite và kiểm tra mỗi giây; không cần GUI mở. Khóa hệ điều hành
  bảo đảm chỉ một worker cho mỗi thư mục dữ liệu; launcher chờ khóa tối đa 5 giây trước khi báo đã bật.
- Kênh lỗi tự thử lại sau 5, 10, 20… giây (tối đa 300 giây); luôn kiểm tra khung 07:00–23:00.
- **Dừng nhắc nền** dừng sau lượt đang xử lý, không xóa lịch.
- Không tự cài Windows Service/Task Scheduler/tự chạy khi đăng nhập. Sau khi khởi động lại máy,
  bật lại worker; lịch bỏ lỡ được gửi bù một lần trong khung giờ.
- Khi cập nhật phần mềm: mở lại GUI và bật lại worker để dùng code mới (worker cũ có thể từ chối
  database đã nâng cấp schema).

Chạy riêng không cần GUI:

```bash
uv run xaydungso-reminders
uv run python -m xaydungso.worker           # tương đương
uv run xaydungso-reminders --once           # xử lý một lượt rồi thoát
uv run xaydungso-reminders --data-dir <thư-mục>
```

Bản đóng gói: `XayDungSo.exe --reminder-worker --data-dir <thư-mục>`. Có thể đặt
`XAYDUNGSO_DATA_DIR` cho cả GUI và worker. Log `reminders.log` ở thư mục dữ liệu có giới hạn
kích thước, không ghi nội dung hồ sơ hoặc credentials.

## Telegram

- Nhập **Bot Token** và **Chat ID** tại **Cài đặt → Telegram Bot**, **Kiểm tra kết nối**, rồi **Lưu**.
  Token lưu mã hóa DPAPI theo tài khoản Windows, không lưu plaintext trong SQLite/log/repository.
- Có thể dùng biến môi trường khi để trống cả hai ô trong Cài đặt (cấu hình đã lưu được ưu tiên):

  ```powershell
  $env:XAYDUNGSO_TELEGRAM_BOT_TOKEN = '<bot-token>'
  $env:XAYDUNGSO_TELEGRAM_CHAT_ID = '<chat-id>'
  uv run xaydungso
  ```

  Đổi biến môi trường thì dừng worker cũ và khởi chạy lại.
- Adapter gọi HTTPS `sendMessage` (timeout 10 giây, kiểm tra `ok`), không dùng parse mode.
  Nguồn: [Telegram Bot API](https://core.telegram.org/bots/api#sendmessage).

**Không nhận được tin?** Kiểm tra lần lượt: nhắc nền đang chạy; giờ gửi dự kiến đã tới và nằm
trong 07:00–23:00; trạng thái kênh Telegram trên bảng; **Kiểm tra kết nối** (Chat ID là người/nhóm
nhận, không phải dãy số đầu Bot Token hay ID của bot; đã bấm Start với bot); đã nhấn **Lưu**.
Gửi thử thành công chưa chứng minh lịch sẽ gửi nếu worker dừng hoặc lịch chưa tới giờ.

## Windows Notification

Dùng Windows PowerShell 5.1 có sẵn và WinRT `ToastNotificationManager`, đăng ký tên hiển thị
`xaydungso` trong HKCU (không cần admin). Nội dung XML được escape và mã hóa base64, không nội
suy thành lệnh PowerShell; kiểm tra exit code, timeout 20 giây.

`sent` nghĩa là Windows đã nhận yêu cầu, không chứng minh popup đã hiện hay người dùng đã đọc.
Cần kiểm tra thực tế: Notifications/Focus Assist, tên ứng dụng, bản đóng gói. Ngoài Windows
kênh này báo thất bại (không giả thành công).
Nguồn: [ToastNotificationManager](https://learn.microsoft.com/en-us/uwp/api/windows.ui.notifications.toastnotificationmanager).

## Giới hạn chống trùng

Claim từng kênh dùng lease 60 giây và token. Tiến trình chết trước khi ghi kết quả → lease hết
hạn cho phép thử lại. Nếu kênh đã nhận tin nhưng tiến trình chết trước khi lưu `sent`, có thể
gửi trùng. Không có transaction phân tán với Telegram/Windows nên **không** bảo đảm
exactly-once; mã nhắc trong nội dung giúp nhận biết các lần gửi cùng lịch.
