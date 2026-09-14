"""Metaobject definition introspection helpers."""

from __future__ import annotations

from typing import Any

from shopify_metaobjects import operations
from shopify_metaobjects.errors import GraphQLError, TransportError
from shopify_metaobjects.transport import GraphQLTransport


def fetch_definition_by_type(transport: GraphQLTransport, metaobject_type: str) -> dict[str, Any] | None:
    response = transport.execute(
        operations.DEFINITION_BY_TYPE_QUERY,
        {"type": metaobject_type},
    )
    if response.graphql_errors:
        raise GraphQLError(
            response.detail or "GraphQL errors fetching definition",
            errors=response.graphql_errors,
            retryable=response.retryable,
            error_code=response.error_code,
        )
    if response.data is None and response.error_code:
        raise TransportError(
            response.detail or "transport failure",
            retryable=response.retryable,
            error_code=response.error_code,
        )
    data = response.data or {}
    return data.get("metaobjectDefinitionByType")


def introspect_field_keys(definition: dict[str, Any] | None) -> list[str]:
    if not definition:
        return []
    fields = definition.get("fieldDefinitions") or definition.get("fields") or []
    return [str(f.get("key")) for f in fields if f.get("key")]
