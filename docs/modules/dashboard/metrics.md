# Dashboard — Định nghĩa chỉ số

## Snapshot và thời gian

Một lần tải lấy thời điểm `as_of` duy nhất, quy đổi sang **Asia/Ho_Chi_Minh**.
Ngày hôm nay là từ 00:00:00 địa phương, bao gồm đầu ngày và không bao gồm 00:00:00
ngày kế tiếp. Adapter chuyển các biên này sang timestamp UTC chuẩn hiện có trong SQLite.
Không dựa vào timezone hệ điều hành, `created_at` của lịch hoặc các cột Excel theo dõi.

## Bốn chỉ số

| Nhãn | Định nghĩa |
|---|---|
| Tổng hồ sơ | COUNT các hàng hiện có trong `records` |
| Chưa hoàn thành | COUNT hồ sơ có status chính xác `Chưa hoàn thành` |
| Đã hoàn thành | COUNT hồ sơ có status chính xác `Đã hoàn thành` |
| Nhắc hôm nay | COUNT lịch `cancelled = 0` có `notify_at` trong ngày địa phương hiện tại |

- Hồ sơ đã xóa vĩnh viễn không được tính; tổng hồ sơ bằng tổng hai trạng thái.
- Nhắc hôm nay đếm **lịch duy nhất**, không đếm số lần gửi hoặc số kênh.
- Chỉ số hôm nay bao gồm lịch đã gửi và chưa gửi có giờ gửi được lên lịch trong ngày;
  loại lịch hủy. Đây không phải số thông báo gửi thành công hoặc số lịch còn chờ.
- Lịch độc lập không liên kết hồ sơ vẫn được tính. Trạng thái hoàn thành hồ sơ không
  tự hủy lịch, vì không có quy tắc nghiệp vụ như vậy.
- Gửi bù không tự chuyển `notify_at` sang ngày thực gửi; không diễn giải chỉ số thành
  số thông báo thực gửi hôm nay.

## Lịch nhắc sắp tới

- Lịch chưa hủy, `notify_at >= as_of`, còn ít nhất một kênh có state khác `sent`.
- Lịch gửi thành công một kênh nhưng còn kênh chưa gửi vẫn chỉ xuất hiện một hàng.
- Không bao gồm lịch quá hạn đang chờ gửi bù; xem toàn bộ trạng thái ở trang Nhắc nhở.
- Thứ tự `notify_at ASC, id ASC`; hiển thị tối đa **10 lịch gần nhất** để giữ Dashboard gọn.
  Nút Xem lịch nhắc mở trang quản lý tất cả lịch.
- Hiển thị nội dung, mã hồ sơ nếu liên kết còn tồn tại (nếu không: `Không liên kết`),
  và `notify_at` theo giờ Việt Nam. Không tự điền hoặc sửa bất kỳ trường nào.

## Những gì không thuộc module

Không biểu đồ, tỷ lệ dự đoán, phân tích hiệu suất, tính toán deadline mới, trạng thái
hồ sơ bổ sung, truy vấn Excel hoặc Word Generation. Dashboard chỉ tổng hợp dữ liệu
SQLite đã commit; không thay đổi hành vi scheduler hoặc điều kiện hoàn thành hồ sơ.
