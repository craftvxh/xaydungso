# Testing & Definition of Done

## Phạm vi

- **Unit tests:** domain calculations, thời gian nhắc, mapping không phụ thuộc filesystem khi có thể.
- **Integration tests:** SQLite transactions, Excel Exporter với workbook thật, lỗi file bị khóa, thay thế đầu ra, xuất sau xóa.
- **GUI tests:** chỉ khi môi trường hỗ trợ Qt; không khởi động GUI trong import tests.

## Lệnh tiêu chuẩn (sau khi Foundation được triển khai)

```bash
uv sync --locked
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Không tuyên bố test qua nếu chưa chạy. Với CI/headless, phải nêu rõ những kiểm tra GUI không thực hiện được.

## Acceptance

- Thỏa yêu cầu và quy tắc đang được phê duyệt.
- Không thêm tính năng ngoài Phase.
- Kiểm thử phù hợp đã chạy, lỗi được ghi nhận.
- Tài liệu được cập nhật nếu thay đổi behavior, schema hoặc contract.

Chi tiết riêng của từng Phase: [Roadmap](../roadmap/overview.md).
