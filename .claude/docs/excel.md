# Sổ theo dõi Excel

## Excel — Ghi một chiều vào sổ làm việc có sẵn

Ứng dụng **ghi hồ sơ từ SQLite vào một file `.xlsx` có sẵn** do người dùng chọn. Không tạo
file mới, không nhập dữ liệu từ Excel vào SQLite. Mapping từng cột: [field-mapping.md](#excel--mapping-14-cột-an).

### Sổ làm việc

- Mặc định dùng trực tiếp `docs/modules/excel/templates/so_theo_doi.xlsx` làm sổ làm việc
  (người dùng chọn). Có thể đổi sang file `.xlsx` có sẵn khác cùng mẫu tại
  **Cài đặt → Sổ theo dõi Excel**; đổi file áp dụng khi mở lại phần mềm.
- Mẫu hiện hành: `Sheet1`, **14 cột A–N**, tiêu đề A1:N4, dữ liệu từ hàng 5. Không có cột
  STT và cột thời gian nhắc. Cột G có tiêu đề "Ngày hẹn trả".
- File hợp lệ khi **tiêu đề và thứ tự cột** đúng mẫu (người dùng duyệt 19/11/2026). Định dạng dòng
  dữ liệu (chiều cao, style) không bắt buộc: file trống có thể không còn dòng 5 mẫu, khi đó dòng mới
  chỉ lấy style cột.
- Workbook sai mẫu bị từ chối, kể cả mẫu cũ còn cột STT (15 cột A–O) hoặc 16 cột A–P;
  không tự dịch cột. Không phải bộ chuyển đổi cho mọi định dạng workbook.

### Khi nào ghi

1. Sau khi thêm/sửa/xóa hồ sơ (kể cả thao tác hàng loạt) được commit SQLite, use case tự
   ghi Excel — không cần bấm nút riêng.
2. Lỗi Excel (file đang mở/khóa, mất file, sai mẫu) **không** hoàn tác SQLite; giao diện báo
   Excel chưa cập nhật. Lần lưu tiếp theo ghi lại toàn bộ; hoặc dùng
   **Cài đặt → Sổ theo dõi Excel → Ghi lại ngay**.
3. **Mở sổ Excel** (trang Quản lý hồ sơ) hoặc **Mở file Excel** (Cài đặt) mở đúng file làm việc.

### Cách ghi (luôn giữ dòng cũ)

1. Lấy hồ sơ theo `created_at ASC, id ASC`; đọc chính workbook đã chọn, kiểm tra Sheet1 và
   tiêu đề.
2. Khớp mã hồ sơ ở cột A: cập nhật dòng trùng mã, nối dòng mới cuối sổ, **giữ các dòng
   không do ứng dụng ghi**. File có mã trùng bị từ chối thay vì chọn ngẫu nhiên một dòng.
3. `excel_record_links` nhớ mã từng ghi theo từng đường dẫn workbook: khi đổi mã hoặc xóa
   hồ sơ, chỉ xóa dòng ứng dụng từng ghi; không dồn các dòng còn lại.
4. Giữ tiêu đề, merged cells, styles, cấu hình in và mọi phần workbook ngoài vùng dữ liệu.
   Không ghi một mẫu rỗng đè lên sổ đang dùng; không có lựa chọn thay toàn bộ (cấu hình
   `replace` cũ được chuẩn hóa về merge).
5. Ghi file tạm cùng thư mục, kiểm tra ZIP/XML, kiểm tra file đích không đổi trong lúc ghi,
   rồi thay thế an toàn tại cùng đường dẫn. Lỗi ghi: giữ nguyên file cũ, không cập nhật
   `excel_record_links`.
6. Đường dẫn symlink bị từ chối. Mọi giá trị ghi dạng text (inline string).

### Chưa nghiệm thu

Khóa file bằng Microsoft Excel thật và bản đóng gói `.exe` cần kiểm tra trên Windows;
test hiện mô phỏng file bị khóa và xác nhận file cũ được giữ.

## Excel — Mapping 14 cột A–N

`Sheet1`, tiêu đề A1:N4, dữ liệu từ hàng 5. Lịch sử mẫu: bỏ cột Thời gian nhắc nhở
(16 → 15 cột), rồi bỏ cột STT (15 → 14 cột); SQLite không có thuộc tính STT.

| Cột | Tiêu đề | Field | Cách ghi |
|---|---|---|---|
| A | Mã hồ sơ | `record_code` | Text, duy nhất; dùng để tìm dòng khi ghi |
| B | Họ và tên | `applicant_name` | Text Unicode |
| C | SĐT | `phone` | Text, giữ số 0 đầu |
| D | Địa chỉ | `address` | Text |
| E | Thời gian nhận | `received_at` | Text như đã nhập |
| F | Thời hạn xử lý | `deadline_at` | `dd/MM/yyyy HH:mm:ss` theo giờ Việt Nam; trống nếu chưa có |
| G | Ngày hẹn trả | `return_appointment_date` | Text như đã nhập |
| H | Bản vẽ đóng dấu | `drawing_stamp_status` | `Có` / `Chưa` |
| I | Giấy phép đóng dấu | `permit_stamp_status` | `Có` / `Chưa` |
| J | Thời gian giao nhận | `handover_at` | Text như đã nhập |
| K | Chữ ký | `signature_status` | `Đã ký` / `Chưa ký` |
| L | Người ký nhận | `recipient_name` | Text Unicode |
| M | Trạng thái | `status` | `Chưa hoàn thành` / `Đã hoàn thành` |
| N | Ghi chú | `notes` | Text Unicode |

Không ghi giờ nhắc (`notify_at`), khoảng báo trước hoặc các trường legacy. Không suy ra
deadline từ thời lượng cũ.
