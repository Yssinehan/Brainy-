"""LLM-backed planning boundary for the agent loop."""

from __future__ import annotations

from brainy.prompts import load_prompt
from brainy.router import Message, ModelRouter
from brainy.tools.registry import ToolRegistry

from .schemas import AgentStep
from .state import AgentState


class AgentPlanner:
    def __init__(self, router: ModelRouter, registry: ToolRegistry) -> None:
        self._router = router
        self._registry = registry

    def next_step(self, state: AgentState) -> AgentStep:
        lines = [f"Goal: {state.goal}"]
        for step, observation in state.transcript:
            lines.extend((f"\nThought: {step.thought}", f"Action: {step.tool.name}({step.tool.args})" if step.tool else "", f"Observation: <observation>{observation}</observation>"))
        lines.append("\nWhat is your next step?" if state.transcript else "\nWhat is your first step?")
        system = Message(role="system", content=load_prompt("agent_system").format(tools=self._registry.prompt_listing()))
        completion = self._router.complete([system, Message(role="user", content="\n".join(lines))], schema=AgentStep)
        return completion.parsed if isinstance(completion.parsed, AgentStep) else AgentStep(thought="(unparsed model output)", final_answer=completion.text)
