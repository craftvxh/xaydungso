# Excel — Mapping 14 cột A–N

`Sheet1`, tiêu đề A1:N4, dữ liệu từ hàng 5. Lịch sử mẫu: bỏ cột Thời gian nhắc nhở
(16 → 15 cột), rồi bỏ cột STT (15 → 14 cột); SQLite không có thuộc tính STT.

| Cột | Tiêu đề | Field | Cách ghi |
|---|---|---|---|
| A | Mã hồ sơ | `record_code` | Text, duy nhất; dùng để tìm dòng khi ghi |
| B | Họ và tên | `applicant_name` | Text Unicode |
| C | SĐT | `phone` | Text, giữ số 0 đầu |
| D | Địa chỉ | `address` | Text |
| E | Thời gian nhận | `received_at` | Text như đã nhập |
| F | Thời hạn xử lý | `deadline_at` | `dd/MM/yyyy HH:mm:ss` theo giờ Việt Nam; trống nếu chưa có |
| G | Ngày hẹn trả | `return_appointment_date` | Text như đã nhập |
| H | Bản vẽ đóng dấu | `drawing_stamp_status` | `Có` / `Chưa` |
| I | Giấy phép đóng dấu | `permit_stamp_status` | `Có` / `Chưa` |
| J | Thời gian giao nhận | `handover_at` | Text như đã nhập |
| K | Chữ ký | `signature_status` | `Đã ký` / `Chưa ký` |
| L | Người ký nhận | `recipient_name` | Text Unicode |
| M | Trạng thái | `status` | `Chưa hoàn thành` / `Đã hoàn thành` |
| N | Ghi chú | `notes` | Text Unicode |

Không ghi giờ nhắc (`notify_at`), khoảng báo trước hoặc các trường legacy. Không suy ra
deadline từ thời lượng cũ.
