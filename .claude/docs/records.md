# Hồ sơ (CPXD) và dữ liệu SQLite

## Hồ sơ xây dựng (CPXD) — Quy tắc và workflow

Mục tiêu: **quản lý hồ sơ xây dựng** trên Windows, một người dùng, local-first. SQLite là
nguồn dữ liệu chính; sổ Excel chỉ là bản ghi một chiều ([Excel](excel.md#excel--ghi-một-chiều-vào-sổ-làm-việc-có-sẵn)).
Schema chi tiết: [schema.md](#schema-sqlite).

### Quy tắc nghiệp vụ

- `record_code` (Mã hồ sơ): bắt buộc, duy nhất (so sánh sau khi trim, không đổi hoa/thường).
- `applicant_name` (Họ và tên người nộp / Chủ đầu tư): bắt buộc.
- Các trường khác không bắt buộc: số điện thoại (giữ số 0 đầu), địa chỉ, ngày tiếp nhận,
  hạn xử lý, ngày hẹn trả, đóng dấu bản vẽ / giấy phép, thời gian giao nhận, chữ ký,
  người ký nhận, ghi chú.
- Hai trạng thái duy nhất: `Chưa hoàn thành` (mặc định), `Đã hoàn thành`. Người dùng tự
  chọn; không tự chuyển khi đóng dấu, ký nhận hay quá hạn.
- Xóa là **xóa vĩnh viễn** sau xác nhận; không có cờ xóa mềm. Xóa hồ sơ hủy các lịch nhắc
  liên quan còn kênh chưa gửi (giữ lịch sử gửi).
- Lưu/sửa hồ sơ **không tạo hoặc sửa lịch nhắc** — lịch thuộc module
  [Nhắc nhở](reminders.md#nhắc-nhở--quy-tắc-nghiệp-vụ).

### Ngày giờ trong form

- **Ngày tiếp nhận**, **Hạn xử lý**, **Ngày hẹn trả kết quả**, **Thời gian giao nhận** nhập
  dạng `dd/mm/yyyy hh:mm` (giờ 24 giờ, Asia/Ho_Chi_Minh), bắt buộc đủ số 0 đầu
  (`08:30`, không nhận `8:30`).
- Thêm mới: ngày tiếp nhận và giao nhận tự điền giờ hiện tại, hạn xử lý tự điền sau 1 ngày;
  có thể sửa hoặc để trống.
- Giá trị cũ không đúng định dạng được giữ nguyên nếu người dùng không sửa ô đó.
- Hạn xử lý lưu UTC ISO 8601 (`deadline_at`); các ô còn lại lưu dạng văn bản.

### Workflow trên giao diện

1. **Quản lý hồ sơ → Thêm hồ sơ**: nhập mã và họ tên, các trường khác khi cần → **Lưu hồ sơ**.
   Lỗi kiểm tra hoặc trùng mã giữ nguyên dữ liệu đang nhập.
2. Sau khi commit SQLite, ứng dụng **tự ghi file Excel** làm việc. Lỗi Excel (file mở/khóa)
   không hoàn tác SQLite; ghi lại bằng lần lưu tiếp theo hoặc **Cài đặt → Sổ theo dõi
   Excel → Ghi lại ngay**.
3. Tìm kiếm Unicode (mã, tên, SĐT, địa chỉ, người nhận, ghi chú), lọc theo trạng thái,
   phân trang 14 dòng. Chọn dòng để mở khung **Chi tiết hồ sơ**; nhấp đúp hoặc **Sửa hồ sơ**
   để sửa.
4. Tick nhiều hồ sơ để **Hoàn thành / Chưa hoàn thành / Xóa** hàng loạt (Excel ghi một lần
   sau cùng; lỗi giữa chừng vẫn giữ các hồ sơ đã commit).
5. Nút chuông trong khung chi tiết mở form **Tạo lịch nhắc** cho hồ sơ đó.
6. Từ Tổng quan, **Chi tiết** ở bảng "Hồ sơ cần chú ý" mở đúng hồ sơ (xóa tìm kiếm/bộ lọc,
   nhảy tới trang chứa hồ sơ).

### Chưa thuộc phạm vi

Tạo văn bản Word và tính toán xây dựng chuyên ngành — chờ mẫu và quy tắc được duyệt.
Chưa có: loại công trình, bộ lọc nâng cao, sắp xếp tùy chọn, mã hồ sơ tự sinh, địa chỉ
hoặc hạn xử lý bắt buộc.

## Schema SQLite

Quy tắc nghiệp vụ: [CPXD](#hồ-sơ-xây-dựng-cpxd--quy-tắc-và-workflow). Mapping sang Excel: [14 cột A–N](excel.md#excel--mapping-14-cột-an).
Trường kỹ thuật không được ghi vào workbook.

### Version và migration

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

### records

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

### excel_record_links

`(workbook_path, record_id, record_code)` ghi nhớ mã từng được ứng dụng ghi vào từng
workbook, để đổi mã/xóa đúng dòng. Không cascade khi xóa hồ sơ (cần giữ tới lần ghi
Excel sau). Không lưu dữ liệu đọc từ Excel.

### reminders và reminder_deliveries

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
  best effort, không exactly-once ([vận hành](reminders.md#nhắc-nhở--vận-hành-và-khắc-phục-sự-cố)).

### notification_templates

| Trường | Ghi chú |
|---|---|
| `id` | Khóa chính tự tăng |
| `name`, `body` | Bắt buộc (không rỗng); `body` là văn bản thường nhiều dòng có biến `{{...}}` |
| `is_default` | 0/1; unique index một phần bảo đảm tối đa một mẫu mặc định |
| `updated_at` | UTC ISO 8601 |

Quy tắc mẫu: [Nhắc nhở → Mẫu nội dung thông báo](reminders.md#mẫu-nội-dung-thông-báo).
