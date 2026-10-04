"""Named world configs: one JSON file per name.

These are spawn settings (count, density, life rules), not a running world.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from agentiki.server.schemas import WorldConfigIn
from agentiki.sim.pd import PayoffMatrix

DEFAULT_DIR = Path(__file__).resolve().parents[3] / "data" / "world_configs"
PAYOFF_ORDER_ERROR = "Приток: предатель > оба C > оба D > кооператор"


def configs_dir(root: Path | None = None) -> Path:
    if root is not None:
        return root
    env = os.environ.get("AGENTIKI_CONFIG_DIR")
    if env:
        return Path(env)
    return DEFAULT_DIR


def normalize_name(name: str) -> str:
    cleaned = name.strip()
    if (
        not cleaned
        or cleaned in {".", ".."}
        or len(cleaned) > 80
        or any(char in cleaned for char in "/\\\0")
    ):
        raise ValueError("Недопустимое имя мира")
    return cleaned


def _check_payoff(config: WorldConfigIn) -> None:
    life = config.life
    try:
        PayoffMatrix(
            reward=life.reward,
            temptation=life.temptation,
            punishment=life.punishment,
            sucker=life.sucker,
        )
    except ValueError as exc:
        raise ValueError(PAYOFF_ORDER_ERROR) from exc


def _path(name: str, root: Path) -> Path:
    return root / f"{name}.json"


def save_world_config(config: WorldConfigIn, root: Path | None = None) -> WorldConfigIn:
    name = normalize_name(config.name)
    stored = config.model_copy(update={"name": name})
    _check_payoff(stored)
    directory = configs_dir(root)
    directory.mkdir(parents=True, exist_ok=True)
    payload = stored.model_dump()
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    _path(name, directory).write_text(text, encoding="utf-8")
    return stored


def list_world_configs(root: Path | None = None) -> list[str]:
    directory = configs_dir(root)
    if not directory.is_dir():
        return []
    names: list[str] = []
    for path in directory.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            names.append(normalize_name(str(data["name"])))
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
            continue
    return sorted(set(names), key=str.casefold)


def load_world_config(name: str, root: Path | None = None) -> WorldConfigIn:
    cleaned = normalize_name(name)
    path = _path(cleaned, configs_dir(root))
    if not path.is_file():
        raise FileNotFoundError(cleaned)
    data = json.loads(path.read_text(encoding="utf-8"))
    return WorldConfigIn.model_validate(data)
