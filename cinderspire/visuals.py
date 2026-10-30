"""Pure visual data and helpers for the CINDERSPIRE curses UI.

Nothing here imports curses, so it is safe to unit test. The UI layers these
glyphs, accents and easing curves over the curses drawing primitives.
"""

import math

# --------------------------------------------------------------- accents --
CLASS_ACCENT = {
    "warden": "blue",
    "ashblade": "green",
    "emberwright": "orange",
    "pilgrim": "gold",
    "paladin": "cyan",
}
CLASS_ACCENT_ALT = {
    "warden": "teal",
    "ashblade": "teal",
    "emberwright": "red",
    "pilgrim": "pink",
    "paladin": "blue",
}
CLASS_EMBLEM = {
    "warden": "W",
    "ashblade": "A",
    "emberwright": "E",
    "pilgrim": "P",
    "paladin": "S",
    "neutral": "N",
}

# -------------------------------------------------------------- keywords --
KW_ICON = {
    "taunt": "\u25a3",          # ▣ shield wall
    "divine_shield": "\u2726",  # ✦ sparkle
    "poisonous": "\u2620",      # ☠
    "charge": "\u00bb",         # »
    "rush": "\u2192",           # →
    "windfury": "\u21bb",       # ↻
    "lifesteal": "\u2665",      # ♥
}
KW_ASCII = {
    "taunt": "T",
    "divine_shield": "*",
    "poisonous": "P",
    "charge": ">",
    "rush": ">",
    "windfury": "W",
    "lifesteal": "+",
}
KW_LABEL = {
    "taunt": "TAUNT",
    "divine_shield": "SHIELD",
    "poisonous": "POISON",
    "charge": "CHARGE",
    "rush": "RUSH",
    "windfury": "WIND",
    "lifesteal": "LEECH",
}

KIND_ICON = {"minion": "\u2694", "spell": "\u2726"}   # ⚔ / ✦
KIND_ASCII = {"minion": "M", "spell": "S"}

RARITY_STRIP = {
    1: "\u00b7",       # cheap/common
    2: "\u2022",
    3: "\u25c6",       # ◆
    4: "\u25c6\u25c6",
    5: "\u2605",       # ★
}
RARITY_ASCII = {1: ".", 2: "*", 3: "#", 4: "##", 5: "@"}


def kw_glyphs(keywords, utf=True):
    table = KW_ICON if utf else KW_ASCII
    return " ".join(table[k] for k in
                    ("taunt", "divine_shield", "poisonous", "charge",
                     "rush", "windfury", "lifesteal") if k in keywords)


def kind_glyph(kind, utf=True):
    return (KIND_ICON if utf else KIND_ASCII).get(kind, "?")


def rarity_glyph(cost, utf=True):
    band = 1 if cost <= 1 else 2 if cost <= 3 else 3 if cost <= 5 else \
        4 if cost <= 7 else 5
    return (RARITY_STRIP if utf else RARITY_ASCII)[band]


def heal_color(frac):
    if frac >= 0.60:
        return "green"
    if frac >= 0.30:
        return "gold"
    return "red"


def mana_color(i, current):
    if i >= current:
        return "faint"
    return "cyan" if i % 2 == 0 else "blue"


def card_color(kind, playable=True):
    if kind == "spell":
        return "purple"
    return "green"


def accent_for(cls):
    return CLASS_ACCENT.get(cls, "gold")


def accent_alt_for(cls):
    return CLASS_ACCENT_ALT.get(cls, "ember")


# --------------------------------------------------------------- easing --
def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def ease_out(t):
    t = clamp(t)
    return 1.0 - (1.0 - t) ** 3


def ease_in_out(t):
    t = clamp(t)
    return t * t * (3.0 - 2.0 * t)


def pulse(t, speed=2.4):
    return 0.5 + 0.5 * math.sin(t * speed)


def breathe(t, speed=1.2):
    """0..1..0 with a soft plateau, good for borders."""
    return clamp(0.5 + 0.5 * math.sin(t * speed))


def sparkle(t, seed=0.0, speed=3.1):
    return pulse(t + seed, speed) > 0.82


# ------------------------------------------------------------------- art --
# Compact one/two-line motifs used on cards and empty slots.
MOTIF = {
    "warden": [" /\\_/\\ ", "( o.o )", " > ^ < "],
    "ashblade": ["  /\\  ", " /  \\ ", " \\  / "],
    "emberwright": ["  .*.  ", " .***. ", "  '*'  "],
    "pilgrim": ["  _|_  ", " (   ) ", "  /|\\  "],
    "paladin": ["  _+_  ", " |   | ", "  \\|/  "],
    "neutral": ["  .-.  ", " (   ) ", "  '-'  "],
}
MOTIF_ASCII = {
    "warden": [" /\\_/\\ ", "( o.o )", " > ^ < "],
    "ashblade": ["  /\\  ", " /  \\ ", " \\  / "],
    "emberwright": ["  .*.  ", " .***. ", "  '*'  "],
    "pilgrim": ["  _|_  ", " (   ) ", "  /|\\  "],
    "paladin": ["  _+_  ", " |   | ", "  \\|/  "],
    "neutral": ["  .-.  ", " (   ) ", "  '-'  "],
}


def motif(cls, utf=True):
    table = MOTIF if utf else MOTIF_ASCII
    return table.get(cls, table["neutral"])


CAMPFIRE = [
    "      (  .  )      ",
    "       .-'-.       ",
    "      /  |  \\      ",
    "     | . | . |     ",
    "      \\  |  /      ",
    "       '-.-'       ",
]

CHEST = [
    "      .--------.      ",
    "     /  .    .  \\     ",
    "    |  / \\  / \\  |    ",
    "    |  \\_/  \\_/  |    ",
    "     \\    __    /     ",
    "      '--------'      ",
]

COIN = [" _ ", "(o)", " - "]
