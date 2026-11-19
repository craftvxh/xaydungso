; Bộ cài Xây Dựng Số: đóng gói dist\XayDungSo (PyInstaller onedir) thành dist\xaydungso_setup.exe.
; Build trước:  uv run python packaging/build_windows.py
; Biên dịch:    ISCC.exe packaging\xaydungso.iss
#define AppName "Xây Dựng Số"
#define AppVersion "0.1.0"
#define AppExe "XayDungSo.exe"

[Setup]
; Giữ nguyên AppId qua mọi phiên bản để bản mới cài đè bản cũ.
AppId={{88B84719-7E89-4595-B66F-468973518B6D}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=Xây Dựng Số
; Cài cho riêng người dùng, không cần quyền admin: %LOCALAPPDATA%\Programs\XayDungSo
PrivilegesRequired=lowest
DefaultDirName={autopf}\XayDungSo
DisableProgramGroupPage=yes
OutputDir=..\dist
OutputBaseFilename=xaydungso_setup
SetupIconFile=xaydungso.ico
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; The app hides to the tray on close, so Restart Manager cannot close it: [Code] stops it.
CloseApplications=no

[Tasks]
Name: "desktopicon"; Description: "Tạo lối tắt ngoài Desktop"; Flags: unchecked

[Files]
Source: "..\dist\XayDungSo\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "Mở {#AppName}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Dừng app và nhắc nền trước khi gỡ để xóa được file.
Filename: "{sys}\taskkill.exe"; Parameters: "/F /IM {#AppExe}"; Flags: runhidden; RunOnceId: "StopApp"

[UninstallDelete]
; Lối tắt Startup do app tạo ở lần mở đầu tiên. Dữ liệu trong %LOCALAPPDATA%\xaydungso được GIỮ LẠI.
Type: files; Name: "{userstartup}\Xây Dựng Số - Nhắc nền.lnk"

[Code]
// Stop a running copy (window in the tray and the reminder worker) before files are replaced.
function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  ResultCode: Integer;
begin
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/F /IM {#AppExe}', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Result := '';
end;
