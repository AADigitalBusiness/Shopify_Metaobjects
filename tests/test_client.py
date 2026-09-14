"""Fake transport and unit tests for MetaobjectClient."""

from __future__ import annotations

from typing import Any, Mapping

import pytest

from shopify_metaobjects import MetaobjectClient, Metaobject
from shopify_metaobjects.operations import UPSERT_MUTATION
from shopify_metaobjects.transport import GraphQLResponse


class FakeTransport:
    def __init__(self, responses: list[GraphQLResponse] | None = None):
        self.calls: list[tuple[str, Mapping[str, Any] | None]] = []
        self._responses = list(responses or [])

    def execute(self, query: str, variables: Mapping[str, Any] | None = None) -> GraphQLResponse:
        self.calls.append((query, variables))
        if self._responses:
            return self._responses.pop(0)
        return GraphQLResponse(data={})


def test_client_requires_transport():
    transport = FakeTransport()
    client = MetaobjectClient(transport)
    assert client is not None


def test_upsert_builds_type_handle_and_fields_not_values():
    transport = FakeTransport(
        [
            GraphQLResponse(
                data={
                    "metaobjectUpsert": {
                        "metaobject": {
                            "id": "gid://shopify/Metaobject/1",
                            "handle": "article-abc",
                            "type": "plt_editorial_article",
                            "fields": [{"key": "title", "value": "Hello"}],
                        },
                        "userErrors": [],
                    }
                }
            )
        ]
    )
    client = MetaobjectClient(transport)
    result = client.upsert(
        metaobject_type="plt_editorial_article",
        handle="article-abc",
        fields=[{"key": "title", "value": "Hello"}, {"key": "body_markdown", "value": "# Hi"}],
    )
    assert result.ok
    assert result.gid == "gid://shopify/Metaobject/1"
    assert len(transport.calls) == 1
    query, variables = transport.calls[0]
    assert "metaobjectUpsert" in query
    assert query.strip() == UPSERT_MUTATION or "metaobject: $metaobject" in query
    assert "values" not in query.lower().split("metaobjectupsert")[0]  # mutation uses fields
    assert variables["handle"] == {"type": "plt_editorial_article", "handle": "article-abc"}
    assert "fields" in variables["metaobject"]
    assert "values" not in variables["metaobject"]
    assert variables["metaobject"]["fields"][0]["key"] == "title"


def test_upsert_user_errors_are_structured_not_raised():
    transport = FakeTransport(
        [
            GraphQLResponse(
                data={
                    "metaobjectUpsert": {
                        "metaobject": None,
                        "userErrors": [{"field": ["handle"], "message": "taken", "code": "TAKEN"}],
                    }
                }
            )
        ]
    )
    client = MetaobjectClient(transport)
    result = client.upsert(
        metaobject_type="plt_editorial_article",
        handle="x",
        fields={"title": "t"},
    )
    assert result.ok is False
    assert result.retryable is False
    assert result.user_errors
    assert result.error_code == "metaobject_user_errors"


def test_upsert_missing_metaobject_id_is_failure():
    transport = FakeTransport(
        [
            GraphQLResponse(
                data={
                    "metaobjectUpsert": {
                        "metaobject": None,
                        "userErrors": [],
                    }
                }
            )
        ]
    )
    client = MetaobjectClient(transport)
    result = client.upsert(
        metaobject_type="plt_editorial_article",
        handle="x",
        fields={"title": "t"},
    )
    assert result.ok is False
    assert result.gid is None
    assert result.error_code == "missing_metaobject_result"
    assert result.retryable is False


def test_upsert_metaobject_without_id_is_failure():
    transport = FakeTransport(
        [
            GraphQLResponse(
                data={
                    "metaobjectUpsert": {
                        "metaobject": {
                            "handle": "x",
                            "type": "plt_editorial_article",
                            "fields": [],
                        },
                        "userErrors": [],
                    }
                }
            )
        ]
    )
    client = MetaobjectClient(transport)
    result = client.upsert(
        metaobject_type="plt_editorial_article",
        handle="x",
        fields={"title": "t"},
    )
    assert result.ok is False
    assert result.error_code == "missing_metaobject_result"


def test_upsert_propagates_retryable_transport_failure():
    transport = FakeTransport(
        [
            GraphQLResponse(
                data=None,
                retryable=True,
                error_code="network_error",
                detail="timeout",
            )
        ]
    )
    client = MetaobjectClient(transport)
    result = client.upsert(
        metaobject_type="plt_editorial_article",
        handle="x",
        fields={"title": "t"},
    )
    assert result.ok is False
    assert result.retryable is True
    assert result.error_code == "network_error"


def test_upsert_top_level_graphql_errors():
    transport = FakeTransport(
        [
            GraphQLResponse(
                data=None,
                graphql_errors=[{"message": "boom"}],
                retryable=False,
                error_code="graphql_error",
                detail="boom",
            )
        ]
    )
    client = MetaobjectClient(transport)
    result = client.upsert(
        metaobject_type="plt_editorial_article",
        handle="x",
        fields={"title": "t"},
    )
    assert result.ok is False
    assert result.error_code == "graphql_error"


def test_get_by_handle():
    transport = FakeTransport(
        [
            GraphQLResponse(
                data={
                    "metaobject": {
                        "id": "gid://shopify/Metaobject/9",
                        "handle": "h",
                        "type": "plt_editorial_article",
                        "fields": [],
                    }
                }
            )
        ]
    )
    client = MetaobjectClient(transport)
    mo = client.get_by_handle(metaobject_type="plt_editorial_article", handle="h")
    assert isinstance(mo, Metaobject)
    assert mo.id.endswith("/9")


def test_core_does_not_import_requests():
    import shopify_metaobjects.client as client_mod
    import shopify_metaobjects.operations as ops_mod
    import shopify_metaobjects.models as models_mod
    import shopify_metaobjects.transport as transport_mod

    for mod in (client_mod, ops_mod, models_mod, transport_mod):
        assert "requests" not in dir(mod)
        source = open(mod.__file__, encoding="utf-8").read()
        assert "import requests" not in source
        assert "from requests" not in source


def test_client_does_not_fetch_access_token():
    transport = FakeTransport(
        [
            GraphQLResponse(
                data={
                    "metaobjectUpsert": {
                        "metaobject": {
                            "id": "gid://shopify/Metaobject/2",
                            "handle": "h",
                            "type": "t",
                            "fields": [],
                        },
                        "userErrors": [],
                    }
                }
            )
        ]
    )
    client = MetaobjectClient(transport)
    client.upsert(metaobject_type="t", handle="h", fields={"a": "1"})
    # Transport never received credentials — only query/variables.
    _, variables = transport.calls[0]
    assert "access_token" not in str(variables)


def test_validate_fields():
    from shopify_metaobjects.errors import ValidationError

    transport = FakeTransport()
    client = MetaobjectClient(transport)
    with pytest.raises(ValidationError):
        client.validate_fields({"title": "x"}, required_keys=["body_markdown"])


def test_batch_upsert_rows_use_same_client():
    from shopify_metaobjects.import_export import upsert_rows

    transport = FakeTransport(
        [
            GraphQLResponse(
                data={
                    "metaobjectUpsert": {
                        "metaobject": {
                            "id": "gid://shopify/Metaobject/1",
                            "handle": "a",
                            "type": "t",
                            "fields": [],
                        },
                        "userErrors": [],
                    }
                }
            ),
            GraphQLResponse(
                data={
                    "metaobjectUpsert": {
                        "metaobject": {
                            "id": "gid://shopify/Metaobject/2",
                            "handle": "b",
                            "type": "t",
                            "fields": [],
                        },
                        "userErrors": [],
                    }
                }
            ),
        ]
    )
    client = MetaobjectClient(transport)
    stats = upsert_rows(
        client,
        metaobject_type="t",
        rows=[{"handle": "a", "title": "A"}, {"handle": "b", "title": "B"}],
    )
    assert stats == {"upserted": 2, "failed": 0}
    assert len(transport.calls) == 2
