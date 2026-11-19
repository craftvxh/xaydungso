# Xây Dựng Số — Tiến trình và bàn giao

**Cập nhật:** 18/11/2026 (giờ Việt Nam).
**Điểm dừng hiện tại:** Launcher .bat đã chuyển sang WScript để chạy uv/Python ẩn; có .vbs mở trực tiếp không nháy CMD. Log ở LOCALAPPDATA/xaydungso/launcher.log, lỗi qua hộp thoại.  Giao diện đã cố định nền trắng/chữ đen toàn ứng dụng, tắt Mica và không theo dark mode Windows.  Cài đặt chỉ còn một File Excel làm việc, mặc định dùng trực tiếp `docs/modules/excel/templates/so_theo_doi.xlsx` theo yêu cầu mới. Đã bỏ chọn chế độ ghi, Sổ Excel đang dùng và Mẫu Excel gốc riêng; luôn giữ dòng cũ và thêm/sửa theo mã. Cấu hình replace cũ được chuẩn hóa thành merge qua use case. File này giờ được phép cập nhật trực tiếp; quy tắc giữ template byte-for-byte trước đây đã được người dùng thay thế. Không thêm dữ liệu test hoặc ghi vào workbook thật trong phiên này. Các luồng hồ sơ/lịch tách riêng và Telegram giữ theo lần bàn giao trước.


**Git:** Khi review trên Windows, HEAD là `264b23c` (`feat: big update`); code triển khai đã có trong commit. Chưa kiểm chứng trạng thái push. Working tree có bốn file `.obsidian/*.json` bị xóa từ trước phiên review; giữ nguyên các thay đổi sẵn có.

## 1. Đọc trước khi tiếp tục

1. Đọc file này, [CLAUDE.md](CLAUDE.md), [README.md](../README.md) và [docs/README.md](docs/README.md).
2. Đọc đặc tả module liên quan; các quyết định mới trong docs đã thay thế các blocker của phiên trước.
3. Kiểm tra `git status --short` và code thực tế. Không `uv init`, không reset/ghi đè thay đổi sẵn có.
4. Xem [quyết định đã thay thế và kiểm chứng](docs/README.md#quyết-định-đã-thay-thế), [schema](docs/records.md#schema-sqlite) và [vận hành nhắc nền](docs/reminders.md#nhắc-nhở--vận-hành-và-khắc-phục-sự-cố).

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

Trên Windows nhấp đúp `chay_xaydungso.bat` ở thư mục gốc: BAT gọi WScript và thoát,
VBS đặt đúng working directory, tìm uv trong `%USERPROFILE%/.local/bin` hoặc PATH,
chạy `uv run --locked python -m xaydungso` ẩn và ghi log lần chạy gần nhất vào
`%LOCALAPPDATA%/xaydungso/launcher.log`. Lỗi qua hộp thoại, không giữ terminal.
Windows có thể nháy CMD lúc tạo process BAT; nhấp đúp `chay_xaydungso.vbs` để không
có CMD ngay từ đầu. Giữ BAT/VBS cùng thư mục.

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

- Database version **5**, `application_id=0x5844534F`; nâng cấp database version 1 tại chỗ, không xóa database người dùng.
- `records` bị DELETE thật, không có soft-delete. Lịch sử reminder giữ kết quả với `record_id=NULL`; lịch còn kênh chưa gửi bị hủy khi xóa hồ sơ.
- F ghi deadline ngày/giờ; E/G/J là văn bản theo dõi thủ công. Không ghi giờ nhắc hoặc khoảng báo trước vào Excel. Thời lượng/trường nhắc theo dõi legacy chỉ được giữ trong SQLite.
- Trạng thái hoàn thành không suy ra từ đóng dấu/chữ ký.
- Timestamp reminder/created_at chuẩn hóa UTC trong SQLite; tính/hiển thị theo Asia/Ho_Chi_Minh.
- Retry kênh lỗi có backoff 5…300 giây; kênh sent không gửi lại. Lease 60 giây phục hồi khi worker chết.
- Best effort chống trùng: transport đã nhận nhưng tiến trình chết trước commit sent vẫn có thể gây gửi trùng khi phục hồi. Không tuyên bố exactly-once.
- Windows sent nghĩa là API chấp nhận yêu cầu, không chứng minh popup đã hiện hoặc được đọc.
- Export chạy ngoài Qt event loop; thao tác lưu xong mới xuất, không gộp Excel vào transaction SQLite.
- Không nhập/sync Excel → SQLite, không cloud/backup/restore/auth và không commit/push tự động.

## 7. Kiểm tra gần nhất

### Xác nhận tự ghi Excel ngay khi lưu hồ sơ — 18/11/2026

- Kiểm tra luồng hiện có: RecordDialog → Records.save → repository.save commit SQLite → exporter.export → báo kết quả/đóng form. Thêm/sửa/xóa hồ sơ đều tự ghi workbook; nút ghi riêng chỉ để retry.
- Đổi Ghi lại Excel thành Thử lại Excel, thêm tooltip giải thích việc ghi tự động và thông báo thành công rõ hơn. Lỗi ghi chỉ dẫn kiểm tra File Excel làm việc/đóng file đang khóa rồi thử lại; không còn chỉ dẫn chọn chế độ ghi đã bị bỏ.
- Bổ sung kiểm tra GUI đọc chính ô B5 trong bản workbook tạm ngay sau Lưu, trước khi bấm nút retry, xác nhận mã hồ sơ đã được tự ghi. Các test tạo sổ trống riêng trong thư mục tạm, không giả định workbook làm việc thật còn trống (file thật hiện đã có dữ liệu). Không thay đổi workbook thật.
- `uv run pytest tests/test_records.py tests/test_existing_workbook.py tests/test_gui_workflow.py`: **22 passed**; Ruff check/format đạt (77 file), git diff --check đạt. Không chạy lại toàn bộ suite cho thay đổi wording/tooltip này.


### Launcher ẩn terminal — 18/11/2026

- BAT chỉ chuyển sang `wscript.exe` rồi thoát. VBS dùng working directory của chính script, tìm uv, chạy console uv/Python ẩn và chờ kết quả; không dùng pause hoặc terminal để báo lỗi. Hộp thoại báo lỗi và launcher.log trong LOCALAPPDATA/xaydungso giữ chẩn đoán lần chạy gần nhất.
- Có thể chạy VBS trực tiếp để không nháy CMD ngay từ đầu; BAT có thể nháy CMD rất ngắn do Windows khởi tạo console trước khi script được thực thi. Không thay file association hoặc thiết lập bảo mật hệ điều hành.
- Đã chạy smoke end-to-end trên Windows bằng BAT thật từ thư mục khác, dữ liệu ứng dụng/log tạm và đường dẫn chứa dấu cách/ký tự &: BAT → WScript → uv/Python ẩn → GUI native → đóng exit code 0, xác nhận log có Application stopped (exit code 0). Hook tự đóng nằm trong thư mục tạm, không sửa code ứng dụng.
- Không chạy lại pytest vì chỉ thay launcher/docs; kết quả 125 passed, 1 skipped bên dưới là lần kiểm tra code Python trước đó. git diff --check đạt. Không gửi Telegram hoặc ghi vào workbook thật.


### Nền trắng / chữ đen toàn ứng dụng — 17/11/2026

- Cấu hình tập trung tại presentation/theme.py: Fluent Theme.LIGHT, Qt Fusion/light color scheme, palette trắng/đen cả disabled/placeholder/selection, override style cho widget Fluent/native và hộp thoại xuất hiện sau. Không tạo QApplication khi import.
- MainWindow nền trắng ngay khi khởi tạo, tắt Mica; nút tiêu đề nền trắng/ký hiệu đen. Qt file dialog trong ứng dụng dùng cùng palette, không phụ thuộc giao diện native Windows.
- Chỉ cập nhật màu/style, không đổi dữ liệu, Excel hoặc logic đặt/gửi lịch; không gửi tin thật trong phiên này.
- Full suite: **125 passed, 1 skipped** (symlink) trên Windows; Ruff check/format đạt, 77 file. git diff --check đạt. Test mới bật dark theme trước cấu hình rồi kiểm tra trở về light, ô nhập/placeholder/nút disabled trắng-đen và hộp thoại tạo sau vẫn đúng màu; entry point xác nhận Mica tắt và nền trắng từ trước show.
- Native Windows đã mở/chụp/xem Dashboard, Cài đặt và form Thêm hồ sơ bằng dữ liệu tạm: nền trắng, chữ/placeholder/nút đen, đóng exit code 0. Chưa kiểm thử bản đóng gói.


### Một file Excel làm việc — 17/11/2026

- Theo yêu cầu mới nhất, dùng trực tiếp so_theo_doi.xlsx làm sổ làm việc mặc định. Cài đặt chỉ có một ô File Excel làm việc; bỏ Chế độ ghi, Sổ đang dùng và Mẫu gốc riêng. Cho phép chọn chính đường dẫn file trước đây gọi là template. Không tự tạo/sao chép file mới.
- Luôn merge theo mã, giữ hồ sơ cũ; cấu hình replace-all cũ được chuẩn hóa về merge. Vẫn theo dõi dòng từng ghi để xóa/đổi mã hồ sơ đúng dòng. Chỉ hàm legacy tạo snapshot riêng còn cấm tự ghi đè nguồn; luồng ghi workbook có sẵn được phép đọc/ghi cùng đường dẫn.
- Test ghi so_theo_doi.xlsx vào chính nó bằng bản tạm đạt, giữ dòng trước khi thêm dòng sau. Không ghi dữ liệu thử vào workbook thật hoặc sửa cấu hình Telegram cá nhân.
- `uv run pytest`: **124 passed, 1 skipped** (symlink). Sau chỉnh nhãn Fluent của Cài đặt, chạy lại 9 test Settings đạt; Ruff check/format và git diff --check đạt, 75 file.
- Native Windows: mở trang Cài đặt với mặc định một file, chụp/xem bố cục, sửa nhãn để hiển thị đúng và đóng exit code 0. Chưa kiểm tra ghi vào workbook đang mở bằng Excel thật; khi khóa file, SQLite vẫn giữ và UI cho Ghi lại Excel.
- Các phần trước đây nói cấm ghi vào template/chọn merge-replace là lịch sử, đã được yêu cầu này thay thế.


### Nút gửi thử Telegram / bật nhắc nền khi lưu lịch — 17/11/2026

- Thêm Gửi tin thử Telegram bên cạnh Kiểm tra kết nối trong Cài đặt. Dùng snapshot ô đang nhập, không tự lưu, không tự retry; hai nút khóa trong lúc yêu cầu đang xử lý. Lỗi an toàn không chứa token. Người dùng nhấn Lưu để lịch dùng cấu hình mới.
- Form lịch mặc định chọn Bật nhắc nền sau khi lưu, cho phép bỏ chọn. Lưu lịch và bật worker là hai bước riêng: khởi động thất bại không rollback lịch, có phản hồi rõ. Launcher đợi khóa OS tối đa 5 giây hoặc báo lỗi tiến trình đã thoát, không coi Popen là đã chạy.
- Worker đọc lại Telegram đã lưu trước mỗi lần gửi, reset kiểm tra token/đích khi thay đổi. Nếu đọc cấu hình lỗi, không gửi bằng đích cũ. Không cần dừng/bật chỉ để đổi cấu hình lưu trong UI sau khi đã nâng cấp worker sang code mới.
- Chẩn đoán thực tế lúc làm task: lịch mới đã đến hạn nhưng worker dừng, attempts=0; cấu hình Chat ID vẫn trùng ID bot. Không thay bằng Chat ID test, không sửa dữ liệu/cấu hình thật hoặc bật worker thật. Không gửi thêm tin thật trong task này; tin test thành công ở phiên trước chỉ chứng minh transport đến đích test.
- `uv run pytest`: **123 passed, 1 skipped** (symlink), Ruff check/format đạt (75 file), git diff --check đạt. Bao phủ nút gửi thử dùng input chưa lưu, khóa bấm trùng, lỗi không retry; lưu lịch tự gọi start, lỗi startup giữ lịch và opt-out không bật; worker đọc đích mới, đọc lỗi không gửi sang đích cũ.
- Native Windows: mở Cài đặt và form lịch bằng database tạm, chụp/xem giao diện hai nút Telegram và checkbox bật nền, đóng exit code 0. Chưa kiểm chứng lịch gửi thật với cấu hình nhận chính của người dùng; cần nhập đúng Chat ID trong Cài đặt, lưu và dùng worker mới.


### Tách hồ sơ / Lịch nhắc nhở và Telegram — 17/11/2026

- Loại bỏ tác vụ tạo/sửa lịch khỏi repository hồ sơ; form hồ sơ không còn khoảng báo trước hoặc bật nhắc tự động. Deadline vẫn lưu trong hồ sơ/Excel. Mọi tạo/sửa lịch nằm ở module Lịch nhắc nhở, có lấy deadline ban đầu từ hồ sơ và preview ngày/giờ gửi. Sửa hồ sơ sau đó không thay lịch; xóa hồ sơ vẫn hủy lịch liên quan chưa gửi theo quy tắc đã duyệt.
- Migration v5 đặt lại record_managed=0 cho lịch cũ, giữ ID/deadline/kết quả gửi; có thể sửa lịch cũ tại trang Nhắc nhở nếu chưa gửi. Không tự hủy các lịch đang có.
- Chẩn đoán cấu hình thật (không lộ credentials): getMe/getChat hợp lệ nhưng đích trùng ID bot; worker dừng; lịch còn hiệu lực đang chờ ngày hôm sau, attempts=0, lịch trước đã hủy. Một lần gửi test được cho phép đã thất bại; không tự retry lệnh này. Sau /start và xác nhận chat chỉ dùng test, đã gửi đúng một tin kiểm tra được Telegram API chấp nhận, không lưu đích test vào cấu hình. Đã kiểm tra file settings.json giữ nguyên byte-for-byte. Người dùng đặt Chat ID chính trong Cài đặt. Không lưu ID/chat/token thật trong repo.
- Thêm nút Kiểm tra Telegram không gửi tin; transport kiểm tra getMe/getChat trước lần gửi đầu, từ chối ID của bot. Lỗi HTTP/mạng chuyển thành thông báo an toàn; engine giữ lỗi an toàn từng kênh và vẫn che lỗi không tin cậy.
- `uv run pytest`: **120 passed, 1 skipped** (symlink); `uv run ruff check .`, `uv run ruff format --check .` đạt, 75 file. `git diff --check` đạt.
- Test GUI kiểm tra tạo hồ sơ không tạo lịch, tạo lịch riêng không đổi hồ sơ; test migration v4→v5 giữ lịch và cho sửa, mock Telegram bot-as-recipient/HTTP errors không lộ token; launcher GUI thực sự bật/dừng worker với database trống đạt.
- Đã mở native Windows cả form hồ sơ và form lịch bằng dữ liệu tạm, xem screenshot, đóng sạch exit code 0. Chưa nghiệm thu popup Windows/bản frozen. Các mục phía dưới là lịch sử trước lần tách module này.


### Deadline / Excel có sẵn — 17/11/2026

- Deadline ở form là `dd/MM/yyyy HH:mm:ss` giờ Việt Nam; khoảng báo trước là số giây nguyên dương/preset. Giờ nhắc yêu cầu = deadline trừ khoảng báo trước rồi áp dụng khung gửi cũ. Lưu/sửa hồ sơ tự quản lý lịch cùng transaction; thay ghi chú không tạo trùng. Lịch tự động sửa qua form hồ sơ.
- Schema v4 giữ dữ liệu và lịch cũ; không tự chuyển thời lượng cũ thành ngày/giờ. Bảng `excel_record_links` lưu liên kết dòng để chỉ xóa/đổi mã dòng từng được app ghi trong chế độ giữ cũ.
- Workbook người dùng sửa đã bỏ H cũ: sau đó bỏ cột STT: hiện 14 cột A–N, mã hồ sơ ở A, deadline ở F, trạng thái M, ghi chú N; không ghi giờ nhắc/khoảng báo trước. Agent không sửa file mẫu, không xóa file khóa `~$so_theo_doi.xlsx` do Excel tạo.
- Hai chat cũ có quyết định tái tạo toàn bộ; yêu cầu hiện tại thay thế quyết định đó bằng ghi vào file có sẵn. Cài đặt có cả hai chế độ giữ dòng cũ/theo mã và thay toàn bộ, mặc định chưa chọn chế độ nên không ghi để tránh chọn thay người dùng. Cấu hình v1 giữ Telegram nhưng không tự chọn workbook cũ.
- `uv run pytest`: **110 passed, 1 skipped** trên Windows. Ruff check và format đạt (75 file). `git diff --check` đạt.
- Bao phủ deadline/báo trước, biên giờ, rollback hồ sơ+lịch, giữ legacy, merge/replace workbook có sẵn, giữ dòng ngoài app và workbook parts, từ chối mã trùng/layout cũ, khóa giả lập giữ workbook/liên kết cũ.
- Native Windows smoke: mở Cài đặt và form Thêm hồ sơ, kiểm tra ô deadline và nhắc trước, chụp/xem bố cục, đóng exit code 0; toàn bộ dùng dữ liệu tạm, không gửi notification. File mẫu đang được Excel giữ mở; Get-FileHash bị khóa, không ghi hoặc thay đổi file đó.
- Chưa gửi Telegram/Windows Notification thật, chưa build frozen hoặc kiểm chứng khóa file bằng Excel thật. Các mục/số test cũ phía dưới là lịch sử trước thay đổi workflow này.

### Module Cài đặt ngày 17/11/2026

- Thêm trang Cài đặt vào thanh điều hướng: Telegram Token/Chat ID, chọn thư mục xuất Excel, xem đường dẫn SQLite/mẫu gốc/sổ hiện tại và mở thư mục dữ liệu.
- Cấu hình lưu atomic vào `settings.json` trong thư mục dữ liệu; token mã hóa Windows DPAPI, không vào SQLite/log. Cấu hình Telegram đã lưu ưu tiên biến môi trường; worker cần dừng/bật lại. Thư mục xuất Excel áp dụng khi mở lại GUI, không di chuyển file hoặc database cũ.
- `uv run pytest`: **94 passed, 1 skipped** trên Windows; gồm DPAPI thật, lưu lỗi giữ file cũ, validation, thao tác UI, worker đọc credentials đã lưu (không gửi thật), khởi động GUI dùng vị trí xuất đã lưu.
- Không thêm dependency, không thay schema hoặc mẫu Excel. Chưa gửi Telegram thật hoặc build bản frozen cho module này.

### Review trên Windows ngày 17/11/2026

**Kết quả mới nhất sau khi người dùng tắt Smart App Control:**

- Xác nhận `VerifiedAndReputablePolicyState=0`; import `PyQt6.sip`, `QtGui`, `QtWidgets` thành công.
- `uv run pytest`: **88 passed, 1 skipped** trên Windows / Python 3.12.10; cả 5 test từng lỗi do bị chặn DLL đã đạt. Test symlink vẫn bỏ qua vì môi trường không hỗ trợ tạo symlink.
- `uv run ruff check .` và `uv run ruff format --check .`: đạt (68 file).
- Smoke test Windows native (không dùng Qt offscreen): khởi động app bằng database tạm, xác nhận cửa sổ hiển thị và Dashboard là trang mặc định, đóng khi task hoàn tất; exit code 0. Không dùng dữ liệu thật, không bật worker hoặc gửi notification. Đây là kiểm tra khởi động tự động, chưa thay thế nghiệm thu bố cục/thao tác thực tế của người dùng.
- Không cần sửa code ứng dụng để xử lý lỗi chặn. Chưa build `.exe`, gửi thông báo thật hoặc kiểm tra Excel đang khóa file.

**Chẩn đoán trước khi người dùng tắt Smart App Control (đã giải quyết):**

- Đối chiếu code composition root, ba trang điều hướng và script đóng gói với bàn giao; không sửa code ứng dụng.
- `uv run pytest` không khởi chạy được launcher do Windows Application Control (`os error 4551`).
- `uv run python -m pytest`: **83 passed, 5 failed, 1 skipped** trên Windows / Python 3.12.10. Cả 5 lỗi tại bước import PyQt6 (`sip`/`QtGui`) do Application Control chặn DLL, nên chưa kiểm chứng được GUI/lifecycle; chưa có kết luận lỗi nghiệp vụ từ các test này. Một test symlink Excel bỏ qua vì môi trường không hỗ trợ tạo symlink.
- `uv run ruff check .`: đạt; `uv run ruff format --check .`: đạt (68 file).
- SHA-256 template vẫn khớp `852e36cbc6c646ab7e1c6242a8a3dd213a8a66719018d322930b949cc6a30242`.
- Chưa build `.exe`, gửi thông báo thật hoặc kiểm tra Microsoft Excel thật. Cần môi trường Windows cho phép nạp DLL PyQt6 trước khi nghiệm thu giao diện.
- Chẩn đoán: `VerifiedAndReputablePolicyState=1`; CodeIntegrity event 3077 xác nhận policy `VerifiedAndReputableDesktop` chặn `PyQt6/QtGui.pyd` và `Scripts/pytest.exe`. `QtGui.pyd` không có chữ ký số; không có Zone.Identifier để xử lý bằng Unblock-File. Đây là Smart App Control, không phải thiếu DLL hay lỗi nghiệp vụ. Người dùng đã xác nhận và tự tắt Smart App Control trước khi chạy lại các kiểm tra đạt ở trên. Theo [Microsoft FAQ](https://support.microsoft.com/en-us/windows/security/threat-malware-protection/smart-app-control-frequently-asked-questions), không có ngoại lệ riêng từng app; phương án giữ bảo vệ là dùng binary có chữ ký hợp lệ.

### Kết quả lịch sử trên Linux

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
| 17/11/2026 | Review trạng thái trên Windows: 83 test đạt, 5 lỗi do Application Control chặn DLL PyQt6, 1 bỏ qua; Ruff/format và hash template đạt; cập nhật bàn giao, không sửa code ứng dụng |
| 17/11/2026 | Người dùng tắt Smart App Control; kiểm tra lại Windows đạt 88 test, 1 bỏ qua; Ruff/format đạt; smoke khởi động Dashboard native và đóng sạch exit code 0; không sửa code ứng dụng |
| 17/11/2026 | Thêm launcher Windows `chay_xaydungso.bat` và hướng dẫn chạy; kiểm tra diff, chưa thử nhấp đúp launcher; không chạy lại pytest vì không sửa Python |
| 17/11/2026 | Sửa placeholder form hồ sơ: ví dụ từng trường, ngày/giờ gợi ý `dd/MM/yyyy HH:mm`, thời lượng số giây nguyên dương; giữ các trường theo dõi là văn bản nhập tay. Kiểm tra GUI workflow/foundation: 6 test đạt; Ruff/format đạt |
| 17/11/2026 | Thêm module Cài đặt Telegram và thư mục xuất Excel, token mã hóa DPAPI; worker đọc cấu hình đã lưu; 94 test đạt, 1 bỏ qua trên Windows |
| 17/11/2026 | Sửa workflow deadline trừ khoảng báo trước, schema v4 và lịch tự động cùng transaction; ghi workbook có sẵn A–O theo chế độ người dùng chọn, không ghi giờ nhắc; 110 test đạt, 1 bỏ qua; native Windows smoke đạt |
| 17/11/2026 | Tách CRUD và lịch nhắc, schema v5 giữ lịch cũ; chẩn đoán Telegram sai Chat ID/worker dừng/lịch chưa đến hạn; thêm kiểm tra kết nối và lỗi an toàn; 120 test đạt, 1 bỏ qua; đã gửi một tin test được API chấp nhận, giữ nguyên cấu hình; Chat ID chính do người dùng nhập trong Cài đặt |
| 17/11/2026 | Thêm Gửi tin thử Telegram, mặc định bật nhắc nền khi lưu lịch và nạp lại cấu hình Telegram trước mỗi lần gửi; 123 test đạt, 1 bỏ qua; không thay cấu hình chính bằng đích test |
| 17/11/2026 | Gộp còn một File Excel làm việc, dùng trực tiếp so_theo_doi.xlsx, luôn cập nhật theo mã; 124 test đạt, 1 bỏ qua; native UI và 9 test Settings sau chỉnh nhãn đạt |
| 17/11/2026 | Cố định toàn ứng dụng nền trắng/chữ đen, tắt Mica và dark mode; 125 test đạt, 1 bỏ qua; native Windows kiểm tra Dashboard/Cài đặt/form đạt |
| 18/11/2026 | Đổi BAT sang launcher WScript chạy ẩn, log/hộp thoại thay terminal; smoke end-to-end Windows từ working directory khác và đường dẫn có dấu cách/& đạt; không chạy lại pytest |
| 18/11/2026 | Xác nhận Excel tự ghi ngay khi Lưu hồ sơ, đổi nhãn thành Thử lại Excel và thông báo rõ hơn; kiểm tra GUI đọc ô đã ghi trước thao tác retry, 22 test liên quan đạt |
| 18/11/2026 | Tạo CONTEXT.md tổng hợp hiểu biết hiện tại, các quyết định đã thay thế, workflow hồ sơ/Excel/lịch nhắc/Telegram và giới hạn nghiệm thu; thêm link vào docs/README.md; kiểm tra UTF-8, liên kết và diff, không chạy lại test ứng dụng |
| 18/11/2026 | Parse thời gian form bắt buộc dd/mm/yyyy hh:mm có số 0 đầu. Theo yêu cầu người dùng bỏ cột STT: so_theo_doi.xlsx xóa cột A (dữ liệu và header dịch trái, A–N), writer/mapping/test/docs theo 14 cột; SQLite vốn không có STT nên không đổi schema; workbook cũ 15 cột bị từ chối; 125 test đạt, 1 bỏ qua; Ruff/format đạt; chưa mở thử trong Microsoft Excel |
| 18/11/2026 | Đổi cột G thành Ngày hẹn trả: header G3 so_theo_doi.xlsx, nhãn form, field `return_appointment_date`, migration schema v6 đổi tên cột SQLite giữ dữ liệu; thêm test migration v5→v6 |
| 18/11/2026 | Chuyển mockup HTML Quản lý hồ sơ sang PyQt/Fluent: thanh điều hướng Tổng quan / Quản lý hồ sơ / Nhắc nhở, Cài đặt ở đáy; trang hồ sơ có toolbar tìm + lọc trạng thái kèm số lượng, bảng mã/tên/địa chỉ/hạn/trạng thái (quá hạn đỏ), khung chi tiết 3 nhóm; bỏ các phần mockup chưa có dữ liệu (Loại công trình, Bản đồ quy hoạch, phân trang...). 129 test đạt, 1 bỏ qua; Ruff đạt; chỉ chụp offscreen, chưa xem native Windows |
| 18/11/2026 | Chỉnh giống thiết kế Stitch hơn: thanh tiêu đề/thanh điều hướng nền tím nhạt, logo, badge số hồ sơ chưa hoàn thành và lịch nhắc hôm nay; tiêu đề trang có ô icon; ô tìm có chip Ctrl+K; bộ lọc trạng thái có chấm/ô đếm; header bảng chữ hoa nền nhạt, mã hồ sơ font mono; chân bảng "Hiển thị N trên tổng số M"; khung chi tiết chữ nhỏ, nhãn (Còn 02 ngày). 129 test đạt, 1 bỏ qua; Ruff đạt; chụp offscreen |
| 18/11/2026 | Theo lựa chọn người dùng: ô tick + chọn tất cả, thao tác hàng loạt Hoàn thành/Chưa hoàn thành/Xóa (ghi Excel một lần, `Records.set_status`/`delete_many`), phân trang 14 dòng. 133 test đạt, 1 bỏ qua; Ruff đạt; chụp offscreen, chưa xem native |
| 18/11/2026 | Căn thẳng bảng hồ sơ (ô chọn tất cả, tiêu đề cột, badge). Làm lại hộp thoại Thêm/Sửa hồ sơ theo ảnh Stitch (`record_dialog.py`); Ngày hẹn trả kết quả kiểm tra định dạng dd/mm/yyyy hh:mm khi nhập mới/sửa. 133 test đạt, 1 bỏ qua; Ruff đạt; render native Windows |
| 18/11/2026 | Bảng hồ sơ thêm cột Số điện thoại, Ngày tiếp nhận, Ngày hẹn trả, Giao nhận (cuộn ngang, kéo được độ rộng); sửa chữ đè ở cột Trạng thái; khung chi tiết chỉ hiện khi chọn hồ sơ. 133 test đạt, 1 bỏ qua; Ruff đạt; render native Windows |
| 18/11/2026 | Theo yêu cầu: cột thời gian liền nhau, Trạng thái ở cuối; thêm đường kẻ cột; bảng giãn hết chiều ngang khi đóng khung chi tiết. 133 test đạt, 1 bỏ qua; Ruff đạt; render native Windows |
| 18/11/2026 | Bỏ chip và phím tắt Ctrl+K ở ô tìm kiếm hồ sơ |
| 18/11/2026 | Làm lại trang Tổng quan theo ảnh Stitch: thẻ Quá hạn thay Nhắc hôm nay (badge vẫn giữ), % tổng số, bảng Hồ sơ cần chú ý (quá hạn hoặc hạn trong 24 giờ, tối đa 10, nút Chi tiết nhảy tới hồ sơ), thẻ lịch nhắc sắp tới, nút Thêm hồ sơ. Snapshot thêm `open_deadlines`/`overdue_records`/`attention`. Test backend + UI mới |
| 18/11/2026 | Tổng quan: bỏ % tổng số, Đã hoàn thành màu xanh lá. Trang Nhắc nhở làm lại theo zip Stitch (`reminders_page.py`): thẻ Chờ gửi/Đã gửi/Gửi lỗi, tìm/lọc/sắp xếp, bảng theo kênh, thao tác Sửa/Hủy, phân trang; Cấu hình mở Cài đặt. Form tạo/sửa lịch giữ nguyên |
| 18/11/2026 | Hộp thoại Tạo/Sửa lịch nhắc theo ảnh Stitch (`reminder_dialog.py`); tách khung hộp thoại dùng chung `card_dialog.py` cho cả form hồ sơ; bỏ EditorDialog/ReminderDialog cũ trong `forms.py`; DurationInput thành danh sách "Trước …" + tự nhập giây |
| 18/11/2026 | Trang Nhắc nhở: thêm cột ô tick + chọn tất cả, thanh thao tác Xóa/Bỏ chọn và nút xóa từng lịch; `SqliteReminders.delete` xóa vĩnh viễn (cascade lịch sử gửi), giữ lịch đang gửi. Test store + GUI |
| 18/11/2026 | Ô tick nhỏ 16px theo DESIGN.md (bảng, tiêu đề, hộp thoại); bấm ô tick không chọn dòng; thêm hiệu ứng mở khung chi tiết, thanh thao tác hàng loạt và hiện hộp thoại (`motion.py`) |
| 19/11/2026 | Bỏ dòng logo "Xây Dựng Số" trong thanh điều hướng theo yêu cầu (tên vẫn ở thanh tiêu đề) |
| 19/11/2026 | Chuyển 21 icon sang Fluent UI System Icons (Windows 11, MIT) — người dùng đồng ý tải SVG từ github.com/microsoft/fluentui-system-icons; `icons.py` + thư mục `icons/` kèm LICENSE, thêm vào build PyInstaller; test icon. Bản .exe chưa build lại để kiểm tra |
| 19/11/2026 | Màn hình Nhắc nhở → Cấu hình theo zip Stitch: quản lý mẫu nội dung thông báo (SQLite v7 `notification_templates`, 4 mẫu sẵn, một mặc định), biến {{ma_ho_so}}/{{ho_ten}}/{{han_xu_ly}}, văn bản thường nhiều dòng theo lựa chọn người dùng, xem trước Telegram/Windows; form lịch nhắc dùng mẫu đã lưu, ô nội dung nhiều dòng. Test domain/SQLite/GUI |
| 19/11/2026 | Hộp xác nhận (xóa/hủy lịch/bỏ thay đổi) chỉ hiện thẻ, nền làm mờ nhẹ slate ~30% thay vì phủ trắng; nút nguy hiểm màu đỏ (`ConfirmBox`) |
| 19/11/2026 | Làm lại trang Cài đặt theo ảnh: 3 mục Dữ liệu (SQLite) / Telegram Bot / Sổ theo dõi Excel, thẻ thông số chỉ đọc (`SqliteDiagnostics`), kiểm tra Telegram trả thêm tên cuộc trò chuyện; bỏ Sao lưu/Nhập Excel (cấm), Nhật ký xử lý/Tự phát hiện ID (chưa đặc tả). Test diagnostics + GUI |
| 19/11/2026 | Cập nhật toàn bộ `docs/` và README theo hành vi hiện tại; gộp và xóa 6 file trùng lặp (architecture/layers, roadmap/phase-01, development/implementation-status, cpxd/workflow, excel/export-workflow, reminders/overview); kiểm tra không còn link hỏng. 158 test đạt, 1 bỏ qua |
| 19/11/2026 | Tổng quan: trạng thái trống căn giữa (icon + tiêu đề + mô tả); thẻ Chưa hoàn thành vàng, Đã hoàn thành xanh lá, Quá hạn đỏ. Chuẩn hóa chữ: font và thang cỡ gom về `theme.py` (token `@font`/`@mono`/`@fs_*`), từ 14 cỡ còn 7; Consolas cho mã hồ sơ và ngày giờ trong bảng; sửa ô Mã hồ sơ trong form không ăn Consolas. Đo lại font thực tế mọi trang/hộp thoại + render native. 159 test đạt, 1 lỗi do workbook làm việc mất dòng 5 trống (không liên quan), 1 bỏ qua |
| 19/11/2026 | Đổi logo ứng dụng sang `presentation/logo.svg` (navy) cho cửa sổ/thanh tác vụ (AppUserModelID riêng), tạo `packaging/xaydungso.ico` 9 cỡ bằng `packaging/make_icon.py` cho bản `.exe`. Gộp `docs/` từ 16 file thành 8 file phẳng (README kèm lộ trình, architecture, ui, dashboard, records, excel, reminders, settings); giữ nguyên đường dẫn mẫu `so_theo_doi.xlsx`; cập nhật AGENTS/README/CONTEXT, kiểm tra không còn link/anchor hỏng |
| 19/11/2026 | Theo yêu cầu: chuyển 8 file đặc tả từ `docs/` sang `.claude/docs/`; thay `AGENTS.md` bằng `CLAUDE.md` (Claude Code tự nạp), viết gọn lại và cập nhật bảng định tuyến tài liệu. `docs/` chỉ còn `modules/excel/templates/so_theo_doi.xlsx` vì app, cấu hình người dùng và build đang dùng đường dẫn này. Kiểm tra link/anchor: không lỗi |
| 19/11/2026 | Chuyển `CLAUDE.md` và `process.md` vào `.claude/` (Claude Code vẫn tự nạp `.claude/CLAUDE.md`); gộp phần riêng của `CONTEXT.md` (quyết định đã thay thế, kiểm chứng/chưa nghiệm thu) vào `.claude/docs/README.md` rồi xóa `CONTEXT.md`. Gốc dự án chỉ còn `README.md`. Các mục nhật ký cũ có thể nhắc đường dẫn cũ |
| 19/11/2026 | Trang tải xuống tĩnh `website/` theo zip Stitch (Miasma, CSS thuần thay Tailwind CDN, icon Lucide nội tuyến); nút tải trỏ `releases/latest/download/<RELEASE_ASSET>` cấu hình trong `website/js/config.js` (tạm `XayDungSo.exe` — chưa có bản phát hành; bản onedir hiện tại không chạy được nếu chỉ tải một .exe). Sửa nội dung không đúng sự thật của bản Stitch (số phiên bản, dung lượng, phím tắt, Google Drive). Thêm `.github/workflows/deploy-website.yml` (Pages, chỉ đăng `website/`). Kiểm tra render 1280px/375px, link nội bộ; chưa chạy workflow trên GitHub |
| 19/11/2026 | Logo: hiện trên thanh tiêu đề (trước tên app); thanh tác vụ hiện logo nhờ AppUserModelID gán cho từng cửa sổ (`presentation/taskbar.py`, Python bản Store bỏ qua ID tiến trình); thêm nền trắng dưới phần rỗng của logo để rõ trên thanh tác vụ tối, tạo lại `.ico`. Đã chụp thanh tác vụ thật xác nhận. Test `tests/test_taskbar.py` |
| 19/11/2026 | Chỉ hỗ trợ Windows: bỏ nhánh Linux (thư mục XDG, khóa `fcntl`, `start_new_session`), bỏ các kiểm tra `sys.platform` trong DPAPI, toast, taskbar, build; bỏ `skipif` theo nền tảng và test giả lập Linux. Giữ marker `sys_platform == 'win32'` trong pyproject để không phải khóa lại `uv.lock`. 160 test đạt, 1 lỗi Excel cũ, 1 bỏ qua (symlink cần Developer Mode) |
| 19/11/2026 | Excel: người dùng chốt chỉ cần đúng tiêu đề/tên trường; định dạng dòng dữ liệu của file trống không quan trọng. Bỏ hai kiểm tra chiều cao/style dòng 6 trong `test_snapshot_preserves_template_parts_layout_and_text` (phụ thuộc dòng 5 mẫu của file làm việc); không đổi code ghi Excel, không sửa workbook. 161 test đạt, 1 bỏ qua |
| 19/11/2026 | Khởi động cùng Windows (người dùng chọn: chỉ nhắc nền, tự bật lần đầu mở app): `infrastructure/startup.py` tạo lối tắt `Xây Dựng Số - Nhắc nền.lnk` trong Startup qua PowerShell/WScript.Shell (giá trị base64, lưu tên ASCII rồi đổi tên); `worker_command()` dùng chung; công tắc ở Cài đặt → Telegram Bot. Đã thử thật: lối tắt tạo trong Startup, mở lối tắt chạy được worker ẩn (thư mục tạm). Phát hiện: Python Store chuyển hướng thư mục dữ liệu sang `Packages\...\LocalCache\Local\xaydungso`. 165 test đạt, 1 bỏ qua |
| 19/11/2026 | Sửa build: `--specpath build` làm đường dẫn `--add-data` tương đối bị tìm trong `build/`; đổi sang đường dẫn tuyệt đối (dấu `;`). Đã build `dist/XayDungSo` (97 MB) và chạy thật với thư mục dữ liệu/APPDATA tạm: cửa sổ mở, tạo database, tạo lối tắt Startup trỏ `XayDungSo.exe --reminder-worker`, mở lối tắt chạy được worker ẩn, `--reminder-worker --once` thoát 0 |
| 19/11/2026 | Khay hệ thống (người dùng chọn cách 2: icon khi app mở, nhấp đúp mở app): X ẩn xuống khay, menu Mở/Thoát (`presentation/tray.py`); một GUI mỗi người dùng qua `QLocalServer` (`presentation/single_instance.py`); VBS dùng `launcher-2.log` khi `launcher.log` bị giữ (trước đó lần mở thứ hai qua VBS báo lỗi). Đã thử thật qua VBS: ẩn, mở lần 2 hiện lại cửa sổ cũ; Thoát kết thúc mã 0. Test `tests/test_tray.py` |
| 19/11/2026 | Sửa lỗi launcher báo `-1073741819` (0xC0000005 trong Qt6Widgets) sau khi Thoát từ khay: app thoát mã 0 nhưng cửa sổ (tray/server giữ tham chiếu) bị hủy lúc tắt Python, sau QApplication. Nay `app.py` đóng server và `sip.delete(window)` trước khi trả về. Event log xác nhận lỗi cũ; 3 lần thoát qua menu khay sau khi sửa không còn crash |
| 19/11/2026 | Menu khay chỉ chữ: **Mở**, **Thoát**. Cửa sổ mở giữa màn hình (`MainWindow.center_on_screen`, màn hình có chuột, vùng làm việc); đo thật 1280×800 tại (320,120) trên màn hình 1920×1032 |
| 19/11/2026 | Bỏ thông báo "Xây Dựng Số vẫn đang chạy" khi bấm X ẩn xuống khay (người dùng yêu cầu) |
| 19/11/2026 | Bộ cài `dist/xaydungso_setup.exe` (28 MB) từ `packaging/xaydungso.iss` bằng Inno Setup 7.1.1: cài theo người dùng, lối tắt Start Menu, tự tắt bản đang chạy (`PrepareToInstall` + taskkill, vì X chỉ ẩn xuống khay), gỡ cài đặt xóa lối tắt Startup và giữ dữ liệu. Đã thử thật: cài im lặng vào thư mục tạm, mở app, gỡ cài đặt (tắt app, xóa file/lối tắt/mục Apps), không crash. Chưa thử cài bằng giao diện và đăng nhập lại Windows với bản cài |

Cập nhật file này sau mỗi phiên, phân biệt code đã có, kiểm tra đã chạy và phần chưa nghiệm thu.
