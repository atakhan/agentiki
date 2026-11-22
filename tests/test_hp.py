"""Life tick drain and energy action costs."""

import random
import unittest
from dataclasses import replace

from agentiki.sim.actions import InteractAction, MoveAction, MoveDirection
from agentiki.sim.agents import START_HP, Agent, AgentPopulation
from agentiki.sim.config import SimulationConfig
from agentiki.sim.engine import PythonEngine
from agentiki.sim.meetings import ContinueChoice, MeetingStore
from agentiki.sim.pd import PayoffMatrix, PDChoice
from agentiki.sim.tick import step_tick


class _FixedStrategy:
    def __init__(self, action, pd=PDChoice.COOPERATE, cont=ContinueChoice.LEAVE):
        self._action = action
        self._pd = pd
        self._cont = cont

    def choose(self, observation, config, rng):
        action = self._action
        if isinstance(action, InteractAction) and action.target_agent_id < 0:
            others = [v.agent_id for v in observation.visible_agents]
            return InteractAction(target_agent_id=others[0])
        return action

    def choose_pd(self, meeting, agent_id, config, rng):
        return self._pd

    def choose_continue(self, meeting, agent_id, round_result, config, rng):
        return self._cont


def _one() -> AgentPopulation:
    pop = AgentPopulation()
    pop.place(Agent(id=1, cell_x=0, cell_y=0, energy=10.0))
    pop._next_id = 2
    return pop


class LifeAndEnergyTests(unittest.TestCase):
    def test_life_ticks_down_by_one_regardless_of_action(self) -> None:
        for direction in (MoveDirection.STAY, MoveDirection.EAST):
            pop = _one()
            step_tick(
                pop,
                SimulationConfig(),
                _FixedStrategy(MoveAction(direction=direction)),
                0,
                random.Random(0),
                MeetingStore(),
            )
            self.assertEqual(pop.get(1).hp, START_HP - 1)

    def test_stay_costs_energy_1(self) -> None:
        pop = _one()
        step_tick(
            pop,
            SimulationConfig(),
            _FixedStrategy(MoveAction(MoveDirection.STAY)),
            0,
            random.Random(0),
            MeetingStore(),
        )
        self.assertEqual(pop.get(1).energy, 9.0)

    def test_move_costs_energy_2(self) -> None:
        pop = _one()
        step_tick(
            pop,
            SimulationConfig(),
            _FixedStrategy(MoveAction(MoveDirection.EAST)),
            0,
            random.Random(0),
            MeetingStore(),
        )
        agent = pop.get(1)
        self.assertEqual((agent.cell_x, agent.cell_y), (1, 0))
        self.assertEqual(agent.energy, 8.0)
        self.assertEqual(agent.hp, START_HP - 1)

    def test_blocked_move_counts_as_stay_energy(self) -> None:
        class _Push:
            def choose(self, observation, config, rng):
                if observation.observer_id == 1:
                    return MoveAction(MoveDirection.EAST)
                return MoveAction(MoveDirection.STAY)

            def choose_pd(self, meeting, agent_id, config, rng):
                return PDChoice.COOPERATE

            def choose_continue(self, meeting, agent_id, round_result, config, rng):
                return ContinueChoice.LEAVE

        pop = AgentPopulation()
        pop.place(Agent(id=1, cell_x=0, cell_y=0, energy=10.0))
        pop.place(Agent(id=2, cell_x=1, cell_y=0, energy=10.0))
        pop._next_id = 3
        step_tick(pop, SimulationConfig(), _Push(), 0, random.Random(0), MeetingStore())
        self.assertEqual((pop.get(1).cell_x, pop.get(1).cell_y), (0, 0))
        self.assertEqual(pop.get(1).energy, 9.0)
        self.assertEqual(pop.get(1).hp, START_HP - 1)

    def test_pd_payoffs_go_to_energy_not_hp(self) -> None:
        pop = AgentPopulation()
        pop.place(Agent(id=1, cell_x=0, cell_y=0, energy=10.0))
        pop.place(Agent(id=2, cell_x=1, cell_y=0, energy=10.0))
        pop._next_id = 3
        step_tick(
            pop,
            SimulationConfig(enable_pd=True),
            _FixedStrategy(InteractAction(target_agent_id=-1)),
            0,
            random.Random(0),
            MeetingStore(),
        )
        # stay 1 + interact 1 + game 1 + leave 1, payoff +3 → net −1
        self.assertEqual(pop.get(1).energy, 9.0)
        self.assertEqual(pop.get(2).energy, 9.0)
        self.assertEqual(pop.get(1).hp, START_HP - 1)
        self.assertEqual(pop.get(2).hp, START_HP - 1)

    def test_nondefault_life_rules_drive_spawn_and_tick(self) -> None:
        engine = PythonEngine()
        engine.set_life_rules(
            start_hp_min=15,
            start_hp_max=15,
            hp_tick=1,
            start_energy=20.0,
            energy_move=4,
            energy_stay=0,
            energy_play_decision=0,
            energy_game=0,
            reward=4,
            temptation=7,
            punishment=2,
            sucker=0,
        )
        spawned = engine.generate_agents(1, 1.0)
        self.assertEqual(spawned[0].hp, 15)
        self.assertEqual(spawned[0].energy, 20.0)
        self.assertEqual(engine.config.energy_move, 4)
        self.assertEqual(
            engine.config.payoff_matrix,
            PayoffMatrix(reward=4, temptation=7, punishment=2, sucker=0),
        )

        pop = AgentPopulation()
        pop.place(Agent(id=1, cell_x=0, cell_y=0, hp=15, energy=20.0))
        step_tick(
            pop,
            engine.config,
            _FixedStrategy(MoveAction(MoveDirection.EAST)),
            0,
            random.Random(0),
            MeetingStore(),
        )
        self.assertEqual(pop.get(1).hp, 14)
        self.assertEqual(pop.get(1).energy, 16.0)

        meeting = AgentPopulation()
        meeting.place(Agent(id=1, cell_x=0, cell_y=0, hp=15, energy=0.0))
        meeting.place(Agent(id=2, cell_x=1, cell_y=0, hp=15, energy=0.0))
        step_tick(
            meeting,
            replace(engine.config, enable_pd=True),
            _FixedStrategy(InteractAction(target_agent_id=-1), pd=PDChoice.COOPERATE),
            0,
            random.Random(0),
            MeetingStore(),
        )
        # Action energy costs are 0; mutual cooperate is pure +4 energy.
        self.assertEqual(meeting.get(1).energy, 4.0)
        self.assertEqual(meeting.get(2).energy, 4.0)
        self.assertEqual(meeting.get(1).hp, 14)

    def test_spawn_hp_in_configured_range(self) -> None:
        engine = PythonEngine(seed=7)
        engine.set_life_rules(
            start_hp_min=10,
            start_hp_max=12,
            hp_tick=1,
            start_energy=100.0,
            energy_move=2,
            energy_stay=1,
            energy_play_decision=1,
            energy_game=1,
            reward=3,
            temptation=5,
            punishment=1,
            sucker=0,
        )
        spawned = engine.generate_agents(20, 1.0)
        hps = {agent.hp for agent in spawned}
        self.assertTrue(hps <= {10, 11, 12})
        self.assertGreaterEqual(len(hps), 1)

    def test_pd_disabled_by_default(self) -> None:
        pop = AgentPopulation()
        pop.place(Agent(id=1, cell_x=0, cell_y=0, energy=5.0))
        pop.place(Agent(id=2, cell_x=1, cell_y=0, energy=5.0))
        pop._next_id = 3
        result = step_tick(
            pop,
            SimulationConfig(),
            _FixedStrategy(InteractAction(target_agent_id=-1)),
            0,
            random.Random(0),
            MeetingStore(),
        )
        self.assertEqual(result.interactions, ())
        self.assertEqual(result.meetings_started, ())
        self.assertEqual(result.pd_rounds, ())
        self.assertEqual(pop.get(1).energy, 4.0)
        self.assertEqual(pop.get(1).hp, START_HP - 1)

    def test_zero_hp_removes_agent(self) -> None:
        pop = _one()
        pop.get(1).hp = 1
        step_tick(
            pop,
            SimulationConfig(),
            _FixedStrategy(MoveAction(MoveDirection.STAY)),
            0,
            random.Random(0),
            MeetingStore(),
        )
        self.assertIsNone(pop.get(1))
        self.assertEqual(len(pop), 0)

    def test_zero_energy_removes_agent(self) -> None:
        pop = AgentPopulation()
        pop.place(Agent(id=1, cell_x=0, cell_y=0, energy=0.0))
        step_tick(
            pop,
            SimulationConfig(),
            _FixedStrategy(MoveAction(MoveDirection.EAST)),
            0,
            random.Random(0),
            MeetingStore(),
        )
        self.assertIsNone(pop.get(1))

    def test_energy_spend_floors_then_death_at_zero(self) -> None:
        pop = AgentPopulation()
        pop.place(Agent(id=1, cell_x=0, cell_y=0, energy=1.0))
        step_tick(
            pop,
            SimulationConfig(),
            _FixedStrategy(MoveAction(MoveDirection.EAST)),
            0,
            random.Random(0),
            MeetingStore(),
        )
        # Move costs 2 → floor 0 → death.
        self.assertIsNone(pop.get(1))


if __name__ == "__main__":
    unittest.main()
