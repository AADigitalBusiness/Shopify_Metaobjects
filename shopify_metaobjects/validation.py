"""Lightweight validation against definition field lists."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from shopify_metaobjects.errors import ValidationError


def validate_fields_against_definition(
    fields: Sequence[Mapping[str, Any]] | Mapping[str, Any],
    *,
    required_keys: Sequence[str] | None = None,
    allowed_keys: Sequence[str] | None = None,
) -> None:
    """Validate field keys for upsert. Raises ValidationError on failure."""
    if isinstance(fields, Mapping):
        keys = list(fields.keys())
    else:
        keys = [str(f.get("key")) for f in fields if f.get("key") is not None]

    if required_keys:
        missing = [k for k in required_keys if k not in keys]
        if missing:
            raise ValidationError(f"missing required fields: {missing}")

    if allowed_keys is not None:
        unknown = [k for k in keys if k not in allowed_keys]
        if unknown:
            raise ValidationError(f"unknown fields for definition: {unknown}")
