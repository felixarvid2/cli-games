import unittest

import support
from coriolis import galaxy, missions

SCREENS = ("title", "chart", "flight", "docked", "buy", "sell", "equip",
           "status", "inventory", "help", "pause")


def open_game(screen, argv=None, rows=24, cols=80):
    """Drive the UI to a screen with the keyboard."""
    argv = argv or ["--seed", "1"]
    if screen == "title":
        return support.make_game("", argv, rows, cols)
    game, scr = support.make_game("\n", argv, rows, cols)   # docked
    if screen == "docked":
        return game, scr
    if screen in ("buy", "sell", "equip", "status", "inventory", "missions"):
        support.pick(game, screen)
        return game, scr
    support.pick(game, "launch")                            # flight
    if screen == "flight":
        return game, scr
    action = {"chart": "h", "status": "2", "inventory": "3"}.get(screen)
    if action:
        game.handle(ord(action))
        return game, scr
    if screen == "help":
        game.handle(ord("?"))
        return game, scr
    if screen == "pause":
        game.handle(support.KEYS["esc"])
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
    def test_new_game_starts_docked_with_a_contract(self):
        game, scr = support.make_game("\n")
        self.assertEqual(game.screen, "docked")
        self.assertIsNotNone(game.state)
        self.assertEqual(game.state.system.name, "Lave")
        self.assertTrue(any(m.tutorial for m in missions.offers(game.state)))
        text = support.draw(game, scr)
        self.assertIn("TUTORIAL 1/5", text)

    def test_chart_arrow_moves_the_selection(self):
        game, _ = open_game("chart")
        before = game.chart_sel
        game.handle(support.KEYS["right"])
        self.assertNotEqual(game.chart_sel, before)

    def test_jump_from_chart_enters_flight(self):
        game, _ = open_game("chart")
        neighbour = galaxy.neighbours(1, game.state.pilot.system)[0][1]
        game.chart_sel = neighbour.index
        game.handle(10)
        self.assertEqual(game.screen, "flight")
        self.assertIsNotNone(game.state.jump)
        self.assertEqual(game.state.jump["index"], neighbour.index)

    def test_jump_completes_and_charges_fuel(self):
        game, _ = open_game("chart")
        dist, neighbour = galaxy.neighbours(1, game.state.pilot.system)[0]
        game.chart_sel = neighbour.index
        game.handle(10)
        for _ in range(200):
            game.step_sim(1 / 60)
        self.assertIsNone(game.state.jump)
        self.assertEqual(game.state.pilot.system, neighbour.index)
        self.assertAlmostEqual(game.state.pilot.fuel, 7.0 - dist, places=1)

    def test_cannot_jump_without_range(self):
        game, _ = open_game("chart")
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
        game, _ = support.make_game("\n")
        game.handle(ord("?"))
        self.assertEqual(game.screen, "help")
        game.handle(27)
        self.assertEqual(game.screen, "docked")

    def test_pause_resumes(self):
        game, _ = open_game("pause")
        game.handle(10)
        self.assertEqual(game.screen, "flight")


if __name__ == "__main__":
    unittest.main()
