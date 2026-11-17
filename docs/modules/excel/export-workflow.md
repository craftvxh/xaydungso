# SQLite → Excel Export Workflow

## Đầu vào / đầu ra

- Template bất biến: `docs/modules/excel/templates/so_theo_doi.xlsx`.
- File xuất mặc định: `so_theo_doi.xlsx` trong **thư mục dữ liệu ứng dụng** (ngoài repository). Tên giống template nhưng đường dẫn khác nhau.
- SQLite là nguồn dữ liệu duy nhất; **không nhập Excel ngược SQLite**, không đồng bộ cloud.

## Quy trình

1. Sau thao tác tạo/sửa/xóa hồ sơ đã **commit SQLite**, yêu cầu exporter tạo lại toàn bộ sổ.
2. Truy vấn danh sách theo `created_at ASC, id ASC` để ổn định thứ tự.
3. Mở **bản sao** mẫu; bảo toàn sheet `Sheet1`, tiêu đề A1:P4, merged cells, styles.
4. Ghi 16 cột A–P từ hàng 5; STT bắt đầu 1 và tăng liên tiếp, không dựa vào ID DB.
5. Giữ số điện thoại dưới dạng text, Unicode tiếng Việt; đặt format ngày/giờ phù hợp với giá trị thực tế.
6. Lưu vào file tạm cùng thư mục đích, kiểm tra tính hợp lệ, thay thế đích an toàn nếu hệ điều hành cho phép.
7. Nếu lỗi (ví dụ Excel đang khóa file), giữ file đích cũ và SQLite, báo lỗi và cung cấp chức năng **Xuất lại Excel**.

## Kiểm thử bắt buộc

- Không hồ sơ, một hồ sơ, nhiều hồ sơ, sửa và xóa hồ sơ.
- Giữ nguyên template gốc, merged cells, đường viền và header.
- STT liên tục, thứ tự ổn định, tiếng Việt/đầu số 0, kiểm tra đầy đủ A–P.
- Lỗi file đích bị khóa, lỗi ghi, ghi dang dở: không phá bản xuất trước.

**Lưu ý:** Xuất lại sau commit không có nghĩa là ghi thành công; GUI phải phân biệt `SQLite đã lưu` và `Excel chưa cập nhật` khi gặp lỗi.
