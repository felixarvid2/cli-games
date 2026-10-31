"""Purchasable hulls: validation, trade-in, and what the ship changes."""
import unittest

import support
from coriolis import core, station as st
from coriolis.ships import PLAYER_SHIPS


def rich_pilot(credits=40000.0, ship="cobra"):
    pilot = core.Pilot()
    pilot.credits = credits
    pilot.ship = ship
    return pilot


class ShipyardTest(unittest.TestCase):
    def test_five_hulls_are_for_sale(self):
        pilot = rich_pilot()
        rows = st.shipyard_rows(pilot)
        self.assertEqual(len(rows), 5)
        names = [row[1].name for row in rows]
        self.assertEqual(len(set(names)), 5)

    def test_hulls_differ_in_the_things_that_matter(self):
        cfg = PLAYER_SHIPS
        self.assertNotEqual(cfg["adder"].cargo, cfg["cobra"].cargo)
        self.assertGreater(cfg["moray"].max_speed, cfg["adder"].max_speed)
        self.assertGreater(cfg["ferdl"].shields, cfg["moray"].shields)
        self.assertLess(cfg["ferdl"].cargo, cfg["adder"].cargo)
        self.assertGreater(cfg["asp"].slots, cfg["moray"].slots)

    def test_buying_deducts_the_price_and_swaps_the_hull(self):
        pilot = rich_pilot(20000.0)
        cost = 5200.0 - 3200.0 * 0.6
        ok, msg = st.buy_ship(pilot, "adder")
        self.assertTrue(ok, msg)
        self.assertEqual(pilot.ship, "adder")
        self.assertAlmostEqual(pilot.credits, 20000.0 - cost, places=1)
        self.assertEqual(pilot.cargo_cap, PLAYER_SHIPS["adder"].cargo)

    def test_cannot_buy_without_credits(self):
        pilot = rich_pilot(10.0)
        ok, msg = st.buy_ship(pilot, "ferdl")
        self.assertFalse(ok)
        self.assertIn("CR", msg)
        self.assertEqual(pilot.ship, "cobra")

    def test_cannot_buy_a_hull_too_small_for_the_cargo(self):
        pilot = rich_pilot()
        pilot.add_cargo("food", 18)          # Adder holds 40, Moray only 12
        ok, msg = st.buy_ship(pilot, "moray")
        self.assertFalse(ok)
        self.assertIn("Hold too small", msg)

    def test_cannot_buy_a_hull_with_too_few_equipment_slots(self):
        pilot = rich_pilot()
        pilot.equipment = {"ecm", "beam", "scoop", "docking", "energy",
                           "bomb", "escape", "largebay"}
        ok, msg = st.buy_ship(pilot, "adder")     # 7 slots, 8 items
        self.assertFalse(ok)
        self.assertIn("slots", msg)

    def test_cannot_buy_a_hull_that_cannot_carry_the_missiles(self):
        racks = PLAYER_SHIPS["asp"].missiles
        pilot = rich_pilot()
        pilot.ship = "ferdl"
        pilot.missiles = racks
        ok, msg = st.buy_ship(pilot, "asp")
        self.assertTrue(ok, msg)

        too_many = PLAYER_SHIPS["moray"].missiles + 1
        pilot = rich_pilot()
        pilot.ship = "asp"
        pilot.missiles = too_many
        ok, msg = st.buy_ship(pilot, "moray")
        self.assertFalse(ok)
        self.assertIn("missiles", msg)

    def test_selling_missiles_makes_room(self):
        pilot = rich_pilot(20000.0)
        pilot.missiles = 4
        pilot.ship = "asp"                     # keeps 4
        pilot.credits = 20000.0
        ok, _ = st.sell_missile(pilot)
        self.assertTrue(ok)
        self.assertEqual(pilot.missiles, 3)
        self.assertGreater(pilot.credits, 20000.0)

    def test_trade_in_never_pays_the_player(self):
        pilot = rich_pilot(20000.0)
        self.assertTrue(st.buy_ship(pilot, "ferdl")[0])
        after_buy = pilot.credits
        ok, _ = st.buy_ship(pilot, "cobra")     # downgrade
        self.assertTrue(ok)
        self.assertLessEqual(pilot.credits, after_buy)
        self.assertEqual(pilot.credits, after_buy)

    def test_swapping_ships_back_and_forth_loses_money(self):
        pilot = rich_pilot(40000.0)
        start = pilot.credits
        st.buy_ship(pilot, "adder")
        st.buy_ship(pilot, "cobra")
        self.assertLess(pilot.credits, start)

    def test_the_new_hull_changes_the_flight_model(self):
        game, _ = support.make_game("\n", ["--seed", "1", "--start-docked"])
        game.state.pilot.credits = 20000.0
        self.assertTrue(st.buy_ship(game.state.pilot, "moray")[0])
        game.state.apply_ship()
        self.assertEqual(game.state.flight.max_speed, PLAYER_SHIPS["moray"].max_speed)
        self.assertEqual(game.state.hull_max, PLAYER_SHIPS["moray"].hull)
        self.assertEqual(game.state.shield_max, PLAYER_SHIPS["moray"].shields)

    def test_hud_limits_follow_the_ship(self):
        game, _ = support.make_game("\n", ["--seed", "1", "--start-docked"])
        game.state.pilot.ship = "adder"
        game.state.apply_ship()
        self.assertEqual(game.state.hull, PLAYER_SHIPS["adder"].hull)
        support.pick(game, "status")
        self.assertEqual(game.screen, "status")
        text = support.draw(game, game.scr)
        self.assertIn("Adder", text)
        self.assertIn("110%", text)

    def test_the_ship_survives_a_save_and_load(self):
        game, _ = support.make_game("\n", ["--seed", "1", "--start-docked"])
        game.state.pilot.credits = 20000.0
        st.buy_ship(game.state.pilot, "asp")
        again = core.GameState.from_dict(game.state.to_dict())
        self.assertEqual(again.pilot.ship, "asp")
        self.assertEqual(again.pilot.cargo_cap, PLAYER_SHIPS["asp"].cargo)

    def test_only_tech_stations_sell_hulls(self):
        low = core.GameState(seed=1)
        low.pilot.system = next(s.index for s in core.galaxy.galaxy(1)
                                if s.tech < st.SHIPYARD_TECH)
        self.assertFalse(st.has_shipyard(low.system))
        game, _ = support.make_game("\n", ["--seed", "1", "--start-docked"])
        actions = [a for a, _ in game.docked_items()]
        self.assertIn("shipyard", actions)

    def test_equipment_slots_are_enforced_in_the_shop(self):
        pilot = core.Pilot()
        pilot.equipment = {"ecm", "scoop", "docking", "energy", "beam",
                           "bomb", "escape", "largebay"}
        self.assertEqual(len(pilot.equipment), pilot.slots)
        from coriolis.data import EQUIPMENT_BY_KEY
        self.assertNotEqual(st.why_not(pilot, EQUIPMENT_BY_KEY["galactic"], 15), "")

    def test_selling_equipment_refunds_half(self):
        pilot = core.Pilot()
        pilot.equipment.add("ecm")
        credits = pilot.credits
        ok, _ = st.sell_equipment(pilot, "ecm")
        self.assertTrue(ok)
        self.assertNotIn("ecm", pilot.equipment)
        self.assertAlmostEqual(pilot.credits, credits + 300.0, places=1)

    def test_version_one_save_gets_a_starter_hull(self):
        old = {"version": 1, "pilot": {"credits": 250.0, "cargo": {"food": 4},
                                       "equipment": ["largebay"], "cargo_cap": 35}}
        pilot = core.Pilot.from_dict(old["pilot"])
        self.assertEqual(pilot.ship, "cobra")
        self.assertEqual(pilot.cargo, {"food": 4})
        self.assertEqual(pilot.cargo_cap, 35)


if __name__ == "__main__":
    unittest.main()
