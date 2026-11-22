"""Genetic scales v0.1: scoring, window, cost, and genome round-trip."""

from __future__ import annotations

import random
import unittest
from collections.abc import Sequence

from agentiki.sim.agents import Agent
from agentiki.sim.genetics import (
    SHVGOP_MAX,
    Genome,
    OpponentMemory,
    decide_against,
    evaluate_opponent,
)
from agentiki.sim.pd import PDChoice

C = PDChoice.COOPERATE
D = PDChoice.DEFECT


class _FixedRng(random.Random):
    def __init__(self, value: float) -> None:
        super().__init__(0)
        self._value = value

    def random(self) -> float:
        return self._value


class _UnreadHistory(Sequence[PDChoice]):
    """Any read is a failure. Used when ШВГОП is 0."""

    def __len__(self) -> int:
        raise AssertionError("history must not be read when shvgop is 0")

    def __getitem__(self, index: int) -> PDChoice:
        raise AssertionError("history must not be read when shvgop is 0")


def _genome(shvgop: int, shpm: float, shz: float) -> Genome:
    return Genome(shvgop=shvgop, shpm=shpm, shz=shz)


class GenomeBoundsTests(unittest.TestCase):
    def test_bounds_accept_endpoints(self) -> None:
        genome = _genome(0, -1, 0)
        self.assertEqual(genome.shvgop, 0)
        self.assertEqual(genome.shpm, -1.0)
        self.assertEqual(genome.shz, 0.0)
        top = _genome(SHVGOP_MAX, 1, 1)
        self.assertEqual(top.shvgop, SHVGOP_MAX)
        self.assertEqual(top.shpm, 1.0)
        self.assertEqual(top.shz, 1.0)

    def test_rejects_out_of_range_and_non_finite(self) -> None:
        for kwargs in (
            {"shvgop": -1, "shpm": 0, "shz": 0},
            {"shvgop": SHVGOP_MAX + 1, "shpm": 0, "shz": 0},
            {"shvgop": 0, "shpm": -1.01, "shz": 0},
            {"shvgop": 0, "shpm": 1.01, "shz": 0},
            {"shvgop": 0, "shpm": 0, "shz": -0.01},
            {"shvgop": 0, "shpm": 0, "shz": 1.01},
            {"shvgop": 0, "shpm": float("nan"), "shz": 0},
            {"shvgop": 0, "shpm": 0, "shz": float("inf")},
        ):
            with self.assertRaises(ValueError):
                Genome(**kwargs)

    def test_rejects_bool_and_non_numeric(self) -> None:
        with self.assertRaises(TypeError):
            Genome(shvgop=True, shpm=0, shz=0)
        with self.assertRaises(TypeError):
            Genome(shvgop=1, shpm="0", shz=0)  # type: ignore[arg-type]


class SpecTableTests(unittest.TestCase):
    """Rows from specification §9.

    Row 1 is written «ШПМ0» in the source table and row 2 is absent. Row 3 is
    the ``p = 0`` coin flip, and §3.2 maps ``p > 0`` to defect, so row 1 is
    implemented as ШВГОП=0 and p>0.
    """

    def test_row_1_no_history_positive_shpm_defects(self) -> None:
        decision = evaluate_opponent(_genome(0, 1, 0), _UnreadHistory(), _FixedRng(0.0))
        self.assertEqual(decision.action, D)
        self.assertFalse(decision.random_tie)
        self.assertIsNone(decision.score)
        self.assertEqual(decision.cognitive_cost, 0)

    def test_no_history_negative_shpm_cooperates(self) -> None:
        decision = evaluate_opponent(_genome(0, -1, 1), (D, D, D), _FixedRng(0.99))
        self.assertEqual(decision.action, C)
        self.assertFalse(decision.random_tie)
        self.assertEqual(decision.cognitive_cost, 0)

    def test_row_3_no_history_neutral_shpm_is_fair_coin(self) -> None:
        low = evaluate_opponent(_genome(0, 0, 1), _UnreadHistory(), _FixedRng(0.0))
        high = evaluate_opponent(_genome(0, 0, 1), _UnreadHistory(), _FixedRng(0.5))
        self.assertEqual(low.action, C)
        self.assertEqual(high.action, D)
        self.assertTrue(low.random_tie)
        self.assertTrue(high.random_tie)
        self.assertIsNone(low.score)
        self.assertEqual(low.cognitive_cost, 0)

    def test_row_4_last_cooperate(self) -> None:
        decision = evaluate_opponent(_genome(1, 0, 0.3), (D, C), random.Random(0))
        self.assertEqual(decision.action, C)
        self.assertEqual(decision.score, -1.0)
        self.assertEqual(decision.cognitive_cost, 1)

    def test_row_5_last_defect(self) -> None:
        decision = evaluate_opponent(_genome(1, 0, 1), (C, D), random.Random(0))
        self.assertEqual(decision.action, D)
        self.assertEqual(decision.score, 1.0)
        self.assertEqual(decision.cognitive_cost, 1)

    def test_row_6_balanced_window_is_a_tie(self) -> None:
        history = (C, D)
        low = evaluate_opponent(_genome(2, 0, 1), history, _FixedRng(0.0))
        high = evaluate_opponent(_genome(2, 0, 1), history, _FixedRng(0.5))
        self.assertEqual(low.score, 0.0)
        self.assertEqual(high.score, 0.0)
        self.assertTrue(low.random_tie)
        self.assertEqual(low.action, C)
        self.assertEqual(high.action, D)
        self.assertEqual(low.cognitive_cost, 2)

    def test_row_7_zero_memory_uses_only_the_newest_defect(self) -> None:
        decision = evaluate_opponent(_genome(2, 0, 0), (C, D), random.Random(0))
        self.assertEqual(decision.score, 1.0)
        self.assertEqual(decision.action, D)

    def test_row_8_moderate_decay_still_defects(self) -> None:
        decision = evaluate_opponent(_genome(3, 0, 0.5), (C, C, D), random.Random(0))
        self.assertEqual(decision.score, 0.25)
        self.assertEqual(decision.action, D)
        self.assertEqual(decision.cognitive_cost, 3)

    def test_row_9_full_memory_cooperates_and_score_is_a_sum(self) -> None:
        decision = evaluate_opponent(_genome(3, 0, 1), (C, C, D), random.Random(0))
        self.assertEqual(decision.score, -1.0)
        self.assertNotEqual(decision.score, -1.0 / 3.0)
        self.assertEqual(decision.action, C)

    def test_row_10_short_history_uses_the_only_episode(self) -> None:
        cooperated = evaluate_opponent(_genome(3, 0, 1), (C,), random.Random(0))
        defected = evaluate_opponent(_genome(3, 0, 0), (D,), random.Random(0))
        self.assertEqual(cooperated.action, C)
        self.assertEqual(cooperated.cognitive_cost, 1)
        self.assertEqual(defected.action, D)
        self.assertEqual(defected.cognitive_cost, 1)

    def test_row_11_forgiveness_cancels_a_defect(self) -> None:
        decision = evaluate_opponent(_genome(1, -1, 1), (D,), _FixedRng(0.0))
        self.assertEqual(decision.score, 0.0)
        self.assertTrue(decision.random_tie)
        self.assertEqual(decision.action, C)
        other = evaluate_opponent(_genome(1, -1, 1), (D,), _FixedRng(0.5))
        self.assertEqual(other.action, D)

    def test_row_12_revenge_cancels_cooperation(self) -> None:
        decision = evaluate_opponent(_genome(4, 1, 1), (C,), _FixedRng(0.5))
        self.assertEqual(decision.score, 0.0)
        self.assertTrue(decision.random_tie)
        self.assertEqual(decision.action, D)


class WorkedExampleTests(unittest.TestCase):
    def test_example_a_decay_changes_the_sign(self) -> None:
        history = (C, C, D)
        zero = evaluate_opponent(_genome(3, 0, 0), history, random.Random(0))
        half = evaluate_opponent(_genome(3, 0, 0.5), history, random.Random(0))
        one = evaluate_opponent(_genome(3, 0, 1), history, random.Random(0))
        self.assertEqual((zero.score, zero.action), (1.0, D))
        self.assertEqual((half.score, half.action), (0.25, D))
        self.assertEqual((one.score, one.action), (-1.0, C))

    def test_example_b_window_depth_changes_the_action(self) -> None:
        history = (C, C, D)
        first = evaluate_opponent(_genome(1, 0, 1), history, random.Random(0))
        second = evaluate_opponent(_genome(2, 0, 1), history, _FixedRng(0.0))
        third = evaluate_opponent(_genome(3, 0, 1), history, random.Random(0))
        self.assertEqual(first.action, D)
        self.assertEqual(second.score, 0.0)
        self.assertTrue(second.random_tie)
        self.assertEqual(third.action, C)

    def test_example_c_shpm_flips_the_same_history(self) -> None:
        history = (C, D)
        forgive = evaluate_opponent(_genome(2, -1, 1), history, random.Random(0))
        neutral = evaluate_opponent(_genome(2, 0, 1), history, _FixedRng(0.0))
        revenge = evaluate_opponent(_genome(2, 1, 1), history, random.Random(0))
        self.assertEqual((forgive.score, forgive.action), (-2.0, C))
        self.assertEqual(neutral.score, 0.0)
        self.assertTrue(neutral.random_tie)
        self.assertEqual((revenge.score, revenge.action), (2.0, D))

    def test_neutral_coin_is_about_even(self) -> None:
        rng = random.Random(1)
        actions = [
            evaluate_opponent(_genome(0, 0, 0), (), rng).action for _ in range(2000)
        ]
        cooperates = actions.count(C)
        self.assertGreater(cooperates, 900)
        self.assertLess(cooperates, 1100)
        self.assertIn(D, actions)


class HistoryAndCostTests(unittest.TestCase):
    def test_zero_horizon_does_not_read_history_or_memory(self) -> None:
        memory = OpponentMemory()
        memory.record(7, D)
        decision = decide_against(_genome(0, 1, 1), memory, 7, random.Random(0))
        self.assertEqual(memory.extractions, 0)
        self.assertEqual(decision.action, D)
        self.assertEqual(decision.cognitive_cost, 0)
        evaluate_opponent(_genome(0, -0.2, 0.4), _UnreadHistory(), random.Random(0))

    def test_cost_is_episodes_actually_read(self) -> None:
        memory = OpponentMemory()
        for action in (C, D, C):
            memory.record(4, action)
        decision = decide_against(_genome(5, 0, 1), memory, 4, random.Random(0))
        self.assertEqual(memory.extractions, 1)
        self.assertEqual(decision.cognitive_cost, 3)
        self.assertEqual(decision.action, C)
        absent = decide_against(_genome(5, -1, 1), memory, 99, random.Random(0))
        self.assertEqual(absent.cognitive_cost, 0)
        self.assertEqual(absent.action, C)

    def test_cost_never_negative(self) -> None:
        memory = OpponentMemory()
        for _ in range(4):
            memory.record(1, D)
        for horizon in range(0, 8):
            decision = decide_against(
                _genome(horizon, 0.25, 0.5), memory, 1, random.Random(0)
            )
            self.assertGreaterEqual(decision.cognitive_cost, 0)
            self.assertLessEqual(decision.cognitive_cost, horizon)
            self.assertLessEqual(decision.cognitive_cost, 4)

    def test_order_is_oldest_to_newest(self) -> None:
        # λ=0 keeps only the newest episode. Reversing the log would defect.
        decision = evaluate_opponent(_genome(2, 0, 0), (D, C), random.Random(0))
        self.assertEqual(decision.action, C)
        self.assertEqual(decision.score, -1.0)

    def test_long_history_uses_only_the_window(self) -> None:
        history = (C,) * 10_000 + (D,)
        kept = evaluate_opponent(
            _genome(SHVGOP_MAX, 0, 1), history, random.Random(0)
        )
        self.assertEqual(kept.cognitive_cost, SHVGOP_MAX)
        self.assertEqual(kept.score, float(-(SHVGOP_MAX - 1) + 1))
        self.assertEqual(kept.action, C)
        newest = evaluate_opponent(
            _genome(SHVGOP_MAX, 0, 0), history, random.Random(0)
        )
        self.assertEqual(newest.score, 1.0)
        self.assertEqual(newest.action, D)
        self.assertEqual(newest.cognitive_cost, SHVGOP_MAX)

    def test_memory_keeps_chronological_order(self) -> None:
        memory = OpponentMemory()
        memory.record(3, D)
        memory.record(3, C)
        self.assertEqual(memory.last(3, 2), (D, C))
        self.assertEqual(memory.last(3, 0), ())
        self.assertEqual(memory.extractions, 1)


class GenomePersistenceTests(unittest.TestCase):
    def test_agent_json_and_bytes_round_trip(self) -> None:
        genome = _genome(5, -0.5, 0.25)
        agent = Agent(id=3, cell_x=1, cell_y=2, hp=40, energy=12.5, genome=genome)
        restored = Genome.from_json(agent.genome.to_json())
        loaded = Agent(
            id=agent.id,
            cell_x=agent.cell_x,
            cell_y=agent.cell_y,
            hp=agent.hp,
            energy=agent.energy,
            genome=restored,
        )
        self.assertEqual(loaded.genome, genome)
        self.assertEqual(Genome.from_bytes(genome.to_bytes()), genome)
        self.assertEqual(Genome.from_dict(genome.to_dict()), genome)

    def test_rejects_corrupt_payloads(self) -> None:
        with self.assertRaises(ValueError):
            Genome.from_dict({"shvgop": 1, "shpm": 0})
        with self.assertRaises(ValueError):
            Genome.from_dict({"shvgop": 1, "shpm": 0, "shz": 0, "extra": 1})
        with self.assertRaises(ValueError):
            Genome.from_bytes(b"nope")
        with self.assertRaises(ValueError):
            Genome.from_json('{"shvgop": 1, "shpm": 2, "shz": 0}')


if __name__ == "__main__":
    unittest.main()
