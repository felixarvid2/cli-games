"""Curses front end for CORIOLIS."""

import argparse
import curses
import math
import os
import sys
import time

from . import __version__, combat, galaxy, sketch
from . import visuals as V
from .core import (GameState, clear_save, load_profile, save_profile)
from .data import GOOD_BY_KEY, MAX_FUEL, MAX_MISSILES, rank_for
from .flight import Mat3, Vec3
from .market import Market
from . import station as st

LOGO = (
    "  ____ ___  ____ ___ _     ___ _   _ ____  ",
    " / ___/ _ \\|  _ \\_ _| |   |_ _| | | / ___| ",
    "| |  | | | | |_) | || |    | || | | \\___ \\ ",
    "| |__| |_| |  _ <| || |___ | || |_| |___) |",
    " \\____\\___/|_| \\_\\___|_____|___|\\___/|____/ ",
)

MENU = ("New game", "Continue", "Controls", "Quit")


def keyname(ch):
    if ch in (10, 13) or ch == curses.KEY_ENTER:
        return "enter"
    if ch == 27:
        return "esc"
    if ch == curses.KEY_UP:
        return "up"
    if ch == curses.KEY_DOWN:
        return "down"
    if ch == curses.KEY_LEFT:
        return "left"
    if ch == curses.KEY_RIGHT:
        return "right"
    if ch == curses.KEY_BACKSPACE:
        return "backspace"
    if ch == 9:
        return "tab"
    if 0 <= ch < 256:
        try:
            return chr(ch).lower()
        except ValueError:
            return ""
    return ""


class Game:
    def __init__(self, scr, opts):
        self.scr = scr
        self.opts = opts
        self.utf = "utf" in (sys.stdout.encoding or "").lower()
        self.g = V.glyphs(self.utf)
        self.art = opts.art
        self.seed = opts.seed
        self.h, self.w = scr.getmaxyx()
        try:
            curses.curs_set(0)
        except curses.error:
            pass
        scr.keypad(True)
        self.attrs = self.init_colours(not opts.no_colour)
        self.screen = "title"
        self.menu = 0
        self.state = None
        self.profile = load_profile()
        self.has_save = GameState.load() is not None
        self.t = 0.0
        self.last = time.monotonic()
        self.acc = 0.0
        self.axes = {"pitch": 0.0, "roll": 0.0}
        self.target_speed = 0.0
        self.chart_sel = galaxy.START_INDEX
        self.docked_sel = 0
        self.market_sel = 0
        self.equip_sel = 0
        self.qty = 1
        self.help_from = "title"
        self.toast = ""
        self.toast_until = 0.0
        self.flash = 0.0
        self.autodock = 0.0
        self.frames = 0
        self.pause_sel = 0

    # -- colours ---------------------------------------------------------
    def init_colours(self, enabled=True):
        attrs = {"default": 0}
        try:
            curses.start_color()
            curses.use_default_colors()
            table = V.COLOUR if (enabled and curses.COLORS >= 256) else V.FALLBACK
            for i, (name, idx) in enumerate(table.items(), start=1):
                curses.init_pair(i, idx, -1)
                attrs[name] = curses.color_pair(i)
                attrs[name + "!"] = curses.color_pair(i) | curses.A_BOLD
        except curses.error:
            pass
        return attrs

    def C(self, name, bold=False):
        if bold:
            return self.attrs.get(name + "!", self.attrs.get(name, 0))
        return self.attrs.get(name, 0)

    # -- drawing primitives ----------------------------------------------
    def put(self, y, x, s, attr=0):
        if y < 0 or y >= self.h or x >= self.w or not s:
            return
        if x < 0:
            s = s[-x:]
            x = 0
        s = s[:max(0, self.w - x)]
        if not s:
            return
        try:
            self.scr.addstr(y, x, s, attr)
        except curses.error:
            pass

    def centre(self, y, s, attr=0):
        self.put(y, max(0, (self.w - len(s)) // 2), s, attr)

    def rule(self, y, colour="navy", ch=None):
        self.put(y, 1, (ch or self.g["h"]) * max(0, self.w - 2), self.C(colour))

    def bar(self, y, x, width, value, maximum, colour="green"):
        self.put(y, x, V.bar(value, maximum, width, self.utf), self.C(colour))

    def chip(self, y, x, text, colour="gold", bold=True):
        self.put(y, x, text, self.C(colour, bold))

    def keycap(self, y, x, key, label, colour="gold"):
        self.put(y, x, key, self.C(colour, True))
        self.put(y, x + len(key) + 1, label, self.C("dim"))

    def box(self, y, x, h, w, colour="cyan", title=None):
        if h < 2 or w < 2:
            return
        g = self.g
        attr = self.C(colour)
        top = g["tl"] + g["h"] * (w - 2) + g["tr"]
        bot = g["bl"] + g["h"] * (w - 2) + g["br"]
        self.put(y, x, top, attr)
        for row in range(1, h - 1):
            self.put(y + row, x, g["v"], attr)
            self.put(y + row, x + w - 1, g["v"], attr)
        self.put(y + h - 1, x, bot, attr)
        if title:
            self.put(y, x + 2, " " + V.cut(title, w - 6) + " ", self.C(colour, True))

    def toast_now(self, text, dur=2.2):
        self.toast = text
        self.toast_until = time.monotonic() + dur

    # -- main loop -------------------------------------------------------
    def loop(self):
        self.scr.timeout(16)
        while self.screen != "quit":
            now = time.monotonic()
            dt = min(0.1, now - self.last)
            self.last = now
            self.t += dt
            self.frames += 1
            self.h, self.w = self.scr.getmaxyx()
            self.tick(dt)
            self.scr.erase()
            self.render(now)
            self.scr.noutrefresh()
            curses.doupdate()
            ch = self.scr.getch()
            if ch != -1:
                self.handle(ch)

    def render(self, now=None):
        """Draw the current screen, or the resize notice if it cannot fit."""
        self.h, self.w = self.scr.getmaxyx()
        if self.h < 24 or self.w < 78:
            self.draw_resize()
            return
        getattr(self, "draw_" + self.screen)()
        now = time.monotonic() if now is None else now
        if self.toast and now < self.toast_until:
            msg = V.cut(" " + self.toast + " ", self.w - 2)
            self.put(self.h - 1, 1, msg.ljust(self.w - 2),
                     self.C("gold", True) | curses.A_REVERSE)

    def handle(self, ch):
        key = keyname(ch)
        if key == "" and ch != -1:
            return
        if key == "esc" and self.screen not in ("title", "dead"):
            if self.screen == "help":
                self.screen = self.help_from
            else:
                self.help_from = self.screen
                self.screen = "pause"
            return
        if key == "?" and self.screen != "help":
            self.help_from = self.screen
            self.screen = "help"
            return
        handler = getattr(self, "key_" + self.screen, None)
        if handler:
            handler(key)

    def tick(self, dt):
        state = self.state
        if state is None or self.screen != "flight":
            return
        for axis in self.axes:
            self.axes[axis] *= math.exp(-dt / 0.11)
            if abs(self.axes[axis]) < 0.01:
                self.axes[axis] = 0.0
        self.acc += dt
        steps = 0
        while self.acc >= 1.0 / 60.0 and steps < 6:
            self.step_sim(1.0 / 60.0)
            self.acc -= 1.0 / 60.0
            steps += 1

    def step_sim(self, dt):
        state = self.state
        state.time += dt
        f = state.flight
        # Speed is a wanted value, approached at the ship's acceleration.
        diff = self.target_speed - f.speed
        if abs(diff) < 1.0:
            f.speed = self.target_speed
        else:
            f.speed += max(-f.brake * dt, min(f.accel * dt, diff))
        f.step(self.axes["pitch"], self.axes["roll"], 0.0, dt)
        if state.jump:
            state.jump["left"] -= dt
            if state.jump["left"] <= 0:
                state.complete_jump(state.jump["index"], state.jump["cost"])
                self.chart_sel = state.pilot.system
                self.target_speed = 200.0
        combat.step(state, dt)
        state.station.step(dt)
        self.autodock = max(0.0, self.autodock - dt)
        if state.pilot.has("docking"):
            self.auto_dock(dt)
        status, text = state.station.dock_check(f)
        if status == "dock":
            self.dock()
        elif status == "crash":
            self.crash(text)
        if state.dead:
            self.die()

    def auto_dock(self, dt):
        """The docking computer: line up the mouth, roll with the slot, creep in."""
        state = self.state
        f = state.flight
        station = state.station
        if (f.pos - station.pos).length() > 3000:
            return
        goal = Vec3(0.0, 0.0, -120.0)          # just inside the slot mouth
        delta = goal - f.pos
        to_go = delta.length()
        speed = max(40.0, min(280.0, to_go * 1.2))
        f.speed = speed
        self.target_speed = speed
        if to_go > 0.5:
            f.pos = f.pos + delta.norm() * min(to_go, speed * dt)
        combat._steer(f, station.pos, dt, 2.0)
        # Roll until our up vector matches the rotating slot.
        if station.roll_error(f.orient.up) > math.radians(1.0):
            slot_up = station.slot_vector()
            up = f.orient.up
            signed = math.atan2(up.x * slot_up.y - up.y * slot_up.x,
                                up.x * slot_up.x + up.y * slot_up.y)
            f.orient = (f.orient @ Mat3.rot_z(signed * min(1.0, 5.0 * dt))).renormalise()
        self.axes = {"pitch": 0.0, "roll": 0.0}

    def dock(self):
        state = self.state
        state.dock()
        self.screen = "docked"
        self.docked_sel = 0
        self.market_sel = 0
        self.equip_sel = 0
        self.target_speed = 0.0
        self.axes = {"pitch": 0.0, "roll": 0.0}
        state.save()
        self.has_save = True

    def crash(self, text):
        state = self.state
        combat.damage_player(state, 45.0)
        state.flight.pos = Vec3(0.0, 0.0, -3000.0)
        state.flight.speed = 0.0
        self.target_speed = 0.0
        state.say("Crash: " + text)
        self.toast_now(text, 2.5)
        if state.dead:
            self.die()

    def die(self):
        state = self.state
        if state.pilot.has("escape"):
            state.pilot.equipment.discard("escape")
            state.pilot.cargo = {}
            state.pilot.deaths += 1
            state.hull = 50.0
            state.shields = {"fore": 100.0, "aft": 100.0}
            state.dead = False
            state.dock()
            state.say("Escape capsule fired. You wake up in the station.")
            self.screen = "docked"
            return
        self.profile.deaths += 1
        self.profile.kills = max(self.profile.kills, state.pilot.kills)
        save_profile(self.profile)
        clear_save()
        self.has_save = False
        self.screen = "dead"

    # -- screens ---------------------------------------------------------
    def draw_resize(self):
        self.centre(max(1, self.h // 2 - 1), "CORIOLIS needs a bigger terminal",
                    self.C("gold", True))
        self.centre(self.h // 2 + 1, f"now {self.w}x{self.h}, need 78x24",
                    self.C("dim"))

    def draw_title(self):
        w, h = self.w, self.h
        top = max(1, h // 2 - 9)
        for i, line in enumerate(LOGO):
            self.centre(top + i, line, self.C("gold" if i % 2 else "amber", True))
        self.centre(top + 6, "E L I T E - S T Y L E   S P A C E   T R A D I N G",
                    self.C("cyan"))
        self.centre(top + 7, f"10 GALAXIES {self.g['dot']} 2560 SYSTEMS {self.g['dot']} "
                             f"NO SHIELDS TO HIDE BEHIND", self.C("dim"))
        base = top + 9
        pad = max(len(m) for m in MENU) + 4
        for i, item in enumerate(MENU):
            if item == "Continue" and not self.has_save:
                attr = self.C("faint")
            elif i == self.menu:
                attr = self.C("gold", True) | curses.A_REVERSE
            else:
                attr = self.C("white")
            label = "  " + item.ljust(pad - 4) + "  "
            self.put(base + i * 2, (w - len(label)) // 2, label, attr)
        self.rule(h - 5)
        rank = rank_for(self.profile.kills)
        self.put(h - 4, 2, f"PILOT {rank}", self.C("cyan"))
        self.put(h - 4, w - 24, f"KILLS {self.profile.kills}", self.C("dim"))
        self.put(h - 3, 2, f"v{__version__}", self.C("faint"))
        self.put(h - 3, w - 34, "ENTER select   Q quit", self.C("dim"))

    def key_title(self, key):
        if key in ("up", "w", "k"):
            self.menu = (self.menu - 1) % len(MENU)
        elif key in ("down", "s", "j"):
            self.menu = (self.menu + 1) % len(MENU)
        elif key in ("enter", "space"):
            item = MENU[self.menu]
            if item == "New game":
                self.new_game()
            elif item == "Continue":
                self.continue_game()
            elif item == "Controls":
                self.help_from = "title"
                self.screen = "help"
            else:
                self.screen = "quit"
        elif key == "q":
            self.screen = "quit"

    def new_game(self):
        self.state = GameState(seed=self.seed)
        if self.opts.galaxy:
            self.state.pilot.galaxy = max(1, min(galaxy.GALAXY_COUNT, self.opts.galaxy))
        self.state.pilot.system = galaxy.START_INDEX
        self.chart_sel = self.state.pilot.system
        self.target_speed = 0.0
        if self.opts.start_docked:
            self.dock()
            self.toast_now("Docked at Lave. Buy low, sell high.", 3.0)
            return
        self.state.launch()
        self.screen = "chart"
        self.toast_now("Welcome, Commander. Pick a destination.", 3.0)

    def continue_game(self):
        state = GameState.load()
        if state is None:
            self.toast_now("No save game found", 2.0)
            return
        self.state = state
        self.chart_sel = state.pilot.system
        if state.mode == "docked":
            self.screen = "docked"
        else:
            state.launch()
            self.target_speed = 200.0
            self.screen = "flight"

    # -- shared header ----------------------------------------------------
    def header(self, left="", right=""):
        state = self.state
        if state is not None:
            p = state.pilot
            self.put(0, 1, "CORIOLIS", self.C("gold", True))
            self.put(0, 11, self.g["dot"], self.C("faint"))
            self.put(0, 13, state.system.name.upper(), self.C("white", True))
            fuel = f"FUEL {p.fuel:4.1f} LY"
            self.put(0, self.w - 52, fuel, self.C("cyan" if p.fuel > 0.5 else "red"))
            self.put(0, self.w - 38, f"CR {V.money(p.credits)}", self.C("gold"))
            legal = p.legal_name.upper()
            colour = {"CLEAN": "green", "OFFENDER": "amber", "FUGITIVE": "red"}[legal]
            self.put(0, self.w - 18, legal, self.C(colour, True))
        else:
            self.put(0, 1, left, self.C("gold", True))
        if right:
            self.put(0, max(1, self.w - len(right) - 2), right, self.C("dim"))
        self.rule(1)

    # -- chart ------------------------------------------------------------
    def chart_geometry(self):
        systems = galaxy.galaxy(self.state.pilot.galaxy)
        minx, miny, maxx, maxy = galaxy.chart_bounds(systems)
        map_x0, map_y0 = 2, 4
        map_w, map_h = max(20, self.w - 36), max(8, self.h - 9)
        spanx = max(1e-6, maxx - minx)
        spany = max(1e-6, maxy - miny)
        return systems, (map_x0, map_y0, map_w, map_h, minx, miny, spanx, spany)

    def chart_pos(self, system, geo):
        x0, y0, w, h, minx, miny, spanx, spany = geo
        px = x0 + int(round((system.x - minx) / spanx * (w - 1)))
        py = y0 + int(round((1.0 - (system.y - miny) / spany) * (h - 1)))
        return px, py

    def draw_chart(self):
        state = self.state
        systems, geo = self.chart_geometry()
        x0, y0, w, h = geo[0], geo[1], geo[2], geo[3]
        here = state.system
        target = galaxy.system(state.pilot.galaxy, self.chart_sel)
        dist = galaxy.distance(here, target)
        self.header()
        self.put(2, 2, f"GALACTIC CHART {state.pilot.galaxy:2d}/{galaxy.GALAXY_COUNT}",
                 self.C("cyan", True))
        self.put(2, 24, f"{here.name.upper()}  {self.g['arrow']}  {target.name.upper()}"
                         f"   {dist:.1f} LY", self.C("white"))
        self.box(y0 - 1, x0 - 1, h + 2, w + 2, "navy")
        reach = set()
        for d, s in galaxy.neighbours(state.pilot.galaxy, here.index):
            reach.add(s.index)
        for s in systems:
            px, py = self.chart_pos(s, geo)
            if s.index == here.index:
                self.put(py, px, "@", self.C("gold", True))
            elif s.index == target.index:
                self.put(py, px, self.g["cursor"], self.C("white", True) | curses.A_REVERSE)
            elif s.index in reach:
                self.put(py, px, self.g["disc"], self.C("green"))
            else:
                self.put(py, px, self.g["dot"], self.C("faint"))
        # A line to the selected system when it is inside one tank.
        if dist <= state.pilot.fuel + 1e-6 and target.index != here.index:
            ax, ay = self.chart_pos(here, geo)
            bx, by = self.chart_pos(target, geo)
            steps = max(abs(bx - ax), abs(by - ay))
            for i in range(1, steps):
                px = ax + round((bx - ax) * i / steps)
                py = ay + round((by - ay) * i / steps)
                if 0 <= px < self.w and 0 <= py < self.h:
                    self.put(py, px, self.g["dot"], self.C("teal"))
        self.draw_chart_labels(systems, geo, here, target, reach, x0, y0, w, h)
        self.draw_chart_panel(target, dist)
        self.put(self.h - 2, 2, "Arrows pick   ENTER/H jump   ESC pause   ? controls",
                 self.C("dim"))

    def draw_chart_labels(self, systems, geo, here, target, reach, x0, y0, w, h):
        placed = []
        for s in (target, here):
            px, py = self.chart_pos(s, geo)
            label = " " + s.name.upper()
            lx = min(max(x0 + 1, px + 1), x0 + w - len(label) - 1)
            ly = min(max(y0 + 1, py), y0 + h - 2)
            box = (lx, ly, lx + len(label))
            clash = any(not (box[2] + 1 < p[0] or box[0] > p[2] + 1) and abs(ly - p[1]) <= 1
                        for p in placed)
            if clash and s is target:
                ly = min(y0 + h - 2, ly + 2)
                lx = max(x0 + 1, lx - 4)
                box = (lx, ly, lx + len(label))
            if clash and s is here:
                continue
            placed.append((lx, ly, lx + len(label)))
            if s.index == here.index:
                colour = "gold"
            else:
                colour = "white"
            self.put(ly, lx, label, self.C(colour, s.index == target.index))

    def draw_chart_panel(self, target, dist):
        pw = 32
        px = self.w - pw - 1
        py = 3
        ph = min(16, self.h - 9)
        fuel_ok = dist <= self.state.pilot.fuel + 1e-6
        self.box(py, px, ph, pw, "cyan", target.name.upper())
        rows = [
            ("Economy", target.economy_short),
            ("Government", target.government_short),
            ("Tech level", str(target.tech)),
            ("Population", f"{target.population:.1f} billion"),
            ("Productivity", str(target.productivity)),
            ("Radius", f"{target.radius} km"),
            ("", ""),
            ("Distance", f"{dist:.1f} LY"),
            ("Fuel cost", f"{dist:.1f} / {self.state.pilot.fuel:.1f} LY"),
            ("", ""),
        ]
        y = py + 1
        for label, value in rows:
            if label:
                self.put(y, px + 2, V.cut(label, 12), self.C("dim"))
                self.put(y, px + 15, V.cut(value, pw - 16), self.C("white"))
            y += 1
        if target.index == self.state.system.index:
            note, colour = "YOU ARE HERE", "gold"
        elif fuel_ok:
            note, colour = "IN RANGE - ENTER TO JUMP", "green"
        else:
            note, colour = "OUT OF RANGE - REFUEL", "red"
        self.put(py + ph - 2, px + 2, V.cut(note, pw - 4), self.C(colour, True))

    def key_chart(self, key):
        state = self.state
        systems = galaxy.galaxy(state.pilot.galaxy)
        if key in ("enter", "h", " "):
            if self.chart_sel == state.pilot.system:
                self.toast_now("Choose another system first")
                return
            if state.begin_jump(self.chart_sel):
                self.screen = "flight"
                self.target_speed = 0.0
                self.axes = {"pitch": 0.0, "roll": 0.0}
            else:
                self.toast_now(state.alert or "Cannot jump")
            return
        if key not in ("up", "down", "left", "right"):
            return
        here = galaxy.system(state.pilot.galaxy, self.chart_sel)
        dx = {"left": -1, "right": 1}.get(key, 0)
        dy = {"down": -1, "up": 1}.get(key, 0)
        best = None
        for s in systems:
            if s.index == here.index:
                continue
            vx, vy = s.x - here.x, s.y - here.y
            if dx and (vx * dx) <= 0.5:
                continue
            if dy and (vy * dy) <= 0.5:
                continue
            score = math.hypot(vx, vy) + abs(vx * dy - vy * dx) * 0.8
            if best is None or score < best[0]:
                best = (score, s)
        if best:
            self.chart_sel = best[1].index

    # -- flight -----------------------------------------------------------
    def paint(self, cv, y0, x0):
        """Blit a sketch.Canvas, one addstr per colour run."""
        for ry, row in enumerate(cv.ch):
            cols = cv.fg[ry]
            x = 0
            n = len(row)
            while x < n:
                colour = cols[x]
                run = x + 1
                while run < n and cols[run] == colour:
                    run += 1
                text = "".join(row[x:run])
                if text.strip():
                    self.put(y0 + ry, x0 + x, text,
                             self.C(colour) if colour else 0)
                x = run

    def level_roll(self):
        f = self.state.flight
        fwd = f.orient.forward
        world_up = Vec3(0.0, 1.0, 0.0)
        want = (world_up - fwd * world_up.dot(fwd))
        if want.length() < 1e-4:
            return
        want = want.norm()
        cur = f.orient.up
        angle = math.atan2(fwd.dot(cur.cross(want)), cur.dot(want))
        f.orient = (f.orient @ Mat3.rot_z(angle)).renormalise()

    def draw_flight(self):
        state = self.state
        self.header()
        vx, vy = 1, 2
        vw = max(20, self.w - 2)
        radar_h = 5 if self.h >= 26 else 3
        vh = max(6, self.h - 13 - (radar_h - 3))
        cv, target = sketch.draw_scene(state, vw, vh, self.art, not self.utf)
        self.paint(cv, vy, vx)
        y = vy + vh
        self.rule(y, "navy")
        f = state.flight
        y += 1
        speed = int(round(f.speed))
        self.put(y, 2, "SPD", self.C("dim"))
        self.bar(y, 6, 12, f.speed, f.max_speed, "green")
        self.put(y, 19, f"{speed:4d} m/s", self.C("white"))
        self.put(y, 31, "FORE", self.C("dim"))
        self.bar(y, 36, 10, state.shields["fore"], 100, "cyan")
        self.put(y, 48, "AFT", self.C("dim"))
        self.bar(y, 52, 10, state.shields["aft"], 100, "cyan")
        self.put(y, 64, f"HULL", self.C("dim"))
        self.bar(y, 69, 8, max(0, state.hull), 100,
                 "green" if state.hull > 40 else "red")
        y += 1
        for i, bank in enumerate(state.banks):
            self.put(y, 2 + i * 9, f"E{i + 1}", self.C("dim"))
            self.bar(y, 5 + i * 9, 5, bank, 25, "amber")
        self.put(y, 40, "MISSILES", self.C("dim"))
        for i in range(MAX_MISSILES):
            on = i < state.pilot.missiles
            self.put(y, 49 + i, self.g["disc"] if on else self.g["ring"],
                     self.C("red" if on else "faint"))
        ecm = "ECM" if state.pilot.has("ecm") else "---"
        self.put(y, 56, ecm, self.C("cyan" if state.pilot.has("ecm") else "faint"))
        bomb = "BOMB" if state.pilot.has("bomb") else "----"
        self.put(y, 61, bomb, self.C("orange" if state.pilot.has("bomb") else "faint"))
        self.put(y, 67, state.pilot.laser.upper()[:6], self.C("gold"))
        y += 1
        self.rule(y, "navy")
        y += 1
        self.draw_radar(y, 2, 15, radar_h)
        self.draw_flight_status(y, 19, target)
        self.draw_flight_hints()

    def draw_radar(self, y, x, w=15, h=3):
        state = self.state
        self.box(y, x - 1, h + 2, w + 2, "navy", "RADAR")
        cells = sketch.radar_contacts(state, w, h)
        for row, col, ch, colour in cells:
            self.put(y + 1 + row, x + col, ch, self.C(colour))
        # The player's ship marker, dead centre.
        self.put(y + 1 + h // 2, x + w // 2, "+", self.C("gold", True))

    def draw_flight_status(self, y, x, target):
        state = self.state
        width = max(10, self.w - x - 2)
        alert = state.alert
        self.put(y, x, "ALERT", self.C("dim"))
        self.put(y, x + 6, V.cut(alert or "None", width - 6),
                 self.C("red" if alert else "faint"))
        y += 1
        if target:
            c, dist = target
            label = f"{c.name} {dist / 1000.0:.1f} km"
            colour = "red" if c.hostile else "green"
            self.put(y, x, "TARGET", self.C("dim"))
            self.put(y, x + 7, V.cut(label, width - 7), self.C(colour))
        else:
            self.put(y, x, "TARGET", self.C("dim"))
            self.put(y, x + 7, "none in sight", self.C("faint"))
        y += 1
        status, text = state.station.dock_check(state.flight)
        dist = (state.flight.pos - state.station.pos).length()
        self.put(y, x, "DOCK", self.C("dim"))
        self.put(y, x + 5, V.cut(f"{dist / 1000.0:.1f} km  {text}", width - 5),
                 self.C("green" if status == "dock" else "white"))
        y += 1
        if state.jump:
            self.put(y, x, "HYPER", self.C("dim"))
            self.put(y, x + 6, f"{state.jump['name'].upper()} in "
                               f"{max(0.0, state.jump['left']):.1f}",
                     self.C("purple", True))
        elif combat.has_mass_lock(state):
            self.put(y, x, "MASS LOCKED", self.C("red", True))
        else:
            self.put(y, x, "HYPER DRIVE READY", self.C("faint"))

    def draw_flight_hints(self):
        hints = (("S/X", "pitch"), (",/.", "roll"), ("A/Z", "speed"),
                 ("SPC", "fire"), ("T", "lock"), ("M", "missile"),
                 ("E", "ECM"), ("H", "chart"), ("L", "level"))
        x = 2
        y = self.h - 2
        for key, label in hints:
            if x + len(key) + len(label) + 2 >= self.w:
                break
            self.put(y, x, key, self.C("gold", True))
            self.put(y, x + len(key) + 1, label, self.C("faint"))
            x += len(key) + len(label) + 3

    def key_flight(self, key):
        state = self.state
        if self.opts.classic and key in ("up", "down", "left", "right"):
            return          # 1984: arrows did nothing, you flew with letters
        if key in ("up", "s", "k"):
            self.axes["pitch"] = 1.0
        elif key in ("down", "x", "j"):
            self.axes["pitch"] = -1.0
        elif key in ("left", ","):
            self.axes["roll"] = -1.0
        elif key in ("right", "."):
            self.axes["roll"] = 1.0
        elif key == "a":
            self.target_speed = min(state.flight.max_speed, self.target_speed + 90)
        elif key == "z":
            self.target_speed = max(0.0, self.target_speed - 90)
        elif key in (" ", "enter"):
            hit = combat.fire_laser(state)
            if hit is not None:
                state.say(f"Hit {hit.name}")
        elif key == "t":
            combat.lock_target(state)
        elif key == "m":
            combat.fire_missile(state)
        elif key == "e":
            combat.ecm(state)
        elif key == "b":
            combat.energy_bomb(state)
        elif key == "l":
            self.level_roll()
        elif key in ("h", "1"):
            self.chart_sel = state.pilot.system
            self.screen = "chart"
        elif key == "2":
            self.screen = "status"
        elif key == "3":
            self.screen = "inventory"

    # -- docked -----------------------------------------------------------
    def docked_items(self):
        state = self.state
        items = [("buy", "Buy cargo"), ("sell", "Sell cargo"),
                 ("equip", "Equipment"), ("refuel", "Refuel tanks"),
                 ("repair", "Repair hull"), ("fine", "Clear record"),
                 ("status", "Status"), ("inventory", "Inventory")]
        if state.pilot.has("galactic"):
            items.append(("galactic", "Galactic hyperdrive"))
        items += [("launch", "Launch"), ("save", "Save and quit")]
        return items

    def draw_docked(self):
        state = self.state
        self.header()
        items = self.docked_items()
        self.put(2, 2, f"DOCKED {self.g['dot']} {state.system.name.upper()} STATION",
                 self.C("gold", True))
        self.put(2, 30, f"TECH {state.system.tech:2d}   {state.system.economy_name.upper()}",
                 self.C("dim"))
        for i, (action, label) in enumerate(items):
            y = 4 + i
            if y >= self.h - 4:
                break
            attr = self.C("gold", True) | curses.A_REVERSE if i == self.docked_sel else self.C("white")
            self.put(y, 3, f" {label:<24}", attr)
        self.draw_trade_advice(len(items))
        self.draw_station_panel()
        self.put(self.h - 2, 2, "Arrows pick   ENTER select   ESC pause   ? controls",
                 self.C("dim"))

    def draw_trade_advice(self, after):
        """The best single hop from here: the quickest way to make a credit."""
        state = self.state
        y = 4 + after + 1
        h = 6
        if y + h > self.h - 3:
            return
        from .market import best_routes
        routes = best_routes(state.system, galaxy.galaxy(state.pilot.galaxy),
                             state.pilot)
        self.box(y, 2, h, 44, "navy", "BEST HOP FROM HERE")
        if not routes:
            self.put(y + 2, 4, "Nothing worth carrying. Try elsewhere.", self.C("faint"))
            return
        for i, (score, sysm, good, margin, tonnes) in enumerate(routes[:3]):
            d = galaxy.distance(state.system, sysm)
            line = (f"{sysm.name[:10]:<10} {d:4.1f} LY {good.name[:9]:<9}"
                    f" {tonnes:2d}t {score:+5.0f}")
            self.put(y + 1 + i, 4, V.cut(line, 40), self.C("green" if i == 0 else "white"))

    def draw_station_panel(self):
        state = self.state
        pw = 30
        px = self.w - pw - 2
        py = 3
        ph = min(16, self.h - 8)
        self.box(py, px, ph, pw, "cyan", "STATION SERVICES")
        sysm = state.system
        rows = [("Economy", sysm.economy_short),
                ("Government", sysm.government_short),
                ("Tech level", str(sysm.tech)),
                ("Population", f"{sysm.population:.1f} bn"),
                ("", ""),
                ("Fuel", f"{state.pilot.fuel:.1f} / {MAX_FUEL:.1f} LY"),
                ("Hull", f"{max(0, state.hull):.0f}%"),
                ("Cargo", f"{state.pilot.cargo_used()} / {state.pilot.cargo_cap} t"),
                ("Missiles", f"{state.pilot.missiles} / {MAX_MISSILES}"),
                ("Rank", state.pilot.rank),
                ("Record", state.pilot.legal_name)]
        y = py + 1
        for label, value in rows:
            if label:
                self.put(y, px + 2, V.cut(label, 10), self.C("dim"))
                self.put(y, px + 14, V.cut(value, pw - 16), self.C("white"))
            y += 1

    def key_docked(self, key):
        items = self.docked_items()
        if key in ("up", "w", "k"):
            self.docked_sel = (self.docked_sel - 1) % len(items)
        elif key in ("down", "s", "j"):
            self.docked_sel = (self.docked_sel + 1) % len(items)
        elif key in ("enter", " "):
            action = items[self.docked_sel][0]
            getattr(self, "do_" + action)()

    def do_buy(self):
        self.market_sel = 0
        self.qty = 1
        self.screen = "buy"

    def do_sell(self):
        self.market_sel = 0
        self.qty = 1
        self.screen = "sell"

    def do_equip(self):
        self.equip_sel = 0
        self.screen = "equip"

    def do_status(self):
        self.screen = "status"

    def do_inventory(self):
        self.screen = "inventory"

    def do_refuel(self):
        ok, msg = st.refuel(self.state.pilot)
        self.toast_now(msg if ok else msg, 2.0)

    def do_repair(self):
        damage = 100.0 - max(0.0, self.state.hull)
        ok, msg = st.repair(self.state.pilot, damage)
        if ok:
            self.state.hull = 100.0
        self.toast_now(msg, 2.0)

    def do_fine(self):
        ok, msg = st.fine(self.state.pilot)
        self.toast_now(msg, 2.0)

    def do_galactic(self):
        state = self.state
        p = state.pilot
        p.equipment.discard("galactic")
        p.galaxy += 1
        if p.galaxy > galaxy.GALAXY_COUNT:
            p.galaxy = 1
            if "GRAND MASTER" not in p.badges:
                p.badges.append("GRAND MASTER")
            state.say("You have circled all ten galaxies. GRAND MASTER.")
        p.system = galaxy.START_INDEX
        state.market = Market.for_system(state.system)
        self.chart_sel = p.system
        self.toast_now(f"Galactic jump: galaxy {p.galaxy}/{galaxy.GALAXY_COUNT}", 2.6)

    def do_launch(self):
        state = self.state
        state.launch()
        combat.spawn(state)
        self.target_speed = 0.0
        self.axes = {"pitch": 0.0, "roll": 0.0}
        self.screen = "flight"

    def do_save(self):
        self.state.pilot.system = self.state.system.index
        self.state.mode = "docked"
        self.state.save()
        self.profile.kills = max(self.profile.kills, self.state.pilot.kills)
        self.profile.best_rank = self.state.pilot.rank
        save_profile(self.profile)
        self.toast_now("Progress saved", 1.6)
        self.screen = "title"
        self.has_save = True
        self.state = None

    # -- market -----------------------------------------------------------
    def market_rows(self, mode):
        market = self.state.market
        if mode == "buy":
            return [(k, n, pr, stk) for k, n, pr, stk in market.rows("buy")]
        rows = []
        for key, qty in self.state.pilot.cargo.items():
            good = GOOD_BY_KEY[key]
            rows.append((key, good.name, market.listings[key].sell_price(), qty))
        rows.sort(key=lambda r: r[0])
        return rows

    def draw_market(self, mode):
        state = self.state
        self.header()
        title = "BUY" if mode == "buy" else "SELL"
        self.put(2, 2, f"{title} {self.g['dot']} {state.system.name.upper()}",
                 self.C("gold", True))
        self.put(2, 22, f"CR {V.money(state.pilot.credits)}", self.C("gold"))
        self.put(2, 42, f"HOLD {state.pilot.cargo_used()}/{state.pilot.cargo_cap} t",
                 self.C("cyan"))
        self.put(3, 2, "GOOD", self.C("dim"))
        self.put(3, 24, "PRICE", self.C("dim"))
        self.put(3, 33, "STOCK" if mode == "buy" else "IN HOLD", self.C("dim"))
        self.put(3, 48, "PROFIT" if mode == "sell" else "", self.C("dim"))
        rows = self.market_rows(mode)
        self.market_sel = max(0, min(self.market_sel, max(0, len(rows) - 1)))
        top = 0
        visible = max(4, self.h - 9)
        if self.market_sel >= visible:
            top = self.market_sel - visible + 1
        for i, (key, name, price, count) in enumerate(rows[top:top + visible]):
            idx = i + top
            y = 4 + i
            selected = idx == self.market_sel
            attr = self.C("gold", True) | curses.A_REVERSE if selected else self.C("white")
            self.put(y, 2, f" {V.cut(name, 20):<20}", attr)
            colour = "green" if price < GOOD_BY_KEY[key].base else "red"
            self.put(y, 24, f"{price:8.1f}", self.C(colour) if not selected else attr)
            self.put(y, 34, f"{count:5d}", self.C("cyan") if not selected else attr)
            if mode == "sell":
                profit = price - GOOD_BY_KEY[key].base
                self.put(y, 48, f"{profit:+6.1f}",
                         self.C("green" if profit >= 0 else "red"))
        if not rows:
            self.put(5, 3, "Nothing in the hold." if mode == "sell" else "No stock.",
                     self.C("faint"))
        self.draw_market_side(rows, mode)
        self.put(self.h - 2, 2, "Up/Down pick   Left/Right qty   ENTER trade   ESC back",
                 self.C("dim"))

    def draw_market_side(self, rows, mode):
        pw = 26
        px = self.w - pw - 2
        py = 3
        ph = 11
        self.box(py, px, ph, pw, "navy", "TRADE")
        if not rows:
            return
        key, name, price, count = rows[self.market_sel]
        good = GOOD_BY_KEY[key]
        lines = [(good.name, "gold"),
                 (f"base {good.base:.1f} CR/t", "dim"),
                 ("illegal" if good.illegal else "legal cargo",
                  "red" if good.illegal else "green"),
                 ("", None),
                 (f"QUANTITY {self.qty}", "white"),
                 (f"COST {price * self.qty:.1f} CR", "gold"),
                 ("", None)]
        y = py + 1
        for text, colour in lines:
            if text:
                self.put(y, px + 2, V.cut(text, pw - 4),
                         self.C(colour) if colour else 0)
            y += 1

    def key_market(self, key, mode):
        state = self.state
        rows = self.market_rows(mode)
        if not rows:
            if mode == "sell":
                self.screen = "docked"
            return
        self.market_sel = max(0, min(self.market_sel, len(rows) - 1))
        if key in ("up", "w", "k"):
            self.market_sel = max(0, self.market_sel - 1)
        elif key in ("down", "s", "j"):
            self.market_sel = min(len(rows) - 1, self.market_sel + 1)
        elif key in ("left", "a", "-"):
            self.qty = max(1, self.qty - 1)
        elif key in ("right", "d", "+", "="):
            self.qty = min(99, self.qty + 1)
        elif key in ("enter", " "):
            good_key = rows[self.market_sel][0]
            if mode == "buy":
                ok, msg = state.market.buy(state.pilot, good_key, self.qty)
            else:
                ok, msg = state.market.sell(state.pilot, good_key, self.qty)
            self.toast_now(msg, 1.8)
            if ok:
                self.qty = 1
        elif key in ("esc", "q"):
            self.screen = "docked"

    def draw_buy(self):
        self.draw_market("buy")

    def draw_sell(self):
        self.draw_market("sell")

    def key_buy(self, key):
        self.key_market(key, "buy")

    def key_sell(self, key):
        self.key_market(key, "sell")

    # -- equipment --------------------------------------------------------
    def draw_equip(self):
        state = self.state
        self.header()
        self.put(2, 2, f"EQUIPMENT {self.g['dot']} {state.system.name.upper()}",
                 self.C("gold", True))
        self.put(2, 30, f"CR {V.money(state.pilot.credits)}", self.C("gold"))
        rows = st.equipment_rows(state.pilot, state.system.tech)
        self.put(3, 2, "ITEM", self.C("dim"))
        self.put(3, 30, "PRICE", self.C("dim"))
        self.equip_sel = max(0, min(self.equip_sel, max(0, len(rows) - 1)))
        visible = max(3, self.h - 10)
        top = max(0, self.equip_sel - visible + 1)
        for i, (key, name, price, desc) in enumerate(rows[top:top + visible]):
            idx = i + top
            y = 4 + i
            attr = self.C("gold", True) | curses.A_REVERSE if idx == self.equip_sel else self.C("white")
            self.put(y, 2, f" {V.cut(name, 26):<26}", attr)
            self.put(y, 30, f"{price:8.0f}", self.C("cyan") if idx != self.equip_sel else attr)
        if not rows:
            self.put(5, 3, "This station has nothing left to sell you.", self.C("faint"))
        if rows:
            _, name, price, desc = rows[self.equip_sel]
            self.put(self.h - 4, 2, V.cut(desc, self.w - 4), self.C("dim"))
        self.put(self.h - 2, 2, "Up/Down pick   ENTER buy   ESC back", self.C("dim"))

    def key_equip(self, key):
        rows = st.equipment_rows(self.state.pilot, self.state.system.tech)
        if not rows:
            if key in ("esc", "q"):
                self.screen = "docked"
            return
        if key in ("up", "w", "k"):
            self.equip_sel = max(0, self.equip_sel - 1)
        elif key in ("down", "s", "j"):
            self.equip_sel = min(len(rows) - 1, self.equip_sel + 1)
        elif key in ("enter", " "):
            ok, msg = st.buy(self.state.pilot, rows[self.equip_sel][0],
                             self.state.system.tech)
            self.toast_now(msg, 1.8)
        elif key in ("esc", "q"):
            self.screen = "docked"

    # -- status / inventory -----------------------------------------------
    def draw_status(self):
        state = self.state
        p = state.pilot
        self.header()
        self.put(2, 2, "PILOT STATUS", self.C("gold", True))
        rows = [("Commander", p.name), ("Rank", p.rank), ("Kills", str(p.kills)),
                ("Legal status", p.legal_name), ("Credits", f"{V.money(p.credits)} CR"),
                ("Fuel", f"{p.fuel:.1f} / {MAX_FUEL:.1f} LY"),
                ("Hull", f"{max(0, state.hull):.0f}%"),
                ("Cargo bay", f"{p.cargo_used()} / {p.cargo_cap} t"),
                ("Missiles", f"{p.missiles} / {MAX_MISSILES}"),
                ("Laser", p.laser.title()),
                ("Galaxy", f"{p.galaxy} / {galaxy.GALAXY_COUNT}"),
                ("Jumps", str(p.jumps)), ("Deaths", str(p.deaths))]
        y = 4
        for label, value in rows:
            self.put(y, 3, V.cut(label, 14), self.C("dim"))
            self.put(y, 19, V.cut(str(value), 30), self.C("white"))
            y += 1
        x = 40
        self.put(4, x, "EQUIPMENT", self.C("cyan", True))
        eq = sorted(p.equipment)
        for i, item in enumerate(eq[:12]):
            self.put(5 + i, x, f"{self.g['tick']} {item}", self.C("green"))
        if not eq:
            self.put(5, x, "nothing fitted", self.C("faint"))
        self.put(18, x, "BADGES", self.C("cyan", True))
        if p.badges:
            for i, badge in enumerate(p.badges[:4]):
                self.put(19 + i, x, f"{self.g['star']} {badge}", self.C("gold"))
        else:
            self.put(19, x, "none yet", self.C("faint"))
        self.put(self.h - 2, 2, "ESC back", self.C("dim"))

    def key_status(self, key):
        if key in ("esc", "q", "enter"):
            self.screen = "docked" if self.state.mode == "docked" else "flight"

    def draw_inventory(self):
        state = self.state
        self.header()
        self.put(2, 2, f"CARGO {self.g['dot']} {state.pilot.cargo_used()}/{state.pilot.cargo_cap} t",
                 self.C("gold", True))
        y = 4
        if not state.pilot.cargo:
            self.put(y, 3, "Hold is empty.", self.C("faint"))
        for key, qty in sorted(state.pilot.cargo.items()):
            good = GOOD_BY_KEY[key]
            self.put(y, 3, V.cut(good.name, 22), self.C("white"))
            self.put(y, 27, f"{qty:3d} t", self.C("cyan"))
            self.put(y, 34, f"{state.market.price(key) * qty:9.1f} CR", self.C("gold"))
            y += 1
        self.put(self.h - 2, 2, "ESC back", self.C("dim"))

    def key_inventory(self, key):
        if key in ("esc", "q", "enter"):
            self.screen = "docked" if self.state.mode == "docked" else "flight"

    # -- help / pause / death ---------------------------------------------
    def draw_help(self):
        self.header("CONTROLS", "ESC to go back")
        col1 = [
            ("FLIGHT", "", ""),
            ("S / X", "pitch up / down", "also UP / DOWN"),
            (", / .", "roll left / right", "also LEFT / RIGHT"),
            ("A / Z", "more / less speed", ""),
            ("SPACE", "fire laser", ""),
            ("T", "lock missile target", ""),
            ("M", "fire missile", ""),
            ("E", "ECM", "destroys missiles"),
            ("B", "energy bomb", "one shot"),
            ("L", "level the roll", "flight assist"),
            ("H / 1", "galactic chart", ""),
            ("2 / 3", "status / inventory", ""),
        ]
        col2 = [
            ("STATION", "", ""),
            ("ENTER", "select / trade", ""),
            ("UP/DOWN", "pick an item", ""),
            ("LEFT/RIGHT", "trade quantity", ""),
            ("ESC", "pause menu", ""),
            (">>", "", ""),
            ("HOW TO SURVIVE", "", ""),
            ("Slot", "fly into the slot", "the = bar"),
            ("Roll", "match the slot", "under 28 deg"),
            ("Speed", "under 320 m/s", ""),
            ("Docking", "computer: 1500 CR", "docks itself"),
            ("Trade", "cheap where made", "food: farms"),
        ]
        y = 3
        for key, label, note in col1:
            if key and not label:
                self.put(y, 3, key, self.C("gold", True))
            else:
                self.put(y, 3, V.cut(key, 10), self.C("cyan"))
                self.put(y, 14, V.cut(label, 24), self.C("white"))
                self.put(y, 39, V.cut(note, 12), self.C("dim"))
            y += 1
        y = 3
        for key, label, note in col2:
            if key and not label:
                self.put(y, 48, key, self.C("gold", True))
            else:
                self.put(y, 48, V.cut(key, 12), self.C("cyan"))
                self.put(y, 61, V.cut(label, 18), self.C("white"))
            y += 1
        self.put(self.h - 3, 3, "Dock to save, refuel and trade. Fuel is 7 LY per tank.",
                 self.C("dim"))
        self.put(self.h - 2, 3, "Hostile ships show red. Police are cyan. Traders are green.",
                 self.C("dim"))

    def key_help(self, key):
        if key in ("esc", "q", "enter", "?"):
            self.screen = self.help_from

    PAUSE_ITEMS = ("Resume", "Controls", "Quit to title", "Quit game")

    def draw_pause(self):
        if self.state is not None:
            self.header()
            self.draw_flight()
        else:
            self.draw_title()
        w, h = 32, 9
        y = max(2, (self.h - h) // 2)
        x = max(2, (self.w - w) // 2)
        self.box(y, x, h, w, "gold", "PAUSED")
        for i, item in enumerate(self.PAUSE_ITEMS):
            attr = self.C("gold", True) | curses.A_REVERSE if i == self.pause_sel else self.C("white")
            self.put(y + 2 + i, x + 4, f" {item:<22}", attr)

    def key_pause(self, key):
        if not hasattr(self, "pause_sel"):
            self.pause_sel = 0
        if key in ("up", "w", "k"):
            self.pause_sel = (self.pause_sel - 1) % len(self.PAUSE_ITEMS)
        elif key in ("down", "s", "j"):
            self.pause_sel = (self.pause_sel + 1) % len(self.PAUSE_ITEMS)
        elif key in ("enter", " "):
            item = self.PAUSE_ITEMS[self.pause_sel]
            if item == "Resume":
                self.screen = self.help_from
            elif item == "Controls":
                self.help_from = self.screen
                self.screen = "help"
            elif item == "Quit to title":
                self.screen = "title"
                self.state = None
            else:
                self.screen = "quit"
        elif key == "esc":
            self.screen = self.help_from

    def draw_dead(self):
        self.put(0, 1, "CORIOLIS", self.C("red", True))
        self.rule(1, "red")
        self.centre(max(3, self.h // 2 - 6), "G A M E   O V E R", self.C("red", True))
        p = self.state.pilot if self.state else None
        if p:
            self.centre(self.h // 2 - 3, f"{p.name} the {p.rank}", self.C("white"))
            self.centre(self.h // 2 - 2, f"{p.kills} kills  {self.g['dot']}  {V.money(p.credits)} CR",
                        self.C("dim"))
            self.centre(self.h // 2 - 1, f"{p.jumps} jumps  {self.g['dot']}  galaxy {p.galaxy}",
                        self.C("dim"))
        self.centre(self.h // 2 + 2, "The void keeps what it takes.", self.C("faint"))
        self.centre(self.h // 2 + 4, "ENTER for a new commander", self.C("gold"))

    def key_dead(self, key):
        if key in ("enter", " ", "q", "esc"):
            self.state = None
            self.has_save = False
            self.screen = "title"
            self.menu = 0


# --------------------------------------------------------------------- CLI --

def parse_args(argv=None):
    ap = argparse.ArgumentParser(
        prog="coriolis",
        description="An Elite-style space trading and combat game for the terminal.")
    ap.add_argument("--seed", type=int, default=None, help="seed for encounters")
    ap.add_argument("--galaxy", type=int, default=1, help="start in galaxy 1-10")
    ap.add_argument("--art", choices=("solid", "wire", "hybrid"), default="solid",
                    help="ship silhouettes, outlines, or outlines up close")
    ap.add_argument("--no-colour", action="store_true", help="monochrome")
    ap.add_argument("--classic", action="store_true", help="1984-style key map")
    ap.add_argument("--start-docked", action="store_true",
                    help="skip the launch and start at the station menu")
    ap.add_argument("--version", action="store_true")
    ap.add_argument("--dump-galaxy", type=int, default=None, metavar="N",
                    help="print the systems of galaxy N and exit")
    ap.add_argument("--selftest", action="store_true",
                    help="run a headless simulation and exit")
    return ap.parse_args(argv)


def dump_galaxy(number):
    systems = galaxy.galaxy(number)
    print(f"# galaxy {number} of {galaxy.GALAXY_COUNT}: {len(systems)} systems")
    print(f"{'idx':>3} {'name':<11} {'x':>7} {'y':>7} {'econ':<18} "
          f"{'gov':<16} {'tech':>4} {'pop':>5}")
    for s in systems:
        print(f"{s.index:3d} {s.name:<11} {s.x:7.1f} {s.y:7.1f} "
              f"{s.economy_name:<18} {s.government_name:<16} {s.tech:4d} "
              f"{s.population:5.1f}")


def selftest(opts):
    """Headless smoke run: physics, combat, docking and the market."""
    import random
    state = GameState(seed=opts.seed if opts.seed is not None else 1)
    state.launch()
    rng = random.Random(state.seed)
    combat.spawn(state)
    frames = 0
    for _ in range(1800):
        state.time += 1.0 / 60.0
        state.flight.step(rng.uniform(-1, 1), rng.uniform(-1, 1), 0, 1.0 / 60.0)
        if frames % 40 == 0:
            combat.fire_laser(state)
        combat.step(state, 1.0 / 60.0)
        frames += 1
        for value in (state.flight.pos.x, state.flight.pos.y, state.flight.pos.z,
                      state.hull, *state.banks):
            assert value == value, "NaN in simulation"
    state.flight.pos = Vec3(0.0, 0.0, -100.0)
    state.flight.orient = Mat3.identity()
    state.flight.speed = 120.0
    status, text = state.station.dock_check(state.flight)
    assert status == "dock", f"docking failed: {status} {text}"
    state.dock()
    ok, msg = state.market.buy(state.pilot, "food", 5)
    assert ok, msg
    ok, msg = state.market.sell(state.pilot, "food", 5)
    assert ok, msg
    state.say("selftest complete")
    print(f"selftest: {frames} ticks, hull {state.hull:.0f}, "
          f"credits {state.pilot.credits:.1f}, contacts {len(state.contacts)}")
    print("selftest: PASS")
    return 0


def main(argv=None):
    opts = parse_args(argv)
    if opts.version:
        print(f"coriolis {__version__}")
        return 0
    if opts.dump_galaxy is not None:
        dump_galaxy(opts.dump_galaxy)
        return 0
    if opts.selftest:
        return selftest(opts)
    try:
        curses.wrapper(lambda scr: Game(scr, opts).loop())
    except KeyboardInterrupt:
        pass
    return 0
