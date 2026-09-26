"""Simulation step outcomes."""

from __future__ import annotations

from dataclasses import dataclass

from agentiki.sim.interactions import Interaction
from agentiki.sim.meetings import Meeting, MeetingRoundOutcome
from agentiki.sim.pd import PDRoundResult


@dataclass(frozen=True, slots=True)
class StepResult:
    tick: int
    interactions: tuple[Interaction, ...]
    meetings_started: tuple[Meeting, ...] = ()
    pd_rounds: tuple[PDRoundResult, ...] = ()
    meeting_outcomes: tuple[MeetingRoundOutcome, ...] = ()
