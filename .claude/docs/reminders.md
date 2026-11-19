# Nhắc nhở và mẫu thông báo

## Nhắc nhở — Quy tắc nghiệp vụ

Hướng dẫn chạy/khắc phục sự cố: [operations.md](#nhắc-nhở--vận-hành-và-khắc-phục-sự-cố).

### Tổng quan

- Module Nhắc nhở **tự quản lý lịch**: hồ sơ chỉ lưu thông tin và hạn xử lý; lưu/sửa hồ sơ
  không tạo, sửa hay hủy lịch.
- Người dùng tạo lịch tại **Nhắc nhở → Tạo nhắc nhở** (hoặc nút chuông trong khung chi tiết
  hồ sơ). Lịch có thể liên kết một hồ sơ (gợi ý hạn xử lý ban đầu) hoặc độc lập.
- Mỗi lịch giữ hạn xử lý và khoảng báo trước của riêng nó; sửa hồ sơ sau đó không đổi lịch.
- Gửi qua **Telegram** và **Windows Notification**, trạng thái và thử lại riêng từng kênh.
- Tiến trình nhắc nền (worker) độc lập Qt và Excel; chạy tiếp khi đóng cửa sổ nếu đã bật
  và máy còn bật. Excel không có cột giờ nhắc và không điều khiển việc gửi.

### Giờ gửi

- Hạn xử lý chọn bằng lịch, theo Asia/Ho_Chi_Minh, hiển thị `dd/MM/yyyy HH:mm`.
- Khoảng báo trước: Trước 10 giây (thử), 1 giờ, 12 giờ, 24 giờ, hoặc tự nhập số giây nguyên
  dương. Đây là thời gian **trước hạn**, không phải "gửi sau N giây kể từ lúc lưu".
- `giờ nhắc yêu cầu = hạn xử lý − khoảng báo trước`, trừ theo thời gian thực (kể cả cuối tuần,
  ngày lễ). Ví dụ: hạn 20/11/2026 16:00, báo trước 1 giờ → 20/11/2026 15:00.
- Khung gửi áp dụng cho **giờ nhắc yêu cầu** (không phải hạn xử lý):
  - trong 07:00:00–23:00:00 (gồm hai đầu mút): gửi đúng giờ;
  - ngoài khung: dời về 22:00 ngày trước ngày của giờ nhắc yêu cầu;
  - nếu mốc đã qua lúc lưu: dời sang 07:00 ngày tiếp theo.
- Form hiển thị **Thời điểm gửi thông báo dự kiến** sau điều chỉnh, kèm giải thích và chip
  Hợp lệ / Chưa hợp lệ. Giờ gửi thực tế có thể khác phép trừ (có thể sau hạn trong trường
  hợp ngoại lệ).
- Worker bỏ lỡ lịch đã lưu (máy tắt, worker dừng): gửi bù một lần khi chạy lại trong khung.

### Lưu, sửa, hủy, xóa

- Mỗi lịch gửi một lần cho mỗi kênh, không lặp. Không gửi lại kênh đã thành công.
- Chỉ sửa được lịch chưa có kênh nào gửi thành công và không đang gửi; sửa tính lại giờ gửi.
- **Hủy lịch**: dừng các kênh chưa gửi, giữ lịch và lịch sử.
- **Xóa lịch** (người dùng duyệt 18/11/2026): xóa vĩnh viễn từng lịch hoặc nhiều lịch đã tick,
  sau xác nhận; xóa luôn lịch sử gửi; không thu hồi tin đã gửi. Lịch đang gửi (`sending`)
  được giữ và báo số lịch chưa xóa.
- Xóa hồ sơ hủy các lịch liên quan còn kênh chưa gửi; lịch sử giữ với `record_id = NULL`.
- Form lịch mặc định chọn **Bật nhắc nền sau khi lưu lịch** (có thể bỏ). Lỗi bật worker không
  rollback lịch và được báo rõ. Không tự cài autostart/service.
- Trạng thái tổng của một lịch trên trang Nhắc nhở: **Đã hủy** nếu đã hủy; **Gửi lỗi** nếu có
  kênh lỗi; **Đã gửi** khi mọi kênh đã gửi; còn lại **Chờ gửi** (gồm đang gửi).
- Lịch tự động cũ (trước schema v5) được giữ nguyên ID, hạn, lịch sử và quản lý như lịch thường.
  Lịch legacy kiểu `start_at + duration` được giữ, không tự đổi thành hạn giả.

### Mẫu nội dung thông báo

Người dùng duyệt 19/11/2026 (bản Stitch "Cấu hình"):

- Quản lý tại **Nhắc nhở → Cấu hình**: danh sách, tìm kiếm, thêm/sửa/xóa, đặt mặc định, xem
  trước Telegram/Windows. Cấu hình Telegram nằm ở **Cài đặt**.
- Nội dung là **văn bản thường nhiều dòng** (emoji, gạch đầu dòng, đường kẻ); không in đậm/
  nghiêng vì Telegram gửi văn bản thường và thông báo Windows không hiển thị định dạng.
- Biến: `{{ma_ho_so}}`, `{{ho_ten}}`, `{{han_xu_ly}}` (`dd/mm/yyyy hh:mm`, theo hạn trong form).
  Biến được thay **khi chọn mẫu trong form lịch nhắc**; lịch lưu nội dung đã thay, worker
  không đổi. Biến không biết được giữ nguyên.
- Mẫu cần một hồ sơ liên kết để điền biến; lịch độc lập dùng **Tự nhập nội dung**. Khi nội dung
  vẫn đúng như mẫu vừa điền, đổi hạn xử lý sẽ cập nhật `{{han_xu_ly}}`; người dùng đã sửa thì giữ.
- Luôn có đúng một mẫu mặc định (chọn sẵn khi tạo lịch mới). Không xóa hay bỏ mặc định của mẫu
  mặc định — đặt mẫu khác làm mặc định trước. Xóa mẫu là vĩnh viễn, không ảnh hưởng lịch đã tạo.
- Lưu trong SQLite (`notification_templates`, schema v7); migration tạo sẵn 4 mẫu, mặc định
  "Nhắc hồ sơ sắp đến hạn".

### Nội dung gửi

Cả hai kênh gửi: tiêu đề `Xây Dựng Số — Nhắc nhở`, nội dung lịch, `Đến hạn: dd/mm/yyyy HH:MM:SS`
và `Mã nhắc: <id>`. Telegram nhận tất cả thành một tin (tối đa 4096 ký tự, phần dài bị rút gọn
nhưng giữ mã nhắc); Windows hiển thị tiêu đề in đậm và phần còn lại.

### Telegram

- **Cài đặt → Telegram Bot → Kiểm tra kết nối** gọi getMe/getChat, không gửi tin; hiển thị tên
  cuộc trò chuyện nhận tin và thời gian phản hồi. **Gửi thử** gửi một tin. Cả hai dùng ô đang
  nhập, không tự lưu, không tự thử lại; cần **Lưu** để lịch dùng cấu hình mới.
- Bot Token và Chat ID là hai thông tin khác nhau; Chat ID của chính bot bị từ chối.
- Lỗi HTTP/mạng được đổi thành thông báo an toàn, không lưu URL/token hoặc nguyên văn lỗi.
- Worker đọc lại cấu hình Telegram đã lưu trước mỗi lần gửi; nếu đọc lỗi thì không gửi tới đích cũ.

### SQLite và Excel

SQLite lưu hạn, khoảng báo trước, giờ gửi và trạng thái từng kênh (UTC, hiển thị giờ Việt Nam).
Excel chỉ có hạn xử lý ở cột F; không ghi khoảng báo trước hay giờ gửi.

## Nhắc nhở — Vận hành và khắc phục sự cố

Quy tắc: [business-rules.md](#nhắc-nhở--quy-tắc-nghiệp-vụ).

### Trên giao diện

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

### Worker (nhắc nền)

- Tiến trình Python riêng, đọc SQLite và kiểm tra mỗi giây; không cần GUI mở. Khóa hệ điều hành
  bảo đảm chỉ một worker cho mỗi thư mục dữ liệu; launcher chờ khóa tối đa 5 giây trước khi báo đã bật.
- Kênh lỗi tự thử lại sau 5, 10, 20… giây (tối đa 300 giây); luôn kiểm tra khung 07:00–23:00.
- **Dừng nhắc nền** dừng sau lượt đang xử lý, không xóa lịch.
- **Khởi động cùng Windows** (người dùng duyệt 19/11/2026): lối tắt `Xây Dựng Số - Nhắc nền.lnk`
  trong thư mục Startup của người dùng (`shell:startup`, không registry, không quyền admin) chạy
  **chỉ worker** ẩn khi đăng nhập (`pythonw -m xaydungso.worker --data-dir …`; bản `.exe`:
  `XayDungSo.exe --reminder-worker`); cửa sổ không tự mở. Lần đầu mở app tự tạo lối tắt (đánh dấu
  `startup-configured` trong thư mục dữ liệu); sau đó giữ lựa chọn của người dùng ở Cài đặt →
  Telegram Bot hoặc Task Manager → Startup apps. Không dùng Windows Service/Task Scheduler.
  Lịch bỏ lỡ khi máy tắt được gửi bù một lần trong khung giờ.
- Python bản Microsoft Store chuyển hướng `%LOCALAPPDATA%\xaydungso` sang
  `%LOCALAPPDATA%\Packages\PythonSoftwareFoundation.Python.3.12_…\LocalCache\Local\xaydungso`;
  GUI và worker thấy cùng một chỗ, nhưng Explorer ở đường dẫn gốc chỉ thấy `launcher.log`.
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

### Telegram

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

### Windows Notification

Dùng Windows PowerShell 5.1 có sẵn và WinRT `ToastNotificationManager`, đăng ký tên hiển thị
`xaydungso` trong HKCU (không cần admin). Nội dung XML được escape và mã hóa base64, không nội
suy thành lệnh PowerShell; kiểm tra exit code, timeout 20 giây.

`sent` nghĩa là Windows đã nhận yêu cầu, không chứng minh popup đã hiện hay người dùng đã đọc.
Cần kiểm tra thực tế: Notifications/Focus Assist, tên ứng dụng, bản đóng gói. Ngoài Windows
kênh này báo thất bại (không giả thành công).
Nguồn: [ToastNotificationManager](https://learn.microsoft.com/en-us/uwp/api/windows.ui.notifications.toastnotificationmanager).

### Giới hạn chống trùng

Claim từng kênh dùng lease 60 giây và token. Tiến trình chết trước khi ghi kết quả → lease hết
hạn cho phép thử lại. Nếu kênh đã nhận tin nhưng tiến trình chết trước khi lưu `sent`, có thể
gửi trùng. Không có transaction phân tán với Telegram/Windows nên **không** bảo đảm
exactly-once; mã nhắc trong nội dung giúp nhận biết các lần gửi cùng lịch.
