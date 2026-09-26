from __future__ import annotations

import random
import unittest

from agentiki.sim.actions import InteractAction, MoveAction, MoveDirection
from agentiki.sim.agents import Agent, AgentPopulation
from agentiki.sim.config import SimulationConfig
from agentiki.sim.interactions import resolve_interactions
from agentiki.sim.meetings import ContinueChoice, MeetingStore
from agentiki.sim.pd import PDChoice
from agentiki.sim.tick import step_tick


def _pop_with_agents(*cells: tuple[int, tuple[int, int]]) -> AgentPopulation:
    pop = AgentPopulation()
    for agent_id, (x, y) in cells:
        pop.place(Agent(id=agent_id, cell_x=x, cell_y=y))
    return pop


class FixedStrategy:
    def __init__(self, actions: dict[int, InteractAction | MoveAction]) -> None:
        self._actions = actions

    def choose(self, observation, config, rng):
        return self._actions[observation.observer_id]

    def choose_pd(self, meeting, agent_id, config, rng):
        return PDChoice.COOPERATE

    def choose_continue(self, meeting, agent_id, round_result, config, rng):
        return ContinueChoice.LEAVE


class InteractionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = SimulationConfig(vision_radius=3, interaction_radius=1)
        self.store = MeetingStore()

    def test_simple_contact(self) -> None:
        pop = _pop_with_agents((1, (0, 0)), (2, (1, 0)))
        result = step_tick(
            pop,
            self.config,
            FixedStrategy({1: InteractAction(2), 2: MoveAction(MoveDirection.STAY)}),
            tick=0,
            rng=random.Random(0),
            meeting_store=self.store,
        )
        self.assertEqual(len(result.interactions), 1)
        interaction = result.interactions[0]
        self.assertEqual(interaction.agent_a, 1)
        self.assertEqual(interaction.agent_b, 2)
        self.assertEqual(interaction.initiators, frozenset({1}))

    def test_unreachable_target(self) -> None:
        pop = _pop_with_agents((1, (0, 0)), (2, (3, 0)))
        result = step_tick(
            pop,
            self.config,
            FixedStrategy({1: InteractAction(2), 2: MoveAction(MoveDirection.STAY)}),
            tick=0,
            rng=random.Random(0),
            meeting_store=self.store,
        )
        self.assertEqual(result.interactions, ())

    def test_mutual_contact_single_event(self) -> None:
        pop = _pop_with_agents((1, (0, 0)), (2, (1, 0)))
        result = step_tick(
            pop,
            self.config,
            FixedStrategy(
                {
                    1: InteractAction(2),
                    2: InteractAction(1),
                }
            ),
            tick=5,
            rng=random.Random(0),
            meeting_store=self.store,
        )
        self.assertEqual(len(result.interactions), 1)
        interaction = result.interactions[0]
        self.assertEqual(interaction.initiators, frozenset({1, 2}))
        self.assertEqual(interaction.tick, 5)

    def test_multiple_initiators_one_target(self) -> None:
        pop = _pop_with_agents((10, (0, 0)), (20, (2, 0)), (30, (1, 0)))
        result = step_tick(
            pop,
            self.config,
            FixedStrategy(
                {
                    10: InteractAction(30),
                    20: InteractAction(30),
                    30: MoveAction(MoveDirection.STAY),
                }
            ),
            tick=0,
            rng=random.Random(0),
            meeting_store=self.store,
        )
        self.assertEqual(len(result.interactions), 1)
        interaction = result.interactions[0]
        self.assertEqual(interaction.agent_a, 10)
        self.assertEqual(interaction.agent_b, 30)
        self.assertEqual(interaction.initiators, frozenset({10}))

    def test_target_moves_away_contact_still_happens(self) -> None:
        pop = _pop_with_agents((1, (0, 0)), (2, (1, 0)))
        result = step_tick(
            pop,
            self.config,
            FixedStrategy(
                {
                    1: InteractAction(2),
                    2: MoveAction(MoveDirection.EAST),
                }
            ),
            tick=0,
            rng=random.Random(0),
            meeting_store=self.store,
        )
        self.assertEqual(len(result.interactions), 1)
        self.assertEqual((pop.get(1).cell_x, pop.get(1).cell_y), (0, 0))
        self.assertEqual((pop.get(2).cell_x, pop.get(2).cell_y), (2, 0))

    def test_movement_alone_does_not_create_contact(self) -> None:
        pop = _pop_with_agents((1, (0, 0)), (2, (3, 0)))
        result = step_tick(
            pop,
            self.config,
            FixedStrategy(
                {
                    1: MoveAction(MoveDirection.EAST),
                    2: MoveAction(MoveDirection.WEST),
                }
            ),
            tick=0,
            rng=random.Random(0),
            meeting_store=self.store,
        )
        self.assertEqual(result.interactions, ())
        self.assertEqual((pop.get(1).cell_x, pop.get(1).cell_y), (1, 0))
        self.assertEqual((pop.get(2).cell_x, pop.get(2).cell_y), (2, 0))

    def test_invalid_interact_stays_in_place(self) -> None:
        pop = _pop_with_agents((1, (0, 0)), (2, (3, 0)))
        step_tick(
            pop,
            self.config,
            FixedStrategy({1: InteractAction(2), 2: MoveAction(MoveDirection.STAY)}),
            tick=0,
            rng=random.Random(0),
            meeting_store=self.store,
        )
        self.assertEqual((pop.get(1).cell_x, pop.get(1).cell_y), (0, 0))

    def test_resolve_interactions_direct(self) -> None:
        pop = _pop_with_agents((1, (0, 0)), (2, (1, 0)))
        interactions = resolve_interactions({1: 2}, pop, self.config, tick=7)
        self.assertEqual(len(interactions), 1)
        self.assertEqual(interactions[0].tick, 7)


if __name__ == "__main__":
    unittest.main()
