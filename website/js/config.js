/*
 * Cấu hình trang tải xuống — chỉ sửa ở đây.
 *
 * Nút "Tải xuống" trỏ tới:
 *   https://github.com/<REPO>/releases/latest/download/<RELEASE_ASSET>
 * GitHub chuyển hướng URL này tới tệp đính kèm cùng tên trong bản phát hành mới nhất
 * (không tính bản nháp / pre-release). Nếu bản phát hành chưa có tệp đúng tên này,
 * liên kết trả về 404.
 *
 * RELEASE_ASSET: tên tệp đính kèm trong GitHub Release — PHẢI khớp chính xác (phân biệt
 * hoa/thường). Hiện chưa có quy trình phát hành: packaging/build_windows.py tạo bản
 * PyInstaller "onedir" (dist/XayDungSo/XayDungSo.exe kèm thư mục _internal), nên một
 * mình XayDungSo.exe KHÔNG chạy được. Khi phát hành, hãy đính kèm một tệp .exe chạy độc
 * lập (bản onefile hoặc bộ cài) rồi đặt đúng tên đó vào đây.
 *
 * Nếu JavaScript bị tắt, các nút dùng href mặc định trong index.html (trang Releases).
 */
window.XDS_CONFIG = {
  REPO: 'craftvxh/xaydungso',
  RELEASE_ASSET: 'XayDungSo.exe', // TODO: xác nhận tên tệp khi tạo bản phát hành đầu tiên
  VERSION_LABEL: 'Phiên bản 0.1.0', // khớp version trong pyproject.toml
};
