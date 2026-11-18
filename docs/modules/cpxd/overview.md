# Hồ sơ xây dựng (CPXD) — Quy tắc và workflow

Mục tiêu: **quản lý hồ sơ xây dựng** trên Windows, một người dùng, local-first. SQLite là
nguồn dữ liệu chính; sổ Excel chỉ là bản ghi một chiều ([Excel](../excel/overview.md)).
Schema chi tiết: [schema.md](schema.md).

## Quy tắc nghiệp vụ

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
  [Nhắc nhở](../reminders/business-rules.md).

## Ngày giờ trong form

- **Ngày tiếp nhận**, **Hạn xử lý**, **Ngày hẹn trả kết quả**, **Thời gian giao nhận** nhập
  dạng `dd/mm/yyyy hh:mm` (giờ 24 giờ, Asia/Ho_Chi_Minh), bắt buộc đủ số 0 đầu
  (`08:30`, không nhận `8:30`).
- Thêm mới: ngày tiếp nhận và giao nhận tự điền giờ hiện tại, hạn xử lý tự điền sau 1 ngày;
  có thể sửa hoặc để trống.
- Giá trị cũ không đúng định dạng được giữ nguyên nếu người dùng không sửa ô đó.
- Hạn xử lý lưu UTC ISO 8601 (`deadline_at`); các ô còn lại lưu dạng văn bản.

## Workflow trên giao diện

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

## Chưa thuộc phạm vi

Tạo văn bản Word và tính toán xây dựng chuyên ngành — chờ mẫu và quy tắc được duyệt.
Chưa có: loại công trình, bộ lọc nâng cao, sắp xếp tùy chọn, mã hồ sơ tự sinh, địa chỉ
hoặc hạn xử lý bắt buộc.
