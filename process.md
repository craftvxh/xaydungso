# Xây Dựng Số — Tiến trình và bàn giao

**Cập nhật:** 17/11/2026 (giờ Việt Nam).
**Điểm dừng hiện tại:** Dashboard là trang mở mặc định, có bốn chỉ số và lịch nhắc sắp tới từ SQLite qua Application. CRUD, Excel và nhắc nền vẫn dùng được qua điều hướng. Cần người dùng nghiệm thu và kiểm chứng các phần Windows/thông báo thật.
**Git:** Chưa commit, chưa push. Giữ nguyên các thay đổi và file chưa được theo dõi khi tiếp tục.

## 1. Đọc trước khi tiếp tục

1. Đọc file này, [AGENTS.md](AGENTS.md), [README.md](README.md) và [docs/README.md](docs/README.md).
2. Đọc đặc tả module liên quan; các quyết định mới trong docs đã thay thế các blocker của phiên trước.
3. Kiểm tra `git status --short` và code thực tế. Không `uv init`, không reset/ghi đè thay đổi sẵn có.
4. Xem [báo cáo kỹ thuật](docs/development/implementation-status.md), [schema](docs/modules/cpxd/schema.md) và [vận hành nhắc nền](docs/modules/reminders/operations.md).

File `process.md` là tiến trình bàn giao hiện hành, không thay thế đặc tả nghiệp vụ. Đã đổi tên theo yêu cầu người dùng; các liên kết tài liệu đã được cập nhật.

## 2. Những gì đã thay đổi so với phiên trước

Trước đây giao diện chỉ có trang chào; người dùng phản hồi đúng rằng chưa thấy chức năng.
Sau khi người dùng cập nhật docs, các yêu cầu sau đã được chốt và triển khai:

- Mã hồ sơ bắt buộc/duy nhất; họ tên bắt buộc; điện thoại/địa chỉ có thể trống.
- Đủ các trường theo dõi theo mapping A–P; đóng dấu Có/Chưa, chữ ký Đã ký/Chưa ký.
- Hai trạng thái; hoàn thành do người dùng chủ động đặt.
- Template chính thức là `docs/modules/excel/templates/so_theo_doi.xlsx`; tên cũ `(1)` không còn là blocker.
- Xuất theo `created_at ASC, id ASC` vào thư mục dữ liệu ứng dụng.
- Reminder theo Asia/Ho_Chi_Minh; 12/24 giờ thực, 10 giây test, biên 07:00/23:00 bao gồm hai đầu mút, ngoại lệ lịch quá khứ và gửi bù.
- Telegram và Windows Notification có kết quả riêng từng kênh.
- Word và tính toán xây dựng chuyên ngành được hoãn, không chặn CRUD/Excel/reminder.

Không yêu cầu người dùng duyệt lại những quyết định trên. AGENTS.md đã được sửa phần scope để không còn mâu thuẫn với yêu cầu triển khai hiện tại.

## 3. Tiến độ thực tế theo roadmap mới

| Phase | Trạng thái | Kết quả |
|---|---|---|
| 01 — Foundation | Đã triển khai | Entry points, cấu hình, logging, FluentWindow |
| 02 — Database | Đã triển khai | Schema version 3, domain models, repository, constraints, migrations/transactions |
| 03 — UI | Đã triển khai | Từ Dashboard đi tới Hồ sơ; bảng, thêm, chi tiết/sửa, tìm kiếm/lọc; trang Nhắc nhở |
| 04 — CRUD | Đã triển khai | Lưu SQLite, kiểm tra trùng mã, giữ input khi lỗi, xóa vĩnh viễn có xác nhận |
| 05 — Reminder | Đã triển khai code và test giả lập | Domain rules, lịch SQLite, worker riêng, retry từng kênh, sửa/hủy và gửi bù; chưa gửi thật |
| 05-D — Dashboard | Đã triển khai | Mở mặc định; tổng/chưa xong/đã xong/nhắc hôm nay, lịch sắp tới; loading/empty/error/retry |
| 06 — Excel | Đã nối vào CRUD | Đủ A–P, thứ tự ổn định, tái xuất sau commit, nút retry/mở file; template không đổi |
| 07 — Testing / Windows packaging | Một phần | Test Linux đạt; có cấu hình Windows, chưa build/test trên Windows |
| Later — Word / chuyên ngành | Hoãn theo quyết định | Không tạo template hoặc generator giả |

### Checklist đã làm

- [x] Dashboard là trang mở mặc định; bốn chỉ số từ SQLite qua Application, không đọc Excel.
- [x] Lịch nhắc sắp tới, điều hướng nhanh, tự refresh và xử lý loading/empty/error/retry.
- [x] Đặc tả Dashboard, định nghĩa metric, roadmap và test SQLite/UI đã cập nhật.
- [x] Thêm, đọc, sửa, xóa hồ sơ qua UI và SQLite.
- [x] Form đầy đủ trường theo dõi, thời lượng xử lý và trạng thái.
- [x] Tìm Unicode, lọc trạng thái, hiển thị lỗi validation/trùng mã.
- [x] Xóa có xác nhận; hủy lịch liên quan chưa gửi trong cùng transaction.
- [x] Xuất lại toàn bộ Excel sau mỗi lần lưu/sửa/xóa đã commit.
- [x] Lỗi xuất không rollback SQLite; giữ bản xuất trước và cho retry.
- [x] Tạo/sửa/hủy lịch; không tự gán giờ scheduler vào cột H theo dõi.
- [x] Theo dõi Telegram/Windows riêng; không retry kênh đã thành công.
- [x] Worker độc lập Qt, khóa OS chống chạy trùng, lease phục hồi claim và token chống ghi đè kết quả cũ.
- [x] Nút Bật/Dừng nhắc nền; GUI đóng không tự dừng worker đang chạy.
- [x] Kiểm tra desktop Linux bằng dữ liệu mẫu; sửa tương phản form và bố cục ngày giờ.
- [x] Cập nhật script đóng gói để mang theo template, tzdata và worker.

### Chưa kiểm chứng / chưa làm

- [ ] Người dùng nghiệm thu luồng làm việc thực tế và bố cục trên Windows.
- [ ] Gửi Telegram thật với bot/chat ID của người dùng.
- [ ] Windows Notification thật, thiết lập Notifications/Focus Assist và tên ứng dụng.
- [ ] Build/chạy `dist/XayDungSo/XayDungSo.exe` trên Windows, cả worker từ bản frozen.
- [ ] Mở/in workbook và khóa file thật bằng Microsoft Excel trên Windows.
- [ ] Installer / service / tự chạy khi đăng nhập: chưa triển khai, không tự bổ sung.
- [ ] Word/chuyên ngành: hoãn, chỉ làm khi có đặc tả và mẫu được duyệt.

Không tuyên bố toàn bộ dự án đã nghiệm thu chỉ vì code/test Linux đạt.

## 4. Cách chạy và dùng ngay

```bash
uv sync --locked
uv run xaydungso
# Hoặc:
uv run python -m xaydungso
```

Ứng dụng mở vào **Tổng quan (Dashboard)**. Chọn **Quản lý hồ sơ** rồi **Thêm hồ sơ**, nhập mã/họ tên và Lưu.
Chọn một dòng để **Chi tiết / sửa**, **Xóa hồ sơ** hoặc **Tạo nhắc cho hồ sơ**.
Dùng **Xuất lại Excel** nếu bản xuất chưa cập nhật; **Mở sổ Excel** mở bản xuất.

Thư mục dữ liệu mặc định:

- Windows: `%LOCALAPPDATA%/xaydungso`.
- Linux: `$XDG_DATA_HOME/xaydungso` hoặc `~/.local/share/xaydungso`.
- Có thể đặt `XAYDUNGSO_DATA_DIR` cho cả GUI/worker. Không trỏ vào thư mục template.

Trong đó có `xaydungso.sqlite3`, bản xuất `so_theo_doi.xlsx`, khóa worker và log kỹ thuật.

Trang **Nhắc nhở** cho tạo/sửa/hủy lịch. Sau khi tạo lịch, chọn **Bật nhắc nền** để xử lý.
Thời điểm bắt đầu mặc định là thời điểm lưu lịch nếu không chỉnh; có thể dùng 10 giây để thử trong khung giờ cho phép.
Đóng GUI không tắt worker; **Dừng nhắc nền** yêu cầu worker dừng, không xóa lịch.
Sau khi khởi động lại máy, cần bật worker lại; chưa có autostart.

Cấu hình Telegram trong PowerShell trước khi mở ứng dụng/bật worker:

```powershell
$env:XAYDUNGSO_TELEGRAM_BOT_TOKEN = '<bot-token>'
$env:XAYDUNGSO_TELEGRAM_CHAT_ID = '<chat-id>'
uv run xaydungso
```

Không đưa token vào Git, SQLite hoặc log. Nếu đổi môi trường cấu hình, dừng worker cũ và mở lại từ môi trường mới.

Worker không cần mở GUI:

```bash
uv run xaydungso-reminders
# Hoặc: uv run python -m xaydungso.worker
# Chỉ chạy một lượt:
uv run xaydungso-reminders --once
```

## 5. Điểm vào code

| File / thư mục | Vai trò |
|---|---|
| `src/xaydungso/app.py` | Composition root; nối database, use cases, exporter, UI và worker control |
| `src/xaydungso/application/dashboard.py` | Snapshot/reader contract, use case và biên ngày Việt Nam |
| `src/xaydungso/infrastructure/dashboard.py` | Đọc chỉ số và lịch sắp tới từ cùng transaction SQLite |
| `src/xaydungso/presentation/dashboard.py` | Thẻ số liệu, bảng sắp tới, navigation, loading/empty/error/retry |
| `src/xaydungso/domain/records.py` | RecordData, Record, statuses, validation và render duration |
| `src/xaydungso/domain/reminders.py` | Timezone, deadline, notify và tạo Reminder |
| `src/xaydungso/application/records.py` | CRUD rồi export độc lập sau commit |
| `src/xaydungso/application/reminders.py` | Use cases lịch và ReminderEngine độc lập Qt |
| `src/xaydungso/infrastructure/database.py` | Migration 1/2/3, lifecycle SQLite |
| `src/xaydungso/infrastructure/records.py` | Repository hồ sơ, tìm/lọc và xóa/hủy lịch |
| `src/xaydungso/infrastructure/reminders.py` | Persistence lịch, trạng thái kênh, claim/lease/retry |
| `src/xaydungso/infrastructure/notifications.py` | Telegram HTTPS và Windows PowerShell/WinRT |
| `src/xaydungso/infrastructure/worker_process.py` | Khóa OS, bật/dừng và kiểm tra worker |
| `src/xaydungso/worker.py` | CLI worker độc lập Qt; log có giới hạn kích thước |
| `src/xaydungso/infrastructure/tracking_export.py` | Mapping A–P từ snapshot SQLite |
| `src/xaydungso/infrastructure/excel.py` | Ghi workbook giữ template và atomic replacement |
| `src/xaydungso/presentation/` | MainWindow, pages, forms và task runner ngoài UI thread |
| `packaging/build_windows.py` | Script Windows-only, bundle template và timezone data |
| `tests/` | Tests domain, SQLite, Excel, engine, transports, GUI và worker |

## 6. Quyết định kỹ thuật cần giữ

- Database version **3**, `application_id=0x5844534F`; nâng cấp database version 1 tại chỗ, không xóa database người dùng.
- `records` bị DELETE thật, không có soft-delete. Lịch sử reminder giữ kết quả với `record_id=NULL`; lịch còn kênh chưa gửi bị hủy khi xóa hồ sơ.
- G lưu thời lượng theo giây; F/H/I/L là văn bản theo dõi thủ công, giữ nguyên khi xuất.
- Trạng thái hoàn thành không suy ra từ đóng dấu/chữ ký.
- Timestamp reminder/created_at chuẩn hóa UTC trong SQLite; tính/hiển thị theo Asia/Ho_Chi_Minh.
- Retry kênh lỗi có backoff 5…300 giây; kênh sent không gửi lại. Lease 60 giây phục hồi khi worker chết.
- Best effort chống trùng: transport đã nhận nhưng tiến trình chết trước commit sent vẫn có thể gây gửi trùng khi phục hồi. Không tuyên bố exactly-once.
- Windows sent nghĩa là API chấp nhận yêu cầu, không chứng minh popup đã hiện hoặc được đọc.
- Export chạy ngoài Qt event loop; thao tác lưu xong mới xuất, không gộp Excel vào transaction SQLite.
- Không nhập/sync Excel → SQLite, không cloud/backup/restore/auth và không commit/push tự động.

## 7. Kiểm tra gần nhất

Trên Linux trong phiên triển khai sau cập nhật docs:

- `uv run pytest`: **89 passed** sau khi thêm Dashboard; gồm metric SQLite/day-boundary/channel và UI loading/error/retry.
- `uv sync --locked`: đạt với lockfile hiện tại.
- `uv run ruff check .`: đạt.
- `uv run ruff format --check .`: đạt (68 file đã đúng định dạng).
- Regression test entry point xác nhận mở Dashboard, có ba trang điều hướng, đóng sạch. Đã mở Dashboard thật trên desktop Linux với database mẫu tạm: 3 tổng / 2 chưa xong / 1 đã xong / 1 lịch hôm nay, kiểm tra lịch sắp tới và xem bố cục toàn cửa sổ; đóng với exit code 0. Chưa nghiệm thu Windows.
- Template giữ nguyên SHA-256 `852e36cbc6c646ab7e1c6242a8a3dd213a8a66719018d322930b949cc6a30242`.
- Có test UI offscreen thực sự thao tác form, search/filter, reminder và xác nhận xóa.
- Transports dùng mock; không gửi thông báo thật.
- Worker test chạy process riêng với database trống, không import Qt, chống chạy trùng và dừng sạch.
- Desktop Linux đã mở danh sách, form và lịch nhắc bằng dữ liệu mẫu tạm; đóng với exit code 0.
- Native Windows build/notification/Excel locking chưa được kiểm chứng.

Phiên đổi tên tài liệu này không sửa code và không chạy lại pytest/Ruff. Các kết quả
89 test và quality checks ở trên là kết quả đã chạy trong phiên triển khai Dashboard.
Đã kiểm tra lại tên file, liên kết nội bộ liên quan và `git diff --check` sau đổi tên.

Lệnh cần chạy sau mỗi thay đổi code phù hợp:

```bash
uv sync --locked
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Chỉ build trên Windows:

```powershell
uv run python packaging/build_windows.py
```

## 8. Phiên tiếp theo nên làm gì?

1. Đọc `process.md`, mở ứng dụng và nghiệm thu Dashboard, Hồ sơ, Nhắc nhở với người dùng; sửa vấn đề thực tế nếu có.
2. Trên Windows: xác nhận đúng thư mục dữ liệu, form Unicode, quyền ghi và bản xuất Excel.
3. Cấu hình bot/chat ID rồi kiểm chứng gửi 10 giây trong khung giờ cho phép, hai kênh, retry riêng kênh và worker khi GUI đóng.
4. Build và thử bản `.exe`, worker frozen, native toast và file Excel đang mở/khóa.
5. Cập nhật tiến độ theo kết quả thực sự chạy; không hỏi lại schema/template đã chốt, không làm lại Foundation.

## 9. Nhật ký

| Ngày | Nội dung |
|---|---|
| 17/11/2026 | Foundation và các adapter ban đầu; 39 test nhưng UI chỉ có trang chào |
| 17/11/2026 | Tạo file bàn giao; ghi rõ thiếu chức năng thao tác được |
| 17/11/2026 | Người dùng cập nhật đặc tả: chốt dữ liệu, template, reminder hai kênh và hoãn Word |
| 17/11/2026 | Triển khai CRUD/UI/Excel/reminder runtime, mở desktop kiểm tra; 82 test đạt |
| 17/11/2026 | Thêm đặc tả Dashboard và triển khai trang mở mặc định qua Application/SQLite; 89 test đạt |
| 17/11/2026 | Cập nhật checklist Dashboard và bàn giao, đổi tên file tiến độ thành `process.md`, cập nhật liên kết; không thay đổi code |

Cập nhật file này sau mỗi phiên, phân biệt code đã có, kiểm tra đã chạy và phần chưa nghiệm thu.
