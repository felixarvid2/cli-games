"""Game state: the pilot, the ship, encounters, docking and save files."""

import json
import os
import random
from dataclasses import dataclass, field

from . import galaxy
from .data import CARGO_BASE, MAX_FUEL, START_CREDITS, legal_for, rank_for
from .flight import FlightModel, Vec3
from .market import Market
from .station import Station

SAVE_VERSION = 1
START_INDEX = galaxy.START_INDEX
DATA_DIR = os.path.join(
    os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share")),
    "coriolis")
SAVE_PATH = os.path.join(DATA_DIR, "save.json")
PROFILE_PATH = os.path.join(DATA_DIR, "profile.json")

MAX_SHIELD = 100.0
BANK = 25.0
HULL = 100.0


@dataclass
class Pilot:
    name: str = "Jameson"
    credits: float = START_CREDITS
    fuel: float = MAX_FUEL
    cargo: dict = field(default_factory=dict)
    cargo_cap: int = CARGO_BASE
    equipment: set = field(default_factory=set)
    missiles: int = 3
    kills: int = 0
    legal: int = 0
    galaxy: int = 1
    system: int = START_INDEX
    badges: list = field(default_factory=list)
    deaths: int = 0
    jumps: int = 0

    # -- cargo ----------------------------------------------------------
    def cargo_used(self):
        return sum(self.cargo.values())

    def cargo_free(self):
        return max(0, self.cargo_cap - self.cargo_used())

    def add_cargo(self, key, qty):
        if qty <= 0:
            return
        self.cargo[key] = self.cargo.get(key, 0) + int(qty)

    def remove_cargo(self, key, qty):
        left = self.cargo.get(key, 0) - int(qty)
        if left > 0:
            self.cargo[key] = left
        else:
            self.cargo.pop(key, None)

    # -- derived ---------------------------------------------------------
    @property
    def laser(self):
        if "military" in self.equipment:
            return "military"
        if "beam" in self.equipment:
            return "beam"
        return "pulse"

    @property
    def rank(self):
        return rank_for(self.kills)

    @property
    def legal_name(self):
        return ("Clean", "Offender", "Fugitive")[legal_for(self.legal)]

    def has(self, key):
        return key in self.equipment

    def to_dict(self):
        return {"name": self.name, "credits": self.credits, "fuel": self.fuel,
                "cargo": self.cargo, "cargo_cap": self.cargo_cap,
                "equipment": sorted(self.equipment), "missiles": self.missiles,
                "kills": self.kills, "legal": self.legal,
                "galaxy": self.galaxy, "system": self.system,
                "badges": self.badges, "deaths": self.deaths,
                "jumps": self.jumps}

    @classmethod
    def from_dict(cls, data):
        p = cls()
        for key in ("name", "credits", "fuel", "cargo_cap", "missiles",
                    "kills", "legal", "galaxy", "system", "deaths", "jumps"):
            if key in data:
                setattr(p, key, data[key])
        p.cargo = {k: int(v) for k, v in (data.get("cargo") or {}).items() if v}
        p.equipment = set(data.get("equipment") or [])
        p.badges = list(data.get("badges") or [])
        return p


@dataclass
class Profile:
    kills: int = 0
    deaths: int = 0
    badges: list = field(default_factory=list)
    best_rank: str = "Harmless"

    def to_dict(self):
        return {"kills": self.kills, "deaths": self.deaths,
                "badges": self.badges, "best_rank": self.best_rank}

    @classmethod
    def from_dict(cls, data):
        p = cls()
        if data:
            p.kills = int(data.get("kills", 0))
            p.deaths = int(data.get("deaths", 0))
            p.badges = list(data.get("badges") or [])
            p.best_rank = data.get("best_rank", "Harmless")
        return p


class GameState:
    """Everything that makes up a run: pilot, ship, system, contacts."""

    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self.seed = seed
        self.pilot = Pilot()
        self.flight = FlightModel()
        self.station = Station(Vec3(0.0, 0.0, 0.0))
        self.sun = Vec3(60000.0, 24000.0, -42000.0)
        self.planet = Vec3(-70000.0, -18000.0, -90000.0)
        self.contacts = []
        self.market = Market.for_system(self.system)
        self.messages = []
        self.mode = "flight"
        self.docking = False
        self.jump = None
        self.time = 0.0
        self.last_shot = 0.0
        self.hull = HULL
        self.shields = {"fore": MAX_SHIELD, "aft": MAX_SHIELD}
        self.banks = [BANK] * 4
        self.cool = 0.0
        self.missile_target = None
        self.dead = False
        self.docked_at = None

    # -- system ----------------------------------------------------------
    @property
    def system(self):
        return galaxy.system(self.pilot.galaxy, self.pilot.system)

    @property
    def seed_value(self):
        return (self.pilot.galaxy * 100003 + self.pilot.system * 977
                + int(self.time * 0.37))

    def say(self, text, dur=3.5):
        self.messages.append([text, dur])
        del self.messages[:-4]

    @property
    def alert(self):
        return self.messages[-1][0] if self.messages else ""

    # -- launch / dock ---------------------------------------------------
    def launch(self):
        """Leave the station, nose pointing at it from six kilometres out."""
        self.station.pos = Vec3(0.0, 0.0, 0.0)
        self.flight = FlightModel(pos=Vec3(0.0, 0.0, -6000.0))
        self.docked_at = None
        self.mode = "flight"
        self.hull = max(self.hull, 1.0)
        self.say("Launch. Fly toward the station slot to dock.")

    def dock(self):
        self.mode = "docked"
        self.docking = False
        self.contacts = []
        if self.docked_at is None or self.docked_at.index != self.system.index:
            self.market = Market.for_system(self.system)
        else:
            # Prices settle back to equilibrium between visits.
            for listing in self.market.listings.values():
                listing.bought = 0
                listing.sold = 0
        self.docked_at = self.system
        self.jump = None
        self.pilot.system = self.system.index
        self.say(f"Docked at {self.system.name} station.")

    # -- hyperspace ------------------------------------------------------
    def can_jump(self, index):
        here = self.system
        target = galaxy.system(self.pilot.galaxy, index)
        d = galaxy.distance(here, target)
        if target.index == here.index:
            return False, "You are already here"
        if d > self.pilot.fuel + 1e-6:
            return False, f"Needs {d:.1f} LY, you have {self.pilot.fuel:.1f}"
        if self.contacts and any(abs((c.pos - self.flight.pos).length()) < 2500
                                 for c in self.contacts):
            return False, "Mass locked"
        return True, f"{target.name}: {d:.1f} LY"

    def begin_jump(self, index):
        ok, msg = self.can_jump(index)
        if not ok:
            self.say(msg)
            return False
        target = galaxy.system(self.pilot.galaxy, index)
        d = galaxy.distance(self.system, target)
        self.jump = {"index": index, "left": 3.0, "cost": d,
                     "name": target.name}
        self.say(f"Hyperspace to {target.name} in 3...")
        return True

    def complete_jump(self, index, cost):
        self.pilot.fuel = round(max(0.0, self.pilot.fuel - cost), 1)
        self.pilot.system = index
        self.pilot.jumps += 1
        self.market = Market.for_system(self.system)
        self.flight = FlightModel(pos=Vec3(0.0, 0.0, -24000.0))
        self.contacts = []
        self.jump = None
        self.say(f"Arrived at {self.system.name}. Station bearing 000.")
        from . import combat
        combat.spawn(self, arrivals=True)

    # -- save/load -------------------------------------------------------
    def to_dict(self):
        return {"version": SAVE_VERSION, "seed": self.seed,
                "pilot": self.pilot.to_dict(),
                "flight": self.flight.to_dict(),
                "hull": self.hull, "shields": self.shields,
                "banks": self.banks, "mode": self.mode}

    def save(self, path=SAVE_PATH):
        write_json(path, self.to_dict())

    @classmethod
    def from_dict(cls, data):
        state = cls(data.get("seed"))
        state.pilot = Pilot.from_dict(data.get("pilot") or {})
        state.flight = FlightModel.from_dict(data.get("flight"))
        state.hull = float(data.get("hull", HULL))
        shields = data.get("shields") or {}
        state.shields = {"fore": float(shields.get("fore", MAX_SHIELD)),
                         "aft": float(shields.get("aft", MAX_SHIELD))}
        state.banks = [float(b) for b in (data.get("banks") or [BANK] * 4)]
        if len(state.banks) != 4:
            state.banks = [BANK] * 4
        state.mode = data.get("mode", "docked")
        state.market = Market.for_system(state.system)
        return state

    @classmethod
    def load(cls, path=SAVE_PATH):
        data = read_json(path)
        if not data or data.get("version") != SAVE_VERSION:
            return None
        try:
            return cls.from_dict(data)
        except (TypeError, ValueError, KeyError):
            return None


def read_json(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def write_json(path, payload):
    """Atomic write: a half-written save must never replace a good one."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1, sort_keys=True)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def load_profile(path=PROFILE_PATH):
    return Profile.from_dict(read_json(path))


def save_profile(profile, path=PROFILE_PATH):
    write_json(path, profile.to_dict())


def clear_save(path=SAVE_PATH):
    try:
        os.remove(path)
        return True
    except OSError:
        return False
