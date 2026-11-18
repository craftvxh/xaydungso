"""Notification text templates with {{variable}} placeholders (plain text)."""

import re
from dataclasses import dataclass

from xaydungso.domain.records import ValidationError

# User-approved (19/11/2026, Stitch "Cấu hình"): plain multi-line text, three
# record fields. Unknown placeholders are left untouched.
VARIABLES = (
    ("ma_ho_so", "Mã hồ sơ"),
    ("ho_ten", "Họ tên"),
    ("han_xu_ly", "Hạn xử lý"),
)
PLACEHOLDER = re.compile(r"\{\{\s*([a-z_]+)\s*\}\}")


@dataclass(frozen=True)
class Template:
    id: int | None
    name: str
    body: str
    is_default: bool = False
    updated_at: str = ""

    def __post_init__(self):
        if not self.name.strip():
            raise ValidationError("Tên mẫu thông báo không được để trống.")
        if not self.body.strip():
            raise ValidationError("Nội dung mẫu thông báo không được để trống.")


def render(body: str, values: dict[str, str]) -> str:
    """Replace known {{placeholders}}; keep unknown ones visible."""
    return PLACEHOLDER.sub(lambda m: values.get(m.group(1), m.group(0)), body)
