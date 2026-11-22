"""Fixed map bounds: cells and engine map size."""

from __future__ import annotations

import unittest

from agentiki.sim.engine import PythonEngine
from agentiki.sim.world import BoundedWorld


class WorldBoundsTests(unittest.TestCase):
    def test_contains(self) -> None:
        world = BoundedWorld(seed=1, width=3, height=2)
        self.assertTrue(world.contains(0, 0))
        self.assertTrue(world.contains(2, 1))
        self.assertFalse(world.contains(-1, 0))
        self.assertFalse(world.contains(3, 0))
        self.assertFalse(world.contains(0, 2))

    def test_cell_outside_raises(self) -> None:
        world = BoundedWorld(seed=1, width=2, height=2)
        with self.assertRaises(ValueError):
            world.cell(2, 0)

    def test_iter_cells_clips_to_map(self) -> None:
        world = BoundedWorld(seed=1, width=4, height=3)
        cells = list(world.iter_cells(-2, -2, 10, 10))
        self.assertEqual(len(cells), 12)
        self.assertEqual({(c.x, c.y) for c in cells}, {
            (x, y) for x in range(4) for y in range(3)
        })

    def test_engine_set_map_size_and_generate(self) -> None:
        engine = PythonEngine(seed=1)
        engine.set_map_size(12, 10)
        self.assertEqual(engine.config.map_width, 12)
        self.assertEqual(engine.config.map_height, 10)
        agents = engine.generate_agents(4, 1.0)
        self.assertEqual(len(agents), 4)
        for agent in agents:
            self.assertTrue(0 <= agent.cell_x < 12)
            self.assertTrue(0 <= agent.cell_y < 10)

    def test_reset_keeps_map_size(self) -> None:
        engine = PythonEngine(seed=1)
        engine.set_map_size(20, 15)
        engine.generate_agents(2, 1.0)
        engine.reset()
        self.assertEqual(engine.config.map_width, 20)
        self.assertEqual(engine.config.map_height, 15)
        self.assertEqual(engine.agent_count, 0)


if __name__ == "__main__":
    unittest.main()
