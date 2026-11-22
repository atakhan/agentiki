from __future__ import annotations

import random
import unittest

from agentiki.sim.actions import InteractAction, MoveAction, MoveDirection
from agentiki.sim.agents import START_HP, Agent, AgentPopulation, AgentState
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
        self.config = SimulationConfig(
            vision_radius=3, interaction_radius=1, enable_pd=True
        )
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

    def test_payoffs_update_energy(self) -> None:
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
        # Default start energy 100. Initiator: −4 +0; partner: −3 +5.
        self.assertEqual(pop.get(1).hp, START_HP - 1)
        self.assertEqual(pop.get(2).hp, START_HP - 1)
        self.assertEqual(pop.get(1).energy, 96.0)
        self.assertEqual(pop.get(2).energy, 102.0)
        self.assertFalse(hasattr(pop.get(1), "score"))

    def test_played_rounds_award_matrix_and_accumulate(self) -> None:
        # Energy starts at 10 so costs are visible without floor clamping.
        cases = (
            (PDChoice.COOPERATE, PDChoice.COOPERATE, 10 - 4 + 3, 10 - 3 + 3),
            (PDChoice.DEFECT, PDChoice.DEFECT, 10 - 4 + 1, 10 - 3 + 1),
            (PDChoice.COOPERATE, PDChoice.DEFECT, 10 - 4 + 0, 10 - 3 + 5),
        )
        for choice_a, choice_b, energy_a, energy_b in cases:
            pop = _pop_with_agents((1, (0, 0)), (2, (1, 0)))
            pop.get(1).energy = 10.0
            pop.get(2).energy = 10.0
            step_tick(
                pop,
                self.config,
                ScriptedStrategy(
                    world_actions={
                        1: InteractAction(2),
                        2: MoveAction(MoveDirection.STAY),
                    },
                    pd_choices={1: choice_a, 2: choice_b},
                    continue_choices={1: ContinueChoice.LEAVE, 2: ContinueChoice.LEAVE},
                ),
                tick=0,
                rng=random.Random(0),
                meeting_store=MeetingStore(),
            )
            self.assertEqual(pop.get(1).hp, START_HP - 1)
            self.assertEqual(pop.get(2).hp, START_HP - 1)
            self.assertEqual(pop.get(1).energy, float(energy_a))
            self.assertEqual(pop.get(2).energy, float(energy_b))

        pop = _pop_with_agents((1, (0, 0)), (2, (1, 0)))
        pop.get(1).energy = 10.0
        pop.get(2).energy = 10.0
        store = MeetingStore()
        step_tick(
            pop,
            self.config,
            ScriptedStrategy(
                world_actions={
                    1: InteractAction(2),
                    2: InteractAction(1),
                },
                pd_choices={1: PDChoice.COOPERATE, 2: PDChoice.COOPERATE},
                continue_choices={
                    1: ContinueChoice.CONTINUE,
                    2: ContinueChoice.CONTINUE,
                },
            ),
            tick=0,
            rng=random.Random(0),
            meeting_store=store,
        )
        # Mutual cooperate: stay+interact+game+continue, payoff +3 → energy 9.
        self.assertEqual(pop.get(1).hp, START_HP - 1)
        self.assertEqual(pop.get(1).energy, 9.0)
        self.assertEqual(pop.get(2).energy, 9.0)
        step_tick(
            pop,
            self.config,
            ScriptedStrategy(
                pd_choices={1: PDChoice.DEFECT, 2: PDChoice.DEFECT},
                continue_choices={1: ContinueChoice.LEAVE, 2: ContinueChoice.LEAVE},
            ),
            tick=1,
            rng=random.Random(0),
            meeting_store=store,
        )
        # Meeting tick: stay+game+leave, payoff +1 → energy 9-3+1=7. Life −2 total.
        self.assertEqual(pop.get(1).hp, START_HP - 2)
        self.assertEqual(pop.get(1).energy, 7.0)
        self.assertEqual(pop.get(2).energy, 7.0)

        far = _pop_with_agents((1, (0, 0)), (2, (5, 0)))
        far.get(1).energy = 10.0
        far.get(2).energy = 10.0
        step_tick(
            far,
            self.config,
            ScriptedStrategy(
                world_actions={
                    1: InteractAction(2),
                    2: MoveAction(MoveDirection.STAY),
                }
            ),
            tick=0,
            rng=random.Random(0),
            meeting_store=MeetingStore(),
        )
        # Out of range: stay+interact decision, no PD.
        self.assertEqual(far.get(1).hp, START_HP - 1)
        self.assertEqual(far.get(1).energy, 8.0)
        self.assertEqual(far.get(2).energy, 9.0)

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
