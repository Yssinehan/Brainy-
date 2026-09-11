"""Durable-in-memory state for one bounded agent run."""

from __future__ import annotations

from dataclasses import dataclass, field

from .schemas import AgentStep, StepRecord


@dataclass
class AgentState:
    goal: str
    transcript: list[tuple[AgentStep, str]] = field(default_factory=list)
    records: list[StepRecord] = field(default_factory=list)
