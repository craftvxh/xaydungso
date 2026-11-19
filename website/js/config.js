/*
 * Cấu hình trang tải xuống — chỉ sửa ở đây.
 *
 * Nút "Tải xuống" trỏ tới:
 *   https://github.com/<REPO>/releases/latest/download/<RELEASE_ASSET>
 * GitHub chuyển hướng URL này tới tệp đính kèm cùng tên trong bản phát hành mới nhất
 * (không tính bản nháp / pre-release). Nếu bản phát hành chưa có tệp đúng tên này,
 * liên kết trả về 404.
 *
 * RELEASE_ASSET: tên bộ cài đính kèm trong GitHub Release — PHẢI khớp chính xác (phân biệt
 * hoa/thường). Bộ cài được tạo bởi packaging/xaydungso.iss (Inno Setup) tại
 * dist/xaydungso_setup.exe; mỗi bản phát hành đính kèm tệp này với đúng tên đó.
 *
 * Nút tải trong index.html cũng có sẵn href tới đúng link này (chạy được cả khi không có JS
 * hoặc trình duyệt còn giữ bản cũ của tệp này). Đổi tên tệp thì sửa cả ở đó.
 * Mỗi lần sửa tệp này hoặc main.js: tăng số ?v=… ở hai thẻ <script> cuối index.html để
 * trình duyệt tải bản mới thay vì bản đã lưu.
 */
window.XDS_CONFIG = {
  REPO: 'craftvxh/xaydungso',
  RELEASE_ASSET: 'xaydungso_setup.exe',
  VERSION_LABEL: 'Phiên bản 0.1.0', // khớp version trong pyproject.toml và packaging/xaydungso.iss
};
