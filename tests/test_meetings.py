from __future__ import annotations

import random
import unittest

from agentiki.sim.actions import InteractAction, MoveAction, MoveDirection
from agentiki.sim.agents import Agent, AgentPopulation, AgentState
from agentiki.sim.config import SimulationConfig
from agentiki.sim.meetings import ContinueChoice, MeetingStatus, MeetingStore
from agentiki.sim.pd import PDChoice, PayoffMatrix
from agentiki.sim.tick import step_tick


def _pop_with_agents(*cells: tuple[int, tuple[int, int]]) -> AgentPopulation:
    pop = AgentPopulation()
    for agent_id, (x, y) in cells:
        pop.place(Agent(id=agent_id, cell_x=x, cell_y=y))
    return pop


class ScriptedStrategy:
    def __init__(
        self,
        world_actions: dict[int, InteractAction | MoveAction] | None = None,
        pd_choices: dict[int, PDChoice] | None = None,
        continue_choices: dict[int, ContinueChoice] | None = None,
    ) -> None:
        self._world_actions = world_actions or {}
        self._pd_choices = pd_choices or {}
        self._continue_choices = continue_choices or {}

    def choose(self, observation, config, rng):
        return self._world_actions[observation.observer_id]

    def choose_pd(self, meeting, agent_id, config, rng):
        return self._pd_choices.get(agent_id, PDChoice.COOPERATE)

    def choose_continue(self, meeting, agent_id, round_result, config, rng):
        return self._continue_choices.get(agent_id, ContinueChoice.LEAVE)


class PayoffMatrixTests(unittest.TestCase):
    def test_default_payoffs(self) -> None:
        matrix = PayoffMatrix()
        self.assertEqual(matrix.payoffs(PDChoice.COOPERATE, PDChoice.COOPERATE), (3, 3))
        self.assertEqual(matrix.payoffs(PDChoice.COOPERATE, PDChoice.DEFECT), (0, 5))
        self.assertEqual(matrix.payoffs(PDChoice.DEFECT, PDChoice.COOPERATE), (5, 0))
        self.assertEqual(matrix.payoffs(PDChoice.DEFECT, PDChoice.DEFECT), (1, 1))

    def test_invalid_matrix_rejected(self) -> None:
        with self.assertRaises(ValueError):
            PayoffMatrix(reward=5, temptation=3, punishment=1, sucker=0)


class MeetingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = SimulationConfig(vision_radius=3, interaction_radius=1)
        self.store = MeetingStore()

    def test_interaction_creates_meeting(self) -> None:
        pop = _pop_with_agents((1, (0, 0)), (2, (1, 0)))
        result = step_tick(
            pop,
            self.config,
            ScriptedStrategy(
                world_actions={
                    1: InteractAction(2),
                    2: MoveAction(MoveDirection.STAY),
                },
                continue_choices={1: ContinueChoice.LEAVE, 2: ContinueChoice.LEAVE},
            ),
            tick=0,
            rng=random.Random(0),
            meeting_store=self.store,
        )
        self.assertEqual(len(result.meetings_started), 1)
        meeting = result.meetings_started[0]
        self.assertEqual(meeting.agent_a_id, 1)
        self.assertEqual(meeting.agent_b_id, 2)
        self.assertEqual(meeting.round_number, 1)
        self.assertEqual(len(result.pd_rounds), 1)
        self.assertEqual(meeting.status, MeetingStatus.FINISHED)
        self.assertEqual(pop.get(1).state, AgentState.FREE)
        self.assertEqual(pop.get(2).state, AgentState.FREE)

    def test_payoffs_update_score(self) -> None:
        pop = _pop_with_agents((1, (0, 0)), (2, (1, 0)))
        step_tick(
            pop,
            self.config,
            ScriptedStrategy(
                world_actions={
                    1: InteractAction(2),
                    2: MoveAction(MoveDirection.STAY),
                },
                pd_choices={1: PDChoice.COOPERATE, 2: PDChoice.DEFECT},
                continue_choices={1: ContinueChoice.LEAVE, 2: ContinueChoice.LEAVE},
            ),
            tick=0,
            rng=random.Random(0),
            meeting_store=self.store,
        )
        self.assertEqual(pop.get(1).score, 0)
        self.assertEqual(pop.get(2).score, 5)

    def test_both_continue_plays_next_round(self) -> None:
        pop = _pop_with_agents((1, (0, 0)), (2, (1, 0)))
        strategy = ScriptedStrategy(
            world_actions={
                1: InteractAction(2),
                2: MoveAction(MoveDirection.STAY),
            },
            continue_choices={
                1: ContinueChoice.CONTINUE,
                2: ContinueChoice.CONTINUE,
            },
        )
        result1 = step_tick(
            pop, self.config, strategy, tick=0, rng=random.Random(0), meeting_store=self.store
        )
        self.assertEqual(len(result1.pd_rounds), 1)
        meeting = result1.meetings_started[0]
        self.assertEqual(meeting.status, MeetingStatus.ACTIVE)
        self.assertEqual(meeting.round_number, 2)
        self.assertEqual(pop.get(1).state, AgentState.IN_MEETING)

        result2 = step_tick(
            pop,
            self.config,
            ScriptedStrategy(
                continue_choices={1: ContinueChoice.LEAVE, 2: ContinueChoice.LEAVE}
            ),
            tick=1,
            rng=random.Random(0),
            meeting_store=self.store,
        )
        self.assertEqual(len(result2.pd_rounds), 1)
        self.assertEqual(meeting.status, MeetingStatus.FINISHED)
        self.assertEqual(pop.get(1).state, AgentState.FREE)

    def test_agent_in_meeting_cannot_start_new_meeting(self) -> None:
        pop = _pop_with_agents((1, (0, 0)), (2, (1, 0)), (3, (0, 1)))
        store = MeetingStore()
        step_tick(
            pop,
            self.config,
            ScriptedStrategy(
                world_actions={
                    1: InteractAction(2),
                    2: MoveAction(MoveDirection.STAY),
                    3: InteractAction(1),
                },
                continue_choices={
                    1: ContinueChoice.CONTINUE,
                    2: ContinueChoice.CONTINUE,
                },
            ),
            tick=0,
            rng=random.Random(0),
            meeting_store=store,
        )
        self.assertEqual(pop.get(1).state, AgentState.IN_MEETING)
        result = step_tick(
            pop,
            self.config,
            ScriptedStrategy(world_actions={3: InteractAction(1)}),
            tick=1,
            rng=random.Random(0),
            meeting_store=store,
        )
        self.assertEqual(result.interactions, ())
        self.assertEqual(result.meetings_started, ())

    def test_one_leave_ends_meeting(self) -> None:
        pop = _pop_with_agents((1, (0, 0)), (2, (1, 0)))
        result = step_tick(
            pop,
            self.config,
            ScriptedStrategy(
                world_actions={
                    1: InteractAction(2),
                    2: MoveAction(MoveDirection.STAY),
                },
                continue_choices={
                    1: ContinueChoice.CONTINUE,
                    2: ContinueChoice.LEAVE,
                },
            ),
            tick=0,
            rng=random.Random(0),
            meeting_store=self.store,
        )
        outcome = result.meeting_outcomes[0]
        self.assertEqual(outcome.continue_a, ContinueChoice.CONTINUE)
        self.assertEqual(outcome.continue_b, ContinueChoice.LEAVE)
        self.assertTrue(outcome.meeting_finished)
        self.assertEqual(pop.get(1).state, AgentState.FREE)
        self.assertEqual(pop.get(2).state, AgentState.FREE)

    def test_agents_in_meeting_do_not_move(self) -> None:
        pop = _pop_with_agents((1, (0, 0)), (2, (1, 0)))
        store = MeetingStore()
        step_tick(
            pop,
            self.config,
            ScriptedStrategy(
                world_actions={
                    1: InteractAction(2),
                    2: MoveAction(MoveDirection.STAY),
                },
                continue_choices={
                    1: ContinueChoice.CONTINUE,
                    2: ContinueChoice.CONTINUE,
                },
            ),
            tick=0,
            rng=random.Random(0),
            meeting_store=store,
        )
        step_tick(
            pop,
            self.config,
            ScriptedStrategy(
                world_actions={
                    1: MoveAction(MoveDirection.EAST),
                    2: MoveAction(MoveDirection.WEST),
                }
            ),
            tick=1,
            rng=random.Random(0),
            meeting_store=store,
        )
        self.assertEqual((pop.get(1).cell_x, pop.get(1).cell_y), (0, 0))
        self.assertEqual((pop.get(2).cell_x, pop.get(2).cell_y), (1, 0))


if __name__ == "__main__":
    unittest.main()
