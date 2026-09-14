"""MetaobjectClient — domain API over an injected GraphQLTransport."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from shopify_metaobjects import operations
from shopify_metaobjects.definitions import fetch_definition_by_type, introspect_field_keys
from shopify_metaobjects.errors import GraphQLError, TransportError, ValidationError
from shopify_metaobjects.models import (
    Metaobject,
    MetaobjectDeleteResult,
    MetaobjectUpsertResult,
)
from shopify_metaobjects.transport import GraphQLResponse, GraphQLTransport
from shopify_metaobjects.validation import validate_fields_against_definition


def _normalize_fields(fields: Sequence[Mapping[str, Any]] | Mapping[str, Any]) -> list[dict[str, str]]:
    if isinstance(fields, Mapping):
        return [{"key": str(k), "value": "" if v is None else str(v)} for k, v in fields.items()]
    out: list[dict[str, str]] = []
    for item in fields:
        key = item.get("key")
        if key is None:
            raise ValidationError("each field requires a key")
        value = item.get("value")
        out.append({"key": str(key), "value": "" if value is None else str(value)})
    return out


class MetaobjectClient:
    def __init__(self, transport: GraphQLTransport):
        self._transport = transport

    def _execute(self, query: str, variables: Mapping[str, Any] | None = None) -> GraphQLResponse:
        response = self._transport.execute(query, variables)
        if response.graphql_errors:
            raise GraphQLError(
                response.detail or "GraphQL errors",
                errors=list(response.graphql_errors),
                retryable=response.retryable,
                error_code=response.error_code,
            )
        if response.data is None and response.error_code:
            raise TransportError(
                response.detail or "transport failure",
                retryable=response.retryable,
                error_code=response.error_code,
            )
        return response

    def upsert(
        self,
        *,
        metaobject_type: str,
        handle: str,
        fields: Sequence[Mapping[str, Any]] | Mapping[str, Any],
    ) -> MetaobjectUpsertResult:
        """Create or update by type+handle using metaobject.fields (partial), never values."""
        normalized = _normalize_fields(fields)
        variables = {
            "handle": {"type": metaobject_type, "handle": handle},
            "metaobject": {"fields": normalized},
        }
        try:
            response = self._execute(operations.UPSERT_MUTATION, variables)
        except TransportError as exc:
            return MetaobjectUpsertResult(
                ok=False,
                type=metaobject_type,
                handle=handle,
                retryable=exc.retryable,
                error_code=exc.error_code,
                detail=str(exc),
            )
        except GraphQLError as exc:
            return MetaobjectUpsertResult(
                ok=False,
                type=metaobject_type,
                handle=handle,
                retryable=exc.retryable,
                error_code=exc.error_code or "graphql_error",
                detail=str(exc),
            )

        payload = ((response.data or {}).get("metaobjectUpsert") or {})
        user_errors = list(payload.get("userErrors") or [])
        if user_errors:
            return MetaobjectUpsertResult(
                ok=False,
                type=metaobject_type,
                handle=handle,
                user_errors=user_errors,
                retryable=False,
                error_code="metaobject_user_errors",
                detail=str(user_errors),
            )

        node = payload.get("metaobject") or {}
        mo = Metaobject.from_shopify_data(node) if node else None
        return MetaobjectUpsertResult(
            ok=True,
            gid=(mo.id if mo else None),
            type=(mo.type if mo else metaobject_type),
            handle=(mo.handle if mo else handle),
            user_errors=[],
            retryable=False,
            metaobject=mo,
        )

    def get_by_handle(self, *, metaobject_type: str, handle: str) -> Metaobject | None:
        response = self._execute(
            operations.GET_BY_HANDLE_LEGACY_QUERY,
            {"handle": handle, "type": metaobject_type},
        )
        node = (response.data or {}).get("metaobject")
        if not node:
            return None
        return Metaobject.from_shopify_data(node)

    def list(
        self,
        *,
        metaobject_type: str,
        first: int = 50,
        after: str | None = None,
    ) -> tuple[list[Metaobject], str | None, bool]:
        response = self._execute(
            operations.LIST_METAOBJECTS_QUERY,
            {"type": metaobject_type, "first": first, "after": after},
        )
        connection = (response.data or {}).get("metaobjects") or {}
        edges = connection.get("edges") or []
        items = [Metaobject.from_shopify_data(edge["node"]) for edge in edges if edge.get("node")]
        page = connection.get("pageInfo") or {}
        return items, page.get("endCursor"), bool(page.get("hasNextPage"))

    def delete(self, *, gid: str) -> MetaobjectDeleteResult:
        try:
            response = self._execute(operations.DELETE_MUTATION, {"id": gid})
        except TransportError as exc:
            return MetaobjectDeleteResult(
                ok=False,
                retryable=exc.retryable,
                error_code=exc.error_code,
                detail=str(exc),
            )
        except GraphQLError as exc:
            return MetaobjectDeleteResult(
                ok=False,
                retryable=exc.retryable,
                error_code=exc.error_code or "graphql_error",
                detail=str(exc),
            )
        payload = ((response.data or {}).get("metaobjectDelete") or {})
        user_errors = list(payload.get("userErrors") or [])
        if user_errors:
            return MetaobjectDeleteResult(
                ok=False,
                user_errors=user_errors,
                error_code="metaobject_user_errors",
                detail=str(user_errors),
            )
        return MetaobjectDeleteResult(ok=True, deleted_id=payload.get("deletedId"))

    def fetch_definition(self, metaobject_type: str) -> dict[str, Any] | None:
        return fetch_definition_by_type(self._transport, metaobject_type)

    def validate_fields(
        self,
        fields: Sequence[Mapping[str, Any]] | Mapping[str, Any],
        *,
        metaobject_type: str | None = None,
        required_keys: Sequence[str] | None = None,
        allowed_keys: Sequence[str] | None = None,
    ) -> None:
        keys_allowed = allowed_keys
        if metaobject_type and keys_allowed is None:
            definition = self.fetch_definition(metaobject_type)
            keys_allowed = introspect_field_keys(definition) or None
        validate_fields_against_definition(
            fields,
            required_keys=required_keys,
            allowed_keys=keys_allowed,
        )
