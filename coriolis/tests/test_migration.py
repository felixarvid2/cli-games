"""Save compatibility: migration, damaged files and the random state."""
import json
import os
import tempfile
import unittest

import support
from coriolis import core, galaxy

V1_SAVE = {
    "version": 1,
    "pilot": {"name": "Jameson", "credits": 420.0, "fuel": 5.0,
              "cargo": {"food": 6, "furs": 2}, "cargo_cap": 35,
              "equipment": ["ecm", "largebay"], "missiles": 2,
              "kills": 12, "legal": 0, "galaxy": 2, "system": 33,
              "badges": ["OLD"], "deaths": 1, "jumps": 9},
    "flight": {"pos": [0, 0, -6000], "speed": 120.0,
               "orient": [[1, 0, 0], [0, 1, 0], [0, 0, 1]]},
    "hull": 72.0, "shields": {"fore": 40.0, "aft": 55.0},
    "banks": [12.0, 25.0, 25.0, 25.0], "mode": "docked",
}


class MigrationTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "save.json")

    def write(self, payload):
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh)

    def test_version_one_save_loads_with_everything_intact(self):
        self.write(V1_SAVE)
        state, reason = core.GameState.load_with_reason(self.path)
        self.assertIsNotNone(state, reason)
        self.assertEqual(state.pilot.credits, 420.0)
        self.assertEqual(state.pilot.cargo, {"food": 6, "furs": 2})
        self.assertEqual(state.pilot.equipment, {"ecm", "largebay"})
        self.assertEqual(state.pilot.kills, 12)
        self.assertEqual(state.pilot.galaxy, 2)
        self.assertEqual(state.pilot.system, 33)
        self.assertEqual(state.hull, 72.0)
        self.assertEqual(state.mode, "docked")

    def test_migration_fills_in_the_new_fields(self):
        self.write(V1_SAVE)
        state, _ = core.GameState.load_with_reason(self.path)
        self.assertEqual(state.pilot.ship, "cobra")
        self.assertEqual(state.pilot.cargo_cap, 35)
        self.assertIn("2:33", state.pilot.visited)
        self.assertTrue(state.pilot.tutorial.get("done"))
        self.assertFalse(state.pilot.missions)
        self.assertEqual(state.pilot.trade_profit, 0.0)
        self.assertEqual(state.markets, {})

    def test_newer_save_is_refused_and_explained(self):
        payload = dict(V1_SAVE)
        payload["version"] = core.SAVE_VERSION + 5
        self.write(payload)
        state, reason = core.GameState.load_with_reason(self.path)
        self.assertIsNone(state)
        self.assertIn("newer", reason)

    def test_damaged_save_is_refused_and_left_alone(self):
        with open(self.path, "w", encoding="utf-8") as fh:
            fh.write("{broken")
        state, reason = core.GameState.load_with_reason(self.path)
        self.assertIsNone(state)
        self.assertIn("damaged", reason)
        self.assertTrue(os.path.exists(self.path))

    def test_saving_over_a_damaged_file_keeps_a_backup(self):
        with open(self.path, "w", encoding="utf-8") as fh:
            fh.write("{broken")
        state = core.GameState(seed=1)
        state.dock()
        state.save(self.path)
        self.assertTrue(os.path.exists(self.path + ".bad"))
        again, _ = core.GameState.load_with_reason(self.path)
        self.assertIsNotNone(again)

    def test_missing_save_says_so(self):
        state, reason = core.GameState.load_with_reason(self.path)
        self.assertIsNone(state)
        self.assertIn("No saved game", reason)

    def test_random_state_survives_a_reload(self):
        state = core.GameState(seed=None)
        state.rng.seed(1234)
        state.dock()
        state.save(self.path)
        first = [round(state.rng.random(), 6) for _ in range(3)]
        again, _ = core.GameState.load_with_reason(self.path)
        second = [round(again.rng.random(), 6) for _ in range(3)]
        self.assertEqual(first, second)

    def test_a_full_v2_round_trip(self):
        game, _ = support.make_game("\n", ["--seed", "1"])
        state = game.state
        state.pilot.trade_profit = 240.0
        state.pilot.visit(1, 40)
        state.dock()
        state.save(self.path)
        again, reason = core.GameState.load_with_reason(self.path)
        self.assertIsNotNone(again, reason)
        self.assertEqual(again.pilot.trade_profit, 240.0)
        self.assertIn("1:40", again.pilot.visited)
        self.assertEqual(again.pilot.ship, state.pilot.ship)


if __name__ == "__main__":
    unittest.main()
