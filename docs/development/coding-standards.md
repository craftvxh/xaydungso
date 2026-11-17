# Development conventions

## Python and tooling

- Python 3.12; quản lý môi trường, dependencies và lockfile bằng `uv`.
- Code dùng type hints khi có ích; tên module, function `snake_case`, class `PascalCase`.
- Import rõ ràng, không wildcard imports hoặc sửa `sys.path` để chữa package layout.
- Không khởi tạo `QApplication` khi import module; tránh block Qt main thread.
- Logging bằng Python standard library; không ghi thông tin cá nhân nhạy cảm vào logs.

## Nguyên tắc thiết kế

- KISS, YAGNI, DRY một cách thực dụng; ưu tiên thay đổi nhỏ và đọc được.
- Ponytail-style: tránh abstraction chưa cần; không hy sinh tính đúng, an toàn dữ liệu hoặc kiểm thử để giảm số dòng code.
- Không thêm dependency vì có thể sẽ cần trong tương lai.
- Không tự ý sửa thuật toán, mapping hay model đã chốt mà không cập nhật tài liệu tương ứng.

## Git

- Dùng Conventional Commits khi thích hợp: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`.
- Không commit `.venv`, caches, local logs, tệp xuất chứa dữ liệu cá nhân.
- Commit `pyproject.toml` cùng `uv.lock` khi thay đổi dependencies.
- Agent không tự commit/push; developer quyết định sau review.

## Review

Kiểm tra phạm vi diff, dependencies, layer boundary, lỗi ngoại lệ, typing, test và tính nhất quán với tài liệu nghiệp vụ.
