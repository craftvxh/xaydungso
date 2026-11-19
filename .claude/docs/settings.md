# Cài đặt

Trang **Cài đặt** (đáy thanh điều hướng) quản lý cấu hình cho một người dùng trên máy.
Bố cục theo ảnh người dùng gửi 19/11/2026: tiêu đề `Cài đặt hệ thống / <mục>`, cột trái chọn
mục, nội dung bên phải. Thông báo kết quả hiện ở cuối trang và được xóa khi đổi mục.

## Dữ liệu (SQLite) — chỉ đọc

- Đường dẫn tệp `xaydungso.sqlite3` (không sửa được) và **Mở thư mục** dữ liệu.
- Thẻ: trạng thái kết nối, phiên bản SQLite, dung lượng tệp, tổng số hồ sơ, phiên bản dữ liệu
  (schema), kiểm tra toàn vẹn (`PRAGMA quick_check`); **Kiểm tra lại** và giờ kiểm tra gần nhất.
- Không sửa, di chuyển, sao lưu hay khôi phục database.

## Telegram Bot

- Chip: Chưa kiểm tra / Đang kết nối / Đã kết nối / Lỗi kết nối.
- Thẻ: thời gian phản hồi (đo ở lần Kiểm tra kết nối/Gửi thử gần nhất), số tin Telegram gửi
  thành công hôm nay (đếm từ lịch sử gửi), kênh nhận thông báo (tên cuộc trò chuyện từ getChat).
- **Bot Token** (che khi nhập, có nút hiện) và **Chat ID** phải nhập cùng nhau; để trống cả hai
  để dùng biến môi trường nếu có. Cấu hình đã lưu được ưu tiên hơn biến môi trường.
- Token không ghi vào SQLite/log/repository; chỉ lưu bản mã Windows DPAPI theo tài khoản hiện
  tại trong `settings.json`. Ngoài Windows vẫn lưu được đường dẫn Excel nhưng không lưu token.
  Không chuyển file cấu hình chứa token sang tài khoản/máy khác.
  Tham khảo [Microsoft DPAPI](https://learn.microsoft.com/en-us/windows/win32/api/dpapi/nf-dpapi-cryptprotectdata).
- **Kiểm tra kết nối** gọi getMe/getChat, không gửi tin. **Gửi thử** gửi đúng một tin mỗi lần
  bấm. Cả hai dùng ô đang nhập, không tự lưu, không tự thử lại; hai nút bị khóa khi đang xử lý.
  Chat ID của chính bot bị từ chối; lỗi không lộ token. Test tự động dùng mock, không gửi thật.
- **Lưu** để lịch nhắc dùng cấu hình mới. Worker đọc lại cấu hình Telegram trước mỗi lần gửi,
  không cần khởi động lại; nếu đọc lỗi thì không gửi tới đích cũ.
- Công tắc **Khởi động nhắc nền cùng Windows** (bật mặc định từ lần mở app đầu tiên) tạo/xóa lối
  tắt Startup ngay khi gạt, không qua **Lưu**; trạng thái đọc lại khi mở trang. Chi tiết:
  [reminders.md](reminders.md#worker-nhắc-nền).

## Sổ theo dõi Excel

- Một file làm việc duy nhất; **Duyệt vị trí…** để chọn file `.xlsx` có sẵn cùng mẫu 14 cột A–N.
  Mặc định dùng trực tiếp `docs/modules/excel/templates/so_theo_doi.xlsx`. Đổi file áp dụng
  khi mở lại phần mềm; không tự tạo file mới hay xóa workbook cũ.
- Thẻ: Tự động cập nhật (luôn bật — ghi khi lưu/xóa hồ sơ), lần ghi file gần nhất (theo thời
  gian sửa file), số hồ sơ ứng dụng đã ghi vào file đó.
- **Mở file Excel**, **Ghi lại ngay** (ghi lại toàn bộ hồ sơ, dùng khi lần ghi trước lỗi), **Lưu**.
- Luôn giữ dòng cũ, thêm/sửa theo mã. `excel_policy` chỉ để tương thích file cấu hình cũ và
  được chuẩn hóa về merge. Chi tiết: [Excel](excel.md#excel--ghi-một-chiều-vào-sổ-làm-việc-có-sẵn).

## Lưu cấu hình

`settings.json` trong thư mục dữ liệu, ghi qua file tạm và thay thế nguyên tử. Lưu lỗi: giữ cấu
hình cũ và dữ liệu đang nhập, không báo thành công giả. Hai nút **Lưu** (mục Telegram và Excel)
cùng lưu toàn bộ cấu hình.

## Chưa có

Sao lưu hồ sơ, nhập Excel (ngoài phạm vi theo CLAUDE.md), nhật ký xử lý, tự phát hiện Chat ID.
Số liệu trạng thái đọc qua `infrastructure/diagnostics.py` (chỉ đọc).
