# Tổng quan — Định nghĩa chỉ số

## Thời điểm và ngày

Mỗi lần tải lấy một thời điểm `as_of` duy nhất theo **Asia/Ho_Chi_Minh**. "Hôm nay" là từ
00:00:00 địa phương (gồm) tới 00:00:00 ngày kế tiếp (không gồm), quy đổi sang UTC để so với
SQLite. Không dựa vào timezone hệ điều hành hay cột Excel.

## Bốn thẻ và badge

Người dùng duyệt 18/11/2026: thẻ thứ tư là **Quá hạn**, thay cho thẻ Nhắc hôm nay (số này
chuyển sang badge của mục Nhắc nhở).

| Nhãn | Định nghĩa |
|---|---|
| Tổng hồ sơ | Số hàng hiện có trong `records` (hồ sơ đã xóa vĩnh viễn không tính) |
| Chưa hoàn thành | Số hồ sơ có status `Chưa hoàn thành`; cũng là badge mục Quản lý hồ sơ |
| Đã hoàn thành | Số hồ sơ có status `Đã hoàn thành` |
| Quá hạn | Số hồ sơ `Chưa hoàn thành` có hạn xử lý và hạn < `as_of` |
| Nhắc hôm nay (badge Nhắc nhở) | Số **lịch** chưa hủy có `notify_at` trong hôm nay — gồm lịch đã và chưa gửi, đếm một lần dù có hai kênh |

- Tổng hồ sơ = Chưa hoàn thành + Đã hoàn thành. Hồ sơ đã hoàn thành hoặc chưa có hạn không quá hạn.
- Lịch độc lập vẫn được đếm. Gửi bù không đổi `notify_at`, nên badge không phải "số tin thực gửi hôm nay".

## Hồ sơ cần chú ý

- Hồ sơ `Chưa hoàn thành` có hạn xử lý và **quá hạn** (hạn < `as_of`) hoặc **sắp hạn**
  (`as_of` ≤ hạn < `as_of` + 24 giờ — người dùng chọn 24 giờ, 18/11/2026).
- Thứ tự: quá hạn trước, rồi sắp hạn; mỗi nhóm theo hạn tăng dần rồi `id`. Hiển thị tối đa
  **10** hồ sơ; chip số lượng đếm toàn bộ.
- Cảnh báo: `Quá hạn`, hoặc `Sắp hạn (Còn N giờ)` / `(Còn N phút)` khi dưới 1 giờ (làm tròn lên).
- Hạn đọc từ `records.deadline_at` (UTC ISO) và so sánh trong Python, không so chuỗi trong SQL.

## Lịch nhắc sắp tới

- Lịch chưa hủy, `notify_at ≥ as_of`, còn ít nhất một kênh chưa `sent`; một thẻ cho mỗi lịch.
- Không gồm lịch đã qua giờ đang chờ gửi bù (xem trang Nhắc nhở).
- Thứ tự `notify_at ASC, id ASC`, tối đa **10** lịch.
- Thẻ: nội dung, mã + họ tên hồ sơ nếu liên kết còn tồn tại (nếu không: `Không liên kết hồ sơ`),
  giờ gửi theo giờ Việt Nam kèm `(Hôm nay)` / `(Ngày mai)`.
