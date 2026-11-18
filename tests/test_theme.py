"""Fixed light colors also cover late dialogs and disabled native/Fluent inputs."""

from test_foundation import run_python


def test_white_black_theme_overrides_dark_mode_and_late_widgets():
    run_python("""
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QPalette
        from PyQt6.QtWidgets import QApplication,QDialog,QDateTimeEdit,QLabel,QVBoxLayout
        from PyQt6.QtTest import QTest
        from qfluentwidgets import Theme,setTheme,isDarkTheme,PrimaryPushButton,LineEdit
        from xaydungso.presentation.theme import configure_theme
        app=QApplication([])
        setTheme(Theme.DARK,save=False)
        configure_theme(app)
        assert not isDarkTheme()
        assert app.testAttribute(Qt.ApplicationAttribute.AA_DontUseNativeDialogs)
        parent=QDialog()
        layout=QVBoxLayout(parent)
        label=QLabel('Text',parent)
        button=PrimaryPushButton('Action',parent)
        edit=LineEdit(parent)
        edit.setPlaceholderText('Example')
        for widget in (label,button,edit):layout.addWidget(widget)
        parent.show()
        QTest.qWait(100)
        button.setEnabled(False)
        QTest.qWait(10)
        for widget in (parent,label,button,edit):
            palette=widget.palette()
            for group in (QPalette.ColorGroup.Active,QPalette.ColorGroup.Disabled):
                assert palette.color(group,QPalette.ColorRole.Window).name()=='#ffffff'
                assert palette.color(group,QPalette.ColorRole.WindowText).name()=='#000000'
                assert palette.color(group,QPalette.ColorRole.ButtonText).name()=='#000000'
        assert edit.palette().color(QPalette.ColorRole.PlaceholderText).name()=='#000000'
        assert button.grab().toImage().pixelColor(8,10).name()=='#ffffff'
        later=QDialog(parent)
        later_layout=QVBoxLayout(later)
        date=QDateTimeEdit(later)
        date.setCalendarPopup(True)
        later_layout.addWidget(date)
        later.show()
        QTest.qWait(50)
        assert later.palette().color(QPalette.ColorRole.Window).name()=='#ffffff'
        assert date.palette().color(QPalette.ColorRole.Text).name()=='#000000'
        later.close()
        parent.close()
    """)
