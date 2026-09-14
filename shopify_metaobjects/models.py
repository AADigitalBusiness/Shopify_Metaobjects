"""Domain models and operation results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Metaobject:
    type: str
    handle: str
    id: str | None = None
    fields: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_shopify_data(cls, data: dict[str, Any]) -> "Metaobject":
        fields_list = data.get("fields") or []
        fields = {f["key"]: f.get("value") for f in fields_list if "key" in f}
        return cls(
            type=str(data.get("type") or ""),
            handle=str(data.get("handle") or ""),
            id=data.get("id"),
            fields=fields,
        )

    def to_shopify_fields(self) -> list[dict[str, str]]:
        return [{"key": str(k), "value": "" if v is None else str(v)} for k, v in self.fields.items()]


@dataclass
class MetaobjectUpsertResult:
    ok: bool
    gid: str | None = None
    type: str = ""
    handle: str = ""
    user_errors: list[dict[str, Any]] = field(default_factory=list)
    retryable: bool = False
    error_code: str | None = None
    detail: str = ""
    metaobject: Metaobject | None = None


@dataclass
class MetaobjectDeleteResult:
    ok: bool
    deleted_id: str | None = None
    user_errors: list[dict[str, Any]] = field(default_factory=list)
    retryable: bool = False
    error_code: str | None = None
    detail: str = ""
