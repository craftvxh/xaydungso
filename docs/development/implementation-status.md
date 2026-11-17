# Trạng thái implementation

**Cập nhật:** 17/11/2026. Báo cáo này đối chiếu bộ đặc tả đã được cập nhật trong
phiên hiện tại, không dùng các blocker schema/template của phiên trước làm lý do dừng.

## Đã triển khai

- **Dashboard:** trang mở mặc định; bốn chỉ số và tối đa 10 lịch sắp tới. Application
  định nghĩa ngày Việt Nam, adapter đọc snapshot SQLite trong một transaction;
  widget không chạy SQL/đọc Excel. Có loading/empty/error/retry và điều hướng Hồ sơ/Nhắc nhở.
- **Foundation:** entry point, cấu hình, logging, Qt lifecycle và package phân lớp.
- **SQLite:** migration version 1 → 2 → 3; records/reminders/reminder_deliveries,
  constraints và transaction; [schema chi tiết](../modules/cpxd/schema.md).
- **UI/CRUD:** từ Dashboard đi tới danh sách Hồ sơ; thêm, xem/sửa, xóa vĩnh viễn có xác nhận,
  tìm kiếm Unicode và lọc trạng thái; form giữ dữ liệu khi lỗi. Hai trạng thái đúng đặc tả.
- **Excel:** mapping đầy đủ A–P; thứ tự `created_at ASC, id ASC`; xuất lại sau commit;
  lỗi xuất không rollback dữ liệu; nút Xuất lại Excel và Mở sổ Excel. Template bất biến,
  file tạm cùng filesystem được kiểm tra trước khi thay thế.
- **Reminder:** tính thời gian thực tại Asia/Ho_Chi_Minh, biên 07:00/23:00, ngoại lệ
  22:00 đã qua, 10 giây test, gửi bù, sửa/hủy; SQLite lưu trạng thái từng kênh,
  claim/lease/retry và không gửi lại kênh đã thành công.
- **Runtime:** worker độc lập Qt, nút bật/dừng, khóa OS chống chạy nhiều worker,
  CLI riêng. GUI có thể đóng khi worker vẫn chạy.
- **Transports:** Telegram HTTPS và WinRT toast qua Windows PowerShell. Có test mock
  request/payload/timeout/failure. Không gửi live notification trong test.
- **Packaging:** script Windows-only, PyInstaller, template được thêm vào bundle,
  tzdata Windows-only và worker entry point cho bản frozen.

## Chưa thuộc phạm vi / chưa kiểm chứng

- Word và tính toán xây dựng chuyên ngành được hoãn theo quyết định mới; không có generator giả.
- Chưa gửi Telegram thật (không dùng credentials thật trong phiên kiểm tra).
- Chưa chạy Windows Notification thật, build executable hoặc kiểm tra bản bundle trên Windows.
- Chưa kiểm tra khóa file bằng Microsoft Excel thật; test mô phỏng lỗi thay thế và xác nhận bản cũ được giữ.
- Không cài service/autostart/installer. Worker phải được người dùng bật và máy phải đang chạy.
- Chống gửi trùng là best effort, không phải exactly-once; xem [vận hành](../modules/reminders/operations.md).

## Kiểm tra đã thực hiện

- Bộ test bao phủ import/lifecycle, migration/rollback, CRUD/constraints, mapping,
  tái xuất sau thêm/sửa/xóa, lỗi xuất sau commit, reminder boundaries, retry riêng
  kênh, cạnh tranh claim, lease recovery, hủy khi xóa hồ sơ, và worker không cần Qt.
- Test giao diện thật dùng Qt offscreen: thêm, lỗi bắt buộc, trùng mã giữ input,
  sửa trạng thái, search/filter, tạo lịch, hủy xóa và xác nhận xóa, retry export.
- Đã mở desktop Linux với dữ liệu mẫu trong thư mục tạm, xem danh sách/form/lịch
  nhắc và sửa lỗi tương phản form. Không dùng dữ liệu cá nhân thật.
- Kết quả các lệnh cuối và số test được ghi trong [process.md](../../process.md).
