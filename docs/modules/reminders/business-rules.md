# Nhắc nhở — Quy tắc nghiệp vụ

Hướng dẫn chạy/khắc phục sự cố: [operations.md](operations.md).

## Tổng quan

- Module Nhắc nhở **tự quản lý lịch**: hồ sơ chỉ lưu thông tin và hạn xử lý; lưu/sửa hồ sơ
  không tạo, sửa hay hủy lịch.
- Người dùng tạo lịch tại **Nhắc nhở → Tạo nhắc nhở** (hoặc nút chuông trong khung chi tiết
  hồ sơ). Lịch có thể liên kết một hồ sơ (gợi ý hạn xử lý ban đầu) hoặc độc lập.
- Mỗi lịch giữ hạn xử lý và khoảng báo trước của riêng nó; sửa hồ sơ sau đó không đổi lịch.
- Gửi qua **Telegram** và **Windows Notification**, trạng thái và thử lại riêng từng kênh.
- Tiến trình nhắc nền (worker) độc lập Qt và Excel; chạy tiếp khi đóng cửa sổ nếu đã bật
  và máy còn bật. Excel không có cột giờ nhắc và không điều khiển việc gửi.

## Giờ gửi

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

## Lưu, sửa, hủy, xóa

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

## Mẫu nội dung thông báo

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

## Nội dung gửi

Cả hai kênh gửi: tiêu đề `Xây Dựng Số — Nhắc nhở`, nội dung lịch, `Đến hạn: dd/mm/yyyy HH:MM:SS`
và `Mã nhắc: <id>`. Telegram nhận tất cả thành một tin (tối đa 4096 ký tự, phần dài bị rút gọn
nhưng giữ mã nhắc); Windows hiển thị tiêu đề in đậm và phần còn lại.

## Telegram

- **Cài đặt → Telegram Bot → Kiểm tra kết nối** gọi getMe/getChat, không gửi tin; hiển thị tên
  cuộc trò chuyện nhận tin và thời gian phản hồi. **Gửi thử** gửi một tin. Cả hai dùng ô đang
  nhập, không tự lưu, không tự thử lại; cần **Lưu** để lịch dùng cấu hình mới.
- Bot Token và Chat ID là hai thông tin khác nhau; Chat ID của chính bot bị từ chối.
- Lỗi HTTP/mạng được đổi thành thông báo an toàn, không lưu URL/token hoặc nguyên văn lỗi.
- Worker đọc lại cấu hình Telegram đã lưu trước mỗi lần gửi; nếu đọc lỗi thì không gửi tới đích cũ.

## SQLite và Excel

SQLite lưu hạn, khoảng báo trước, giờ gửi và trạng thái từng kênh (UTC, hiển thị giờ Việt Nam).
Excel chỉ có hạn xử lý ở cột F; không ghi khoảng báo trước hay giờ gửi.
