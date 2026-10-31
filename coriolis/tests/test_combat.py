import unittest

import support  # noqa: F401
from coriolis import combat, core
from coriolis.data import LASER_DAMAGE
from coriolis.flight import Vec3


class CombatTest(unittest.TestCase):
    def setUp(self):
        self.state = core.GameState(seed=11)
        self.state.launch()
        self.state.flight.pos = Vec3(0.0, 0.0, 0.0)
        self.state.contacts = []

    def test_damage_hits_the_facing_shield(self):
        state = self.state
        combat.damage_player(state, 30, Vec3(0, 0, 500))
        self.assertEqual(state.shields["fore"], 70.0)
        self.assertEqual(state.shields["aft"], 100.0)
        combat.damage_player(state, 30, Vec3(0, 0, -500))
        self.assertEqual(state.shields["aft"], 70.0)

    def test_shields_then_banks_then_hull(self):
        state = self.state
        state.shields = {"fore": 10.0, "aft": 10.0}
        before = sum(state.banks)
        combat.damage_player(state, 30, Vec3(0, 0, 100))
        self.assertEqual(state.shields["fore"], 0.0)
        self.assertAlmostEqual(sum(state.banks), before - 20, places=3)
        self.assertEqual(state.hull, 100.0)
        combat.damage_player(state, 500)
        self.assertLess(state.hull, 100.0)
        self.assertTrue(state.dead)

    def test_laser_hits_a_target_in_the_cone(self):
        c = combat.make("ship", "sidewinder", Vec3(0, 0, 800))
        self.state.contacts = [c]
        hit = combat.fire_laser(self.state)
        self.assertIs(hit, c)
        self.assertLess(c.shields, c.type.shields)

    def test_laser_misses_off_axis(self):
        c = combat.make("ship", "sidewinder", Vec3(900, 0, 800))
        self.state.contacts = [c]
        self.assertIsNone(combat.fire_laser(self.state))
        self.assertEqual(c.shields, c.type.shields)

    def test_laser_costs_energy_and_has_a_cooldown(self):
        c = combat.make("ship", "sidewinder", Vec3(0, 0, 800))
        self.state.contacts = [c]
        before = sum(self.state.banks)
        combat.fire_laser(self.state)
        self.assertLess(sum(self.state.banks), before)
        self.assertIsNone(combat.fire_laser(self.state))

    def test_laser_damage_depends_on_the_fitted_laser(self):
        pulse = LASER_DAMAGE["pulse"]
        military = LASER_DAMAGE["military"]
        self.assertGreater(military, pulse)
        self.state.pilot.equipment.add("military")
        self.assertEqual(self.state.pilot.laser, "military")

    def test_kill_pays_the_bounty(self):
        c = combat.make("ship", "cobra", Vec3(0, 0, 700), hostile=True)
        self.state.contacts = [c]
        credits = self.state.pilot.credits
        c.shields = 0
        combat.damage_contact(self.state, c, 1000)
        self.assertEqual(self.state.pilot.credits, credits + c.type.bounty)
        self.assertEqual(self.state.pilot.kills, 1)
        self.assertEqual(self.state.contacts, [])

    def test_killing_police_makes_you_a_fugitive(self):
        c = combat.make("ship", "viper", Vec3(0, 0, 700))
        self.state.contacts = [c]
        c.shields = 0
        combat.damage_contact(self.state, c, 1000)
        self.assertEqual(self.state.pilot.legal, 30)
        self.assertEqual(self.state.pilot.legal_name, "Offender")
        self.assertEqual(self.state.pilot.kills, 0)

    def test_missile_needs_a_lock(self):
        self.assertFalse(combat.fire_missile(self.state))
        c = combat.make("ship", "cobra", Vec3(0, 0, 900))
        self.state.contacts = [c]
        combat.lock_target(self.state)
        self.assertTrue(combat.fire_missile(self.state))
        self.assertEqual(self.state.pilot.missiles, 2)
        self.assertTrue(any(x.kind == "missile" for x in self.state.contacts))

    def test_ecm_clears_missiles(self):
        self.state.pilot.equipment.add("ecm")
        self.state.contacts = [combat.make("missile", "missile", Vec3(0, 0, 400))]
        self.assertTrue(combat.ecm(self.state))
        self.assertEqual(self.state.contacts, [])

    def test_energy_bomb_clears_the_neighbourhood(self):
        self.state.pilot.equipment.add("bomb")
        self.state.contacts = [combat.make("ship", "cobra", Vec3(0, 0, 500), True),
                               combat.make("ship", "cobra", Vec3(0, 0, 30000), True)]
        self.assertTrue(combat.energy_bomb(self.state))
        self.assertEqual(len(self.state.contacts), 1)
        self.assertFalse(self.state.pilot.has("bomb"))

    def test_mass_lock_near_ships(self):
        self.assertFalse(combat.has_mass_lock(self.state))
        self.state.contacts = [combat.make("ship", "cobra", Vec3(0, 0, 800))]
        self.assertTrue(combat.has_mass_lock(self.state))

    def test_long_run_is_stable(self):
        combat.spawn(self.state, arrivals=True)
        for _ in range(1200):
            combat.step(self.state, 1 / 60)
        self.assertFalse(self.state.dead)
        for c in self.state.contacts:
            self.assertTrue(0 <= c.energy)
        self.assertGreaterEqual(self.state.hull, 0)

    def test_npcs_can_turn_to_targets_anywhere_around_them(self):
        import math
        for bearing in (0, 45, 90, 135, 180, -90, -135):
            for elevation in (-40, 0, 40):
                c = combat.make("ship", "cobra", Vec3(0, 0, 0))
                r, e = math.radians(bearing), math.radians(elevation)
                target = Vec3(math.sin(r) * math.cos(e), math.sin(e),
                              math.cos(r) * math.cos(e)) * 1500
                for _ in range(300):
                    combat._steer(c, target, 1 / 60, 1.4)
                err = math.degrees(c.orient.forward.angle_to(target))
                self.assertLess(err, 5, f"bearing {bearing} elevation {elevation}")

    def test_steering_is_bounded_by_the_turn_rate(self):
        import math
        c = combat.make("ship", "cobra", Vec3(0, 0, 0))
        start = c.orient.forward
        combat._steer(c, Vec3(0, 0, -1500), 1 / 60, 1.0)   # dead astern
        turned = math.degrees(start.angle_to(c.orient.forward))
        self.assertLessEqual(turned, math.degrees(1.0 / 60) + 0.01)

    def test_steering_uses_simulation_time(self):
        c1 = combat.make("ship", "cobra", Vec3(0, 0, 0))
        c2 = combat.make("ship", "cobra", Vec3(0, 0, 0))
        for _ in range(60):
            combat._steer(c1, Vec3(0, 800, 800), 1 / 60, 1.0)
        combat._steer(c2, Vec3(0, 800, 800), 1.0, 1.0)
        self.assertGreater(c1.orient.forward.y, c2.orient.forward.y)

    def test_player_missile_homes_and_hits(self):
        target = combat.make("ship", "sidewinder", Vec3(0, 0, 1200), hostile=True)
        self.state.contacts = [target]
        combat.lock_target(self.state)
        self.assertTrue(combat.fire_missile(self.state))
        for _ in range(600):
            combat.step(self.state, 1 / 60)
            if target not in self.state.contacts:
                break
        self.assertNotIn(target, self.state.contacts)

    def test_ecm_stops_an_incoming_missile(self):
        self.state.pilot.equipment.add("ecm")
        missile = combat.make("missile", "missile",
                              self.state.flight.pos + Vec3(0, 0, 900))
        self.state.contacts = [missile]
        self.assertTrue(combat.ecm(self.state))
        self.assertEqual(self.state.contacts, [])

    def test_spawn_respects_lawless_space(self):
        pirates = 0
        for seed in range(40):
            state = core.GameState(seed=seed)
            state.pilot.system = 11
            state.launch()
            combat.spawn(state, arrivals=True)
            pirates += sum(1 for c in state.contacts if c.hostile)
        self.assertGreater(pirates, 0)


if __name__ == "__main__":
    unittest.main()
