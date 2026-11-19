"""Atomic local preferences; Telegram token protected with Windows user DPAPI."""

import base64
import ctypes
import json
import os
import tempfile
from pathlib import Path

from xaydungso.application.settings import Preferences


def protect_token(value: bytes, *, decrypt=False) -> bytes:
    from ctypes import wintypes

    class Blob(ctypes.Structure):
        _fields_ = [("size", wintypes.DWORD), ("data", ctypes.POINTER(ctypes.c_char))]

    source_buffer = ctypes.create_string_buffer(value)
    source = Blob(len(value), ctypes.cast(source_buffer, ctypes.POINTER(ctypes.c_char)))
    target = Blob()
    crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.LocalFree.restype = ctypes.c_void_p
    if decrypt:
        result = crypt32.CryptUnprotectData(
            ctypes.byref(source), None, None, None, None, 1, ctypes.byref(target)
        )
    else:
        result = crypt32.CryptProtectData(
            ctypes.byref(source), None, None, None, None, 1, ctypes.byref(target)
        )
    if not result:
        raise RuntimeError("Không thể bảo vệ/đọc Bot Token bằng tài khoản Windows này.")
    try:
        return ctypes.string_at(target.data, target.size)
    finally:
        kernel32.LocalFree(ctypes.cast(target.data, ctypes.c_void_p))


class FilePreferences:
    def __init__(self, directory: Path):
        self.path = directory / "settings.json"

    def load(self) -> Preferences:
        try:
            content = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return Preferences()
        try:
            data = json.loads(content)
            if data.get("version") not in (1, 2):
                raise ValueError("Unsupported preferences")
            folder, chat, encrypted = (
                data["excel_file"] if data["version"] == 2 else "",
                data["telegram_chat_id"],
                data["telegram_token"],
            )
            if not all(isinstance(value, str) for value in (folder, chat, encrypted)):
                raise ValueError("Invalid preferences")
            token = (
                protect_token(
                    base64.b64decode(encrypted, validate=True), decrypt=True
                ).decode("utf-8")
                if encrypted
                else ""
            )
            policy = data.get("excel_policy", "")
            if policy not in ("", "merge", "replace"):
                raise ValueError("Invalid Excel policy")
            return Preferences(folder, token, chat, policy)
        except (ValueError, KeyError, TypeError, AttributeError, RuntimeError):
            raise RuntimeError(
                "Không đọc được cài đặt. Kiểm tra file settings.json và tài khoản Windows."
            ) from None

    def save(self, value: Preferences) -> None:
        encrypted = (
            base64.b64encode(
                protect_token(value.telegram_token.encode("utf-8"))
            ).decode("ascii")
            if value.telegram_token
            else ""
        )
        data = {
            "version": 2,
            "excel_file": value.excel_file,
            "excel_policy": value.excel_policy,
            "telegram_chat_id": value.telegram_chat_id,
            "telegram_token": encrypted,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.path.parent,
                delete=False,
                suffix=".tmp",
            ) as stream:
                temporary = Path(stream.name)
                json.dump(data, stream, ensure_ascii=False, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        finally:
            if temporary:
                temporary.unlink(missing_ok=True)
