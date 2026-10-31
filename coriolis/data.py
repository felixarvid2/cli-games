"""Static game data: goods, equipment, ranks, and tuning constants.

Pure data, no curses and no game logic, so tests can import it freely.
"""

from dataclasses import dataclass

# ------------------------------------------------------------------ tuning --
MAX_FUEL = 7.0            # light years on a full tank
FUEL_PRICE = 0.5          # credits per light year
START_CREDITS = 100.0
CARGO_BASE = 20           # tonnes
CARGO_LARGE = 35
MAX_MISSILES = 4
START_SYSTEM = "Lave"
START_GALAXY = 1
TICK = 1.0 / 60.0         # physics step
RENDER_FPS = 30
NEAR_PLANE = 12.0         # metres; anything closer is clipped
LASER_RANGE = 3000.0      # metres
LASER_CONE = 0.055        # radians half-angle
MASS_LOCK_RANGE = 2500.0  # metres
DOCK_RANGE = 1500.0


@dataclass(frozen=True)
class Good:
    key: str
    name: str
    base: float          # credits per tonne in a neutral market
    industrial: float    # 1.0 = industrial good, 0.0 = agricultural good
    tech: int            # minimum tech level that produces it
    illegal: bool = False


GOODS = (
    Good("food", "Food", 4.0, 0.0, 1),
    Good("textiles", "Textiles", 6.5, 0.2, 1),
    Good("radioactives", "Radioactives", 22.0, 0.7, 5),
    Good("slaves", "Slaves", 14.0, 0.1, 3, True),
    Good("liquor", "Liquor/Wines", 26.0, 0.1, 4),
    Good("luxuries", "Luxuries", 92.0, 0.3, 6),
    Good("narcotics", "Narcotics", 110.0, 0.4, 7, True),
    Good("computers", "Computers", 85.0, 1.0, 8),
    Good("machinery", "Machinery", 60.0, 0.9, 6),
    Good("alloys", "Alloys", 34.0, 0.8, 4),
    Good("firearms", "Firearms", 70.0, 0.8, 6, True),
    Good("furs", "Furs", 56.0, 0.1, 1),
    Good("minerals", "Minerals", 12.0, 0.6, 1),
    Good("gold", "Gold", 380.0, 0.5, 6),
    Good("platinum", "Platinum", 900.0, 0.5, 7),
    Good("gems", "Gem-Stones", 1600.0, 0.4, 9),
    Good("alien", "Alien Items", 500.0, 0.5, 10, True),
)

GOOD_BY_KEY = {g.key: g for g in GOODS}


@dataclass(frozen=True)
class Equipment:
    key: str
    name: str
    price: float
    tech: int
    desc: str


EQUIPMENT = (
    Equipment("missile", "Missile", 30.0, 1, "Homing warhead. Up to four."),
    Equipment("largebay", "Large Cargo Bay", 400.0, 2,
              "Raises capacity from 20 to 35 tonnes."),
    Equipment("ecm", "E.C.M. System", 600.0, 4,
              "Destroys incoming missiles, drains energy."),
    Equipment("beam", "Beam Laser", 1000.0, 5,
              "Twice the punch of the pulse laser."),
    Equipment("scoop", "Fuel Scoops", 525.0, 5,
              "Scoop cargo canisters, and skim suns for fuel."),
    Equipment("bomb", "Energy Bomb", 900.0, 7,
              "One shot. Kills everything nearby."),
    Equipment("escape", "Escape Capsule", 1000.0, 6,
              "Saves you, not the cargo, when the hull goes."),
    Equipment("docking", "Docking Computer", 1500.0, 9,
              "Docks for you from two kilometres out."),
    Equipment("energy", "Extra Energy Unit", 1500.0, 8,
              "Faster energy bank recharge."),
    Equipment("military", "Military Laser", 6000.0, 10,
              "Three times the punch of the pulse laser."),
    Equipment("galactic", "Galactic Hyperdrive", 5000.0, 10,
              "One jump to the next galaxy."),
)

EQUIPMENT_BY_KEY = {e.key: e for e in EQUIPMENT}

# Laser tiers by equipment key (higher is better).
LASER_DAMAGE = {"pulse": 8.0, "beam": 16.0, "military": 26.0}

RANKS = (
    (0, "Harmless"),
    (8, "Mostly Harmless"),
    (16, "Poor"),
    (32, "Average"),
    (64, "Above Average"),
    (128, "Competent"),
    (512, "Dangerous"),
    (2560, "Deadly"),
    (6400, "Elite"),
)

LEGAL_NAMES = ("Clean", "Offender", "Fugitive")


def rank_for(kills):
    name = RANKS[0][1]
    for need, title in RANKS:
        if kills >= need:
            name = title
    return name


def legal_for(points):
    """Legal status from accumulated points (0 clean, 50+ fugitive)."""
    if points <= 0:
        return 0
    return 1 if points < 50 else 2


def next_rank(kills):
    """(title, kills still needed) for the next promotion."""
    for need, title in RANKS:
        if kills < need:
            return title, need - kills
    return RANKS[-1][1], 0
