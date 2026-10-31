"""Mission contracts: the station board, accepted work, and its progress.

The rules live here, away from curses: the board is generated from the world
seed, accepted missions are stored on the pilot, and every state change goes
through a function that can be tested headlessly. Time is the simulation clock,
which only advances while the game is being flown.
"""

import math
import zlib
from dataclasses import asdict, dataclass, field

from . import galaxy
from .data import GOODS

KINDS = ("freight", "courier", "escort", "rescue", "bounty")
BOARD_SIZE = 4
REFRESH = 900.0            # seconds of flight time before a board refreshes
CANCEL_PENALTY = 0.15      # share of the fee kept on an abandoned contract


@dataclass
class Mission:
    mid: str
    kind: str
    title: str
    brief: str
    origin: str                     # "galaxy:index"
    dest: str | None                # "galaxy:index"
    pay: float
    deadline: float | None          # absolute simulation time, seconds
    accepted_at: float = 0.0
    state: str = "offered"          # offered | active | complete | failed
    cargo_key: str | None = None
    cargo_qty: int = 0
    target_name: str | None = None
    target_key: str | None = None
    threat: int = 0
    progress: dict = field(default_factory=dict)
    paid: bool = False
    reason: str = ""
    difficulty: int = 1

    # -- helpers ---------------------------------------------------------
    @property
    def dest_tuple(self):
        return parse_key(self.dest) if self.dest else None

    @property
    def dest_system(self):
        if not self.dest:
            return None
        g, i = parse_key(self.dest)
        return galaxy.system(g, i)

    def dest_name(self):
        s = self.dest_system
        return s.name if s else "-"

    def remaining(self, now):
        if self.deadline is None:
            return None
        return self.deadline - now

    def deadline_text(self, now):
        left = self.remaining(now)
        if left is None:
            return "no deadline"
        if left <= 0:
            return "expired"
        mins = int(left // 60)
        secs = int(left % 60)
        return f"{mins}m {secs:02d}s left"

    def expired(self, now):
        return self.deadline is not None and now > self.deadline

    def cargo_name(self):
        if not self.cargo_key:
            return ""
        from .data import GOOD_BY_KEY
        good = GOOD_BY_KEY.get(self.cargo_key)
        return good.name if good else self.cargo_key

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})


def parse_key(key):
    g, i = str(key).split(":")
    return int(g), int(i)


def make_key(galaxy_no, index):
    return f"{int(galaxy_no)}:{int(index)}"


def _rng(state, salt):
    base = zlib.crc32(f"{state.seed}:{salt}".encode())
    import random
    return random.Random(base)


# --------------------------------------------------------------- generation --

def _rank_tier(pilot):
    return min(4, pilot.kills // 64)


def _pick_destination(state, rng, min_ly=4.0, max_ly=26.0):
    here = state.system
    options = []
    for system in galaxy.galaxy(here.galaxy):
        if system.index == here.index:
            continue
        d = galaxy.distance(here, system)
        if min_ly <= d <= max_ly:
            options.append((d, system))
    if not options:
        return None, 0.0
    options.sort(key=lambda row: row[0])
    d, system = options[rng.randrange(len(options))]
    return system, d


def _new_mid(state, rng):
    return f"{state.seed % 100000:05d}-{rng.randrange(1 << 30):08x}"


def _freight(state, pilot, rng):
    dest, dist = _pick_destination(state, rng)
    if dest is None:
        return None
    stock = state.market.rows("buy")
    choices = [row for row in stock if row[3] > 0]
    if not choices:
        return None
    key, name, price, _ = choices[rng.randrange(len(choices))]
    room = max(4, min(12, pilot.cargo_cap // 2))
    qty = rng.randint(4, room)
    pay = round(14 * qty + 12 * dist + 20 * dest.danger + 5 * _rank_tier(pilot), 1)
    hours = 0.25 + dist / 60.0
    return Mission(
        mid=_new_mid(state, rng), kind="freight",
        title=f"Freight: {qty}t {name} to {dest.name}",
        brief=(f"Haul {qty} tonnes of {name} to {dest.name} station. The cargo "
               f"is loaded now and is reserved until delivery."),
        origin=make_key(state.pilot.galaxy, state.pilot.system),
        dest=make_key(dest.galaxy, dest.index),
        pay=pay, deadline=state.time + hours * 3600.0,
        cargo_key=key, cargo_qty=qty, threat=int(dest.danger * 3) + 1,
        difficulty=1 + int(dist // 8))


def _courier(state, pilot, rng):
    dest, dist = _pick_destination(state, rng, min_ly=3.0)
    if dest is None:
        return None
    pay = round(10 * dist + 20 + 4 * _rank_tier(pilot), 1)
    hours = 0.2 + dist / 90.0
    return Mission(
        mid=_new_mid(state, rng), kind="courier",
        title=f"Courier: sealed packet to {dest.name}",
        brief=f"Carry a sealed packet to {dest.name}. It takes no cargo space.",
        origin=make_key(state.pilot.galaxy, state.pilot.system),
        dest=make_key(dest.galaxy, dest.index),
        pay=pay, deadline=state.time + hours * 3600.0,
        threat=int(dest.danger * 2), difficulty=1 + int(dist // 10))


def _escort(state, pilot, rng):
    dest, dist = _pick_destination(state, rng, min_ly=4.0)
    if dest is None:
        return None
    pay = round(24 * dist + 60 + 8 * _rank_tier(pilot), 1)
    return Mission(
        mid=_new_mid(state, rng), kind="escort",
        title=f"Escort: trader to {dest.name}",
        brief=("A loaded trader needs an escort. Keep her alive until you dock "
               f"at {dest.name}."),
        origin=make_key(state.pilot.galaxy, state.pilot.system),
        dest=make_key(dest.galaxy, dest.index),
        pay=pay, deadline=state.time + (0.3 + dist / 50.0) * 3600.0,
        threat=2 + int(dest.danger * 4), difficulty=2 + int(dist // 8))


def _rescue(state, pilot, rng):
    dest, dist = _pick_destination(state, rng, min_ly=3.0)
    if dest is None:
        return None
    pay = round(30 * dist + 60 + 8 * _rank_tier(pilot), 1)
    return Mission(
        mid=_new_mid(state, rng), kind="rescue",
        title="Rescue: survivors adrift",
        brief=("A ship is breaking up in this system. Recover the survivors "
               f"(get within 100 m and press R), then take them to {dest.name}."),
        origin=make_key(state.pilot.galaxy, state.pilot.system),
        dest=make_key(dest.galaxy, dest.index),
        pay=pay, deadline=state.time + 900.0,
        threat=2, difficulty=2,
        progress={"recovered": 0})


def _bounty(state, pilot, rng):
    dest, dist = _pick_destination(state, rng, min_ly=3.0)
    if dest is None:
        return None
    from .ships import HUNTERS, PIRATES
    key = rng.choice(PIRATES + HUNTERS)
    name = "".join(rng.choice("BCDFGHJKLMNPQRSTVWZ") for _ in range(3))
    ship_name = key
    pay = round(70 + 18 * dist + 20 * _rank_tier(pilot), 1)
    return Mission(
        mid=_new_mid(state, rng), kind="bounty",
        title=f"Bounty: {name} in {dest.name}",
        brief=(f"{name}, a wanted {ship_name}, was seen in {dest.name}. "
               "Destroy the ship to collect."),
        origin=make_key(state.pilot.galaxy, state.pilot.system),
        dest=make_key(dest.galaxy, dest.index),
        pay=pay, deadline=state.time + 1800.0,
        target_name=name, target_key=key, threat=3,
        difficulty=3 + int(dist // 10))


_GENERATORS = {"freight": _freight, "courier": _courier, "escort": _escort,
               "rescue": _rescue, "bounty": _bounty}


# ------------------------------------------------------------------- board --

def ensure_board(state):
    """Generate (once) and persist the board for the current station."""
    key = make_key(state.pilot.galaxy, state.pilot.system)
    board = state.boards.get(key)
    if board and state.time < board.get("next", 0):
        return [Mission.from_dict(d) for d in board["offers"]]
    rng = _rng(state, f"board:{key}:{int(state.time // REFRESH)}")
    pilot = state.pilot
    count = 3 + min(2, _rank_tier(pilot))
    if pilot.cargo_cap >= 30:
        count += 1
    offers = []
    kinds = ["freight", "courier", "escort", "rescue", "bounty"]
    rng.shuffle(kinds)
    for kind in kinds[:count]:
        mission = _GENERATORS[kind](state, pilot, rng)
        if mission is not None and mission.dest != key:
            offers.append(mission)
    state.boards[key] = {"offers": [m.to_dict() for m in offers],
                         "next": state.time + REFRESH}
    return offers


def offers(state):
    return [m for m in ensure_board(state) if m.state == "offered"]


def _drop_offer(state, mission):
    key = make_key(state.pilot.galaxy, state.pilot.system)
    board = state.boards.get(key)
    if not board:
        return
    board["offers"] = [d for d in board["offers"]
                       if d.get("mid") != mission.mid]


# ---------------------------------------------------------------- contracts --

def accept(state, mission):
    """Take a contract. Returns (ok, message)."""
    pilot = state.pilot
    if mission.state != "offered":
        return False, "That contract is no longer on offer"
    if any(m.mid == mission.mid for m in state.missions):
        return False, "That contract is already yours"
    if mission.kind == "freight":
        if mission.cargo_qty > pilot.cargo_free():
            return False, (f"Needs {mission.cargo_qty}t of hold space; "
                           f"you have {pilot.cargo_free()}t free")
        pilot.add_cargo(mission.cargo_key, mission.cargo_qty)
        pilot.reserve(mission.cargo_key, mission.cargo_qty)
    mission.state = "active"
    mission.accepted_at = state.time
    state.missions.append(mission)
    _drop_offer(state, mission)
    state.say(f"Contract accepted: {mission.title}")
    return True, f"Accepted: {mission.title}"


def abandon(state, mission, reason="abandoned"):
    """Walk away. Reserved cargo is unloaded and a share of the fee is lost."""
    if mission.state != "active":
        return False, "That contract is not active"
    pilot = state.pilot
    if mission.cargo_key and mission.cargo_qty:
        pilot.remove_cargo(mission.cargo_key, mission.cargo_qty)
    mission.state = "failed"
    mission.reason = reason
    mission.paid = False
    state.missions.remove(mission)
    state.say(f"Contract failed: {mission.title} ({reason})")
    return True, f"Abandoned: {mission.title}"


def complete(state, mission, note=""):
    """Pay a contract exactly once, then retire it."""
    if mission.state != "active":
        return False, "That contract is not active"
    pilot = state.pilot
    if mission.cargo_key and mission.cargo_qty:
        pilot.remove_cargo(mission.cargo_key, mission.cargo_qty)
    if not mission.paid:
        pilot.credits = round(pilot.credits + mission.pay, 1)
        mission.paid = True
    mission.state = "complete"
    mission.reason = note or "delivered"
    if mission in state.missions:
        state.missions.remove(mission)
    state.completed.append(mission.mid)
    state.say(f"Contract complete: {mission.title} (+{mission.pay:.0f} CR)")
    return True, f"Paid {mission.pay:.0f} CR for {mission.title}"


def fail(state, mission, reason):
    if mission.state != "active":
        return False, "That contract is not active"
    pilot = state.pilot
    if mission.cargo_key and mission.cargo_qty:
        pilot.remove_cargo(mission.cargo_key, mission.cargo_qty)
    mission.state = "failed"
    mission.reason = reason
    if mission in state.missions:
        state.missions.remove(mission)
    state.say(f"Contract failed: {mission.title} - {reason}")
    return True, f"Failed: {mission.title} ({reason})"


# ------------------------------------------------------------------ spawns --

def spawn_contacts(state):
    """Put escort ships, distress beacons and wanted targets in the sky."""
    from . import combat
    from .flight import Vec3

    here = make_key(state.pilot.galaxy, state.pilot.system)
    for mission in active(state):
        if mission.kind == "escort" and mission.origin == here:
            if any(getattr(c, "mission", "") == mission.mid for c in state.contacts):
                continue
            contact = combat.make("ship", "python",
                                  state.flight.pos - state.flight.forward * 500
                                  + Vec3(120, 0, 0))
            contact.mission = mission.mid
            contact.tag = "escort"
            contact.hostile = False
            state.contacts.append(contact)
        elif mission.kind == "rescue" and mission.origin == here                 and not mission.progress.get("recovered"):
            if any(getattr(c, "mission", "") == mission.mid for c in state.contacts):
                continue
            spot = state.flight.pos + Vec3(2400, 600, 1800)
            contact = combat.make("cargo", "escape", spot)
            contact.mission = mission.mid
            contact.tag = "rescue"
            contact.energy = 5
            contact.shields = 0
            state.contacts.append(contact)
        elif mission.kind == "bounty" and mission.dest == here:
            if any(getattr(c, "mission", "") == mission.mid for c in state.contacts):
                continue
            spot = state.flight.pos + Vec3(-3000, 400, 4200)
            contact = combat.make("ship", mission.target_key or "cobra", spot,
                                  hostile=True)
            contact.mission = mission.mid
            contact.tag = "wanted"
            state.contacts.append(contact)
    return state.contacts


def recover(state):
    """Collect survivors from a rescue beacon within 100 m."""
    best = None
    for contact in state.contacts:
        if getattr(contact, "tag", "") != "rescue":
            continue
        dist = (contact.pos - state.flight.pos).length()
        if dist <= 100.0 and (best is None or dist < best[0]):
            best = (dist, contact)
    if best is None:
        # Say why, rather than failing silently.
        near = [c for c in state.contacts if getattr(c, "tag", "") == "rescue"]
        if near:
            dist = min((c.pos - state.flight.pos).length() for c in near)
            state.say(f"Survivors {dist:.0f} m away - get within 100 m")
        return False
    _, contact = best
    for mission in active(state):
        if mission.mid == contact.mission:
            mission.progress["recovered"] = 1
            state.say(f"Survivors recovered - take them to {mission.dest_name()}")
    state.contacts.remove(contact)
    return True


# ---------------------------------------------------------------- lifecycle --

def active(state):
    return [m for m in state.missions if m.state == "active"]


def active_for_dest(state, key):
    return [m for m in active(state) if m.dest == key]


def on_dock(state):
    """Resolve deliveries and returns when the player docks."""
    notes = []
    here = make_key(state.pilot.galaxy, state.pilot.system)
    for mission in list(active(state)):
        if mission.dest != here:
            continue
        if mission.kind in ("freight", "courier"):
            ok, msg = complete(state, mission, "delivered")
            if ok:
                notes.append(msg)
        elif mission.kind == "rescue":
            if mission.progress.get("recovered"):
                ok, msg = complete(state, mission, "survivors safe")
                if ok:
                    notes.append(msg)
            else:
                notes.append(f"{mission.title}: survivors still adrift")
        elif mission.kind == "escort":
            if mission.progress.get("escort_alive", 1):
                ok, msg = complete(state, mission, "trader delivered")
                if ok:
                    notes.append(msg)
            else:
                fail(state, mission, "the trader was lost")
    return notes


def on_jump(state):
    """Escorts travel with you; check deadlines on arrival."""
    for mission in list(active(state)):
        if mission.kind == "escort":
            if not mission.progress.get("escort_alive", 1):
                fail(state, mission, "the trader was lost")
    return check_deadlines(state)


def on_kill(state, contact):
    """A mission target destroyed: pay the bounty."""
    notes = []
    mid = getattr(contact, "mission", "")
    if not mid:
        return notes
    for mission in list(active(state)):
        if mission.mid != mid:
            continue
        mission.progress["killed"] = 1
        ok, msg = complete(state, mission, "target destroyed")
        if ok:
            notes.append(msg)
    return notes


def check_deadlines(state):
    notes = []
    for mission in list(active(state)):
        if mission.expired(state.time):
            fail(state, mission, "deadline passed")
            notes.append(f"{mission.title}: deadline passed")
    return notes


def step(state, dt):
    """Keep escorts alive and tracked while flying."""
    notes = check_deadlines(state)
    for mission in active(state):
        if mission.kind != "escort":
            continue
        escort = None
        for contact in state.contacts:
            if getattr(contact, "mission", "") == mission.mid:
                escort = contact
                break
        mission.progress["escort_alive"] = 1 if escort is not None else 0
    return notes


def progress(state, mission):
    """One line describing where the contract stands."""
    if mission.kind == "freight":
        return f"{mission.cargo_qty}t {mission.cargo_name()} for {mission.dest_name()}"
    if mission.kind == "courier":
        return f"packet for {mission.dest_name()}"
    if mission.kind == "escort":
        alive = mission.progress.get("escort_alive", 1)
        return f"trader {'alive' if alive else 'lost'} - dock at {mission.dest_name()}"
    if mission.kind == "rescue":
        if mission.progress.get("recovered"):
            return f"survivors aboard - dock at {mission.dest_name()}"
        return "recover survivors: get within 100 m and press R"
    if mission.kind == "bounty":
        return f"find and destroy {mission.target_name} in {mission.dest_name()}"
    return mission.brief


def summary(state):
    """(mid, title, progress, deadline) for the journal screen."""
    rows = []
    for mission in active(state):
        rows.append((mission.mid, mission.title, progress(state, mission),
                     mission.deadline_text(state.time)))
    return rows
