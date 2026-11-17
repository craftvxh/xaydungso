# Phase 01.1 — Project Foundation

## Mục tiêu

Có một ứng dụng desktop PyQt6 + QFluentWidgets tối thiểu, chạy được, có package structure, kiểm thử và tài liệu rõ ràng, **không có nghiệp vụ**.

## In scope

- `uv init --app --package xaydungso`, Python 3.12, `uv.lock`.
- PyQt6, PyQt6-Fluent-Widgets, pytest, Ruff.
- `src/xaydungso` với `presentation`, `application`, `domain`, `infrastructure`, `core` theo nhu cầu thực tế.
- `FluentWindow` tối thiểu và màn hình chào; `main()` + `__main__.py`.
- Configuration, logging đơn giản, import tests, README, AGENTS.md, docs.

## Out of scope

SQLite schema hoặc repository, CRUD, deadline/reminder scheduler, Excel Exporter, Word generation, auth, backup, cloud, đa người dùng, installer, business UI.

## Acceptance criteria

- `uv sync --locked` thành công.
- `uv run python -c "import xaydungso"` thành công.
- `uv run xaydungso` và `uv run python -m xaydungso` khởi chạy giao diện (nếu môi trường GUI hỗ trợ).
- Mở / đóng main window sạch; không tạo QApplication khi import.
- `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .` đạt.
- Docs nhất quán, không có tính năng ngoài phạm vi.

## Trạng thái tài liệu

Bộ `docs/` v1.0 được chuẩn bị trước khi source code Foundation được tạo. **Không đồng nghĩa** implementation hoặc test Phase 01.1 đã hoàn tất.
