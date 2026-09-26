from __future__ import annotations

import unittest

from agentiki.sim.agents import Agent, AgentPopulation
from agentiki.sim.config import SimulationConfig
from agentiki.sim.engine import PythonEngine
from agentiki.sim.perception import (
    chebyshev_distance,
    is_interactable,
    observe,
)


def _pop(*cells: tuple[int, tuple[int, int]]) -> AgentPopulation:
    pop = AgentPopulation()
    for agent_id, (x, y) in cells:
        pop.place(Agent(id=agent_id, cell_x=x, cell_y=y))
    return pop


class PerceptionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = SimulationConfig(vision_radius=3, interaction_radius=1)

    def test_chebyshev_distance(self) -> None:
        self.assertEqual(chebyshev_distance(2, 0), 2)
        self.assertEqual(chebyshev_distance(-2, 2), 2)

    def test_sees_nobody_out_of_range(self) -> None:
        pop = _pop((1, (0, 0)), (2, (5, 0)))
        obs = observe(pop.get(1), pop, self.config)
        self.assertEqual(obs.visible_agents, ())

    def test_sees_agent_in_range(self) -> None:
        pop = _pop((1, (0, 0)), (2, (2, 0)))
        obs = observe(pop.get(1), pop, self.config)
        self.assertEqual(len(obs.visible_agents), 1)
        visible = obs.visible_agents[0]
        self.assertEqual(visible.agent_id, 2)
        self.assertEqual(visible.relative_x, 2)
        self.assertEqual(visible.relative_y, 0)

    def test_negative_relative_coordinates(self) -> None:
        pop = _pop((1, (10, 10)), (2, (8, 12)))
        obs = observe(pop.get(1), pop, self.config)
        self.assertEqual(obs.visible_agents[0].relative_x, -2)
        self.assertEqual(obs.visible_agents[0].relative_y, 2)

    def test_vision_boundary_inclusive(self) -> None:
        pop = _pop((1, (0, 0)), (2, (3, 0)))
        obs = observe(pop.get(1), pop, self.config)
        self.assertEqual(len(obs.visible_agents), 1)

    def test_vision_boundary_exclusive(self) -> None:
        pop = _pop((1, (0, 0)), (2, (4, 0)))
        obs = observe(pop.get(1), pop, self.config)
        self.assertEqual(obs.visible_agents, ())

    def test_interaction_boundary(self) -> None:
        self.assertTrue(is_interactable(self.config, 1, 0))
        self.assertTrue(is_interactable(self.config, 1, 1))
        self.assertFalse(is_interactable(self.config, 2, 0))
        self.assertFalse(is_interactable(self.config, 0, 0))

    def test_multiple_visible_agents(self) -> None:
        pop = _pop((1, (0, 0)), (2, (1, 0)), (3, (0, 2)), (4, (5, 5)))
        obs = observe(pop.get(1), pop, self.config)
        self.assertEqual({v.agent_id for v in obs.visible_agents}, {2, 3})

    def test_strategy_view_hides_agent_ids(self) -> None:
        pop = _pop((1, (0, 0)), (2, (1, 0)))
        obs = observe(pop.get(1), pop, self.config)
        strategy = obs.for_strategy()
        self.assertEqual(len(strategy), 1)
        self.assertEqual(strategy[0].relative_x, 1)
        self.assertEqual(strategy[0].relative_y, 0)

    def test_observation_updates_after_movement(self) -> None:
        pop = _pop((1, (0, 0)), (2, (5, 0)))
        self.assertEqual(observe(pop.get(1), pop, self.config).visible_agents, ())
        pop.apply_positions({1: (0, 0), 2: (3, 0)})
        obs = observe(pop.get(1), pop, self.config)
        self.assertEqual(len(obs.visible_agents), 1)
        self.assertEqual(obs.visible_agents[0].relative_x, 3)

    def test_engine_observe(self) -> None:
        engine = PythonEngine(seed=1, config=self.config)
        engine.generate_agents(5, 1.0)
        obs = engine.observe(1)
        self.assertEqual(obs.observer_id, 1)


class ConfigTests(unittest.TestCase):
    def test_interaction_must_not_exceed_vision(self) -> None:
        with self.assertRaises(ValueError):
            SimulationConfig(vision_radius=1, interaction_radius=2)


if __name__ == "__main__":
    unittest.main()
