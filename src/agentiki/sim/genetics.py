"""Genetic scales: how an agent scores an opponent from past episodes.

The three genes (ШВГОП / ШПМ / ШЗ) are a value object. This module scores
history and picks cooperate or defect. It does not mutate genes, inherit
them, draw a starting distribution, or spend energy. Those rules are outside
specification v0.1. Cognitive cost is reported and is not subtracted from
``Agent.energy``.

History passed to :func:`evaluate_opponent` is oldest episode first.
"""

from __future__ import annotations

import json
import math
import random
import struct
from dataclasses import dataclass
from typing import Sequence

from agentiki.sim.pd import PDChoice

# The specification requires a finite range ``0 … N_max`` and does not assign
# ``N_max``. 256 is the v0.1 bound: long enough for a memory experiment, small
# enough that a gene stays a bounded integer.
SHVGOP_MAX = 256

_MAGIC = b"AGN1"
_PACK = struct.Struct("<idd")
_DICT_KEYS = frozenset({"shvgop", "shpm", "shz"})


def _bounded_float(name: str, value: object, low: float, high: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a real number")
    number = float(value)
    if not math.isfinite(number) or number < low or number > high:
        raise ValueError(f"{name} must be in [{low}, {high}]")
    return number


@dataclass(frozen=True, slots=True)
class Genome:
    """Inherited scales. Not edited during an agent's life by this module.

    ``shvgop`` (ШВГОП) — how many past episodes to read, ``0 … SHVGOP_MAX``.
    ``shpm`` (ШПМ) — forgiveness–revenge, ``[-1, 1]``.
    ``shz`` (ШЗ) — how fast older episodes fade, ``[0, 1]``.
    """

    shvgop: int
    shpm: float
    shz: float

    def __post_init__(self) -> None:
        if isinstance(self.shvgop, bool) or not isinstance(self.shvgop, int):
            raise TypeError("shvgop must be an int")
        if not 0 <= self.shvgop <= SHVGOP_MAX:
            raise ValueError(f"shvgop must be in [0, {SHVGOP_MAX}]")
        object.__setattr__(self, "shpm", _bounded_float("shpm", self.shpm, -1.0, 1.0))
        object.__setattr__(self, "shz", _bounded_float("shz", self.shz, 0.0, 1.0))

    def to_dict(self) -> dict[str, int | float]:
        return {"shvgop": self.shvgop, "shpm": self.shpm, "shz": self.shz}

    @classmethod
    def from_dict(cls, payload: object) -> Genome:
        if not isinstance(payload, dict) or set(payload) != _DICT_KEYS:
            raise ValueError("genome payload must contain shvgop, shpm, shz")
        return cls(
            shvgop=payload["shvgop"],
            shpm=payload["shpm"],
            shz=payload["shz"],
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), allow_nan=False, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> Genome:
        return cls.from_dict(json.loads(text))

    def to_bytes(self) -> bytes:
        return _MAGIC + _PACK.pack(self.shvgop, self.shpm, self.shz)

    @classmethod
    def from_bytes(cls, data: bytes) -> Genome:
        if len(data) != len(_MAGIC) + _PACK.size or not data.startswith(_MAGIC):
            raise ValueError("invalid genome bytes")
        shvgop, shpm, shz = _PACK.unpack(data[len(_MAGIC) :])
        return cls(shvgop=shvgop, shpm=shpm, shz=shz)


@dataclass(frozen=True, slots=True)
class OpponentDecision:
    """One evaluation of a single opponent.

    ``score`` is ``None`` when the initial ШПМ rule is used (no episodes).
    ``random_tie`` is set when the specification calls for a fair coin flip
    (``p = 0`` with no history, or ``S = 0``). ``action`` is the flip's result.
    ``cognitive_cost`` equals the number of episodes actually read and is
    never negative.
    """

    action: PDChoice
    score: float | None
    cognitive_cost: int
    random_tie: bool


class OpponentMemory:
    """Per-opponent log of the opponent's actions, oldest first.

    ``last(opponent_id, 0)`` returns an empty window and does not touch the log.
    """

    def __init__(self) -> None:
        self._episodes: dict[int, list[PDChoice]] = {}
        self.extractions = 0

    def record(self, opponent_id: int, opponent_action: PDChoice) -> None:
        if opponent_action is not PDChoice.COOPERATE and opponent_action is not PDChoice.DEFECT:
            raise TypeError("opponent_action must be a PDChoice")
        self._episodes.setdefault(opponent_id, []).append(opponent_action)

    def last(self, opponent_id: int, n: int) -> tuple[PDChoice, ...]:
        if n <= 0:
            return ()
        self.extractions += 1
        episodes = self._episodes.get(opponent_id)
        if not episodes:
            return ()
        if n >= len(episodes):
            return tuple(episodes)
        return tuple(episodes[-n:])


def behavioral_weight(action: PDChoice, shpm: float) -> float:
    """``w(x, p) = x (1 + p x)`` with cooperate = −1 and defect = +1."""
    if action is PDChoice.COOPERATE:
        x = -1.0
    elif action is PDChoice.DEFECT:
        x = 1.0
    else:
        raise TypeError("action must be a PDChoice")
    return x * (1.0 + shpm * x)


def temporal_weight(episodes_after: int, shz: float) -> float:
    """Weight ``λ^{episodes_after}``. The newest episode has age 0 and weight 1.

    ``λ = 0`` gives weight 0 to every older episode. Age 0 stays 1, including
    the ``0^0`` case.
    """
    if episodes_after < 0:
        raise ValueError("episodes_after must be >= 0")
    if episodes_after == 0:
        return 1.0
    if shz == 0.0:
        return 0.0
    return shz**episodes_after


def select_episodes(history: Sequence[PDChoice], n: int) -> tuple[PDChoice, ...]:
    """Last ``n`` episodes, oldest first.

    ``n <= 0`` returns an empty window and does not read ``history``.
    A shorter log is returned in full.
    """
    if n <= 0:
        return ()
    length = len(history)
    if length == 0:
        return ()
    if n >= length:
        return tuple(history)
    return tuple(history[-n:])


def _coin_flip(rng: random.Random) -> PDChoice:
    if rng.random() < 0.5:
        return PDChoice.COOPERATE
    return PDChoice.DEFECT


def _initial_action(shpm: float, rng: random.Random) -> OpponentDecision:
    if shpm < 0.0:
        action = PDChoice.COOPERATE
        tie = False
    elif shpm > 0.0:
        action = PDChoice.DEFECT
        tie = False
    else:
        action = _coin_flip(rng)
        tie = True
    return OpponentDecision(
        action=action,
        score=None,
        cognitive_cost=0,
        random_tie=tie,
    )


def evaluate_opponent(
    genome: Genome,
    history: Sequence[PDChoice],
    rng: random.Random,
) -> OpponentDecision:
    """Score ``history`` with the three scales and choose an action.

    ``history`` is oldest → newest and may be longer than ШВГОП. When ШВГОП
    is 0 the history object is not read. The total is a sum, not a mean.
    """
    episodes = select_episodes(history, genome.shvgop)
    if not episodes:
        return _initial_action(genome.shpm, rng)

    count = len(episodes)
    score = 0.0
    for index, action in enumerate(episodes):
        age = count - 1 - index
        score += temporal_weight(age, genome.shz) * behavioral_weight(action, genome.shpm)

    if score > 0.0:
        action = PDChoice.DEFECT
        tie = False
    elif score < 0.0:
        action = PDChoice.COOPERATE
        tie = False
    else:
        action = _coin_flip(rng)
        tie = True
    return OpponentDecision(
        action=action,
        score=score,
        cognitive_cost=count,
        random_tie=tie,
    )


def decide_against(
    genome: Genome,
    memory: OpponentMemory,
    opponent_id: int,
    rng: random.Random,
) -> OpponentDecision:
    """Evaluate one opponent from that agent's memory of them."""
    episodes = memory.last(opponent_id, genome.shvgop)
    return evaluate_opponent(genome, episodes, rng)
