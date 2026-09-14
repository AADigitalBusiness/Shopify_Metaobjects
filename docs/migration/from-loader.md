# Migration from ShopifyMetaobjectLoader

```python
# Before
from shopify_metaobject_loader import ShopifyMetaobjectLoader
loader = ShopifyMetaobjectLoader(shop_domain=..., access_token=...)
loader.process_csv("file.csv", "my_type")

# After (standalone)
from shopify_metaobjects import MetaobjectClient
from shopify_metaobjects.transports.standalone import StandaloneShopifyTransport
from shopify_metaobjects.import_export import process_csv

client = MetaobjectClient(
    StandaloneShopifyTransport(shop_domain=..., access_token=...)
)
process_csv(client, file_path="file.csv", metaobject_type="my_type")

# After (Django)
from shopify_metaobjects import MetaobjectClient
from shopify_metaobjects.transports.django_shopify import DjangoShopifyTransport

client = MetaobjectClient(DjangoShopifyTransport(shop="my-shop"))
client.upsert(metaobject_type="t", handle="h", fields={"title": "x"})
```

`ShopifyMetaobjectLoader` remains as a deprecated facade emitting `DeprecationWarning`.
