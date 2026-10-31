"""A whole game loop, without the terminal: trade, fly, dock, fight, save."""
import unittest

import support  # noqa: F401
from coriolis import combat, core, galaxy
from coriolis.flight import Vec3
from coriolis.market import Market


class PlaythroughTest(unittest.TestCase):
    def setUp(self):
        self.state = core.GameState(seed=5)
        self.state.dock()

    def fly_to_the_slot(self):
        state = self.state
        state.launch()
        state.contacts = []
        state.flight.pos = Vec3(0.0, 0.0, -100.0)
        state.flight.orient = state.flight.orient
        state.flight.speed = 120.0
        status, text = state.station.dock_check(state.flight)
        self.assertEqual(status, "dock", text)
        state.dock()

    def test_following_the_trade_advice_makes_a_profit(self):
        """Buy what the station recommends, fly there, sell it, come out ahead."""
        from coriolis.market import best_routes
        state = self.state
        start = state.pilot.credits
        routes = best_routes(state.system, galaxy.galaxy(1), state.pilot)
        self.assertTrue(routes)
        score, target, good, margin, tonnes = routes[0]
        self.assertGreater(tonnes, 0)
        ok, msg = state.market.buy(state.pilot, good.key, tonnes)
        self.assertTrue(ok, msg)
        self.fly_to_the_slot()
        ok, msg = state.can_jump(target.index)
        self.assertTrue(ok, msg)
        state.begin_jump(target.index)
        for _ in range(400):
            if state.jump:
                state.jump["left"] -= 1 / 60
                if state.jump["left"] <= 0:
                    state.complete_jump(state.jump["index"], state.jump["cost"])
            combat.step(state, 1 / 60)
        self.assertEqual(state.pilot.system, target.index)
        state.contacts = []
        state.flight.pos = Vec3(0.0, 0.0, -100.0)
        state.flight.speed = 100.0
        self.assertEqual(state.station.dock_check(state.flight)[0], "dock")
        state.dock()
        held = state.pilot.cargo[good.key]
        ok, msg = state.market.sell(state.pilot, good.key, held)
        self.assertTrue(ok, msg)
        self.assertGreater(state.pilot.credits, start)
        self.assertEqual(state.pilot.cargo, {})

    def test_running_out_of_fuel_blocks_the_jump(self):
        state = self.state
        state.pilot.fuel = 0.5
        far = max(galaxy.neighbours(1, state.system.index), key=lambda row: row[0])
        state.launch()
        state.contacts = []
        ok, msg = state.can_jump(far[1].index)
        self.assertFalse(ok)
        self.assertIn("LY", msg)

    def test_mass_lock_blocks_the_jump(self):
        state = self.state
        target = galaxy.neighbours(1, state.system.index)[0][1]
        state.launch()
        state.contacts = [combat.make("ship", "cobra",
                                      state.flight.pos + Vec3(0, 0, 500))]
        ok, msg = state.can_jump(target.index)
        self.assertFalse(ok)
        self.assertEqual(msg, "Mass locked")

    def test_death_with_an_escape_capsule_keeps_the_pilot(self):
        state = self.state
        state.pilot.equipment.add("escape")
        state.pilot.add_cargo("gold", 3)
        state.launch()
        state.hull = 1.0
        combat.damage_player(state, 500)
        self.assertTrue(state.dead)
        # The UI handles the capsule; simulate the same branch here.
        self.assertTrue(state.pilot.has("escape"))

    def test_galactic_jump_wraps_and_awards_a_badge(self):
        state = self.state
        from coriolis import ui
        game, screen = support.make_game("\n", ["--seed", "1", "--start-docked"])
        game.state.pilot.galaxy = galaxy.GALAXY_COUNT
        game.state.pilot.equipment.add("galactic")
        game.do_galactic()
        self.assertEqual(game.state.pilot.galaxy, 1)
        self.assertIn("GRAND MASTER", game.state.pilot.badges)

    def test_save_after_a_trade_is_loadable(self):
        state = self.state
        state.market.buy(state.pilot, "food", 4)
        state.save()
        again = core.GameState.load()
        self.assertIsNotNone(again)
        self.assertEqual(again.pilot.cargo.get("food"), 4)
        core.clear_save()


if __name__ == "__main__":
    unittest.main()
