"""Fluent UI System Icons are bundled with their licence and every icon exists."""

from xaydungso.presentation.icons import ICON_DIR, Icon


def test_every_icon_file_is_a_plain_bundled_svg():
    assert (ICON_DIR / "LICENSE").read_text(encoding="utf-8").startswith("MIT License")
    for member in Icon:
        svg = (ICON_DIR / f"{member.value}.svg").read_text(encoding="utf-8")
        assert svg.startswith("<svg") and "<path" in svg
        assert "<script" not in svg and "href" not in svg
