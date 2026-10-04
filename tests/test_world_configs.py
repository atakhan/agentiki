"""Save, list, and load named world config files."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agentiki.server.schemas import LifeRulesIn, WorldConfigIn
from agentiki.server.world_configs import (
    list_world_configs,
    load_world_config,
    save_world_config,
)


def _config(name: str, count: int = 12, temptation: int = 9) -> WorldConfigIn:
    return WorldConfigIn(
        name=name,
        count=count,
        density=3,
        life=LifeRulesIn(
            start_hp=40,
            hp_move=4,
            hp_stay=0,
            hp_play_decision=2,
            hp_game=1,
            reward=4,
            temptation=temptation,
            punishment=2,
            sucker=0,
        ),
    )


class WorldConfigStoreTests(unittest.TestCase):
    def test_save_list_load_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            save_world_config(_config("  Альфа  "), root)
            save_world_config(_config("Бета", count=7), root)
            save_world_config(_config("Альфа", count=15), root)

            self.assertEqual(list_world_configs(root), ["Альфа", "Бета"])
            loaded = load_world_config("Альфа", root)
            self.assertEqual(loaded.name, "Альфа")
            self.assertEqual(loaded.count, 15)
            self.assertEqual(loaded.density, 3)
            self.assertEqual(loaded.life.start_hp, 40)
            self.assertEqual(loaded.life.hp_move, 4)
            self.assertEqual(loaded.life.temptation, 9)
            self.assertEqual(loaded.life.reward, 4)
            self.assertTrue((root / "Альфа.json").is_file())

    def test_bad_payoff_order_is_rejected_and_not_written(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(ValueError) as raised:
                save_world_config(_config("Сломан", temptation=1), root)
            self.assertIn("предатель", str(raised.exception))
            self.assertEqual(list_world_configs(root), [])
            self.assertEqual(list(root.glob("*.json")), [])

    def test_bad_name_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(ValueError):
                save_world_config(_config("a/b"), root)
            self.assertEqual(list_world_configs(root), [])


if __name__ == "__main__":
    unittest.main()
