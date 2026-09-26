from __future__ import annotations

import unittest

from agentiki.sim.agents import Agent, AgentPopulation
from agentiki.sim.config import SimulationConfig
from agentiki.sim.movement import (
    Action,
    build_intents_from_actions,
    resolve_moves,
    tick_rng,
)
from agentiki.sim.meetings import MeetingStore
from agentiki.sim.strategy import RandomTestStrategy
from agentiki.sim.tick import step_tick


def _pop_with_agents(*cells: tuple[int, tuple[int, int]]) -> AgentPopulation:
    pop = AgentPopulation()
    for agent_id, (x, y) in cells:
        pop.place(Agent(id=agent_id, cell_x=x, cell_y=y))
    return pop


def _resolve(pop: AgentPopulation, actions: dict[int, Action]) -> dict[int, tuple[int, int]]:
    agents = {a.id: (a.cell_x, a.cell_y) for a in pop.list()}
    intents = build_intents_from_actions(agents, actions)
    return resolve_moves(pop._occupancy, intents)


class MovementTests(unittest.TestCase):
    def test_single_move_east(self) -> None:
        pop = _pop_with_agents((1, (0, 0)))
        final = _resolve(pop, {1: Action.EAST})
        self.assertEqual(final[1], (1, 0))

    def test_stay(self) -> None:
        pop = _pop_with_agents((1, (0, 0)))
        final = _resolve(pop, {1: Action.STAY})
        self.assertEqual(final[1], (0, 0))

    def test_destination_conflict_min_id_wins(self) -> None:
        pop = _pop_with_agents((1, (0, 0)), (2, (2, 0)))
        final = _resolve(pop, {1: Action.EAST, 2: Action.WEST})
        self.assertEqual(final[1], (1, 0))
        self.assertEqual(final[2], (2, 0))

    def test_blocked_by_staying_occupant(self) -> None:
        pop = _pop_with_agents((1, (0, 0)), (2, (1, 0)))
        final = _resolve(pop, {1: Action.EAST, 2: Action.STAY})
        self.assertEqual(final[1], (0, 0))
        self.assertEqual(final[2], (1, 0))

    def test_chain_moves(self) -> None:
        pop = _pop_with_agents((1, (0, 0)), (2, (1, 0)), (3, (2, 0)))
        final = _resolve(
            pop,
            {1: Action.EAST, 2: Action.EAST, 3: Action.EAST},
        )
        self.assertEqual(final[1], (1, 0))
        self.assertEqual(final[2], (2, 0))
        self.assertEqual(final[3], (3, 0))

    def test_chain_with_staying_tail_blocks_predecessor(self) -> None:
        pop = _pop_with_agents(
            (1, (0, 0)),
            (2, (1, 0)),
            (3, (2, 0)),
            (4, (3, 0)),
        )
        final = _resolve(
            pop,
            {1: Action.EAST, 2: Action.EAST, 3: Action.EAST, 4: Action.STAY},
        )
        self.assertEqual(final[4], (3, 0))
        self.assertEqual(final[3], (2, 0))
        self.assertEqual(final[2], (1, 0))
        self.assertEqual(final[1], (0, 0))

    def test_order_independent(self) -> None:
        pop = _pop_with_agents((1, (0, 0)), (2, (1, 0)), (3, (2, 0)))
        actions = {1: Action.EAST, 2: Action.EAST, 3: Action.NORTH}
        occupancy = dict(pop._occupancy)

        agents_fwd = {a.id: (a.cell_x, a.cell_y) for a in sorted(pop.list(), key=lambda a: a.id)}
        agents_rev = {a.id: (a.cell_x, a.cell_y) for a in sorted(pop.list(), key=lambda a: a.id, reverse=True)}

        intents_fwd = build_intents_from_actions(agents_fwd, actions)
        intents_rev = build_intents_from_actions(agents_rev, actions)

        self.assertEqual(
            resolve_moves(occupancy, intents_fwd),
            resolve_moves(occupancy, intents_rev),
        )

    def test_apply_positions_updates_occupancy(self) -> None:
        pop = _pop_with_agents((1, (0, 0)))
        pop.apply_positions({1: (5, 5)})
        self.assertEqual(pop.at_cell(5, 5).id, 1)
        self.assertIsNone(pop.at_cell(0, 0))

    def test_step_tick_is_deterministic(self) -> None:
        config = SimulationConfig()
        strategy = RandomTestStrategy()
        pop_a = _pop_with_agents((1, (0, 0)), (2, (1, 0)), (3, (0, 1)))
        pop_b = _pop_with_agents((1, (0, 0)), (2, (1, 0)), (3, (0, 1)))
        store_a = MeetingStore()
        store_b = MeetingStore()
        step_tick(
            pop_a, config, strategy, tick=0, rng=tick_rng(seed=42, tick=0), meeting_store=store_a
        )
        step_tick(
            pop_b, config, strategy, tick=0, rng=tick_rng(seed=42, tick=0), meeting_store=store_b
        )
        for a, b in zip(
            sorted(pop_a.list(), key=lambda x: x.id),
            sorted(pop_b.list(), key=lambda x: x.id),
        ):
            self.assertEqual((a.cell_x, a.cell_y), (b.cell_x, b.cell_y))


if __name__ == "__main__":
    unittest.main()
