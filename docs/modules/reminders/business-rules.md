# Reminder Business Rules — Approved

## 1. Nguyên tắc

- Reminder Engine hoạt động độc lập với Excel. SQLite lưu lịch nhắc, deadline, thời điểm nhắc và trạng thái gửi.
- Người dùng tạo lịch nhắc với **thời điểm bắt đầu mặc định là thời điểm tạo lịch** và có thể sửa giờ bắt đầu.
- Thời lượng: **10 giây (chỉ để test)**, 1 giờ, nửa ngày = **12 giờ thực**, 1 ngày = **24 giờ thực**; cho phép thời lượng hợp lệ khác theo thiết kế UI.
- Tính thời lượng **liên tục theo thời gian thực**, không loại trừ cuối tuần/ngày lễ.
- Múi giờ: **Asia/Ho_Chi_Minh**.
- `deadline_at = start_at + duration` theo thời gian thực.

## 2. Khung giờ gửi

- Được gửi trong **07:00:00 đến 23:00:00**, bao gồm cả hai đầu mút.
- Nếu deadline nằm trong khung cho phép, `notify_at = deadline_at`.
- Nếu deadline nằm ngoài khung, chuyển `notify_at` về **22:00 ngày trước ngày deadline**.
- **Ngoại lệ khi mốc 22:00 đã qua trước thời điểm tạo lịch:** đặt lịch gửi lúc **07:00 ngày tiếp theo**. Không tạo lịch gửi trong quá khứ.

| Deadline | Notify at |
|---|---|
| 18/11/2026 09:00 | 18/11/2026 09:00 |
| 18/11/2026 02:00 | 17/11/2026 22:00 |
| 18/11/2026 23:30 | 17/11/2026 22:00 |
| Tạo 17/11 23:30; deadline 18/11 00:30 | 18/11/2026 07:00 (ngoại lệ) |

## 3. Trạng thái và hành vi

- Một lịch nhắc được xử lý **một lần** (không tự lặp định kỳ). Một hồ sơ có thể có các lịch nhắc riêng nếu người dùng chủ động tạo.
- Sửa lịch chưa gửi: tính lại `deadline_at` và `notify_at`.
- Xóa hồ sơ: hủy các lịch chưa gửi liên quan; không thực hiện soft delete hồ sơ.
- Cần lưu ID lịch nhắc duy nhất và trạng thái gửi để giảm nguy cơ gửi trùng.
- Khi máy/tiến trình không hoạt động và bỏ lỡ lịch, **gửi bù một lần** khi tiến trình hoạt động lại trong khung giờ cho phép; nếu khởi động ngoài khung, đợi đến 07:00 kế tiếp.
- Kênh gửi: **Telegram và Windows Notification**. Theo dõi kết quả từng kênh để không lặp lại kênh đã gửi thành công khi thử lại.
- Việc gửi thực tế chỉ khả thi khi tiến trình nhắc nhở chạy; không bảo đảm gửi đúng thời điểm khi máy tắt.

## 4. Quan hệ với cột Excel

- Trong các cột thời gian Excel, chỉ cột **G — Thời hạn xử lý** biểu diễn thời lượng phục vụ phép tính lịch nhắc.
- F, H, I, L chỉ ghi thông tin theo dõi, không tự tính; đặc biệt **không** tự điền `notify_at` vào cột H.
- Không thêm cột kỹ thuật `deadline_at`, `notify_at` vào workbook chuẩn.

## 5. Yêu cầu triển khai

- Tính toán thời gian phải có unit test cho các mốc 07:00, 23:00, 23:00:01, 22:00 hôm trước, ngoại lệ tạo lịch muộn và thời lượng 10 giây.
- Cần kiểm thử cách chống gửi trùng và retry riêng từng kênh. Thông báo tới hai kênh là hai kết quả vận chuyển riêng, không phải một transaction phân tán.
