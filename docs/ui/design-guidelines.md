# Giao diện — Hướng dẫn thiết kế

PyQt6 + **PyQt6-Fluent-Widgets** (`qfluentwidgets`), phong cách Windows 11. Thiết kế chi tiết
lấy từ các bản Stitch người dùng cung cấp (bảng màu "Slate Minimal Desktop"). Mỗi trang cần
người dùng nghiệm thu trên Windows.

## Nguyên tắc chung

- Không đặt SQL, quy tắc nghiệp vụ hay ghi file trong widget; tác vụ I/O chạy ngoài Qt event
  loop (`presentation/tasks.py`). Lỗi lưu SQLite và lỗi ghi Excel được báo riêng.
- Dùng layout, không định vị cố định; chữ tiếng Việt hiển thị đúng Unicode.
- Form giữ dữ liệu khi kiểm tra hoặc lưu thất bại; không đóng khi đang lưu.
- Mọi thao tác xóa vĩnh viễn, hủy lịch hay bỏ thay đổi cần xác nhận.
- Không dựng UI cho phần chưa có dữ liệu/quy tắc (Word, loại công trình, bản đồ quy hoạch,
  bộ lọc nâng cao, nhật ký xử lý…).

## Màu, chữ, icon, chuyển động

- **Theme sáng cố định**, không theo dark mode Windows, tắt Mica. Nền trang `#faf8ff`, thẻ và
  bảng nền trắng, chữ gần đen `#131b2e`, chữ phụ `#44474c`, đường kẻ `#e4e5eb`. Màu chủ đạo navy
  `#1d2b3e`, nút chính slate `#334155`. Badge: chưa hoàn thành vàng (`#fef3c7`/`#b45309`),
  hoàn thành xanh lá (`#dcfce7`/`#15803d`), lỗi/quá hạn đỏ (`#fee2e2`/`#b91c1c`).
  Token màu: `COLORS` trong `presentation/theme.py`.
- `presentation/theme.py` ép nền trắng/chữ tối cho widget thường; widget có thiết kế riêng dùng
  `styled()` hoặc thuộc tính `xdsStyled` để giữ style của mình.
- Font Segoe UI; mã hồ sơ dùng Consolas đậm.
- **Icon:** Fluent UI System Icons của Microsoft (20px regular, MIT) trong `presentation/icons/`
  kèm `LICENSE`, dùng qua `presentation/icons.py` (`Icon.X`); tô màu bằng `colored_icon()`.
  Không dùng `FluentIcon` của qfluentwidgets.
- **Ô tick:** 16px, bo 4px, slate khi chọn (bảng: `CompactCheckDelegate`; widget:
  `compact_checkbox`). Bấm vào cột ô tick chỉ đánh dấu, không chọn dòng.
- **Chuyển động** (`presentation/motion.py`, ~180 ms ease-out): khung chi tiết trượt mở, thanh
  thao tác hàng loạt mở dần, hộp thoại hiện dần và nhích lên. Chỉ hiệu ứng khi hiện; ẩn tức thì.
- **Hộp xác nhận** `ConfirmBox` (`presentation/confirm.py`): chỉ hiện thẻ hộp thoại, phía sau làm
  mờ nhẹ bằng lớp `#0F172A` ~30%; nút nguy hiểm màu đỏ; nút an toàn được focus sẵn.
- **Hộp thoại nhập liệu** dùng khung chung `presentation/card_dialog.py`: thẻ bo góc không viền
  hệ thống, tiêu đề có icon và nút đóng, kéo ở thanh tiêu đề, chân có Hủy / Lưu.

## Khung cửa sổ (`presentation/shell.py`)

- `FluentWindow` 1280 × 800 lúc mở. Thanh tiêu đề "Xây Dựng Số - Giải pháp chuyển đổi số",
  thanh tiêu đề và thanh điều hướng nền `#f2f3ff`; không có dòng logo trong thanh điều hướng.
- Mục: **Tổng quan**, **Quản lý hồ sơ**, **Nhắc nhở**, và **Cài đặt** ở đáy. Badge: số hồ sơ chưa
  hoàn thành (Quản lý hồ sơ), số lịch nhắc hôm nay (Nhắc nhở, màu đỏ); ẩn khi bằng 0.

## Tổng quan

Xem [Dashboard](../modules/dashboard/overview.md): 4 thẻ, bảng Hồ sơ cần chú ý, thẻ lịch sắp tới.

## Quản lý hồ sơ (`presentation/pages.py`, `record_widgets.py`)

- Tiêu đề có ô icon + **Mở sổ Excel / Tải lại / Thêm hồ sơ**. Thanh công cụ: ô tìm kiếm, bộ lọc
  trạng thái dạng segmented kèm số lượng, tổng số hồ sơ đang hiển thị.
- Bảng (thứ tự người dùng chọn): ô tick, mã, họ tên, số điện thoại, địa chỉ, ngày tiếp nhận,
  hạn xử lý, ngày hẹn trả, giao nhận, trạng thái (badge). Đường kẻ cột nhạt; cuộn ngang khi bảng
  rộng hơn khung, phần dư chia cho Họ tên / Địa chỉ khi khung rộng hơn; kéo được độ rộng cột.
  Hạn đã qua của hồ sơ chưa hoàn thành hiển thị đỏ đậm. Phân trang 14 dòng; tìm kiếm/đổi bộ lọc
  về trang 1.
- Tick nhiều dòng → thanh hàng loạt **Hoàn thành / Chưa hoàn thành / Xóa / Bỏ chọn**.
- Khung **Chi tiết hồ sơ** (chỉ đọc) chỉ mở khi chọn một dòng, đóng bằng X: Thông tin hồ sơ;
  Quy trình & thời gian xử lý (nhãn Còn N ngày / Hôm nay / Quá hạn); Kết quả & tình trạng;
  nút **Sửa hồ sơ**, chuông (tạo lịch nhắc), **Xóa hồ sơ**. Nhấp đúp dòng để sửa.
- Hộp thoại **Thêm hồ sơ mới / Sửa hồ sơ** (`record_dialog.py`): 1. Thông tin người nộp & địa
  điểm; 2. Quy trình & thời gian xử lý (định dạng `dd/MM/yyyy HH:mm`); 3. Tình trạng thẩm định &
  kết quả (thẻ chọn trạng thái, đóng dấu Bản vẽ kỹ thuật / Giấy phép XD, giao nhận, người ký
  nhận, chữ ký) và Ghi chú. Quy tắc nhập: [CPXD](../modules/cpxd/overview.md).

## Nhắc nhở (`presentation/reminders_page.py`)

- Tiêu đề + chip trạng thái nhắc nền; **Bật/Dừng nhắc nền**, **Cấu hình**, **Tạo nhắc nhở**.
  Ba thẻ Chờ gửi / Đã gửi / Gửi lỗi. Thanh công cụ: tìm kiếm, lọc trạng thái, sắp xếp
  Mới nhất/Cũ nhất, số lời nhắc, tải lại.
- Bảng: ô tick, mã hồ sơ, chủ đầu tư/công trình, kênh gửi (trạng thái từng kênh, lỗi ở tooltip),
  nội dung + báo trước/hạn, thời gian dự kiến, trạng thái, thao tác Sửa / Hủy / Xóa; thanh hàng
  loạt Xóa / Bỏ chọn; phân trang 14 dòng.
- Hộp thoại **Tạo / Sửa lịch nhắc** (`reminder_dialog.py`): A. hồ sơ liên quan, hạn xử lý, khoảng
  thời gian nhắc, ô thời điểm gửi dự kiến + giải thích; B. chọn mẫu thông báo + ô nội dung nhiều
  dòng; C. xem trước đúng nội dung worker gửi và hai kênh; ô Bật nhắc nền sau khi lưu.
- Màn hình **Cấu hình nội dung thông báo** (`templates_page.py`, mở từ nút Cấu hình, không có mục
  riêng trên thanh điều hướng): danh sách mẫu + tìm kiếm; trình sửa (tên, nội dung, gạch đầu
  dòng, đường kẻ, emoji, chèn biến), đặt mặc định, xem trước Telegram/Windows Toast với dữ liệu
  minh họa; Xóa mẫu / Hủy thay đổi / Lưu mẫu; hỏi trước khi bỏ thay đổi chưa lưu.
- Quy tắc: [Nhắc nhở](../modules/reminders/business-rules.md).

## Cài đặt (`presentation/settings.py`)

Cột trái chọn **Dữ liệu (SQLite)**, **Telegram Bot**, **Sổ theo dõi Excel**; nội dung từng mục
trong [Cài đặt](../modules/settings/overview.md). Hộp chọn file dùng Qt dialog trong ứng dụng.
