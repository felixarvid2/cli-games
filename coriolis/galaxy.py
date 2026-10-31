"""Procedural galaxy generation for CORIOLIS.

The structure follows Elite (1984): every galaxy is a chain of 256 systems
produced from three 16-bit seed words. Each system consumes draws from that
chain to derive its name, chart position, economy, government, tech level,
population, productivity and radius. Nothing here imports curses, so the
whole galaxy can be generated and asserted on in tests.
"""

from dataclasses import dataclass

GALAXY_COUNT = 10
SYSTEM_COUNT = 256

# The digram table from the original game. Table 0 holds the blank/punctuation
# digrams, so names are only drawn from tables 1-3.
DIGRAMS = (
    "..LEXEGEZACEBISO",
    "USESARMAINDIREA.",
    "ERATENBERALAVETI",
    "EDORQUANTEISRION",
)

ECONOMY_NAMES = (
    "Rich Industrial", "Average Industrial", "Poor Industrial",
    "Mainly Industrial", "Mainly Agricultural", "Rich Agricultural",
    "Average Agricultural", "Poor Agricultural",
)
ECONOMY_SHORT = (
    "Rich Ind.", "Avg Ind.", "Poor Ind.", "Mainly Ind.", "Mainly Agr.",
    "Rich Agr.", "Avg Agr.", "Poor Agr.",
)
GOVERNMENT_SHORT = (
    "Anarchy", "Feudal", "Multi-Gov.", "Dictator", "Communist",
    "Confed.", "Democracy", "Corporate",
)
GOVERNMENT_NAMES = (
    "Anarchy", "Feudal", "Multi-Government", "Dictatorship", "Communist",
    "Confederacy", "Democracy", "Corporate State",
)

# Seed for galaxy 1, chosen so that system 7 is LAVE with its classic profile
# (agricultural, democracy, tech 5, 2.5 billion). See tools/find_seed.py.
GALAXY1_SEED = (0x2A6F, 0x2827, 0x9D3C)
START_INDEX = 7


def tweak(seed):
    """Advance the three seed words by one step (the original 'twist')."""
    seed[0] = (seed[0] + seed[1]) & 0xFFFF
    seed[1] = (seed[1] + seed[2]) & 0xFFFF
    seed[2] = (seed[2] + seed[0]) & 0xFFFF


def draw(seed):
    """Consume one 16-bit value from the seed chain."""
    tweak(seed)
    return seed[2]


def _raw_name(seed):
    v = draw(seed)
    length = 2 + ((v >> 10) & 1) + ((v >> 12) & 1) + ((v >> 14) & 1)
    parts = []
    for _ in range(length):
        d = draw(seed)
        table = 1 + ((d >> 13) & 1) + ((d >> 14) & 1)
        idx = (d >> 9) & 0xF
        parts.append(DIGRAMS[table][idx * 2:idx * 2 + 2])
    return "".join(parts).capitalize()


def system_name(seed, used=None):
    """Generate a pronounceable 4-9 letter name, unique within a galaxy."""
    name = _raw_name(seed)
    for _ in range(40):
        valid = 4 <= len(name) <= 9 and "." not in name
        if valid and (used is None or name not in used):
            return name
        name = _raw_name(seed)
    # Nothing usable in 40 draws: build a unique name from what we have.
    base = "".join(ch for ch in name if ch.isalpha()) or "Zeta"
    base = (base + "Aaaa")[:4]
    if used is not None:
        for suffix in "ABCDEFGHJKLMNPQRSTUVWXYZ":
            if base + suffix not in used:
                return base + suffix
    return base


@dataclass(frozen=True)
class System:
    """One star system, fully derived from the galaxy seed chain."""

    galaxy: int
    index: int
    name: str
    x: float
    y: float
    economy: int
    government: int
    tech: int
    population: float
    productivity: int
    radius: int

    @property
    def key(self):
        return (self.galaxy, self.index)

    @property
    def economy_name(self):
        return ECONOMY_NAMES[self.economy]

    @property
    def government_name(self):
        return GOVERNMENT_NAMES[self.government]

    @property
    def economy_short(self):
        return ECONOMY_SHORT[self.economy]

    @property
    def government_short(self):
        return GOVERNMENT_SHORT[self.government]

    @property
    def industrial(self):
        """0.0 for poor agricultural ... 1.0 for rich industrial."""
        return (7 - self.economy) / 7.0

    @property
    def danger(self):
        """0..1 rough likelihood of pirates, used for spawns and warnings."""
        return max(0.0, min(1.0, (7 - self.government) / 7.0 * 0.75
                          + (1.0 - self.industrial) * 0.25))

    @property
    def is_anarchy(self):
        return self.government == 0

    def distance_to(self, other):
        return distance(self, other)

def distance(a, b):
    """Chart distance in light years (0.1 LY resolution)."""
    dx = a.x - b.x
    dy = a.y - b.y
    return round((dx * dx + dy * dy) ** 0.5, 1)


# Chart layout: 256 systems live on a jittered 16x16 grid. The grid keeps
# galaxies evenly spread (no two systems on top of each other) while the
# jitter stops the chart from looking like graph paper.
GRID = 16
SPACING = 5.4
JITTER = 1.5
MAX_JUMP = 7.0
MIN_SEP = 2.2


def _jitter(seed):
    return ((draw(seed) & 0xFF) - 128) / 128.0 * JITTER


def _repair(points, max_ly=6.5, passes=4):
    """Pull isolated systems towards their nearest neighbour.

    A system with nothing inside one fuel tank can never be reached, so the
    generated chart is nudged until every system has a neighbour within
    max_ly. The pass is deterministic: same galaxy, same nudge.
    """
    import math
    for _ in range(passes):
        moved = False
        for i in range(len(points)):
            best = None
            for j in range(len(points)):
                if i == j:
                    continue
                d = math.dist(points[i], points[j])
                if best is None or d < best[0]:
                    best = (d, j)
            d, j = best
            if d > max_ly:
                moved = True
                xi, yi = points[i]
                xj, yj = points[j]
                n = math.hypot(xi - xj, yi - yj) or 1.0
                points[i] = [xj + (xi - xj) / n * max_ly,
                             yj + (yi - yj) / n * max_ly]
        for i in range(len(points)):
            for j in range(i + 1, len(points)):
                d = math.dist(points[i], points[j])
                if d < MIN_SEP:
                    moved = True
                    xi, yi = points[i]
                    xj, yj = points[j]
                    if d < 0.01:
                        xj, yj = xi + MIN_SEP, yi
                        d = MIN_SEP
                    nx, ny = (xj - xi) / d, (yj - yi) / d
                    push = (MIN_SEP - d) / 2.0 + 0.01
                    points[i] = [xi - nx * push, yi - ny * push]
                    points[j] = [xj + nx * push, yj + ny * push]
        if not moved:
            break


def _build(seed, number):
    raw = []
    used = set()
    for i in range(SYSTEM_COUNT):
        name = system_name(seed, used)
        used.add(name)
        col, row = i % GRID, i // GRID
        x = (col - (GRID - 1) / 2) * SPACING + _jitter(seed)
        y = (row - (GRID - 1) / 2) * SPACING + _jitter(seed)
        economy = draw(seed) & 7
        government = (draw(seed) >> 5) & 7
        population = round(0.1 + (draw(seed) % 70) / 10.0, 1)
        productivity = 1 + draw(seed) % 100
        radius = 2000 + (draw(seed) % 40) * 100
        wealth = (7 - economy) * 8 + productivity // 2
        tech = 1 + int((wealth + population * 10 + (7 - government) * 3) / 18)
        tech = max(1, min(15, tech))
        raw.append((name, x, y, economy, government, population,
                    productivity, radius, tech))
    points = [[r[1], r[2]] for r in raw]
    _repair(points)
    # Centre every chart on the system you start in.
    ox, oy = points[START_INDEX]
    systems = []
    for i, r in enumerate(raw):
        systems.append(System(number, i, r[0], round(points[i][0] - ox, 3),
                              round(points[i][1] - oy, 3), r[3], r[4], r[8],
                              r[5], r[6], r[7]))
    return tuple(systems), seed


_CACHE = {}


def galaxy(number=1):
    """Return the 256 systems of a galaxy (1-10), generated on first use."""
    number = max(1, min(GALAXY_COUNT, int(number)))
    if number not in _CACHE:
        seed = list(GALAXY1_SEED)
        systems = ()
        for n in range(1, number + 1):
            systems, seed = _build(seed, n)
            _CACHE[n] = systems
    return _CACHE[number]


def galaxy_seed(number=1):
    """The three seed words that a galaxy's chain starts from."""
    seed = list(GALAXY1_SEED)
    for n in range(1, max(1, min(GALAXY_COUNT, int(number)))):
        _, seed = _build(seed, n)
    return tuple(seed)


def system(galaxy_number, index):
    systems = galaxy(galaxy_number)
    return systems[max(0, min(SYSTEM_COUNT - 1, int(index)))]


def start_system(galaxy_number=1):
    return system(galaxy_number, START_INDEX)


def find(name, galaxy_number=1):
    """Look a system up by name (case insensitive)."""
    want = name.strip().lower()
    for s in galaxy(galaxy_number):
        if s.name.lower() == want:
            return s
    return None


def neighbours(galaxy_number, index, max_ly=7.0):
    """Systems reachable on one tank, nearest first."""
    here = system(galaxy_number, index)
    out = []
    for s in galaxy(galaxy_number):
        if s.index == here.index:
            continue
        d = distance(here, s)
        if d <= max_ly:
            out.append((d, s))
    out.sort(key=lambda item: (item[0], item[1].name))
    return out


def chart_bounds(systems):
    """Bounding box (minx, miny, maxx, maxy) of a set of systems."""
    xs = [s.x for s in systems]
    ys = [s.y for s in systems]
    return min(xs), min(ys), max(xs), max(ys)
