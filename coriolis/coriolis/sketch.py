"""The 3D view, rasterised to characters.

Nothing here imports curses: the renderer fills a Canvas of glyphs and colour
names, and the UI layer paints that canvas onto the terminal. That keeps the
projection maths unit-testable.
"""

import math
import zlib

from .flight import Vec3, camera, project
from .station import RADIUS

CHAR_ASPECT = 2.0   # a terminal cell is about twice as tall as it is wide


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.ch = [[" "] * w for _ in range(h)]
        self.fg = [[None] * w for _ in range(h)]
        self.depth = [[1e12] * w for _ in range(h)]

    def put(self, x, y, ch, colour=None, depth=1e9):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h and depth <= self.depth[y][x]:
            self.ch[y][x] = ch
            self.fg[y][x] = colour
            self.depth[y][x] = depth

    def text(self, x, y, s, colour=None):
        for i, c in enumerate(s):
            if c != " ":
                self.put(x + i, y, c, colour, -1e9)

    def rows(self):
        return ["".join(r) for r in self.ch]

    def colours(self):
        return self.fg


# A fixed, deterministic star sphere so the background never flickers.
def _stars(count=260):
    out = []
    for i in range(count):
        a = zlib.crc32(f"a{i}".encode()) / 0xFFFFFFFF
        b = zlib.crc32(f"b{i}".encode()) / 0xFFFFFFFF
        z = a * 2 - 1
        phi = b * 2 * math.pi
        r = math.sqrt(max(0.0, 1 - z * z))
        out.append(Vec3(r * math.cos(phi), z, r * math.sin(phi)))
    return out


STARS = _stars()


def draw_starfield(cv, orient, focal, ascii_only=False):
    for i, star in enumerate(STARS):
        local = orient.t() @ star
        if local.z <= 0.15:
            continue
        sx = cv.w / 2.0 + local.x / local.z * focal * 0.75
        sy = cv.h / 2.0 - local.y / local.z * focal * 0.75 / CHAR_ASPECT
        x, y = int(sx), int(sy)
        if 0 <= x < cv.w and 0 <= y < cv.h:
            bright = zlib.crc32(f"c{i}".encode()) % 3
            cv.put(x, y, "." if ascii_only or bright else ".",
                   ("faint", "dim", "white")[bright], 1e9)


def draw_body(cv, orient, pos, world, radius, ch, colour, focal):
    cam = camera(orient, pos, world)
    if cam.z <= 1:
        return
    sx = cv.w / 2.0 + cam.x / cam.z * focal
    sy = cv.h / 2.0 - cam.y / cam.z * focal / CHAR_ASPECT
    apparent = radius * focal / cam.z
    if apparent < 1.2:
        cv.put(sx, sy, ch, colour, cam.z)
        return
    r = min(apparent, max(cv.w, cv.h) * 0.9)
    for dy in range(-int(r), int(r) + 1):
        for dx in range(-int(r), int(r) + 1):
            if dx * dx + dy * dy * 4 <= r * r:
                edge = dx * dx + dy * dy * 4 > (r - 1.2) ** 2
                cv.put(sx + dx, sy + dy, ch if edge else ch.lower(),
                       colour, cam.z + 1)


def sprite_size(width_m, z, focal, art_w):
    """How many characters wide a ship of width_m metres looks at z metres."""
    if z <= 0:
        return 0
    apparent = width_m * focal / z
    return max(1, min(art_w, int(round(apparent))))


def draw_sprite(cv, orient, pos, world, art, width_m, colour, focal, mode="solid", flash=False):
    cam = camera(orient, pos, world)
    if cam.z <= 4:
        return None
    vis = project(cam, cv.w, cv.h, focal)
    if vis is None:
        return None
    sx, sy, z, _ = vis
    rows = [r.ljust(max(len(r) for r in art)) for r in art]
    art_w = len(rows[0])
    art_h = len(rows)
    tw = sprite_size(width_m, z, focal, art_w * 2)
    if tw < 3:
        cv.put(sx, sy, "*" if flash else "+", colour, z)
        return (sx, sy, tw, 1)
    th = max(2, min(art_h * 2, int(round(art_h * tw / art_w * CHAR_ASPECT / 2.0))))
    for ay in range(th):
        src_y = int(ay * art_h / th)
        row = rows[src_y]
        for ax in range(tw):
            src_x = int(ax * art_w / tw)
            ch = row[src_x]
            if ch == " ":
                continue
            if mode == "wire" and 0 < ay < th - 1 and 0 < ax < tw - 1:
                continue
            cv.put(sx - tw / 2 + ax, sy - th / 2 + ay, ch if not flash else "#",
                   colour if not flash else "white", z)
    return (sx, sy, tw, th)


def draw_contact(cv, orient, pos, c, focal, mode="solid"):
    colour = c.colour
    if c.flash > 0:
        colour = "white"
    return draw_sprite(cv, orient, pos, c.pos, c.type.art, c.size, colour,
                       focal, mode, flash=c.flash > 0.1)


def octagon(cv, sx, sy, w, h, colour, depth=100.0):
    """A chamfered box, drawn at any size: the station hull up close."""
    bs = chr(92)
    w, h = max(5, int(w)), max(3, int(h))
    x0, y0 = int(sx - w / 2), int(sy - h / 2)
    cut = max(1, w // 6)
    for x in range(x0 + cut, x0 + w - cut):
        cv.put(x, y0, "_", colour, depth)
        cv.put(x, y0 + h - 1, "_", colour, depth)
    for y in range(y0 + 1, y0 + h - 1):
        cv.put(x0, y, "|", colour, depth)
        cv.put(x0 + w - 1, y, "|", colour, depth)
    for i in range(cut):
        cv.put(x0 + cut - i, y0 + i, "/", colour, depth)
        cv.put(x0 + w - cut + i - 1, y0 + i, bs, colour, depth)
        cv.put(x0 + cut - i, y0 + h - 1 - i, bs, colour, depth)
        cv.put(x0 + w - cut + i - 1, y0 + h - 1 - i, "/", colour, depth)


def draw_station(cv, orient, pos, station, focal, mode="solid"):
    """The Coriolis, drawn as a scalable hull with a slot that tumbles."""
    cam = camera(orient, pos, station.pos)
    if cam.z <= 5:
        return None
    vis = project(cam, cv.w, cv.h, focal * 0.95)
    if vis is None:
        return None
    sx, sy, z, _ = vis
    apparent = RADIUS * 2.1 * focal / z
    w = max(9.0, min(cv.w + 10, apparent))
    h = max(4.0, w / 2.2)
    octagon(cv, sx, sy, w, h, "cyan", z)
    if w >= 12:
        half = max(2, int(w) // 8)
        tilt = math.sin(station.angle) * (h / 6)
        for i in range(-half, half + 1):
            cv.put(sx + i, sy + tilt, "=", "gold", z - 1)
    return (sx, sy, w, h)


def draw_reticle(cv, colour="gold"):
    """A gunsight that only fills empty cells, so it never eats a hull."""
    cx, cy = cv.w // 2, cv.h // 2
    for dx, dy in ((-3, 0), (-2, 0), (2, 0), (3, 0), (0, -2), (0, 2)):
        x, y = cx + dx, cy + dy
        if 0 <= x < cv.w and 0 <= y < cv.h and cv.ch[y][x] == " ":
            cv.put(x, y, "-" if dy == 0 else "|", colour, -1e9)


def draw_scene(state, w, h, mode="solid", ascii_only=False, show_reticle=True):
    """Render the forward view. Returns (canvas, target_info)."""
    cv = Canvas(w, h)
    orient = state.flight.orient
    pos = state.flight.pos
    focal = w * 0.95
    draw_starfield(cv, orient, focal, ascii_only)
    draw_body(cv, orient, pos, state.planet, 9000, "o", "blue", focal)
    draw_body(cv, orient, pos, state.sun, 14000, "O", "orange", focal)
    contact = sorted(state.contacts,
                     key=lambda c: camera(orient, pos, c.pos).z, reverse=True)
    target_info = None
    for c in contact:
        if c.kind in ("ship", "missile", "cargo", "asteroid"):
            box = draw_contact(cv, orient, pos, c, focal, mode)
            if box and c is getattr(state, "missile_target", None):
                sx, sy, tw, th = box
                hw = max(1, tw // 2 + 1)
                hh = max(1, th // 2 + 1)
                for dx in range(-hw, hw + 1):
                    cv.put(sx + dx, sy - hh, "-", "green", -1e9)
                    cv.put(sx + dx, sy + hh, "-", "green", -1e9)
                for dy in range(-hh + 1, hh):
                    cv.put(sx - hw, sy + dy, "|", "green", -1e9)
                    cv.put(sx + hw, sy + dy, "|", "green", -1e9)
    draw_station(cv, orient, pos, state.station, focal, mode)
    if show_reticle:
        draw_reticle(cv, "red" if any(c.hostile for c in state.contacts) else "gold")
    best = None
    for c in state.contacts:
        if c.kind != "ship":
            continue
        cam = camera(orient, pos, c.pos)
        d = cam.length()
        ang = orient.forward.angle_to(c.pos - pos)
        if ang < 0.5 and (best is None or d < best[0]):
            best = (d, c)
    if best:
        target_info = (best[1], best[0])
    return cv, target_info


def radar_contacts(state, cols=15, rows=5, max_range=16000.0):
    """Tactical radar: bearing across, distance up, height as the glyph.

    Forward is up, the player sits at the centre. A contact that is behind
you shows as an x near the bottom edge.
    """
    orient = state.flight.orient
    pos = state.flight.pos
    cells = []
    for c in state.contacts:
        if c.kind == "missile":
            continue
        cam = camera(orient, pos, c.pos)
        if cam.length() > max_range:
            continue
        col = int(round((cam.x / max_range) * (cols - 1) / 2 + (cols - 1) / 2))
        row = int(round((rows - 1) / 2 - (cam.z / max_range) * (rows - 1) / 2))
        if not (0 <= col < cols and 0 <= row < rows):
            continue
        if cam.z <= 0:
            ch, colour = "x", "faint"
        elif cam.y > max_range * 0.12:
            ch, colour = "^", c.colour
        elif cam.y < -max_range * 0.12:
            ch, colour = "v", c.colour
        else:
            ch, colour = "o", c.colour
        cells.append((row, col, ch, colour))
    return cells
