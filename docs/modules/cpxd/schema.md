# Schema SQLite

Quy tắc nghiệp vụ: [CPXD](overview.md). Mapping sang Excel: [14 cột A–N](../excel/field-mapping.md).
Trường kỹ thuật không được ghi vào workbook.

## Version và migration

| Version | Thay đổi |
|---|---|
| 1 | Baseline Foundation, chưa có bảng nghiệp vụ |
| 2 | Bảng `records` và index thứ tự xuất |
| 3 | `reminders`, `reminder_deliveries`, index lịch đến hạn |
| 4 | Deadline/khoảng báo trước, cờ lịch tự động, `excel_record_links`; giữ dữ liệu cũ |
| 5 | Đặt `record_managed=0`: lịch tự động cũ chuyển sang quản lý riêng, giữ lịch và kết quả gửi |
| 6 | Đổi tên `overall_processing_time` → `return_appointment_date` (Ngày hẹn trả), giữ giá trị |
| 7 | Bảng `notification_templates`, tạo sẵn 4 mẫu, tối đa một mẫu mặc định |

- `PRAGMA application_id = 0x5844534F`, `PRAGMA user_version = 7`.
- Migration chạy liên tiếp trong một transaction `BEGIN IMMEDIATE`; lỗi rollback cả schema
  và version. Không downgrade database mới hơn; database của ứng dụng khác bị từ chối.
- Mỗi connection bật foreign keys và đóng sau khi dùng. Không có backup/restore, không xóa mềm.

## records

| Trường | Kiểu | Ghi chú |
|---|---|---|
| `id` | INTEGER | Khóa chính tự tăng, chỉ dùng nội bộ (không có STT) |
| `record_code` | TEXT | Bắt buộc, UNIQUE, trim hai đầu |
| `applicant_name` | TEXT | Bắt buộc, trim hai đầu |
| `phone`, `address` | TEXT | Có thể trống; SĐT giữ số 0 đầu |
| `received_at` | TEXT | Ngày tiếp nhận, văn bản `dd/mm/yyyy hh:mm` |
| `deadline_at` | TEXT | Hạn xử lý, UTC ISO 8601 hoặc rỗng |
| `return_appointment_date` | TEXT | Ngày hẹn trả, văn bản `dd/mm/yyyy hh:mm` |
| `drawing_stamp_status`, `permit_stamp_status` | INTEGER 0/1 | Đóng dấu bản vẽ / giấy phép |
| `handover_at` | TEXT | Thời gian giao nhận, văn bản |
| `signature_status` | INTEGER 0/1 | Chữ ký |
| `recipient_name`, `notes` | TEXT | Có thể trống |
| `status` | TEXT | CHECK: `Chưa hoàn thành` / `Đã hoàn thành` |
| `created_at` | TEXT | UTC ISO 8601, không đổi khi sửa; thứ tự danh sách và Excel |
| `processing_duration`, `reminder_tracking_time`, `reminder_lead_seconds` | — | Legacy, giữ dữ liệu cũ, không dùng cho form/Excel |

Tìm kiếm dùng Unicode `casefold` trong ứng dụng; `%`/`_` là ký tự thường, không phải
wildcard SQL. Không thêm regex SĐT hay điều kiện hoàn thành chưa được yêu cầu.

## excel_record_links

`(workbook_path, record_id, record_code)` ghi nhớ mã từng được ứng dụng ghi vào từng
workbook, để đổi mã/xóa đúng dòng. Không cascade khi xóa hồ sơ (cần giữ tới lần ghi
Excel sau). Không lưu dữ liệu đọc từ Excel.

## reminders và reminder_deliveries

- `reminders.id` là UUID. `record_id` tùy chọn, `ON DELETE SET NULL`. Lưu nội dung,
  deadline, `lead_seconds` (khoảng báo trước), `notify_at` (giờ gửi sau điều chỉnh),
  `created_at`, `cancelled`; legacy `start_at`/`duration`, `record_managed`.
- Timestamp UTC ISO 8601; tính và hiển thị theo Asia/Ho_Chi_Minh.
- `reminder_deliveries`: khóa `(reminder_id, channel)`, channel `telegram` hoặc `windows`;
  `state` `pending` / `sending` / `sent` / `failed`, số lần thử, giờ thử lại, lease 60 giây,
  claim token, `sent_at`, lỗi đã loại thông tin nhạy cảm. `ON DELETE CASCADE` theo lịch.
- Xóa hồ sơ (cùng transaction): hủy lịch liên quan còn kênh chưa gửi rồi xóa hồ sơ; lịch
  sử gửi giữ lại với `record_id = NULL`.
- Xóa lịch nhắc là vĩnh viễn (xóa luôn deliveries); lịch có kênh đang `sending` được giữ.
- Claim dùng transaction ghi và token riêng; kênh `sent` không được chọn lại. Chống trùng
  best effort, không exactly-once ([vận hành](../reminders/operations.md)).

## notification_templates

| Trường | Ghi chú |
|---|---|
| `id` | Khóa chính tự tăng |
| `name`, `body` | Bắt buộc (không rỗng); `body` là văn bản thường nhiều dòng có biến `{{...}}` |
| `is_default` | 0/1; unique index một phần bảo đảm tối đa một mẫu mặc định |
| `updated_at` | UTC ISO 8601 |

Quy tắc mẫu: [Nhắc nhở → Mẫu nội dung thông báo](../reminders/business-rules.md#mẫu-nội-dung-thông-báo).
