"""Colour names, glyphs and small helpers shared by the UI.

Pure data only: nothing here imports curses, so the tables can be tested.
"""

# 256-colour indexes (xterm palette), with a sane fallback for 8-colour terms.
COLOUR = {
    "white": 255, "faint": 240, "dim": 244, "grey": 250,
    "gold": 220, "amber": 214, "orange": 208, "red": 203,
    "green": 47, "lime": 118, "cyan": 51, "teal": 37,
    "blue": 33, "navy": 19, "purple": 135, "pink": 213,
}

FALLBACK = {
    "white": 7, "faint": 8, "dim": 8, "grey": 7,
    "gold": 3, "amber": 3, "orange": 3, "red": 1,
    "green": 2, "lime": 2, "cyan": 6, "teal": 6,
    "blue": 4, "navy": 4, "purple": 5, "pink": 5,
}

UTF = {
    "bar_full": "\u2588", "bar_empty": "\u2591", "bar_half": "\u2592",
    "dot": "\u00b7", "block": "\u25aa", "arrow": "\u2192", "up": "\u2191",
    "down": "\u2193", "cursor": "\u25ba", "tick": "\u2713", "cross": "\u00d7",
    "ring": "\u25cb", "disc": "\u25cf", "star": "\u2726", "warn": "\u26a0",
    "h": "\u2500", "v": "\u2502", "tl": "\u250c", "tr": "\u2510",
    "bl": "\u2514", "br": "\u2518", "bullet": "\u2022",
}
ASCII = {
    "bar_full": "#", "bar_empty": "-", "bar_half": "+",
    "dot": ".", "block": "#", "arrow": "->", "up": "^",
    "down": "v", "cursor": ">", "tick": "x", "cross": "X",
    "ring": "o", "disc": "@", "star": "*", "warn": "!",
    "h": "-", "v": "|", "tl": "+", "tr": "+",
    "bl": "+", "br": "+", "bullet": "*",
}


def glyphs(utf=True):
    return UTF if utf else ASCII


def bar(value, maximum, width, utf=True):
    """A text progress bar, always exactly `width` cells."""
    if width <= 0:
        return ""
    ratio = 0.0 if maximum <= 0 else max(0.0, min(1.0, value / maximum))
    filled = int(round(ratio * width))
    g = glyphs(utf)
    return g["bar_full"] * filled + g["bar_empty"] * (width - filled)


def clamp(value, lo, hi):
    return max(lo, min(hi, value))


def ease_out(t):
    t = clamp(t, 0.0, 1.0)
    return 1.0 - (1.0 - t) ** 3


def pulse(t, speed=2.2):
    import math
    return 0.5 + 0.5 * math.sin(t * speed)


def cut(text, width):
    if width <= 0:
        return ""
    if len(text) <= width:
        return text
    if width <= 1:
        return text[:width]
    return text[:width - 1] + "."


def money(value):
    return f"{value:,.1f}"


def crouch(text, width):
    """Right-align inside width."""
    return text.rjust(width)


def wrap(text, width):
    """Greedy word wrap; always returns at least one line."""
    if width <= 1:
        return [text[:max(0, width)]]
    lines, line = [], ""
    for word in str(text).split():
        if not line:
            line = word
        elif len(line) + 1 + len(word) <= width:
            line += " " + word
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines or [""]
