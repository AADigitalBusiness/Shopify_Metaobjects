"""Backward-compatible module path for the legacy monolithic loader.

Prefer::

    from shopify_metaobjects import MetaobjectClient
"""

from shopify_metaobjects.loader import ShopifyMetaobjectLoader
from shopify_metaobjects.models import Metaobject

__all__ = ["ShopifyMetaobjectLoader", "Metaobject"]
