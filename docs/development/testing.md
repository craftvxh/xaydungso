# Kiểm thử và Definition of Done

## Lệnh tiêu chuẩn

```bash
uv sync --locked
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Không tuyên bố test đạt nếu chưa chạy. Ghi lại kết quả thực tế (số test đạt/bỏ qua) vào
[process.md](../../process.md).

## Phạm vi test

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

## Kiểm tra giao diện native

Ảnh chụp offscreen không đủ để đánh giá bố cục: chạy với `QT_QPA_PLATFORM=windows` (Windows)
và dữ liệu tạm khi cần so sánh với thiết kế. Không dùng dữ liệu cá nhân thật.

## Acceptance

- Đúng yêu cầu và quy tắc đã duyệt; không thêm tính năng ngoài phạm vi.
- Test phù hợp đã chạy và đạt; lỗi còn lại được ghi rõ.
- Tài liệu được cập nhật khi thay đổi hành vi, schema hoặc contract.
- Những gì chưa kiểm chứng trên Windows thật (thông báo, bản `.exe`, khóa Excel thật) được nêu rõ.
