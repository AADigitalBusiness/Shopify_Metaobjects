import warnings

from shopify_metaobjects.loader import ShopifyMetaobjectLoader


def test_deprecated_loader_warns(monkeypatch):
    class StubTransport:
        def execute(self, query, variables=None):
            from shopify_metaobjects.transport import GraphQLResponse

            return GraphQLResponse(
                data={
                    "metaobjectUpsert": {
                        "metaobject": {
                            "id": "gid://shopify/Metaobject/1",
                            "handle": "h",
                            "type": "t",
                            "fields": [],
                        },
                        "userErrors": [],
                    }
                }
            )

    monkeypatch.setattr(
        "shopify_metaobjects.transports.standalone.StandaloneShopifyTransport",
        lambda **kwargs: StubTransport(),
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        loader = ShopifyMetaobjectLoader("shop.myshopify.com", "tok")
        assert any(issubclass(w.category, DeprecationWarning) for w in caught)
    from shopify_metaobjects.models import Metaobject

    mo = loader.upsert_metaobject(Metaobject(type="t", handle="h", fields={"a": "1"}))
    assert mo is not None
