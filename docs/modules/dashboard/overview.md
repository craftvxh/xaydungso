# Dashboard — Tổng quan

Dashboard là **trang mở mặc định** của Xây Dựng Số, sử dụng PyQt6 và QFluentWidgets.
Mục tiêu là xem nhanh tình hình hồ sơ/lịch nhắc và đi tới màn hình quản lý, không
thêm nghiệp vụ tính toán xây dựng hoặc phân tích dự đoán.

## Phạm vi

- Bốn chỉ số: tổng hồ sơ, chưa hoàn thành, đã hoàn thành và lịch nhắc hôm nay.
- Danh sách lịch nhắc sắp tới, hiển thị nội dung, hồ sơ liên kết nếu có và giờ gửi.
- Nút **Quản lý hồ sơ**, **Xem lịch nhắc** và **Tải lại**.
- Chỉ dùng hai trạng thái hồ sơ đã duyệt; không thêm trạng thái hoặc biểu đồ.
- Định nghĩa chỉ số và phạm vi thời gian: [Metrics](metrics.md).

## Nguồn dữ liệu và kiến trúc

`Dashboard widget → Application Dashboard.load() → SQLite read adapter`.

- SQLite là nguồn duy nhất. Không đọc Excel, không dùng bản xuất hoặc cache Excel.
- Application xác định thời điểm và ngày địa phương, trả snapshot chỉ đọc cho UI.
- Infrastructure đọc `records`, `reminders`, `reminder_deliveries` trong một read
  transaction để các chỉ số và danh sách phản ánh cùng snapshot.
- Widget không import SQLite/Database hoặc chạy SQL. Truy vấn chạy ngoài Qt event loop
  bằng task runner hiện có; không tạo worker/scheduler mới cho Dashboard.
- Tái sử dụng schema version 3, không thêm bảng lưu số liệu thống kê.

## Tải, refresh và lỗi

- Tải khi mở ứng dụng; tải lại khi quay về Dashboard, sau thay đổi hồ sơ/lịch nhắc,
  khi bấm Tải lại và mỗi 30 giây lúc Dashboard đang hiển thị và task runner rảnh.
- Đang tải: hiện thông báo và dấu `—`; không giả số 0 hoặc cho kết quả cũ là mới.
- Database rỗng: bốn số 0, thông báo không có lịch sắp tới; nút điều hướng vẫn dùng được.
- Lỗi: hiển thị thông báo ngắn và cho thử lại; không hiện exception SQL hoặc dữ liệu
  nhạy cảm. Chỉ số để `—`, danh sách trống, không báo nhầm database rỗng.

## Điều kiện triển khai / nghiệm thu

Dashboard triển khai sau khi có schema hồ sơ và lịch nhắc cùng các trường thời gian,
trạng thái gửi. Các interface này đã có; không để Dashboard dưới dạng trang rỗng.

Kiểm tra số đếm, chuyển ngày theo giờ Việt Nam, chống nhân đôi do hai kênh, lịch hủy,
lịch đã gửi, thứ tự danh sách, empty/error/retry và điều hướng. Word Generation
vẫn hoãn; Dashboard không phụ thuộc Word hoặc Excel.
