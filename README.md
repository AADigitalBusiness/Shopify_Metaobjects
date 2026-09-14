# shopify-metaobjects

Reusable Shopify Metaobjects client with an injectable GraphQL transport.

## Install

```bash
pip install -e .
pip install -e ".[standalone,csv,dev]"   # optional extras
```

## Usage

### Tests (FakeTransport)

```python
from shopify_metaobjects import MetaobjectClient
from shopify_metaobjects.transport import GraphQLResponse

class FakeTransport:
    def execute(self, query, variables=None):
        return GraphQLResponse(data={"metaobjectUpsert": {"metaobject": {...}, "userErrors": []}})

client = MetaobjectClient(FakeTransport())
```

### Django (django_shopify)

```python
from shopify_metaobjects import MetaobjectClient
from shopify_metaobjects.transports.django_shopify import DjangoShopifyTransport

client = MetaobjectClient(DjangoShopifyTransport(shop="my-shop"))
result = client.upsert(
    metaobject_type="plt_editorial_article",
    handle="stable-handle",
    fields=[{"key": "title", "value": "Hello"}],
)
```

### Standalone

```python
from shopify_metaobjects import MetaobjectClient
from shopify_metaobjects.transports.standalone import StandaloneShopifyTransport

client = MetaobjectClient(
    StandaloneShopifyTransport(
        shop_domain="my-shop.myshopify.com",
        access_token="shpat_...",
    )
)
```

`upsert` always uses `metaobject: { fields: [...] }` (partial). It does not use replace-all `values`.

See `docs/architecture/transport-boundary.md` and `docs/migration/from-loader.md`.
