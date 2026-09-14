"""Shopify Metaobjects — injectable-transport client library."""

from shopify_metaobjects.client import MetaobjectClient
from shopify_metaobjects.errors import (
    GraphQLError,
    MetaobjectUserError,
    ShopifyMetaobjectsError,
    TransportError,
    ValidationError,
)
from shopify_metaobjects.loader import ShopifyMetaobjectLoader
from shopify_metaobjects.models import Metaobject, MetaobjectUpsertResult
from shopify_metaobjects.transport import GraphQLResponse, GraphQLTransport

__all__ = [
    "MetaobjectClient",
    "Metaobject",
    "MetaobjectUpsertResult",
    "GraphQLTransport",
    "GraphQLResponse",
    "ShopifyMetaobjectsError",
    "TransportError",
    "GraphQLError",
    "MetaobjectUserError",
    "ValidationError",
    "ShopifyMetaobjectLoader",
]

__version__ = "0.2.0"
