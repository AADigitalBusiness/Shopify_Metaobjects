"""Deprecated compatibility facade for ShopifyMetaobjectLoader."""

from __future__ import annotations

import warnings
from typing import Any

from shopify_metaobjects.client import MetaobjectClient
from shopify_metaobjects.models import Metaobject


class ShopifyMetaobjectLoader:
    """Deprecated: prefer MetaobjectClient(transport=...).

    This facade uses StandaloneShopifyTransport and delegates upsert/fetch.
    """

    def __init__(
        self,
        shop_domain: str,
        access_token: str,
        api_version: str = "2025-04",
        cache_dir: str | None = None,
    ) -> None:
        warnings.warn(
            "ShopifyMetaobjectLoader is deprecated; use MetaobjectClient with an "
            "explicit GraphQLTransport (StandaloneShopifyTransport or DjangoShopifyTransport).",
            DeprecationWarning,
            stacklevel=2,
        )
        from shopify_metaobjects.transports.standalone import StandaloneShopifyTransport

        self.shop_domain = shop_domain
        self.access_token = access_token
        self.api_version = api_version
        self.cache_dir = cache_dir
        self._client = MetaobjectClient(
            StandaloneShopifyTransport(
                shop_domain=shop_domain,
                access_token=access_token,
                api_version=api_version,
            )
        )

    def upsert_metaobject(self, metaobject: Metaobject) -> Metaobject | None:
        result = self._client.upsert(
            metaobject_type=metaobject.type,
            handle=metaobject.handle,
            fields=metaobject.fields,
        )
        return result.metaobject if result.ok else None

    def fetch_metaobject_by_handle(self, handle: str, metaobject_type: str) -> Metaobject | None:
        return self._client.get_by_handle(metaobject_type=metaobject_type, handle=handle)

    def process_csv(self, file_path: str, metaobject_type: str) -> dict[str, int]:
        from shopify_metaobjects.import_export import process_csv

        return process_csv(
            self._client,
            file_path=file_path,
            metaobject_type=metaobject_type,
        )

    def fetch_definition(self, metaobject_type: str) -> dict[str, Any] | None:
        return self._client.fetch_definition(metaobject_type)
