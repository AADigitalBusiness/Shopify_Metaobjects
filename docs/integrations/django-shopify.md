# Integration: django_shopify

```python
from shopify_metaobjects import MetaobjectClient
from shopify_metaobjects.transports.django_shopify import DjangoShopifyTransport

client = MetaobjectClient(DjangoShopifyTransport(shop="my-shop"))
result = client.upsert(
    metaobject_type="plt_editorial_article",
    handle="article_abc",
    fields=[{"key": "title", "value": "Hello"}],
)
```

Requires the host project to install `django_shopify` (e.g. editable `django-shopify-app-start-template`) and configure `SHOPIFY_*` / `ShopConfig`. The adapter does not store tokens.
