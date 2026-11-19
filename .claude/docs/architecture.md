# Kiến trúc và phát triển

## Kiến trúc

### Mục tiêu

Ứng dụng desktop **local-first cho một người dùng**, **chỉ chạy trên Windows** (10/11, ưu tiên 11); không giữ nhánh code Linux/macOS (dữ liệu ở `%LOCALAPPDATA%`, khóa worker `msvcrt`, DPAPI, toast, taskbar). Không có backend
server, đăng nhập, API nhiều người dùng, cloud hay backup/restore. Luồng dữ liệu:
[data-flow.md](#luồng-dữ-liệu--sqlite-là-nguồn-chính).

### Modular Monolith + Layered Architecture

Phân tách trách nhiệm vừa đủ; không tạo class, interface hay service rỗng để dự phòng.

| Layer (`src/xaydungso/…`) | Nhiệm vụ | Không được |
|---|---|---|
| `presentation` | Cửa sổ Fluent, các trang, hộp thoại, widget dùng chung, theme/icon/animation | SQL trực tiếp, quy tắc nghiệp vụ, ghi file |
| `application` | Use case: hồ sơ, nhắc nhở + engine gửi, mẫu thông báo, Dashboard, cài đặt; các cổng (ports) | Phụ thuộc widget Qt |
| `domain` | Mô hình và quy tắc thuần Python: hồ sơ, giờ nhắc, mẫu thông báo | Import PyQt6, SQLite, thư viện tài liệu |
| `infrastructure` | SQLite (migration, repository, diagnostics chỉ đọc), ghi Excel, Telegram, Windows toast, cấu hình DPAPI, quản lý tiến trình worker | Quyết định quy tắc nghiệp vụ thay Domain |
| `core` | Cấu hình ứng dụng, logging, đường dẫn dữ liệu | Trở thành nơi gom helper/nghiệp vụ |

Hướng phụ thuộc: Presentation → Application → Domain; Infrastructure hiện thực các cổng của
lớp trong. Composition root là `app.py` (GUI) và `worker.py` (nhắc nền) — nơi duy nhất nối
dependencies. Không ép mapping một-một giữa `docs/modules/` và Python packages.

### Thành phần chính

- **GUI** (`uv run xaydungso`): `FluentWindow` với Tổng quan, Quản lý hồ sơ, Nhắc nhở (+ màn
  hình Cấu hình mẫu), Cài đặt. Tác vụ I/O chạy ngoài Qt event loop qua `presentation/tasks.py`.
- **Worker** (`uv run xaydungso-reminders`): tiến trình riêng không cần Qt, đọc SQLite và gửi
  thông báo; một worker cho mỗi thư mục dữ liệu (khóa hệ điều hành).
- **Dữ liệu** (thư mục dữ liệu người dùng): `xaydungso.sqlite3` (nguồn chính duy nhất),
  `settings.json`, `reminders.log`, `launcher.log`, file khóa/dừng worker.
- **Excel**: đầu ra một chiều vào sổ làm việc có sẵn; không bao giờ là nguồn dữ liệu.

### Stack

Python 3.12, Astral uv (`uv.lock`), PyQt6 + PyQt6-Fluent-Widgets, SQLite (thư viện chuẩn),
pytest, Ruff. Icon: Fluent UI System Icons (MIT, đi kèm repository). Đóng gói: PyInstaller
(`packaging/build_windows.py`) + bộ cài Inno Setup 7 (`packaging/xaydungso.iss` →
`dist/xaydungso_setup.exe`, cài theo người dùng, không ký số vì chỉ dùng nội bộ).

### Thay đổi kiến trúc

Mọi quyết định đổi ranh giới layer, nguồn dữ liệu chính hoặc hướng dữ liệu phải được ghi vào
tài liệu trước khi đổi code.

## Luồng dữ liệu — SQLite là nguồn chính

### Hồ sơ

`Form → Application/Domain kiểm tra → SQLite commit → ghi Excel`

- Mọi thêm/sửa/xóa hồ sơ đi qua ứng dụng; xóa là vĩnh viễn sau xác nhận.
- Lưu hồ sơ không tạo hay sửa lịch nhắc. Xóa hồ sơ hủy các lịch liên quan chưa gửi (cùng transaction).
- Không đọc dữ liệu hồ sơ từ Excel.

### Sổ Excel

`SQLite (hồ sơ đã commit) → writer → file .xlsx có sẵn do người dùng chọn`

- Ghi tự động sau mỗi thay đổi hồ sơ; giữ dòng cũ, thêm/sửa theo mã hồ sơ, giữ bố cục workbook.
- Lỗi Excel **không** hoàn tác SQLite; ghi qua file tạm rồi thay thế an toàn.
- Chi tiết: [Excel](excel.md#excel--ghi-một-chiều-vào-sổ-làm-việc-có-sẵn).

### Nhắc nhở

`Form lịch (+ mẫu thông báo) → SQLite (reminders, deliveries) → worker → Telegram / Windows`

- Nội dung lịch được tạo từ mẫu (`notification_templates`) khi người dùng chọn mẫu trong form;
  lịch lưu nội dung đã điền biến.
- Giờ gửi = hạn xử lý − khoảng báo trước, áp dụng khung 07:00–23:00
  ([quy tắc](reminders.md#nhắc-nhở--quy-tắc-nghiệp-vụ)).
- Worker claim từng kênh, gửi, ghi kết quả/thử lại; độc lập Qt và Excel. Excel không chứa giờ nhắc.

### Tổng quan và Cài đặt

- Tổng quan đọc một snapshot SQLite qua Application ([metrics](dashboard.md#tổng-quan--định-nghĩa-chỉ-số)).
- Cài đặt đọc số liệu chỉ đọc (`SqliteDiagnostics`) và lưu cấu hình vào `settings.json`
  (token mã hóa DPAPI); worker đọc lại cấu hình Telegram trước mỗi lần gửi.

### Văn bản Word (tương lai)

`SQLite / tính toán Domain → tạo văn bản → file Word` — hoãn tới khi có mẫu và mapping được duyệt.

## Development conventions

### Python and tooling

- Python 3.12; quản lý môi trường, dependencies và lockfile bằng `uv`.
- Code dùng type hints khi có ích; tên module, function `snake_case`, class `PascalCase`.
- Import rõ ràng, không wildcard imports hoặc sửa `sys.path` để chữa package layout.
- Không khởi tạo `QApplication` khi import module; tránh block Qt main thread.
- Logging bằng Python standard library; không ghi thông tin cá nhân nhạy cảm vào logs.

### Nguyên tắc thiết kế

- KISS, YAGNI, DRY một cách thực dụng; ưu tiên thay đổi nhỏ và đọc được.
- Ponytail-style: tránh abstraction chưa cần; không hy sinh tính đúng, an toàn dữ liệu hoặc kiểm thử để giảm số dòng code.
- Không thêm dependency vì có thể sẽ cần trong tương lai.
- Không tự ý sửa thuật toán, mapping hay model đã chốt mà không cập nhật tài liệu tương ứng.

### Git

- Dùng Conventional Commits khi thích hợp: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`.
- Không commit `.venv`, caches, local logs, tệp xuất chứa dữ liệu cá nhân.
- Commit `pyproject.toml` cùng `uv.lock` khi thay đổi dependencies.
- Agent không tự commit/push; developer quyết định sau review.

### Review

Kiểm tra phạm vi diff, dependencies, layer boundary, lỗi ngoại lệ, typing, test và tính nhất quán với tài liệu nghiệp vụ.

## Kiểm thử và Definition of Done

### Lệnh tiêu chuẩn

```bash
uv sync --locked
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Không tuyên bố test đạt nếu chưa chạy. Ghi lại kết quả thực tế (số test đạt/bỏ qua) vào
[process.md](../process.md).

### Phạm vi test

- **Unit:** quy tắc domain (định dạng ngày giờ, giờ nhắc, khung gửi, mẫu thông báo, trạng thái
  lịch), mapping Excel, quy tắc Dashboard.
- **Integration (SQLite thật trong thư mục tạm):** migration/rollback, CRUD và ràng buộc, thao
  tác hàng loạt, xóa vĩnh viễn, mẫu thông báo, diagnostics chỉ đọc, engine nhắc (retry riêng
  kênh, claim/lease, chống trùng), ghi workbook có sẵn (merge, giữ dòng ngoài ứng dụng, file
  bị khóa giả lập, sai mẫu).
- **GUI:** chạy trong tiến trình con với `QT_QPA_PLATFORM=offscreen` và thư mục dữ liệu tạm
  (`tests/test_foundation.py::run_python`); mô phỏng bấm nút, nhập form, hộp xác nhận
  (`ConfirmBox.exec` được thay bằng giá trị trả về cố định).
- **Transport:** Telegram và Windows toast được mock; không gửi thông báo thật, không dùng
  credentials thật.
- Không dùng hoặc sửa workbook làm việc thật; test sao chép mẫu vào thư mục tạm.
- Một test bị bỏ qua khi hệ điều hành không cho tạo symlink.

### Kiểm tra giao diện native

Ảnh chụp offscreen không đủ để đánh giá bố cục: chạy với `QT_QPA_PLATFORM=windows` (Windows)
và dữ liệu tạm khi cần so sánh với thiết kế. Không dùng dữ liệu cá nhân thật.

### Acceptance

- Đúng yêu cầu và quy tắc đã duyệt; không thêm tính năng ngoài phạm vi.
- Test phù hợp đã chạy và đạt; lỗi còn lại được ghi rõ.
- Tài liệu được cập nhật khi thay đổi hành vi, schema hoặc contract.
- Những gì chưa kiểm chứng trên Windows thật (thông báo, bản `.exe`, khóa Excel thật) được nêu rõ.
