"""How the other ships react to the player."""
import unittest

import support
from coriolis import combat, core
from coriolis.flight import Mat3, Vec3


def world(seed=11):
    state = core.GameState(seed=seed)
    state.launch()
    state.flight.pos = Vec3(0, 0, -6000)
    state.contacts = []
    return state


def run(state, seconds, dt=1 / 60):
    for _ in range(int(seconds / dt)):
        combat.step(state, dt)


class PirateTest(unittest.TestCase):
    def test_pirate_demands_then_attacks(self):
        state = world()
        state.pilot.add_cargo("food", 6)
        pirate = combat.make("ship", "krait", state.flight.pos + Vec3(0, 0, 900))
        state.contacts = [pirate]
        run(state, 0.5)
        self.assertEqual(pirate.state, "demand")
        self.assertFalse(pirate.hostile)
        self.assertIn("jettison", state.alert.lower())
        run(state, combat.DEMAND_TIME + 1.0)
        self.assertTrue(pirate.hostile)
        self.assertIn("opens fire", " ".join(m[0] for m in state.messages).lower())

    def test_jettisoning_satisfies_the_pirate(self):
        state = world()
        state.pilot.add_cargo("food", 6)
        pirate = combat.make("ship", "krait", state.flight.pos + Vec3(0, 0, 900))
        state.contacts = [pirate]
        run(state, 0.5)
        ok, msg = combat.jettison(state, "food", 2)
        self.assertTrue(ok, msg)
        self.assertEqual(state.pilot.cargo["food"], 4)
        self.assertEqual(state.jettison_count, 1)
        canisters = [c for c in state.contacts if c.kind == "cargo"]
        self.assertTrue(canisters)
        run(state, 12.0)
        self.assertFalse(pirate.hostile, "pirate should break off")

    def test_pirate_leaves_a_pilot_with_an_empty_hold_alone(self):
        state = world()
        pirate = combat.make("ship", "krait", state.flight.pos + Vec3(0, 0, 900))
        state.contacts = [pirate]
        run(state, 4.0)
        self.assertFalse(pirate.hostile)
        self.assertNotEqual(pirate.state, "demand")

    def test_pirate_never_demands_cargo_the_player_does_not_have(self):
        state = world()
        state.pilot.add_cargo("food", 1)
        state.pilot.reserve("food", 1)          # mission cargo only
        pirate = combat.make("ship", "krait", state.flight.pos + Vec3(0, 0, 900))
        state.contacts = [pirate]
        run(state, 2.0)
        self.assertNotEqual(pirate.state, "demand")


class PoliceTest(unittest.TestCase):
    def test_clean_pilot_is_scanned_and_left_alone(self):
        state = world()
        cop = combat.make("ship", "viper", state.flight.pos + Vec3(0, 0, 1500))
        state.contacts = [cop]
        run(state, 3.0)
        self.assertFalse(cop.hostile)
        self.assertIn("clean", " ".join(m[0] for m in state.messages).lower())

    def test_contraband_is_detected_and_punished(self):
        state = world()
        state.pilot.add_cargo("narcotics", 4)
        cop = combat.make("ship", "viper", state.flight.pos + Vec3(0, 0, 1500))
        state.contacts = [cop]
        run(state, 1.0)
        self.assertIn("contraband", " ".join(m[0] for m in state.messages).lower())
        self.assertFalse(cop.hostile)
        run(state, 12.0)
        self.assertTrue(cop.hostile)
        self.assertGreater(state.pilot.intel.get("fines", 0), 0)
        self.assertGreater(state.pilot.legal, 0)
        self.assertLess(state.pilot.cargo.get("narcotics", 0), 4)

    def test_jettisoning_contraband_ends_the_scan(self):
        state = world()
        state.pilot.add_cargo("narcotics", 4)
        cop = combat.make("ship", "viper", state.flight.pos + Vec3(0, 0, 1500))
        state.contacts = [cop]
        run(state, 1.0)
        combat.jettison(state, "narcotics", 4)
        run(state, 12.0)
        self.assertFalse(cop.hostile)
        self.assertEqual(state.pilot.intel.get("fines", 0), 0)

    def test_fugitive_is_engaged_on_sight(self):
        state = world()
        state.pilot.legal = 60
        cop = combat.make("ship", "viper", state.flight.pos + Vec3(0, 0, 2000))
        state.contacts = [cop]
        run(state, 1.0)
        self.assertTrue(cop.hostile)
        self.assertIn("fugitive", " ".join(m[0] for m in state.messages).lower())

    def test_lawful_systems_field_more_police(self):
        police = 0
        for seed in range(40):
            state = core.GameState(seed=seed)
            lawful = next(s for s in core.galaxy.galaxy(1) if s.government >= 6)
            state.pilot.system = lawful.index
            state.launch()
            state.contacts = []
            combat.spawn(state)
            police += sum(1 for c in state.contacts if c.type.role == "police")
        self.assertGreater(police, 0)


class TraderTest(unittest.TestCase):
    def test_trader_flees_and_calls_for_help(self):
        state = world()
        trader = combat.make("ship", "python", state.flight.pos + Vec3(0, 0, 2000))
        pirate = combat.make("ship", "mamba", trader.pos + Vec3(0, 0, 600), hostile=True)
        state.contacts = [trader, pirate]
        run(state, 1.0)
        self.assertEqual(trader.state, "flee")
        self.assertIn("mayday", " ".join(m[0] for m in state.messages).lower())
        closest = (trader.pos - pirate.pos).length()
        run(state, 9.0)
        self.assertGreater((trader.pos - pirate.pos).length(), closest)

    def test_trader_drops_cargo_while_running(self):
        state = world()
        trader = combat.make("ship", "python", state.flight.pos + Vec3(0, 0, 2000))
        pirate = combat.make("ship", "mamba", trader.pos + Vec3(0, 0, 500), hostile=True)
        state.contacts = [trader, pirate]
        run(state, 12.0)
        self.assertTrue(any(c.kind == "cargo" and c.tag == "salvage"
                            for c in state.contacts))


class HunterTest(unittest.TestCase):
    def test_hunter_ignores_a_clean_pilot(self):
        state = world()
        hunter = combat.make("ship", "ferdl", state.flight.pos + Vec3(0, 0, 1500))
        state.contacts = [hunter]
        run(state, 2.0)
        self.assertFalse(hunter.hostile)

    def test_hunter_attacks_an_offender(self):
        state = world()
        state.pilot.legal = 20
        hunter = combat.make("ship", "ferdl", state.flight.pos + Vec3(0, 0, 1500))
        state.contacts = [hunter]
        run(state, 1.0)
        self.assertTrue(hunter.hostile)
        self.assertIn("record", " ".join(m[0] for m in state.messages).lower())


class MissileTest(unittest.TestCase):
    def test_npc_missile_is_telegraphed_and_hurts(self):
        state = world()
        pirate = combat.make("ship", "mamba", state.flight.pos + Vec3(0, 0, 3000),
                             hostile=True)
        pirate.state = "attack"
        pirate.missiles = 1
        state.contacts = [pirate]
        hull = state.hull
        run(state, 1.0)
        missiles = [c for c in state.contacts if c.kind == "missile"]
        self.assertTrue(missiles)
        self.assertIn("incoming missile",
                      " ".join(m[0] for m in state.messages).lower())
        run(state, 8.0)
        self.assertLess(state.hull + sum(state.shields.values()), hull + 200)

    def test_ecm_stops_the_incoming_missile(self):
        state = world()
        state.pilot.equipment.add("ecm")
        pirate = combat.make("ship", "mamba", state.flight.pos + Vec3(0, 0, 3000),
                             hostile=True)
        pirate.state = "attack"
        pirate.missiles = 1
        state.contacts = [pirate]
        run(state, 1.0)
        self.assertTrue(any(c.kind == "missile" for c in state.contacts))
        self.assertTrue(combat.ecm(state))
        self.assertFalse(any(c.kind == "missile" for c in state.contacts))


class KillCreditTest(unittest.TestCase):
    def test_asteroid_is_not_murder(self):
        state = world()
        rock = combat.make("asteroid", "asteroid", state.flight.pos + Vec3(0, 0, 500))
        state.contacts = [rock]
        rock.shields = 0
        combat.damage_contact(state, rock, 999)
        self.assertEqual(state.pilot.legal, 0)
        self.assertEqual(state.pilot.kills, 0)

    def test_scooping_salvage_is_not_murder(self):
        state = world()
        state.pilot.equipment.add("scoop")
        can = combat.make("cargo", "canister", state.flight.pos + Vec3(0, 0, 30))
        can.cargo = "gold"
        can.qty = 2
        state.contacts = [can]
        state.flight.speed = 100
        run(state, 1.0)
        self.assertEqual(state.pilot.cargo.get("gold"), 2)
        self.assertEqual(state.pilot.legal, 0)
        self.assertNotIn(can, state.contacts)

    def test_destroying_an_interceptor_missile_is_not_murder(self):
        state = world()
        missile = combat.make("missile", "missile", state.flight.pos + Vec3(0, 0, 500))
        missile.tag = "player"
        state.contacts = [missile]
        missile.energy = 0
        combat.damage_contact(state, missile, 10)
        self.assertEqual(state.pilot.legal, 0)
        self.assertEqual(state.pilot.kills, 0)


if __name__ == "__main__":
    unittest.main()
