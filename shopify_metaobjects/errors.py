"""Shopify Metaobjects errors."""

from __future__ import annotations


class ShopifyMetaobjectsError(Exception):
    """Base error for the package."""


class TransportError(ShopifyMetaobjectsError):
    """Transport / HTTP / connectivity failure."""

    def __init__(self, message: str, *, retryable: bool = False, error_code: str | None = None):
        super().__init__(message)
        self.retryable = retryable
        self.error_code = error_code


class GraphQLError(ShopifyMetaobjectsError):
    """Top-level GraphQL errors payload."""

    def __init__(
        self,
        message: str,
        *,
        errors: list | None = None,
        retryable: bool = False,
        error_code: str | None = None,
    ):
        super().__init__(message)
        self.errors = errors or []
        self.retryable = retryable
        self.error_code = error_code


class MetaobjectUserError(ShopifyMetaobjectsError):
    """Raised only when a caller opts into exception mode for userErrors."""

    def __init__(self, message: str, *, user_errors: list | None = None):
        super().__init__(message)
        self.user_errors = user_errors or []


class ValidationError(ShopifyMetaobjectsError):
    """Domain validation against a metaobject definition."""
