"""Shared test helpers: a fake terminal for the curses UI."""

import curses
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# The bits of curses that need a real terminal.
curses.curs_set = lambda n: None
curses.start_color = lambda: None
curses.use_default_colors = lambda: None
curses.init_pair = lambda *a: None
curses.color_pair = lambda n: 0
curses.doupdate = lambda: None
curses.COLORS = 256


class FakeScreen:
    def __init__(self, h=24, w=80):
        self.h, self.w = h, w
        self.grid = [[" "] * w for _ in range(h)]
        self.attr = [[0] * w for _ in range(h)]

    def getmaxyx(self):
        return self.h, self.w

    def addstr(self, y, x, s, attr=0):
        if not 0 <= y < self.h:
            return
        for i, ch in enumerate(s):
            if 0 <= x + i < self.w:
                self.grid[y][x + i] = ch
                self.attr[y][x + i] = attr

    def erase(self):
        self.grid = [[" "] * self.w for _ in range(self.h)]
        self.attr = [[0] * self.w for _ in range(self.h)]

    def noutrefresh(self):
        pass

    def refresh(self):
        pass

    def timeout(self, ms):
        pass

    def keypad(self, flag):
        pass

    def getch(self):
        return -1

    def text(self):
        return "\n".join("".join(row) for row in self.grid)


KEYS = {"up": curses.KEY_UP, "down": curses.KEY_DOWN,
        "left": curses.KEY_LEFT, "right": curses.KEY_RIGHT,
        "enter": 10, "esc": 27}


def make_game(keys="", argv=None, rows=24, cols=80):
    """Build a Game on a fake screen and type `keys` at it."""
    from coriolis import ui
    opts = ui.parse_args(argv or ["--seed", "1"])
    screen = FakeScreen(rows, cols)
    game = ui.Game(screen, opts)
    i = 0
    while i < len(keys):
        if keys[i] == "~" and keys[i:i + 2] in ("~U", "~D", "~L", "~R"):
            game.handle(KEYS[{"~U": "up", "~D": "down", "~L": "left",
                             "~R": "right"}[keys[i:i + 2]]])
            i += 2
        elif keys[i] == "~":
            game.handle(KEYS["enter"])
            i += 1
        else:
            game.handle(ord(keys[i]))
            i += 1
    return game, screen


def draw(game, screen):
    screen.erase()
    game.render()
    return screen.text()


def pick(game, action):
    """Choose a station menu entry by its action key."""
    actions = [key for key, _ in game.docked_items()]
    game.docked_sel = actions.index(action)
    game.handle(10)
