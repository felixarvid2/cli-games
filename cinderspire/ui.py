"""Terminal presentation for CINDERSPIRE (curses)."""

import curses
import math
import os
import traceback
import random
import sys
import time

from . import __version__
from .core import (ACT_NAMES, ACTS, CARDS, DATA_DIR, FLOORS, NODE_TYPES,
                   TOTAL_FLOORS,
                   RELICS, SAVE_PATH, RUN_PATH, Combat, Run, can_upgrade,
                   cdata, clear_run, ctext, load_best, load_run, run_from_dict,
                   run_to_dict, save_best, save_run, st)
from .data import ACHIEVEMENTS, BOSSES, CLASSES, ENEMIES, POTIONS, TIPS
from .board import BoardCombat, enemy_for
from .board_data import BOARD_CARDS, ENEMY_HEROES, STARTER_DECKS
from . import visuals as V

ANIM = max(0.0, float(os.environ.get("CINDERSPIRE_ANIM", "1")))
DEFAULT_SETTINGS = {"anim": ANIM, "confirm_end": True, "flash": True,
                    "shake": True}

# ------------------------------------------------------------------ glyphs --

def _utf8():
    try:
        return "utf" in (sys.stdout.encoding or "").lower()
    except Exception:
        return False


UTF = _utf8()
ROMAN = ["I", "II", "III", "IV"]
GL = dict(
    tl="┌", tr="┐", bl="└", br="┘", h="─", v="│",
    lt="├", rt="┤", full="█", empty="░", arrow="▶", down="▼",
    dot="●", ring="○", sep="·", ell="…", up="▲", dl="╔", dr="╗",
    ul="╚", ur="╝", dh="═", dv="║", cross="┼", tick="✓", skull="☠",
    rtl="╭", rtr="╮", rbl="╰", rbr="╯", dash="╌", star="★", flame="▲",
    coin="●", heart="♥", bolt="↯", halo="○", bullet="•", flask="⚗",
    shield="⛨", sword="⚔", wing="≈",
)
if not UTF:
    GL = dict(
        tl="+", tr="+", bl="+", br="+", h="-", v="|",
        lt="+", rt="+", full="#", empty="-", arrow=">", down="v",
        dot="*", ring="o", sep=".", ell=">", up="^", dl="+", dr="+",
        ul="+", ur="+", dh="=", dv="|", cross="+", tick="x", skull="X",
        rtl="+", rtr="+", rbl="+", rbr="+", dash="-", star="*", flame="^",
        coin="o", heart="+", bolt="!", halo="o", bullet="*", flask="!",
        shield="T", sword="x", wing="~",
    )

BOX_MASK = {0: " ", 1: " ", 2: " ", 3: "│", 4: " ", 5: "┘", 6: "┐",
            7: "┤", 8: " ", 9: "└", 10: "┌", 11: "├", 12: "─",
            13: "┴", 14: "┬", 15: "┼"}

if not UTF:
    BOX_MASK = {0: " ", 1: " ", 2: " ", 3: "|", 4: " ", 5: "+", 6: "+",
                7: "+", 8: " ", 9: "+", 10: "+", 11: "+", 12: "-",
                13: "+", 14: "+", 15: "+"}

UP, DOWN, LEFT, RIGHT = 1, 2, 4, 8

BANNER_FONT = {
    "C": ["█████", "█    ", "█    ", "█    ", "█████"],
    "I": ["█████", "  █  ", "  █  ", "  █  ", "█████"],
    "N": ["█   █", "██  █", "█ █ █", "█  ██", "█   █"],
    "D": ["████ ", "█   █", "█   █", "█   █", "████ "],
    "E": ["█████", "█    ", "████ ", "█    ", "█████"],
    "R": ["████ ", "█   █", "████ ", "█  █ ", "█   █"],
    "S": ["█████", "█    ", "█████", "    █", "█████"],
    "P": ["████ ", "█   █", "████ ", "█    ", "█    "],
    "V": ["█   █", "█   █", "█   █", " █ █ ", "  █  "],
    "O": ["█████", "█   █", "█   █", "█   █", "█████"],
    "Y": ["█   █", " █ █ ", "  █  ", "  █  ", "  █  "],
    "U": ["█   █", "█   █", "█   █", "█   █", "█████"],
    "T": ["█████", "  █  ", "  █  ", "  █  ", "  █  "],
    "A": ["█████", "█   █", "█████", "█   █", "█   █"],
    "H": ["█   █", "█   █", "█████", "█   █", "█   █"],
    "L": ["█    ", "█    ", "█    ", "█    ", "█████"],
    "F": ["█████", "█    ", "████ ", "█    ", "█    "],
    "W": ["█   █", "█   █", "█ █ █", "██ ██", "█   █"],
    " ": ["     ", "     ", "     ", "     ", "     "],
}


def banner(text):
    rows = ["", "", "", "", ""]
    for ch in text:
        pat = BANNER_FONT.get(ch, BANNER_FONT[" "])
        for i in range(5):
            rows[i] += pat[i] + " "
    out = [r.rstrip() for r in rows]
    if not UTF:
        out = [r.replace("█", "#") for r in out]
    return out


# ------------------------------------------------------------------ colors --

PAIRS = {}
_ACACHE = {}

PALETTE = {
    "text": 252, "dim": 243, "faint": 238, "white": 255,
    "red": 203, "orange": 209, "gold": 221, "green": 114,
    "teal": 79, "blue": 111, "purple": 141, "pink": 211,
    "cyan": 116, "ember": 166,
    "steel": 109, "rust": 173, "bone": 230, "crimson": 160,
    "lime": 154, "violet": 135, "ice": 159, "sand": 222,
    "blood": 124, "moss": 107, "brass": 179, "coal": 236,
    "parchment": 223, "arcane": 99, "poison": 106, "holy": 229,
}
BASIC = {
    "text": curses.COLOR_WHITE, "dim": curses.COLOR_WHITE,
    "faint": curses.COLOR_BLACK, "white": curses.COLOR_WHITE,
    "red": curses.COLOR_RED, "orange": curses.COLOR_YELLOW,
    "gold": curses.COLOR_YELLOW, "green": curses.COLOR_GREEN,
    "teal": curses.COLOR_CYAN, "blue": curses.COLOR_BLUE,
    "purple": curses.COLOR_MAGENTA, "pink": curses.COLOR_MAGENTA,
    "cyan": curses.COLOR_CYAN, "ember": curses.COLOR_RED,
    "steel": curses.COLOR_BLUE, "rust": curses.COLOR_YELLOW,
    "bone": curses.COLOR_WHITE, "crimson": curses.COLOR_RED,
    "lime": curses.COLOR_GREEN, "violet": curses.COLOR_MAGENTA,
    "ice": curses.COLOR_CYAN, "sand": curses.COLOR_YELLOW,
    "blood": curses.COLOR_RED, "moss": curses.COLOR_GREEN,
    "brass": curses.COLOR_YELLOW, "coal": curses.COLOR_BLACK,
    "parchment": curses.COLOR_WHITE, "arcane": curses.COLOR_MAGENTA,
    "poison": curses.COLOR_GREEN, "holy": curses.COLOR_WHITE,
}


def init_colors():
    curses.start_color()
    try:
        curses.use_default_colors()
        bg = -1
    except curses.error:
        bg = curses.COLOR_BLACK
    rich = curses.COLORS >= 256
    for i, name in enumerate(PALETTE, start=1):
        fg = PALETTE[name] if rich else BASIC[name]
        try:
            curses.init_pair(i, fg, bg)
        except curses.error:
            curses.init_pair(i, BASIC[name], bg)
        PAIRS[name] = i


def C(name, bold=False, rev=False, dim=False):
    key = (name, bold, rev, dim)
    a = _ACACHE.get(key)
    if a is None:
        a = curses.color_pair(PAIRS.get(name, 0))
        if bold:
            a |= curses.A_BOLD
        if rev:
            a |= curses.A_REVERSE
        if dim:
            a |= curses.A_DIM
        _ACACHE[key] = a
    return a


# ----------------------------------------------------------------- helpers --

def cut(s, n):
    if n <= 0:
        return ""
    s = s.replace("\n", " ")
    if len(s) <= n:
        return s
    return s[:n - 1] + GL["ell"]


def wrap(text, width):
    out = []
    for para in text.split("\n"):
        if not para.strip():
            out.append("")
            continue
        line = ""
        for word in para.split():
            if not line:
                line = word
            elif len(line) + 1 + len(word) <= width:
                line += " " + word
            else:
                out.append(line)
                line = word
        out.append(line)
    return out


def is_enter(ch):
    return ch in (10, 13, curses.KEY_ENTER)


LEFT_KEYS = (curses.KEY_LEFT,)
RIGHT_KEYS = (curses.KEY_RIGHT,)
UP_KEYS = (curses.KEY_UP,)
DOWN_KEYS = (curses.KEY_DOWN,)


# ------------------------------------------------------------------- canvas --

class Game:
    def __init__(self, scr):
        self.scr = scr
        try:
            curses.curs_set(0)
        except curses.error:
            pass
        scr.keypad(True)
        try:
            curses.mousemask(curses.ALL_MOUSE_EVENTS
                             | curses.REPORT_MOUSE_POSITION)
            curses.mouseinterval(0)
            self.mouse_ok = True
        except curses.error:
            self.mouse_ok = False
        self.hot = []
        self.last_hand_click = {}
        self.drag = None
        self._pos = {}
        self.confetti = []
        self.transition_until = 0.0
        self.transition_label = ""
        self.h, self.w = scr.getmaxyx()
        self.state = "title"
        self.t = 0.0
        self.last = time.monotonic()
        self.run = None
        self.cb = None
        self.sel = 0
        self.tgt = 0
        self.map_sel = 0
        self.path = []
        self.win_at = None
        self.lose_at = None
        self.anim_next = 0.0
        self.toast = None
        self.toast_queue = []
        self.overlay = None
        self.detail = None
        self.picker = None
        self.menu = 0
        self.help_from = "title"
        self.best = load_best()
        self.settings = dict(DEFAULT_SETTINGS)
        self.settings.update(self.best.get("settings", {}) or {})
        self.anim = float(self.settings.get("anim", 1.0))
        self.saved = load_run() is not None
        self.seed_buf = ""
        self.deck_sort = True
        self.history_sel = 0
        self.settings_sel = 0
        self.act_banner_until = 0.0
        self.act_banner_text = ""
        self.pause_state = "map"
        self.settings_from_pause = False
        self.codex_tab = 0
        self.codex_sel = 0
        self.codex_scroll = 0
        self.daily = False
        self.heart_sel = 0
        self.class_sel = 0
        self.pending = {}
        self.ash = []
        self.gold_disp = 0.0
        self.energy_disp = 0.0
        self.last_turn = 0
        self.turn_banner_until = 0.0
        self.gold_seen = 0
        self.gold_flash_until = 0.0
        self.confirm_end_until = 0.0
        self.card_tip_until = 0.0
        self.tip_pinned = True
        self.row = 0
        self.bsel = 0
        self.esel = 0
        self.event = None
        self.event_stage = 0
        self.event_msg = ""
        self.event_choice = None
        self.reward = None
        self.reward_sel = 0
        self.rest_sel = 0
        self.rest_msg = None
        self.shop_sel = 0
        self.shop_msg = ""
        self.pot_sel = 0
        self.boons = []
        self.boon_sel = 0
        self.interlude_heal = 0
        self.new_best = False
        self.confirm_sel = 0
        self.disp_hp = {}
        self.final = None
        self.treasure_lines = []
        self.treasure_desc = ""
        self.frame = 0
        self.rng = random.Random()
        self.embers = [[self.rng.uniform(0, 80), self.rng.uniform(0, 24),
                        self.rng.choice(["*", "·", ".", "˙"]),
                        self.rng.uniform(0.6, 2.4)] for _ in range(30)]

    # -- drawing primitives ------------------------------------------------
    def put(self, y, x, s, attr=0, maxw=None):
        if y < 0 or y >= self.h or x >= self.w or not s:
            return
        if x < 0:
            s = s[-x:]
            x = 0
        if maxw is not None:
            s = s[:maxw]
        s = s[:max(0, self.w - x)]
        if not s:
            return
        try:
            self.scr.addstr(y, x, s, attr)
        except curses.error:
            pass

    def center(self, y, s, attr=0):
        self.put(y, max(0, (self.w - len(s)) // 2), s, attr)

    def accent(self):
        if self.run is not None:
            return V.accent_for(self.run.cls)
        return "gold"

    def accent_alt(self):
        if self.run is not None:
            return V.accent_alt_for(self.run.cls)
        return "orange"

    def put_grad(self, y, x, text, colors, bold=False, dim=False):
        """Draw text one character at a time with a cycling colour ramp."""
        if not text:
            return
        for i, ch in enumerate(text):
            if x + i >= self.w:
                break
            col = colors[min(len(colors) - 1, i * len(colors) // max(1, len(text)))]
            self.put(y, x + i, ch, C(col, bold=bold, dim=dim))

    def chip(self, y, x, text, color="gold", bold=True, rev=True, dim=False):
        label = f" {text} "
        self.put(y, x, label, C(color, bold=bold, rev=rev, dim=dim))
        return len(label)

    def keycap(self, y, x, key, label, color="gold"):
        w = self.chip(y, x, key, color, bold=True)
        self.put(y, x + w, " " + label, C("text"))
        return w + 1 + len(label)

    def shadow_box(self, y, x, h, w):
        """A faint stipple shadow under and right of a panel."""
        if y + h < self.h:
            self.put(y + h, x + 2, GL["empty"] * max(0, w - 2),
                     C("coal", dim=True))
        if x + w < self.w:
            for i in range(1, h):
                self.put(y + i, x + w, GL["empty"], C("coal", dim=True))

    def panel(self, y, x, h, w, title=None, accent=None, double=False,
              shadow=True, rounded=True):
        accent = accent or self.accent()
        if shadow:
            self.shadow_box(y, x, h, w)
        self.box(y, x, h, w, C(accent, bold=True), double=double,
                 title=title, tattr=C(accent, bold=True), rounded=rounded)

    def rule(self, y, attr=None, ch=None):
        if ch is not None or attr is not None:
            ch = ch or GL["h"]
            self.put(y, 0, ch * self.w, attr if attr is not None else C("faint"))
            return
        accent = self.accent()
        mid = self.w // 2
        left = accent if self.w >= 60 else "faint"
        self.put(y, 0, GL["h"] * (mid - 3), C(left, dim=True))
        self.put(y, mid - 3, " " + GL["star"] + " ", C(accent, bold=True))
        self.put(y, mid + 1, GL["h"] * (self.w - mid - 1), C("faint"))

    def bar(self, y, x, width, cur, mx, color=None):
        frac = 0 if mx <= 0 else max(0.0, min(1.0, cur / mx))
        color = color or V.heal_color(frac)
        filled = int(round(width * frac))
        self.put(y, x, GL["full"] * filled, C(color, bold=True))
        self.put(y, x + filled, GL["empty"] * (width - filled), C("faint"))
        # quarter ticks make the bar readable at a glance
        for q in (0.25, 0.5, 0.75):
            tx = x + int(width * q)
            self.put(y, tx, GL["v"], C("coal", bold=True))

    def gem(self, y, x, value, color="gold", bold=True):
        text = f"({value})"
        self.put(y, x, text, C(color, bold=bold))
        return len(text)

    def kw_icons(self, keywords, color="cyan", dim=False):
        glyphs = V.kw_glyphs(keywords, UTF)
        return glyphs, C(color, bold=True, dim=dim)

    def box(self, y, x, h, w, attr, double=False, title=None, tattr=None,
            rounded=False):
        if h < 2 or w < 2:
            return
        if double:
            tl, tr, bl, br = (GL["dl"], GL["dr"], GL["ul"], GL["ur"])
        elif rounded:
            tl, tr, bl, br = (GL["rtl"], GL["rtr"], GL["rbl"], GL["rbr"])
        else:
            tl, tr, bl, br = (GL["tl"], GL["tr"], GL["bl"], GL["br"])
        hh, vv = (GL["dh"], GL["dv"]) if double else (GL["h"], GL["v"])
        self.put(y, x, tl + hh * (w - 2) + tr, attr)
        for i in range(1, h - 1):
            self.put(y + i, x, vv, attr)
            self.put(y + i, x + w - 1, vv, attr)
        self.put(y + h - 1, x, bl + hh * (w - 2) + br, attr)
        if title:
            t = cut(f" {title} ", w - 4)
            self.put(y, x + 3, t, tattr if tattr is not None else attr)

    def clear_inside(self, y, x, h, w):
        for i in range(1, h - 1):
            self.put(y + i, x + 1, " " * (w - 2))

    # -- main loop ---------------------------------------------------------
    def loop(self):
        self.scr.timeout(16)
        while self.state != "quit":
            now = time.monotonic()
            dt = min(0.12, now - self.last)
            self.last = now
            self.t += dt
            self.frame += 1
            self.h, self.w = self.scr.getmaxyx()
            self.animate(dt, now)
            self.scr.erase()
            if self.h < 24 or self.w < 78:
                self.draw_resize()
            else:
                self.draw()
            self.scr.noutrefresh()
            curses.doupdate()
            ch = self.scr.getch()
            if ch != -1:
                self.handle(ch)

    def animate(self, dt, now):
        if self.run is not None:
            if not self.gold_disp:
                self.gold_disp = float(self.run.gold)
            if abs(self.gold_disp - self.run.gold) > 0.5:
                step = max(20.0, abs(self.gold_disp - self.run.gold) * 6) * dt
                self.gold_disp += min(step, self.run.gold - self.gold_disp) \
                    if self.gold_disp < self.run.gold else \
                    -min(step, self.gold_disp - self.run.gold)
            else:
                self.gold_disp = float(self.run.gold)
        if self.cb and self.state == "combat":
            target = float(self.cb.energy)
            if abs(self.energy_disp - target) > 0.05:
                step = max(2.0, abs(self.energy_disp - target) * 8) * dt
                self.energy_disp += (min(step, target - self.energy_disp)
                                     if self.energy_disp < target else
                                     -min(step, self.energy_disp - target))
            else:
                self.energy_disp = target
            if self.cb.turn != self.last_turn:
                self.last_turn = self.cb.turn
                self.turn_banner_until = now + 1.0
        if self.state in ("combat", "victory"):
            if not self.ash:
                self.ash = [[self.rng.uniform(1, self.w - 2),
                             self.rng.uniform(3, self.h - 10),
                             self.rng.uniform(0.015, 0.06),
                             self.rng.choice(["\u00b7", ".", "*"])]
                            for _ in range(14)]
            for a in self.ash:
                a[1] += dt * (0.6 + a[2] * 20)
                a[0] += math.sin(self.t * 0.6 + a[1]) * dt * 2
                if a[1] > self.h - 12:
                    a[1] = 4
                    a[0] = self.rng.uniform(20, self.w - 3)
        if self.state in ("victory", "gameover", "title") and self.confetti:
            for c in self.confetti:
                c[1] += c[3] * dt
                c[0] += math.sin(self.t * 2 + c[2]) * dt * 2
                if c[1] > self.h + 1:
                    c[1] = -1
                    c[0] = self.rng.uniform(1, self.w - 2)
        if self.state == "title":
            for e in self.embers:
                e[1] -= dt * e[3]
                e[0] += math.sin(self.t * 0.7 + e[1]) * dt * 3
                if e[1] < 1:
                    e[1] = self.h - 1
                    e[0] = self.rng.uniform(0, self.w)
        if self.cb:
            for k in list(self.cb.popups):
                self.cb.popups[k][2] -= dt
                if self.cb.popups[k][2] <= 0:
                    del self.cb.popups[k]
            for k in list(self.cb.shake):
                self.cb.shake[k] -= dt
                if self.cb.shake[k] <= 0:
                    del self.cb.shake[k]
            for k in list(self.cb.flash):
                self.cb.flash[k] -= dt
                if self.cb.flash[k] <= 0:
                    del self.cb.flash[k]
            if (self.state == "combat" and self.cb.phase == "enemy"
                    and now >= self.anim_next and not self.overlay):
                self.cb.step_enemy()
                self.anim_next = now + 0.40 * self.anim
            if self.state == "combat":
                if self.cb.phase == "won" and self.win_at is None:
                    self.win_at = now + 0.65 * self.anim
                if self.cb.phase == "lost" and self.lose_at is None:
                    self.lose_at = now + 1.1 * self.anim
                if self.win_at is not None and now >= self.win_at:
                    self.combat_won()
                elif self.lose_at is not None and now >= self.lose_at:
                    self.game_over()

    # -- screen dispatch ---------------------------------------------------
    def draw(self):
        self.hot = []
        d = getattr(self, "draw_" + self.state, None)
        if d:
            d()
        if self.overlay:
            self.draw_overlay()
        if self.toast:
            txt, until = self.toast
            if time.monotonic() < until:
                t = cut("* " + txt + " *", self.w - 4)
                self.put(2, max(1, (self.w - len(t)) // 2), t,
                         C("gold", bold=True))
            else:
                if self.toast_queue:
                    msg, dur = self.toast_queue.pop(0)
                    self.toast = (msg, time.monotonic() + dur)
                else:
                    self.toast = None

    def hot_add(self, x, y, w, h, action):
        self.hot.append((x, y, w, h, action))

    def zone_at(self, mx, my):
        for hx, hy, hw, hh, action in reversed(self.hot):
            if hx <= mx < hx + hw and hy <= my < hy + hh:
                return action
        return None

    def zone_label(self, zone):
        cb = self.cb
        if not zone or cb is None:
            return ""
        if zone[0] == "hero":
            return f"ENEMY HERO {cb.enemy.hp}/{cb.enemy.max_hp}"
        if zone[0] == "enemy" and 0 <= zone[1] < len(cb.eboard):
            m = cb.eboard[zone[1]]
            kws = [k.upper() for k in ("taunt", "divine_shield", "poisonous",
                                       "windfury", "rush") if k in m.kw]
            return f"{m.name} {m.atk}/{m.hp}" + (
                " " + " ".join(kws) if kws else "")
        if zone[0] == "board" and 0 <= zone[1] < len(cb.pboard):
            m = cb.pboard[zone[1]]
            return f"{m.name} {m.atk}/{m.hp}"
        if zone[0] == "hand" and 0 <= zone[1] < len(cb.hand):
            return BOARD_CARDS[cb.hand[zone[1]]["id"]]["name"]
        return ""

    def on_mouse(self):
        try:
            _, mx, my, _, bstate = curses.getmouse()
        except curses.error:
            return
        moved = bool(bstate & curses.REPORT_MOUSE_POSITION)

        if bstate & curses.BUTTON1_PRESSED:
            self.drag = dict(zone=self.zone_at(mx, my), x=mx, y=my,
                             moved=False, hover=self.zone_at(mx, my))
            self._drag_xy = (my, mx)
            return

        if moved:
            if self.drag is not None:
                if (abs(mx - self.drag["x"]) > 1
                        or abs(my - self.drag["y"]) > 1):
                    self.drag["moved"] = True
                self.drag["hover"] = self.zone_at(mx, my)
                self.drag["x"], self.drag["y"] = mx, my
                self._drag_xy = (my, mx)
            return

        if bstate & (curses.BUTTON1_RELEASED | curses.BUTTON1_CLICKED
                     | curses.BUTTON1_DOUBLE_CLICKED):
            drag = self.drag
            self.drag = None
            zone = self.zone_at(mx, my)
            if drag is None:
                if zone:
                    self.activate(zone)
                return
            src = drag["zone"]
            if src and zone and zone != src:
                self.drop(src, zone)
            elif zone:
                self.activate(zone)

    def drop(self, src, dst):
        """Drag a hand card or one of your minions onto an enemy."""
        cb = self.cb
        if cb is None or self.state != "combat" or cb.phase != "player":
            return
        if src[0] == "hand" and 0 <= src[1] < len(cb.hand):
            i = src[1]
            d = BOARD_CARDS[cb.hand[i]["id"]]
            self.row = 0
            self.sel = i
            if dst[0] in ("enemy", "hero"):
                self.esel = 0 if dst[0] == "hero" else dst[1] + 1
                if d["kind"] == "spell" and any(
                        op[0] in ("dmg_target", "destroy_target")
                        for op in d["effects"]):
                    self.play(i)
                elif d["kind"] == "spell":
                    self.play(i)
                else:
                    self.play(i)
            elif dst[0] == "board":
                self.play(i)
        elif src[0] == "board" and 0 <= src[1] < len(cb.player_alive()):
            if dst[0] in ("enemy", "hero"):
                self.row = 1
                self.bsel = src[1]
                self.esel = 0 if dst[0] == "hero" else dst[1] + 1
                self.attack_action()

    def activate(self, act):
        kind = act[0]
        cb = self.cb
        if kind == "menu":
            self.menu = act[1]
            self.handle(10)
        elif kind == "hand" and cb:
            i = act[1]
            now = time.monotonic()
            double = (self.row == 0 and self.sel == i
                      and now - self.last_hand_click.get(i, 0) < 0.7)
            self.last_hand_click[i] = now
            if double:
                self.play(i)
            else:
                self.row = 0
                self.sel = i
                self.card_tip_until = now + 3.0
        elif kind == "board" and cb:
            i = act[1]
            if self.row == 1 and self.bsel == i:
                self.attack_action()
            else:
                self.row = 1
                self.bsel = i
        elif kind in ("enemy", "hero") and cb:
            self.esel = 0 if kind == "hero" else act[1] + 1
            if self.row == 1:
                self.attack_action()
            elif self.row == 0 and cb.hand:
                d = BOARD_CARDS[cb.hand[min(self.sel, len(cb.hand) - 1)]["id"]]
                if d["kind"] == "spell" and any(
                        op[0] in ("dmg_target", "destroy_target")
                        for op in d["effects"]):
                    self.play(self.sel)
                else:
                    self.row = 2
            else:
                self.row = 2
        elif kind == "end" and cb and cb.phase == "player":
            cb.end_turn()
            self.turn_banner_until = time.monotonic() + 0.85
            self.anim_next = time.monotonic() + 0.30 * self.anim
            self.row = 0
            self.sel = 0
        elif kind == "map":
            r = self.run
            lane = act[2]
            if act[1] == r.floor and lane in r.avail:
                self.map_sel = r.avail.index(lane)
                self.handle(10)
            elif r.floor >= FLOORS and lane == "boss":
                self.handle(10)
        elif kind == "reward":
            self.reward_sel = act[1]
            self.handle(10)
        elif kind == "skip":
            self.handle(ord("s"))
        elif kind == "rest":
            self.rest_sel = act[1]
            self.handle(10)
        elif kind == "shop":
            self.shop_sel = act[1]
            self.handle(10)
        elif kind == "event":
            if self.event_stage < len(self.event["choices"]):
                self.event_stage = act[1]
                self.handle(10)
            else:
                self.handle(10)
        elif kind == "pause":
            self.menu = act[1]
            self.key_overlay(10)
        elif kind == "confirm":
            self.confirm_sel = act[1]
            self.key_overlay(10)
        elif kind == "close":
            self.overlay = None
        elif kind == "endscreen":
            self.handle(10)
        elif kind == "interlude":
            self.boon_sel = act[1]
            self.handle(10)
        elif kind == "heart":
            self.heart_sel = act[1]
            self.handle(10)
        elif kind == "pick":
            if self.overlay == "picker" and 0 <= act[1] < len(self.run.deck):
                idx = act[1]
                if self.picker["valid"](idx):
                    self.picker["sel"] = idx
                    fn = self.picker["on_pick"]
                    self.overlay = None
                    fn(idx)
        elif kind == "potion":
            self.pot_sel = act[1]
            self.key_overlay(10)
        elif kind == "buy":
            self.handle(10)

    def draw_resize(self):
        for i in range(5):
            self.put_grad(self.h // 2 - 4, max(2, self.w // 2 - 17),
                          "CINDERSPIRE NEEDS MORE ROOM"[:max(0, self.w - 8)],
                          ["ember", "orange", "gold"], bold=True)
        art = ["┌───────────────┐", "│  ██  ██  ██   │",
               "│   resize me   │", "└───────────────┘"]
        y = self.h // 2 - 2
        for i, line in enumerate(art):
            self.center(y + i, line, C("gold", bold=True))
        need = f"needs at least 78 x 24  (now {self.w} x {self.h})"
        self.center(y + 5, need, C("dim"))
        self.hint("drag the terminal corner or maximize the window")

    # ------------------------------------------------------------- header --
    def draw_header(self, subtitle=None, boss_label=True):
        r = self.run
        accent = self.accent()
        self.put(0, 2, GL["flame"], C("ember", bold=True))
        self.put_grad(0, 4, "CINDER", ["ember", "red", "orange"], bold=True)
        self.put_grad(0, 10, "SPIRE", ["gold", "brass", "sand"], bold=True)
        if subtitle:
            self.put(0, 17, GL["sep"], C("faint"))
            self.chip(0, 19, subtitle.upper(), accent, bold=True, rev=True)
        if r:
            clock = time.monotonic()
            if r.floor >= r.floors and boss_label:
                s = ENEMIES[BOSSES[r.act][0]]["name"].upper()
                self.put(0, max(23, self.w - 3 - len(s)), s,
                         C("red", bold=True))
                self.put(0, max(21, self.w - 5 - len(s)), GL["skull"],
                         C("red", bold=True))
            else:
                s = (f"ACT {ROMAN[r.act]}  {GL['sep']}  "
                     f"FLOOR {min(r.floor + 1, r.floors)}/{r.floors}")
                if r.daily:
                    s += "  DAILY"
                if r.ascension:
                    s = f"A{r.ascension}  " + s
                filled = min(r.floors, r.floor + 1)
                pips = "".join(GL["dot"] if i < filled else GL["ring"]
                               for i in range(r.floors))
                px = max(23, self.w - 3 - len(s) - len(pips) - 1)
                self.put(0, px, pips, C(accent, dim=True))
                self.put(0, max(23, self.w - 2 - len(s)), s, C("dim"))
            # HP rail
            self.put(1, 2, GL["heart"], C("red", bold=True))
            self.put(1, 4, "HP", C("red", bold=True))
            frac = 0 if r.max_hp <= 0 else r.hp / r.max_hp
            self.bar(1, 7, 18, r.hp, r.max_hp)
            self.put(1, 26, f"{r.hp}/{r.max_hp}",
                     C("white" if frac > 0.3 else "red", bold=True))
            # gold
            if r.gold != self.gold_seen:
                self.gold_seen = r.gold
                self.gold_flash_until = clock + 0.7
            flash = clock < self.gold_flash_until
            spin = int(self.t * 6) % 3
            self.put(1, 35, GL["coin"] if not flash else GL["star"],
                     C("brass" if spin else "gold", bold=True))
            shown = int(round(self.gold_disp)) if self.gold_disp else r.gold
            self.put(1, 38, str(shown),
                     C("white", bold=True) if flash else C("gold", bold=True))
            # deck
            self.put(1, 45, GL["bullet"], C("faint"))
            self.put(1, 47, "DECK", C("dim"))
            self.put(1, 52, str(len(r.deck)), C("text", bold=True))
            # relic tags as small chips
            tags = [RELICS[x]["tag"] for x in r.relics]
            if tags:
                tx = max(56, self.w - 2 - (len(tags) * 4 - 1))
                for i, tag in enumerate(tags[:6]):
                    self.put(1, tx + i * 4, f"[{tag}]",
                             C("gold", dim=True))
                if len(tags) > 6:
                    self.put(1, tx + 6 * 4, f"+{len(tags) - 6}",
                             C("faint"))

    def hint(self, text):
        self.put(self.h - 1, 0, " " * self.w, C("coal", rev=True))
        self.put(self.h - 1, 2, GL["arrow"], C(self.accent(), bold=True))
        self.put(self.h - 1, 4, cut(text, self.w - 6), C("text"))

    def layout(self):
        cards_y = self.h - 9
        header_y = cards_y - 1
        rule_y = header_y - 1
        log2 = rule_y - 1
        log1 = log2 - 1
        arena_bottom = log1 - 1
        return cards_y, header_y, rule_y, log1, log2, arena_bottom

    # -------------------------------------------------------------- title --
    def draw_title(self):
        # drifting embers and a soft corner vignette
        for e in self.embers:
            x, y = int(e[0]), int(e[1])
            if 0 <= y < self.h:
                col = "ember" if int(e[1]) % 3 else "orange"
                self.put(y, x, e[2], C(col, dim=True))
        for cx, cy, g in ((1, 2, GL["rtl"]), (self.w - 2, 2, GL["rtr"]),
                          (1, self.h - 2, GL["rbl"]),
                          (self.w - 2, self.h - 2, GL["rbr"])):
            self.put(cy, cx, g, C("ember", dim=True))
        art = banner("CINDERSPIRE")
        y0 = max(2, self.h // 2 - 9)
        ramp = ["ember", "red", "orange", "gold", "brass", "sand"]
        for i, line in enumerate(art):
            x = max(0, (self.w - len(line)) // 2)
            self.put_grad(y0 + i, x, line,
                          ramp[i:] + ramp[:i], bold=True)
            self.put(y0 + i, max(0, x - 3), GL["flame"],
                     C("ember" if i % 2 else "orange", bold=True))
            self.put(y0 + i, x + len(line) + 1, GL["flame"],
                     C("orange" if i % 2 else "ember", bold=True))
        sub = "A   D E C K B U I L D I N G   R O G U E L I K E"
        self.center(y0 + 6, sub, C("dim"))
        # class emblems
        labels = [f"({V.CLASS_EMBLEM[cid]})" for cid in self.CLASS_ORDER]
        total = sum(len(x) for x in labels) + 3 * (len(labels) - 1)
        ex = max(2, (self.w - total) // 2)
        for i, cid in enumerate(self.CLASS_ORDER):
            col = V.accent_for(cid)
            self.put(y0 + 7, ex, labels[i], C(col, bold=True))
            ex += len(labels[i]) + 3
        items = self.title_items()
        self.menu_items = items
        for i, it in enumerate(items):
            y = y0 + 9 + i
            sel = i == self.menu
            if sel:
                label = f"{GL['arrow']}  {it}  {GL['arrow']}"
                self.center(y, " " * (len(label) + 2),
                            C(self.accent(), rev=True))
                self.center(y, label, C("white", bold=True))
            else:
                self.center(y, it, C("dim"))
            lx = max(0, (self.w - len(it)) // 2)
            self.hot_add(lx, y, len(it), 1, ("menu", i))
        # stats plaque
        if self.best.get("best") and y0 + 9 + len(items) < self.h - 7:
            line = (f"BEST {self.best['best']}   WINS {self.best.get('wins', 0)}"
                    f"   RUNS {self.best.get('runs', 0)}")
            wdt = min(58, self.w - 8)
            py = self.h - 6
            px = (self.w - wdt) // 2
            self.box(py, px, 3, wdt, C("ember", dim=True), rounded=True)
            self.center(py + 1, line, C("gold"))
        tips = list(TIPS.values())
        tip = tips[int(self.t / 6) % len(tips)] if tips else ""
        if tip:
            self.center(self.h - 3, cut(tip, self.w - 8), C("faint"))
        self.put(self.h - 1, self.w - 2 - len(__version__) - 1,
                 "v" + __version__, C("faint"))

    def today(self):
        return time.strftime("%Y-%m-%d")

    def title_items(self):
        items = ["BEGIN THE ASCENT"]
        if self.best.get("wins", 0) > 0:
            items.append(f"ASCEND  \u00b7  A{self.best.get('asc', 1)}")
        done = self.best.get("daily", {}).get("date") == self.today()
        items.append(f"DAILY RUN  \u00b7  {time.strftime('%d %b').upper()}"
                     + ("  \u2713" if done else ""))
        items.append("CODEX")
        items.append("HOW TO PLAY")
        if self.saved:
            items.insert(0, "CONTINUE")
        items.append("SETTINGS")
        if self.best.get("history"):
            items.append("RUN HISTORY")
        items.append("QUIT")
        return items

    def draw_settings(self):
        self.draw_header("settings", boss_label=False)
        wdt = min(66, self.w - 8)
        hgt = 17
        y, x = self.overlay_box(hgt, wdt, "SETTINGS")
        anim = ("fast" if self.anim < 0.6 else
                "slow" if self.anim > 1.4 else "normal")
        rows = [("Animation speed", anim, GL["bolt"]),
                ("Confirm end turn",
                 "on" if self.settings.get("confirm_end") else "off",
                 GL["tick"]),
                ("Flash effects",
                 "on" if self.settings.get("flash") else "off", GL["star"]),
                ("Screen shake",
                 "on" if self.settings.get("shake", True) else "off",
                 GL["flame"]),
                ("Hints", "on" if self.settings.get("hints", True) else "off",
                 GL["bullet"])]
        for i, (label, val, icon) in enumerate(rows):
            sel = i == self.settings_sel
            yy = y + 2 + i * 2
            if sel:
                self.put(yy, x + 2, " " * (wdt - 4), C("coal", rev=True))
            self.put(yy, x + 3, icon, C(self.accent() if sel else "faint",
                                        bold=sel))
            self.put(yy, x + 5, label,
                     C("white", bold=True) if sel else C("text"))
            on = val in ("on", "normal", "fast", "slow")
            self.chip(yy, x + wdt - 11, f"< {val} >",
                      "green" if on else "red", rev=sel, bold=True)
        self.put(y + hgt - 2, x + 3,
                 "up/down choose   left/right change   esc back", C("faint"))

    def key_settings(self, ch):
        if ch in UP_KEYS:
            self.settings_sel = (self.settings_sel - 1) % 5
        elif ch in DOWN_KEYS:
            self.settings_sel = (self.settings_sel + 1) % 5
        elif ch in LEFT_KEYS or ch in RIGHT_KEYS or is_enter(ch):
            step = -1 if ch in LEFT_KEYS else 1
            if self.settings_sel == 0:
                opts = [0.35, 1.0, 1.8]
                cur = min(range(3), key=lambda i: abs(opts[i] - self.anim))
                self.anim = opts[(cur + step) % 3]
                self.settings["anim"] = self.anim
            elif self.settings_sel == 1:
                self.settings["confirm_end"] = not self.settings.get(
                    "confirm_end", True)
            elif self.settings_sel == 2:
                self.settings["flash"] = not self.settings.get("flash", True)
            elif self.settings_sel == 3:
                self.settings["shake"] = not self.settings.get("shake", True)
            else:
                self.settings["hints"] = not self.settings.get("hints", True)
            self.best["settings"] = dict(self.settings)
            self.save_meta()
        elif ch == 27:
            if getattr(self, "settings_from_pause", False):
                self.settings_from_pause = False
                self.state = getattr(self, "pause_state", "combat")
                self.overlay = "pause"
                self.menu = 4
            else:
                self.state = "title"

    # -------------------------------------------------------------- codex --
    CODEX_TABS = ["CARDS", "RELICS", "POTIONS", "BESTIARY", "ACHIEVEMENTS"]

    def codex_entries(self):
        tab = self.codex_tab
        seen = self.best["seen"]
        if tab == 0:
            order = {"minion": 0, "spell": 1}
            corder = {c: n for n, c in enumerate(self.CLASS_ORDER)}
            ids = sorted((i for i in BOARD_CARDS
                          if not BOARD_CARDS[i]["token"]
                          and BOARD_CARDS[i]["cls"] in self.CLASS_ORDER),
                         key=lambda i: (corder.get(BOARD_CARDS[i].get("cls"), 9),
                                        order.get(BOARD_CARDS[i]["kind"], 2),
                                        BOARD_CARDS[i]["cost"],
                                        BOARD_CARDS[i]["name"]))
            return [dict(key=i, name=BOARD_CARDS[i]["name"],
                         short=(f"{BOARD_CARDS[i]['cost']} "
                                f"{'M' if BOARD_CARDS[i]['kind'] == 'minion' else 'S'}")
                         if i in seen["cards"] else "",
                         seen=i in seen["cards"]) for i in ids]
        if tab == 1:
            return [dict(key=i, name=RELICS[i]["name"],
                         short=("BOON" if RELICS[i].get("boss") else "RELIC")
                         if i in seen["relics"] else "",
                         seen=i in seen["relics"])
                    for i in sorted(RELICS, key=lambda r: RELICS[r]["name"])]
        if tab == 2:
            return [dict(key=i, name=POTIONS[i]["name"],
                         short="POTION" if i in seen["potions"] else "",
                         seen=i in seen["potions"]) for i in sorted(POTIONS)]
        if tab == 3:
            return [dict(key=i, name=h["name"],
                         short=("BOSS" if h.get("boss") else
                                "ELITE" if h.get("elite") else "MOB"),
                         seen=True)
                    for i, h in sorted(enumerate(ENEMY_HEROES),
                                       key=lambda kv: kv[1]["name"])]
        return [dict(key=i, name=ACHIEVEMENTS[i]["name"], short="",
                     seen=i in self.best["achievements"])
                for i in sorted(ACHIEVEMENTS, key=lambda a: ACHIEVEMENTS[a]["name"])]

    def codex_totals(self):
        seen = self.best["seen"]
        codex_cards = sum(1 for c in BOARD_CARDS.values()
                          if not c["token"] and c["cls"] in self.CLASS_ORDER)
        return [(len(seen["cards"]), codex_cards),
                (len(seen["relics"]), len(RELICS)),
                (len(seen["potions"]), len(POTIONS)),
                (len(ENEMY_HEROES), len(ENEMY_HEROES)),
                (len(self.best["achievements"]), len(ACHIEVEMENTS))]

    def codex_detail(self, e, width):
        tab = self.codex_tab
        if not e["seen"]:
            return ["Not discovered yet.", "",
                    "Find it in the spire to unlock this entry."]
        if tab == 0:
            c = BOARD_CARDS[e["key"]]
            cname = CLASSES.get(c.get("cls"), {}).get("name", "Neutral")
            head = f"{c['kind'].title()}  \u00b7  {cname}  \u00b7  Cost {c['cost']}"
            lines = [head, ""]
            if c["kind"] == "minion":
                kw = V.kw_glyphs(c["kw"], UTF)
                labels = " ".join(V.KW_LABEL[k] for k in
                                  ("taunt", "divine_shield", "poisonous",
                                   "charge", "rush", "windfury")
                                  if k in c["kw"])
                lines.append(f"{c['atk']} / {c['hp']}   {kw} {labels}".rstrip())
                lines.append("")
            lines += wrap(c["text"] or "No ability.", width)
            return lines
        if tab == 1:
            r = RELICS[e["key"]]
            return [("Ember boon" if r.get("boss") else "Relic"), ""] + \
                wrap(r["desc"], width)
        if tab == 2:
            return [POTIONS[e["key"]]["name"], ""] + \
                wrap(POTIONS[e["key"]]["desc"], width)
        if tab == 3:
            d = ENEMY_HEROES[e["key"]]
            kind = ("Keeper" if d.get("boss") else
                    "Elite" if d.get("elite") else "Enemy")
            return [f"HP {d['hp']}", kind,
                    f"{len(d['deck'])} cards in its deck", "",
                    "It plays minions and attacks with them."]
        a = ACHIEVEMENTS[e["key"]]
        return [a["desc"], "", "Unlocked" if e["seen"] else "Locked"]

    def draw_codex(self):
        tabs = self.CODEX_TABS
        totals = self.codex_totals()
        got = sum(a for a, b in totals)
        total = sum(b for a, b in totals)
        self.put(0, 2, "CINDERSPIRE", C("gold", bold=True))
        self.put(0, 15, GL["sep"], C("faint"))
        self.put(0, 17, "CODEX", C("dim"))
        s = f"{got} / {total} discovered"
        self.put(0, self.w - 2 - len(s), s, C("dim"))
        # tabs as chips with a live progress bar
        x = 3
        for i, name in enumerate(tabs):
            active = i == self.codex_tab
            w = self.chip(2, x, name, "gold" if active else "faint",
                          rev=active, bold=active)
            x += w + 1
        got_tab, tot_tab = totals[self.codex_tab]
        self.bar(3, 3, 24, got_tab, max(1, tot_tab),
                 color=self.accent())
        self.put(3, 29, f"{got_tab}/{tot_tab}", C("dim"))
        bw = 38
        bh = self.h - 7
        self.box(4, 2, bh, bw, C("gold", dim=True))
        self.box(4, 42, bh, self.w - 44, C("gold", dim=True))
        entries = self.codex_entries()
        self.codex_sel = max(0, min(self.codex_sel, max(0, len(entries) - 1)))
        rows = bh - 4
        if self.codex_sel < self.codex_scroll:
            self.codex_scroll = self.codex_sel
        if self.codex_sel >= self.codex_scroll + rows:
            self.codex_scroll = self.codex_sel - rows + 1
        self.codex_scroll = max(0, min(self.codex_scroll,
                                       max(0, len(entries) - rows)))
        self.put(4, 4, f"{tabs[self.codex_tab]}  {totals[self.codex_tab][0]}/"
                 f"{totals[self.codex_tab][1]}", C("gold", bold=True))
        for k in range(rows):
            i = self.codex_scroll + k
            if i >= len(entries):
                break
            e = entries[i]
            y = 6 + k
            sel = i == self.codex_sel
            name = e["name"] if e["seen"] else "???"
            attr = C("gold", bold=True) if sel else (
                C("text") if e["seen"] else C("faint"))
            if sel:
                self.put(y, 3, " " * (bw - 2), C("blue", rev=True))
                self.put(y, 1, GL["arrow"], C("gold", bold=True))
            elif i % 2:
                self.put(y, 3, " " * (bw - 2), C("coal", dim=True))
            self.put(y, 4, cut(name, bw - 16), attr)
            if e["seen"]:
                self.put(y, bw - 10, GL["bullet"], C("gold", dim=True))
            self.put(y, bw - 8, e["short"], C("faint"))
        # detail
        e = entries[self.codex_sel] if entries else None
        if e:
            dw = self.w - 48
            self.put(4, 44, "DETAIL", C("gold", bold=True))
            for j, line in enumerate(self.codex_detail(e, dw)):
                if 6 + j > bh + 2:
                    break
                self.put(6 + j, 44, cut(line, dw), C("text"))
        seen_all = totals[self.codex_tab][0]
        self.hint(f"{seen_all} of {totals[self.codex_tab][1]} in this page"
                  "   \u2190\u2192 page   \u2191\u2193 scroll   esc back")

    def key_codex(self, ch):
        if ch == 27:
            self.state = "title"
            return
        if ch in LEFT_KEYS:
            self.codex_tab = (self.codex_tab - 1) % len(self.CODEX_TABS)
            self.codex_sel = self.codex_scroll = 0
        elif ch in RIGHT_KEYS:
            self.codex_tab = (self.codex_tab + 1) % len(self.CODEX_TABS)
            self.codex_sel = self.codex_scroll = 0
        elif ch in UP_KEYS:
            self.codex_sel = max(0, self.codex_sel - 1)
        elif ch in DOWN_KEYS:
            self.codex_sel = min(len(self.codex_entries()) - 1,
                                 self.codex_sel + 1)
        elif ch in (curses.KEY_PPAGE,):
            self.codex_sel = max(0, self.codex_sel - 10)
        elif ch in (curses.KEY_NPAGE,):
            self.codex_sel = min(len(self.codex_entries()) - 1,
                                 self.codex_sel + 10)

    def draw_history(self):
        self.draw_header("history")
        hist = list(self.best.get("history", []))[:5]
        wdt = min(76, self.w - 8)
        hgt = min(7 + len(hist) * 2, self.h - 4)
        y, x = self.overlay_box(hgt, wdt, "LAST RUNS")
        if not hist:
            self.put(y + 2, x + 3, "No runs yet.", C("dim"))
        for i, h in enumerate(hist):
            yy = y + 2 + i * 2
            if yy > y + hgt - 3:
                break
            if i % 2 == 0:
                self.put(yy, x + 2, " " * (wdt - 4), C("coal", dim=True))
            won = h.get("won")
            tag = " WIN " if won else "DIED "
            col = "green" if won else "red"
            self.chip(yy, x + 3, tag.strip(), col, rev=True)
            if won:
                self.put(yy, x + 9, GL["star"], C("gold", bold=True))
            self.put(yy, x + 12, f"Act {ROMAN[min(h.get('act', 0), 2)]}"
                     f"  {GL['sep']}  floor {h.get('floor', 0)}/21",
                     C("text"))
            self.put(yy, x + 38, f"score {h.get('score', 0)}", C("gold"))
            self.put(yy, x + 55, str(h.get("when", "")), C("faint"))
        self.put(y + min(hgt, self.h - 4) - 2, x + 3, "esc back", C("faint"))

    CLASS_ORDER = ["warden", "ashblade", "emberwright", "pilgrim", "paladin"]

    def choose_class(self, asc=0, seed=None, daily=False):
        self.pending = dict(asc=asc, seed=seed, daily=daily)
        self.class_sel = 0
        self.state = "class"

    def draw_class(self):
        self.draw_header("new run")
        self.center(2, "C H O O S E   Y O U R   P A T H",
                    C("gold", bold=True))
        start_y = max(3, (self.h - 20) // 2)
        for i, cid in enumerate(self.CLASS_ORDER):
            meta = CLASSES[cid]
            col = V.accent_for(cid)
            y = start_y + i * 4
            sel = i == self.class_sel
            wdt = min(62, self.w - 8)
            x = (self.w - wdt) // 2
            if sel:
                self.panel(y, x, 4, wdt, None, accent=col, double=True)
            else:
                self.box(y, x, 4, wdt, C(col, dim=True), rounded=True)
            self.put(y + 1, x + 2, f"({V.CLASS_EMBLEM[cid]})",
                     C(col, bold=True))
            self.put(y + 1, x + 6, meta["name"].upper(),
                     C("white", bold=True) if sel else C(col, bold=True))
            n = sum(1 for c in BOARD_CARDS.values()
                    if c.get("cls") == cid and not c["token"])
            self.put(y + 1, x + wdt - 9, f"{n:>2} cards", C("faint"))
            self.put(y + 2, x + 6, cut(meta["detail"], wdt - 20),
                     C("text" if sel else "dim"))
            if sel:
                self.put(y + 2, x + wdt - 4, GL["arrow"],
                         C(col, bold=True))
            self.put(y + 2, x + 5, GL["bullet"], C("faint"))
            self.hot_add(x, y, wdt, 4, ("class", i))
        self.hint("\u2191\u2193 choose   enter begin   esc back")

    def key_class(self, ch):
        if ch in UP_KEYS:
            self.class_sel = (self.class_sel - 1) % len(self.CLASS_ORDER)
        elif ch in DOWN_KEYS:
            self.class_sel = (self.class_sel + 1) % len(self.CLASS_ORDER)
        elif is_enter(ch) or ch == ord(" "):
            cls = self.CLASS_ORDER[self.class_sel]
            self.new_run(self.pending.get("asc", 0),
                         self.pending.get("seed"),
                         self.pending.get("daily", False), cls)
        elif ch == 27:
            self.state = "title"

    def draw_seed(self):
        self.draw_header("new run", boss_label=False)
        wdt = 54
        hgt = 9
        y, x = self.overlay_box(hgt, wdt, "ENTER A SEED")
        self.put(y + 1, x + (wdt - 11) // 2, GL["star"] + " SEED "
                 + GL["star"], C("gold", bold=True))
        self.put(y + 3, x + (wdt - 22) // 2, "seed:", C("dim"))
        cursor = "_" if int(self.t * 2) % 2 == 0 else " "
        val = (self.seed_buf or "random") + cursor
        self.put(y + 4, x + (wdt - len(val)) // 2, val, C("gold", bold=True))
        self.put(y + 6, x + 3, "0-9 type   backspace erase", C("faint"))
        kx = x + 3
        kx += self.keycap(y + hgt - 2, kx, "ENTER", "start", "green") + 2
        self.keycap(y + hgt - 2, kx, "ESC", "back", "red")

    def key_seed(self, ch):
        if ch in (10, 13, curses.KEY_ENTER):
            self.choose_class(0, int(self.seed_buf) if self.seed_buf else None,
                              False)
        elif ch == 27:
            self.state = "title"
        elif ch in (curses.KEY_BACKSPACE, 8, 127):
            self.seed_buf = self.seed_buf[:-1]
        elif ord("0") <= ch <= ord("9") and len(self.seed_buf) < 9:
            self.seed_buf += chr(ch)

    def save_meta(self):
        save_best(self.best)

    def notify(self, msg, dur=3.0, priority=False):
        now = time.monotonic()
        if self.toast and now < self.toast[1]:
            if priority:
                self.toast_queue.insert(0, (msg, dur))
            else:
                self.toast_queue.append((msg, dur))
        else:
            self.toast = (msg, now + dur)

    def unlock(self, aid):
        if aid not in ACHIEVEMENTS or aid in self.best["achievements"]:
            return False
        self.best["achievements"].append(aid)
        self.save_meta()
        self.notify(f"Achievement: {ACHIEVEMENTS[aid]['name']}", 3.5,
                    priority=True)
        return True

    def see(self, kind, ids):
        lst = self.best["seen"].get(kind)
        if lst is None:
            return
        changed = False
        for i in ids:
            if i and i not in lst:
                lst.append(i)
                changed = True
        if changed:
            self.save_meta()
            total = (len(CARDS) + len(RELICS) + len(POTIONS) + len(ENEMIES))
            got = sum(len(v) for v in self.best["seen"].values())
            if total and got / total >= 0.8:
                self.unlock("loremaster")

    def tip(self, key):
        if not self.settings.get("hints", True):
            return
        if key in self.best.get("tips", []) or key not in TIPS:
            return
        self.best["tips"].append(key)
        self.save_meta()
        self.notify(TIPS[key], 3.5)

    def save_progress(self):
        if not self.run:
            return
        try:
            save_run(run_to_dict(self.run, self.path))
            self.saved = True
        except Exception:
            pass

    def continue_run(self):
        d = load_run()
        if not d:
            self.saved = False
            return
        try:
            self.run = run_from_dict(d)
            self.path = [tuple(p) for p in d.get("path", [])]
        except Exception:
            clear_run()
            self.saved = False
            self.toast = ("The old save could not be read.", time.monotonic() + 3)
            return
        self.cb = None
        self.overlay = None
        self.state = "map"
        self.map_sel = 0
        self.toast = ("Run resumed.", time.monotonic() + 2.5)

    def draw_help(self):
        self.draw_header("how to play", boss_label=False)
        self.rule(2)
        bw = min(80, self.w - 6)
        bx = (self.w - bw) // 2
        by = 3
        bh = min(19, self.h - 6)
        self.panel(by, bx, bh, bw, "THE BASICS", accent=self.accent(),
                   shadow=False)
        rows = [
            (GL["flame"], "GOAL", "Climb three acts and break the keepers."),
            (GL["sword"], "BOARD", "Five minion slots per side. Heroes have 80 HP."),
            ("M", "MANA", "Start at 3, gain one each turn, up to 8."),
            (GL["bolt"], "COMBAT", "Minions attack once; Windfury twice."),
            (GL["shield"], "TAUNT", "Taunt is attacked first. Divine Shield blocks one hit."),
            (GL["star"], "COMBO", "The second card in a turn triggers Combo bonuses."),
            (GL["heart"], "DECK", "Take cards after fights, upgrade at campfires (+1/+1)."),
            (GL["coin"], "SHOP", "Spend gold on cards, relics, potions or a removal."),
            (GL["skull"], "POISON", "Poisonous kills anything it damages. Rush cannot hit heroes."),
        ]
        y = by + 3
        for icon, tag, text in rows:
            if y >= by + bh - 5:
                break
            self.put(y, bx + 3, icon, C(self.accent(), bold=True))
            self.put(y, bx + 6, tag.ljust(7), C("gold", bold=True))
            self.put(y, bx + 14, cut(text, bw - 17), C("text"))
            y += 1
        ky = by + bh - 4
        self.put(ky, bx + 3, GL["h"] * (bw - 6), C("faint"))
        keys = [("1-9", "play"), ("TAB", "rows"), ("ENTER", "act"),
                ("E", "end"), ("A", "all"), ("Q", "potion"),
                ("V", "card"), ("ESC", "menu")]
        kx = bx + 4
        for n, (k, label) in enumerate(keys):
            if n == 4:
                kx = bx + 4
                ky += 1
            need = len(k) + len(label) + 5
            if kx + need > bx + bw - 2:
                continue
            kx += self.keycap(ky + 1, kx, k, label, "gold") + 2
        self.hint("enter to return")

    # ---------------------------------------------------------------- map --
    def lane_x(self, lane):
        panel = self.w - 18
        avail = max(30, panel - 10)
        spacing = min(16, avail // 4)
        total = spacing * 3
        start = 10 + max(0, (avail - total) // 2)
        return start + lane * spacing

    def map_spacing(self):
        floors = self.run.floors if self.run else FLOORS
        return max(2, min(4, (self.h - 9) // floors))

    def row_y(self, r):
        return 3 + r * self.map_spacing()

    def draw_map(self):
        r = self.run
        accent = self.accent()
        self.draw_header(ACT_NAMES[r.act])
        self.rule(2)
        # soft vertical guide behind the route
        for y in range(3, self.row_y(r.floors) + 1):
            if y % 2 == 0:
                for lane in range(4):
                    self.put(y, self.lane_x(lane),
                             GL["dash"], C("coal", dim=True))
        bits = {}
        edges = []
        for (rr, p), kids in r.map["edges"].items():
            for c in kids:
                edges.append((rr, p, c))
        boss_x = (self.lane_x(0) + self.lane_x(3)) // 2
        for (rr, p, c) in edges:
            self.add_edge(bits, self.row_y(rr), self.row_y(rr + 1),
                          self.lane_x(p), self.lane_x(c))
        for p in r.map["rows"][r.floors - 1]["lanes"]:
            self.add_edge(bits, self.row_y(r.floors - 1), self.row_y(r.floors),
                          self.lane_x(p), boss_x)
        for (y, x), m in bits.items():
            self.put(y, x, BOX_MASK[m], C("faint"))
        # travelled route gets a warm trail
        prev = None
        for (rr, lane) in self.path:
            if prev is not None:
                x1, x2 = self.lane_x(prev[1]), self.lane_x(lane)
                y = self.row_y(rr)
                for x in range(min(x1, x2), max(x1, x2) + 1):
                    self.put(y, x, GL["h"], C("ember", dim=True))
            prev = (rr, lane)
        icons = {"monster": "⚔", "elite": "☠", "event": "?",
                 "rest": "●", "shop": "$", "treasure": "▣"}
        avail = r.avail
        for rr, row in enumerate(r.map["rows"]):
            for lane in row["lanes"]:
                t = row["types"][lane]
                meta = NODE_TYPES[t]
                x = self.lane_x(lane)
                y = self.row_y(rr)
                here = (rr, lane) == r.node
                visited = (rr, lane) in self.path
                can = (rr == r.floor and lane in avail
                       and self.run.floor < r.floors)
                icon = icons.get(t, "?")
                label = f"[{icon}]"
                if here:
                    attr = C("white", bold=True, rev=True)
                elif can:
                    pulse = int(self.t * 2.5) % 2 == 0
                    attr = C(meta["color"], bold=True, rev=pulse)
                elif visited:
                    attr = C("faint")
                else:
                    attr = C(meta["color"], dim=visited)
                if visited:
                    self.put(y + 1, x - 1, " " + GL["tick"] + " ",
                             C("green", dim=True))
                self.put(y, x - 1, label, attr)
                if here:
                    self.put(y, x - 4, GL["arrow"], C("gold", bold=True))
                if can:
                    self.hot_add(x - 1, y, 3, 1, ("map", rr, lane))
                if can and avail.index(lane) == self.map_sel % max(1, len(avail)):
                    self.put(y, x - 4, GL["arrow"], C("gold", bold=True))
                    self.put(y, x + 3, GL["arrow"], C("gold", bold=True))
        # boss crown
        by = self.row_y(r.floors)
        boss_avail = r.floor >= r.floors
        battr = C("red", bold=True, rev=boss_avail)
        if not boss_avail:
            battr = C("red", bold=True, dim=True)
        self.put(by - 1, boss_x - 1, "♛", C("red", bold=True,
                                               dim=not boss_avail))
        self.put(by, boss_x - 1, "[B]", battr)
        if boss_avail:
            self.put(by, boss_x - 4, GL["arrow"], C("gold", bold=True))
            self.hot_add(boss_x - 1, by, 3, 1, ("map", FLOORS, "boss"))
        bname = ENEMIES[BOSSES[r.act][0]]["name"].upper()
        self.put(by + 1, boss_x - len(bname) // 2, bname, C("red", dim=True))
        # side panel
        px = self.w - 18
        self.panel(3, px - 1, self.h - 9, 17, "SPIRE", accent=accent,
                   shadow=False)
        self.put(4, px, "RELICS", C("gold", bold=True))
        for i, rid in enumerate(self.run.relics[:7]):
            tag = RELICS[rid]["tag"]
            self.put(5 + i, px, f"[{tag}]", C("gold", dim=True))
            self.put(5 + i, px + 5, cut(RELICS[rid]["name"], 12),
                     C(RELICS[rid]["color"]))
        if len(self.run.relics) > 7:
            self.put(5 + 7, px, f"+{len(self.run.relics) - 7} more", C("dim"))
        py = 13
        self.put(py, px, "BELT", C("cyan", bold=True))
        for i, pid in enumerate(self.run.potions[:3]):
            pm = POTIONS[pid]
            self.put(py + 1 + i, px, V.KW_ICON["lifesteal"],
                     C(pm["color"], bold=True))
            self.put(py + 1 + i, px + 3, cut(pm["name"], 12),
                     C(pm["color"]))
        # legend
        ly = py + 4
        leg = [] if self.h < 30 else [
               (icons["monster"], "mob", "red"),
               (icons["elite"], "elite", "orange"),
               ("?", "event", "purple"),
               (icons["rest"], "rest", "green"),
               ("$", "shop", "gold"),
               (icons["treasure"], "loot", "cyan")]
        for i, (ic, name, col) in enumerate(leg):
            y = ly + i
            if y >= self.h - 2:
                break
            self.put(y, px, f"[{ic}]", C(col, bold=True))
            self.put(y, px + 5, name, C("faint"))
        if self.act_banner_until > time.monotonic() and self.act_banner_text:
            msg = f"{self.act_banner_text}  {GL['sep']}  {ACT_NAMES[r.act]}"
            self.chip(2, max(2, (self.w - len(msg) - 4) // 2), msg,
                      accent, rev=True)
        self.hint("arrows choose   enter travel   d deck   r relics   esc menu")

    def add_edge(self, bits, y1, y2, x1, x2):
        mid = y2 - 1

        def add(yy, xx, m):
            bits[(yy, xx)] = bits.get((yy, xx), 0) | m

        for y in range(y1 + 1, mid):
            add(y, x1, UP | DOWN)
        if x1 == x2:
            add(mid, x1, UP | DOWN)
            return
        step = 1 if x2 > x1 else -1
        add(mid, x1, UP | (RIGHT if step > 0 else LEFT))
        add(mid, x2, DOWN | (LEFT if step > 0 else RIGHT))
        for x in range(min(x1, x2) + 1, max(x1, x2)):
            add(mid, x, LEFT | RIGHT)

    def key_map(self, ch):
        if self.overlay:
            return self.key_overlay(ch)
        r = self.run
        if r.floor >= r.floors:
            if is_enter(ch) or ch == ord(" "):
                self.start_node("boss")
            elif ch == ord("d"):
                self.overlay = "deck"
            elif ch == ord("r"):
                self.overlay = "relics"
            elif ch == 27:
                self.menu = 0
                self.overlay = "pause"
            return
        avail = r.avail
        if not avail:
            return
        if ch in LEFT_KEYS:
            self.map_sel = (self.map_sel - 1) % len(avail)
        elif ch in RIGHT_KEYS:
            self.map_sel = (self.map_sel + 1) % len(avail)
        elif is_enter(ch) or ch == ord(" "):
            lane = avail[self.map_sel % len(avail)]
            kind = r.choose(lane)
            self.path.append((r.floor, lane))
            self.start_node(kind)
        elif ch == ord("d"):
            self.overlay = "deck"
        elif ch == ord("r"):
            self.overlay = "relics"
        elif ch in (ord("v"), ord("V")):
            self.tip_pinned = not self.tip_pinned
            self.card_tip_until = time.monotonic() + 3.0
        elif ch == ord("L"):
            self.overlay = "log"
        elif ch == ord("?"):
            self.overlay = "glossary"
        elif ch in (ord("q"), ord("Q")):
            self.pot_sel = 0
            self.overlay = "potions"
        elif ch == 27:
            self.menu = 0
            self.overlay = "pause"

    # ------------------------------------------------------------- combat --
    # ------------------------------------------------------ board combat --
    def combat_off(self):
        return max(0, (self.h - 24) // 2)

    def draw_combat(self):
        cb = self.cb
        self._pos = {}
        self._hero_ids = set()
        accent = self.accent()
        sub = {"monster": "combat", "normal": "combat",
               "elite": "elite", "boss": "boss"}.get(cb.kind, "combat")
        self.draw_header(sub)
        off = self.combat_off()
        hero_y = 3 + off
        eboard_y = 4 + off
        rule1 = 8 + off
        pboard_y = 9 + off
        log1 = 13 + off
        rule2 = 14 + off
        # ambient ash inside the arena
        if self.ash:
            for a in self.ash:
                if 3 <= int(a[1]) < self.h - 9:
                    self.put(int(a[1]), int(a[0]), a[3],
                             C("ember", dim=True))
        # keep text rails clean of ambient ash
        self.put(hero_y, 0, " " * self.w, C("text"))
        self.put(log1, 0, " " * self.w, C("text"))
        self.rule(2)
        drag_hover = (self.drag.get("hover") if self.drag
                      and self.drag.get("moved") else None)
        hero_sel = self.esel == 0
        hero_drag = drag_hover == ("hero",)
        # enemy hero plaque
        emblem = (cb.enemy.name[:1] or "E").upper()
        ex = 2
        self.put(hero_y, ex, f"({emblem})",
                 C("red", bold=True))
        name = cb.enemy.name.upper()
        nattr = (C("white", bold=True, rev=hero_drag) if hero_drag else
                 C("white", bold=True) if hero_sel else C("red", bold=True))
        self.put(hero_y, ex + 4, cut(name, 18), nattr)
        self.put(hero_y, ex + 23, GL["heart"], C("red"))
        bw = 10
        self.bar(hero_y, ex + 25, bw, cb.enemy.hp, cb.enemy.max_hp)
        self.put(hero_y, ex + 36, f"{cb.enemy.hp}/{cb.enemy.max_hp}",
                 C("bone", bold=True))
        # mana crystals
        self.put(hero_y, ex + 46, "M", C("cyan", dim=True))
        for i in range(max(3, cb.enemy.max_mana)):
            on = i < cb.enemy.mana
            self.put(hero_y, ex + 48 + i * 2,
                     GL["dot"] if on else GL["ring"],
                     C(V.mana_color(i, cb.enemy.mana)))
        self.put(hero_y, ex + 48 + max(3, cb.enemy.max_mana) * 2 + 1,
                 f"H{len(cb.ehand)}", C("dim"))
        self.hot_add(0, hero_y, self.w, 1, ("hero",))
        self._pos[id(cb.enemy)] = (hero_y, 2, 34)
        self._hero_ids.add(id(cb.enemy))
        self.draw_side(cb, "enemy", eboard_y)
        self.rule(rule1)
        self.draw_side(cb, "player", pboard_y)
        self._pos[id(cb.player)] = (1, 5, 18)
        self._hero_ids.add(id(cb.player))
        # turn banner
        if self.turn_banner_until > time.monotonic():
            label = "YOUR TURN" if cb.phase == "player" else "ENEMY TURN"
            msg = f"{label}  {GL['sep']}  TURN {cb.turn}"
            self.chip(2, max(2, (self.w - len(msg) - 4) // 2), msg,
                      accent, rev=True)
        # combo chain badge
        if cb.played_this_turn:
            chain = f"COMBO x{cb.played_this_turn}"
            self.chip(log1, self.w - len(chain) - 5, chain, "orange",
                      rev=True)
        # lethal warning
        if not any(m.alive and m.taunt for m in cb.eboard):
            dmg = sum(m.atk for m in cb.player_alive() if m.ready)
            if dmg >= cb.enemy.hp > 0:
                self.chip(hero_y, self.w - 11, "LETHAL" + GL["skull"],
                          "red", rev=True)
        now = time.monotonic()
        if self.row == 0 and cb.hand and (self.tip_pinned
                                          or now < self.card_tip_until):
            inst = cb.hand[min(self.sel, len(cb.hand) - 1)]
            d = BOARD_CARDS[inst["id"]]
            body = d["text"].replace("\n", " ")
            head = (f"{V.kind_glyph(d['kind'], UTF)} {d['name']} "
                    f"({d['cost']})")
            if d["kind"] == "minion":
                head += (f"  {d['atk'] + inst.get('up', 0)}/"
                         f"{d['hp'] + inst.get('up', 0)}")
                glyphs = V.kw_glyphs(d["kw"], UTF)
                if glyphs:
                    head += "  " + glyphs
            for i, ln in enumerate(wrap(head + ": " + body, self.w - 20)[:1]):
                self.put(log1 + i, 3, ln, C("gold", bold=True))
        else:
            self.put(log1, 2, cut(cb.logs[-1][0], self.w - 4),
                     C(cb.logs[-1][1]) if cb.logs else C("text"))
        self.draw_hand(cb)
        self.draw_attack_line(cb, drag_hover)
        self.draw_popups(cb)
        if self.esel == 0:
            tgt = "HERO"
        elif 0 <= self.esel - 1 < len(cb.eboard):
            m = cb.eboard[self.esel - 1]
            tgt = f"{m.name} {m.atk}/{m.hp}"
        else:
            tgt = "HERO"
        if self.row == 0:
            hint = f"[{tgt}] 1-9 play  TAB target  A all  E end"
        elif self.row == 1:
            board = cb.player_alive()
            atk = board[min(self.bsel, len(board) - 1)].atk if board else 0
            hint = (f"[{tgt}] {atk} ATK  ENTER attack  0-5 target  "
                    "TAB rows")
        else:
            hint = f"[{tgt}] 0-5 pick  ENTER attack  TAB rows"
        suffix = "  Q potion  V card  ESC"
        if cb.phase == "enemy":
            dots = "." * (int(self.t * 3) % 4)
            hint = f"The enemy is thinking{dots}   please wait"
            suffix = ""
        elif self.drag and self.drag.get("moved"):
            label = self.zone_label(drag_hover)
            if self.drag["zone"] and self.drag["zone"][0] == "board":
                act = "release to attack"
            else:
                act = "release to play"
            hint = (f"DRAG \u2192 {label or 'the board'}   {act}   "
                    "move over the enemy")
            suffix = "   ESC cancel"
        elif cb.played_this_turn:
            hint = "COMBO READY  " + hint
        self.hint(hint + suffix)

    def draw_side(self, cb, side, y):
        board = cb.pboard if side == "player" else cb.eboard
        w = 14
        gap = 1
        total = 5 * w + 4 * gap
        x0 = max(1, (self.w - total) // 2)
        hover = (self.drag.get("hover") if self.drag
                 and self.drag.get("moved") else None)
        for g in range(1, 5):
            gx = x0 + g * (w + gap) - 1
            for yy in range(y, y + 4):
                self.put(yy, gx, GL["v"], C("coal", dim=True))
        for i in range(5):
            x = x0 + i * (w + gap)
            if i < len(board):
                m = board[i]
                sel = side == "player" and self.row == 1 and self.bsel == i
                tgt = (side == "enemy" and self.esel == i + 1) or \
                    hover == (("enemy", i) if side == "enemy" else ("board", i))
                self.draw_minion_tile(y, x, w, m, sel, tgt)
                self._pos[id(m)] = (y, x, w)
                self.hot_add(x, y, w, 4,
                             ("board" if side == "player" else "enemy", i))
            else:
                self.box(y, x, 4, w, C("coal", dim=True), rounded=True)
                self.clear_inside(y, x, 4, w)
                self.put(y + 1, x + 2, GL["dash"] * (w - 4),
                         C("coal", bold=True))
                self.put(y + 2, x + max(1, (w - 5) // 2), "empty",
                         C("faint"))

    def draw_minion_tile(self, y, x, w, m, selected, target):
        cb = self.cb
        if cb is not None and id(m) in cb.shake:
            x += int(math.sin(self.t * 70 + m.atk) * 1.2)
        flash = cb is not None and id(m) in getattr(cb, "flash", {})
        owner_col = "green" if m.owner == "player" else "purple"
        if selected:
            pulse = int(self.t * 5) % 2
            self.box(y, x, 4, w, C("white" if pulse else "gold", bold=True),
                     double=True)
        elif target:
            self.box(y, x, 4, w, C("red", bold=True), double=True)
        elif flash:
            self.box(y, x, 4, w, C("white", bold=True), double=True)
        else:
            self.box(y, x, 4, w, C(owner_col, dim=not m.ready),
                     rounded=True)
        # stat gems
        hp_frac = 0 if m.max_hp <= 0 else m.hp / m.max_hp
        stat_col = V.heal_color(hp_frac)
        self.put(y + 1, x + 1, "⚔", C(owner_col, dim=True))
        self.put(y + 1, x + 2, str(m.atk),
                 C("gold", bold=True) if m.ready else C("dim", bold=True))
        self.put(y + 1, x + 4, GL["heart"], C("red", dim=True))
        self.put(y + 1, x + 5, str(m.hp), C(stat_col, bold=True))
        # keyword icons
        kw_show = [k for k in ("taunt", "divine_shield", "poisonous",
                               "windfury", "rush", "charge") if k in m.kw][:3]
        glyphs = V.kw_glyphs(kw_show, UTF)
        if glyphs:
            self.put(y + 1, x + w - 1 - len(glyphs),
                     glyphs, C("cyan", bold=True))
        # portrait/emblem + name
        em = V.CLASS_EMBLEM.get(BOARD_CARDS.get(m.cid, {}).get("cls", ""), "?")
        attr = C("white", bold=True) if selected else (
            C("red", bold=True) if target else C("text"))
        self.put(y + 2, x + 1, f"({em})", C("faint"))
        self.put(y + 2, x + 5, cut(m.name, w - 7), attr)
        if m.ready:
            self.put(y + 2, x + w - 2, GL["arrow"],
                     C("green", bold=True))
        if m.divine:
            self.put(y + 1, x + w - 2, GL["star"],
                     C("holy", bold=True))
        if target:
            for cy, cx in ((y, x), (y, x + w - 1), (y + 3, x),
                           (y + 3, x + w - 1)):
                self.put(cy, cx, GL["cross"], C("red", bold=True))

    def draw_attack_line(self, cb, drag_hover=None):
        """A faint dotted arrow from the acting minion to its target."""
        src = None
        if self.row == 1 and cb.player_alive():
            i = min(self.bsel, len(cb.player_alive()) - 1)
            m = cb.player_alive()[i]
            if m.ready:
                src = self._pos.get(id(m))
        if self.drag and self.drag.get("moved"):
            src_zone = self.drag.get("zone")
            if src_zone and src_zone[0] == "board":
                board = cb.player_alive()
                if 0 <= src_zone[1] < len(board):
                    src = self._pos.get(id(board[src_zone[1]]))
        if not src:
            return
        if drag_hover and drag_hover[0] in ("hero", "enemy"):
            dst = getattr(self, "_drag_xy", None)
            ty, tx = dst if dst else (4, self.w // 2)
        else:
            dst = None
            if self.esel == 0:
                dst = self._pos.get(id(cb.enemy))
            elif 0 <= self.esel - 1 < len(cb.eboard):
                dst = self._pos.get(id(cb.eboard[self.esel - 1]))
            if not dst:
                return
            ty, tx, _ = dst
            tx = self.w // 2 if self.esel == 0 else tx + 7
        sy, sx, sw = src
        sx += sw // 2
        sy += 2
        steps = max(abs(tx - sx), abs(ty - sy))
        if steps < 2:
            return
        for k in range(1, steps):
            xx = sx + round((tx - sx) * k / steps)
            yy = sy + round((ty - sy) * k / steps)
            if (yy, xx) in ((sy, sx), (ty, tx)):
                continue
            self.put(yy, xx, GL["bullet"], C(self.accent(), dim=True))
        self.put(ty, tx, GL["cross"], C("red", bold=True))

    def draw_popups(self, cb):
        now = time.monotonic()
        for key, val in list(cb.popups.items()):
            text, color, ttl = val
            pos = self._pos.get(key)
            if not pos:
                continue
            y, x, w = pos
            rise = int((0.8 - max(0.0, ttl)) * 5)
            # enemy minions sit directly under the hero rail; keep their
            # damage numbers inside the tile instead of on the hero line.
            if key in getattr(self, "_hero_ids", ()):
                py = max(2, y - 1 - rise)
            elif y <= 9:
                py = y + 2
            else:
                py = max(2, y - 1 - rise)
            px = max(1, min(self.w - len(text) - 1, x + max(1, w // 2 - len(text) // 2)))
            self.put(py + 1, px + 1, text, C("coal", bold=True))
            self.put(py, px, text, C(color, bold=True, rev=True))

    def draw_hand(self, cb):
        h = self.h
        accent = self.accent()
        cards_y = h - 9
        header_y = cards_y - 1
        n = len(cb.hand)
        self.chip(header_y, 2, "MANA", "cyan", rev=False)
        mx = max(3, cb.player.max_mana)
        for i in range(mx):
            on = i < cb.player.mana
            self.put(header_y, 9 + i * 2,
                     "\u25c6" if on else "\u25c7",
                     C(V.mana_color(i, cb.player.mana), bold=on))
        self.put(header_y, 9 + mx * 2 + 1,
                 f"{cb.player.mana}/{cb.player.max_mana}", C("dim"))
        turn = f"TURN {cb.turn}"
        self.chip(header_y, 31, turn, accent, rev=True)
        self.put(header_y, 41, GL["bullet"], C("faint"))
        self.put(header_y, 43, f"DECK {len(cb.deck)}", C("dim"))
        self.put(header_y, 53, f"GRAVE {len(cb.discard)}", C("faint"))
        bx = self.w - 14
        end_col = "gold" if cb.phase == "player" else "faint"
        self.chip(header_y, bx, "END TURN", end_col, rev=cb.phase == "player")
        self.hot_add(bx, header_y, 12, 1, ("end",))
        if n == 0:
            self.center(cards_y + 3, "no cards in hand", C("faint"))
            return
        gap = 1
        if n > 6:
            show = 6
            self.sel = max(0, min(self.sel, n - 1))
            start = min(max(0, self.sel - show // 2), n - show)
            cw = min(17, max(11, (self.w - (show - 1) * gap - 2) // show))
        else:
            show, start = n, 0
            cw = min(17, max(9, (self.w - (n - 1) * gap - 2) // n))
        total = show * cw + (show - 1) * gap
        x0 = max(1, (self.w - total) // 2)
        for k in range(show):
            i = start + k
            inst = cb.hand[i]
            self.draw_bcard(cards_y, x0 + k * (cw + gap), cw, inst,
                            i == self.sel and self.row == 0,
                            cb.can_play(i))
            self.hot_add(x0 + k * (cw + gap), cards_y, cw, 8, ("hand", i))
        if start > 0:
            self.put(header_y, 58, f"\u2039 {start}", C("gold", dim=True))
        if start + show < n:
            self.put(header_y, 61, f"{n - start - show} \u203a",
                     C("gold", dim=True))

    def draw_bcard(self, y, x, w, inst, selected, playable):
        d = BOARD_CARDS[inst["id"]]
        up = inst.get("up", 0)
        cb = self.cb
        kind_col = "purple" if d["kind"] == "spell" else "green"
        cls = d.get("cls", "neutral")
        edge = V.accent_for(cls) if cls in V.CLASS_ACCENT else kind_col
        combo = (cb is not None and cb.played_this_turn > 0
                 and d.get("combo"))
        if selected:
            pulse = int(self.t * 5) % 2
            self.box(y, x, 8, w, C("white" if pulse else "gold", bold=True),
                     double=True)
        else:
            self.box(y, x, 8, w, C(edge, dim=not playable), rounded=True)
        # top accent stripe and cost gem
        self.put(y, x + 5, GL["h"] * max(0, w - 10), C(edge, bold=playable))
        cost_txt = f"({d['cost']})"
        self.put(y, x + 1, cost_txt,
                 C("gold", bold=True) if playable else C("dim"))
        name_icon = V.kind_glyph(d["kind"], UTF)
        name = cut(d["name"], w - 6)
        self.put(y + 1, x + 2, f"{name_icon} {name}",
                 C("white", bold=True) if selected else
                 C(edge, bold=True, dim=not playable))
        self.put(y + 2, x + 1, GL["dash"] * (w - 2), C(edge, dim=True))
        if d["kind"] == "minion":
            atk = d["atk"] + up
            hp = d["hp"] + up
            self.put(y + 3, x + 2, "\u2694", C("gold", dim=True))
            self.put(y + 3, x + 3, str(atk),
                     C("gold", bold=True) if playable else C("dim"))
            self.put(y + 3, x + 6, GL["heart"], C("red", dim=True))
            self.put(y + 3, x + 7, str(hp),
                     C("green", bold=True) if playable else C("dim"))
            if up:
                self.put(y + 3, x + 9, f"+{up}", C("cyan", dim=True))
            kw_show = [k for k in ("taunt", "divine_shield", "poisonous",
                                   "windfury", "rush", "charge")
                       if k in d["kw"]][:3]
            glyphs = V.kw_glyphs(kw_show, UTF)
            self.put(y + 4, x + 2, glyphs, C("cyan", dim=True))
            lines = wrap(d["text"], w - 4)
            for i, ln in enumerate(lines[:2]):
                self.put(y + 5 + i, x + 2, cut(ln, w - 4),
                         C("text", dim=not playable))
        else:
            self.put(y + 3, x + 2, f"{V.KIND_ICON['spell']} SPELL",
                     C("purple", bold=True))
            lines = wrap(d["text"], w - 4)
            for i, ln in enumerate(lines[:3]):
                self.put(y + 4 + i, x + 2, cut(ln, w - 4),
                         C("text", dim=not playable))
        if combo:
            self.put(y, x + w - 4, " C ", C("orange", bold=True, rev=True))
        rar = V.rarity_glyph(d["cost"], UTF)
        self.put(y + 7, x + w - 2 - len(rar), rar,
                 C("gold" if d["cost"] >= 5 else "faint", dim=True))
        if selected:
            self.put(y + 7, x + 1, GL["arrow"], C("gold", bold=True))

    def enemy_target(self):
        if self.esel == 0:
            return ("hero",)
        return ("e", self.esel - 1)

    def key_combat(self, ch):
        cb = self.cb
        if self.overlay:
            return self.key_overlay(ch)
        if cb.phase != "player":
            return
        n = len(cb.hand)
        board = cb.player_alive()
        if ch in (9,):
            self.row = (self.row + 1) % 3
            self.card_tip_until = time.monotonic() + 2.0
        elif ch in UP_KEYS:
            self.row = (self.row - 1) % 3
        elif ch in DOWN_KEYS:
            self.row = (self.row + 1) % 3
        elif ch in LEFT_KEYS:
            if self.row == 0:
                self.sel = (self.sel - 1) % max(1, n)
                self.card_tip_until = time.monotonic() + 3.0
            elif self.row == 1:
                self.bsel = (self.bsel - 1) % max(1, len(board))
            else:
                self.esel = (self.esel - 1) % (len(cb.eboard) + 1)
        elif ch in RIGHT_KEYS:
            if self.row == 0:
                self.sel = (self.sel + 1) % max(1, n)
                self.card_tip_until = time.monotonic() + 3.0
            elif self.row == 1:
                self.bsel = (self.bsel + 1) % max(1, len(board))
            else:
                self.esel = (self.esel + 1) % (len(cb.eboard) + 1)
        elif is_enter(ch) or ch == ord(" "):
            if self.row == 0:
                self.play(self.sel)
            else:
                self.attack_action()
        elif ord("0") <= ch <= ord("9"):
            if self.row == 0 and ch != ord("0"):
                idx = getattr(self, "win_start", 0) + (ch - ord("1"))
                if idx < n:
                    self.sel = idx
                    self.play(idx)
            elif self.row in (1, 2):
                if ch == ord("0"):
                    self.esel = 0
                else:
                    self.esel = min(ch - ord("0"), len(cb.eboard))
                self.card_tip_until = time.monotonic() + 2.0
        elif ch in (ord("a"), ord("A")):
            self.attack_all()
        elif ch in (ord("e"), ord("E")):
            cb.end_turn()
            self.turn_banner_until = time.monotonic() + 0.85
            self.anim_next = time.monotonic() + 0.30 * self.anim
            self.row = 0
            self.sel = 0
        elif ch == ord("d"):
            self.overlay = "deck"
        elif ch == ord("r"):
            self.overlay = "relics"
        elif ch in (ord("v"), ord("V")):
            if cb.hand:
                self.detail = cb.hand[min(self.sel, len(cb.hand) - 1)]
                self.overlay = "carddetail"
        elif ch == ord("?"):
            self.overlay = "glossary"
        elif ch in (ord("q"), ord("Q")):
            self.pot_sel = 0
            self.overlay = "potions"
        elif ch == 27:
            self.menu = 0
            self.overlay = "pause"

    def play(self, i):
        cb = self.cb
        if not cb.can_play(i):
            return
        d = BOARD_CARDS[cb.hand[i]["id"]]
        target = self.enemy_target() if d["kind"] == "spell" else None
        if d["kind"] == "spell" and any(op[0] == "destroy_target"
                                       for op in d["effects"]) and self.esel == 0:
            self.notify("Choose an enemy minion first (TAB).", 2.0)
            return
        cb.play_card(i, target)
        self.sel = max(0, min(self.sel, len(cb.hand) - 1))
        self.card_tip_until = time.monotonic() + 2.0

    def attack_all(self):
        cb = self.cb
        for _ in range(10):
            board = cb.player_alive()
            ready = [i for i, m in enumerate(board) if m.ready]
            if not ready:
                break
            self.bsel = ready[0]
            if not self.attack_action(advance=False):
                break

    def attack_action(self, advance=True):
        cb = self.cb
        board = cb.player_alive()
        if not board:
            return False
        if not board[min(self.bsel, len(board) - 1)].ready:
            ready = [i for i, m in enumerate(board) if m.ready]
            if ready:
                self.bsel = ready[0]
        i = min(self.bsel, len(board) - 1)
        target = self.enemy_target()
        taunts = [j for j, e in enumerate(cb.eboard) if e.alive and e.taunt]
        if taunts and (target[0] == "hero"
                       or not cb.eboard[target[1]].taunt):
            self.notify("A Taunt blocks the way - pick a Taunt minion "
                        "(0-5 or \u2190\u2192).", 2.5)
            self.row = 2
            return False
        ok = cb.attack(i, target)
        if ok and advance:
            ready = [j for j, m in enumerate(cb.player_alive()) if m.ready]
            self.bsel = ready[0] if ready else 0
            self.card_tip_until = time.monotonic() + 2.0
        return ok

    def combat_won(self):
        cb = self.cb
        if cb is None:
            return
        kind = cb.kind
        self.run.hp = max(1, cb.player.hp)
        self.run.stats["kills"] += cb.kills
        self.run.stats["damage"] = self.run.stats.get("damage", 0) + cb.damage_dealt
        life = self.best["lifetime"]
        life["combats"] += 1
        life["kills"] += cb.kills
        life["damage"] += cb.damage_dealt
        self.save_meta()
        self.unlock("first_blood")
        if cb.best_hit >= 12:
            self.unlock("big_hit")
        if len(self.run.relics) >= 8:
            self.unlock("collector")
        if self.run.gold >= 500:
            self.unlock("rich")
        if life["kills"] >= 50:
            self.unlock("slayer")
        self.run.post_combat()
        self.cb = None
        self.win_at = None
        if kind == "boss":
            self.run.gold += 70 + 25 * self.run.act
            if self.run.act == 0:
                self.unlock("act1")
            elif self.run.act == 1:
                self.unlock("act2")
            self.run.add_potion()
            if self.run.act == 2:
                if self.best.get("wins", 0) >= 1:
                    self.heart_sel = 0
                    self.state = "heart"
                else:
                    self.finish_run(True)
            elif self.run.act >= 3:
                self.finish_run(True)
            else:
                self.start_interlude()
            return
        rw = self.run.make_reward(kind)
        self.run.grant_reward(rw)
        self.see("cards", rw["cards"])
        if rw["relic"]:
            self.see("relics", [rw["relic"]])
        self.tip("reward")
        rw["potion"] = None
        if kind == "elite" or self.rng.random() < 0.38:
            rw["potion"] = self.run.add_potion()
        self.reward = rw
        self.reward_sel = 0
        self.state = "reward"
        msg = f"+{rw['gold']} gold"
        if rw["relic"]:
            msg += f"   relic: {RELICS[rw['relic']]['name']}"
        if rw.get("potion"):
            msg += f"   potion: {POTIONS[rw['potion']]['name']}"
            self.see("potions", [rw["potion"]])
        self.notify(msg, 3.0)


    def game_over(self):
        self.cb = None
        self.finish_run(False)

    def finish_run(self, won):
        score = int(self.run.score(won) * (1 + 0.5 * self.run.ascension))
        self.new_best = score > self.best.get("best", 0)
        if won and self.run.ascension >= self.best.get("asc", 1):
            self.best["asc"] = self.run.ascension + 1
        self.best["runs"] = self.best.get("runs", 0) + 1
        if won:
            self.best["wins"] = self.best.get("wins", 0) + 1
        if score > self.best.get("best", 0):
            self.best["best"] = score
        if won:
            cw = self.best.setdefault("class_wins", {})
            cw[self.run.cls] = cw.get(self.run.cls, 0) + 1
            if all(cw.get(c, 0) > 0 for c in self.CLASS_ORDER):
                self.unlock("polymath")
            self.unlock("victory")
            if self.run.act >= 3:
                self.unlock("first_flame")
                self.unlock("fourth")
            if self.run.ascension >= 1:
                self.unlock("asc1")
            if len(self.run.deck) <= 15:
                self.unlock("lean")
        if self.run.daily:
            today = self.today()
            prev = self.best.get("daily", {})
            prev_score = prev.get("score", 0) if prev.get("date") == today else 0
            self.best["daily"] = {"date": today,
                                  "score": max(prev_score, score),
                                  "won": bool(prev.get("won")) or won}
            self.unlock("daily")
        clear_run()
        self.saved = False
        self.best.setdefault("history", []).insert(0, dict(
            score=score, won=won, act=self.run.act,
            floor=self.run.total_floor, when=time.strftime("%Y-%m-%d"),
            seed=self.run.seed))
        del self.best["history"][5:]
        save_best(self.best)
        self.final = dict(score=score, won=won, floor=self.run.total_floor,
                          seed=self.run.seed,
                          damage=self.run.stats.get("damage", 0),
                          act=self.run.act,
                          kills=self.run.stats["kills"],
                          hp=self.run.hp, gold=self.run.gold,
                          deck=len(self.run.deck), relics=len(self.run.relics))
        self.state = "victory" if won else "gameover"
        self.cb = None

    # --------------------------------------------------------------- heart --
    def draw_heart(self):
        r = self.run
        self.draw_header("the ember heart", boss_label=False)
        self.rule(2)
        for i, (glyph, col) in enumerate(((GL["flame"], "ember"),
                                          (GL["heart"], "red"),
                                          (GL["star"], "gold"))):
            self.put(6 + i, 2, glyph, C(col, bold=True))
            self.put(6 + i, self.w - 3, glyph, C(col, bold=True))
        self.center(4, "THE THRONE CRACKS", C("gold", bold=True))
        lines = ["The Cinder King falls, and the throne splits open.",
                 "Below, something older than the spire still burns.",
                 "", "You can leave with the crown - or descend."]
        for i, line in enumerate(lines):
            self.center(6 + i, line, C("text") if line else C("dim"))
        opts = [("Descend into the Ember Heart",
                 "heal and claim a boon - then four floors and the First Flame"),
                ("Take the crown and leave", "end the run as a victor")]
        for i, (label, desc) in enumerate(opts):
            y = 13 + i * 2
            sel = i == self.heart_sel
            self.put(y, 8, (GL["arrow"] + " " + label) if sel
                     else ("  " + label),
                     C("gold", bold=True) if sel else C("text"))
            self.put(y + 1, 10, desc, C("dim"))
            self.hot_add(6, y, self.w - 12, 2, ("heart", i))
        self.hint("\u2191\u2193 choose   enter decide")

    def key_heart(self, ch):
        if ch in UP_KEYS or ch in DOWN_KEYS:
            self.heart_sel = 1 - self.heart_sel
        elif is_enter(ch) or ch == ord(" "):
            if self.heart_sel == 0:
                self.descend_heart()
            else:
                self.finish_run(True)

    def descend_heart(self):
        self.unlock("heart")
        self.start_interlude()

    # ----------------------------------------------------------- interlude --
    def start_interlude(self):
        self.tip("boon")
        self.boons = self.run.roll_boss_relics(3)
        self.see("relics", self.boons)
        self.boon_sel = 0
        heal = int(self.run.max_hp * 0.50)
        self.interlude_heal = min(heal, self.run.max_hp - self.run.hp)
        self.run.hp += self.interlude_heal
        self.run.max_hp += 5
        self.run.hp += 5
        self.state = "interlude"

    def draw_interlude(self):
        r = self.run
        self.draw_header(ACT_NAMES[r.act], boss_label=False)
        self.rule(2)
        self.center(3, f"ACT {ROMAN[r.act]} CLEARED", C("gold", bold=True))
        self.center(4, "the way upward opens", C("dim"))
        self.center(5, f"you recover {self.interlude_heal} HP and gain 5 max HP",
                    C("green"))
        self.center(6, f"HP {r.hp}/{r.max_hp}   \u00b7   {len(r.relics)} relics",
                    C("dim"))
        self.center(7, "choose an ember boon", C("dim"))
        n = len(self.boons)
        wdt = min(28, (self.w - 4) // max(1, n) - 2)
        gap = 2
        total = n * wdt + (n - 1) * gap
        x0 = (self.w - total) // 2
        y = 8
        for i, rid in enumerate(self.boons):
            rl = RELICS[rid]
            x = x0 + i * (wdt + gap)
            sel = i == self.boon_sel
            if sel:
                self.panel(y, x, 8, wdt, None, accent=rl["color"],
                           double=True)
            else:
                self.box(y, x, 8, wdt, C(rl["color"], dim=True),
                         rounded=True)
            if V.sparkle(self.t, i):
                self.put(y + 1, x + wdt - 3, GL["star"],
                         C("gold", bold=True))
            self.put(y + 1, x + 2, f"{GL['star']} {rl['tag']}",
                     C(rl["color"], bold=True))
            self.put(y + 2, x + 2, cut(rl["name"], wdt - 4),
                     C("white", bold=True) if sel else C(rl["color"], bold=True))
            self.put(y + 3, x + 1, GL["h"] * (wdt - 2), C(rl["color"], dim=True))
            for j, line in enumerate(wrap(rl["desc"], wdt - 4)[:3]):
                self.put(y + 4 + j, x + 2, cut(line, wdt - 4), C("text"))
            self.hot_add(x, y, wdt, 8, ("interlude", i))
        self.hint("arrows choose   enter claim")

    def key_interlude(self, ch):
        if not self.boons:
            if is_enter(ch) or ch == ord(" "):
                self.advance_act()
            return
        if ch in LEFT_KEYS:
            self.boon_sel = (self.boon_sel - 1) % len(self.boons)
        elif ch in RIGHT_KEYS:
            self.boon_sel = (self.boon_sel + 1) % len(self.boons)
        elif is_enter(ch) or ch == ord(" "):
            self.run.add_relic(self.boons[self.boon_sel])
            self.see("relics", [self.boons[self.boon_sel]])
            self.advance_act()

    def advance_act(self):
        self.run.next_act()
        self.save_progress()
        self.act_banner_text = f"ACT {ROMAN[self.run.act]}"
        self.act_banner_until = time.monotonic() + 2.2
        self.path = []
        self.map_sel = 0
        self.sel = 0
        self.tgt = 0
        self.state = "map"
        self.notify(f"Act {ROMAN[self.run.act]} \u00b7 "
                    f"{ACT_NAMES[self.run.act].title()}", 3.0)

    # ------------------------------------------------------------- reward --
    def draw_reward(self):
        self.draw_header("spoils")
        self.rule(2)
        rw = self.reward
        accent = self.accent()
        self.center(3, GL["star"] + "  V I C T O R Y  " + GL["star"],
                    C("green", bold=True))
        self.center(4, "the enemies lie still", C("dim"))
        line = 5
        if rw["relic"]:
            rl = RELICS[rw["relic"]]
            self.center(line, f"{GL['star']}  {rl['name']}  {GL['star']}",
                        C(rl["color"], bold=True))
            line += 1
            self.center(line, cut(rl["desc"], self.w - 8), C("dim"))
            line += 1
        if rw.get("potion"):
            pm = POTIONS[rw["potion"]]
            self.center(line, f"{GL['bolt']} {pm['name']}",
                        C(pm["color"], bold=True))
            line += 1
        self.center(line + 1, "choose a card to add to your deck", C("dim"))
        n = len(rw["cards"])
        cw = 19
        gap = 2
        total = n * cw + (n - 1) * gap
        x0 = (self.w - total) // 2
        y = max(10, line + 3)
        for i, cid in enumerate(rw["cards"]):
            d = BOARD_CARDS[cid]
            yy = y - (1 if n >= 3 and i == n // 2 else 0)
            self.draw_bcard(yy, x0 + i * (cw + gap), cw,
                            {"id": cid, "up": 0},
                            i == self.reward_sel, True)
            # rarity sparkle above high-cost cards
            if d["cost"] >= 5 and V.sparkle(self.t, i):
                self.put(yy + 1, x0 + i * (cw + gap) + cw - 3,
                         GL["star"], C("gold", bold=True))
            if i == self.reward_sel:
                for j in range(3):
                    self.put(yy + 9 + (j == 1), x0 + i * (cw + gap) + 2 + j * 5,
                             GL["star"], C("gold", bold=True))
            self.hot_add(x0 + i * (cw + gap), yy, cw, 8, ("reward", i))
        # coin stacks
        for sx in (3, self.w - 8):
            for j, line in enumerate(V.COIN):
                self.put(self.h - 5 + j, sx, line,
                         C("gold", bold=(j == 1), dim=(j != 1)))
        self.hint("arrows choose   enter take card   s skip")
        self.chip(self.h - 1, self.w - 10, "SKIP", "gold", rev=True)
        self.hot_add(self.w - 10, self.h - 1, 8, 1, ("skip",))

    def key_reward(self, ch):
        n = len(self.reward["cards"])
        if ch in LEFT_KEYS:
            self.reward_sel = (self.reward_sel - 1) % n
        elif ch in RIGHT_KEYS:
            self.reward_sel = (self.reward_sel + 1) % n
        elif is_enter(ch) or ch == ord(" "):
            cid = self.reward["cards"][self.reward_sel]
            self.run.add_card(cid)
            self.notify(f"{BOARD_CARDS[cid]['name']} added to your deck.", 2.0)
            self.reward = None
            self.leave_node()
        elif ch in (ord("s"), ord("S"), 27):
            self.reward = None
            self.leave_node()

    def leave_node(self):
        self.run.advance()
        self.save_progress()
        self.state = "map"
        self.map_sel = 0
        self.sel = 0
        self.cb = None
        self.overlay = None

    # --------------------------------------------------------------- rest --
    def draw_rest(self):
        self.draw_header("campfire")
        self.rule(2)
        accent = self.accent()
        cx = self.w // 2
        y = 4
        flick = int(self.t * 8) % 3
        cols = ["gold", "orange", "red", "ember"]
        for i, line in enumerate(V.CAMPFIRE):
            col = cols[(i + flick) % len(cols)]
            self.put(y + i, cx - 10, line, C(col, bold=True))
        # rising sparks
        for i in range(6):
            sx = cx - 8 + int((math.sin(self.t * 1.7 + i) + 1) * 7)
            sy = y + 5 - int((self.t * 6 + i * 3) % 8)
            if sy >= y - 1:
                self.put(sy, sx, "*" if i % 3 == 0 else ".",
                         C("ember" if i % 2 else "gold", dim=True))
        self.center(y + 8, "A quiet place between the fires.", C("dim"))
        upg = sum(1 for c in self.run.deck if can_upgrade(c))
        opts = [("Rest", f"Heal {int(self.run.max_hp * 0.3)} HP", GL["heart"],
                 "green"),
                ("Smith", f"Upgrade a card ({upg} available)",
                 V.KIND_ICON["minion"], "gold")]
        for i, (name, desc, icon, col) in enumerate(opts):
            oy = y + 10 + i * 3
            sel = i == self.rest_sel
            wdt = 44
            ox = cx - wdt // 2
            if sel:
                self.panel(oy, ox, 3, wdt, None, accent=accent,
                           double=True, shadow=True)
            else:
                self.box(oy, ox, 3, wdt, C("coal", dim=True), rounded=True)
            label = f"{icon} {name}"
            self.put(oy + 1, ox + 3, label,
                     C(col if sel else "text", bold=sel))
            self.put(oy + 1, ox + 15, cut(desc, wdt - 17),
                     C("text" if sel else "dim"))
            self.put(oy + 1, ox + wdt - 4, GL["arrow"] if sel else " ",
                     C(accent, bold=True))
            self.hot_add(ox, oy, wdt, 3, ("rest", i))
        heal = min(self.run.max_hp - self.run.hp, int(self.run.max_hp * 0.3))
        self.center(y + 16, f"{GL['heart']} {self.run.hp}/{self.run.max_hp}"
                    f"  (+{heal} after resting)", C("dim"))
        self.hint("arrows choose   enter confirm")

    def key_rest(self, ch):
        if ch in UP_KEYS or ch in DOWN_KEYS:
            self.rest_sel = 1 - self.rest_sel
        elif is_enter(ch) or ch == ord(" "):
            if self.rest_sel == 0:
                base = int(self.run.max_hp * 0.3)
                if "teapot" in self.run.relics:
                    base += 4
                heal = min(self.run.max_hp - self.run.hp, base)
                self.run.hp += heal
                self.rest_msg = f"You rest and heal {heal} HP."
                self.state = "rest_result"
            else:
                if not any(can_upgrade(c) for c in self.run.deck):
                    self.toast = ("Nothing left to upgrade.",
                                  time.monotonic() + 2.0)
                else:
                    self.open_picker("upgrade", self.do_upgrade_rest,
                                     "choose a card to upgrade")
        elif ch == 27:
            self.overlay = "pause"

    def do_upgrade_rest(self, idx):
        self.run.upgrade_card(idx)
        self.rest_msg = (f"{BOARD_CARDS[self.run.deck[idx]['id']]['name']} grows "
                         "stronger (+1/+1).")
        self.state = "rest_result"

    def draw_rest_result(self):
        self.draw_header("campfire")
        self.rule(2)
        self.center(self.h // 2 - 2, "CAMPFIRE", C("gold", bold=True))
        self.center(self.h // 2, self.rest_msg or "", C("text"))
        self.hint("enter continue")

    def key_rest_result(self, ch):
        if is_enter(ch) or ch == ord(" ") or ch == 27:
            self.leave_node()

    # --------------------------------------------------------------- shop --
    def shop_rows(self):
        s = self.run.shop
        rows = [("card", i) for i in range(len(s["cards"]))]
        if s["relic"]:
            rows.append(("relic", 0))
        rows += [("potion", i) for i in range(len(s.get("potions", [])))]
        rows.append(("removal", 0))
        return rows

    def draw_shop(self):
        r = self.run
        s = r.shop
        accent = self.accent()
        self.draw_header("shop")
        self.rule(2)
        # striped awning
        for x in range(2, self.w - 2, 4):
            col = accent if (x // 4) % 2 else "ember"
            self.put(3, x, GL["full"] * 3, C(col, dim=True))
        self.chip(4, 2, "THE ASHEN MARKET", "gold", rev=True)
        self.put(4, self.w - 21, GL["coin"], C("gold", bold=True))
        self.put(4, self.w - 19, f"{r.gold} GOLD", C("gold", bold=True))
        rows = self.shop_rows()
        for k, (kind, idx) in enumerate(rows):
            y = 5 + k * 2
            if y > self.h - 4:
                break
            self.hot_add(2, y, self.w - 4, 1, ("shop", k))
            sel = k == self.shop_sel
            if kind == "card":
                item = s["cards"][idx]
                price = item["price"]
                sold = (f"card:{idx}" in s["sold"] or idx in s["sold"])
                data = BOARD_CARDS[item["cid"]]
            elif kind == "relic":
                price = s["relic_price"]
                sold = "relic" in s["sold"]
                data = RELICS[s["relic"]]
            elif kind == "potion":
                item = s["potions"][idx]
                price = item["price"]
                sold = f"potion:{idx}" in s["sold"]
                data = POTIONS[item["pid"]]
            else:
                price = s["removal"]
                sold = "removal" in s["sold"]
                data = None
            afford = r.gold >= price
            if k:
                self.put(y - 1, 4, GL["dash"] * (self.w - 12),
                         C("coal", dim=True))
            self.put(y, 1, GL["arrow"] if sel else GL["bullet"],
                     C(accent if sel else "faint", bold=sel))
            if kind == "potion":
                col = data.get("color", "purple")
                self.put(y, 4, GL["heart"], C(col, bold=True))
                self.put(y, 6, cut(data["name"], 19),
                         C("faint") if sold else (
                             C("white", bold=True) if sel else C("text")))
                self.put(y, 27, "POTION", C(col, dim=sold))
                self.put(y, 34, cut(data["desc"], self.w - 45), C("dim"))
            elif kind == "card":
                cd = data
                typ = "SPELL" if cd["kind"] == "spell" else "MINION"
                tcol = "purple" if cd["kind"] == "spell" else "green"
                self.put(y, 4, V.kind_glyph(cd["kind"], UTF),
                         C(tcol, bold=True, dim=sold))
                self.put(y, 6, f"({cd['cost']})", C("gold", dim=sold))
                self.put(y, 10, cut(cd["name"], 16),
                         C("faint") if sold else (
                             C("white", bold=True) if sel else C(tcol)))
                self.put(y, 27, typ, C(tcol, dim=sold))
                if cd["kind"] == "minion":
                    desc = (f"{cd['atk']}/{cd['hp']}  "
                            + V.kw_glyphs(cd["kw"], UTF) + "  " + cd["text"])
                else:
                    desc = cd["text"]
                self.put(y, 34, cut(desc, self.w - 45), C("dim"))
            elif kind == "relic":
                self.put(y, 4, GL["star"], C("gold", bold=True, dim=sold))
                self.put(y, 6, cut(data["name"], 19),
                         C("faint") if sold else (
                             C("white", bold=True) if sel else C("gold")))
                self.put(y, 27, "RELIC", C("gold", dim=sold))
                self.put(y, 34, cut(data["desc"], self.w - 45), C("dim"))
            else:
                self.put(y, 4, "X", C("purple", bold=True, dim=sold))
                self.put(y, 6, "Remove a card",
                         C("faint") if sold else (
                             C("white", bold=True) if sel else C("text")))
                self.put(y, 27, "SERVICE", C("purple", dim=sold))
                self.put(y, 35, "Cut one card from your deck.", C("dim"))
            # price tag
            if sold:
                self.put(y, self.w - 10, "[SOLD]", C("faint"))
            else:
                pr = f"{price}"
                self.put(y, self.w - 10, GL["coin"], C("gold", bold=True))
                self.put(y, self.w - 8, pr.rjust(6),
                         C("gold" if afford else "red", bold=True))
            if sel and not sold:
                self.put(y + 1, 4, GL["h"] * (self.w - 12),
                         C(accent, dim=True))
        self.put(self.h - 2, 2, "\"Everything has a price, even the ash.\"",
                 C("dim"))
        self.hint("arrows choose   enter buy   esc leave")
        if self.shop_msg:
            self.put(self.h - 3, 2, cut(self.shop_msg, self.w - 4), C("green"))

    def key_shop(self, ch):
        if self.overlay:
            return self.key_overlay(ch)
        rows = len(self.shop_rows())
        if ch in UP_KEYS:
            self.shop_sel = (self.shop_sel - 1) % rows
        elif ch in DOWN_KEYS:
            self.shop_sel = (self.shop_sel + 1) % rows
        elif is_enter(ch) or ch == ord(" "):
            self.buy()
        elif ch == 27:
            self.leave_node()

    def buy(self):
        r = self.run
        s = r.shop
        rows = self.shop_rows()
        if not rows:
            return
        kind, idx = rows[self.shop_sel % len(rows)]
        if kind == "card":
            if r.buy_card(idx):
                self.shop_msg = f"Bought {BOARD_CARDS[s['cards'][idx]['cid']]['name']}."
            else:
                self.shop_msg = ("Not enough gold." if s["cards"][idx]["price"] > r.gold
                                 else "Sold out.")
        elif kind == "relic":
            if r.buy_relic():
                self.shop_msg = f"Bought {RELICS[s['relic']]['name']}."
            else:
                self.shop_msg = "Not enough gold."
        elif kind == "potion":
            if len(r.potions) >= 3:
                self.shop_msg = "Your potion belt is full."
            elif r.buy_potion(idx):
                self.shop_msg = f"Bought {POTIONS[s['potions'][idx]['pid']]['name']}."
            else:
                self.shop_msg = "Not enough gold."
        else:
            if "removal" in s["sold"]:
                self.shop_msg = "The service has been used."
            elif r.gold < s["removal"]:
                self.shop_msg = "Not enough gold."
            else:
                self.open_picker("remove", self.do_remove_shop,
                                 "choose a card to remove")

    def do_remove_shop(self, idx):
        if not self.run.pay_removal():
            self.shop_msg = "Not enough gold."
            return
        c = self.run.remove_card(idx)
        if c:
            self.shop_msg = f"{BOARD_CARDS[c['id']]['name']} was removed."
        self.overlay = None

    # -------------------------------------------------------------- event --
    def draw_event(self):
        ev = self.event
        accent = self.accent()
        self.draw_header("encounter")
        self.rule(2)
        bw = min(74, self.w - 8)
        bx = (self.w - bw) // 2
        by = 4
        bh = 16
        self.panel(by, bx, bh, bw, None, accent="purple", double=True)
        title = ev["title"].upper()
        tw = self.chip(by + 1, bx + (bw - len(title) - 2) // 2, title,
                       "purple", rev=True)
        stat = (f"{GL['heart']} {self.run.hp}/{self.run.max_hp}   "
                f"{GL['coin']} {self.run.gold}")
        self.put(by + 1, bx + bw - 3 - len(stat), stat, C("dim"))
        # tiny thematic emblem
        low = ev["title"].lower()
        icon = (GL["flame"] if any(k in low for k in ("fire", "flame", "ember"))
                else GL["skull"] if any(k in low for k in ("bone", "dead", "tomb"))
                else GL["star"] if any(k in low for k in ("altar", "shrine", "star"))
                else GL["bolt"])
        self.put(by + 3, bx + 3, icon, C("purple", bold=True))
        for i, line in enumerate(ev["text"]):
            self.put(by + 3 + i, bx + (bw - len(line)) // 2, line, C("text"))
        if self.event_stage < len(ev["choices"]):
            oy = by + 7
            for i, ch in enumerate(ev["choices"]):
                sel = i == self.event_stage
                broke = (ch.get("gold", 0) < 0
                         and self.run.gold + ch["gold"] < 0)
                y = oy + i * 2
                if sel:
                    self.put(y, bx + 2, " " * (bw - 4),
                             C("purple", rev=True))
                    self.put(y, bx + 3, GL["arrow"], C("gold", bold=True))
                num = self.chip(y, bx + 4, str(i + 1),
                                "gold" if not broke else "red", rev=not sel)
                label = ch["label"]
                if broke:
                    label += "  (no gold)"
                self.put(y, bx + 5 + num, cut(label, 24),
                         C("white", bold=True) if sel and not broke else
                         (C("faint") if broke else C("text")))
                # effect badge
                eff = ch["efe"]
                ecol = "red" if broke else ("green" if eff.startswith("+")
                                            else "dim")
                self.put(y, bx + 32, cut(eff, bw - 35),
                         C(ecol, dim=not sel))
                self.hot_add(bx + 3, y, bw - 6, 1, ("event", i))
            self.hint("arrows choose   enter decide")
        else:
            lines = wrap(self.event_msg, bw - 8)
            self.put(by + 7, bx + 2, GL["h"] * (bw - 4), C("faint"))
            for i, line in enumerate(lines[:3]):
                self.put(by + 9 + i, bx + (bw - len(line)) // 2, line,
                         C("gold", bold=True))
            self.put(by + 13, bx + (bw - 12) // 2, "enter continue",
                     C("faint"))
            self.hint("enter continue")

    def key_event(self, ch):
        if self.event_stage < len(self.event["choices"]):
            n = len(self.event["choices"])
            if ch in UP_KEYS:
                self.event_stage = (self.event_stage - 1) % n
            elif ch in DOWN_KEYS:
                self.event_stage = (self.event_stage + 1) % n
            elif is_enter(ch) or ch == ord(" "):
                self.take_event(self.event["choices"][self.event_stage])
        else:
            if is_enter(ch) or ch == ord(" "):
                self.leave_node()

    def take_event(self, ch):
        self.event_choice = ch
        if ch.get("pick"):
            self.open_picker(ch["pick"], self.do_event_pick,
                             f"choose a card to {ch['pick']}")
        else:
            self.event_msg = self.run.resolve_choice(ch)
            self.event_stage = 99

    def do_event_pick(self, idx):
        self.event_msg = self.run.resolve_choice(self.event_choice, picked=idx)
        self.event_stage = 99

    # ------------------------------------------------------------ treasure --
    def draw_treasure(self):
        self.draw_header("treasure")
        self.rule(2)
        accent = self.accent()
        self.center(4, GL["star"] + "  A CACHE IN THE ASH  " + GL["star"],
                    C("cyan", bold=True))
        top = 6
        for i, line in enumerate(V.CHEST):
            self.center(top + i, line, C("gold", bold=True))
        # sparkles around the lid
        for i in range(5):
            sx = self.w // 2 - 12 + int((math.sin(self.t * 2 + i) + 1) * 12)
            sy = top + (i * 2) % 5
            if V.sparkle(self.t, i, 4.0):
                self.put(sy, sx, GL["star"], C("gold", bold=True))
        self.center(top + 7, GL["dh"] * 30, C("faint"))
        for i, line in enumerate(self.treasure_lines):
            self.chip(top + 9 + i * 2,
                      max(2, (self.w - len(line) - 2) // 2), line,
                      "gold", rev=True)
        if self.treasure_desc:
            self.center(top + 12, cut(self.treasure_desc, self.w - 8),
                        C("dim"))
        self.center(self.h - 3, "enter to continue", C("faint"))
        self.hint("enter continue")

    def key_treasure(self, ch):
        if is_enter(ch) or ch == ord(" ") or ch == 27:
            self.leave_node()

    # -------------------------------------------------------- end screens --
    def draw_victory(self):
        self.hot_add(0, 0, self.w, self.h, ("endscreen",))
        f = self.final
        if not self.confetti:
            self.confetti = [[self.rng.uniform(1, self.w - 2),
                              self.rng.uniform(-self.h, 0),
                              self.rng.uniform(0, 6),
                              self.rng.uniform(2.5, 7.0),
                              self.rng.choice([GL["star"], GL["bullet"],
                                               GL["flame"]])]
                             for _ in range(42)]
        for c in self.confetti:
            if 0 <= int(c[1]) < self.h:
                self.put(int(c[1]), int(c[0]), c[4],
                         C(self.rng.choice(["gold", "orange", "ember",
                                            "green"]), dim=True))
        for a in self.ash:
            if 0 <= int(a[1]) < self.h:
                self.put(int(a[1]), int(a[0]), a[3], C("ember", dim=True))
        art = banner("VICTORY")
        y0 = 3
        ramp = ["gold", "brass", "sand", "orange"]
        for i, line in enumerate(art):
            x = max(0, (self.w - len(line)) // 2)
            self.put_grad(y0 + i, x, line, ramp, bold=True)
        if f.get("act", 2) >= 3:
            self.center(y0 + 6, "The First Flame gutters out. The spire goes cold.",
                        C("text"))
            self.center(y0 + 7, "Nothing burns below you any more.",
                        C("dim"))
        else:
            self.center(y0 + 6, "The Cinder King falls. The spire goes dark.",
                        C("text"))
            self.center(y0 + 7, "You descend with the last of the embers.",
                        C("dim"))
        self.stats_block(y0 + 9, f)
        self.chip(self.h - 2, 3, "ENTER TITLE", "gold", rev=True)
        self.chip(self.h - 2, 19, "R NEW RUN", "green", rev=True)
        self.hot_add(0, self.h - 2, self.w, 1, ("endscreen",))

    def draw_gameover(self):
        self.hot_add(0, 0, self.w, self.h, ("endscreen",))
        f = self.final
        if not self.confetti:
            self.confetti = [[self.rng.uniform(1, self.w - 2),
                              self.rng.uniform(0, self.h),
                              self.rng.uniform(0, 6),
                              -self.rng.uniform(1.0, 3.0),
                              self.rng.choice([".", "*", GL["bullet"]])]
                             for _ in range(30)]
        for c in self.confetti:
            if 0 <= int(c[1]) < self.h:
                self.put(int(c[1]), int(c[0]), c[4], C("ember", dim=True))
        art = banner("YOU DIED")
        y0 = 3
        ramp = ["red", "blood", "ember", "rust"]
        for i, line in enumerate(art):
            x = max(0, (self.w - len(line)) // 2)
            self.put_grad(y0 + i, x, line, ramp, bold=True)
        self.center(y0 + 6, "Your deck is scattered in the ash.",
                    C("text"))
        self.center(y0 + 7, GL["skull"] + "  the spire keeps its embers  "
                    + GL["skull"], C("red", dim=True))
        self.stats_block(y0 + 9, f)
        self.chip(self.h - 2, 3, "ENTER TITLE", "gold", rev=True)
        self.chip(self.h - 2, 19, "R NEW RUN", "red", rev=True)
        self.hot_add(0, self.h - 2, self.w, 1, ("endscreen",))

    def stats_block(self, y, f):
        rows = [
            ("FLOORS CLIMBED", f"{f['floor']} / {TOTAL_FLOORS}"),
            ("ACTS CLEARED",
             f"{min(f['act'] + (1 if f['won'] else 0), ACTS)} / {ACTS}"),
            ("ENEMIES SLAIN", str(f["kills"])),
            ("DAMAGE DEALT", str(f.get("damage", 0))),
            ("GOLD", str(f["gold"])),
            ("DECK", f"{f['deck']} cards"),
            ("RELICS", str(f["relics"])),
            ("SCORE", f"{f['score']}   seed {f.get('seed', '-')}"),
        ]
        x = self.w // 2 - 14
        for i, (k, v) in enumerate(rows):
            if i % 2 == 0:
                self.put(y + i, x - 1, " " * 36, C("coal", dim=True))
            self.put(y + i, x, k, C("dim"))
            self.put(y + i, x + 18, v, C("text", bold=True))
            if k == "FLOORS CLIMBED":
                self.bar(y + i, x + 30, 8, f["floor"], TOTAL_FLOORS,
                         color=self.accent())
            elif k == "ACTS CLEARED":
                self.bar(y + i, x + 30, 8,
                         min(f["act"] + (1 if f["won"] else 0), ACTS), ACTS,
                         color="gold")
        if getattr(self, "new_best", False):
            self.center(y + len(rows) + 1, GL["star"] + " NEW BEST SCORE "
                        + GL["star"], C("gold", bold=True))

    def key_end(self, ch):
        if ch in (ord("r"), ord("R")):
            self.new_run(0)
            return
        if is_enter(ch) or ch == ord(" ") or ch == 27:
            self.state = "title"
            self.menu = 0
            self.run = None
            self.cb = None
            self.final = None
            self.overlay = None
            self.new_best = False
            self.confetti = []

    # ------------------------------------------------------------ overlays --
    def draw_overlay(self):
        if self.overlay == "deck":
            cname = CLASSES[self.run.cls]["name"].upper()
            self.draw_card_list(self.run.deck, -1,
                                f"YOUR DECK  \u00b7  {cname}",
                                "s sort   esc to close", sort=self.deck_sort)
        elif self.overlay == "relics":
            self.draw_relics()
        elif self.overlay == "pause":
            self.draw_pause()
        elif self.overlay == "potions":
            self.draw_potions()
        elif self.overlay == "log":
            self.draw_log()
        elif self.overlay == "glossary":
            self.draw_glossary()
        elif self.overlay == "confirm":
            self.draw_confirm()
        elif self.overlay == "picker":
            self.draw_card_list(self.run.deck, self.picker["sel"],
                                self.picker["title"], "arrows choose   "
                                "enter confirm   esc cancel",
                                valid=self.picker["valid"])
        elif self.overlay == "carddetail":
            self.draw_card_detail()

    def overlay_box(self, hgt, wdt, title):
        y = max(1, (self.h - hgt) // 2)
        x = max(1, (self.w - wdt) // 2)
        self.shadow_box(y, x, hgt, wdt)
        self.clear_inside(y, x, hgt, wdt)
        self.box(y, x, hgt, wdt, C(self.accent(), bold=True), double=True,
                 title=title,
                 tattr=C(self.accent(), bold=True), rounded=False)
        for cy, cx, g in ((y, x, GL["rtl"]), (y, x + wdt - 1, GL["rtr"]),
                          (y + hgt - 1, x, GL["rbl"]),
                          (y + hgt - 1, x + wdt - 1, GL["rbr"])):
            self.put(cy, cx, g, C("gold", bold=True))
        return y, x

    def draw_card_detail(self):
        inst = self.detail
        if not inst:
            self.overlay = None
            return
        d = BOARD_CARDS[inst["id"]]
        up = inst.get("up", 0)
        cls = d.get("cls", "neutral")
        edge = V.accent_for(cls) if cls in V.CLASS_ACCENT else "gold"
        wdt = min(68, self.w - 6)
        hgt = min(self.h - 4, 17)
        y, x = self.overlay_box(hgt, wdt, d["name"].upper())
        self.put(y + 1, x + 3, V.kind_glyph(d["kind"], UTF) + " ", C(edge, bold=True))
        head = f"{d['cost']} mana"
        if d["kind"] == "minion":
            head += f"    {V.KIND_ICON['minion']} {d['atk'] + up}    "
            head += f"{GL['heart']} {d['hp'] + up}"
        self.put(y + 1, x + 5, head, C("gold", bold=True))
        if d["kw"]:
            glyphs = V.kw_glyphs(d["kw"], UTF)
            self.put(y + 2, x + 4, glyphs, C("cyan", bold=True))
            labels = " ".join(V.KW_LABEL[k] for k in
                              ("taunt", "divine_shield", "poisonous",
                               "charge", "rush", "windfury", "lifesteal")
                              if k in d["kw"])
            self.put(y + 2, x + 5 + len(glyphs), cut(labels, wdt - 8 - len(glyphs)),
                     C("dim"))
        row = y + 4
        for line in wrap(d["text"], wdt - 8)[:hgt - 8]:
            if "Combo" in line:
                self.put(row, x + 4, line, C("orange", bold=True))
            else:
                self.put(row, x + 4, line, C("text"))
            row += 1
        # large faded class motif fills the lower half of the card
        motif = V.motif(cls, UTF)
        my = min(row + 1, y + hgt - 7)
        for i, line in enumerate(motif):
            self.put(my + i, x + max(2, (wdt - len(line)) // 2), line,
                     C(edge, dim=True))
        if d.get("combo"):
            self.put(y + hgt - 4, x + 4, "Combo bonus:", C("orange", bold=True))
            for line in wrap(" ".join(str(x) for x in d["combo"]),
                             wdt - 10)[:1]:
                self.put(y + hgt - 3, x + 6, cut(line, wdt - 8), C("gold"))
        self.put(y + hgt - 2, x + 3,
                 "any key closes", C("faint"))
        self.hot_add(x, y, wdt, hgt, ("close",))

    def draw_card_list(self, cards, sel, title, hint, valid=None, sort=True):
        wdt = min(96, self.w - 6)
        hgt = min(self.h - 2, max(10, 7 + (len(cards) + 2) // 3))
        y, x = self.overlay_box(hgt, wdt, title)
        rows = max(1, (hgt - 4))
        per_col = rows
        inner = wdt - 4
        colw = inner // 3
        order = {"minion": 0, "spell": 1}
        if sort:
            idxs = sorted(range(len(cards)),
                          key=lambda k: (order.get(BOARD_CARDS[cards[k]["id"]]["kind"], 2),
                                         BOARD_CARDS[cards[k]["id"]]["cost"],
                                         BOARD_CARDS[cards[k]["id"]]["name"]))
        else:
            idxs = list(range(len(cards)))
        for pos, i in enumerate(idxs):
            c = cards[i]
            cd = dict(BOARD_CARDS[c["id"]])
            cd["up"] = c.get("up", 0)
            col = pos // per_col
            rowi = pos % per_col
            if col > 2:
                break
            cy = y + 2 + rowi
            cx = x + 2 + col * colw
            ok = True if valid is None else valid(i)
            is_sel = i == sel
            if is_sel:
                self.put(cy, cx - 1, " " * (colw - 1),
                         C(self.accent(), rev=True))
                self.put(cy, cx - 1, GL["arrow"], C("gold", bold=True))
            elif pos % 2:
                self.put(cy, cx - 1, " " * (colw - 1), C("coal", dim=True))
            elif not ok:
                self.put(cy, cx - 1, " " * (colw - 1), C("faint"))
            attr = C("white", bold=True) if is_sel else (
                C("text") if ok else C("faint"))
            name = cut(cd["name"], colw - 14)
            cost = "X" if cd["cost"] < 0 else str(cd["cost"])
            self.put(cy, cx, V.kind_glyph(cd["kind"], UTF),
                     C("purple" if cd["kind"] == "spell" else "green",
                       dim=not ok))
            self.put(cy, cx + 2, f"({cost})", C("gold") if ok else C("faint"))
            self.put(cy, cx + 6, name, attr)
            if cd.get("up"):
                self.put(cy, cx + 6 + len(name) + 1, GL["star"] * cd["up"],
                         C("cyan", bold=True))
            tag = (f"{cd['atk'] + cd['up']}/{cd['hp'] + cd['up']}"
                   if cd["kind"] == "minion" else "SPELL")
            self.put(cy, cx + colw - 8, tag, C("dim"))
            if sel >= 0:
                self.hot_add(cx - 1, cy, colw - 1, 1, ("pick", i))
        if len(cards) == 0:
            self.put(y + 2, x + 2, "empty", C("dim"))
        for k in (1, 2):
            dx = x + 1 + k * colw
            for yy in range(y + 2, y + hgt - 3):
                self.put(yy, dx, GL["v"], C("coal", dim=True))
        self.put(y + hgt - 2, x + 3, cut(hint, wdt - 6), C("faint"))
        if sel < 0:
            self.hot_add(x, y, wdt, hgt, ("close",))

    def draw_log(self):
        wdt = min(88, self.w - 6)
        logs = self.cb.logs[-18:] if self.cb else []
        hgt = min(self.h - 4, len(logs) + 4)
        y, x = self.overlay_box(hgt, wdt, "COMBAT LOG")
        for i, (msg, col) in enumerate(logs):
            bullet = { "red": GL["skull"], "green": GL["heart"],
                       "gold": GL["star"], "dim": GL["bullet"] }.get(col, GL["bullet"])
            if i % 2 == 0:
                self.put(y + 2 + i, x + 2, " " * (wdt - 4), C("coal", dim=True))
            self.put(y + 2 + i, x + 2, bullet, C(col, dim=True))
            self.put(y + 2 + i, x + 4, cut(msg, wdt - 6), C(col))
        self.put(y + hgt - 2, x + 3, "esc to close", C("faint"))

    def draw_glossary(self):
        rows = [
            ("Taunt", "Enemies must attack this minion first."),
            ("Charge", "Can attack the turn it is summoned."),
            ("Rush", "Attacks minions at once, but never heroes."),
            ("Windfury", "Attacks twice per turn."),
            ("Divine Shield", "Absorbs the first damage it takes."),
            ("Poisonous", "Destroys any minion it damages."),
            ("Battlecry", "Triggers when the card is played."),
            ("Deathrattle", "Triggers when the minion dies."),
            ("Combo", "Bonus if you already played a card this turn."),
            ("Lifesteal", "Damage dealt also heals your hero."),
            ("Mana", "Grows by one each turn, up to 8."),
            ("Board", "Five minions per side; one attack per turn."),
        ]
        wdt = min(78, self.w - 6)
        hgt = len(rows) + 5
        y, x = self.overlay_box(hgt, wdt, "KEYWORDS")
        for i, (name, desc) in enumerate(rows):
            self.put(y + 2 + i, x + 2, name, C("gold", bold=True))
            self.put(y + 2 + i, x + 17, cut(desc, wdt - 20), C("text"))
        self.put(y + hgt - 2, x + 3, "esc to close", C("faint"))

    def draw_potions(self):
        pots = self.run.potions
        wdt = min(64, self.w - 8)
        hgt = 7 + len(pots)
        y, x = self.overlay_box(hgt, wdt, "POTIONS")
        if not pots:
            self.put(y + 2, x + 3, "Your belt is empty.", C("dim"))
        for i, pid in enumerate(pots):
            p = POTIONS[pid]
            sel = i == self.pot_sel
            self.put(y + 2 + i * 2, x + 2, GL["flask"],
                     C(p["color"], bold=True))
            self.put(y + 2 + i * 2, x + 4,
                     (GL["arrow"] + " " + p["name"]) if sel else ("  " + p["name"]),
                     C(p["color"], bold=True) if sel else C("text"))
            self.put(y + 2 + i * 2, x + 26, cut(p["desc"], wdt - 28), C("dim"))
            self.hot_add(x + 2, y + 2 + i * 2, wdt - 4, 1, ("potion", i))
        self.put(y + hgt - 2, x + 3, "arrows choose   enter drink   esc close",
                 C("faint"))

    def draw_confirm(self):
        text, _ = self.confirm
        wdt = 56
        hgt = 9
        y, x = self.overlay_box(hgt, wdt, "ARE YOU SURE?")
        for i, line in enumerate(wrap(text, wdt - 8)):
            self.put(y + 2 + i, x + (wdt - len(line)) // 2, line, C("text"))
        for i, lab in enumerate(["Yes, abandon", "No, keep playing"]):
            sel = i == self.confirm_sel
            self.put(y + 5 + i, x + 5,
                     (GL["arrow"] + " " + lab) if sel else ("  " + lab),
                     C("red" if i == 0 else "gold", bold=True) if sel else C("text"))
            self.hot_add(x + 4, y + 5 + i, wdt - 8, 1, ("confirm", i))
        self.put(y + hgt - 2, x + 3, "y / n   or arrows + enter", C("faint"))

    def draw_relics(self):
        wdt = min(96, self.w - 6)
        hgt = min(self.h - 2, 6 + len(self.run.relics))
        y, x = self.overlay_box(hgt, wdt, "RELICS")
        for i, rid in enumerate(self.run.relics[:hgt - 4]):
            rl = RELICS[rid]
            self.put(y + 2 + i, x + 2, f"[{rl['tag']}]", C("gold", bold=True))
            self.put(y + 2 + i, x + 7, cut(rl["name"], 20),
                     C(rl["color"], bold=True))
            self.put(y + 2 + i, x + 27, cut(rl["desc"], wdt - 30), C("dim"))
        self.put(y + hgt - 2, x + 3, "esc to close", C("faint"))
        self.hot_add(x, y, wdt, hgt, ("close",))

    def draw_pause(self):
        wdt = 46
        hgt = 15
        y, x = self.overlay_box(hgt, wdt, "PAUSED")
        items = [("Resume", GL["arrow"]), ("Deck", GL["sword"]),
                 ("Relics", GL["star"]), ("How to play", "?"),
                 ("Settings", "*"), ("Save and quit", GL["tick"]),
                 ("Abandon run", GL["skull"])]
        for i, (it, icon) in enumerate(items):
            sel = i == self.menu
            if sel:
                self.put(y + 2 + i, x + 2, " " * (wdt - 4),
                         C(self.accent(), rev=True))
            self.put(y + 2 + i, x + 4, icon,
                     C("gold" if sel else "faint", bold=sel))
            self.put(y + 2 + i, x + 6,
                     (GL["arrow"] + " " + it) if sel else ("  " + it),
                     C("white" if sel else "text", bold=sel))
            self.hot_add(x + 3, y + 2 + i, wdt - 6, 1, ("pause", i))
        if self.run is not None:
            self.put(y + 10, x + 3,
                     f"{CLASSES[self.run.cls]['name']}  \u00b7  "
                     f"Act {ROMAN[self.run.act]}  \u00b7  floor "
                     f"{min(self.run.floor + 1, self.run.floors)}/"
                     f"{self.run.floors}  \u00b7  "
                     f"{self.run.stats.get('kills', 0)} kills", C("dim"))
            self.put(y + 11, x + 3, f"seed {self.run.seed}", C("faint"))
        self.put(y + hgt - 2, x + 3, "esc resume", C("faint"))

    def open_picker(self, mode, cb, title):
        self.picker = dict(mode=mode, sel=self.first_valid(mode), title=title,
                           valid=(lambda i: can_upgrade(self.run.deck[i]))
                           if mode == "upgrade" else (lambda i: True))
        self.picker["on_pick"] = cb
        self.overlay = "picker"
        self.menu = 0

    def pick_move(self, step):
        n = len(self.run.deck)
        valid = self.picker["valid"]
        i = self.picker["sel"]
        for _ in range(n):
            i = (i + step) % n
            if valid(i):
                self.picker["sel"] = i
                return

    def first_valid(self, mode):
        for i, c in enumerate(self.run.deck):
            if mode != "upgrade" or can_upgrade(c):
                return i
        return 0

    def key_overlay(self, ch):
        if self.overlay == "carddetail":
            self.overlay = None
            return
        if self.overlay == "deck":
            if ch in (27, 10, 13, curses.KEY_ENTER, ord(" "), ord("d")):
                self.overlay = None
            elif ch in (ord("s"), ord("S")):
                self.deck_sort = not self.deck_sort
        elif self.overlay == "relics":
            if ch in (27, 10, 13, curses.KEY_ENTER, ord(" "), ord("r")):
                self.overlay = None
        elif self.overlay == "pause":
            if ch == 27:
                self.overlay = None
            elif ch in UP_KEYS:
                self.menu = (self.menu - 1) % 7
            elif ch in DOWN_KEYS:
                self.menu = (self.menu + 1) % 7
            elif is_enter(ch) or ch == ord(" "):
                if self.menu == 0:
                    self.overlay = None
                elif self.menu == 1:
                    self.overlay = "deck"
                elif self.menu == 2:
                    self.overlay = "relics"
                elif self.menu == 3:
                    self.overlay = None
                    self.help_from = self.state
                    self.state = "help"
                elif self.menu == 4:
                    self.overlay = None
                    self.pause_state = self.state
                    self.settings_from_pause = True
                    self.settings_sel = 0
                    self.state = "settings"
                elif self.menu == 5:
                    self.save_progress()
                    self.overlay = None
                    self.state = "title"
                    self.menu = 0
                    self.toast = ("Run saved.", time.monotonic() + 2.0)
                elif self.menu == 6:
                    self.confirm = ("Abandon this run and return to the "
                                    "title? Your deck will be lost.", None)
                    self.confirm_sel = 1
                    self.overlay = "confirm"
        elif self.overlay == "confirm":
            if ch in (27, ord("n"), ord("N")):
                self.overlay = "pause"
            elif ch in (ord("y"), ord("Y")):
                self.overlay = None
                self.finish_run(False)
            elif ch in UP_KEYS or ch in DOWN_KEYS:
                self.confirm_sel = 1 - self.confirm_sel
            elif is_enter(ch) or ch == ord(" "):
                if self.confirm_sel == 0:
                    self.overlay = None
                    self.finish_run(False)
                else:
                    self.overlay = "pause"
        elif self.overlay == "log":
            if ch in (27, 10, 13, curses.KEY_ENTER, ord(" "), ord("L")):
                self.overlay = None
        elif self.overlay == "glossary":
            if ch in (27, 10, 13, curses.KEY_ENTER, ord(" "), ord("?")):
                self.overlay = None
        elif self.overlay == "potions":
            if ch in (27, ord("q"), ord("Q")):
                self.overlay = None
            elif ch in UP_KEYS or ch in LEFT_KEYS:
                if self.run.potions:
                    self.pot_sel = (self.pot_sel - 1) % len(self.run.potions)
            elif ch in DOWN_KEYS or ch in RIGHT_KEYS:
                if self.run.potions:
                    self.pot_sel = (self.pot_sel + 1) % len(self.run.potions)
            elif is_enter(ch) or ch == ord(" "):
                if self.run.potions:
                    if self.cb and self.cb.use_potion(
                            self.run.potions[self.pot_sel], self.enemy_target()):
                        self.run.potions.pop(self.pot_sel)
                        self.overlay = None
                        life = self.best["lifetime"]
                        life["potions"] += 1
                        self.save_meta()
                        if life["potions"] >= 10:
                            self.unlock("potion_user")
                    elif not self.cb:
                        self.overlay = None
            elif ord("1") <= ch <= ord("3"):
                idx = ch - ord("1")
                if idx < len(self.run.potions):
                    self.pot_sel = idx
                    if self.cb and self.cb.use_potion(
                            self.run.potions[idx], self.enemy_target()):
                        self.run.potions.pop(idx)
                        self.overlay = None
                        life = self.best["lifetime"]
                        life["potions"] += 1
                        self.save_meta()
                        if life["potions"] >= 10:
                            self.unlock("potion_user")
        elif self.overlay == "picker":
            n = len(self.run.deck)
            if n == 0:
                self.overlay = None
                return
            if ch in UP_KEYS or ch in LEFT_KEYS:
                self.pick_move(-1)
            elif ch in DOWN_KEYS or ch in RIGHT_KEYS:
                self.pick_move(1)
            elif is_enter(ch) or ch == ord(" "):
                idx = self.picker["sel"]
                if self.picker["valid"](idx):
                    fn = self.picker["on_pick"]
                    self.overlay = None
                    fn(idx)
            elif ch == 27:
                self.overlay = None
                if self.state == "rest":
                    self.rest_msg = None

    # -- node entry --------------------------------------------------------
    def start_node(self, kind):
        r = self.run
        self.overlay = None
        if kind in ("monster", "elite", "boss"):
            hero = enemy_for(r, kind, r.rng)
            self.disp_hp.clear()
            self.cb = BoardCombat(r, hero, kind, r.rng)
            if kind == "boss":
                self.notify(f"{hero['name']} blocks the way.", 3.0)
            else:
                self.tip("combat")
            self.sel = 0
            self.bsel = 0
            self.esel = 0
            self.row = 0
            self.win_at = None
            self.lose_at = None
            self.card_tip_until = time.monotonic() + 3.0
            self.tip_pinned = True
            self.anim_next = time.monotonic() + 0.3
            self.state = "combat"
        elif kind == "rest":
            self.rest_sel = 0
            self.rest_msg = None
            self.tip("rest")
            self.state = "rest"
        elif kind == "shop":
            r.open_shop()
            self.shop_sel = 0
            self.shop_msg = ""
            self.tip("shop")
            self.see("cards", [c["cid"] for c in r.shop["cards"]])
            self.see("potions", [p["pid"] for p in r.shop["potions"]])
            if r.shop["relic"]:
                self.see("relics", [r.shop["relic"]])
            self.state = "shop"
        elif kind == "event":
            self.event = r.roll_event()
            self.event_stage = 0
            self.event_msg = ""
            self.state = "event"
        elif kind == "treasure":
            rng = r.rng
            gold = rng.randint(30, 55)
            r.gold += gold
            lines = [f"+{gold} gold"]
            rid = r.random_relic()
            self.treasure_desc = ""
            if rid:
                r.add_relic(rid)
                lines.append(f"relic: {RELICS[rid]['name']}")
                self.treasure_desc = RELICS[rid]["desc"]
            else:
                r.gold += 40
                lines.append("+40 gold")
            self.treasure_lines = lines
            self.state = "treasure"

    def handle(self, ch):
        if ch == curses.KEY_RESIZE:
            return
        if ch == curses.KEY_MOUSE:
            self.on_mouse()
            return
        if self.overlay and self.state not in ("title", "help", "victory",
                                              "gameover"):
            self.key_overlay(ch)
            return
        if self.state == "help":
            if ch in (27, 10, 13, curses.KEY_ENTER, ord(" ")):
                self.state = self.help_from if self.help_from != "help" else "title"
                if self.state == "title":
                    self.menu = 0
            return
        if self.state == "title":
            items = self.title_items()
            if ch in UP_KEYS:
                self.menu = (self.menu - 1) % len(items)
            elif ch in DOWN_KEYS:
                self.menu = (self.menu + 1) % len(items)
            elif ch == ord("s") or ch == ord("S"):
                self.seed_buf = ""
                self.state = "seed"
            elif is_enter(ch) or ch == ord(" "):
                label = items[self.menu % len(items)]
                if label.startswith("CONTINUE"):
                    self.continue_run()
                elif label.startswith("BEGIN"):
                    self.choose_class(0, None, False)
                elif label.startswith("ASCEND"):
                    self.choose_class(max(1, self.best.get("asc", 1)),
                                      None, False)
                elif label.startswith("HOW"):
                    self.help_from = "title"
                    self.state = "help"
                elif label.startswith("DAILY"):
                    self.choose_class(0, self.daily_seed(), True)
                elif label.startswith("CODEX"):
                    self.codex_tab = 0
                    self.codex_sel = 0
                    self.codex_scroll = 0
                    self.state = "codex"
                elif label.startswith("SETTINGS"):
                    self.settings_sel = 0
                    self.state = "settings"
                elif label.startswith("RUN"):
                    self.state = "history"
                else:
                    self.state = "quit"
            elif ch == 27:
                self.state = "quit"
            return
        if self.state == "settings":
            self.key_settings(ch)
            return
        if self.state == "history":
            if ch in (27, 10, 13, curses.KEY_ENTER, ord(" ")):
                self.state = "title"
            return
        if self.state == "seed":
            self.key_seed(ch)
            return
        if self.state == "codex":
            self.key_codex(ch)
            return
        if self.state == "class":
            self.key_class(ch)
            return
        if self.state in ("victory", "gameover"):
            self.key_end(ch)
            return
        if self.state == "combat":
            self.key_combat(ch)
        elif self.state == "map":
            self.key_map(ch)
        elif self.state == "reward":
            self.key_reward(ch)
        elif self.state == "interlude":
            self.key_interlude(ch)
        elif self.state == "heart":
            self.key_heart(ch)
        elif self.state == "rest":
            self.key_rest(ch)
        elif self.state == "rest_result":
            self.key_rest_result(ch)
        elif self.state == "shop":
            self.key_shop(ch)
        elif self.state == "event":
            self.key_event(ch)
        elif self.state == "treasure":
            self.key_treasure(ch)

    def daily_seed(self):
        return int(time.strftime("%Y%m%d"))

    def new_run(self, asc=0, seed=None, daily=False, cls="warden"):
        if seed is None:
            seed = self.rng.randint(1, 10 ** 9)
        clear_run()
        self.saved = False
        self.run = Run(seed, cls)
        self.run.ascension = asc
        self.run.daily = daily
        self.daily = daily
        self.act_banner_text = ""
        self.cb = None
        self.path = []
        self.sel = 0
        self.tgt = 0
        self.map_sel = 0
        self.overlay = None
        self.state = "map"
        self.see("cards", [c["id"] for c in self.run.deck])
        self.see("relics", list(self.run.relics))
        self.tip("map")
        self.notify("The spire waits. Choose your path.", 3.0)


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(
        prog="cinderspire",
        description="A deckbuilding roguelike for the terminal.")
    parser.add_argument("--version", action="version",
                        version=f"cinderspire {__version__}")
    parser.add_argument("--seed", type=int, default=None,
                        help="start a run with a fixed seed")
    parser.add_argument("--reset", action="store_true",
                        help="delete saves and exit")
    args = parser.parse_args(argv)
    if args.reset:
        clear_run()
        for p in (SAVE_PATH, SAVE_PATH + ".bak", SAVE_PATH + ".tmp"):
            try:
                os.remove(p)
            except OSError:
                pass
        print("CINDERSPIRE saves cleared.")
        return

    os.environ.setdefault("ESCDELAY", "25")
    try:
        sys.stdout.write("\x1b]0;CINDERSPIRE\x07")
        sys.stdout.flush()
    except Exception:
        pass

    game = None

    def _run(scr):
        nonlocal game
        init_colors()
        game = Game(scr)
        if args.seed is not None:
            game.new_run(0, seed=args.seed)
        game.loop()

    try:
        curses.wrapper(_run)
    except Exception:
        tb = traceback.format_exc()
        seed = None
        try:
            if game is not None:
                if game.run is not None:
                    seed = game.run.seed
                game.save_progress()
                game.save_meta()
        except Exception:
            pass
        log = os.path.join(DATA_DIR, "crash.log")
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(log, "a") as f:
                f.write(f"\n--- {time.strftime('%Y-%m-%d %H:%M:%S')} "
                        f"seed={seed} ---\n{tb}")
        except Exception:
            log = "(could not write log)"
        print("CINDERSPIRE hit an error. Your run was saved at the last map.")
        print(f"Crash log: {log}")
        print()
        print(tb)
        raise SystemExit(1)
    finally:
        try:
            sys.stdout.write("\x1b]0;\x07")
            sys.stdout.flush()
        except Exception:
            pass
