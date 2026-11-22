"""Uniform lattice generation: density is nearest-neighbor spacing."""

import math
import unittest

from agentiki.sim.agents import AgentPopulation


def _nearest_axis(points: list[tuple[int, int]]) -> int:
    best = None
    for i, (x, y) in enumerate(points):
        for x2, y2 in points[i + 1 :]:
            if x == x2:
                axis = abs(y - y2)
            elif y == y2:
                axis = abs(x - x2)
            else:
                continue
            best = axis if best is None else min(best, axis)
    assert best is not None
    return best


class GenerationTests(unittest.TestCase):
    def test_spacing_matches_density(self) -> None:
        pop = AgentPopulation()
        agents = pop.generate(count=25, density=3, seed=1)
        points = [(a.cell_x, a.cell_y) for a in agents]
        self.assertEqual(len(points), 25)
        self.assertEqual(len(set(points)), 25)
        self.assertEqual(_nearest_axis(points), 3)

    def test_not_clustered_at_origin(self) -> None:
        pop = AgentPopulation()
        agents = pop.generate(count=100, density=2, seed=7)
        points = [(a.cell_x, a.cell_y) for a in agents]
        # Mean radius of a uniform square is much larger than a center-weighted blob.
        mean_r = sum(math.hypot(x, y) for x, y in points) / len(points)
        self.assertGreater(mean_r, 5)

    def test_centered(self) -> None:
        pop = AgentPopulation()
        agents = pop.generate(count=9, density=2, seed=0, origin_x=10, origin_y=-4)
        xs = sorted({a.cell_x for a in agents})
        ys = sorted({a.cell_y for a in agents})
        self.assertEqual(xs, [8, 10, 12])
        self.assertEqual(ys, [-6, -4, -2])

    def test_fits_inside_map(self) -> None:
        pop = AgentPopulation()
        agents = pop.generate(
            count=9,
            density=1,
            seed=0,
            origin_x=4,
            origin_y=4,
            map_width=10,
            map_height=10,
        )
        for agent in agents:
            self.assertGreaterEqual(agent.cell_x, 0)
            self.assertLess(agent.cell_x, 10)
            self.assertGreaterEqual(agent.cell_y, 0)
            self.assertLess(agent.cell_y, 10)

    def test_rejects_when_count_exceeds_area(self) -> None:
        pop = AgentPopulation()
        with self.assertRaises(ValueError):
            pop.generate(
                count=5,
                density=1,
                seed=0,
                map_width=2,
                map_height=2,
            )

    def test_rejects_when_lattice_spills_past_edge(self) -> None:
        pop = AgentPopulation()
        with self.assertRaises(ValueError):
            pop.generate(
                count=9,
                density=3,
                seed=0,
                origin_x=1,
                origin_y=1,
                map_width=5,
                map_height=5,
            )


if __name__ == "__main__":
    unittest.main()
