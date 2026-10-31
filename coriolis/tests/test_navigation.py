"""Screen navigation: every menu must be escapable, and back must be right."""
import unittest

import support
from coriolis import galaxy

ESC = support.KEYS["esc"]
ENTER = support.KEYS["enter"]


def docked_game(argv=None):
    return support.make_game("\n", (argv or ["--seed", "1"]) + ["--start-docked"])


def flight_game():
    game, scr = support.make_game("\n", ["--seed", "1"])
    support.pick(game, "launch")
    assert game.screen == "flight", game.screen
    return game, scr


class EscapeTest(unittest.TestCase):
    def test_escape_from_a_station_submenu_returns_to_the_station(self):
        for action in ("buy", "sell", "equip", "status", "inventory"):
            game, _ = docked_game()
            support.pick(game, action)
            self.assertEqual(game.screen, action)
            game.handle(ESC)
            self.assertEqual(game.screen, "docked", action)

    def test_escape_from_a_submenu_then_the_station_opens_pause(self):
        game, _ = docked_game()
        support.pick(game, "buy")
        game.handle(ESC)
        self.assertEqual(game.screen, "docked")
        game.handle(ESC)
        self.assertEqual(game.screen, "pause")
        game.handle(ESC)
        self.assertEqual(game.screen, "docked")
        self.assertNotIn("pause", game.stack)

    def test_escape_from_flight_pauses_and_resumes(self):
        game, _ = flight_game()
        game.handle(ESC)
        self.assertEqual(game.screen, "pause")
        game.handle(ESC)
        self.assertEqual(game.screen, "flight")

    def test_resume_returns_to_the_screen_the_pause_came_from(self):
        game, _ = flight_game()
        game.handle(ESC)
        game.handle(ENTER)                     # Resume is the first entry
        self.assertEqual(game.screen, "flight")
        self.assertEqual(game.stack[-1], "flight")
        self.assertNotIn("pause", game.stack)

    def test_escape_from_the_chart_returns_to_flight(self):
        game, _ = flight_game()
        game.handle(ord("h"))
        self.assertEqual(game.screen, "chart")
        game.handle(ESC)
        self.assertEqual(game.screen, "flight")

    def test_help_returns_to_where_it_was_opened(self):
        game, _ = docked_game()
        game.handle(ord("?"))
        self.assertEqual(game.screen, "help")
        game.handle(ESC)
        self.assertEqual(game.screen, "docked")

        game, _ = flight_game()
        game.handle(ord("?"))
        self.assertEqual(game.screen, "help")
        game.handle(ord("?"))
        self.assertEqual(game.screen, "flight")

    def test_help_from_the_pause_menu_returns_to_the_pause_menu(self):
        game, _ = flight_game()
        game.handle(ESC)
        game.pause_sel = 1                       # Controls
        game.handle(ENTER)
        self.assertEqual(game.screen, "help")
        game.handle(ESC)
        self.assertEqual(game.screen, "pause")
        game.handle(ESC)
        self.assertEqual(game.screen, "flight")

    def test_status_and_inventory_return_to_their_own_context(self):
        game, _ = flight_game()
        game.handle(ord("2"))
        self.assertEqual(game.screen, "status")
        game.handle(ESC)
        self.assertEqual(game.screen, "flight")
        game.handle(ord("3"))
        self.assertEqual(game.screen, "inventory")
        game.handle(ESC)
        self.assertEqual(game.screen, "flight")

        game, _ = docked_game()
        support.pick(game, "status")
        game.handle(ESC)
        self.assertEqual(game.screen, "docked")

    def test_escape_on_the_title_screen_does_nothing(self):
        game, _ = support.make_game("", ["--seed", "1"])
        game.handle(ESC)
        self.assertEqual(game.screen, "title")
        self.assertEqual(game.stack, ["title"])


class CycleTest(unittest.TestCase):
    def test_opening_and_closing_menus_repeatedly_never_traps(self):
        game, _ = docked_game()
        for _ in range(6):
            for action in ("buy", "equip", "status", "inventory"):
                support.pick(game, action)
                self.assertEqual(game.screen, action)
                game.handle(ESC)
                self.assertEqual(game.screen, "docked")
        self.assertEqual(game.stack, ["docked"])

    def test_pausing_repeatedly_keeps_the_stack_flat(self):
        game, _ = flight_game()
        for _ in range(5):
            game.handle(ESC)
            self.assertEqual(game.screen, "pause")
            game.handle(ESC)
            self.assertEqual(game.screen, "flight")
        self.assertEqual(game.stack.count("pause"), 0)
        self.assertLessEqual(len(game.stack), 3)

    def test_pause_from_the_station_resumes_the_station(self):
        game, _ = docked_game()
        game.handle(ESC)
        self.assertEqual(game.screen, "pause")
        game.handle(ENTER)                       # Resume
        self.assertEqual(game.screen, "docked")

    def test_quitting_to_title_clears_the_stack(self):
        game, _ = flight_game()
        game.handle(ESC)
        game.pause_sel = 2                       # Quit to title
        game.handle(ENTER)
        self.assertEqual(game.screen, "title")
        self.assertEqual(game.stack, ["title"])
        self.assertIsNone(game.state)


if __name__ == "__main__":
    unittest.main()
