"""Notification templates: rendering, seeded rows, one default, deletion rules."""

import pytest

from xaydungso.application.templates import Templates
from xaydungso.domain.records import ValidationError
from xaydungso.domain.templates import Template, render
from xaydungso.infrastructure.templates import SqliteTemplates


@pytest.fixture
def templates(database):
    return Templates(SqliteTemplates(database))


def test_render_replaces_known_and_keeps_unknown_placeholders():
    body = "Hồ sơ {{ma_ho_so}} — {{ ho_ten }} · {{khong_ro}}"
    assert render(body, {"ma_ho_so": "HS-1", "ho_ten": "An"}) == (
        "Hồ sơ HS-1 — An · {{khong_ro}}"
    )


def test_name_and_body_are_required():
    with pytest.raises(ValidationError):
        Template(None, " ", "x")
    with pytest.raises(ValidationError):
        Template(None, "Tên", "  ")


def test_migration_seeds_four_templates_with_one_default(templates):
    items = templates.list()
    assert len(items) == 4
    assert [item.is_default for item in items] == [True, False, False, False]
    assert items[0].name == "Nhắc hồ sơ sắp đến hạn"
    assert "{{han_xu_ly}}" in items[0].body and "\n" in items[0].body


def test_setting_a_new_default_moves_the_flag(templates):
    old_default = templates.list()[0]
    saved = templates.save(Template(None, "Mẫu mới", "Nội dung {{ho_ten}}", True))
    items = {item.id: item for item in templates.list()}
    assert items[saved.id].is_default and not items[old_default.id].is_default
    assert sum(item.is_default for item in items.values()) == 1


def test_default_cannot_be_deleted_or_unset_but_others_can(templates):
    default, other = templates.list()[:2]
    with pytest.raises(ValidationError):
        templates.delete(default.id)
    with pytest.raises(ValidationError):
        templates.save(Template(default.id, default.name, default.body, False))
    templates.delete(other.id)
    assert other.id not in {item.id for item in templates.list()}
    edited = templates.save(Template(default.id, "Đổi tên", "Nội dung mới", True))
    assert edited.name == "Đổi tên" and edited.is_default


def test_templates_page_edit_add_default_and_delete():
    from test_foundation import run_python

    run_python("""
        import time
        from PyQt6.QtTest import QTest
        from PyQt6.QtWidgets import QApplication
        from xaydungso.application.templates import Templates
        from xaydungso.core.paths import data_directory
        from xaydungso.infrastructure.database import Database
        from xaydungso.infrastructure.templates import SqliteTemplates
        import xaydungso.presentation.templates_page as module
        from xaydungso.presentation.tasks import TaskRunner

        app = QApplication([])
        db = Database(data_directory() / 'tpl.sqlite3')
        db.initialize()
        service = Templates(SqliteTemplates(db))
        runner = TaskRunner()
        page = module.TemplatesPage(service, runner)
        page.show()

        def idle():
            limit = time.monotonic() + 5
            QTest.qWait(10)
            while runner.busy:
                assert time.monotonic() < limit
                QTest.qWait(10)

        idle()
        assert len(page.cards) == 4 and page.count.text() == '4 mẫu'
        assert page.current.is_default and not page.dirty
        assert 'CPXD-2026-0089' in page.preview_text.text()  # Sample values.
        page.delete_button.click()  # Default template is protected.
        assert 'mặc định' in page.error.text()
        page.body.setPlainText('Sửa {{ho_ten}}')
        assert page.dirty and page.save_button.isEnabled()
        page.save_button.click()
        idle()
        assert not page.dirty
        assert service.list()[0].body == 'Sửa {{ho_ten}}'

        page.add_button.click()
        page.name.setText('Mẫu mới')
        page.body.setPlainText('')
        page.variable_buttons['ma_ho_so'].click()  # Insert a variable.
        assert page.body.toPlainText() == '{{ma_ho_so}}'
        page.default_check.setChecked(True)
        page.save_button.click()
        idle()
        items = service.list()
        assert len(items) == 5 and items[0].name == 'Mẫu mới' and items[0].is_default
        assert sum(item.is_default for item in items) == 1

        old = next(card for card in page.cards if card.template_id == items[1].id)
        old.click()  # Not dirty: switches without asking.
        assert page.current.id == items[1].id
        module.ConfirmBox.exec = lambda self: 1
        page.delete_button.click()
        idle()
        assert len(service.list()) == 4
        backs = []
        page.back.connect(lambda: backs.append(1))
        page.back_button.click()
        assert backs == [1]
        page.close()
    """)
