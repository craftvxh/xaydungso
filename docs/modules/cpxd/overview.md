# Module CPXD — Tổng quan

Mục tiêu trước mắt: **quản lý hồ sơ xây dựng** trên Windows, một người dùng, local-first, lưu SQLite và xuất sổ Excel theo mẫu đã duyệt.

## Quyết định nghiệp vụ

- `record_code`: bắt buộc và duy nhất.
- `applicant_name`: bắt buộc.
- `phone`, `address`: không bắt buộc ở MVP.
- Trạng thái duy nhất: `Chưa hoàn thành` (mặc định), `Đã hoàn thành`.
- Trạng thái `Đã hoàn thành` do người dùng chủ động đặt; không tự chuyển khi đóng dấu/giao nhận.
- Xóa hồ sơ là xóa vĩnh viễn, UI cần xác nhận, không có `is_deleted`.
- SQLite là nguồn chính; sổ Excel chỉ là bản xuất một chiều.

## Phạm vi

Ưu tiên: schema SQLite, danh sách hồ sơ, form chi tiết, CRUD, reminder, xuất Excel.
**Word Generation và calculation nghiệp vụ xây dựng để giai đoạn sau**, không chặn việc hoàn thành module quản lý hồ sơ.
