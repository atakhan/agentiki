"""Life points: move, stay, play decision, and the game itself."""

import random
import unittest

from agentiki.sim.actions import InteractAction, MoveAction, MoveDirection
from agentiki.sim.agents import START_HP, Agent, AgentPopulation
from agentiki.sim.config import SimulationConfig
from agentiki.sim.meetings import ContinueChoice, MeetingStore
from agentiki.sim.pd import PDChoice
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


def _one(direction: MoveDirection) -> AgentPopulation:
    pop = AgentPopulation()
    pop.place(Agent(id=1, cell_x=0, cell_y=0))
    pop._next_id = 2
    return pop


class HpTests(unittest.TestCase):
    def test_starts_at_60(self) -> None:
        pop = _one(MoveDirection.STAY)
        self.assertEqual(pop.get(1).hp, START_HP)

    def test_stay_costs_1(self) -> None:
        pop = _one(MoveDirection.STAY)
        step_tick(pop, SimulationConfig(), _FixedStrategy(MoveAction(MoveDirection.STAY)), 0, random.Random(0), MeetingStore())
        self.assertEqual(pop.get(1).hp, START_HP - 1)

    def test_move_costs_2(self) -> None:
        pop = _one(MoveDirection.EAST)
        step_tick(pop, SimulationConfig(), _FixedStrategy(MoveAction(MoveDirection.EAST)), 0, random.Random(0), MeetingStore())
        agent = pop.get(1)
        self.assertEqual((agent.cell_x, agent.cell_y), (1, 0))
        self.assertEqual(agent.hp, START_HP - 2)

    def test_blocked_move_counts_as_stay(self) -> None:
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
        pop.place(Agent(id=1, cell_x=0, cell_y=0))
        pop.place(Agent(id=2, cell_x=1, cell_y=0))
        pop._next_id = 3
        step_tick(pop, SimulationConfig(), _Push(), 0, random.Random(0), MeetingStore())
        self.assertEqual((pop.get(1).cell_x, pop.get(1).cell_y), (0, 0))
        self.assertEqual(pop.get(1).hp, START_HP - 1)

    def test_game_and_decision_cost_extra(self) -> None:
        pop = AgentPopulation()
        pop.place(Agent(id=1, cell_x=0, cell_y=0))
        pop.place(Agent(id=2, cell_x=1, cell_y=0))
        pop._next_id = 3
        step_tick(
            pop,
            SimulationConfig(),
            _FixedStrategy(InteractAction(target_agent_id=-1)),
            0,
            random.Random(0),
            MeetingStore(),
        )
        # stay + interact decision + game + leave decision, plus mutual cooperate +3
        self.assertEqual(pop.get(1).hp, START_HP - 4 + 3)
        self.assertEqual(pop.get(2).hp, START_HP - 4 + 3)

    def test_zero_hp_removes_agent(self) -> None:
        pop = _one(MoveDirection.STAY)
        pop.get(1).hp = 1
        step_tick(pop, SimulationConfig(), _FixedStrategy(MoveAction(MoveDirection.STAY)), 0, random.Random(0), MeetingStore())
        self.assertIsNone(pop.get(1))
        self.assertEqual(len(pop), 0)


if __name__ == "__main__":
    unittest.main()
