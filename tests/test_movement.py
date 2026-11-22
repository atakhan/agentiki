from __future__ import annotations

import unittest

from agentiki.sim.agents import Agent, AgentPopulation
from agentiki.sim.config import SimulationConfig
from agentiki.sim.movement import (
    Action,
    build_intents_from_actions,
    move_priority,
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


def _resolve(
    pop: AgentPopulation,
    actions: dict[int, Action],
    *,
    seed: int = 1,
    tick: int = 0,
) -> dict[int, tuple[int, int]]:
    agents = {a.id: (a.cell_x, a.cell_y) for a in pop.list()}
    intents = build_intents_from_actions(agents, actions)
    return resolve_moves(pop._occupancy, intents, seed=seed, tick=tick)


class MovementTests(unittest.TestCase):
    def test_single_move_east(self) -> None:
        pop = _pop_with_agents((1, (0, 0)))
        final = _resolve(pop, {1: Action.EAST})
        self.assertEqual(final[1], (1, 0))

    def test_stay(self) -> None:
        pop = _pop_with_agents((1, (0, 0)))
        final = _resolve(pop, {1: Action.STAY})
        self.assertEqual(final[1], (0, 0))

    def test_hard_wall_blocks_outbound_move(self) -> None:
        pop = _pop_with_agents((1, (0, 0)))
        agents = {1: (0, 0)}
        intents = build_intents_from_actions(agents, {1: Action.WEST})
        final = resolve_moves(
            pop._occupancy, intents, seed=1, tick=0, map_width=8, map_height=8
        )
        self.assertEqual(final[1], (0, 0))

    def test_hard_wall_allows_inward_move(self) -> None:
        pop = _pop_with_agents((1, (0, 0)))
        agents = {1: (0, 0)}
        intents = build_intents_from_actions(agents, {1: Action.EAST})
        final = resolve_moves(
            pop._occupancy, intents, seed=1, tick=0, map_width=8, map_height=8
        )
        self.assertEqual(final[1], (1, 0))

    def test_destination_conflict_highest_priority_wins(self) -> None:
        seed, tick = 1, 0
        dest = (1, 0)
        winner = max(
            (1, 2),
            key=lambda agent_id: (
                move_priority(seed, tick, dest[0], dest[1], agent_id),
                agent_id,
            ),
        )
        loser = 1 if winner == 2 else 2
        pop = _pop_with_agents((1, (0, 0)), (2, (2, 0)))
        final = _resolve(pop, {1: Action.EAST, 2: Action.WEST}, seed=seed, tick=tick)
        self.assertEqual(final[winner], dest)
        self.assertEqual(
            final[loser],
            (0, 0) if loser == 1 else (2, 0),
        )

    def test_destination_conflict_winner_varies_with_seed(self) -> None:
        winners: set[int] = set()
        for seed in range(64):
            pop = _pop_with_agents((1, (0, 0)), (2, (2, 0)))
            final = _resolve(
                pop, {1: Action.EAST, 2: Action.WEST}, seed=seed, tick=0
            )
            if final[1] == (1, 0):
                winners.add(1)
            else:
                winners.add(2)
        self.assertEqual(winners, {1, 2})

    def test_destination_conflict_is_deterministic(self) -> None:
        pop_a = _pop_with_agents((1, (0, 0)), (2, (2, 0)))
        pop_b = _pop_with_agents((1, (0, 0)), (2, (2, 0)))
        actions = {1: Action.EAST, 2: Action.WEST}
        self.assertEqual(
            _resolve(pop_a, actions, seed=7, tick=3),
            _resolve(pop_b, actions, seed=7, tick=3),
        )

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
        agents_rev = {
            a.id: (a.cell_x, a.cell_y)
            for a in sorted(pop.list(), key=lambda a: a.id, reverse=True)
        }

        intents_fwd = build_intents_from_actions(agents_fwd, actions)
        intents_rev = build_intents_from_actions(agents_rev, actions)

        self.assertEqual(
            resolve_moves(occupancy, intents_fwd, seed=11, tick=2),
            resolve_moves(occupancy, intents_rev, seed=11, tick=2),
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
            pop_a,
            config,
            strategy,
            tick=0,
            rng=tick_rng(seed=42, tick=0),
            meeting_store=store_a,
            seed=42,
        )
        step_tick(
            pop_b,
            config,
            strategy,
            tick=0,
            rng=tick_rng(seed=42, tick=0),
            meeting_store=store_b,
            seed=42,
        )
        for a, b in zip(
            sorted(pop_a.list(), key=lambda x: x.id),
            sorted(pop_b.list(), key=lambda x: x.id),
        ):
            self.assertEqual((a.cell_x, a.cell_y), (b.cell_x, b.cell_y))


if __name__ == "__main__":
    unittest.main()
