# CPXD — Hồ sơ Management Workflow

1. Nhập hồ sơ: mã hồ sơ (bắt buộc, duy nhất), họ và tên (bắt buộc); các trường theo dõi khác theo nhu cầu.
2. Validate đầu vào và commit SQLite.
3. Hiển thị danh sách, tìm kiếm/lọc, mở chi tiết để sửa thông tin tiến độ, đóng dấu, giao nhận.
4. Trạng thái mặc định `Chưa hoàn thành`; người dùng xác nhận chuyển `Đã hoàn thành` khi cần.
5. Xóa hồ sơ vĩnh viễn chỉ sau xác nhận; hủy lịch nhắc chưa gửi liên quan.
6. Sau thay đổi liên quan, xuất lại toàn bộ Excel từ SQLite; nếu xuất lỗi, dữ liệu đã lưu vẫn còn và có thể xuất lại.
7. Người dùng có thể tạo lịch nhắc với thời lượng (có cả 10 giây test). Reminder độc lập với các cột Excel theo dõi.

**Chưa thuộc phạm vi hiện tại:** tính toán xây dựng chuyên ngành và tạo Word theo ba mẫu; sẽ đặc tả riêng khi có mẫu.
