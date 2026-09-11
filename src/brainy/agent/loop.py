"""Plan-act-reflect loop (docs/TDD.md Agent Framework). One base Agent; specialized
agents are just different registries/permissions/prompts, not new code (docs/PRD.md)."""

from __future__ import annotations

from brainy.memory.store import MemoryStore
from brainy.router import ModelRouter
from brainy.tools.registry import ToolRegistry
from brainy.tools.schemas import ToolPermission

from .executor import AgentExecutor
from .planner import AgentPlanner
from .reflection import AgentReflection
from .schemas import AgentResult, AgentStep, StepRecord
from .state import AgentState

import json


def _parse_tool_args(raw: str) -> tuple[dict, str | None]:
    try:
        parsed = json.loads(raw) if raw and raw.strip() else {}
    except json.JSONDecodeError as exc:
        return {}, str(exc)
    if not isinstance(parsed, dict):
        return {}, "tool args must be a JSON object"
    return parsed, None

DEFAULT_MAX_STEPS = 6
DEFAULT_ALLOWED_PERMISSIONS: frozenset[ToolPermission] = frozenset({"read_only"})


class Agent:
    def __init__(
        self,
        router: ModelRouter,
        registry: ToolRegistry,
        store: MemoryStore,
        allowed_permissions: set[ToolPermission] | frozenset[ToolPermission] = DEFAULT_ALLOWED_PERMISSIONS,
        max_steps: int = DEFAULT_MAX_STEPS,
    ) -> None:
        self._router = router
        self._registry = registry
        self._store = store
        self._allowed_permissions = set(allowed_permissions)
        self._max_steps = max_steps

    def run(self, goal: str) -> AgentResult:
        state = AgentState(goal=goal)
        planner = AgentPlanner(self._router, self._registry)
        executor = AgentExecutor(self._registry, self._allowed_permissions)
        reflection = AgentReflection()

        for _ in range(self._max_steps):
            step = planner.next_step(state)

            if step.tool is None:
                final = step.final_answer or "Done."
                state.records.append(StepRecord(thought=step.thought))
                self._store.log("agent", "final_answer", {"goal": goal, "answer": final})
                return AgentResult(goal=goal, final_answer=final, steps=state.records, succeeded=True)

            parsed_args, observation, tool_ok = executor.execute(step)
            observation = reflection.summarize_observation(observation)

            self._store.log(
                "agent",
                "tool_call",
                {"goal": goal, "tool": step.tool.name, "args": parsed_args, "ok": tool_ok},
            )
            state.records.append(
                StepRecord(
                    thought=step.thought,
                    tool_name=step.tool.name,
                    tool_args=parsed_args,
                    observation=observation,
                )
            )
            state.transcript.append((step, observation))

        self._store.log("agent", "max_steps_exceeded", {"goal": goal, "steps": self._max_steps})
        return AgentResult(
            goal=goal,
            final_answer=f"I couldn't finish within {self._max_steps} steps. Try narrowing the goal.",
            steps=state.records,
            succeeded=False,
        )
