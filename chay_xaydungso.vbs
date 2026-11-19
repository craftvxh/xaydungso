Option Explicit

Dim shell, files, baseDir, uvPath, entry, folder, logDir, logPath, command, result
Set shell = CreateObject("WScript.Shell")
Set files = CreateObject("Scripting.FileSystemObject")
baseDir = files.GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = baseDir

uvPath = shell.ExpandEnvironmentStrings("%USERPROFILE%\.local\bin\uv.exe")
If Not files.FileExists(uvPath) Then
    uvPath = ""
    For Each entry In Split(shell.Environment("PROCESS")("PATH"), ";")
        folder = shell.ExpandEnvironmentStrings(Replace(Trim(entry), Chr(34), ""))
        If Len(folder) > 0 Then
            If files.FileExists(files.BuildPath(folder, "uv.exe")) Then
                uvPath = files.BuildPath(folder, "uv.exe")
                Exit For
            End If
        End If
    Next
End If
If Len(uvPath) = 0 Then Fail "Khong tim thay uv. Vui long cai uv roi chay lai."

logDir = shell.ExpandEnvironmentStrings("%LOCALAPPDATA%\xaydungso")
On Error Resume Next
If Not files.FolderExists(logDir) Then files.CreateFolder logDir
If Err.Number <> 0 Then Fail "Khong tao duoc thu muc log: " & logDir
On Error GoTo 0
logPath = files.BuildPath(logDir, "launcher.log")
' A running copy (e.g. hidden in the tray) keeps launcher.log open; this launch
' only asks it to show its window, so log to a second file instead.
If Not CanWrite(logPath) Then logPath = files.BuildPath(logDir, "launcher-2.log")

' Hide the console for uv and Python; capture diagnostics instead of showing a terminal.
command = Quote(shell.ExpandEnvironmentStrings("%ComSpec%")) & " /d /s /c " & _
    Quote(Quote(uvPath) & " run --locked python -m xaydungso > " & Quote(logPath) & " 2>&1")
On Error Resume Next
result = shell.Run(command, 0, True)
If Err.Number <> 0 Then Fail "Khong the khoi dong phan mem. Xem log: " & logPath
On Error GoTo 0
If result <> 0 Then Fail "Phan mem dung voi loi " & result & ". Xem log: " & logPath
WScript.Quit 0

Function CanWrite(path)
    Dim stream
    On Error Resume Next
    Set stream = files.OpenTextFile(path, 8, True)
    CanWrite = (Err.Number = 0)
    If CanWrite Then stream.Close
    On Error GoTo 0
End Function

Function Quote(value)
    Quote = Chr(34) & value & Chr(34)
End Function

Sub Fail(message)
    MsgBox message, vbOKOnly + vbExclamation, "Xay Dung So"
    WScript.Quit 1
End Sub
