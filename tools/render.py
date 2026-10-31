#!/usr/bin/env python3
"""Render CORIOLIS screens headlessly.

Runs the real Game class against a fake screen, so the layout can be checked
(and unit tested) without a terminal. Keys are typed with a tiny script:
ordinary characters as themselves, and ~U ~D ~L ~R ~E for the arrows and
return. `--attrs` marks reverse-video cells with '#' so cursor highlights are
visible in the dump.
"""
import argparse
import curses
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# The parts of curses that need an initialised terminal.
curses.curs_set = lambda n: None
curses.start_color = lambda: None
curses.use_default_colors = lambda: None
curses.init_pair = lambda *a: None
curses.color_pair = lambda n: 0
curses.doupdate = lambda: None
curses.COLORS = 256

from coriolis import ui  # noqa: E402


class FakeScreen:
    def __init__(self, h, w):
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
        return "\n".join("".join(row).rstrip() for row in self.grid)

    def highlights(self):
        out = []
        for row, attrs in zip(self.grid, self.attr):
            out.append("".join(ch if not (a & curses.A_REVERSE) else "#"
                               for ch, a in zip(row, attrs)).rstrip())
        return "\n".join(out)


SPECIAL = {"~U": curses.KEY_UP, "~D": curses.KEY_DOWN, "~L": curses.KEY_LEFT,
           "~R": curses.KEY_RIGHT, "~E": 10}


def play(opts, keys, contacts=0):
    screen = FakeScreen(opts.rows, opts.cols)
    game = ui.Game(screen, opts)
    i = 0
    while i < len(keys):
        pair = keys[i:i + 2]
        if pair in SPECIAL:
            game.handle(SPECIAL[pair])
            i += 2
        else:
            game.handle(ord(keys[i]))
            i += 1
    if contacts and game.state is not None:
        from coriolis import combat
        from coriolis.flight import Vec3
        names = ["cobra", "sidewinder", "python", "mamba"]
        for i in range(contacts):
            c = combat.make("ship", names[i % len(names)],
                            Vec3(-700 + 500 * i, 140 - 90 * i, 1300 + 500 * i),
                            hostile=(i % 2 == 0))
            game.state.contacts.append(c)
        game.state.missile_target = game.state.contacts[0]
    screen.erase()
    getattr(game, "draw_" + game.screen)()
    return game, screen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keys", default="")
    ap.add_argument("--cols", type=int, default=80)
    ap.add_argument("--rows", type=int, default=24)
    ap.add_argument("--attrs", action="store_true")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--start-docked", action="store_true")
    ap.add_argument("--contacts", type=int, default=0)
    ns = ap.parse_args()
    keys = ns.keys.encode().decode("unicode_escape")
    argv = ["--seed", str(ns.seed)]
    if ns.start_docked:
        argv.append("--start-docked")
    opts = ui.parse_args(argv)
    opts.rows, opts.cols = ns.rows, ns.cols
    game, screen = play(opts, keys, ns.contacts)
    print(f"# screen={game.screen}  {ns.cols}x{ns.rows}")
    print(screen.highlights() if ns.attrs else screen.text())


if __name__ == "__main__":
    main()
