"""User preferences and validation, independent of UI and storage details."""

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Protocol

from xaydungso.domain.records import ValidationError


@dataclass(frozen=True)
class Preferences:
    excel_file: str = ""
    telegram_token: str = field(default="", repr=False)
    telegram_chat_id: str = ""
    excel_policy: str = "merge"


class PreferencesStore(Protocol):
    def load(self) -> Preferences: ...
    def save(self, value: Preferences) -> None: ...


class Settings:
    def __init__(
        self,
        store: PreferencesStore,
        directory: Path,
        template: Path,
        telegram_checker=None,
        telegram_tester=None,
    ):
        self.store = store
        self.directory = directory.resolve()
        self.template = template.resolve()
        self.telegram_checker = telegram_checker
        self.telegram_tester = telegram_tester

    def test_telegram(self, token, chat_id):
        if self.telegram_tester is None:
            raise ValidationError("Không có kết nối gửi thử Telegram.")
        self.telegram_tester(token.strip(), chat_id.strip())
        return "Telegram đã chấp nhận tin nhắn kiểm tra. Hãy kiểm tra cuộc trò chuyện nhận tin. Cài đặt chưa được lưu tự động."

    def check_telegram(self, token, chat_id):
        if self.telegram_checker is None:
            raise ValidationError("Không có kết nối kiểm tra Telegram.")
        return self.telegram_checker(token.strip(), chat_id.strip())

    def load(self) -> Preferences:
        return replace(self.store.load(), excel_policy="merge")

    def export_path(self, value: Preferences) -> Path:
        return Path(value.excel_file) if value.excel_file else self.template

    def save(self, value: Preferences) -> Preferences:
        token, chat = value.telegram_token.strip(), value.telegram_chat_id.strip()
        if bool(token) != bool(chat):
            raise ValidationError("Nhập đủ Bot Token và Chat ID, hoặc để trống cả hai.")
        filename = value.excel_file.strip() or str(self.template)
        if filename:
            path = Path(filename).expanduser()
            if (
                not path.is_absolute()
                or not path.is_file()
                or path.suffix.lower() != ".xlsx"
            ):
                raise ValidationError(
                    "Chọn một file Excel .xlsx có sẵn, có đường dẫn đầy đủ."
                )
            if path.is_symlink():
                raise ValidationError(
                    "Chọn đường dẫn file Excel trực tiếp, không dùng liên kết."
                )
            filename = str(path.resolve())
        value = Preferences(filename, token, chat, "merge")
        self.store.save(value)
        return value
