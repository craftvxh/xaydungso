# Lộ trình

Triển khai theo module và thứ tự phụ thuộc; mỗi giai đoạn có test và review. Lộ trình không
được dùng để suy diễn quy tắc nghiệp vụ còn thiếu. Nhật ký chi tiết: [process.md](../../process.md).

| Phase | Nội dung | Trạng thái |
|---|---|---|
| 01 | Foundation: PyQt6/QFluentWidgets, logging, tests, docs | Xong |
| 02 | SQLite schema, domain, repository | Xong — schema v7 |
| 03–04 | Quản lý hồ sơ: danh sách, chi tiết, form, CRUD, thao tác hàng loạt, phân trang | Xong — chờ người dùng nghiệm thu |
| 05 | Nhắc nhở: lịch theo hạn − báo trước, worker, Telegram + Windows, mẫu thông báo | Xong — cần kiểm chứng gửi thật/popup thật trên Windows |
| 05-D | Tổng quan (Dashboard) | Xong — chờ nghiệm thu |
| 06 | Ghi sổ Excel có sẵn (14 cột A–N) | Xong — cần kiểm tra khóa file bằng Microsoft Excel thật |
| 06-S | Cài đặt: Dữ liệu, Telegram, Excel | Xong — chờ nghiệm thu |
| UI | Giao diện theo thiết kế Stitch, icon Windows 11, hiệu ứng, hộp xác nhận | Xong — tiếp tục chỉnh theo phản hồi |
| 07 | Kiểm thử tích hợp và đóng gói Windows (`.exe`) | Script build có sẵn; chưa build/nghiệm thu |
| Sau | Tạo văn bản Word, tính toán xây dựng chuyên ngành | Hoãn — chờ mẫu và quy tắc |

Ngoài phạm vi (AGENTS.md): nhập Excel → SQLite, cloud, sao lưu/khôi phục database, đa người dùng.
Chưa có đặc tả: loại công trình, bản đồ quy hoạch, nhật ký xử lý, tự phát hiện Chat ID,
installer/tự chạy khi đăng nhập.
