"""Mission board, contracts, rewards and persistence."""
import unittest

import support
from coriolis import combat, core, galaxy, missions
from coriolis.flight import Vec3


def docked(seed=3):
    state = core.GameState(seed=seed)
    state.dock()
    return state


def by_kind(state):
    return {m.kind: m for m in missions.offers(state)}


def find_kind(seed_range=range(1, 40), kind="freight"):
    for seed in seed_range:
        state = docked(seed)
        if kind in by_kind(state):
            return state, by_kind(state)[kind]
    raise AssertionError(f"no {kind} mission found")


class BoardTest(unittest.TestCase):
    def test_board_is_stable_for_a_visit(self):
        state = docked()
        first = [(m.mid, m.pay) for m in missions.offers(state)]
        second = [(m.mid, m.pay) for m in missions.offers(state)]
        self.assertEqual(first, second)

    def test_board_is_persisted_across_docking(self):
        state = docked()
        mids = [m.mid for m in missions.offers(state)]
        state.launch()
        state.dock()
        self.assertEqual([m.mid for m in missions.offers(state)], mids)

    def test_board_differs_between_systems(self):
        a = docked(5)
        b = core.GameState(seed=5)
        b.pilot.system = 12
        b.dock()
        self.assertNotEqual([m.mid for m in missions.offers(a)],
                            [m.mid for m in missions.offers(b)])

    def test_offers_have_a_reachable_destination(self):
        from coriolis import navigation
        state = docked()
        for mission in missions.offers(state):
            self.assertIsNotNone(mission.dest)
            dest = mission.dest_tuple
            route = navigation.plan(state.pilot.galaxy, state.pilot.system, dest[1])
            self.assertTrue(route.ok, mission.title)

    def test_offers_show_what_the_player_needs_to_decide(self):
        state = docked()
        for mission in missions.offers(state):
            self.assertGreater(mission.pay, 0)
            self.assertIn(mission.kind, missions.KINDS)
            self.assertTrue(mission.brief)
            self.assertTrue(mission.dest_name())
            self.assertIsNotNone(mission.deadline)
            if mission.kind == "freight":
                self.assertGreater(mission.cargo_qty, 0)

    def test_board_scales_with_a_bigger_hold(self):
        small = docked(9)
        big = docked(9)
        big.pilot.ship = "adder"
        small_count = len(missions.offers(small))
        big_count = len(missions.offers(big))
        self.assertGreaterEqual(big_count, small_count)


class FreightTest(unittest.TestCase):
    def test_accepting_reserves_the_cargo(self):
        state, mission = find_kind()
        ok, msg = missions.accept(state, mission)
        self.assertTrue(ok, msg)
        self.assertEqual(state.pilot.cargo.get(mission.cargo_key), mission.cargo_qty)
        self.assertEqual(state.pilot.reserved.get(mission.cargo_key), mission.cargo_qty)
        self.assertEqual(len(missions.active(state)), 1)

    def test_reserved_cargo_cannot_be_sold(self):
        state, mission = find_kind()
        missions.accept(state, mission)
        ok, msg = state.market.sell(state.pilot, mission.cargo_key, 1)
        self.assertFalse(ok)
        self.assertIn("reserved", msg)

    def test_delivery_pays_once(self):
        state, mission = find_kind()
        missions.accept(state, mission)
        credits = state.pilot.credits
        state.pilot.system = mission.dest_tuple[1]
        state.dock()
        self.assertAlmostEqual(state.pilot.credits, credits + mission.pay, places=1)
        self.assertEqual(state.pilot.cargo.get(mission.cargo_key), None)
        self.assertEqual(state.pilot.reserved, {})
        self.assertEqual(missions.active(state), [])
        # Docking again must not pay twice.
        state.launch()
        state.dock()
        self.assertAlmostEqual(state.pilot.credits, credits + mission.pay, places=1)

    def test_accept_refuses_when_the_hold_is_full(self):
        state, mission = find_kind()
        state.pilot.add_cargo("food", state.pilot.cargo_cap)
        ok, msg = missions.accept(state, mission)
        self.assertFalse(ok)
        self.assertIn("hold", msg.lower())

    def test_abandoning_removes_the_cargo_and_pays_nothing(self):
        state, mission = find_kind()
        missions.accept(state, mission)
        credits = state.pilot.credits
        ok, _ = missions.abandon(state, mission)
        self.assertTrue(ok)
        self.assertEqual(state.pilot.cargo.get(mission.cargo_key), None)
        self.assertEqual(state.pilot.credits, credits)
        self.assertFalse(mission.paid)
        state.pilot.system = mission.dest_tuple[1]
        state.dock()
        self.assertEqual(state.pilot.credits, credits)


class OtherKindsTest(unittest.TestCase):
    def test_courier_needs_no_cargo_and_pays_on_arrival(self):
        state, mission = find_kind(kind="courier")
        self.assertEqual(mission.cargo_qty, 0)
        missions.accept(state, mission)
        credits = state.pilot.credits
        state.pilot.system = mission.dest_tuple[1]
        state.dock()
        self.assertAlmostEqual(state.pilot.credits, credits + mission.pay, places=1)

    def test_bounty_spawns_in_the_target_system_and_pays_on_kill(self):
        state, mission = find_kind(kind="bounty")
        missions.accept(state, mission)
        state.pilot.system = mission.dest_tuple[1]
        state.launch()
        targets = [c for c in state.contacts if c.mission == mission.mid]
        self.assertTrue(targets, "no wanted ship spawned")
        target = targets[0]
        target.shields = 0
        credits = state.pilot.credits
        combat.damage_contact(state, target, 999)
        notes = missions.on_kill(state, target)
        self.assertTrue(notes)
        # The kill also pays the ship's own bounty; the contract pays once.
        paid_once = state.pilot.credits
        self.assertGreaterEqual(paid_once, credits + mission.pay - 0.1)
        self.assertEqual(missions.active(state), [])
        missions.on_kill(state, target)
        self.assertEqual(state.pilot.credits, paid_once)

    def test_rescue_requires_proximity_then_delivery(self):
        state, mission = find_kind(kind="rescue")
        missions.accept(state, mission)
        state.launch()
        beacons = [c for c in state.contacts if c.tag == "rescue"]
        self.assertTrue(beacons)
        self.assertFalse(missions.recover(state))
        state.flight.pos = beacons[0].pos
        self.assertTrue(missions.recover(state))
        self.assertEqual(mission.progress.get("recovered"), 1)
        credits = state.pilot.credits
        state.pilot.system = mission.dest_tuple[1]
        state.dock()
        self.assertAlmostEqual(state.pilot.credits, credits + mission.pay, places=1)

    def test_escort_is_lost_if_the_trader_dies(self):
        state, mission = find_kind(kind="escort")
        missions.accept(state, mission)
        state.launch()
        escort = [c for c in state.contacts if c.mission == mission.mid]
        self.assertTrue(escort)
        state.contacts.remove(escort[0])
        missions.step(state, 0.1)
        self.assertEqual(mission.progress.get("escort_alive"), 0)
        missions.on_jump(state)
        self.assertEqual(mission.state, "failed")


class DeadlineTest(unittest.TestCase):
    def test_deadline_fails_the_contract(self):
        state, mission = find_kind(kind="courier")
        missions.accept(state, mission)
        state.time = mission.deadline + 1
        notes = missions.check_deadlines(state)
        self.assertTrue(notes)
        self.assertEqual(mission.state, "failed")
        self.assertEqual(missions.active(state), [])

    def test_clock_only_moves_while_flying(self):
        state, mission = find_kind(kind="courier")
        missions.accept(state, mission)
        before = state.time
        state.dock()
        self.assertEqual(state.time, before)


class PersistenceTest(unittest.TestCase):
    def test_missions_survive_a_save_and_load(self):
        state, mission = find_kind()
        missions.accept(state, mission)
        data = state.to_dict()
        again = core.GameState.from_dict(data)
        self.assertEqual(len(missions.active(again)), 1)
        loaded = missions.active(again)[0]
        self.assertEqual(loaded.mid, mission.mid)
        self.assertEqual(loaded.pay, mission.pay)
        self.assertEqual(again.pilot.reserved.get(mission.cargo_key), mission.cargo_qty)

    def test_a_paid_contract_is_not_paid_again_after_reload(self):
        state, mission = find_kind()
        missions.accept(state, mission)
        state.pilot.system = mission.dest_tuple[1]
        state.dock()
        credits = state.pilot.credits
        again = core.GameState.from_dict(state.to_dict())
        again.dock()
        self.assertAlmostEqual(again.pilot.credits, credits, places=1)
        self.assertIn(mission.mid, again.completed)

    def test_board_survives_a_reload(self):
        state = docked(11)
        mids = sorted(m.mid for m in missions.offers(state))
        again = core.GameState.from_dict(state.to_dict())
        self.assertEqual(sorted(m.mid for m in missions.offers(again)), mids)


if __name__ == "__main__":
    unittest.main()
