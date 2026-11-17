# Tổng quan kiến trúc

## Mục tiêu

`xaydungso` là ứng dụng desktop local-first dành cho **một người dùng**, Windows 11 là môi trường mục tiêu. Không cần backend server, tài khoản đăng nhập, API phục vụ nhiều người dùng hay microservices cho MVP.

## Cách tiếp cận

**Modular Monolith + Layered Architecture** theo hướng pragmatic: phân tách trách nhiệm đủ rõ nhưng không tạo class, interface, service rỗng để dự phòng.

- **Presentation:** PyQt6 và QFluentWidgets.
- **Application:** điều phối use case và giao dịch.
- **Domain:** quy tắc và mô hình nghiệp vụ thuần Python.
- **Infrastructure:** SQLite, xuất Excel, xuất Word, các cổng thông báo khi được triển khai.
- **Core:** cấu hình và logging kỹ thuật dùng chung, phạm vi hạn chế.

SQLite là nguồn dữ liệu duy nhất có thẩm quyền. Excel là đầu ra dẫn xuất và **không** làm nguồn dữ liệu nhập ngược. Chi tiết: [Data flow](data-flow.md).

## Stack và triển khai từng bước

Python 3.12, Astral uv, PyQt6 + PyQt6-Fluent-Widgets; pytest và Ruff. SQLite và các thư viện xử lý tài liệu được tích hợp ở Phase tương ứng. Không triển khai chức năng cloud, backup/restore hoặc đa người dùng.

## Điều kiện thay đổi

Kiến trúc có thể phát triển theo yêu cầu thực tế, nhưng bất kỳ quyết định nào đổi ranh giới layer, source of truth hay hướng dữ liệu phải được ghi nhận trước khi thay đổi code.
