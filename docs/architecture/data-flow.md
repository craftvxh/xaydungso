# Luồng dữ liệu — SQLite là nguồn chính

## Hồ sơ

`Form → Application/Domain kiểm tra → SQLite commit → ghi Excel`

- Mọi thêm/sửa/xóa hồ sơ đi qua ứng dụng; xóa là vĩnh viễn sau xác nhận.
- Lưu hồ sơ không tạo hay sửa lịch nhắc. Xóa hồ sơ hủy các lịch liên quan chưa gửi (cùng transaction).
- Không đọc dữ liệu hồ sơ từ Excel.

## Sổ Excel

`SQLite (hồ sơ đã commit) → writer → file .xlsx có sẵn do người dùng chọn`

- Ghi tự động sau mỗi thay đổi hồ sơ; giữ dòng cũ, thêm/sửa theo mã hồ sơ, giữ bố cục workbook.
- Lỗi Excel **không** hoàn tác SQLite; ghi qua file tạm rồi thay thế an toàn.
- Chi tiết: [Excel](../modules/excel/overview.md).

## Nhắc nhở

`Form lịch (+ mẫu thông báo) → SQLite (reminders, deliveries) → worker → Telegram / Windows`

- Nội dung lịch được tạo từ mẫu (`notification_templates`) khi người dùng chọn mẫu trong form;
  lịch lưu nội dung đã điền biến.
- Giờ gửi = hạn xử lý − khoảng báo trước, áp dụng khung 07:00–23:00
  ([quy tắc](../modules/reminders/business-rules.md)).
- Worker claim từng kênh, gửi, ghi kết quả/thử lại; độc lập Qt và Excel. Excel không chứa giờ nhắc.

## Tổng quan và Cài đặt

- Tổng quan đọc một snapshot SQLite qua Application ([metrics](../modules/dashboard/metrics.md)).
- Cài đặt đọc số liệu chỉ đọc (`SqliteDiagnostics`) và lưu cấu hình vào `settings.json`
  (token mã hóa DPAPI); worker đọc lại cấu hình Telegram trước mỗi lần gửi.

## Văn bản Word (tương lai)

`SQLite / tính toán Domain → tạo văn bản → file Word` — hoãn tới khi có mẫu và mapping được duyệt.
