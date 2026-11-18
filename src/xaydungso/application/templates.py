"""Notification template use cases; rendering rules live in the domain."""

from typing import Protocol

from xaydungso.domain.templates import Template


class TemplateStore(Protocol):
    def list(self) -> list[Template]: ...
    def save(self, template: Template) -> Template: ...
    def delete(self, template_id: int) -> None: ...


class Templates:
    def __init__(self, store: TemplateStore):
        self.store = store

    def list(self) -> list[Template]:
        return self.store.list()

    def save(self, template: Template) -> Template:
        return self.store.save(template)

    def delete(self, template_id: int) -> None:
        self.store.delete(template_id)
