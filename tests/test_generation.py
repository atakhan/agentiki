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


if __name__ == "__main__":
    unittest.main()
