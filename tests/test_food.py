"""Food perception, seeking, EatAction consumption, and replenishment."""

from __future__ import annotations

import random
import unittest

from agentiki.sim.actions import EatAction, MoveAction, MoveDirection
from agentiki.sim.agents import Agent, AgentPopulation, AgentState
from agentiki.sim.config import SimulationConfig
from agentiki.sim.engine import PythonEngine
from agentiki.sim.food import (
    FoodStore,
    cell_density,
    pick_lowest_density_cell,
    process_food_consumption,
    spawn_initial_food,
)
from agentiki.sim.foraging import direction_toward, pick_eatable_food, pick_nearest_food
from agentiki.sim.meetings import ContinueChoice, MeetingStore
from agentiki.sim.perception import VisibleFood, observe
from agentiki.sim.pd import PDChoice
from agentiki.sim.strategy import RandomTestStrategy
from agentiki.sim.tick import step_tick


class _FixedMove:
    def __init__(self, direction: MoveDirection):
        self._direction = direction

    def choose(self, observation, config, rng):
        return MoveAction(direction=self._direction)

    def choose_pd(self, meeting, agent_id, config, rng):
        return PDChoice.COOPERATE

    def choose_continue(self, meeting, agent_id, round_result, config, rng):
        return ContinueChoice.LEAVE


class _EatOrStay:
    """Eat when strategy would; otherwise stay (for controlled tests)."""

    def choose(self, observation, config, rng):
        eatable = pick_eatable_food(
            observation.visible_food, config.interaction_radius, rng
        )
        if eatable is not None:
            return EatAction(food_id=eatable.food_id)
        return MoveAction(direction=MoveDirection.STAY)

    def choose_pd(self, meeting, agent_id, config, rng):
        return PDChoice.COOPERATE

    def choose_continue(self, meeting, agent_id, round_result, config, rng):
        return ContinueChoice.LEAVE


class FoodPerceptionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = SimulationConfig(
            map_width=20, map_height=20, vision_radius=3, food_capacity=0
        )

    def test_sees_food_chebyshev_1(self) -> None:
        pop = AgentPopulation()
        pop.place(Agent(id=1, cell_x=5, cell_y=5))
        store = FoodStore()
        store.place(6, 5, 10.0)
        obs = observe(pop.get(1), pop, self.config, store)
        self.assertEqual(len(obs.visible_food), 1)

    def test_sees_food_chebyshev_3(self) -> None:
        pop = AgentPopulation()
        pop.place(Agent(id=1, cell_x=5, cell_y=5))
        store = FoodStore()
        store.place(8, 5, 10.0)
        obs = observe(pop.get(1), pop, self.config, store)
        self.assertEqual(len(obs.visible_food), 1)

    def test_does_not_see_food_beyond_vision(self) -> None:
        pop = AgentPopulation()
        pop.place(Agent(id=1, cell_x=5, cell_y=5))
        store = FoodStore()
        store.place(9, 5, 10.0)
        obs = observe(pop.get(1), pop, self.config, store)
        self.assertEqual(obs.visible_food, ())

    def test_picks_nearest_by_manhattan(self) -> None:
        foods = (
            VisibleFood(1, 3, 0),
            VisibleFood(2, 1, 1),
            VisibleFood(3, 2, 2),
        )
        chosen = pick_nearest_food(foods, random.Random(0))
        self.assertEqual(chosen.food_id, 2)

    def test_tie_break_is_deterministic(self) -> None:
        foods = (VisibleFood(1, 2, 0), VisibleFood(2, 0, 2))
        a = pick_nearest_food(foods, random.Random(7))
        b = pick_nearest_food(foods, random.Random(7))
        self.assertEqual(a.food_id, b.food_id)

    def test_eatable_only_within_interaction_radius(self) -> None:
        foods = (VisibleFood(1, 2, 0), VisibleFood(2, 1, 0))
        chosen = pick_eatable_food(foods, interaction_radius=1, rng=random.Random(0))
        self.assertEqual(chosen.food_id, 2)
        self.assertIsNone(
            pick_eatable_food(foods[:1], interaction_radius=1, rng=random.Random(0))
        )


class FoodMovementTests(unittest.TestCase):
    def test_moves_toward_food_cardinal(self) -> None:
        self.assertEqual(
            direction_toward(2, 0, random.Random(0)), MoveDirection.EAST
        )

    def test_diagonal_chooses_cardinal_only(self) -> None:
        for seed in range(20):
            direction = direction_toward(2, -3, random.Random(seed))
            self.assertIn(direction, (MoveDirection.EAST, MoveDirection.SOUTH))

    def test_strategy_moves_when_food_not_yet_reachable(self) -> None:
        config = SimulationConfig(map_width=10, map_height=10, food_capacity=0)
        pop = AgentPopulation()
        pop.place(Agent(id=1, cell_x=2, cell_y=2))
        store = FoodStore()
        store.place(5, 2, 10.0)
        step_tick(
            pop,
            config,
            RandomTestStrategy(),
            tick=0,
            rng=random.Random(1),
            meeting_store=MeetingStore(),
            seed=1,
            food_store=store,
        )
        self.assertEqual((pop.get(1).cell_x, pop.get(1).cell_y), (3, 2))
        self.assertEqual(pop.get(1).energy, 98.0)  # start 100 − move 2

    def test_arrival_does_not_eat_same_tick(self) -> None:
        config = SimulationConfig(
            map_width=8, map_height=8, food_capacity=1, food_energy=10.0
        )
        pop = AgentPopulation()
        pop.place(Agent(id=1, cell_x=0, cell_y=0))
        store = FoodStore()
        store.place(1, 0, 10.0)
        result = step_tick(
            pop,
            config,
            _FixedMove(MoveDirection.EAST),
            tick=0,
            rng=random.Random(0),
            meeting_store=MeetingStore(),
            seed=1,
            food_store=store,
        )
        self.assertEqual((pop.get(1).cell_x, pop.get(1).cell_y), (1, 0))
        self.assertEqual(result.food_consumed, ())
        self.assertEqual(pop.get(1).energy, 98.0)  # start 100 − move 2
        self.assertIsNotNone(store.at_cell(1, 0))

    def test_eat_requires_dedicated_tick(self) -> None:
        config = SimulationConfig(
            map_width=8, map_height=8, food_capacity=1, food_energy=10.0
        )
        pop = AgentPopulation()
        pop.place(Agent(id=1, cell_x=0, cell_y=0))
        store = FoodStore()
        store.place(1, 0, 10.0)
        step_tick(
            pop,
            config,
            _FixedMove(MoveDirection.EAST),
            0,
            random.Random(0),
            MeetingStore(),
            seed=1,
            food_store=store,
        )
        result = step_tick(
            pop,
            config,
            _EatOrStay(),
            1,
            random.Random(0),
            MeetingStore(),
            seed=1,
            food_store=store,
        )
        self.assertEqual(len(result.food_consumed), 1)
        # move −2, then eat stay −1 +10 → 107
        self.assertEqual(pop.get(1).energy, 107.0)
        self.assertEqual((pop.get(1).cell_x, pop.get(1).cell_y), (1, 0))


class FoodConsumptionTests(unittest.TestCase):
    def test_single_agent_full_energy(self) -> None:
        config = SimulationConfig(
            map_width=8, map_height=8, food_capacity=1, food_energy=10.0
        )
        pop = AgentPopulation()
        pop.place(Agent(id=1, cell_x=3, cell_y=3, energy=0.0))
        store = FoodStore()
        food = store.place(3, 3, 10.0)
        events, spawned = process_food_consumption(
            store,
            pop,
            config,
            tick=0,
            seed=1,
            rng=random.Random(0),
            eat_intents={1: food.id},
        )
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].energy, 10.0)
        self.assertEqual(pop.get(1).energy, 10.0)
        self.assertEqual(len(store), 1)
        self.assertEqual(len(spawned), 1)

    def test_no_intent_means_no_eat(self) -> None:
        config = SimulationConfig(
            map_width=8, map_height=8, food_capacity=1, food_energy=10.0
        )
        pop = AgentPopulation()
        pop.place(Agent(id=1, cell_x=3, cell_y=3, energy=0.0))
        store = FoodStore()
        store.place(3, 3, 10.0)
        events, spawned = process_food_consumption(
            store, pop, config, tick=0, seed=1, rng=random.Random(0), eat_intents={}
        )
        self.assertEqual(events, ())
        self.assertEqual(spawned, ())
        self.assertEqual(pop.get(1).energy, 0.0)
        self.assertEqual(len(store), 1)

    def test_two_agents_split_evenly(self) -> None:
        config = SimulationConfig(
            map_width=8, map_height=8, food_capacity=1, food_energy=10.0
        )
        pop = AgentPopulation()
        pop.place(Agent(id=1, cell_x=3, cell_y=3, energy=0.0))
        pop.place(Agent(id=2, cell_x=4, cell_y=3, energy=0.0))
        store = FoodStore()
        food = store.place(3, 3, 10.0)
        events, _spawned = process_food_consumption(
            store,
            pop,
            config,
            tick=0,
            seed=1,
            rng=random.Random(0),
            eat_intents={1: food.id, 2: food.id},
        )
        self.assertEqual(len(events), 2)
        self.assertEqual(pop.get(1).energy, 5.0)
        self.assertEqual(pop.get(2).energy, 5.0)

    def test_three_agents_keep_fractional_share(self) -> None:
        config = SimulationConfig(
            map_width=8, map_height=8, food_capacity=1, food_energy=10.0
        )
        pop = AgentPopulation()
        pop.place(Agent(id=1, cell_x=3, cell_y=3, energy=0.0))
        pop.place(Agent(id=2, cell_x=4, cell_y=3, energy=0.0))
        pop.place(Agent(id=3, cell_x=3, cell_y=4, energy=0.0))
        store = FoodStore()
        food = store.place(3, 3, 10.0)
        process_food_consumption(
            store,
            pop,
            config,
            tick=0,
            seed=1,
            rng=random.Random(0),
            eat_intents={1: food.id, 2: food.id, 3: food.id},
        )
        share = 10.0 / 3.0
        self.assertAlmostEqual(pop.get(1).energy, share)

    def test_consume_from_neighbor_cell(self) -> None:
        config = SimulationConfig(
            map_width=8, map_height=8, food_capacity=1, food_energy=10.0
        )
        pop = AgentPopulation()
        pop.place(Agent(id=1, cell_x=2, cell_y=2, energy=0.0))
        store = FoodStore()
        food = store.place(3, 2, 10.0)
        events, _ = process_food_consumption(
            store,
            pop,
            config,
            tick=0,
            seed=1,
            rng=random.Random(0),
            eat_intents={1: food.id},
        )
        self.assertEqual(len(events), 1)
        self.assertEqual(pop.get(1).energy, 10.0)

    def test_out_of_range_intent_ignored(self) -> None:
        config = SimulationConfig(
            map_width=8, map_height=8, food_capacity=1, food_energy=10.0
        )
        pop = AgentPopulation()
        pop.place(Agent(id=1, cell_x=0, cell_y=0, energy=0.0))
        store = FoodStore()
        food = store.place(3, 0, 10.0)
        events, _ = process_food_consumption(
            store,
            pop,
            config,
            tick=0,
            seed=1,
            rng=random.Random(0),
            eat_intents={1: food.id},
        )
        self.assertEqual(events, ())
        self.assertEqual(pop.get(1).energy, 0.0)

    def test_agent_eats_at_most_one_food_per_tick(self) -> None:
        config = SimulationConfig(
            map_width=8, map_height=8, food_capacity=2, food_energy=10.0
        )
        pop = AgentPopulation()
        pop.place(Agent(id=1, cell_x=3, cell_y=3, energy=0.0))
        store = FoodStore()
        food_a = store.place(3, 3, 10.0)
        store.place(4, 3, 10.0)
        events, spawned = process_food_consumption(
            store,
            pop,
            config,
            tick=0,
            seed=1,
            rng=random.Random(0),
            eat_intents={1: food_a.id},
        )
        self.assertEqual(len(events), 1)
        self.assertEqual(pop.get(1).energy, 10.0)
        self.assertEqual(len(store), 2)
        self.assertEqual(len(spawned), 1)

    def test_meeting_agent_can_eat(self) -> None:
        config = SimulationConfig(
            map_width=8, map_height=8, food_capacity=1, food_energy=10.0
        )
        pop = AgentPopulation()
        pop.place(
            Agent(id=1, cell_x=1, cell_y=1, state=AgentState.IN_MEETING, energy=100.0)
        )
        store = FoodStore()
        store.place(1, 1, 10.0)
        result = step_tick(
            pop,
            config,
            _FixedMove(MoveDirection.EAST),
            0,
            random.Random(0),
            MeetingStore(),
            seed=1,
            food_store=store,
        )
        self.assertEqual((pop.get(1).cell_x, pop.get(1).cell_y), (1, 1))
        self.assertEqual(len(result.food_consumed), 1)
        self.assertEqual(pop.get(1).energy, 109.0)  # stay −1 +10

    def test_capacity_restored_after_consumption(self) -> None:
        config = SimulationConfig(
            map_width=10, map_height=10, food_capacity=3, food_energy=10.0
        )
        pop = AgentPopulation()
        pop.place(Agent(id=1, cell_x=1, cell_y=1))
        store = FoodStore()
        spawn_initial_food(store, pop, config, random.Random(2))
        food = store.list()[0]
        pop.get(1).cell_x = food.cell_x
        pop.get(1).cell_y = food.cell_y
        process_food_consumption(
            store,
            pop,
            config,
            tick=0,
            seed=1,
            rng=random.Random(0),
            eat_intents={1: food.id},
        )
        self.assertEqual(len(store), 3)

    def test_initial_spawn_and_engine(self) -> None:
        engine = PythonEngine(seed=3)
        engine.set_map_size(12, 12)
        engine.set_food_rules(
            food_capacity=8, food_density_radius=2, food_energy=10.0
        )
        engine.generate_agents(4, 1.0)
        self.assertEqual(engine.food_count, 8)

    def test_density_helper(self) -> None:
        agents = {(0, 0), (1, 0)}
        food = {(0, 1)}
        self.assertEqual(cell_density(0, 0, 1, agents, food), 3)
        cell = pick_lowest_density_cell(
            3, 1, 1, {(0, 0)}, set(), seed=1, tick=0
        )
        self.assertEqual(cell, (2, 0))


if __name__ == "__main__":
    unittest.main()
