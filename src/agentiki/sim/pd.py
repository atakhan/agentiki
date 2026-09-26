"""Prisoner's Dilemma choices, payoffs, and round results."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PDChoice(Enum):
    COOPERATE = "COOPERATE"
    DEFECT = "DEFECT"


@dataclass(frozen=True, slots=True)
class PayoffMatrix:
    reward: int = 3
    temptation: int = 5
    punishment: int = 1
    sucker: int = 0

    def __post_init__(self) -> None:
        if not (
            self.temptation > self.reward > self.punishment > self.sucker
        ):
            raise ValueError(
                "payoff matrix must satisfy temptation > reward > punishment > sucker"
            )

    def payoffs(self, choice_a: PDChoice, choice_b: PDChoice) -> tuple[int, int]:
        if choice_a is PDChoice.COOPERATE and choice_b is PDChoice.COOPERATE:
            return (self.reward, self.reward)
        if choice_a is PDChoice.COOPERATE and choice_b is PDChoice.DEFECT:
            return (self.sucker, self.temptation)
        if choice_a is PDChoice.DEFECT and choice_b is PDChoice.COOPERATE:
            return (self.temptation, self.sucker)
        return (self.punishment, self.punishment)


@dataclass(frozen=True, slots=True)
class PDRoundResult:
    meeting_id: int
    agent_a_id: int
    agent_b_id: int
    round_number: int
    choice_a: PDChoice
    choice_b: PDChoice
    payoff_a: int
    payoff_b: int
    tick: int
