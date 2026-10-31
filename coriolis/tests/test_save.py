import json
import os
import tempfile
import unittest

import support  # noqa: F401
from coriolis import core


class SaveTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "save.json")

    def test_round_trip(self):
        state = core.GameState(seed=7)
        state.pilot.credits = 1234.5
        state.pilot.cargo = {"food": 3, "furs": 2}
        state.pilot.equipment = {"ecm", "beam"}
        state.pilot.kills = 40
        state.pilot.legal = 60
        state.pilot.galaxy = 4
        state.pilot.system = 99
        state.hull = 61.5
        state.save(self.path)
        again = core.GameState.load(self.path)
        self.assertIsNotNone(again)
        self.assertEqual(again.pilot.credits, 1234.5)
        self.assertEqual(again.pilot.cargo, {"food": 3, "furs": 2})
        self.assertEqual(again.pilot.equipment, {"ecm", "beam"})
        self.assertEqual(again.pilot.kills, 40)
        self.assertEqual(again.pilot.legal_name, "Fugitive")
        self.assertEqual(again.pilot.galaxy, 4)
        self.assertEqual(again.pilot.system, 99)
        self.assertEqual(again.hull, 61.5)
        self.assertEqual(again.system.name, core.GameState.load(self.path).system.name)

    def test_save_is_atomic_and_leaves_no_temp_file(self):
        state = core.GameState(seed=1)
        state.save(self.path)
        self.assertTrue(os.path.exists(self.path))
        self.assertFalse(os.path.exists(self.path + ".tmp"))

    def test_missing_file_loads_as_none(self):
        self.assertIsNone(core.GameState.load(os.path.join(self.dir, "nope.json")))

    def test_corrupt_file_loads_as_none(self):
        with open(self.path, "w", encoding="utf-8") as fh:
            fh.write("{not json")
        self.assertIsNone(core.GameState.load(self.path))

    def test_wrong_version_is_refused(self):
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump({"version": core.SAVE_VERSION + 9, "pilot": {}}, fh)
        self.assertIsNone(core.GameState.load(self.path))

    def test_profile_round_trip(self):
        path = os.path.join(self.dir, "profile.json")
        profile = core.Profile(kills=99, deaths=2, badges=["GRAND MASTER"],
                               best_rank="Competent")
        core.save_profile(profile, path)
        again = core.load_profile(path)
        self.assertEqual(again.kills, 99)
        self.assertEqual(again.deaths, 2)
        self.assertEqual(again.badges, ["GRAND MASTER"])
        self.assertEqual(again.best_rank, "Competent")

    def test_clear_save(self):
        state = core.GameState(seed=1)
        state.save(self.path)
        self.assertTrue(core.clear_save(self.path))
        self.assertFalse(os.path.exists(self.path))
        self.assertFalse(core.clear_save(self.path))

    def test_docked_state_reloads_docked(self):
        state = core.GameState(seed=1)
        state.launch()
        state.dock()
        state.save(self.path)
        again = core.GameState.load(self.path)
        self.assertEqual(again.mode, "docked")


if __name__ == "__main__":
    unittest.main()
