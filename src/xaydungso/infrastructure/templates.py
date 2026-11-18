"""SQLite storage for notification templates (one default at most)."""

import sqlite3
from datetime import UTC, datetime

from xaydungso.domain.records import ValidationError
from xaydungso.domain.templates import Template
from xaydungso.infrastructure.database import Database


def _template(row: sqlite3.Row) -> Template:
    return Template(
        row["id"], row["name"], row["body"], bool(row["is_default"]), row["updated_at"]
    )


class SqliteTemplates:
    def __init__(self, database: Database):
        self.database = database

    def list(self) -> list[Template]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM notification_templates "
                "ORDER BY is_default DESC, updated_at DESC, id"
            ).fetchall()
        return [_template(row) for row in rows]

    def save(self, template: Template) -> Template:
        now = datetime.now(UTC).isoformat(timespec="seconds")
        with self.database.connect() as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            if template.is_default:
                connection.execute("UPDATE notification_templates SET is_default=0")
            elif template.id is not None:
                current = connection.execute(
                    "SELECT is_default FROM notification_templates WHERE id=?",
                    (template.id,),
                ).fetchone()
                if current is not None and current["is_default"]:
                    raise ValidationError(
                        "Cần có một mẫu mặc định. Hãy đặt mẫu khác làm mặc định trước."
                    )
            if template.id is None:
                cursor = connection.execute(
                    "INSERT INTO notification_templates(name,body,is_default,updated_at) "
                    "VALUES (?,?,?,?)",
                    (template.name.strip(), template.body, template.is_default, now),
                )
                template_id = cursor.lastrowid
            else:
                cursor = connection.execute(
                    "UPDATE notification_templates SET name=?,body=?,is_default=?,"
                    "updated_at=? WHERE id=?",
                    (
                        template.name.strip(),
                        template.body,
                        template.is_default,
                        now,
                        template.id,
                    ),
                )
                if cursor.rowcount != 1:
                    raise ValidationError(
                        "Mẫu không còn tồn tại. Hãy tải lại danh sách."
                    )
                template_id = template.id
            row = connection.execute(
                "SELECT * FROM notification_templates WHERE id=?", (template_id,)
            ).fetchone()
        return _template(row)

    def delete(self, template_id: int) -> None:
        with self.database.connect() as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT is_default FROM notification_templates WHERE id=?",
                (template_id,),
            ).fetchone()
            if row is None:
                return
            if row["is_default"]:
                raise ValidationError(
                    "Không xóa được mẫu mặc định. Hãy đặt mẫu khác làm mặc định trước."
                )
            connection.execute(
                "DELETE FROM notification_templates WHERE id=?", (template_id,)
            )
