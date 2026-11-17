# UI Design Guidelines

## Stack

PyQt6 + **PyQt6-Fluent-Widgets** (`qfluentwidgets`); hướng thiết kế Fluent Design trên Windows 11.

## Quy tắc

- Dùng `FluentWindow` cho cửa sổ chính khi Foundation triển khai.
- Ưu tiên Fluent components; chỉ dùng QWidget native khi phù hợp hơn về chức năng.
- Dùng layout thay vì fixed positioning; spacing nhất quán, chữ tiếng Việt hiển thị đúng Unicode.
- Không trộn tính toán nghiệp vụ, SQL hoặc xử lý xuất Excel trong widget.
- Tác vụ I/O dài không chặn main Qt event loop.
- Tránh stylesheet tùy biến nặng hoặc hệ thống theme riêng khi thư viện đã hỗ trợ.
- Mọi thao tác xóa vĩnh viễn cần xác nhận rõ ràng.

## Phase 01.1

Chỉ cần main FluentWindow và trang chào. Chưa tạo menu nghiệp vụ, bảng dữ liệu hoặc các trang rỗng.

## Sau Foundation

Thiết kế danh sách hồ sơ và trang chi tiết từ nhu cầu thực tế. Không sao chép 16 cột Excel lên một màn hình chỉ vì đó là layout xuất báo cáo.

## Giao diện quản lý hiện tại

- Mở mặc định vào Dashboard (Tổng quan); nút Quản lý hồ sơ dẫn tới trang Hồ sơ.
- Dashboard dùng bốn thẻ số liệu và bảng lịch sắp tới, có loading/empty/error/retry; xem [metrics](../modules/dashboard/metrics.md). Chỉ đọc dữ liệu qua Application, không truy vấn SQLite trong widget hoặc dùng Excel làm nguồn.
- Bảng gọn: mã, họ tên, số điện thoại, thời gian nhận và trạng thái; các trường còn lại ở form chi tiết có cuộn.
- Tìm kiếm Unicode theo mã/tên/điện thoại/địa chỉ/người nhận/ghi chú, kèm bộ lọc trạng thái.
- Lưu và xuất Excel chạy ngoài Qt event loop. Lỗi xuất được phân biệt với lỗi lưu SQLite.
- Trang Nhắc nhở có tạo/sửa/hủy lịch, kết quả riêng từng kênh và điều khiển tiến trình nền.
- Form giữ dữ liệu khi validation hoặc lưu thất bại; không đóng cửa sổ khi còn công việc lưu/xuất đang chạy.
- Thiết kế này cần người dùng nghiệm thu trên Windows; không thêm UI Word khi chưa có mẫu.
