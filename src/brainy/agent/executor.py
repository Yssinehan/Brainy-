"""Validated, permission-gated execution boundary for agent tools."""

from __future__ import annotations

import json

from brainy.tools.registry import ToolRegistry
from brainy.tools.schemas import ToolPermission

from .schemas import AgentStep


def _parse_tool_args(raw: str) -> tuple[dict, str | None]:
    try:
        parsed = json.loads(raw) if raw and raw.strip() else {}
    except json.JSONDecodeError as exc:
        return {}, str(exc)
    if not isinstance(parsed, dict):
        return {}, "tool args must be a JSON object"
    return parsed, None


class AgentExecutor:
    def __init__(self, registry: ToolRegistry, allowed_permissions: set[ToolPermission]) -> None:
        self._registry = registry
        self._allowed_permissions = allowed_permissions

    def execute(self, step: AgentStep) -> tuple[dict, str, bool]:
        assert step.tool is not None
        parsed_args, args_error = _parse_tool_args(step.tool.args)
        if args_error is not None:
            return parsed_args, f"ERROR: invalid tool args - {args_error}", False
        result = self._registry.invoke(step.tool.name, parsed_args, self._allowed_permissions)
        return parsed_args, result.output if result.ok else f"ERROR: {result.error}", result.ok
