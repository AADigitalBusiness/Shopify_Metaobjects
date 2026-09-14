"""Adapter for django_shopify.requests.execute_admin_graphql (lazy Django import)."""

from __future__ import annotations

from typing import Any, Mapping

from shopify_metaobjects.transport import GraphQLResponse


class DjangoShopifyTransport:
    """Maps django_shopify AdminGraphqlResult → GraphQLResponse."""

    def __init__(self, *, shop: str):
        self.shop = shop

    def execute(
        self,
        query: str,
        variables: Mapping[str, Any] | None = None,
    ) -> GraphQLResponse:
        try:
            from django_shopify.requests import execute_admin_graphql
            from django_shopify.requests.graphql_service import (
                extract_graphql_errors_from_result,
            )
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "DjangoShopifyTransport requires django_shopify installed in the host project"
            ) from exc

        result = execute_admin_graphql(
            query,
            shop=self.shop,
            variables=dict(variables or {}),
        )
        graphql_errors = extract_graphql_errors_from_result(result)
        if not result.ok:
            return GraphQLResponse(
                data=result.data,
                graphql_errors=graphql_errors,
                retryable=bool(result.retryable),
                error_code=result.error_code,
                detail=result.log_detail or "",
            )
        return GraphQLResponse(
            data=result.data,
            graphql_errors=graphql_errors,
            retryable=False,
            error_code=None,
            detail="",
        )
