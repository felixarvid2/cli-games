"""Route planning and the chart's navigation tools."""
import unittest

import support
from coriolis import galaxy, navigation
from coriolis.data import MAX_FUEL


class PlannerTest(unittest.TestCase):
    def test_every_leg_fits_in_a_tank(self):
        for target in (12, 40, 99, 200, 255):
            route = navigation.plan(1, 7, target)
            self.assertTrue(route.ok, route.reason)
            for leg in route.legs:
                self.assertLessEqual(leg, MAX_FUEL + 1e-9)

    def test_path_starts_and_ends_where_it_should(self):
        route = navigation.plan(1, 7, 40)
        self.assertEqual(route.path[0], 7)
        self.assertEqual(route.path[-1], 40)
        self.assertEqual(route.jumps, len(route.legs))
        self.assertAlmostEqual(route.total, sum(route.legs), places=1)

    def test_route_is_at_least_as_long_as_the_straight_line(self):
        route = navigation.plan(1, 7, 40)
        direct = galaxy.distance(galaxy.system(1, 7), galaxy.system(1, 40))
        self.assertGreaterEqual(route.total + 0.05, min(direct, route.total))
        self.assertGreaterEqual(route.total, direct - 0.1)

    def test_a_low_tank_asks_for_a_refill_before_the_first_leg(self):
        route = navigation.plan(1, 7, 40, fuel=1.0)
        self.assertTrue(route.ok)
        self.assertIn(route.path[0], route.refuel_at)
        self.assertGreater(route.fuel_cost, 0)

    def test_a_full_tank_needs_fewer_stops(self):
        low = navigation.plan(1, 7, 40, fuel=1.0)
        full = navigation.plan(1, 7, 40, fuel=MAX_FUEL)
        self.assertLessEqual(len(full.refuel_at), len(low.refuel_at))

    def test_same_system_is_not_a_route(self):
        route = navigation.plan(1, 7, 7)
        self.assertFalse(route.ok)
        self.assertIn("Already", route.reason)

    def test_unknown_system_is_explained(self):
        route = navigation.plan(1, 7, 9999)
        self.assertFalse(route.ok)
        self.assertTrue(route.reason)

    def test_safe_mode_weights_danger(self):
        self.assertGreater(navigation._cost("safe", 5.0, 1.0),
                           navigation._cost("short", 5.0, 1.0))
        self.assertEqual(navigation._cost("short", 5.0, 1.0), 5.0)

    def test_both_modes_produce_valid_routes(self):
        for mode in navigation.MODES:
            route = navigation.plan(1, 7, 120, mode=mode)
            self.assertTrue(route.ok, (mode, route.reason))
            self.assertEqual(route.path[-1], 120)

    def test_steps_describe_the_legs(self):
        route = navigation.plan(1, 7, 40)
        steps = navigation.steps(1, route)
        self.assertEqual(len(steps), route.jumps)
        for index, dist, refuel in steps:
            self.assertIn(index, route.path)
            self.assertLessEqual(dist, MAX_FUEL + 1e-9)

    def test_reachable_covers_the_galaxy_from_lave(self):
        reach = navigation.reachable(1, 7)
        self.assertGreater(len(reach), 200)
        self.assertNotIn(7, reach)

    def test_search_by_name(self):
        matches = navigation.search(1, "lav")
        self.assertEqual(matches[0].name, "Lave")
        self.assertEqual(navigation.search(1, "zzzz"), [])
        self.assertTrue(all("be" in s.name.lower() for s in navigation.search(1, "be")))


class ChartTest(unittest.TestCase):
    def chart(self, keys="\n"):
        return support.make_game(keys, ["--seed", "1"])

    def test_search_selects_a_system(self):
        game, scr = self.chart()
        target = galaxy.system(1, 33).name
        for ch in "/" + target.lower():
            game.handle(ord(ch))
        game.handle(10)
        self.assertFalse(game.chart_searching)
        self.assertEqual(galaxy.system(1, game.chart_sel).name, target)

    def test_backspace_edits_the_query(self):
        game, _ = self.chart()
        game.handle(ord("/"))
        for ch in "abc":
            game.handle(ord(ch))
        game.handle(127)
        self.assertEqual(game.chart_query, "ab")

    def test_planning_a_route_reports_jumps(self):
        game, _ = self.chart()
        game.chart_sel = 40
        game.handle(ord("p"))
        self.assertEqual(game.chart_target, 40)
        route = game.chart_route()
        self.assertTrue(route.ok)
        self.assertGreater(route.jumps, 0)
        text = support.draw(game, game.scr)
        self.assertIn("ROUTE", text)
        self.assertIn("jumps", text)

    def test_enter_jumps_the_next_hop_of_the_route(self):
        game, _ = self.chart()
        game.chart_sel = 40
        game.handle(ord("p"))
        route = game.chart_route()
        game.handle(10)
        self.assertEqual(game.screen, "flight")
        self.assertIsNotNone(game.state.jump)
        self.assertEqual(game.state.jump["index"], route.next_hop)

    def test_local_view_shows_fewer_systems(self):
        game, _ = self.chart()
        galaxy_view = len(game.chart_systems())
        game.handle(ord("v"))
        local_view = len(game.chart_systems())
        self.assertLess(local_view, galaxy_view)
        self.assertEqual(game.chart_view, 0)

    def test_mode_toggles(self):
        game, _ = self.chart()
        self.assertEqual(game.chart_mode, "short")
        game.handle(ord("m"))
        self.assertEqual(game.chart_mode, "safe")

    def test_unreachable_jump_explains_itself(self):
        game, _ = self.chart()
        game.state.pilot.fuel = 0.0
        game.chart_sel = 40
        game.handle(10)
        self.assertEqual(game.screen, "chart")
        self.assertFalse(game.chart_searching)
        self.assertIn("LY", game.toast)

    def test_mission_and_trade_targets_can_be_selected(self):
        game, _ = self.chart()
        game.handle(ord("t"))
        self.assertIsNotNone(game.chart_sel)
        game.handle(ord("n"))
        self.assertIsNotNone(game.chart_sel)

    def test_route_never_bypasses_the_jump(self):
        game, _ = self.chart()
        game.chart_sel = 40
        game.handle(ord("p"))
        before = game.state.pilot.fuel
        game.handle(10)
        for _ in range(400):
            game.step_sim(1 / 60)
        self.assertLess(game.state.pilot.fuel, before)


if __name__ == "__main__":
    unittest.main()
