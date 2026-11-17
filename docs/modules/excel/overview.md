# Excel Tracking Register — Vai trò

## Mẫu đã chốt

- File template: `templates/so_theo_doi.xlsx` (đổi tên từ `so_theo_doi(1).xlsx`, không sửa nội dung workbook).
- Worksheet: `Sheet1`; tiêu đề `SỔ THEO DÕI HỒ SƠ XÂY DỰNG`.
- Header A1:P4, dữ liệu từ hàng 5; 16 cột.

## Vai trò

Excel chỉ là **sổ theo dõi được xuất** từ SQLite. Người dùng thao tác CRUD trong ứng dụng. Workbook không phải nguồn dữ liệu độc lập, không có chiều Excel → SQLite và không chạy lịch nhắc nhở.

- Giữ template nguyên trạng trong repository.
- Bản xuất được tạo ở **thư mục dữ liệu ứng dụng**, không ghi đè bản template trong `docs/`.
- Khi hồ sơ SQLite thay đổi, tạo lại toàn bộ sổ theo [quy trình xuất](export-workflow.md).
- [Mapping cột A–P](field-mapping.md) xác định dữ liệu được hiển thị.
- Không đưa file Excel chứa dữ liệu cá nhân thực vào Git.
