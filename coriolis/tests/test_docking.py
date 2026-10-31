"""The docking instrument and the docking computer."""
import math
import unittest

import support
from coriolis import core, station as st
from coriolis.flight import FlightModel, Mat3, Vec3


def aligned(angle=0.0, pos=None, speed=100.0):
    station = st.Station(Vec3(0, 0, 0), angle=angle)
    ship = FlightModel(pos=pos or Vec3(0, 0, -100), speed=speed)
    up = station.slot_vector()
    forward = Vec3(0, 0, 1)
    right = up.cross(forward)
    ship.orient = Mat3(right, up, forward).renormalise()
    return station, ship


class InstrumentTest(unittest.TestCase):
    def test_aligned_ship_is_told_it_can_dock(self):
        for angle in (0.0, 0.6, 2.2, 5.5):
            station, ship = aligned(angle)
            info = station.dock_status(ship)
            self.assertEqual(info["status"], "dock", info["text"])
            self.assertTrue(all(info["ok"].values()))
            self.assertEqual(info["hints"], [])

    def test_instrument_reports_distance_lateral_roll_and_speed(self):
        station, ship = aligned()
        ship.pos = Vec3(40, 0, -600)
        ship.speed = 400
        info = station.dock_status(ship)
        self.assertAlmostEqual(info["dist"], 600, delta=1)
        self.assertAlmostEqual(info["lateral"], 40, delta=1)
        self.assertEqual(info["speed"], 400)
        self.assertEqual(info["max_speed"], st.DOCK_SPEED)
        self.assertFalse(info["ok"]["speed"])
        self.assertIn("reduce speed", info["hints"])

    def test_roll_hint_points_the_way_the_player_must_press(self):
        for angle in (0.4, 1.1, 2.0, 3.4, 5.0):
            station, ship = aligned(0.0, speed=100)
            station.angle = angle
            info = station.dock_status(ship)
            if abs(info["roll"]) <= math.degrees(st.DOCK_ROLL):
                continue
            self.assertIn("roll right" if info["roll"] > 0 else "roll left",
                          info["hints"])
            # Apply the player's roll key in that direction and the error shrinks.
            direction = 1.0 if info["roll"] > 0 else -1.0
            for _ in range(180):
                ship.rotate(0.0, direction, 1 / 60)
                if abs(station.dock_status(ship)["roll"]) < 5.0:
                    break
            after = station.dock_status(ship)
            self.assertLess(abs(after["roll"]), abs(info["roll"]))
            self.assertEqual(after["status"], "dock", (info, after))

    def test_lateral_hint_names_the_side_the_slot_is_on(self):
        station, ship = aligned()
        ship.pos = Vec3(-80, 0, -200)
        info = station.dock_status(ship)
        self.assertLess(info["offset"], 0)
        self.assertIn("slot to the right", info["hints"])
        self.assertFalse(info["ok"]["lateral"])

    def test_status_agrees_with_the_rules(self):
        cases = [
            (Vec3(0, 0, -2500), 100, "wait"),
            (Vec3(0, 0, -100), 100, "wait"),   # roll is wrong at station angle 0.9
            (Vec3(0, 0, -100), 900, "wait"),
            (Vec3(200, 0, -150), 100, "crash"),
            (Vec3(0, 0, 300), 100, "crash"),
        ]
        station = st.Station(Vec3(0, 0, 0), angle=0.9)
        for pos, speed, expected in cases:
            ship = FlightModel(pos=pos, speed=speed)
            info = station.dock_status(ship)
            status, text = station.dock_check(ship)
            self.assertEqual(status, info["status"])
            self.assertEqual(status, expected, (pos, speed, text))


class ComputerTest(unittest.TestCase):
    def docked_game(self):
        game, scr = support.make_game("\n", ["--seed", "1", "--start-docked"])
        return game, scr

    def test_computer_is_off_until_armed(self):
        game, _ = self.docked_game()
        game.state.pilot.equipment.add("docking")
        support.pick(game, "launch")
        for _ in range(120):
            game.step_sim(1 / 60)
        self.assertEqual(game.screen, "flight")
        self.assertFalse(game.computer_armed())

    def test_computer_cannot_engage_without_the_equipment(self):
        game, _ = self.docked_game()
        support.pick(game, "launch")
        game.handle(ord("c"))
        self.assertFalse(game.computer_armed())
        self.assertIn("not fitted", game.computer_reason())

    def test_arming_and_flying_in_docks_the_ship(self):
        game, _ = self.docked_game()
        game.state.pilot.equipment.add("docking")
        support.pick(game, "launch")
        game.handle(ord("c"))
        self.assertTrue(game.computer_armed())
        for step in range(60 * 120):
            game.target_speed = 400.0
            game.step_sim(1 / 60)
            if game.screen == "docked":
                break
        self.assertEqual(game.screen, "docked")
        self.assertEqual(game.state.hull, game.state.hull_max)
        self.assertFalse(game.computer_armed(), "computer should disarm after docking")

    def test_computer_explains_why_it_cannot_engage_far_out(self):
        game, _ = self.docked_game()
        game.state.pilot.equipment.update({"docking", "ecm"})
        support.pick(game, "launch")
        game.handle(ord("c"))
        game.state.flight.pos = Vec3(0, 0, -20000)
        self.assertIn("range", game.computer_reason())


class LimitsTest(unittest.TestCase):
    def test_repair_uses_the_hulls_own_maximum(self):
        pilot = core.Pilot()
        pilot.ship = "adder"
        pilot.credits = 1000.0
        damage = pilot.hull_max - 20.0
        ok, msg = st.repair(pilot, damage)
        self.assertTrue(ok, msg)
        self.assertLess(pilot.credits, 1000.0)
        self.assertEqual(pilot.hull_max, 110.0)


if __name__ == "__main__":
    unittest.main()
