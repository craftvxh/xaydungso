# Xây Dựng Số — Mục lục tài liệu

Thư mục này là nguồn chính thức cho đặc tả đã duyệt: **mỗi chủ đề một file**. [README](../../README.md)
giới thiệu và hướng dẫn chạy; [CLAUDE.md](../CLAUDE.md) là quy tắc làm việc cho Claude Code (tự nạp);
[process.md](../process.md) là nhật ký bàn giao. Cuối file này: các quyết định đã thay thế và trạng thái
kiểm chứng.

| File | Nội dung |
|---|---|
| [architecture.md](architecture.md) | Kiến trúc, layer, luồng dữ liệu, quy ước code, kiểm thử |
| [ui.md](ui.md) | Giao diện: màu, chữ (font, thang cỡ), icon, hiệu ứng, từng trang |
| [dashboard.md](dashboard.md) | Tổng quan: bố cục và định nghĩa chỉ số |
| [records.md](records.md) | Hồ sơ (CPXD): quy tắc, workflow và schema SQLite |
| [excel.md](excel.md) | Ghi sổ Excel có sẵn và mapping 14 cột A–N |
| [reminders.md](reminders.md) | Nhắc nhở, mẫu thông báo, vận hành worker |
| [settings.md](settings.md) | Cài đặt: Dữ liệu, Telegram Bot, Sổ theo dõi Excel |

Trang tải xuống tĩnh (GitHub Pages): `website/` — sửa tên tệp phát hành trong `website/js/config.js`; triển khai bằng `.github/workflows/deploy-website.yml`.

Mẫu sổ làm việc: [`docs/modules/excel/templates/so_theo_doi.xlsx`](../../docs/modules/excel/templates/so_theo_doi.xlsx)
(cũng là file làm việc mặc định của ứng dụng — giữ nguyên đường dẫn này).

## Quy tắc bảo trì

- Mỗi quy tắc chỉ định nghĩa ở **một** file; file khác liên kết tới đó.
- Cập nhật tài liệu cùng lúc với thay đổi hành vi, dữ liệu, schema hoặc kiến trúc.
- Không tự điền quy tắc nghiệp vụ còn thiếu: ghi rõ "chưa có đặc tả" hoặc **TBD**.
- Ghi ngày và nguồn (người dùng duyệt, bản thiết kế) khi một quyết định thay thế quyết định cũ.
- Module mới được phê duyệt: thêm một file `.claude/docs/<module>.md` và một dòng vào bảng trên; không
  tạo thư mục con.
- Nhật ký phiên làm việc và kết quả test ghi vào `process.md`, không thêm file trạng thái trong `.claude/docs/`.

## Lộ trình

Triển khai theo module và thứ tự phụ thuộc; mỗi giai đoạn có test và review. Lộ trình không
được dùng để suy diễn quy tắc nghiệp vụ còn thiếu. Nhật ký chi tiết: [process.md](../process.md).

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

Ngoài phạm vi (CLAUDE.md): nhập Excel → SQLite, cloud, sao lưu/khôi phục database, đa người dùng.
Chưa có đặc tả: loại công trình, bản đồ quy hoạch, nhật ký xử lý, tự phát hiện Chat ID,
installer. Đã có: nhắc nền tự chạy khi đăng nhập (lối tắt Startup).

## Quyết định đã thay thế

Không quay lại các quyết định cũ chỉ vì đọc được lịch sử trong `process.md`.

| Trước | Hiện tại |
|---|---|
| Tạo file Excel xuất mới từ template; cấm ghi vào template | Ghi vào chính workbook có sẵn, kể cả `so_theo_doi.xlsx` |
| Excel 16 cột A–P → 15 cột A–O | 14 cột A–N (bỏ giờ nhắc, bỏ STT); G "Thời hạn toàn quy trình" → "Ngày hẹn trả" |
| Chọn merge/thay toàn bộ trong Cài đặt | Một file làm việc, luôn giữ cũ, thêm/sửa theo mã |
| Thời hạn xử lý là thời lượng; lưu hồ sơ tự tạo lịch | Hạn xử lý là mốc ngày giờ; lịch đặt riêng ở Nhắc nhở |
| Thẻ "Nhắc hôm nay" trên Tổng quan, kèm % tổng số | Thẻ "Quá hạn"; số nhắc hôm nay ở badge thanh điều hướng; bỏ % |
| Nền trắng/chữ đen thuần, icon `FluentIcon` | Bảng màu slate theo Stitch (vẫn theme sáng cố định), icon Fluent UI System Icons (Windows 11, MIT) |
| Mẫu nội dung cố định trong form lịch | Mẫu do người dùng quản lý tại Nhắc nhở → Cấu hình |
| "Cấu hình" trên trang Nhắc nhở mở Cài đặt | Mở màn hình quản lý mẫu nội dung |
| Chỉ hủy lịch | Hủy (giữ lịch sử) hoặc xóa vĩnh viễn, kể cả hàng loạt |
| Hộp xác nhận phủ trắng toàn cửa sổ | Chỉ hiện thẻ hộp thoại, nền làm mờ nhẹ, nút nguy hiểm màu đỏ |
| Cài đặt một form chung | Ba mục Dữ liệu / Telegram Bot / Sổ theo dõi Excel |
| Ô tìm kiếm có Ctrl+K; dòng logo trên thanh điều hướng | Đã bỏ theo yêu cầu |
| Icon cửa sổ là icon Fluent "building" | Logo người dùng cung cấp (`presentation/logo.svg`, `packaging/xaydungso.ico`) |
| Tài liệu trong `docs/` nhiều thư mục; `AGENTS.md`, `CONTEXT.md`, `process.md` ở gốc | Tất cả trong `.claude/` (CLAUDE.md, docs/, process.md); `docs/` chỉ còn mẫu Excel |
| BAT giữ terminal | Chạy ẩn qua VBS, lỗi bằng hộp thoại/log |

## Kiểm chứng

**Đã kiểm tra (19/11/2026, Windows):** `uv run pytest` **161 passed, 1 skipped** (bỏ qua: tạo
symlink cần Developer Mode); `ruff check` và `ruff format --check` đạt. Các trang và hộp thoại đã được render native
Windows bằng dữ liệu tạm để so với thiết kế; ứng dụng thật mở được qua launcher.

**Chưa nghiệm thu:**

- Workflow thực tế với dữ liệu thật; tên kênh nhận Telegram với bot thật (mới test bằng mock).
- Gửi Telegram và popup Windows Notification thật theo lịch (Notifications/Focus Assist, máy ngủ/tắt).
- Khóa file bằng Microsoft Excel thật; xem `so_theo_doi.xlsx` sau khi bỏ STT/đổi tiêu đề G trong Excel.
- Cảm giác hiệu ứng chuyển động trên máy người dùng.
- Build và chạy bản `.exe` cùng worker; chưa có installer.
- Nhắc nền tự chạy qua lối tắt Startup sau khi đăng nhập lại Windows (đã thử mở lối tắt khởi
  động được worker ẩn; chưa thử đăng xuất/đăng nhập thật).
