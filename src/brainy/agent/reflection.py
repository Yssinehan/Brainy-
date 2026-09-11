"""Deterministic run reflection kept separate from planning and execution."""

from __future__ import annotations


class AgentReflection:
    def summarize_observation(self, observation: str) -> str:
        """Preserve the full observation for reasoning, with one testable seam for future critique."""
        return observation
