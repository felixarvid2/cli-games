"""Every screen, at every supported size, in Unicode, ASCII and monochrome."""
import unittest

import support
from coriolis import galaxy, missions

SIZES = ((78, 24), (80, 24), (100, 32))
MODES = (("utf", []), ("ascii", ["--no-utf"]), ("mono", ["--no-colour"]))


def open_screen(name, argv, rows, cols):
    game, scr = support.make_game("\n", argv, rows, cols)
    if name == "docked":
        return game, scr
    if name == "title":
        return support.make_game("", argv, rows, cols)
    if name in ("missions", "journal", "buy", "sell", "equip", "shipyard",
                "status", "inventory"):
        support.pick(game, name)
        return game, scr
    support.pick(game, "launch")
    if name == "flight":
        return game, scr
    if name == "chart":
        game.handle(ord("h"))
    elif name == "status2":
        game.handle(ord("2"))
    elif name == "inventory2":
        game.handle(ord("3"))
    elif name == "journal2":
        game.handle(ord("4"))
    elif name == "help":
        game.handle(ord("?"))
    elif name == "pause":
        game.handle(support.KEYS["esc"])
    return game, scr


MARKERS = {
    "title": "New game",
    "docked": "DOCKED",
    "missions": "MISSION BOARD",
    "journal": "JOURNAL",
    "buy": "BUY",
    "sell": "SELL",
    "equip": "EQUIPMENT",
    "shipyard": "SHIPYARD",
    "status": "PILOT STATUS",
    "inventory": "CARGO",
    "flight": "SPD",
    "chart": "CHART",
    "status2": "PILOT STATUS",
    "inventory2": "CARGO",
    "journal2": "JOURNAL",
    "help": "FLIGHT",
    "pause": "PAUSED",
}


class ScreenMatrixTest(unittest.TestCase):
    def test_every_screen_renders_with_content_at_every_size_and_mode(self):
        for name, marker in MARKERS.items():
            for cols, rows in SIZES:
                for mode, extra in MODES:
                    with self.subTest(screen=name, size=f"{cols}x{rows}", mode=mode):
                        argv = ["--seed", "1"] + extra
                        game, scr = open_screen(name, argv, rows, cols)
                        support.draw(game, scr)
                        text = scr.text()
                        self.assertIn(marker, text)
                        self.assertLessEqual(
                            max(len(line) for line in text.split("\n")), cols)
                        self.assertTrue(text.strip())

    def test_monochrome_does_not_rely_on_glyphs_only(self):
        game, scr = open_screen("docked", ["--seed", "1", "--no-utf"], 24, 80)
        text = support.draw(game, scr)
        self.assertNotIn("\u2588", text)
        self.assertIn("Missions", text)

    def test_flight_hud_shows_the_docking_instrument(self):
        game, scr = open_screen("flight", ["--seed", "1"], 24, 80)
        support.draw(game, scr)
        text = scr.text()
        self.assertIn("DOCK", text)
        self.assertIn("lat", text)
        self.assertIn("roll", text)

    def test_chart_shows_route_when_planned(self):
        game, scr = support.make_game("\n", ["--seed", "1"])
        support.pick(game, "launch")
        game.handle(ord("h"))
        game.chart_sel = 40
        game.handle(ord("p"))
        text = support.draw(game, scr)
        self.assertIn("ROUTE", text)
        self.assertIn("jumps", text)

    def test_missions_screen_lists_a_contract_with_its_details(self):
        game, scr = support.make_game("\n", ["--seed", "1"])
        support.pick(game, "missions")
        text = support.draw(game, scr)
        offer = missions.offers(game.state)[0]
        self.assertIn(offer.dest_name(), text)
        self.assertIn("Pay", text)
        self.assertIn("Deadline", text)

    def test_docked_screen_shows_the_tutorial_step(self):
        game, scr = support.make_game("\n", ["--seed", "1"])
        text = support.draw(game, scr)
        self.assertIn("TUTORIAL 1/5", text)
        self.assertIn("contract", text)

    def test_shipyard_shows_both_hulls(self):
        game, scr = support.make_game("\n", ["--seed", "1"])
        support.pick(game, "shipyard")
        text = support.draw(game, scr)
        self.assertIn("Cobra Mk III", text)
        self.assertIn("Adder", text)
        self.assertIn("Cost", text)

    def test_resize_screen_at_77_columns(self):
        game, scr = support.make_game("\n", ["--seed", "1"], 24, 77)
        text = support.draw(game, scr)
        self.assertIn("bigger terminal", text)


if __name__ == "__main__":
    unittest.main()
