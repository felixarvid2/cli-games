import unittest

import support
from coriolis import galaxy

SCREENS = ("title", "chart", "flight", "docked", "buy", "sell", "equip",
           "status", "inventory", "help", "pause")


def open_game(screen, argv=None, rows=24, cols=80):
    """Drive the UI to a screen via the keyboard and return (game, screen)."""
    argv = argv or ["--seed", "1"]
    if screen == "title":
        return support.make_game("", argv, rows, cols)
    if screen == "chart":
        return support.make_game("\n", argv, rows, cols)
    if screen == "flight":
        game, scr = support.make_game("\n", argv, rows, cols)
        game.chart_sel = galaxy.neighbours(1, game.state.pilot.system)[0][1].index
        game.handle(10)
        return game, scr
    if screen in ("docked", "equip", "status", "inventory"):
        game, scr = support.make_game("\n", argv + ["--start-docked"], rows, cols)
        if screen in ("equip", "status", "inventory"):
            support.pick(game, screen)
        return game, scr
    if screen in ("buy", "sell"):
        game, scr = support.make_game("\n", argv + ["--start-docked"], rows, cols)
        support.pick(game, screen)
        return game, scr
    if screen == "help":
        game, scr = support.make_game("\n?", argv, rows, cols)
        return game, scr
    if screen == "pause":
        game, scr = support.make_game("\n~R", argv, rows, cols)
        game.chart_sel = galaxy.neighbours(1, game.state.pilot.system)[0][1].index
        game.handle(10)
        game.handle(27)
        return game, scr
    raise AssertionError(screen)


class ScreenTest(unittest.TestCase):
    def test_every_screen_renders_at_the_minimum_size(self):
        for name in SCREENS:
            with self.subTest(screen=name):
                game, scr = open_game(name)
                self.assertEqual(game.screen, name)
                text = support.draw(game, scr)
                if name != "title":
                    self.assertIn("CORIOLIS", text)
                self.assertLessEqual(max(len(line) for line in text.split("\n")), 80)

    def test_every_screen_renders_at_a_large_size(self):
        for name in SCREENS:
            with self.subTest(screen=name):
                game, scr = open_game(name, rows=32, cols=100)
                text = support.draw(game, scr)
                self.assertLessEqual(max(len(line) for line in text.split("\n")), 100)

    def test_header_shows_the_system_name_and_credits(self):
        game, scr = open_game("chart")
        text = support.draw(game, scr)
        self.assertIn("LAVE", text)
        self.assertIn("CR 100.0", text)
        self.assertIn("CLEAN", text)

    def test_small_terminal_asks_for_resize(self):
        game, scr = support.make_game("", rows=18, cols=60)
        text = support.draw(game, scr)
        self.assertIn("bigger terminal", text)
        self.assertIn("60x18", text)


class FlowTest(unittest.TestCase):
    def test_new_game_opens_the_chart(self):
        game, scr = support.make_game("\n")
        self.assertEqual(game.screen, "chart")
        self.assertIsNotNone(game.state)
        self.assertEqual(game.state.system.name, "Lave")

    def test_chart_arrow_moves_the_selection(self):
        game, _ = support.make_game("\n")
        before = game.chart_sel
        game.handle(support.KEYS["right"])
        self.assertNotEqual(game.chart_sel, before)

    def test_jump_from_chart_enters_flight(self):
        game, _ = support.make_game("\n")
        neighbour = galaxy.neighbours(1, game.state.pilot.system)[0][1]
        game.chart_sel = neighbour.index
        game.handle(10)
        self.assertEqual(game.screen, "flight")
        self.assertIsNotNone(game.state.jump)
        self.assertEqual(game.state.jump["index"], neighbour.index)

    def test_jump_completes_and_charges_fuel(self):
        game, _ = support.make_game("\n")
        dist, neighbour = galaxy.neighbours(1, game.state.pilot.system)[0]
        game.chart_sel = neighbour.index
        game.handle(10)
        for _ in range(200):
            game.step_sim(1 / 60)
        self.assertIsNone(game.state.jump)
        self.assertEqual(game.state.pilot.system, neighbour.index)
        self.assertAlmostEqual(game.state.pilot.fuel, 7.0 - dist, places=1)

    def test_cannot_jump_without_range(self):
        game, _ = support.make_game("\n")
        game.state.pilot.fuel = 0.0
        game.chart_sel = galaxy.neighbours(1, game.state.pilot.system)[0][1].index
        game.handle(10)
        self.assertEqual(game.screen, "chart")
        self.assertIsNone(game.state.jump)

    def test_buying_cargo_costs_credits(self):
        game, scr = open_game("buy")
        credits = game.state.pilot.credits
        game.handle(10)
        self.assertLess(game.state.pilot.credits, credits)
        self.assertTrue(game.state.pilot.cargo)

    def test_selling_cargo_earns_credits(self):
        game, scr = open_game("sell")
        game.state.pilot.add_cargo("furs", 5)
        credits = game.state.pilot.credits
        game.handle(10)
        self.assertGreater(game.state.pilot.credits, credits)
        self.assertEqual(game.state.pilot.cargo.get("furs"), 4)

    def test_selling_at_the_same_station_is_a_loss(self):
        game, scr = open_game("buy")
        start = game.state.pilot.credits
        game.handle(10)                      # buy one tonne
        game.handle(27)                      # back to the station
        support.pick(game, "sell")
        game.handle(10)                      # sell it straight back
        self.assertLess(game.state.pilot.credits, start)

    def test_launch_returns_to_flight(self):
        game, _ = open_game("docked")
        support.pick(game, "launch")
        self.assertEqual(game.screen, "flight")
        self.assertGreaterEqual(game.state.flight.pos.length(), 2000)

    def test_docked_autosaves(self):
        game, _ = open_game("docked")
        self.assertTrue(game.has_save)

    def test_help_returns_to_where_it_came_from(self):
        game, _ = support.make_game("\n?")
        self.assertEqual(game.screen, "help")
        game.handle(27)
        self.assertEqual(game.screen, "chart")

    def test_pause_resumes(self):
        game, _ = open_game("pause")
        game.handle(10)
        self.assertEqual(game.screen, "flight")


if __name__ == "__main__":
    unittest.main()
