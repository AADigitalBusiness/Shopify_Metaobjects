"""No live Shopify calls: definition planning and mutation contract tests."""

import pytest

from shopify_metaobjects.errors import GraphQLError, ValidationError
from shopify_metaobjects.schema_reconciliation import (
    DefinitionReconciler,
    DefinitionSchema,
    FieldSchema,
    plan_definition,
)
from shopify_metaobjects.transport import GraphQLResponse


SCHEMA = DefinitionSchema(
    type="glossary_term",
    name="Glossary term",
    fields=(
        FieldSchema("title", "single_line_text_field", required=True),
        FieldSchema("definition", "multi_line_text_field"),
    ),
)


def remote(fields=None):
    return {
        "id": "gid://shopify/MetaobjectDefinition/1",
        "type": SCHEMA.type,
        "name": SCHEMA.name,
        "description": None,
        "fieldDefinitions": fields or [
            {"key": "title", "type": {"name": "single_line_text_field"}, "required": True}
        ],
    }


class FakeTransport:
    def __init__(self, definition=None, mutation=None):
        self.definition = definition
        self.mutation = mutation
        self.calls = []

    def execute(self, query, variables=None):
        self.calls.append((query, variables))
        if "MetaobjectDefinitionByType" in query:
            return GraphQLResponse(data={"metaobjectDefinitionByType": self.definition})
        return self.mutation or GraphQLResponse(data={
            "metaobjectDefinitionUpdate": {
                "metaobjectDefinition": {"id": "gid://shopify/MetaobjectDefinition/1"},
                "userErrors": [],
            }
        })


def test_create_plan_is_read_only():
    transport = FakeTransport()
    plan = DefinitionReconciler(transport).plan(SCHEMA)
    assert plan.action == "create"
    assert len(transport.calls) == 1
    assert "query" in transport.calls[0][0]


def test_additive_update_only():
    plan = plan_definition(SCHEMA, remote())
    assert plan.action == "update"
    assert [field.key for field in plan.add_fields] == ["definition"]


def test_unchanged_schema_is_noop():
    fields = remote()["fieldDefinitions"] + [
        {"key": "definition", "type": {"name": "multi_line_text_field"}, "required": False}
    ]
    assert plan_definition(SCHEMA, remote(fields)).action == "noop"


@pytest.mark.parametrize("fields", [
    [{"key": "title", "type": {"name": "number_integer"}, "required": True}],
    [{"key": "title", "type": {"name": "single_line_text_field"}, "required": False}],
    remote()["fieldDefinitions"] + [
        {"key": "legacy", "type": {"name": "single_line_text_field"}, "required": False}
    ],
])
def test_incompatible_drift_is_blocked(fields):
    plan = plan_definition(SCHEMA, remote(fields))
    assert plan.action == "blocked"
    assert plan.blockers


def test_duplicate_keys_rejected():
    with pytest.raises(ValidationError):
        DefinitionSchema("example", "Example", (FieldSchema("a", "json"), FieldSchema("a", "json")))


def test_apply_requires_explicit_confirmation():
    transport = FakeTransport(remote())
    reconciler = DefinitionReconciler(transport)
    plan = reconciler.plan(SCHEMA)
    with pytest.raises(ValidationError):
        reconciler.apply(plan)
    assert len(transport.calls) == 1


def test_apply_rechecks_drift_and_fails_closed():
    transport = FakeTransport(remote())
    reconciler = DefinitionReconciler(transport)
    plan = reconciler.plan(SCHEMA)
    transport.definition = remote(remote()["fieldDefinitions"] + [
        {"key": "other", "type": {"name": "json"}, "required": False}
    ])
    with pytest.raises(ValidationError, match="changed since planning"):
        reconciler.apply(plan, confirm=True)
    assert len(transport.calls) == 2


def test_update_uses_field_create_only():
    transport = FakeTransport(remote())
    reconciler = DefinitionReconciler(transport)
    plan = reconciler.plan(SCHEMA)
    result = reconciler.apply(plan, confirm=True)
    assert result.ok
    mutation, variables = transport.calls[-1]
    assert "metaobjectDefinitionUpdate" in mutation
    assert variables["definition"] == {
        "fieldDefinitions": [{"create": SCHEMA.fields[1].create_input()}]
    }


def test_user_errors_are_not_reported_as_success():
    transport = FakeTransport(
        remote(),
        GraphQLResponse(data={
            "metaobjectDefinitionUpdate": {
                "metaobjectDefinition": None,
                "userErrors": [{"message": "Denied", "code": "ACCESS_DENIED"}],
            }
        }),
    )
    reconciler = DefinitionReconciler(transport)
    assert not reconciler.apply(reconciler.plan(SCHEMA), confirm=True).ok


def test_graphql_errors_fail_closed():
    transport = FakeTransport(
        remote(),
        GraphQLResponse(data=None, graphql_errors=[{"message": "Failure"}]),
    )
    reconciler = DefinitionReconciler(transport)
    with pytest.raises(GraphQLError):
        reconciler.apply(reconciler.plan(SCHEMA), confirm=True)
