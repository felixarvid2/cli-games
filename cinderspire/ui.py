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
)
if not UTF:
    GL = dict(
        tl="+", tr="+", bl="+", br="+", h="-", v="|",
        lt="+", rt="+", full="#", empty="-", arrow=">", down="v",
        dot="*", ring="o", sep=".", ell=">", up="^", dl="+", dr="+",
        ul="+", ur="+", dh="=", dv="|", cross="+", tick="x", skull="X",
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
}
BASIC = {
    "text": curses.COLOR_WHITE, "dim": curses.COLOR_WHITE,
    "faint": curses.COLOR_BLACK, "white": curses.COLOR_WHITE,
    "red": curses.COLOR_RED, "orange": curses.COLOR_YELLOW,
    "gold": curses.COLOR_YELLOW, "green": curses.COLOR_GREEN,
    "teal": curses.COLOR_CYAN, "blue": curses.COLOR_BLUE,
    "purple": curses.COLOR_MAGENTA, "pink": curses.COLOR_MAGENTA,
    "cyan": curses.COLOR_CYAN, "ember": curses.COLOR_RED,
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

    def rule(self, y, attr=None, ch=None):
        ch = ch or GL["h"]
        self.put(y, 0, ch * self.w, attr if attr is not None else C("faint"))

    def bar(self, y, x, width, cur, mx, color="red"):
        frac = 0 if mx <= 0 else max(0.0, min(1.0, cur / mx))
        filled = int(round(width * frac))
        self.put(y, x, GL["full"] * filled, C(color))
        self.put(y, x + filled, GL["empty"] * (width - filled), C("faint"))

    def box(self, y, x, h, w, attr, double=False, title=None, tattr=None):
        if h < 2 or w < 2:
            return
        tl, tr, bl, br = ((GL["dl"], GL["dr"], GL["ul"], GL["ur"]) if double
                          else (GL["tl"], GL["tr"], GL["bl"], GL["br"]))
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
        if self.state == "title":
            for e in self.embers:
                e[1] -= dt * e[3]
                e[0] += math.sin(self.t * 0.7 + e[1]) * dt * 3
                if e[1] < 1:
                    e[1] = self.h - 1
                    e[0] = self.rng.uniform(0, self.w)
        if self.cb:
            for f in [self.cb.player] + self.cb.enemies:
                cur = self.disp_hp.get(id(f))
                if cur is None:
                    self.disp_hp[id(f)] = float(f.hp)
                elif abs(cur - f.hp) > 0.05:
                    step = max(18.0, f.max_hp * 2.0) * dt
                    self.disp_hp[id(f)] = (cur - min(step, cur - f.hp)
                                           if cur > f.hp else
                                           cur + min(step, f.hp - cur))
                else:
                    self.disp_hp[id(f)] = float(f.hp)
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

    def draw_resize(self):
        msg = "Please resize the terminal"
        need = f"needs at least 78 x 24  (now {self.w} x {self.h})"
        self.center(max(0, self.h // 2 - 1), msg, C("red", bold=True))
        self.center(max(0, self.h // 2), need, C("dim"))

    # ------------------------------------------------------------- header --
    def draw_header(self, subtitle=None, boss_label=True):
        r = self.run
        self.put(0, 2, "CINDERSPIRE", C("gold", bold=True))
        if subtitle:
            self.put(0, 15, GL["sep"], C("faint"))
            self.put(0, 17, subtitle.upper(), C("dim"))
        if r:
            if r.floor >= r.floors and boss_label:
                s = ENEMIES[BOSSES[r.act][0]]["name"].upper()
                self.put(0, self.w - 2 - len(s), s, C("red", bold=True))
            else:
                s = (f"ACT {ROMAN[r.act]}  {GL['sep']}  "
                     f"FLOOR {min(r.floor + 1, r.floors)}/{r.floors}")
                if r.daily:
                    s += "  \u00b7  DAILY"
                if r.ascension:
                    s = f"A{r.ascension}  " + s
                self.put(0, self.w - 2 - len(s), s, C("dim"))
            self.put(1, 2, "HP", C("red", bold=True))
            self.bar(1, 5, 16, r.hp, r.max_hp)
            self.put(1, 22, f"{r.hp}/{r.max_hp}", C("text"))
            if r.gold != self.gold_seen:
                self.gold_seen = r.gold
                self.gold_flash_until = time.monotonic() + 0.7
            flash = time.monotonic() < self.gold_flash_until
            self.put(1, 32, "GOLD", C("gold", bold=True))
            shown = int(round(self.gold_disp)) if self.gold_disp else r.gold
            self.put(1, 37, str(shown),
                     C("white", bold=True) if flash else C("gold"))
            self.put(1, 47, "DECK", C("dim"))
            self.put(1, 52, str(len(r.deck)), C("text"))
            tags = " ".join(RELICS[x]["tag"] for x in r.relics)
            if tags:
                self.put(1, max(56, self.w - 2 - len(tags)), cut(tags, 24),
                         C("gold", dim=True))

    def hint(self, text):
        self.put(self.h - 1, 2, cut(text, self.w - 4), C("faint"))

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
        for e in self.embers:
            x, y = int(e[0]), int(e[1])
            if 0 <= y < self.h:
                col = "ember" if int(e[1]) % 3 else "orange"
                self.put(y, x, e[2], C(col, dim=True))
        art = banner("CINDERSPIRE")
        y0 = max(2, self.h // 2 - 8)
        colors = ["ember", "red", "orange", "gold", "gold"]
        for i, line in enumerate(art):
            self.center(y0 + i, line, C(colors[i], bold=True))
        sub = "A   D E C K B U I L D I N G   R O G U E L I K E"
        self.center(y0 + 6, sub, C("dim"))
        self.center(y0 + 7, GL["h"] * 34, C("faint"))
        items = self.title_items()
        self.menu_items = items
        for i, it in enumerate(items):
            y = y0 + 8 + i
            sel = i == self.menu
            label = (GL["arrow"] + "  " + it + "  " + GL["arrow"]) if sel else it
            attr = C("gold", bold=True) if sel else C("dim")
            self.center(y, label, attr)
        if self.best.get("best"):
            s = f"BEST RUN  {self.best['best']}   ·   WINS {self.best.get('wins', 0)}"
            self.center(self.h - 3, s, C("dim"))
        self.put(self.h - 1, self.w - 8, "v1.0", C("faint"))
        self.center(self.h - 1, "arrows to choose  ·  enter to confirm",
                    C("faint"))

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
        self.put(0, 2, "CINDERSPIRE", C("gold", bold=True))
        self.put(0, 15, GL["sep"], C("faint"))
        self.put(0, 17, "SETTINGS", C("dim"))
        wdt = min(64, self.w - 8)
        hgt = 17
        y, x = self.overlay_box(hgt, wdt, "SETTINGS")
        anim = "fast" if self.anim < 0.6 else ("slow" if self.anim > 1.4 else "normal")
        rows = [("Animation speed", anim),
                ("Confirm end turn", "on" if self.settings.get("confirm_end") else "off"),
                ("Flash effects", "on" if self.settings.get("flash") else "off"),
                ("Screen shake", "on" if self.settings.get("shake", True) else "off"),
                ("Hints", "on" if self.settings.get("hints", True) else "off")]
        for i, (label, val) in enumerate(rows):
            sel = i == self.settings_sel
            self.put(y + 2 + i * 2, x + 3,
                     (GL["arrow"] + " " + label) if sel else ("  " + label),
                     C("gold", bold=True) if sel else C("text"))
            self.put(y + 2 + i * 2, x + wdt - 10, f"< {val} >", C("dim"))
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
            order = {"attack": 0, "skill": 1, "power": 2}
            corder = {c: n for n, c in enumerate(self.CLASS_ORDER)}
            ids = sorted((i for i in CARDS
                          if CARDS[i]["rarity"] not in ("status", "token")),
                         key=lambda i: (corder.get(CARDS[i].get("cls"), 9),
                                        order.get(CARDS[i]["type"], 3),
                                        CARDS[i]["cost"], CARDS[i]["name"]))
            return [dict(key=i, name=CARDS[i]["name"],
                         short=(f"{'X' if CARDS[i]['cost'] < 0 else CARDS[i]['cost']}"
                                f" {CARDS[i]['type'][0].upper()}")
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
            return [dict(key=i, name=ENEMIES[i]["name"],
                         short=("BOSS" if ENEMIES[i].get("ai") == "boss"
                                else "MOB") if i in seen["enemies"] else "",
                         seen=i in seen["enemies"])
                    for i in sorted(ENEMIES, key=lambda e: ENEMIES[e]["name"])]
        return [dict(key=i, name=ACHIEVEMENTS[i]["name"], short="",
                     seen=i in self.best["achievements"])
                for i in sorted(ACHIEVEMENTS, key=lambda a: ACHIEVEMENTS[a]["name"])]

    def codex_totals(self):
        seen = self.best["seen"]
        codex_cards = sum(1 for c in CARDS.values()
                          if c["rarity"] not in ("status", "token"))
        return [(len(seen["cards"]), codex_cards),
                (len(seen["relics"]), len(RELICS)),
                (len(seen["potions"]), len(POTIONS)),
                (len(seen["enemies"]), len(ENEMIES)),
                (len(self.best["achievements"]), len(ACHIEVEMENTS))]

    def codex_detail(self, e, width):
        tab = self.codex_tab
        if not e["seen"]:
            return ["Not discovered yet.", "",
                    "Find it in the spire to unlock this entry."]
        if tab == 0:
            c = CARDS[e["key"]]
            up = cdata({"id": e["key"], "up": 1})
            cname = CLASSES.get(c.get("cls"), {}).get("name", "Shared")
            lines = [f"{c['type'].title()}  \u00b7  {c['rarity'].title()}",
                     f"{cname}  \u00b7  Cost {c['cost']}"
                     + ("   (X)" if c["cost"] < 0 else ""), ""]
            lines += wrap(ctext(cdata({"id": e["key"], "up": 0})), width)
            lines += ["", "Upgraded:"]
            lines += wrap(ctext(up), width)
            return lines
        if tab == 1:
            r = RELICS[e["key"]]
            return [("Ember boon" if r.get("boss") else "Relic"), ""] + \
                wrap(r["desc"], width)
        if tab == 2:
            return [POTIONS[e["key"]]["name"], ""] + \
                wrap(POTIONS[e["key"]]["desc"], width)
        if tab == 3:
            d = ENEMIES[e["key"]]
            lines = [f"HP {d['hp'][0]}-{d['hp'][1]}",
                     "Keeper" if d.get("ai") == "boss" else "Enemy", "", "Moves:"]
            for m in d["moves"]:
                dmg = ""
                if m["dmg"]:
                    dmg = f"  {m['dmg']}" + (f"x{m['hits']}" if m["hits"] > 1 else "")
                lines.append(f"  {m['name']}{dmg}")
            return lines
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
        # tabs
        x = 3
        for i, name in enumerate(tabs):
            active = i == self.codex_tab
            self.put(2, x, name, C("gold", bold=True) if active else C("faint"))
            x += len(name) + 3
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
            self.put(y, 4, cut(name, bw - 16), attr)
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
        self.put(0, 2, "CINDERSPIRE", C("gold", bold=True))
        self.put(0, 15, GL["sep"], C("faint"))
        self.put(0, 17, "RUN HISTORY", C("dim"))
        hist = list(self.best.get("history", []))[:5]
        wdt = min(74, self.w - 8)
        hgt = 7 + len(hist) * 2
        y, x = self.overlay_box(min(hgt, self.h - 4), wdt, "LAST RUNS")
        if not hist:
            self.put(y + 2, x + 3, "No runs yet.", C("dim"))
        for i, h in enumerate(hist):
            yy = y + 2 + i * 2
            if yy > y + hgt - 3:
                break
            tag = "WIN " if h.get("won") else "DIED"
            col = "green" if h.get("won") else "red"
            self.put(yy, x + 3, tag, C(col, bold=True))
            self.put(yy, x + 9, f"Act {ROMAN[min(h.get('act', 0), 2)]}"
                     f"  floor {h.get('floor', 0)}/21", C("text"))
            self.put(yy, x + 34, f"score {h.get('score', 0)}", C("gold"))
            self.put(yy, x + 52, str(h.get("when", "")), C("faint"))
        self.put(y + min(hgt, self.h - 4) - 2, x + 3, "esc back", C("faint"))

    CLASS_ORDER = ["warden", "ashblade", "emberwright", "pilgrim", "paladin"]

    def choose_class(self, asc=0, seed=None, daily=False):
        self.pending = dict(asc=asc, seed=seed, daily=daily)
        self.class_sel = 0
        self.state = "class"

    def draw_class(self):
        self.put(0, 2, "CINDERSPIRE", C("gold", bold=True))
        self.put(0, 15, GL["sep"], C("faint"))
        self.put(0, 17, "NEW RUN", C("dim"))
        self.center(2, "CHOOSE YOUR PATH", C("gold", bold=True))
        for i, cid in enumerate(self.CLASS_ORDER):
            meta = CLASSES[cid]
            y = 4 + i * 3
            sel = i == self.class_sel
            name = meta["name"].upper()
            if sel:
                self.put(y, 6, " " * (self.w - 12), C("blue", rev=True))
                self.put(y, 8, GL["arrow"] + " " + name,
                         C(meta["color"], bold=True))
            else:
                self.put(y, 10, name, C(meta["color"]))
            n = sum(1 for c in CARDS.values()
                    if c.get("cls") == cid
                    and c["rarity"] not in ("status", "token"))
            self.put(y, self.w - 12, f"{n} cards", C("faint"))
            starter = CARDS[meta["starter"]]["name"]
            self.put(y + 1, 10, cut(meta["detail"], self.w - 24),
                     C("text" if sel else "dim"))
            self.put(y + 2, 10, f"starts with {starter}", C("faint"))
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
        self.put(0, 2, "CINDERSPIRE", C("gold", bold=True))
        self.put(0, 15, GL["sep"], C("faint"))
        self.put(0, 17, "NEW RUN", C("dim"))
        wdt = 52
        hgt = 8
        y, x = self.overlay_box(hgt, wdt, "ENTER A SEED")
        self.put(y + 2, x + (wdt - 22) // 2, "seed:", C("dim"))
        val = (self.seed_buf or "random") + "_"
        self.put(y + 3, x + (wdt - len(val)) // 2, val, C("gold", bold=True))
        self.put(y + hgt - 2, x + 3, "digits   enter start   esc back",
                 C("faint"))

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
        self.put(0, 2, "CINDERSPIRE", C("gold", bold=True))
        self.put(0, 15, GL["sep"], C("faint"))
        self.put(0, 17, "HOW TO PLAY", C("dim"))
        bw = min(80, self.w - 6)
        bx = (self.w - bw) // 2
        by = 3
        bh = 17
        self.box(by, bx, bh, bw, C("gold", dim=True))
        self.put(by + 1, bx + (bw - 12) // 2, "THE BASICS", C("gold", bold=True))
        rows = [
            ("GOAL", "Climb three acts, seven floors each, and defeat"),
            ("", "the three keepers. Claim an ember boon after each one."),
            ("COMBAT", "3 Energy and 5 cards each turn. Block resets"),
            ("", "every turn. Press E to end your turn."),
            ("INTENT", "The line above each enemy is its next move."),
            ("", "Block before the hit, not after."),
            ("STATUS", "Vulnerable: +50% damage taken.  Weak: -25%"),
            ("", "damage dealt.  Poison and Thorns tick by themselves."),
            ("DECK", "Take a new card after each fight, upgrade at"),
            ("", "campfires, cut dead weight at shops."),
            ("MAP", "M mob  E elite  ? event  R rest  $ shop  T loot"),
            ("KEYS", "1-9 play   arrows select   TAB target   Q potion"),
            ("", "E end turn   D deck   R relics   ESC menu"),
        ]
        y = by + 3
        for tag, text in rows:
            if tag:
                self.put(y, bx + 4, tag, C("gold", bold=True))
            self.put(y, bx + 13, text, C("text") if tag else C("dim"))
            y += 1
        self.center(self.h - 1, "press enter to return", C("faint"))

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
        self.draw_header(ACT_NAMES[r.act])
        self.rule(2)
        # connectors
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
        # nodes
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
                label = f"[{meta['label']}]"
                if here:
                    attr = C("white", bold=True)
                elif can:
                    pulse = int(self.t * 2.5) % 2 == 0
                    attr = C(meta["color"], bold=True, rev=pulse)
                elif visited:
                    attr = C("faint")
                else:
                    attr = C(meta["color"], dim=visited)
                self.put(y, x - 1, label, attr)
                if here:
                    self.put(y, x - 3, GL["tick"], C("green", bold=True))
                if can and avail.index(lane) == self.map_sel % max(1, len(avail)):
                    self.put(y, x - 3, GL["arrow"], C("gold", bold=True))
        # boss
        by = self.row_y(r.floors)
        boss_avail = r.floor >= r.floors
        battr = C("red", bold=True, rev=boss_avail)
        if not boss_avail:
            battr = C("red", bold=True, dim=True)
        self.put(by, boss_x - 1, "[B]", battr)
        if boss_avail:
            self.put(by, boss_x - 3, GL["arrow"], C("gold", bold=True))
        bname = ENEMIES[BOSSES[r.act][0]]["name"].upper()
        self.put(by + 1, boss_x - len(bname) // 2, bname, C("red", dim=True))
        # side panel
        px = self.w - 17
        self.put(3, px, "RELICS", C("gold", bold=True))
        for i, rid in enumerate(self.run.relics[:9]):
            self.put(4 + i, px, cut(RELICS[rid]["name"], 16),
                     C(RELICS[rid]["color"]))
        if len(self.run.relics) > 9:
            self.put(4 + 9, px, f"+{len(self.run.relics) - 9} more", C("dim"))
        if self.run.potions:
            self.put(18, px, "POTIONS", C("dim", bold=True))
            for i, pid in enumerate(self.run.potions):
                pm = POTIONS[pid]
                self.put(19 + i, px, cut(pm["name"], 16), C(pm["color"]))
        for i, leg in enumerate(["M mob    E elite", "? event  R rest",
                                 "$ shop   T loot"]):
            self.put(14 + i, px, leg, C("faint"))
        if self.act_banner_until > time.monotonic() and self.act_banner_text:
            msg = f"{self.act_banner_text}  \u00b7  {ACT_NAMES[r.act]}"
            self.center(21, msg, C("gold", bold=True))
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
    def draw_combat(self):
        cb = self.cb
        self.draw_header("combat" if cb.kind == "normal" else cb.kind)
        self.rule(2)
        self.draw_arena(cb)
        cards_y, header_y, rule_y, log1, log2, _ = self.layout()
        low = cb.player.hp <= cb.player.max_hp * 0.25
        if low and int(self.t * 3) % 2 == 0:
            self.rule(rule_y, C("red", dim=True))
        else:
            self.rule(rule_y)
        for i, (msg, col) in enumerate(cb.logs[-2:]):
            att = C("gold", bold=True) if msg.startswith("-- Turn") else C(col)
            self.put(log1 + i, 2, cut(msg, self.w - 4), att)
        self.draw_hand(cb)
        self.hint("1-9 play  \u2190\u2192  TAB target  E end  Q potion  "
                  "L log  ? help  ESC")

    def draw_arena(self, cb):
        top = 3
        _, _, _, _, _, bottom = self.layout()
        if bottom - top < 7:
            bottom = top + 7
        n = len(cb.enemies)
        px = 0
        panel_w = 17
        arena_x = panel_w + 1
        colw = max(14, (self.w - arena_x) // max(1, n))
        block_h = 8
        top_block = top + max(0, (bottom - top + 1 - block_h) // 2)
        art_top = top_block + 1
        # player panel
        p = cb.player
        ptop = top_block
        self.put(ptop, 2, "YOU", C("white", bold=True))
        self.put(ptop, 7, f"T{cb.turn}", C("dim"))
        sprite = [" o ", "/|\\", "/ \\"]
        for i, line in enumerate(sprite):
            self.put(ptop + 1 + i, 2, line, C("white", bold=True))
        self.put(ptop + 4, 2, f"BLK {p.block}", C("blue", bold=True))
        inc = self.incoming_damage(cb)
        if inc <= 0:
            self.put(ptop + 4, 10, "IN 0", C("faint"))
        elif inc >= p.hp:
            self.put(ptop + 4, 9, f"IN {inc}!!", C("red", bold=True))
        else:
            self.put(ptop + 4, 9, f"IN {inc}", C("orange"))
        low = p.max_hp and p.hp <= p.max_hp * 0.25
        blink = low and int(self.t * 3) % 2 == 0
        self.put(ptop + 5, 2, f"{p.hp}/{p.max_hp}",
                 C("white", bold=True) if blink else C("red", bold=True))
        toks = []
        for key, lab, col in (("str", "STR", "orange"), ("dex", "DEX", "green"),
                              ("vuln", "VULN", "purple"), ("weak", "WEAK", "purple"),
                              ("regen", "REGEN", "green"), ("thorns", "THRN", "green"),
                              ("metallicize", "PLATE", "blue"),
                              ("demon", "DEMON", "red"), ("berserk", "BERSK", "red"),
                              ("juggernaut", "JUGG", "orange"),
                              ("shield", "SHLD", "gold"),
                              ("aura", "AURA", "orange"),
                              ("lightbringer", "LBR", "gold")):
            v = st(p, key)
            if v:
                toks.append((f"{lab}{v}", col))
        sx = ptop + 6
        cx = 2
        for txt, col in toks:
            if cx + len(txt) > panel_w - 1:
                sx += 1
                cx = 2
                if sx > bottom:
                    break
            self.put(sx, cx, txt, C(col))
            cx += len(txt) + 1
        pop = cb.popups.get(id(p))
        if pop:
            self.put(ptop + 1, 9, pop[0], C(pop[1], bold=True))
        # enemies
        for i, e in enumerate(cb.enemies):
            x0 = arena_x + i * colw
            cx = x0 + colw // 2
            if not e.alive:
                if cb.popups.get(id(e)):
                    self.put(top_block + 2, cx - 1, "\u2620",
                             C("red", bold=True))
                else:
                    self.put(top_block + 2, cx - 4, "· gone ·", C("faint"))
                continue
            art = e.defn["art"]
            start = art_top
            name_y = start + len(art)
            m = e.next_move
            txt, col = self.intent(m, e)
            targeted = (i == self.tgt)
            if targeted:
                txt = GL["arrow"] + " " + txt
                col = "white"
            self.put(max(top, start - 1), cx - len(txt) // 2, txt,
                     C(col, bold=True))
            sh = 0
            if id(e) in cb.shake and self.settings.get("shake", True):
                amp = 2 if cb.shake[id(e)] > 0.28 else 1
                sh = amp if int(time.monotonic() * 40) % 2 else -amp
            flashing = (id(e) in cb.flash and self.settings.get("flash", True))
            for j, line in enumerate(art):
                self.put(start + j, cx - len(line) // 2 + sh, line,
                         C(e.color, bold=True, rev=flashing))
            nattr = (C("white", bold=True) if targeted else
                     C(e.color, bold=True, dim=e.hp < e.max_hp * 0.25))
            self.put(name_y, cx - len(e.name) // 2, cut(e.name, colw - 1), nattr)
            bw = min(14, colw - 12)
            hp_y = name_y + 1
            lab = f"{e.hp}/{e.max_hp}"
            total = bw + 1 + len(lab) + (4 if e.block else 0)
            bx = cx - total // 2
            bcol = "red" if (e.max_hp < 100 or e.hp <= e.max_hp * 0.5) \
                else "orange"
            self.bar(hp_y, bx, bw, self.disp_hp.get(id(e), e.hp), e.max_hp,
                     bcol)
            for tick in range(4, bw, 4):
                self.put(hp_y, bx + tick, GL["v"], C("faint"))
            self.put(hp_y, bx + bw + 1, lab, C("text"))
            if e.block:
                self.put(hp_y, bx + bw + 2 + len(lab), f"+{e.block}",
                         C("blue"))
            bits = []
            for key, lab, c2 in (("str", "str", "orange"), ("vuln", "vuln", "purple"),
                                 ("weak", "weak", "purple"), ("poison", "psn", "green"),
                                 ("ritual", "ritual", "gold")):
                v = st(e, key)
                if v:
                    bits.append(f"{lab} {v}")
            if bits:
                s = " ".join(bits)
                self.put(name_y + 2, max(x0, cx - len(s) // 2),
                         cut(s, colw - 1), C("purple", dim=True))
            pop = cb.popups.get(id(e))
            if pop:
                self.put(min(start + 1, name_y - 1), cx + 5, pop[0],
                         C(pop[1], bold=True))

    def intent(self, m, e=None):
        if not m:
            return "---", "dim"
        if m["kind"] == "attack":
            dmg = m["dmg"]
            if e is not None:
                dmg += st(e, "str")
                if st(self.cb.player, "vuln") > 0:
                    dmg = int(dmg * 1.5)
                if st(e, "weak") > 0:
                    dmg = int(dmg * 0.75)
            s = f"ATK {dmg}"
            if m["hits"] > 1:
                s += f"x{m['hits']}"
            if m["block"]:
                s += f" +{m['block']}BLK"
            return s, "red"
        if m["kind"] == "block":
            return f"BLK {m['block']}", "blue"
        if m["kind"] == "buff":
            if m["block"]:
                return f"BUFF +{m['block']}BLK", "gold"
            return "BUFF", "gold"
        if m["kind"] == "debuff":
            return "HEX", "purple"
        return m["name"].upper()[:10], "text"

    def incoming_damage(self, cb):
        total = 0
        for e in cb.alive_enemies():
            m = e.next_move
            if not m or not m["dmg"]:
                continue
            d = m["dmg"] + st(e, "str")
            if st(cb.player, "vuln") > 0:
                d = int(d * 1.5)
            if st(e, "weak") > 0:
                d = int(d * 0.75)
            total += max(0, d) * m["hits"]
        return total

    def mod_dmg(self, cb, cd, target):
        base = cd["dmg"]
        if cd["id"] == "body_slam":
            base = cb.player.block
        dmg = base + st(cb.player, "str")
        if cb.relic("twin_fangs"):
            dmg += 2
        if target is not None and st(target, "vuln") > 0:
            dmg = int(dmg * 1.5)
        if st(cb.player, "weak") > 0:
            dmg = int(dmg * 0.75)
        if cb.relic("pen_nib") and (cb.attacks_played + 1) % 10 == 0:
            dmg *= 2
        return max(0, dmg)

    def preview(self, cb, cd):
        if cd["type"] == "attack":
            alive = cb.alive_enemies()
            tgt = self.target_obj(cb)
            if cd["target"] == "all":
                d = self.mod_dmg(cb, cd, alive[0] if alive else None)
                return f"{d} DMG ALL"
            d = self.mod_dmg(cb, cd, tgt)
            s = f"{d} DMG"
            if cd["hits"] > 1:
                s += f"x{cd['hits']}"
            if tgt is not None and cd["target"] == "enemy":
                s += f" \u2192 {cut(tgt.name, 16)}"
            return s
        if cd["block"]:
            return f"+{cd['block'] + st(cb.player, 'dex')} BLOCK"
        return ""

    def target_obj(self, cb):
        if 0 <= self.tgt < len(cb.enemies) and cb.enemies[self.tgt].alive:
            return cb.enemies[self.tgt]
        alive = cb.alive_enemies()
        return alive[0] if alive else None

    def draw_hand(self, cb):
        h = self.h
        cards_y, header_y, _, _, _, _ = self.layout()
        caret_y = h - 1
        n = len(cb.hand)
        # header
        self.put(header_y, 2, "HAND", C("dim", bold=True))
        self.put(header_y, 8, f"{len(cb.hand)}", C("text"))
        energy = cb.energy
        shown = int(round(self.energy_disp)) if self.energy_disp else energy
        ex = 16
        self.put(header_y, ex, "ENERGY", C("dim", bold=True))
        for i in range(max(3, energy, shown)):
            on = i < shown
            self.put(header_y, ex + 7 + i * 2, GL["dot"] if on else GL["ring"],
                     C("gold") if on else C("faint"))
        pots = cb.run.potions
        if pots:
            self.put(header_y, 31, "Q", C("gold", bold=True))
            for i in range(3):
                px = 33 + i * 4
                if i < len(pots):
                    pmeta = POTIONS[pots[i]]
                    self.put(header_y, px, "[" + pmeta["tag"] + "]",
                             C(pmeta["color"], bold=True))
                else:
                    self.put(header_y, px, "[ ]", C("faint"))
        if self.w >= 94:
            s = (f"DRAW {len(cb.draw_pile)}   DISCARD {len(cb.discard)}"
                 f"   EXHAUST {len(cb.exhausted)}")
        else:
            s = (f"D{len(cb.draw_pile)}  X{len(cb.discard)}"
                 f"  E{len(cb.exhausted)}")
        piles_x = self.w - 2 - len(s)
        if cb.hand:
            idx = min(self.sel, len(cb.hand) - 1)
            cd = cdata(cb.hand[idx])
            pv = self.preview(cb, cd)
            if not pv and cb.energy and not any(cb.can_play(i)
                                                for i in range(len(cb.hand))):
                pv = "no playable cards"
            if pv:
                cap = piles_x - 47
                if cap > 6:
                    self.put(header_y, 46, cut(pv, cap),
                             C("gold" if cb.can_play(idx) else "faint"))
        self.put(header_y, piles_x, s, C("dim"))
        if n == 0:
            self.center(cards_y + 3, "no cards in hand", C("faint"))
            return
        gap = 1
        if n > 6:
            show = 6
            start = min(max(0, self.sel - show // 2), n - show)
            cw = min(17, max(11, (self.w - (show - 1) * gap - 2) // show))
        else:
            show, start = n, 0
            cw = min(17, max(9, (self.w - (n - 1) * gap - 2) // n))
        self.win_start = start
        total = show * cw + (show - 1) * gap
        x0 = max(1, (self.w - total) // 2)
        for k in range(show):
            i = start + k
            c = cb.hand[i]
            cd = cdata(c)
            ok = cb.can_play(i)
            selected = i == self.sel
            self.draw_card(cards_y, x0 + k * (cw + gap), cw, cd, selected, ok)
        if start > 0:
            self.put(header_y, 30, f"\u2039 {start}", C("gold", dim=True))
        if start + show < n:
            self.put(header_y, 35, f"{n - start - show} \u203a", C("gold", dim=True))

    def draw_card(self, y, x, w, cd, selected, playable):
        col = {"attack": "red", "skill": "blue", "power": "purple"}.get(
            cd["type"], "text")
        h = 8
        if selected:
            self.box(y, x, h, w, C("white", bold=True), double=True)
        else:
            self.box(y, x, h, w, C(col, dim=not playable))
        name = cut(cd["name"], w - 5)
        if selected:
            self.put(y + 1, x + 2, name.ljust(w - 5), C("gold", bold=True, rev=True))
        else:
            self.put(y + 1, x + 2, name,
                     C(col, bold=True, dim=not playable))
        cost = "X" if cd["cost"] < 0 else str(cd["cost"])
        self.put(y + 1, x + w - 3, cost,
                 C("gold", bold=True) if playable else C("dim"))
        self.put(y + 2, x + 1,
                 (GL["dh"] if selected else GL["h"]) * (w - 2),
                 C("white" if selected else col, dim=True))
        lines = wrap(ctext(cd), w - 4)
        for i, ln in enumerate(lines[:4]):
            self.put(y + 3 + i, x + 2, cut(ln, w - 4),
                     C("text", dim=not playable))
        if len(lines) > 4:
            self.put(y + 6, x + w - 2, GL["ell"], C("dim"))

    def key_combat(self, ch):
        cb = self.cb
        if self.overlay:
            return self.key_overlay(ch)
        if cb.phase != "player":
            return
        n = len(cb.hand)
        if ch in LEFT_KEYS or ch == ord("h"):
            self.sel = (self.sel - 1) % max(1, n)
        elif ch in RIGHT_KEYS or ch == ord("l"):
            self.sel = (self.sel + 1) % max(1, n)
        elif ch in (9,):
            self.cycle_target()
        elif ch in UP_KEYS or ch == ord("k"):
            self.cycle_target(-1)
        elif ch in DOWN_KEYS or ch == ord("j"):
            self.cycle_target(1)
        elif is_enter(ch) or ch == ord(" "):
            self.play(self.sel)
        elif ord("1") <= ch <= ord("9"):
            idx = getattr(self, "win_start", 0) + (ch - ord("1"))
            if idx < n:
                self.sel = idx
                self.play(idx)
        elif ch in (ord("e"), ord("E")):
            if cb.phase == "player":
                now = time.monotonic()
                if (self.settings.get("confirm_end", True) and cb.energy > 0
                        and any(cb.can_play(i) for i in range(len(cb.hand)))
                        and now > self.confirm_end_until):
                    self.confirm_end_until = now + 2.0
                    self.toast = ("Energy left \u2014 press E again to end turn.",
                                  now + 2.0)
                    return
                cb.end_turn()
                self.anim_next = time.monotonic() + 0.30 * self.anim
                self.sel = 0
        elif ch == ord("d"):
            self.overlay = "deck"
        elif ch == ord("r"):
            self.overlay = "relics"
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

    def cycle_target(self, step=1):
        cb = self.cb
        alive = [i for i, e in enumerate(cb.enemies) if e.alive]
        if not alive:
            return
        if self.tgt not in alive:
            self.tgt = alive[0]
            return
        i = alive.index(self.tgt)
        self.tgt = alive[(i + step) % len(alive)]

    def play(self, i):
        cb = self.cb
        if not cb.can_play(i):
            return
        cd = cdata(cb.hand[i])
        if cd["target"] == "enemy" and cb.enemies:
            self.cycle_target(0)
        cb.play_card(i, self.tgt)
        self.sel = max(0, min(self.sel, len(cb.hand) - 1))

    def combat_won(self):
        cb = self.cb
        if cb is None:
            return
        kind = cb.kind
        self.run.hp = cb.player.hp
        killed = sum(1 for e in cb.enemies if not e.alive)
        self.run.stats["kills"] += killed
        self.run.stats["damage"] = (self.run.stats.get("damage", 0)
                                    + cb.damage_dealt)
        life = self.best["lifetime"]
        life["combats"] += 1
        life["kills"] += killed
        life["damage"] += cb.damage_dealt
        self.save_meta()
        self.unlock("first_blood")
        if cb.best_hit >= 50:
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
        if kind == "elite" or self.run.rng.random() < 0.38:
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
                self.box(y, x, 8, wdt, C("white", bold=True), double=True)
            else:
                self.box(y, x, 8, wdt, C(rl["color"], dim=True))
            self.put(y + 1, x + 2, f"[{rl['tag']}]", C(rl["color"], bold=True))
            self.put(y + 2, x + 2, cut(rl["name"], wdt - 4),
                     C("white", bold=True) if sel else C(rl["color"], bold=True))
            self.put(y + 3, x + 1, GL["h"] * (wdt - 2), C(rl["color"], dim=True))
            for j, line in enumerate(wrap(rl["desc"], wdt - 4)[:3]):
                self.put(y + 4 + j, x + 2, cut(line, wdt - 4), C("text"))
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
        self.center(3, "VICTORY", C("green", bold=True))
        self.center(4, "the enemies lie still", C("dim"))
        line = 5
        if rw["relic"]:
            rl = RELICS[rw["relic"]]
            self.center(line, f"relic found: {rl['name']}",
                        C(rl["color"], bold=True))
            line += 1
            self.center(line, cut(rl["desc"], self.w - 8), C("dim"))
            line += 1
        if rw.get("potion"):
            self.center(line, f"potion: {POTIONS[rw['potion']]['name']}",
                        C(POTIONS[rw["potion"]]["color"], bold=True))
            line += 1
        self.center(line + 1, "choose a card to add to your deck", C("dim"))
        n = len(rw["cards"])
        cw = 19
        gap = 2
        total = n * cw + (n - 1) * gap
        x0 = (self.w - total) // 2
        y = max(10, line + 3)
        for i, cid in enumerate(rw["cards"]):
            cd = cdata({"id": cid, "up": 0})
            self.draw_card(y, x0 + i * (cw + gap), cw, cd,
                           i == self.reward_sel, True)
        self.hint("arrows choose   enter take card   s skip")

    def key_reward(self, ch):
        n = len(self.reward["cards"])
        if ch in LEFT_KEYS:
            self.reward_sel = (self.reward_sel - 1) % n
        elif ch in RIGHT_KEYS:
            self.reward_sel = (self.reward_sel + 1) % n
        elif is_enter(ch) or ch == ord(" "):
            cid = self.reward["cards"][self.reward_sel]
            self.run.add_card(cid)
            self.toast = (f"{CARDS[cid]['name']} added to your deck.",
                          time.monotonic() + 2.0)
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
        # fire
        cx = self.w // 2
        y = 4
        flick = int(self.t * 8) % 3
        fire = [
            r"     (  .  )     ",
            r"      .-'-.      ",
            r"     /  |  \     ",
            r"    | . | . |    ",
            r"     \  |  /     ",
            r"      '-.-'      ",
        ]
        cols = ["gold", "orange", "red"]
        for i, line in enumerate(fire):
            self.put(y + i, cx - 9, line, C(cols[(i + flick) % 3], bold=True))
        self.center(y + 8, "A quiet place between the fires.", C("dim"))
        upg = sum(1 for c in self.run.deck if can_upgrade(c))
        opts = [("Rest", f"Heal {int(self.run.max_hp * 0.3)} HP"),
                ("Smith", f"Upgrade a card ({upg} available)")]
        for i, (name, desc) in enumerate(opts):
            oy = y + 10 + i * 2
            sel = i == self.rest_sel
            label = f"{GL['arrow']} {name}" if sel else f"  {name}"
            self.put(oy, cx - 18, label.ljust(9),
                     C("gold", bold=True) if sel else C("text"))
            self.put(oy, cx - 7, desc, C("dim"))
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
        self.rest_msg = (f"{cdata(self.run.deck[idx])['name']} glows with new "
                         "power.")
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
        self.draw_header("shop")
        self.rule(2)
        self.put(3, 2, "THE ASHEN MARKET", C("gold", bold=True))
        self.put(3, self.w - 20, f"YOUR GOLD  {r.gold}", C("gold"))
        rows = self.shop_rows()
        for k, (kind, idx) in enumerate(rows):
            y = 5 + k * 2
            if y > self.h - 3:
                break
            sel = k == self.shop_sel
            if kind == "card":
                item = s["cards"][idx]
                price = item["price"]
                sold = idx in s["sold"]
                data = cdata({"id": item["cid"], "up": 0})
            elif kind == "relic":
                price = s["relic_price"]
                sold = "relic" in s["sold"]
                data = RELICS[s["relic"]]
            elif kind == "potion":
                item = s["potions"][idx]
                price = item["price"]
                sold = idx in s["sold"]
                data = POTIONS[item["pid"]]
            else:
                price = s["removal"]
                sold = "removal" in s["sold"]
                data = None
            afford = r.gold >= price
            attr = C("faint") if sold else (
                C("white", bold=True) if sel else C("text"))
            mark = GL["arrow"] if sel else " "
            if kind == "potion":
                self.put(y, 2, mark, C("gold", bold=True))
                self.put(y, 4, "P", C("purple", bold=True))
                self.put(y, 7, cut(data["name"], 20), attr)
                self.put(y, 28, "POTION", C("purple", dim=sold))
                self.put(y, 36, cut(data["desc"], self.w - 48), C("dim"))
                pr = f"{price}g" if not sold else "sold"
                self.put(y, self.w - 9, pr.rjust(7),
                         C("gold" if afford and not sold else "red")
                         if not sold else C("faint"))
                continue
            if kind == "card":
                cd = data
                name = cd["name"]
                typ = cd["type"].upper()
                tcol = {"attack": "red", "skill": "blue",
                        "power": "purple"}[cd["type"]]
                self.put(y, 2, mark, C("gold", bold=True))
                cost = "X" if cd["cost"] < 0 else str(cd["cost"])
                self.put(y, 4, cost, C("gold", dim=sold))
                self.put(y, 7, cut(name, 20),
                         C(tcol, bold=sel, dim=sold) if not sold else C("faint"))
                self.put(y, 28, typ, C(tcol, dim=sold))
                self.put(y, 36, cut(ctext(cd), self.w - 48), C("dim"))
                pr = f"{price}g" if not sold else "sold"
                self.put(y, self.w - 9, pr.rjust(7),
                         C("gold" if afford and not sold else "red")
                         if not sold else C("faint"))
            elif kind == "relic":
                self.put(y, 2, mark, C("gold", bold=True))
                self.put(y, 4, cut(data["name"], 22), attr)
                self.put(y, 27, "RELIC", C("gold", dim=sold))
                self.put(y, 36, cut(data["desc"], 28), C("dim"))
                self.put(y, self.w - 9, (f"{price}g" if not sold else "sold").rjust(7),
                         C("gold" if afford and not sold else "red")
                         if not sold else C("faint"))
            else:
                self.put(y, 2, mark, C("gold", bold=True))
                self.put(y, 4, "Remove a card", attr)
                self.put(y, 27, "SERVICE", C("purple", dim=sold))
                self.put(y, 36, "Cut one card from your deck.", C("dim"))
                self.put(y, self.w - 9, (f"{price}g" if not sold else "sold").rjust(7),
                         C("gold" if afford and not sold else "red")
                         if not sold else C("faint"))
        self.hint("arrows choose   enter buy   esc leave")
        if self.shop_msg:
            self.put(self.h - 2, 2, cut(self.shop_msg, self.w - 4), C("green"))

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
                self.shop_msg = f"Bought {CARDS[s['cards'][idx]['cid']]['name']}."
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
            self.shop_msg = f"{CARDS[c['id']]['name']} was removed."
        self.overlay = None

    # -------------------------------------------------------------- event --
    def draw_event(self):
        ev = self.event
        self.draw_header("encounter")
        self.rule(2)
        bw = min(74, self.w - 8)
        bx = (self.w - bw) // 2
        by = 4
        bh = 16
        self.box(by, bx, bh, bw, C("purple", dim=True))
        title = ev["title"].upper()
        self.put(by + 1, bx + (bw - len(title)) // 2, title,
                 C("purple", bold=True))
        self.put(by + 2, bx + 2, GL["h"] * (bw - 4), C("faint"))
        stat = f"HP {self.run.hp}/{self.run.max_hp}   {self.run.gold}g"
        self.put(by + 1, bx + bw - 3 - len(stat), stat, C("dim"))
        for i, line in enumerate(ev["text"]):
            self.put(by + 4 + i, bx + (bw - len(line)) // 2, line, C("text"))
        if self.event_stage < len(ev["choices"]):
            oy = by + 8
            for i, ch in enumerate(ev["choices"]):
                sel = i == self.event_stage
                broke = (ch.get("gold", 0) < 0
                         and self.run.gold + ch["gold"] < 0)
                label = f"{GL['arrow']} {ch['label']}" if sel else f"  {ch['label']}"
                if broke:
                    label += "  (no gold)"
                self.put(oy + i * 2, bx + 5, label.ljust(22),
                         C("gold", bold=True) if sel and not broke
                         else (C("faint") if broke else C("text")))
                self.put(oy + i * 2, bx + 29, cut(ch["efe"], bw - 32),
                         C("red", dim=True) if broke else C("dim"))
            self.hint("arrows choose   enter decide")
        else:
            lines = wrap(self.event_msg, bw - 8)
            for i, line in enumerate(lines[:3]):
                self.put(by + 8 + i, bx + (bw - len(line)) // 2, line,
                         C("gold"))
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
        self.center(4, "A CACHE IN THE ASH", C("cyan", bold=True))
        art = [
            r"      .--------.      ",
            r"     /  .    .  \     ",
            r"    |  / \  / \  |    ",
            r"    |  \_/  \_/  |    ",
            r"     \    __    /     ",
            r"      '--------'      ",
        ]
        top = 7
        for i, line in enumerate(art):
            self.center(top + i, line, C("gold", bold=True))
        self.center(top + 8, GL["h"] * 30, C("faint"))
        for i, line in enumerate(self.treasure_lines):
            self.center(top + 10 + i * 2, line, C("gold"))
        if self.treasure_desc:
            self.center(top + 13, cut(self.treasure_desc, self.w - 8),
                        C("dim"))
        self.hint("enter continue")

    def key_treasure(self, ch):
        if is_enter(ch) or ch == ord(" ") or ch == 27:
            self.leave_node()

    # -------------------------------------------------------- end screens --
    def draw_victory(self):
        f = self.final
        for a in self.ash:
            if 0 <= int(a[1]) < self.h:
                self.put(int(a[1]), int(a[0]), a[3], C("ember", dim=True))
        art = banner("VICTORY")
        y0 = 4
        for i, line in enumerate(art):
            self.center(y0 + i, line, C("gold", bold=True))
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
        self.center(self.h - 2, "enter title   \u00b7   r new run", C("faint"))

    def draw_gameover(self):
        f = self.final
        art = banner("YOU DIED")
        y0 = 4
        for i, line in enumerate(art):
            self.center(y0 + i, line, C("red", bold=True))
        self.center(y0 + 6, "Your deck is scattered in the ash.",
                    C("text"))
        self.stats_block(y0 + 9, f)
        self.center(self.h - 2, "enter title   \u00b7   r new run", C("faint"))

    def stats_block(self, y, f):
        rows = [
            ("FLOORS CLIMBED", f"{f['floor']} / {TOTAL_FLOORS}"),
            ("ACTS CLEARED", f"{min(f['act'] + (1 if f['won'] else 0), ACTS)} / {ACTS}"),
            ("ENEMIES SLAIN", str(f["kills"])),
            ("DAMAGE DEALT", str(f.get("damage", 0))),
            ("GOLD", str(f["gold"])),
            ("DECK", f"{f['deck']} cards"),
            ("RELICS", str(f["relics"])),
            ("SCORE", f"{f['score']}   seed {f.get('seed', '-')}"),
        ]
        x = self.w // 2 - 12
        for i, (k, v) in enumerate(rows):
            self.put(y + i, x, k, C("dim"))
            self.put(y + i, x + 18, v, C("text", bold=True))
        if getattr(self, "new_best", False):
            self.center(y + len(rows) + 1, "NEW BEST SCORE", C("gold", bold=True))

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

    def overlay_box(self, hgt, wdt, title):
        y = max(1, (self.h - hgt) // 2)
        x = max(1, (self.w - wdt) // 2)
        self.clear_inside(y, x, hgt, wdt)
        self.box(y, x, hgt, wdt, C("gold"), double=True, title=title,
                 tattr=C("gold", bold=True))
        return y, x

    def draw_card_list(self, cards, sel, title, hint, valid=None, sort=True):
        wdt = min(96, self.w - 6)
        hgt = min(self.h - 2, max(10, 7 + (len(cards) + 2) // 3))
        y, x = self.overlay_box(hgt, wdt, title)
        rows = max(1, (hgt - 4))
        per_col = rows
        inner = wdt - 4
        colw = inner // 3
        order = {"attack": 0, "skill": 1, "power": 2}
        if sort:
            idxs = sorted(range(len(cards)),
                          key=lambda k: (order.get(CARDS[cards[k]["id"]]["type"], 3),
                                         CARDS[cards[k]["id"]]["cost"],
                                         cdata(cards[k])["name"]))
        else:
            idxs = list(range(len(cards)))
        for pos, i in enumerate(idxs):
            c = cards[i]
            cd = cdata(c)
            col = pos // per_col
            rowi = pos % per_col
            if col > 2:
                break
            cy = y + 2 + rowi
            cx = x + 2 + col * colw
            ok = True if valid is None else valid(i)
            is_sel = i == sel
            if not ok:
                self.put(cy, cx - 1, " " * (colw - 1), C("faint"))
            attr = C("white", bold=True) if is_sel else (
                C("text") if ok else C("faint"))
            if is_sel:
                self.put(cy, cx - 1, " " * (colw - 1), C("blue", rev=True))
            name = cut(cd["name"], colw - 8)
            cost = "X" if cd["cost"] < 0 else str(cd["cost"])
            self.put(cy, cx, cost.rjust(2), C("gold") if ok else C("faint"))
            self.put(cy, cx + 3, name, attr)
            self.put(cy, cx + colw - 7,
                     cd["type"][:6].upper(), C("dim"))
        if len(cards) == 0:
            self.put(y + 2, x + 2, "empty", C("dim"))
        self.put(y + hgt - 2, x + 3, cut(hint, wdt - 6), C("faint"))

    def draw_log(self):
        wdt = min(88, self.w - 6)
        logs = self.cb.logs[-18:] if self.cb else []
        hgt = min(self.h - 4, len(logs) + 4)
        y, x = self.overlay_box(hgt, wdt, "COMBAT LOG")
        for i, (msg, col) in enumerate(logs):
            self.put(y + 2 + i, x + 2, cut(msg, wdt - 4), C(col))
        self.put(y + hgt - 2, x + 3, "esc to close", C("faint"))

    def draw_glossary(self):
        rows = [
            ("Vulnerable", "Takes 50% more damage. Ticks down each turn."),
            ("Weak", "Deals 25% less damage. Ticks down each turn."),
            ("Poison", "Loses HP at the start of its turn, then 1 stack."),
            ("Strength", "Adds damage to every attack."),
            ("Dexterity", "Adds Block to every card that grants Block."),
            ("Thorns", "Deals damage back when hit by an attack."),
            ("Metallicize", "Gains Block at the end of its turn."),
            ("Regeneration", "Heals at the end of its turn."),
            ("Blur", "Keeps its Block for one more turn."),
            ("Berserk", "+1 Energy each turn. Gained with 2 Vulnerable."),
            ("Juggernaut", "Deals damage whenever it gains Block."),
            ("Exhaust", "The card leaves your deck for this combat."),
        ]
        wdt = min(78, self.w - 6)
        hgt = len(rows) + 5
        y, x = self.overlay_box(hgt, wdt, "STATUS GLOSSARY")
        for i, (name, desc) in enumerate(rows):
            self.put(y + 2 + i, x + 2, name, C("gold", bold=True))
            self.put(y + 2 + i, x + 16, cut(desc, wdt - 19), C("text"))
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
            self.put(y + 2 + i * 2, x + 3,
                     (GL["arrow"] + " " + p["name"]) if sel else ("  " + p["name"]),
                     C(p["color"], bold=True) if sel else C("text"))
            self.put(y + 2 + i * 2, x + 26, cut(p["desc"], wdt - 28), C("dim"))
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

    def draw_pause(self):
        wdt = 46
        hgt = 15
        y, x = self.overlay_box(hgt, wdt, "PAUSED")
        items = ["Resume", "Deck", "Relics", "How to play", "Settings",
                 "Save and quit", "Abandon run"]
        for i, it in enumerate(items):
            sel = i == self.menu
            self.put(y + 2 + i, x + 4,
                     (GL["arrow"] + " " + it) if sel else ("  " + it),
                     C("gold", bold=True) if sel else C("text"))
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
                    if self.cb and self.cb.use_potion(self.pot_sel, self.tgt):
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
                    if self.cb and self.cb.use_potion(idx, self.tgt):
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
            ids = r.encounter_for(kind)
            self.disp_hp.clear()
            self.cb = Combat(r, ids, kind, r.rng)
            self.see("enemies", ids)
            if kind == "boss" and self.cb.enemies:
                self.notify(f"{self.cb.enemies[0].name} blocks the way.", 3.0)
            else:
                self.tip("combat")
            self.sel = 0
            self.tgt = 0
            self.win_at = None
            self.lose_at = None
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
