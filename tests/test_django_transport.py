from types import SimpleNamespace

from shopify_metaobjects.transports.django_shopify import DjangoShopifyTransport


def test_django_shopify_transport_maps_result(monkeypatch):
    calls = {}

    def fake_execute(query, *, shop, variables=None, **kwargs):
        calls["query"] = query
        calls["shop"] = shop
        calls["variables"] = variables
        return SimpleNamespace(
            ok=True,
            data={"ping": True},
            extensions=None,
            error_code=None,
            log_detail="",
            reauthorization_required=False,
            retryable=False,
            raw=None,
        )

    def fake_extract(_result):
        return []

    import sys
    import types

    graphql_service = types.ModuleType("django_shopify.requests.graphql_service")
    graphql_service.extract_graphql_errors_from_result = fake_extract
    requests_mod = types.ModuleType("django_shopify.requests")
    requests_mod.execute_admin_graphql = fake_execute
    requests_mod.graphql_service = graphql_service
    package = types.ModuleType("django_shopify")
    package.requests = requests_mod

    monkeypatch.setitem(sys.modules, "django_shopify", package)
    monkeypatch.setitem(sys.modules, "django_shopify.requests", requests_mod)
    monkeypatch.setitem(
        sys.modules, "django_shopify.requests.graphql_service", graphql_service
    )

    transport = DjangoShopifyTransport(shop="demo-shop")
    response = transport.execute("query { shop { id } }", {"a": 1})
    assert response.data == {"ping": True}
    assert calls["shop"] == "demo-shop"
    assert calls["variables"] == {"a": 1}
