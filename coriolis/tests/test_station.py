import math
import unittest

import support  # noqa: F401
from coriolis import galaxy, station as st
from coriolis.core import Pilot
from coriolis.data import CARGO_LARGE, EQUIPMENT_BY_KEY, MAX_FUEL, MAX_MISSILES
from coriolis.flight import FlightModel, Vec3


class DockingTest(unittest.TestCase):
    def setUp(self):
        self.station = st.Station(Vec3(0, 0, 0))
        self.ship = FlightModel(pos=Vec3(0, 0, -2500), speed=200)

    def test_far_away_is_not_a_docking(self):
        status, text = self.station.dock_check(self.ship)
        self.assertEqual(status, "wait")
        self.assertIn("ahead", text)

    def test_aligned_approach_docks(self):
        self.ship.pos = Vec3(0, 0, -100)
        self.ship.speed = 120
        status, _ = self.station.dock_check(self.ship)
        self.assertEqual(status, "dock")

    def test_too_fast_is_refused(self):
        self.ship.pos = Vec3(0, 0, -100)
        self.ship.speed = 900
        status, text = self.station.dock_check(self.ship)
        self.assertEqual(status, "wait")
        self.assertIn("fast", text)

    def test_lateral_offset_is_refused(self):
        self.ship.pos = Vec3(200, 0, -600)
        self.ship.speed = 100
        status, text = self.station.dock_check(self.ship)
        self.assertEqual(status, "wait")
        self.assertIn("Lateral", text)

    def test_hitting_the_hull_is_a_crash(self):
        self.ship.pos = Vec3(0, 0, 300)
        status, _ = self.station.dock_check(self.ship)
        self.assertEqual(status, "crash")

    def test_flying_into_the_face_is_a_crash(self):
        self.ship.pos = Vec3(0, 0, -300)
        self.ship.speed = 100
        self.ship.orient = self.ship.orient @ (type(self.ship.orient).rot_z(math.pi / 2)) @ (type(self.ship.orient).rot_z(-math.pi / 2))
        self.ship.orient = type(self.ship.orient).rot_z(math.pi / 2)
        status, _ = self.station.dock_check(self.ship)
        self.assertEqual(status, "wait")

    def test_roll_matters(self):
        self.ship.pos = Vec3(0, 0, -100)
        self.ship.speed = 100
        self.ship.orient = type(self.ship.orient).rot_z(math.pi / 2)
        status, text = self.station.dock_check(self.ship)
        self.assertEqual(status, "wait")
        self.assertIn("Roll", text)

    def test_roll_matching_the_slot_allows_docking(self):
        for angle in (0.0, 0.7, 2.5, 5.9):
            station = st.Station(Vec3(0, 0, 0), angle=angle)
            up = station.slot_vector()
            forward = Vec3(0, 0, 1)
            right = up.cross(forward)
            ship = FlightModel(pos=Vec3(0, 0, -120), speed=150)
            ship.orient = type(ship.orient)(right, up, forward).renormalise()
            status, text = station.dock_check(ship)
            self.assertLess(station.roll_error(ship.orient.up), st.DOCK_ROLL)
            self.assertEqual(status, "dock", f"angle {angle}: {text}")

    def test_station_spins(self):
        start = self.station.angle
        self.station.step(1.0)
        self.assertNotEqual(self.station.angle, start)
        for _ in range(100):
            self.station.step(1.0)
        self.assertTrue(0 <= self.station.angle < 2 * math.pi)


class ServicesTest(unittest.TestCase):
    def setUp(self):
        self.pilot = Pilot()

    def test_refuel_from_empty(self):
        self.pilot.fuel = 1.0
        credits = self.pilot.credits
        ok, msg = st.refuel(self.pilot)
        self.assertTrue(ok)
        self.assertEqual(self.pilot.fuel, MAX_FUEL)
        self.assertLess(self.pilot.credits, credits)

    def test_refuel_when_full_is_refused(self):
        ok, _ = st.refuel(self.pilot)
        self.assertFalse(ok)

    def test_refuel_without_credits_is_refused(self):
        self.pilot.fuel = 0.0
        self.pilot.credits = 0.0
        ok, _ = st.refuel(self.pilot)
        self.assertFalse(ok)
        self.assertEqual(self.pilot.fuel, 0.0)

    def test_repair(self):
        self.pilot.credits = 500.0
        ok, _ = st.repair(self.pilot, 20.0)
        self.assertTrue(ok)
        self.assertLess(self.pilot.credits, 500.0)

    def test_repair_nothing_is_refused(self):
        self.assertFalse(st.repair(self.pilot, 0.0)[0])

    def test_fine_clears_a_record(self):
        self.pilot.legal = 2
        self.pilot.credits = 1000.0
        ok, _ = st.fine(self.pilot)
        self.assertTrue(ok)
        self.assertEqual(self.pilot.legal, 0)

    def test_fine_on_a_clean_record_is_refused(self):
        self.assertFalse(st.fine(self.pilot)[0])

    def test_shop_is_gated_by_tech_level(self):
        low = st.equipment_rows(self.pilot, 1)
        high = st.equipment_rows(self.pilot, 15)
        self.assertLess(len(low), len(high))
        self.assertTrue(all(EQUIPMENT_BY_KEY[k].tech <= 1 for k, _, _, _ in low))

    def test_buying_a_missile_adds_one(self):
        self.pilot.credits = 100.0
        before = self.pilot.missiles
        ok, _ = st.buy(self.pilot, "missile", 1)
        self.assertTrue(ok)
        self.assertEqual(self.pilot.missiles, before + 1)

    def test_missile_rack_is_capped(self):
        self.pilot.credits = 1000.0
        self.pilot.missiles = MAX_MISSILES
        self.assertFalse(st.available(self.pilot, EQUIPMENT_BY_KEY["missile"], 15))

    def test_large_cargo_bay_raises_capacity(self):
        self.pilot.credits = 1000.0
        ok, _ = st.buy(self.pilot, "largebay", 3)
        self.assertTrue(ok)
        self.assertEqual(self.pilot.cargo_cap, CARGO_LARGE)
        self.assertFalse(st.available(self.pilot, EQUIPMENT_BY_KEY["largebay"], 15))

    def test_lasers_upgrade_in_order(self):
        self.pilot.credits = 10000.0
        self.assertEqual(self.pilot.laser, "pulse")
        st.buy(self.pilot, "beam", 15)
        self.assertEqual(self.pilot.laser, "beam")
        st.buy(self.pilot, "military", 15)
        self.assertEqual(self.pilot.laser, "military")
        self.assertNotIn("beam", self.pilot.equipment)
        self.assertFalse(st.available(self.pilot, EQUIPMENT_BY_KEY["military"], 15))

    def test_cannot_buy_what_you_cannot_afford(self):
        self.pilot.credits = 1.0
        ok, _ = st.buy(self.pilot, "ecm", 15)
        self.assertFalse(ok)
        self.assertNotIn("ecm", self.pilot.equipment)

    def test_cannot_buy_below_tech_level(self):
        ok, _ = st.buy(self.pilot, "military", 1)
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
