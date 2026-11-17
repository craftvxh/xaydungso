# Schema SQLite đã triển khai

Schema bám theo [quyết định CPXD](overview.md) và [mapping A–P](../excel/field-mapping.md).
Các trường kỹ thuật không được thêm vào workbook xuất.

## Version và migration

- Version 1: baseline Foundation cũ, chưa có bảng nghiệp vụ; giữ nguyên để nâng cấp tại chỗ.
- Version 2: bảng `records` và index thứ tự xuất.
- Version 3: `reminders`, `reminder_deliveries` và index lịch đến hạn.
- `PRAGMA application_id = 0x5844534F`, `PRAGMA user_version = 3`.
- Migration liên tiếp, thực hiện toàn bộ phần chưa áp dụng trong một transaction
  `BEGIN IMMEDIATE`; lỗi rollback cả schema và version. Không downgrade database mới hơn.
- Mỗi connection bật foreign keys và đóng sau sử dụng. Không có backup/restore hoặc soft delete hồ sơ.

## Bảng records

| Trường | Kiểu lưu | Ràng buộc / ý nghĩa |
|---|---|---|
| `id` | INTEGER | Primary key tự tăng, không tái dùng làm STT Excel |
| `record_code` | TEXT | Bắt buộc, duy nhất; ứng dụng trim khoảng trắng hai đầu |
| `applicant_name` | TEXT | Bắt buộc, ứng dụng trim khoảng trắng hai đầu |
| `phone`, `address` | TEXT | Có thể trống; số điện thoại giữ nguyên số 0 đầu |
| `received_at` | TEXT | Thông tin theo dõi nhập thủ công |
| `processing_duration` | INTEGER hoặc NULL | Số giây nguyên dương; render dễ đọc ở cột G |
| `reminder_tracking_time` | TEXT | Theo dõi thủ công, không đồng nhất với `notify_at` |
| `overall_processing_time` | TEXT | Thông tin theo dõi thủ công |
| `drawing_stamp_status`, `permit_stamp_status` | INTEGER 0/1 | Mặc định 0; xuất `Chưa` / `Có` |
| `handover_at` | TEXT | Thông tin theo dõi thủ công |
| `signature_status` | INTEGER 0/1 | Mặc định 0; xuất `Chưa ký` / `Đã ký` |
| `recipient_name`, `notes` | TEXT | Có thể trống |
| `status` | TEXT | CHECK đúng hai trạng thái; mặc định `Chưa hoàn thành` |
| `created_at` | TEXT | UTC ISO 8601, không thay đổi khi sửa |

Các cột theo dõi F/H/I/L được lưu và xuất đúng nội dung văn bản người dùng nhập;
không tự parse, tự tính hoặc đổi thành timestamp. Thời lượng G lưu riêng theo giây.
UI hỗ trợ preset 10 giây, 1 giờ, 12 giờ, 24 giờ và số giây dương nhập tay.

Uniqueness dùng so sánh TEXT mặc định của SQLite sau khi ứng dụng trim mã; không
tự quy đổi hoa/thường hoặc sửa mã. Không bổ sung regex điện thoại hoặc điều kiện
hoàn thành chưa được yêu cầu. Tìm kiếm dùng Unicode `casefold` trong ứng dụng;
ký tự `%`/`_` là văn bản tìm kiếm, không phải wildcard SQL.

## Bảng reminders

UUID `id` là khóa chính. `record_id` tùy chọn liên kết `records(id)` với
`ON DELETE SET NULL`. Nội dung nhắc, start/duration/deadline/notify/created được lưu
riêng. Timestamp lịch nhắc là UTC ISO 8601; tính và hiển thị theo Asia/Ho_Chi_Minh.
`cancelled` là trạng thái lịch, không phải soft-delete hồ sơ.

Xóa hồ sơ thực hiện trong cùng transaction: hủy lịch liên quan còn kênh chưa gửi,
sau đó DELETE hồ sơ. Lịch sử và kết quả gửi được giữ với `record_id = NULL`.

## Bảng reminder_deliveries

Khóa ghép `(reminder_id, channel)`; channel chỉ `telegram` hoặc `windows`.
Lưu `state` (`pending`, `sending`, `sent`, `failed`), số lần thử, giờ thử tiếp,
lease, token claim, giờ gửi thành công và lỗi đã loại thông tin nhạy cảm.

Claim sử dụng transaction ghi và token riêng; kênh `sent` không được chọn lại.
Lease hết hạn sau 60 giây cho phép phục hồi khi tiến trình chết. Token cũ không
thể ghi đè kết quả claim mới. Đây là chống trùng tốt nhất có thể, không bảo đảm
exactly-once qua mạng; xem [vận hành nhắc](../reminders/operations.md).
