"""Confirmation boxes dim the app instead of covering it in white."""

from test_foundation import run_python


def test_confirm_box_uses_dark_veil_and_danger_button():
    run_python("""
        from PyQt6.QtWidgets import QApplication, QWidget
        from xaydungso.presentation.confirm import ConfirmBox
        from xaydungso.presentation.theme import configure_theme
        app = QApplication([])
        configure_theme(app)
        parent = QWidget()
        parent.resize(800, 600)
        box = ConfirmBox('Xóa?', 'Không thể hoàn tác.', parent,
                         yes='Xóa vĩnh viễn', no='Giữ lại')
        sheet = box.windowMask.styleSheet().replace(' ', '')
        assert 'rgba(15,23,42' in sheet, sheet  # Slate veil, not white.
        assert box.property('xdsStyled')  # Not repainted white by the theme.
        assert box.yesButton.text() == 'Xóa vĩnh viễn'
        assert box.cancelButton.text() == 'Giữ lại'
        safe = ConfirmBox('Lưu?', '', parent, danger=False)
        assert not safe.yesButton.property('xdsStyled')
    """)
