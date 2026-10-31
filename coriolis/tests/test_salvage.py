"""Salvage, scooping and mining."""
import unittest

import support
from coriolis import combat, core
from coriolis.flight import Vec3


def world(seed=4):
    state = core.GameState(seed=seed)
    state.launch()
    state.contacts = []
    state.flight.speed = 100.0
    return state


def rock(state, at=500.0, ore="minerals", left=5):
    c = combat.make("asteroid", "asteroid", state.flight.pos + Vec3(0, 0, at))
    c.resource = ore
    c.remaining = left
    state.contacts.append(c)
    return c


class MiningTest(unittest.TestCase):
    def test_mining_needs_the_equipment(self):
        state = world()
        rock(state)
        self.assertFalse(combat.mine(state))
        self.assertIn("mining laser", state.alert.lower())

    def test_mining_needs_an_asteroid_in_the_arc(self):
        state = world()
        state.pilot.equipment.add("mining")
        self.assertFalse(combat.mine(state))
        rock(state, at=2500.0)
        self.assertFalse(combat.mine(state))

    def test_mining_cuts_one_tonne_into_a_fragment(self):
        state = world()
        state.pilot.equipment.add("mining")
        stone = rock(state, left=3)
        self.assertTrue(combat.mine(state))
        self.assertEqual(stone.remaining, 2)
        fragments = [c for c in state.contacts if c.tag == "fragment"]
        self.assertEqual(len(fragments), 1)
        self.assertEqual(fragments[0].cargo, "minerals")
        self.assertEqual(fragments[0].qty, 1)

    def test_asteroids_run_out(self):
        state = world()
        state.pilot.equipment.add("mining")
        stone = rock(state, left=2)
        for _ in range(2):
            state.cool = 0.0
            combat.mine(state)
        self.assertNotIn(stone, state.contacts)
        state.cool = 0.0
        self.assertFalse(combat.mine(state))
        self.assertEqual(len([c for c in state.contacts if c.tag == "fragment"]), 2)

    def test_mining_costs_energy(self):
        state = world()
        state.pilot.equipment.add("mining")
        rock(state)
        before = sum(state.banks)
        combat.mine(state)
        self.assertLess(sum(state.banks), before)

    def test_fragments_must_be_scooped(self):
        state = world()
        state.pilot.equipment.update({"mining", "scoop"})
        stone = rock(state)
        combat.mine(state)
        fragment = [c for c in state.contacts if c.tag == "fragment"][0]
        fragment.pos = state.flight.pos + Vec3(0, 0, 20)
        state.flight.speed = 100
        combat.step(state, 1 / 60)
        self.assertEqual(state.pilot.cargo.get(stone.resource), 1)
        self.assertNotIn(fragment, state.contacts)

    def test_mined_ore_is_worth_money(self):
        state = world()
        state.pilot.equipment.add("mining")
        stone = rock(state, ore="gold", left=1)
        combat.mine(state)
        state.pilot.add_cargo("gold", 1)
        state.dock()
        credits = state.pilot.credits
        ok, _ = state.market.sell(state.pilot, "gold", 1)
        self.assertTrue(ok)
        self.assertGreater(state.pilot.credits, credits)


class SalvageTest(unittest.TestCase):
    def test_a_wreck_can_leave_a_canister(self):
        state = world()
        state.rng.seed(1)
        drops = 0
        for _ in range(40):
            ship = combat.make("ship", "python", state.flight.pos + Vec3(0, 0, 600))
            ship.shields = 0
            state.contacts = [ship]
            combat.damage_contact(state, ship, 999)
            drops += len([c for c in state.contacts if c.kind == "cargo"])
            state.contacts = []
        self.assertGreater(drops, 0)

    def test_canister_has_a_commodity_and_a_quantity(self):
        state = world()
        state.rng.seed(2)
        for _ in range(40):
            ship = combat.make("ship", "python", state.flight.pos + Vec3(0, 0, 600))
            ship.shields = 0
            state.contacts = [ship]
            combat.damage_contact(state, ship, 999)
            cans = [c for c in state.contacts if c.kind == "cargo"]
            if cans:
                self.assertTrue(cans[0].cargo)
                self.assertGreaterEqual(cans[0].qty, 1)
                return
        self.fail("no salvage dropped")

    def test_scooping_requires_equipment_and_room(self):
        state = world()
        can = combat.make("cargo", "canister", state.flight.pos + Vec3(0, 0, 20))
        can.cargo = "food"
        can.qty = 1
        state.contacts = [can]
        combat.step(state, 1 / 60)
        self.assertIn(can, state.contacts, "the canister must stay in space")
        self.assertEqual(state.pilot.cargo.get("food"), None)
        self.assertIn("scoop", " ".join(m[0] for m in state.messages).lower())

    def test_full_hold_refuses_the_scoop(self):
        state = world()
        state.pilot.equipment.add("scoop")
        state.pilot.add_cargo("food", state.pilot.cargo_cap)
        can = combat.make("cargo", "canister", state.flight.pos + Vec3(0, 0, 20))
        can.cargo = "gold"
        state.contacts = [can]
        combat.step(state, 1 / 60)
        self.assertIn(can, state.contacts)
        self.assertIn("full", " ".join(m[0] for m in state.messages).lower())

    def test_speed_limits_the_scoop(self):
        state = world()
        state.pilot.equipment.add("scoop")
        state.flight.speed = 400
        can = combat.make("cargo", "canister", state.flight.pos + Vec3(0, 0, 20))
        can.cargo = "gold"
        state.contacts = [can]
        combat.step(state, 1 / 60)
        self.assertIn(can, state.contacts)
        self.assertIn("fast", " ".join(m[0] for m in state.messages).lower())

    def test_a_canister_is_collected_only_once(self):
        state = world()
        state.pilot.equipment.add("scoop")
        can = combat.make("cargo", "canister", state.flight.pos + Vec3(0, 0, 20))
        can.cargo = "gold"
        can.qty = 2
        state.contacts = [can]
        for _ in range(30):
            combat.step(state, 1 / 60)
        self.assertEqual(state.pilot.cargo.get("gold"), 2)


if __name__ == "__main__":
    unittest.main()
