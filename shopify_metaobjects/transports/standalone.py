"""Standalone HTTP transport using requests. Not imported by the domain core."""

from __future__ import annotations

from typing import Any, Mapping

from shopify_metaobjects.transport import GraphQLResponse

try:
    import requests
    from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "StandaloneShopifyTransport requires: pip install 'shopify-metaobjects[standalone]'"
    ) from exc


class StandaloneShopifyTransport:
    """Direct Admin GraphQL transport with explicit credentials (non-Django)."""

    def __init__(
        self,
        *,
        shop_domain: str,
        access_token: str,
        api_version: str = "2025-04",
    ):
        shop = shop_domain.strip().replace("https://", "").replace("http://", "").split("/")[0]
        self.shop_domain = shop
        self.access_token = access_token
        self.api_version = api_version
        self.base_url = f"https://{shop}/admin/api/{api_version}/graphql.json"
        self.headers = {
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json",
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(requests.RequestException),
        reraise=True,
    )
    def _post(self, query: str, variables: Mapping[str, Any] | None) -> dict[str, Any]:
        response = requests.post(
            self.base_url,
            json={"query": query, "variables": dict(variables or {})},
            headers=self.headers,
            timeout=60,
        )
        if response.status_code == 429:
            return {
                "_transport_error": True,
                "retryable": True,
                "error_code": "rate_limited",
                "detail": "Shopify API rate limit exceeded",
            }
        response.raise_for_status()
        return response.json()

    def execute(
        self,
        query: str,
        variables: Mapping[str, Any] | None = None,
    ) -> GraphQLResponse:
        try:
            payload = self._post(query, variables)
        except requests.RequestException as exc:
            return GraphQLResponse(
                data=None,
                graphql_errors=[],
                retryable=True,
                error_code="network_error",
                detail=str(exc),
            )

        if payload.get("_transport_error"):
            return GraphQLResponse(
                data=None,
                retryable=bool(payload.get("retryable")),
                error_code=payload.get("error_code"),
                detail=str(payload.get("detail") or ""),
            )

        errors = payload.get("errors") or []
        return GraphQLResponse(
            data=payload.get("data"),
            graphql_errors=list(errors),
            retryable=False,
            error_code="graphql_error" if errors else None,
            detail=str(errors) if errors else "",
        )
