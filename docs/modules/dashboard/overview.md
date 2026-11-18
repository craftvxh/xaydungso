# Tổng quan (Dashboard)

Trang **mở mặc định**: xem nhanh tình hình hồ sơ và lịch nhắc, rồi đi tới trang quản lý.
Không có biểu đồ, phân tích dự đoán hay tính toán xây dựng. Định nghĩa từng con số:
[metrics.md](metrics.md).

## Bố cục (thiết kế Stitch, 18/11/2026)

- Tiêu đề **Tổng quan** + chip `Đồng bộ: HH:MM` (thời điểm tải gần nhất); nút **Tải lại** và
  **Thêm hồ sơ** (chuyển sang Quản lý hồ sơ và mở form thêm mới).
- Bốn thẻ: **Tổng hồ sơ**, **Chưa hoàn thành**, **Đã hoàn thành** (số màu xanh lá), **Quá hạn**
  (nền đỏ nhạt). Không hiển thị % tổng số (người dùng bỏ).
- Bảng **Hồ sơ cần chú ý**: hồ sơ quá hạn hoặc đến hạn trong 24 giờ, cảnh báo dạng badge, nút
  **Chi tiết** (mở đúng hồ sơ) và **Xem tất cả**.
- Cột **Lịch nhắc sắp tới**: tối đa 10 thẻ lịch, nút **Xem lịch nhắc**.
- Số hồ sơ chưa hoàn thành và số lịch nhắc hôm nay cũng hiện ở badge trên thanh điều hướng.

## Nguồn dữ liệu

`Dashboard widget → Application Dashboard.load() → SQLite read adapter`.

- Chỉ đọc SQLite (`records`, `reminders`, `reminder_deliveries`) trong một read transaction,
  không đọc Excel. Không thêm bảng thống kê.
- Application xác định thời điểm và ngày theo giờ Việt Nam, áp dụng quy tắc quá hạn / sắp hạn
  trên các hồ sơ chưa hoàn thành có hạn xử lý; widget không chạy SQL.
- Truy vấn chạy ngoài Qt event loop bằng task runner chung.

## Tải lại và lỗi

- Tải khi mở ứng dụng, khi quay lại trang, sau thay đổi hồ sơ/lịch, khi bấm Tải lại và mỗi
  30 giây khi trang đang hiển thị và task runner rảnh.
- Đang tải: dấu `—`, không giả số 0. Database rỗng: các số 0 và thông báo không có lịch/hồ sơ
  cần chú ý; nút điều hướng vẫn dùng được.
- Lỗi: thông báo ngắn và cho Tải lại; không hiện exception SQL hay dữ liệu nhạy cảm.
