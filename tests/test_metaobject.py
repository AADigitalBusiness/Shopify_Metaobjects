from shopify_metaobjects.models import Metaobject


def test_metaobject_roundtrip_fields():
    mo = Metaobject(type="t", handle="h", fields={"title": "Hello"})
    assert mo.to_shopify_fields() == [{"key": "title", "value": "Hello"}]
    restored = Metaobject.from_shopify_data(
        {
            "id": "gid://shopify/Metaobject/1",
            "type": "t",
            "handle": "h",
            "fields": [{"key": "title", "value": "Hello"}],
        }
    )
    assert restored.id.endswith("/1")
    assert restored.fields["title"] == "Hello"
