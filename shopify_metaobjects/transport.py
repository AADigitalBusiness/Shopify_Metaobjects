"""Injectable GraphQL transport contract — no credentials in the domain layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol, runtime_checkable


@dataclass
class GraphQLResponse:
    data: dict[str, Any] | None
    graphql_errors: list[Any] = field(default_factory=list)
    retryable: bool = False
    error_code: str | None = None
    detail: str = ""

    @property
    def ok(self) -> bool:
        return not self.graphql_errors and self.data is not None


@runtime_checkable
class GraphQLTransport(Protocol):
    def execute(
        self,
        query: str,
        variables: Mapping[str, Any] | None = None,
    ) -> GraphQLResponse:
        """Execute Admin GraphQL. Must not expose tokens to callers of MetaobjectClient."""
        ...
