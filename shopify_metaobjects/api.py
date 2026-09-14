"""Deprecated module path. Prefer shopify_metaobjects.transports.standalone."""

from shopify_metaobjects.transports.standalone import StandaloneShopifyTransport


def make_graphql_request(base_url, headers, query, variables):
    raise RuntimeError(
        "make_graphql_request is removed from the core API. "
        "Use MetaobjectClient with StandaloneShopifyTransport or DjangoShopifyTransport."
    )


__all__ = ["StandaloneShopifyTransport", "make_graphql_request"]
