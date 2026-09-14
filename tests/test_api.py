"""api.py no longer owns HTTP; standalone transport does."""

from shopify_metaobjects.api import make_graphql_request
import pytest


def test_legacy_make_graphql_request_removed():
    with pytest.raises(RuntimeError):
        make_graphql_request("https://example", {}, "query", {})
