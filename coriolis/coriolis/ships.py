"""Ship types: stats, silhouettes and spawn tables.

Stats are in metres, metres per second and hit points. Bounties are credits
paid for a kill; police ships pay nothing (and cost you legal status).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ShipType:
    key: str
    name: str
    art: tuple
    width: float
    speed: float
    turn: float
    shields: float
    energy: float
    laser: float
    bounty: float
    cargo: int
    role: str
    aggression: float

    @property
    def colour(self):
        return {"pirate": "red", "police": "cyan", "trader": "green",
                "hunter": "orange", "military": "blue", "alien": "purple",
                "rock": "dim", "traffic": "faint", "cargo": "gold",
                "missile": "red"}.get(self.role, "white")


SHIPS = {
    "sidewinder": ShipType(
        "sidewinder", "Sidewinder",
        ("    /\\    ", "   /  \\   ", "  /_/\\_\\  ", "<__/  \\__>"),
        15, 320, 1.6, 20, 35, 4, 5, 1, "pirate", 0.6),
    "krait": ShipType(
        "krait", "Krait",
        ("  /\\  /\\  ", " /  \\/  \\ ", "/_/\\__/\\_\\", "   |__|   "),
        30, 380, 1.4, 30, 50, 6, 10, 2, "pirate", 0.7),
    "mamba": ShipType(
        "mamba", "Mamba",
        ("    /\\    ", "   /__\\   ", "  /_/\\_\\  ", " /_/  \\_\\ ",
         "<_/    \\_>"),
        45, 500, 1.7, 35, 60, 8, 15, 2, "pirate", 0.8),
    "cobra1": ShipType(
        "cobra1", "Cobra Mk I",
        ("   /\\   ", "  /__\\  ", " /_/\\_\\ ", "<_/  \\_>"),
        50, 420, 1.2, 30, 55, 6, 20, 3, "trader", 0.3),
    "cobra": ShipType(
        "cobra", "Cobra Mk III",
        ("    /\\    ", "   /__\\   ", "  /_||_\\  ", " /_/  \\_\\ ",
         "/_/    \\_\\"),
        65, 450, 1.3, 45, 70, 8, 25, 4, "trader", 0.4),
    "python": ShipType(
        "python", "Python",
        ("   ______   ", "  /|    |\\  ", " /_|____|_\\ ", "<_/  __  \\_>",
         "  /_/  \\_\\  "),
        110, 300, 0.7, 80, 90, 6, 40, 8, "trader", 0.2),
    "adder": ShipType(
        "adder", "Adder",
        ("  /\\  ", " /__\\ ", "<_/\\_>"),
        25, 360, 1.5, 20, 40, 4, 8, 2, "trader", 0.3),
    "moray": ShipType(
        "moray", "Moray",
        ("  /\\/\\  ", " /_||_\\ ", "<_/  \\_>"),
        45, 400, 1.4, 30, 55, 6, 15, 3, "trader", 0.35),
    "ferdl": ShipType(
        "ferdl", "Fer-de-Lance",
        ("    /\\    ", "   /_\\/   ", "  /_/\\_\\  ", " /_/  \\_\\ ",
         "<_/    \\_>"),
        40, 560, 1.9, 45, 65, 12, 45, 3, "hunter", 0.9),
    "asp": ShipType(
        "asp", "Asp Mk II",
        ("    /\\    ", "   /__\\   ", "  /_|\\_\\  ", " /_/  \\_\\ ",
         "<_/    \\_>"),
        60, 620, 1.8, 50, 70, 12, 60, 4, "military", 0.8),
    "viper": ShipType(
        "viper", "Viper",
        ("    /\\    ", "   /__\\   ", "  /_|__\\  ", " /_/  \\_\\ "),
        35, 520, 1.8, 40, 60, 10, 0, 2, "police", 1.0),
    "thargoid": ShipType(
        "thargoid", "Thargoid",
        ("   _____   ", "  /|   |\\  ", " /_|___|_\\ ", "<_/     \\_>",
         "  \\_____/  "),
        90, 480, 1.4, 90, 110, 16, 100, 0, "alien", 1.0),
    "thargon": ShipType(
        "thargon", "Thargon",
        (" <\\/ > ", " <//\\> ", "  \\/  "),
        20, 420, 2.0, 25, 30, 6, 15, 0, "alien", 1.0),
    "shuttle": ShipType(
        "shuttle", "Shuttle",
        ("  ____  ", " /|__|\\ ", "<_/  \\_>"),
        20, 220, 1.0, 15, 25, 0, 0, 1, "traffic", 0.0),
    "transporter": ShipType(
        "transporter", "Transporter",
        ("  ______  ", " /|    |\\ ", "<_|____|_>"),
        80, 260, 0.8, 40, 50, 4, 20, 5, "trader", 0.15),
    "asteroid": ShipType(
        "asteroid", "Asteroid",
        ("  .--.  ", " / o  \\ ", "|  o  | ", " \\  o / ", "  '--'  "),
        120, 60, 0.2, 60, 80, 0, 0, 3, "rock", 0.0),
    "canister": ShipType(
        "canister", "Cargo Canister",
        ("[##]", "[##]"),
        4, 40, 0.1, 1, 1, 0, 0, 0, "cargo", 0.0),
    "missile": ShipType(
        "missile", "Missile",
        ("<|=)", " || "),
        3, 700, 1.0, 1, 1, 0, 0, 0, "missile", 1.0),
    "escape": ShipType(
        "escape", "Escape Capsule",
        ("[=]", "[=]"),
        6, 300, 0.5, 5, 5, 0, 0, 0, "cargo", 0.0),
}

PLAYER_SHIP = "cobra"

# Encounter tables by system government (0 anarchy .. 7 corporate state).
PIRATES = ("sidewinder", "krait", "mamba", "cobra1")
TRADERS = ("adder", "moray", "cobra", "python", "transporter")
HUNTERS = ("ferdl", "asp")
POLICE = ("viper", "asp")
TRAFFIC = ("shuttle", "transporter")


def default_missile_target():
    return "cobra"


@dataclass(frozen=True)
class PlayerShip:
    """A hull the commander can own and fly."""

    key: str
    name: str
    price: float          # showroom price, credits
    hull: float
    shields: float
    cargo: int            # tonnes before a cargo bay
    max_speed: float
    accel: float
    pitch_rate: float
    roll_rate: float
    missiles: int
    slots: int            # equipment slots
    repair: float         # repair cost multiplier
    blurb: str


PLAYER_SHIPS = {
    "cobra": PlayerShip(
        "cobra", "Cobra Mk III", 3200.0, 100.0, 100.0, 20, 900.0, 700.0,
        1.15, 2.0, 4, 8, 1.0,
        "The all-rounder: enough hold, enough guns, enough speed."),
    "adder": PlayerShip(
        "adder", "Adder", 5200.0, 110.0, 80.0, 40, 620.0, 420.0,
        0.95, 1.6, 4, 7, 0.9,
        "A slow freighter with a cavernous hold. Bring an escort."),
    "moray": PlayerShip(
        "moray", "Moray Starboat", 7400.0, 80.0, 95.0, 12, 1150.0, 950.0,
        1.35, 2.5, 3, 8, 1.1,
        "A fast courier: run before you fight."),
    "ferdl": PlayerShip(
        "ferdl", "Fer-de-Lance", 12500.0, 120.0, 130.0, 16, 1050.0, 880.0,
        1.3, 2.2, 4, 9, 1.3,
        "A combat hull with teeth and a small hold."),
    "asp": PlayerShip(
        "asp", "Asp Mk II", 15800.0, 105.0, 115.0, 18, 1000.0, 820.0,
        1.25, 2.1, 3, 10, 1.2,
        "Long legs and deep tanks for the far side of the chart."),
}
SHIP_ORDER = ("cobra", "adder", "moray", "ferdl", "asp")
TRADE_IN = 0.6          # a used hull is worth 60% of its showroom price
LARGE_BAY_BONUS = 15


def player_ship(key):
    return PLAYER_SHIPS.get(key, PLAYER_SHIPS["cobra"])
