"""Taskbar identity is best effort: it never raises."""

from xaydungso.presentation import taskbar


class FakeWindow:
    def winId(self):
        return 0  # Not a real window handle.


def test_invalid_window_fails_quietly():
    assert taskbar.set_taskbar_identity(FakeWindow()) is False
