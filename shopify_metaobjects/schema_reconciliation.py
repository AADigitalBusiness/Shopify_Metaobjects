"""Declarative, fail-closed planning for Shopify metaobject definitions.

Planning is read-only. Applying requires an explicit opt-in and rejects
incompatible drift; no existing field is silently removed or retyped.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from shopify_metaobjects.definitions import fetch_definition_by_type
from shopify_metaobjects.errors import GraphQLError, TransportError, ValidationError
from shopify_metaobjects.transport import GraphQLTransport


CREATE_DEFINITION = """
mutation CreateMetaobjectDefinition($definition: MetaobjectDefinitionCreateInput!) {
  metaobjectDefinitionCreate(definition: $definition) {
    metaobjectDefinition { id type }
    userErrors { field message code }
  }
}
""".strip()

UPDATE_DEFINITION = """
mutation UpdateMetaobjectDefinition($id: ID!, $definition: MetaobjectDefinitionUpdateInput!) {
  metaobjectDefinitionUpdate(id: $id, definition: $definition) {
    metaobjectDefinition { id type }
    userErrors { field message code }
  }
}
""".strip()


@dataclass(frozen=True)
class FieldSchema:
    key: str
    type: str
    name: str | None = None
    description: str | None = None
    required: bool = False

    def __post_init__(self) -> None:
        if not self.key or not self.type:
            raise ValidationError("field key and type must be non-empty")

    def create_input(self) -> dict[str, Any]:
        value: dict[str, Any] = {
            "key": self.key,
            "name": self.name or self.key,
            "type": self.type,
            "required": self.required,
        }
        if self.description is not None:
            value["description"] = self.description
        return value


@dataclass(frozen=True)
class DefinitionSchema:
    type: str
    name: str
    fields: tuple[FieldSchema, ...]
    description: str | None = None

    def __post_init__(self) -> None:
        if not self.type or not self.name:
            raise ValidationError("definition type and name must be non-empty")
        keys = [item.key for item in self.fields]
        if len(set(keys)) != len(keys):
            raise ValidationError("duplicate definition field keys")

    def create_input(self) -> dict[str, Any]:
        value: dict[str, Any] = {
            "type": self.type,
            "name": self.name,
            "fieldDefinitions": [item.create_input() for item in self.fields],
        }
        if self.description is not None:
            value["description"] = self.description
        return value


@dataclass(frozen=True)
class DefinitionPlan:
    schema: DefinitionSchema
    action: str
    definition_id: str | None = None
    add_fields: tuple[FieldSchema, ...] = ()
    blockers: tuple[str, ...] = ()
    # Snapshot used to detect changes between planning and applying.
    remote_fields: tuple[tuple[str, str, bool], ...] = ()

    @property
    def can_apply(self) -> bool:
        return self.action in {"create", "update"} and not self.blockers


@dataclass(frozen=True)
class DefinitionApplyResult:
    ok: bool
    action: str
    definition_id: str | None = None
    user_errors: tuple[dict[str, Any], ...] = ()
    detail: str = ""


def _remote_field_signature(remote: Mapping[str, Any]) -> tuple[tuple[str, str, bool], ...]:
    fields = remote.get("fieldDefinitions") or []
    return tuple(sorted(
        (str(f["key"]), str((f.get("type") or {}).get("name") or ""), bool(f.get("required")))
        for f in fields
    ))


def plan_definition(schema: DefinitionSchema, remote: Mapping[str, Any] | None) -> DefinitionPlan:
    """Return create/update/noop/blocked without modifying Shopify."""
    if remote is None:
        return DefinitionPlan(schema=schema, action="create")
    remote_id = remote.get("id")
    if not remote_id:
        return DefinitionPlan(schema=schema, action="blocked", blockers=("remote definition lacks id",))

    current = {key: (kind, required) for key, kind, required in _remote_field_signature(remote)}
    desired = {f.key: f for f in schema.fields}
    blockers: list[str] = []
    for key, (kind, required) in current.items():
        if key not in desired:
            blockers.append(f"remote field {key!r} would be removed")
        elif desired[key].type != kind or desired[key].required != required:
            blockers.append(f"remote field {key!r} type/required differs")

    additions = tuple(f for f in schema.fields if f.key not in current)
    if remote.get("type") != schema.type:
        blockers.append("remote definition type mismatch")
    # Name/description changes are deliberately outside this additive-only contract.
    if remote.get("name") != schema.name:
        blockers.append("remote definition name differs")
    if schema.description is not None and remote.get("description") != schema.description:
        blockers.append("remote definition description differs")

    action = "blocked" if blockers else ("update" if additions else "noop")
    return DefinitionPlan(
        schema=schema, action=action, definition_id=str(remote_id),
        add_fields=additions, blockers=tuple(blockers),
        remote_fields=_remote_field_signature(remote),
    )


class DefinitionReconciler:
    def __init__(self, transport: GraphQLTransport):
        self.transport = transport

    def plan(self, schema: DefinitionSchema) -> DefinitionPlan:
        return plan_definition(schema, fetch_definition_by_type(self.transport, schema.type))

    def apply(self, plan: DefinitionPlan, *, confirm: bool = False) -> DefinitionApplyResult:
        if not confirm:
            raise ValidationError("definition writes require confirm=True")
        if plan.action == "noop":
            return DefinitionApplyResult(ok=True, action="noop", definition_id=plan.definition_id)
        if not plan.can_apply:
            raise ValidationError(f"unsafe definition plan: {plan.blockers or plan.action}")
        # Re-read immediately before writing to fail closed against concurrent changes.
        fresh = self.plan(plan.schema)
        if fresh != plan:
            raise ValidationError("definition changed since planning; create a fresh plan")

        if plan.action == "create":
            query = CREATE_DEFINITION
            variables = {"definition": plan.schema.create_input()}
            payload_key = "metaobjectDefinitionCreate"
        else:
            query = UPDATE_DEFINITION
            variables = {
                "id": plan.definition_id,
                "definition": {
                    "fieldDefinitions": [
                        {"create": item.create_input()} for item in plan.add_fields
                    ]
                },
            }
            payload_key = "metaobjectDefinitionUpdate"
        response = self.transport.execute(query, variables)
        if response.graphql_errors:
            raise GraphQLError(
                response.detail or "definition mutation failed",
                errors=list(response.graphql_errors),
                retryable=response.retryable,
                error_code=response.error_code,
            )
        if response.data is None:
            raise TransportError(
                response.detail or "definition mutation returned no data",
                retryable=response.retryable,
                error_code=response.error_code,
            )
        payload = response.data.get(payload_key) or {}
        user_errors = tuple(payload.get("userErrors") or ())
        if user_errors:
            return DefinitionApplyResult(
                ok=False, action=plan.action, user_errors=user_errors,
                detail="Shopify rejected definition mutation",
            )
        definition = payload.get("metaobjectDefinition") or {}
        definition_id = definition.get("id")
        if not definition_id:
            return DefinitionApplyResult(
                ok=False, action=plan.action,
                detail="Shopify returned no definition id",
            )
        return DefinitionApplyResult(
            ok=True, action=plan.action, definition_id=str(definition_id)
        )
