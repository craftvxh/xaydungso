# Excel Field Mapping — `so_theo_doi.xlsx`

Workbook chuẩn có `Sheet1`, vùng tiêu đề `A1:P4`; dữ liệu bắt đầu hàng 5. 16 cột A–P. Đây là mapping ứng dụng dự kiến, tên field Python cần đồng bộ với schema được triển khai.

| Cột | Nội dung | Field SQLite dự kiến | Cách xuất đã chốt |
|---|---|---|---|
| A | STT | Không lưu riêng | 1..N theo thứ tự tạo hồ sơ tăng dần |
| B | Mã hồ sơ | `record_code` | Text, bắt buộc, duy nhất |
| C | Họ và tên | `applicant_name` | Text Unicode, bắt buộc |
| D | SĐT | `phone` | Text giữ số 0 đầu; có thể trống |
| E | Địa chỉ | `address` | Text; có thể trống trong MVP |
| F | Thời gian nhận | `received_at` | Theo dõi, không tự tính |
| G | Thời hạn xử lý | `processing_duration` | Hiển thị dễ đọc: `10 giây` (test), `1 giờ`, `12 giờ`, `24 giờ`, hoặc thời lượng đã nhập |
| H | Thời gian nhắc nhở | `reminder_tracking_time` | Trường theo dõi nhập thủ công; không tự gán `notify_at` |
| I | Thời hạn xử lý toàn quy trình | `overall_processing_time` | Theo dõi, không tự tính |
| J | Bản vẽ thiết kế đã đóng dấu | `drawing_stamp_status` | `Có` / `Chưa` |
| K | Giấy phép đã đóng dấu | `permit_stamp_status` | `Có` / `Chưa` |
| L | Thời gian giao nhận | `handover_at` | Theo dõi, không tự tính |
| M | Chữ ký | `signature_status` | `Đã ký` / `Chưa ký` (không nhúng ảnh chữ ký) |
| N | Họ và tên người ký nhận | `recipient_name` | Text Unicode |
| O | Trạng thái | `status` | `Chưa hoàn thành` / `Đã hoàn thành`; mặc định chưa hoàn thành |
| P | Ghi chú | `notes` | Text Unicode |

## Ranh giới dữ liệu

- SQLite là nguồn dữ liệu gốc. Exporter chỉ đọc các hồ sơ đã commit.
- Cột G là *giá trị thời lượng hiển thị*, không phải cột timestamp được tính.
- Không dùng Excel làm input cho scheduler. `start_at`, `deadline_at`, `notify_at` lưu riêng trong dữ liệu reminder.
- Các cột thời gian F/H/I/L là thông tin người dùng theo dõi; cần giữ kiểu hiển thị tương ứng với dữ liệu đầu vào, không tự suy ra phép tính.
- File Excel không lưu trường nội bộ `created_at`; trường này chỉ dùng sắp xếp.
