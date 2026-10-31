"""Game state: the pilot, the ship, encounters, docking and save files."""

import json
import os
import random
from dataclasses import dataclass, field

from . import galaxy
from . import economy
from . import missions as mission_mod
from .data import MAX_FUEL, START_CREDITS, legal_for, rank_for
from .ships import LARGE_BAY_BONUS, PLAYER_SHIPS, player_ship
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
    equipment: set = field(default_factory=set)
    missiles: int = 3
    kills: int = 0
    legal: int = 0
    galaxy: int = 1
    system: int = START_INDEX
    badges: list = field(default_factory=list)
    deaths: int = 0
    jumps: int = 0
    ship: str = "cobra"
    costs: dict = field(default_factory=dict)       # cost basis per good
    reserved: dict = field(default_factory=dict)    # mission cargo, not sellable
    trade_profit: float = 0.0
    missions: list = field(default_factory=list)    # mission state (see missions.py)
    visited: list = field(default_factory=list)     # "galaxy:index" keys
    tutorial: dict = field(default_factory=dict)
    intel: dict = field(default_factory=dict)       # fines, scans, reputation

    # -- hull ------------------------------------------------------------
    @property
    def ship_cfg(self):
        return player_ship(self.ship)

    @property
    def ship_name(self):
        return self.ship_cfg.name

    @property
    def hull_max(self):
        return self.ship_cfg.hull

    @property
    def shield_max(self):
        return self.ship_cfg.shields

    @property
    def max_missiles(self):
        return self.ship_cfg.missiles

    @property
    def slots(self):
        return self.ship_cfg.slots

    @property
    def cargo_cap(self):
        bonus = LARGE_BAY_BONUS if "largebay" in self.equipment else 0
        return self.ship_cfg.cargo + bonus

    # -- cargo -----------------------------------------------------------
    def cargo_used(self):
        return sum(self.cargo.values())

    def cargo_free(self):
        return max(0, self.cargo_cap - self.cargo_used())

    def sellable(self, key=None):
        """Tonnes that are not reserved for a mission."""
        if key is None:
            return sum(max(0, q - self.reserved.get(k, 0))
                       for k, q in self.cargo.items())
        return max(0, self.cargo.get(key, 0) - self.reserved.get(key, 0))

    def add_cargo(self, key, qty):
        if qty <= 0:
            return
        self.cargo[key] = self.cargo.get(key, 0) + int(qty)

    def remove_cargo(self, key, qty):
        """Take cargo out of the hold, returning the cost basis removed."""
        qty = int(qty)
        have = self.cargo.get(key, 0)
        if qty <= 0 or have <= 0:
            return 0.0
        qty = min(qty, have)
        basis = self.cost_basis(key, qty)
        left = have - qty
        if left > 0:
            self.cargo[key] = left
        else:
            self.cargo.pop(key, None)
            self.costs.pop(key, None)
        held = self.reserved.get(key, 0)
        if held:
            if held - qty > 0:
                self.reserved[key] = held - qty
            else:
                self.reserved.pop(key, None)
        return basis

    # -- cost basis ------------------------------------------------------
    def add_cost(self, key, amount):
        self.costs[key] = round(self.costs.get(key, 0.0) + amount, 2)

    def cost_basis(self, key, qty):
        """Cost of `qty` tonnes at the average price paid for the holding."""
        have = self.cargo.get(key, 0)
        total = self.costs.get(key, 0.0)
        if have <= 0 or total <= 0 or qty <= 0:
            return 0.0
        qty = min(qty, have)
        basis = round(total * qty / have, 2)
        left = round(total - basis, 2)
        if left > 0:
            self.costs[key] = left
        else:
            self.costs.pop(key, None)
        return basis

    def reserve(self, key, qty):
        if qty > 0:
            self.reserved[key] = self.reserved.get(key, 0) + int(qty)

    def release(self, key, qty):
        left = self.reserved.get(key, 0) - int(qty)
        if left > 0:
            self.reserved[key] = left
        else:
            self.reserved.pop(key, None)

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

    def visit(self, galaxy_no, index):
        """Record a new system; returns True the first time it is seen."""
        key = f"{galaxy_no}:{index}"
        if key in self.visited:
            return False
        self.visited.append(key)
        return True

    # -- persistence -----------------------------------------------------
    def to_dict(self):
        return {"name": self.name, "credits": self.credits, "fuel": self.fuel,
                "cargo": self.cargo, "equipment": sorted(self.equipment),
                "missiles": self.missiles, "kills": self.kills,
                "legal": self.legal, "galaxy": self.galaxy,
                "system": self.system, "badges": self.badges,
                "deaths": self.deaths, "jumps": self.jumps,
                "ship": self.ship, "costs": self.costs,
                "reserved": self.reserved, "trade_profit": self.trade_profit,
                "missions": self.missions, "visited": self.visited,
                "tutorial": self.tutorial, "intel": self.intel}

    @classmethod
    def from_dict(cls, data):
        p = cls()
        for key in ("name", "credits", "fuel", "missiles", "kills", "legal",
                    "galaxy", "system", "deaths", "jumps", "ship",
                    "trade_profit"):
            if key in data:
                setattr(p, key, data[key])
        if p.ship not in PLAYER_SHIPS:
            p.ship = "cobra"
        p.cargo = {k: int(v) for k, v in (data.get("cargo") or {}).items() if v}
        p.equipment = set(data.get("equipment") or [])
        p.badges = list(data.get("badges") or [])
        p.costs = {k: float(v) for k, v in (data.get("costs") or {}).items()}
        p.reserved = {k: int(v) for k, v in (data.get("reserved") or {}).items() if v}
        p.missions = list(data.get("missions") or [])
        p.visited = list(data.get("visited") or [])
        p.tutorial = dict(data.get("tutorial") or {})
        p.intel = dict(data.get("intel") or {})
        # A version-1 save has no ship: it was always the Cobra.
        if "ship" not in data:
            p.ship = "cobra"
        if not p.costs and p.cargo:
            p.costs = {}
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
        self.flight = FlightModel().apply_ship(self.pilot.ship_cfg)
        self.station = Station(Vec3(0.0, 0.0, 0.0))
        self.sun = Vec3(60000.0, 24000.0, -42000.0)
        self.planet = Vec3(-70000.0, -18000.0, -90000.0)
        self.contacts = []
        self.messages = []
        self.mode = "flight"
        self.docking = False
        self.jump = None
        self.time = 0.0
        self.last_shot = 0.0
        self.hull = self.pilot.hull_max
        self.shields = {"fore": self.pilot.shield_max,
                        "aft": self.pilot.shield_max}
        self.banks = [BANK] * 4
        self.cool = 0.0
        self.missile_target = None
        self.dead = False
        self.docked_at = None
        self.missions = []      # Mission objects, alive for this run
        self.markets = {}       # "g:i" -> Market, kept between visits
        self.events = {}        # "g:i" -> EventRecord, kept between visits
        self.boards = {}        # "g:i" -> {offers, next}
        self.completed = []     # mission ids already paid
        self.jettison_count = 0  # how many times the hatch has been used

    # -- system ----------------------------------------------------------
    @property
    def system(self):
        return galaxy.system(self.pilot.galaxy, self.pilot.system)

    @property
    def market(self):
        return self.market_for(self.system)

    def market_for(self, system=None):
        """The market of a system, with its events, kept in one place."""
        system = system or self.system
        key = f"{system.galaxy}:{system.index}"
        market = self.markets.get(key)
        if market is None or not market.events and self.events.get(key):
            market = market or Market.for_system(system)
            events, record = economy.merge(self.seed, system.galaxy,
                                           system.index, self.time,
                                           self.events.get(key))
            self.events[key] = record
            market.set_events(events)
            self.markets[key] = market
        return market

    def tick_markets(self, dt):
        for market in self.markets.values():
            market.decay(dt)

    def step(self, dt):
        """Advance the whole simulation by one tick."""
        from . import combat, missions as missions_mod
        combat.step(self, dt)
        self.tick_markets(dt)
        return missions_mod.step(self, dt)

    @property
    def hull_max(self):
        return self.pilot.hull_max

    @property
    def shield_max(self):
        return self.pilot.shield_max

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
        self.flight = FlightModel(pos=Vec3(0.0, 0.0, -6000.0)).apply_ship(
            self.pilot.ship_cfg)
        self.docked_at = None
        self.mode = "flight"
        self.hull = max(self.hull, 1.0)
        self.say("Launch. Fly toward the station slot to dock.")
        mission_mod.spawn_contacts(self)

    def dock(self):
        self.mode = "docked"
        self.docking = False
        self.contacts = []
        self.docked_at = self.system
        self.jump = None
        self.pilot.system = self.system.index
        self.say(f"Docked at {self.system.name} station.")
        fines = float(self.pilot.intel.get("fines", 0.0) or 0.0)
        if fines > 0:
            paid = min(fines, max(0.0, self.pilot.credits))
            self.pilot.credits = round(self.pilot.credits - paid, 1)
            self.pilot.intel["fines"] = round(fines - paid, 1)
            self.say(f"Fines of {paid:.0f} CR collected"
                     + (" - the rest is still owed"
                        if fines - paid > 0 else ""))
        for note in mission_mod.on_dock(self):
            self.say(note)

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
        self.flight = FlightModel(pos=Vec3(0.0, 0.0, -24000.0)).apply_ship(
            self.pilot.ship_cfg)
        self.contacts = []
        self.jump = None
        self.say(f"Arrived at {self.system.name}. Station bearing 000.")
        for note in mission_mod.on_jump(self):
            self.say(note)
        from . import combat
        combat.spawn(self, arrivals=True)
        mission_mod.spawn_contacts(self)

    # -- save/load -------------------------------------------------------
    def to_dict(self):
        return {"version": SAVE_VERSION, "seed": self.seed,
                "pilot": self.pilot.to_dict(),
                "flight": self.flight.to_dict(),
                "hull": self.hull, "shields": self.shields,
                "banks": self.banks, "mode": self.mode,
                "time": self.time,
                "missions": [m.to_dict() for m in self.missions],
                "boards": self.boards, "completed": self.completed,
                "jettison_count": self.jettison_count,
                "markets": {key: m.to_dict() for key, m in self.markets.items()},
                "events": {key: rec.to_dict() for key, rec in self.events.items()}}

    def save(self, path=SAVE_PATH):
        write_json(path, self.to_dict())

    def apply_ship(self, repair=True):
        """Re-fit the flight model and the hull limits to the current ship."""
        cfg = self.pilot.ship_cfg
        self.flight.apply_ship(cfg)
        self.hull = self.hull_max if repair else min(self.hull, self.hull_max)
        self.shields = {"fore": self.shield_max, "aft": self.shield_max}
        self.pilot.missiles = min(self.pilot.missiles, cfg.missiles)

    def save_after_trade(self):
        """Keep the on-disk save in step after a station transaction."""
        if self.mode != "docked":
            return False
        self.pilot.system = self.system.index
        try:
            self.save()
        except OSError:
            return False
        return True

    @classmethod
    def from_dict(cls, data):
        state = cls(data.get("seed"))
        state.pilot = Pilot.from_dict(data.get("pilot") or {})
        state.flight = FlightModel.from_dict(data.get("flight")).apply_ship(
            state.pilot.ship_cfg)
        state.hull = float(data.get("hull", HULL))
        shields = data.get("shields") or {}
        state.shields = {"fore": float(shields.get("fore", MAX_SHIELD)),
                         "aft": float(shields.get("aft", MAX_SHIELD))}
        state.banks = [float(b) for b in (data.get("banks") or [BANK] * 4)]
        if len(state.banks) != 4:
            state.banks = [BANK] * 4
        state.mode = data.get("mode", "docked")
        state.time = float(data.get("time", 0.0))
        state.missions = [mission_mod.Mission.from_dict(d)
                          for d in (data.get("missions") or [])]
        state.boards = dict(data.get("boards") or {})
        state.completed = list(data.get("completed") or [])
        state.jettison_count = int(data.get("jettison_count", 0))
        state.markets = {
            key: Market.from_dict(galaxy.system(*[int(x) for x in key.split(":")]),
                                  payload)
            for key, payload in (data.get("markets") or {}).items()}
        state.events = {key: economy.EventRecord.from_dict(payload)
                        for key, payload in (data.get("events") or {}).items()}
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
    """Atomic write: a half-written save must never replace a good one.

    The temporary file is unique per process, so two copies of the game (or a
    screenshot run next to a real session) cannot clobber each other's save.
    """
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    tmp = f"{path}.{os.getpid()}.tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=1, sort_keys=True)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass


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
