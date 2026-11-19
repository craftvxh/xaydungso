# Xây Dựng Số (`xaydungso`)

Ứng dụng desktop Windows giúp một người quản lý hồ sơ xây dựng, theo dõi hạn xử lý, nhắc việc
qua Telegram / Windows và ghi sổ theo dõi Excel. Chạy cục bộ, không cần máy chủ hay đăng nhập.

> **Trạng thái:** Đã có Tổng quan, Quản lý hồ sơ, Nhắc nhở (kèm mẫu thông báo), Cài đặt và ghi
> sổ Excel. Kiểm thử tự động đạt trên Windows. Chưa nghiệm thu: gửi Telegram/popup Windows thật
> với cấu hình chính, khóa file bằng Microsoft Excel thật, bản đóng gói `.exe`.
> Tạo văn bản Word và tính toán xây dựng chuyên ngành đang hoãn.

## Chức năng

- **Tổng quan** (mở mặc định): tổng hồ sơ, chưa hoàn thành, đã hoàn thành, quá hạn; bảng hồ sơ
  quá hạn hoặc đến hạn trong 24 giờ; lịch nhắc sắp tới.
- **Quản lý hồ sơ**: thêm/sửa/xóa vĩnh viễn, tìm kiếm, lọc trạng thái, phân trang, thao tác hàng
  loạt (đổi trạng thái, xóa), khung chi tiết. Mã hồ sơ và họ tên là bắt buộc.
- **Sổ Excel**: sau mỗi thay đổi, tự ghi vào file `.xlsx` có sẵn theo mẫu 14 cột A–N (mặc định
  `docs/modules/excel/templates/so_theo_doi.xlsx`); giữ dòng cũ, thêm/sửa theo mã hồ sơ.
- **Nhắc nhở**: lịch riêng theo *hạn xử lý − khoảng báo trước*, gửi trong 07:00–23:00 qua Telegram
  và Windows Notification (trạng thái/thử lại từng kênh); tiến trình nhắc nền chạy cả khi đóng cửa
  sổ. **Cấu hình** quản lý mẫu nội dung thông báo có biến `{{ma_ho_so}}`, `{{ho_ten}}`, `{{han_xu_ly}}`.
- **Cài đặt**: thông tin cơ sở dữ liệu (chỉ đọc), Bot Token/Chat ID Telegram (kiểm tra, gửi thử;
  token mã hóa theo tài khoản Windows), chọn file Excel làm việc.

## Chạy trên Windows

Nhấp đúp `chay_xaydungso.vbs` (hoặc `chay_xaydungso.bat`) trong thư mục dự án. Cần cài
[uv](https://docs.astral.sh/uv/); launcher dùng `uv.lock` và chạy ẩn, lỗi báo bằng hộp thoại, log
lần chạy gần nhất ở `%LOCALAPPDATA%\xaydungso\launcher.log`. Giữ hai file launcher cùng thư mục.

Đóng cửa sổ (X) chỉ ẩn phần mềm xuống khay hệ thống; nhấp đúp icon ở khay để mở lại, chuột phải →
**Thoát** để tắt hẳn. Mở phần mềm lần nữa khi đang chạy sẽ hiện lại cửa sổ cũ, không mở thêm bản mới.

Sau khi cập nhật code: đóng và mở lại phần mềm; nếu nhắc nền đang chạy, dừng rồi bật lại.

## Dữ liệu

- Thư mục dữ liệu: `%LOCALAPPDATA%\xaydungso`; đặt `XAYDUNGSO_DATA_DIR` để dùng thư mục khác.
  Ứng dụng chỉ hỗ trợ Windows (10/11).
- Gồm `xaydungso.sqlite3` (nguồn dữ liệu chính), `settings.json`, `reminders.log`, `launcher.log`.
- Database tự nâng cấp schema khi mở (hiện v7), không xóa dữ liệu cũ. Không có sao lưu/khôi phục
  trong ứng dụng, không nhập dữ liệu từ Excel.

## Phát triển

Python 3.12 · PyQt6 · PyQt6-Fluent-Widgets · SQLite · uv · pytest · Ruff. Kiến trúc Modular
Monolith phân lớp ([Kiến trúc](.claude/docs/architecture.md)).

```bash
uv sync --locked
uv run xaydungso                 # hoặc: uv run python -m xaydungso
uv run xaydungso-reminders       # nhắc nền không cần GUI (--once, --data-dir)
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Đóng gói Windows (dừng nhắc nền và Thoát app trước):

1. `uv run python packaging/build_windows.py` → `dist\XayDungSo\XayDungSo.exe` (PyInstaller).
2. Biên dịch bộ cài bằng Inno Setup 7 → `dist\xaydungso_setup.exe`:
   `& "$env:LOCALAPPDATA\Programs\Inno Setup 7\ISCC.exe" packaging\xaydungso.iss`

Bộ cài cài cho riêng người dùng (không cần admin) vào `%LOCALAPPDATA%\Programs\XayDungSo`, tạo lối
tắt Start Menu (Desktop tùy chọn), tự tắt bản đang chạy trước khi cài đè; gỡ cài đặt xóa lối tắt
Startup nhưng giữ dữ liệu `%LOCALAPPDATA%\xaydungso`. Chưa ký số (dùng nội bộ). Mỗi bản mới: tăng
`version` trong `pyproject.toml` và `AppVersion` trong `packaging/xaydungso.iss`, giữ nguyên `AppId`.

Nhắc nền tự chạy ẩn khi đăng nhập Windows (lối tắt trong Startup, tạo ở lần mở app đầu tiên; tắt ở
Cài đặt → Telegram Bot hoặc Task Manager → Startup apps).

## Tài liệu

- [Mục lục tài liệu](.claude/docs/README.md) — đặc tả từng module, giao diện, kiến trúc, kiểm thử
- [Vận hành nhắc nhở và khắc phục Telegram](.claude/docs/reminders.md#nhắc-nhở--vận-hành-và-khắc-phục-sự-cố)
- [Lộ trình](.claude/docs/README.md#lộ-trình) · [Nhật ký bàn giao](.claude/process.md) · [Quy tắc Claude Code](.claude/CLAUDE.md)

Icon: [Fluent UI System Icons](https://github.com/microsoft/fluentui-system-icons) của Microsoft
(giấy phép MIT, xem `src/xaydungso/presentation/icons/LICENSE`).
