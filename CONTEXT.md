# Xây Dựng Số — Tổng hợp context hiện tại

**Cập nhật:** 19/11/2026 (giờ Việt Nam).
**Mục đích:** tóm tắt sản phẩm, các quyết định mới nhất và trạng thái để rà soát hoặc bàn giao
cho phiên làm việc khác. Đặc tả chi tiết nằm trong [`docs/`](docs/README.md) — khi có mâu thuẫn,
ưu tiên `docs/`, yêu cầu mới nhất của người dùng và code hiện hành. Nhật ký từng phiên:
[process.md](process.md) (các mục cũ có thể mô tả hành vi đã thay đổi).

## 1. Sản phẩm

- **Xây Dựng Số** (`xaydungso`): ứng dụng desktop Windows, chạy cục bộ, một người dùng; quản lý
  hồ sơ xây dựng, theo dõi hạn xử lý, nhắc việc qua Telegram/Windows và ghi sổ Excel có sẵn.
- Python 3.12 · PyQt6 · PyQt6-Fluent-Widgets · SQLite · uv (`uv.lock`) · pytest · Ruff.
  Modular Monolith phân lớp ([kiến trúc](docs/architecture/overview.md)).
- **SQLite là nguồn dữ liệu duy nhất.** Excel chỉ nhận dữ liệu một chiều; không nhập/sync ngược.
- Ngoài phạm vi (AGENTS.md): nhập Excel, cloud, sao lưu/khôi phục database, đa người dùng.
  **Hoãn:** tạo văn bản Word, tính toán xây dựng chuyên ngành — chờ mẫu và quy tắc.

## 2. Các trang

| Trang | Nội dung chính | Đặc tả |
|---|---|---|
| **Tổng quan** (mở mặc định) | 4 thẻ Tổng / Chưa hoàn thành / Đã hoàn thành (xanh lá) / Quá hạn; bảng Hồ sơ cần chú ý (quá hạn hoặc hạn trong 24 giờ, nút Chi tiết); lịch nhắc sắp tới; Tải lại, Thêm hồ sơ | [dashboard](docs/modules/dashboard/overview.md) |
| **Quản lý hồ sơ** | Bảng (ô tick, mã, tên, SĐT, địa chỉ, 4 cột thời gian, trạng thái), tìm kiếm, lọc, phân trang 14 dòng, thao tác hàng loạt, khung chi tiết, form Thêm/Sửa 3 nhóm | [cpxd](docs/modules/cpxd/overview.md) |
| **Nhắc nhở** | 3 thẻ Chờ gửi/Đã gửi/Gửi lỗi, bảng theo kênh, Sửa/Hủy/Xóa, xóa hàng loạt, Bật/Dừng nhắc nền, form Tạo lịch nhắc A/B/C; **Cấu hình** = quản lý mẫu nội dung | [reminders](docs/modules/reminders/business-rules.md) |
| **Cài đặt** | Dữ liệu (SQLite, chỉ đọc), Telegram Bot (kiểm tra, gửi thử, tên kênh nhận), Sổ theo dõi Excel (chọn file, Ghi lại ngay) | [settings](docs/modules/settings/overview.md) |

Giao diện theo các bản thiết kế Stitch người dùng gửi; quy ước màu/icon/hiệu ứng:
[UI design](docs/ui/design-guidelines.md).

## 3. Quy tắc cốt lõi (tóm tắt)

- **Hồ sơ:** mã bắt buộc, duy nhất; họ tên bắt buộc; hai trạng thái `Chưa hoàn thành` /
  `Đã hoàn thành` do người dùng chọn; xóa vĩnh viễn sau xác nhận. Ngày giờ trong form nhập
  `dd/mm/yyyy hh:mm` đủ số 0 đầu. Lưu hồ sơ **không** tạo/sửa lịch nhắc.
- **Excel:** tự ghi sau mỗi thay đổi vào file có sẵn (mặc định chính
  `docs/modules/excel/templates/so_theo_doi.xlsx`), mẫu **14 cột A–N** (không STT, không giờ
  nhắc; G = Ngày hẹn trả, F = hạn xử lý); giữ dòng cũ, thêm/sửa theo mã; lỗi Excel không hoàn tác
  SQLite ([excel](docs/modules/excel/overview.md)).
- **Nhắc nhở:** giờ gửi = hạn xử lý − khoảng báo trước, khung 07:00–23:00 (ngoài khung dời 22:00
  hôm trước; đã qua thì 07:00 hôm sau); hai kênh có trạng thái/thử lại riêng; worker là tiến trình
  riêng, chạy tiếp khi đóng cửa sổ; chống trùng best effort.
- **Mẫu thông báo:** văn bản thường nhiều dòng, biến `{{ma_ho_so}}`, `{{ho_ten}}`, `{{han_xu_ly}}`
  được thay khi chọn mẫu trong form; luôn một mẫu mặc định; lưu SQLite (schema v7).
- **Telegram:** Bot Token ≠ Chat ID; token mã hóa DPAPI trong `settings.json`; Kiểm tra kết nối
  không gửi tin; Gửi thử gửi một tin; cả hai không tự lưu — cần **Lưu**. Worker đọc lại cấu hình
  trước mỗi lần gửi. Không đưa token/Chat ID thật vào tài liệu hoặc code.

## 4. Dữ liệu và chạy ứng dụng

- Thư mục dữ liệu `%LOCALAPPDATA%\xaydungso` (hoặc `XAYDUNGSO_DATA_DIR`): `xaydungso.sqlite3`,
  `settings.json`, `reminders.log`, `launcher.log`, file khóa/dừng worker.
- Database **schema v7**, tự nâng cấp khi mở, giữ dữ liệu cũ (cột legacy giữ nguyên, không suy
  ra deadline từ thời lượng cũ). Database thật của người dùng đã ở v7.
- Mở bằng `chay_xaydungso.vbs` / `.bat` (chạy ẩn qua uv, lỗi bằng hộp thoại). Sau khi cập nhật
  code: mở lại GUI và bật lại worker (worker code cũ có thể từ chối schema mới).
- Cửa sổ mở 1280 × 800, không nhớ kích thước lần trước.

## 5. Quyết định đã thay thế

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
| BAT giữ terminal | Chạy ẩn qua VBS, lỗi bằng hộp thoại/log |

## 6. Kiểm chứng

**Đã kiểm tra (19/11/2026, Windows):** `uv run pytest` **158 passed, 1 skipped** (bỏ qua: tạo
symlink); `ruff check` và `ruff format --check` đạt. Các trang và hộp thoại đã được render native
Windows bằng dữ liệu tạm để so với thiết kế; ứng dụng thật mở được qua launcher.

**Chưa nghiệm thu:**

- Workflow thực tế với dữ liệu thật; tên kênh nhận Telegram với bot thật (mới test bằng mock).
- Gửi Telegram và popup Windows Notification thật theo lịch (Notifications/Focus Assist, máy ngủ/tắt).
- Khóa file bằng Microsoft Excel thật; xem `so_theo_doi.xlsx` sau khi bỏ STT/đổi tiêu đề G trong Excel.
- Cảm giác hiệu ứng chuyển động trên máy người dùng.
- Build và chạy bản `.exe` cùng worker; chưa có installer/tự chạy khi đăng nhập.

## 7. Tiếp tục phát triển

1. Đọc [AGENTS.md](AGENTS.md), [docs/README.md](docs/README.md) và đặc tả đúng module; xem
   [process.md](process.md) cho các phiên gần nhất.
2. Xem code và `git status`: HEAD vẫn là `264b23c` (`feat: big update`), còn nhiều thay đổi chưa
   commit (toàn bộ công việc ngày 18–19/11). Không tự commit/push; không reset.
3. Giữ nguyên workbook đang dùng và các thay đổi sẵn có của người dùng; không đưa credentials hay
   dữ liệu cá nhân vào Git.
4. Không quay lại các quyết định cũ ở mục 5 chỉ vì đọc được lịch sử trong process.md.
5. Sau khi sửa code: chạy pytest/Ruff bằng uv, render native khi đổi giao diện, cập nhật `docs/`
   và process.md; báo đúng những gì đã thực sự kiểm tra.

Điểm vào code: `src/xaydungso/app.py` (GUI), `src/xaydungso/worker.py` (nhắc nền); giao diện ở
`presentation/`, use case ở `application/`, quy tắc ở `domain/`, SQLite/Excel/Telegram/Windows/
worker ở `infrastructure/`.
