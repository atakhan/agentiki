"""Meetings between agents: creation, rounds, and lifecycle."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Protocol

from agentiki.sim.agents import AgentState
from agentiki.sim.interactions import Interaction
from agentiki.sim.pd import PDRoundResult, PayoffMatrix, PDChoice

if TYPE_CHECKING:
    import random

    from agentiki.sim.agents import AgentPopulation
    from agentiki.sim.config import SimulationConfig


class MeetingStatus(Enum):
    ACTIVE = "ACTIVE"
    FINISHED = "FINISHED"


class ContinueChoice(Enum):
    CONTINUE = "CONTINUE"
    LEAVE = "LEAVE"


@dataclass(slots=True)
class Meeting:
    meeting_id: int
    agent_a_id: int
    agent_b_id: int
    round_number: int
    status: MeetingStatus
    started_tick: int


@dataclass(frozen=True, slots=True)
class MeetingRoundOutcome:
    round_result: PDRoundResult
    continue_a: ContinueChoice
    continue_b: ContinueChoice
    meeting_finished: bool


class MeetingStrategy(Protocol):
    def choose_pd(
        self,
        meeting: Meeting,
        agent_id: int,
        config: SimulationConfig,
        rng: random.Random,
    ) -> PDChoice: ...

    def choose_continue(
        self,
        meeting: Meeting,
        agent_id: int,
        round_result: PDRoundResult,
        config: SimulationConfig,
        rng: random.Random,
    ) -> ContinueChoice: ...


@dataclass
class MeetingStore:
    _meetings: dict[int, Meeting] = field(default_factory=dict)
    _agent_meeting: dict[int, int] = field(default_factory=dict)
    _next_id: int = 1

    def clear(self) -> None:
        self._meetings.clear()
        self._agent_meeting.clear()
        self._next_id = 1

    def get(self, meeting_id: int) -> Meeting | None:
        return self._meetings.get(meeting_id)

    def active_meetings(self) -> list[Meeting]:
        return [
            meeting
            for meeting in self._meetings.values()
            if meeting.status is MeetingStatus.ACTIVE
        ]

    def agent_in_meeting(self, agent_id: int) -> bool:
        return agent_id in self._agent_meeting

    def busy_agents(self) -> set[int]:
        return set(self._agent_meeting)

    def create_from_interaction(
        self,
        interaction: Interaction,
        population: AgentPopulation,
        tick: int,
    ) -> Meeting | None:
        a_id = interaction.agent_a
        b_id = interaction.agent_b
        agent_a = population.get(a_id)
        agent_b = population.get(b_id)
        if agent_a is None or agent_b is None:
            return None
        if (
            agent_a.state is not AgentState.FREE
            or agent_b.state is not AgentState.FREE
            or self.agent_in_meeting(a_id)
            or self.agent_in_meeting(b_id)
        ):
            return None

        meeting = Meeting(
            meeting_id=self._next_id,
            agent_a_id=a_id,
            agent_b_id=b_id,
            round_number=1,
            status=MeetingStatus.ACTIVE,
            started_tick=tick,
        )
        self._next_id += 1
        self._meetings[meeting.meeting_id] = meeting
        self._agent_meeting[a_id] = meeting.meeting_id
        self._agent_meeting[b_id] = meeting.meeting_id
        agent_a.state = AgentState.IN_MEETING
        agent_b.state = AgentState.IN_MEETING
        agent_a.meeting_id = meeting.meeting_id
        agent_b.meeting_id = meeting.meeting_id
        return meeting

    def _release_agents(self, meeting: Meeting, population: AgentPopulation) -> None:
        for agent_id in (meeting.agent_a_id, meeting.agent_b_id):
            agent = population.get(agent_id)
            if agent is not None:
                agent.state = AgentState.FREE
                agent.meeting_id = None
            self._agent_meeting.pop(agent_id, None)

    def play_round(
        self,
        meeting: Meeting,
        population: AgentPopulation,
        payoff_matrix: PayoffMatrix,
        strategy: MeetingStrategy,
        config: SimulationConfig,
        rng: random.Random,
        tick: int,
    ) -> MeetingRoundOutcome:
        if meeting.status is MeetingStatus.ACTIVE:
            choice_a = strategy.choose_pd(meeting, meeting.agent_a_id, config, rng)
            choice_b = strategy.choose_pd(meeting, meeting.agent_b_id, config, rng)
            payoff_a, payoff_b = payoff_matrix.payoffs(choice_a, choice_b)

            agent_a = population.get(meeting.agent_a_id)
            agent_b = population.get(meeting.agent_b_id)
            if agent_a is not None:
                agent_a.score += payoff_a
            if agent_b is not None:
                agent_b.score += payoff_b

            round_result = PDRoundResult(
                meeting_id=meeting.meeting_id,
                agent_a_id=meeting.agent_a_id,
                agent_b_id=meeting.agent_b_id,
                round_number=meeting.round_number,
                choice_a=choice_a,
                choice_b=choice_b,
                payoff_a=payoff_a,
                payoff_b=payoff_b,
                tick=tick,
            )

            continue_a = strategy.choose_continue(
                meeting, meeting.agent_a_id, round_result, config, rng
            )
            continue_b = strategy.choose_continue(
                meeting, meeting.agent_b_id, round_result, config, rng
            )

            meeting_finished = not (
                continue_a is ContinueChoice.CONTINUE
                and continue_b is ContinueChoice.CONTINUE
            )
            if meeting_finished:
                meeting.status = MeetingStatus.FINISHED
                self._release_agents(meeting, population)
            else:
                meeting.round_number += 1

            return MeetingRoundOutcome(
                round_result=round_result,
                continue_a=continue_a,
                continue_b=continue_b,
                meeting_finished=meeting_finished,
            )

        raise ValueError(f"cannot play round for finished meeting {meeting.meeting_id}")


def create_meetings_from_interactions(
    interactions: tuple[Interaction, ...],
    store: MeetingStore,
    population: AgentPopulation,
    tick: int,
) -> tuple[Meeting, ...]:
    created: list[Meeting] = []
    for interaction in interactions:
        meeting = store.create_from_interaction(interaction, population, tick)
        if meeting is not None:
            created.append(meeting)
    return tuple(created)


def process_meeting_rounds(
    meetings: tuple[Meeting, ...],
    store: MeetingStore,
    population: AgentPopulation,
    payoff_matrix: PayoffMatrix,
    strategy: MeetingStrategy,
    config: SimulationConfig,
    rng: random.Random,
    tick: int,
) -> tuple[MeetingRoundOutcome, ...]:
    outcomes: list[MeetingRoundOutcome] = []
    for meeting in sorted(meetings, key=lambda item: item.meeting_id):
        if meeting.status is not MeetingStatus.ACTIVE:
            continue
        outcomes.append(
            store.play_round(
                meeting,
                population,
                payoff_matrix,
                strategy,
                config,
                rng,
                tick,
            )
        )
    return tuple(outcomes)
