# Declarative Metaobject Definition Reconciliation

This API adopts the schema-as-code and migration-planning pattern without
depending on the experimental TypeScript `shopify-orm` package.

It extends the existing injected `GraphQLTransport`. No Shopify credentials,
Django models, or production writes are required to calculate a plan.

```python
from shopify_metaobjects import (
    DefinitionReconciler, DefinitionSchema, FieldSchema,
)

schema = DefinitionSchema(
    type="glossary_term",
    name="Glossary term",
    fields=(
        FieldSchema("title", "single_line_text_field", required=True),
        FieldSchema("definition", "multi_line_text_field"),
    ),
)

reconciler = DefinitionReconciler(existing_transport)
plan = reconciler.plan(schema)  # read-only: create / update / noop / blocked
print(plan.action, plan.blockers, plan.add_fields)

# Only after a human or an explicitly authorized workflow approves the plan:
if plan.can_apply:
    result = reconciler.apply(plan, confirm=True)
    assert result.ok, (result.user_errors, result.detail)
```

## Safety contract

- `plan()` only queries `metaobjectDefinitionByType`.
- `apply()` requires `confirm=True`; it never runs implicitly.
- The planner only supports creation or adding fields to existing definitions.
- Existing fields cannot be removed, retyped, or have their required flag changed.
- Definition name/description drift is reported as a blocker, not overwritten.
- A fresh definition read immediately before mutation detects concurrent drift.
- Shopify GraphQL errors and mutation `userErrors` do not count as success.
- An empty/missing mutation response is not considered successful.
- No editorial content is published and existing metaobjects are not modified.
- For destructive or non-additive migrations, create a separate, reviewed migration.
- A plan should be approved independently from the permission to execute it.
- Shopify remains the authoritative remote schema; this library provides inspection
  and explicitly approved additive reconciliation, not background synchronization.

## Current scope

Definition creation and additive field creation only. Capabilities, access policies,
validations and field updates are intentionally not reconciled. Before using this
with a real shop, validate the input against its pinned Admin GraphQL API version.

Run `pytest tests/test_schema_reconciliation.py` locally.
