"""Contacts, ship AI, weapons and damage."""

import math
from dataclasses import dataclass, field

from .data import LASER_CONE, LASER_DAMAGE, LASER_RANGE, MASS_LOCK_RANGE
from .flight import Mat3, Vec3
from .ships import (HUNTERS, PIRATES, POLICE, SHIPS, TRADERS, TRAFFIC)


@dataclass
class Contact:
    kind: str
    type: object
    pos: Vec3
    orient: Mat3 = field(default_factory=Mat3.identity)
    vel: Vec3 = Vec3()
    shields: float = 1.0
    energy: float = 1.0
    hostile: bool = False
    state: str = "patrol"
    cooldown: float = 0.0
    age: float = 0.0
    cargo: str = ""
    flash: float = 0.0
    lock: bool = False
    mission: str = ""          # contract this contact belongs to
    tag: str = ""              # escort | rescue | wanted | jettison | player
    missiles: int = 0
    missile_cd: float = 0.0
    demand_until: float = 0.0
    demand_jettison: int = -1
    flagged: bool = False
    qty: int = 1

    @property
    def name(self):
        return self.type.name

    @property
    def size(self):
        return self.type.width

    @property
    def colour(self):
        return self.type.colour

    def alive(self):
        return self.energy > 0


def make(kind, key, pos, hostile=False, orient=None):
    t = SHIPS[key]
    rack = 0
    if kind == "ship":
        rack = {"pirate": 1, "police": 1, "hunter": 2, "alien": 2,
                "military": 1}.get(t.role, 0)
    return Contact(kind=kind, type=t, pos=pos, orient=orient or Mat3.identity(),
                   shields=t.shields, energy=t.energy, hostile=hostile,
                   cooldown=0.4, missiles=rack)


def _ring(rng, centre, radius, height=0.0):
    a = rng.uniform(0, 2 * math.pi)
    return Vec3(centre.x + math.cos(a) * radius,
                centre.y + height + rng.uniform(-radius * 0.15, radius * 0.15),
                centre.z + math.sin(a) * radius)


def spawn(state, arrivals=False):
    """Populate the current system with a plausible mix of traffic."""
    rng = state.rng
    system = state.system
    danger = system.danger
    created = []
    if arrivals:
        # A welcoming committee: pirates in lawless space, police elsewhere.
        roll = rng.random()
        if roll < danger * 0.55:
            for _ in range(rng.randint(1, 2)):
                key = rng.choice(PIRATES)
                created.append(make("ship", key, _ring(rng, state.flight.pos, rng.uniform(6000, 14000)), True))
        elif roll > 0.82 and system.government >= 4:
            key = rng.choice(POLICE)
            created.append(make("ship", key, _ring(rng, state.flight.pos, rng.uniform(8000, 16000))))
        else:
            key = rng.choice(TRAFFIC)
            created.append(make("ship", key, _ring(rng, state.station.pos, rng.uniform(3000, 9000))))
    else:
        # Lawful systems keep a bigger patrol out.
        if system.government >= 5 and rng.random() < 0.55:
            for _ in range(rng.randint(1, 2)):
                created.append(make("ship", rng.choice(POLICE),
                                    _ring(rng, state.station.pos,
                                          rng.uniform(3000, 9000))))
        for _ in range(rng.randint(0, 3)):
            roll = rng.random()
            if roll < danger * 0.6:
                created.append(make("ship", rng.choice(PIRATES),
                                    _ring(rng, state.flight.pos, rng.uniform(7000, 18000)), True))
            elif roll < 0.8:
                created.append(make("ship", rng.choice(TRADERS),
                                    _ring(rng, state.station.pos, rng.uniform(2000, 9000))))
            else:
                created.append(make("ship", rng.choice(HUNTERS),
                                    _ring(rng, state.flight.pos, rng.uniform(9000, 16000))))
    # An asteroid field lives near the sun.
    if state.flight.pos.length() > 0 and rng.random() < 0.25:
        for _ in range(rng.randint(1, 3)):
            created.append(make("asteroid", "asteroid",
                                _ring(rng, state.flight.pos, rng.uniform(3000, 9000))))
    state.contacts.extend(created)
    return created


def has_mass_lock(state):
    for c in state.contacts:
        if c.kind == "ship" and (c.pos - state.flight.pos).length() < MASS_LOCK_RANGE:
            return True
    return False


# ------------------------------------------------------------------ damage --

def energy_total(state):
    return sum(state.banks)


def drain(state, amount):
    left = amount
    for i in range(len(state.banks)):
        take = min(state.banks[i], left)
        state.banks[i] -= take
        left -= take
        if left <= 0:
            break
    return amount - left


def damage_player(state, amount, source_pos=None):
    """Shields, then energy banks, then hull. Fore or aft depends on bearing."""
    if amount <= 0:
        return
    if source_pos is None:
        side = "fore"
    else:
        bearing = state.flight.forward.dot(source_pos - state.flight.pos)
        side = "fore" if bearing >= 0 else "aft"
    shield = state.shields[side]
    if shield > 0:
        absorbed = min(shield, amount)
        state.shields[side] = round(shield - absorbed, 1)
        amount -= absorbed
    if amount > 0:
        state.banks = [round(b, 1) for b in state.banks]
        got = drain(state, amount)
        amount -= got
    if amount > 0:
        state.hull = round(state.hull - amount, 1)
        state.say("Hull breach!")
    if state.hull <= 0 and not state.dead:
        state.dead = True


def damage_contact(state, c, amount):
    """Shields first, then the hull: overflow must not be thrown away."""
    c.flash = 0.25
    if c.shields > 0:
        absorbed = min(c.shields, amount)
        c.shields = round(c.shields - absorbed, 1)
        amount -= absorbed
    if amount <= 0:
        return False
    c.energy = round(max(0.0, c.energy - amount), 1)
    if c.energy > 0:
        return False
    kill(state, c)
    return True


def kill(state, c):
    """Destroy a contact. Only warships and clean ships carry consequences."""
    if c in state.contacts:
        state.contacts.remove(c)
    role = c.type.role
    if role in ("rock", "cargo", "missile", "traffic"):
        state.say(f"{c.name} destroyed")
        _salvage_from(state, c)
        return
    bounty = c.type.bounty
    if c.hostile or role in ("pirate", "alien", "hunter"):
        state.pilot.kills += 1
        if bounty:
            state.pilot.credits = round(state.pilot.credits + bounty, 1)
            state.say(f"{c.name} destroyed. Bounty {bounty:.0f} CR")
        else:
            state.say(f"{c.name} destroyed")
    elif role in ("police", "military"):
        state.pilot.legal += 30
        state.say("You killed a police ship!")
    else:
        state.pilot.legal += 12
        state.say(f"{c.name} destroyed. That was a clean ship.")
    _salvage_from(state, c)
    from . import missions
    for note in missions.on_kill(state, c):
        state.say(note)


def _salvage_from(state, c):
    """Wrecks sometimes leave a canister behind."""
    if c.kind != "ship" or c.type.cargo <= 0 or c.tag == "escort":
        return
    if state.rng.random() > 0.6:
        return
    from .data import GOODS
    good = state.rng.choice(GOODS)
    can = make("cargo", "canister", c.pos + Vec3(state.rng.uniform(-30, 30),
                                                  state.rng.uniform(-30, 30),
                                                  state.rng.uniform(-30, 30)))
    can.cargo = good.key
    can.qty = state.rng.randint(1, max(1, c.type.cargo))
    can.tag = "salvage"
    state.contacts.append(can)


def jettison(state, key=None, qty=1):
    """Push cargo out of the hatch: the answer to a pirate demand."""
    pilot = state.pilot
    options = [(k, pilot.sellable(k)) for k in pilot.cargo if pilot.sellable(k) > 0]
    if not options:
        state.say("Nothing to jettison")
        return False, "Nothing to jettison"
    if key is None:
        key = max(options, key=lambda row: state.market.price(row[0]) * row[1])[0]
    qty = min(int(qty), pilot.sellable(key))
    if qty <= 0:
        return False, "That cargo is reserved"
    pilot.remove_cargo(key, qty)
    can = make("cargo", "canister", state.flight.pos - state.flight.forward * 70)
    can.cargo = key
    can.qty = qty
    can.tag = "jettison"
    state.contacts.append(can)
    state.jettison_count += 1
    from .data import GOOD_BY_KEY
    name = GOOD_BY_KEY[key].name if key in GOOD_BY_KEY else key
    state.say(f"Jettisoned {qty}t {name}")
    return True, f"Jettisoned {qty}t {name}"


def collect(state, canister):
    """Scoop a canister. Resolved before any collision damage."""
    pilot = state.pilot
    if canister.cooldown > 0:
        return False
    if not pilot.has("scoop"):
        canister.cooldown = 3.0
        state.say("Fuel scoops are needed to collect cargo")
        return False
    if state.flight.speed > SCOOP_SPEED:
        canister.cooldown = 1.5
        state.say(f"Too fast to scoop ({state.flight.speed:.0f} m/s)")
        return False
    if pilot.cargo_free() < canister.qty:
        canister.cooldown = 2.0
        state.say("Cargo hold full - cannot scoop")
        return False
    from .data import GOOD_BY_KEY
    key = canister.cargo or "food"
    pilot.add_cargo(key, canister.qty)
    if canister in state.contacts:
        state.contacts.remove(canister)
    name = GOOD_BY_KEY[key].name if key in GOOD_BY_KEY else key
    state.say(f"Scooped {canister.qty}t {name}")
    return True


# -------------------------------------------------------------------- fire --

def fire_laser(state):
    """Player laser. Returns the contact hit, or None."""
    if state.cool > 0:
        return None
    cost = 1.4
    if energy_total(state) < cost:
        state.say("Energy banks empty")
        return None
    drain(state, cost)
    state.cool = 0.26
    fwd = state.flight.forward
    pos = state.flight.pos
    best = None
    for c in state.contacts:
        rel = c.pos - pos
        d = rel.length()
        if d > LASER_RANGE or d < 40:
            continue
        ang = fwd.angle_to(rel)
        if ang <= LASER_CONE and (best is None or ang < best[0]):
            best = (ang, c, d)
    if best is None:
        return None
    _, c, d = best
    damage = LASER_DAMAGE[state.pilot.laser] * (1.0 - 0.55 * d / LASER_RANGE)
    damage_contact(state, c, damage)
    return c


def lock_target(state):
    fwd = state.flight.forward
    pos = state.flight.pos
    best = None
    for c in state.contacts:
        if c.kind != "ship":
            continue
        rel = c.pos - pos
        d = rel.length()
        if d > 16000:
            continue
        ang = fwd.angle_to(rel)
        if ang < 0.6 and (best is None or ang < best[0]):
            best = (ang, c)
    if best is None:
        state.say("No target in sight")
        state.missile_target = None
        return None
    state.missile_target = best[1]
    state.say(f"Missile locked: {best[1].name}")
    return best[1]


def fire_missile(state):
    if state.pilot.missiles <= 0:
        state.say("No missiles")
        return False
    target = state.missile_target
    if target is None or target not in state.contacts:
        state.say("No missile lock")
        return False
    state.pilot.missiles -= 1
    m = make("missile", "missile", state.flight.pos + state.flight.forward * 60,
             hostile=False, orient=state.flight.orient)
    m.energy = 25
    m.cooldown = 0.0
    m.lock = True
    m.cargo = id(target)
    state.contacts.append(m)
    state.missile_target = None
    state.say("Missile away")
    return True


def ecm(state):
    if not state.pilot.has("ecm"):
        state.say("No E.C.M. fitted")
        return False
    if energy_total(state) < 6:
        state.say("Not enough energy for E.C.M.")
        return False
    drain(state, 6)
    killed = 0
    for c in list(state.contacts):
        if c.kind == "missile":
            state.contacts.remove(c)
            killed += 1
    state.say(f"E.C.M. fired. {killed} missile(s) destroyed" if killed else "E.C.M. fired")
    return True


def energy_bomb(state):
    if not state.pilot.has("bomb"):
        state.say("No energy bomb fitted")
        return False
    state.pilot.equipment.discard("bomb")
    hit = 0
    for c in list(state.contacts):
        if c.kind in ("ship", "missile") and (c.pos - state.flight.pos).length() < 6000:
            kill(state, c)
            hit += 1
    state.say(f"Energy bomb: {hit} target(s) destroyed")
    return True


# ---------------------------------------------------------------------- AI --

SEE_RANGE = 14000.0
FIGHT_RANGE = 3500.0
DEMAND_RANGE = 1200.0
DEMAND_TIME = 9.0
SCAN_RANGE = 4000.0
SCAN_COOLDOWN = 25.0
MISSILE_RANGE = 7000.0
MISSILE_COOLDOWN = 26.0
SCOOP_RANGE = 60.0
SCOOP_SPEED = 250.0

ILEGAL_GOODS = ("slaves", "narcotics", "firearms", "alien")


def _steer(c, target, dt, rate):
    """Turn a ship towards a target using pitch and roll only.

    A pilot rolls first, until the target sits in the pitch plane, and only
    then pitches onto it; rolling and pitching at the same time just trades one
    angle for the other and the ship can stall short of the target. A target
    dead astern becomes a loop rather than an unreachable bearing. Every
    rotation is bounded by `rate` radians per second of simulated time, so NPCs
    and missiles turn at their own speed and never snap onto a target.
    """
    local = c.orient.t() @ (target - c.pos)
    dist = local.length()
    if dist < 1e-6 or dt <= 0 or rate <= 0:
        return
    d = local * (1.0 / dist)
    step = rate * dt

    def wrap(a):
        while a > math.pi:
            a -= 2 * math.pi
        while a < -math.pi:
            a += 2 * math.pi
        return a

    az_up = 0.0 if math.hypot(d.x, d.y) < 1e-9 else wrap(-math.atan2(d.x, d.y))
    az_down = wrap(az_up + math.pi)
    sign = getattr(c, "_steer_sign", 0)
    if sign == 0:
        sign = 1 if d.y >= 0 else -1
    # Prefer the branch that needs the least roll, but require a clear win: a
    # target near the roll plane would otherwise chatter between the two.
    here_cost = abs(az_up) if sign > 0 else abs(az_down)
    other_cost = abs(az_up) if sign < 0 else abs(az_down)
    if other_cost + 0.35 < here_cost:
        sign = -sign
    c._steer_sign = sign
    az = az_up if sign > 0 else az_down
    alpha = math.atan2(math.hypot(d.x, d.y), d.z)
    if abs(az) > 0.10:
        c.orient = (c.orient @ Mat3.rot_z(max(-step, min(step, az)))).renormalise()
    else:
        c.orient = (c.orient
                    @ Mat3.rot_x(-sign * max(-step, min(step, alpha)))).renormalise()


def _move(c, dt, scale=1.0):
    c.pos = c.pos + c.orient.forward * (c.type.speed * scale * dt)


def _move_towards(c, target, dt, scale=1.0):
    """Fly at `target`, easing off while the nose is still swinging round."""
    local = c.orient.t() @ (target - c.pos)
    if local.length() < 1e-6:
        return
    align = max(0.0, local.norm().z)
    _move(c, dt, scale * (0.12 + 0.88 * align))


def _patrol(state, c, dt):
    goal = state.station.pos + Vec3(math.cos(c.age * 0.2) * 2500,
                                    0.0, math.sin(c.age * 0.2) * 2500)
    _steer(c, goal, dt, c.type.turn * 0.5)
    _move(c, dt, 0.4)


def _shoot(state, c, dist, burst=0.9):
    if c.cooldown > 0 or dist > LASER_RANGE:
        return False
    if c.orient.forward.angle_to(state.flight.pos - c.pos) > 0.09:
        return False
    c.cooldown = burst
    damage_player(state, c.type.laser * 0.8, c.pos)
    return True


def _launch_missile(state, c, dist):
    """Telegraphed missile attack: the player gets time to use ECM."""
    if c.missiles <= 0 or c.missile_cd > 0:
        return False
    if dist < 900 or dist > MISSILE_RANGE:
        return False
    c.missiles -= 1
    c.missile_cd = MISSILE_COOLDOWN
    missile = make("missile", "missile", c.pos + c.orient.forward * 60,
                   orient=c.orient)
    missile.tag = "player"
    missile.energy = 30
    state.contacts.append(missile)
    state.say(f"INCOMING MISSILE from {c.name} - press E for ECM")
    return True


def _nearest_hostile(state, pos, radius):
    best = None
    for other in state.contacts:
        if not other.hostile or other.kind != "ship":
            continue
        d = (other.pos - pos).length()
        if d <= radius and (best is None or d < best[0]):
            best = (d, other)
    return best[1] if best else None


def _pirate(state, c, dt, dist):
    """Intercept, demand cargo, and only open fire when refused."""
    pilot = state.pilot
    prey = pilot.sellable() > 0

    # 1. Has the player paid up? Then go and pick the drop up.
    if c.state in ("demand", "collect") and not c.hostile:
        canister = None
        for other in state.contacts:
            if other.kind == "cargo" and other.tag == "jettison":
                if canister is None or ((other.pos - c.pos).length()
                                        < (canister.pos - c.pos).length()):
                    canister = other
        paid = state.jettison_count > c.demand_jettison
        if paid and canister is not None:
            c.state = "collect"
            _steer(c, canister.pos, dt, c.type.turn)
            _move_towards(c, canister.pos, dt, 0.9)
            if (canister.pos - c.pos).length() < 80:
                state.contacts.remove(canister)
                c.state = "patrol"
                c.demand_until = 0.0
                state.say(f"{c.name}: cargo received - breaking off")
            return
        if paid and canister is None:
            c.state = "patrol"
            return
        # 2. Still waiting: hold the standoff, then open fire.
        if state.time >= c.demand_until:
            c.state = "attack"
            c.hostile = True
            state.say(f"{c.name} opens fire - you did not comply")
        elif dist > 900:
            _steer(c, state.flight.pos, dt, c.type.turn * 0.7)
            _move_towards(c, state.flight.pos, dt, 0.6)
        return

    # 3. Look for prey.
    if not c.hostile:
        if dist > SEE_RANGE or not prey:
            _patrol(state, c, dt)
            return
        if dist <= DEMAND_RANGE:
            c.state = "demand"
            c.demand_until = state.time + DEMAND_TIME
            c.demand_jettison = state.jettison_count
            state.say(f"{c.name}: jettison cargo or be destroyed "
                      f"({DEMAND_TIME:.0f}s)")
            return
        _steer(c, state.flight.pos, dt, c.type.turn)
        _move_towards(c, state.flight.pos, dt, 1.0)
        return

    # 4. Fight.
    if dist > FIGHT_RANGE:
        _steer(c, state.flight.pos, dt, c.type.turn)
        _move_towards(c, state.flight.pos, dt, 1.0)
        return
    _steer(c, state.flight.pos, dt, c.type.turn)
    _move(c, dt, 0.75)
    _shoot(state, c, dist)
    _launch_missile(state, c, dist)


def _police(state, c, dt, dist):
    """Scan for contraband and hunt wanted pilots; nothing else is a crime."""
    pilot = state.pilot
    if pilot.legal >= 50 and dist < SEE_RANGE and not c.hostile:
        c.hostile = True
        state.say(f"{c.name}: fugitive on file - power down and submit")
    if c.hostile:
        if dist > FIGHT_RANGE:
            _steer(c, state.flight.pos, dt, c.type.turn)
            _move(c, dt, 1.0)
        else:
            _steer(c, state.flight.pos, dt, c.type.turn)
            _move(c, dt, 0.8)
            _shoot(state, c, dist)
            _launch_missile(state, c, dist)
        return
    if dist > SCAN_RANGE:
        _patrol(state, c, dt)
        return
    if c.cooldown <= 0:
        c.cooldown = SCAN_COOLDOWN
        if _contraband(pilot):
            c.flagged = True
            c.demand_until = state.time + 10.0
            c.demand_jettison = state.jettison_count
            state.say(f"{c.name}: contraband detected - jettison it or be fined")
        else:
            state.say(f"{c.name}: scan clean, carry on")
    if c.flagged:
        if state.jettison_count > getattr(c, "demand_jettison", -1):
            c.flagged = False
            c.demand_until = 0.0
            state.say("Contraband jettisoned - no charges")
        elif c.demand_until and state.time > c.demand_until:
            tonnes = sum(pilot.cargo.get(k, 0) for k in ILEGAL_GOODS)
            fine_amount = round(60 + 25 * tonnes, 1)
            pilot.intel["fines"] = round(pilot.intel.get("fines", 0.0)
                                         + fine_amount, 1)
            pilot.legal += 20
            for key in ILEGAL_GOODS:
                held = pilot.cargo.get(key, 0)
                if held:
                    pilot.remove_cargo(key, max(1, held // 2))
            c.flagged = False
            c.hostile = True
            state.say(f"Fined {fine_amount:.0f} CR, cargo seized, under fire")
    _steer(c, state.flight.pos, dt, c.type.turn * 0.4)
    _move(c, dt, 0.35)


def _trader(state, c, dt, dist):
    """Flee when threatened, call for help, and shed cargo to survive."""
    threat = _nearest_hostile(state, c.pos, 9000.0)
    hurt = c.energy < c.type.energy * 0.7
    if threat is not None or hurt:
        if not c.flagged:
            c.flagged = True
            c.state = "flee"
            state.say(f"{c.name}: mayday, mayday - under attack!")
        away = c.pos + (c.pos - (threat.pos if threat else state.flight.pos)).norm() * 6000
        _steer(c, away, dt, c.type.turn)
        _move_towards(c, away, dt, 1.0)
        if c.cooldown <= 0 and c.type.cargo:
            c.cooldown = 9.0
            can = make("cargo", "canister", c.pos - c.orient.forward * 70)
            can.cargo = "food"
            can.qty = 1
            can.tag = "salvage"
            state.contacts.append(can)
        return
    _patrol(state, c, dt)


def _hunter(state, c, dt, dist):
    """Bounty hunters only care about pilots with a record."""
    pilot = state.pilot
    if pilot.legal <= 0 and not c.hostile:
        _patrol(state, c, dt)
        return
    if not c.hostile:
        c.hostile = True
        state.say(f"{c.name}: your record precedes you, commander")
    if dist > FIGHT_RANGE:
        _steer(c, state.flight.pos, dt, c.type.turn)
        _move_towards(c, state.flight.pos, dt, 1.0)
        return
    _steer(c, state.flight.pos, dt, c.type.turn)
    _move(c, dt, 0.8)
    _shoot(state, c, dist)
    _launch_missile(state, c, dist)


def _escort(state, c, dt, dist):
    """Fly the player's wing and match their speed."""
    slot = state.flight.pos - state.flight.forward * 420
    _steer(c, slot, dt, c.type.turn * 0.8)
    gap = (c.pos - slot).length()
    speed = 0.9 if gap > 700 else (0.25 if gap > 150 else 0.15)
    _move(c, dt, speed)
    if dist < 3000:
        for other in state.contacts:
            if other.hostile and other.kind == "ship" and other is not c:
                if (other.pos - c.pos).length() < 2500:
                    _shoot(state, c, (other.pos - c.pos).length(), burst=1.2)
                break


def _contraband(pilot):
    return any(pilot.cargo.get(key, 0) > 0 for key in ILEGAL_GOODS)


def _ai_ship(state, c, dt, dist):
    role = c.type.role
    if c.tag == "escort":
        _escort(state, c, dt, dist)
    elif c.tag == "wanted" or role == "alien":
        if dist > FIGHT_RANGE:
            _steer(c, state.flight.pos, dt, c.type.turn)
            _move(c, dt, 1.0)
        else:
            _steer(c, state.flight.pos, dt, c.type.turn)
            _move(c, dt, 0.8)
            _shoot(state, c, dist)
            _launch_missile(state, c, dist)
    elif role == "pirate":
        _pirate(state, c, dt, dist)
    elif role in ("police", "military"):
        _police(state, c, dt, dist)
    elif role == "hunter":
        _hunter(state, c, dt, dist)
    elif role in ("trader", "traffic"):
        _trader(state, c, dt, dist)
    else:
        _move(c, dt, 0.2)


def _missile_step(state, m, dt):
    """Home on the player or on the ship that was locked when it was fired."""
    if m.tag == "player":
        aim = state.flight.pos
        _steer(m, aim, dt, 2.6)
        m.pos = m.pos + m.orient.forward * (m.type.speed * dt)
        if (m.pos - aim).length() < 90:
            damage_player(state, 85.0, m.pos)
            if m in state.contacts:
                state.contacts.remove(m)
            state.say("Missile hit - hull damage!")
        return
    target = None
    for c in state.contacts:
        if id(c) == m.cargo and c.kind in ("ship", "asteroid"):
            target = c
            break
    if target is None:
        m.energy -= 20 * dt
        m.pos = m.pos + m.orient.forward * (m.type.speed * dt)
        if m.energy <= 0 and m in state.contacts:
            state.contacts.remove(m)
        return
    _steer(m, target.pos, dt, 2.4)
    m.pos = m.pos + m.orient.forward * (m.type.speed * dt)
    if (m.pos - target.pos).length() < 90:
        damage_contact(state, target, 85)
        if m in state.contacts:
            state.contacts.remove(m)
        state.say("Missile hit")


def step(state, dt):
    """Advance the clock, every contact, and the bookkeeping."""
    state.time += dt
    state.cool = max(0.0, state.cool - dt)
    for m in list(state.messages):
        m[1] -= dt
        if m[1] <= 0:
            state.messages.remove(m)
    # Shield and bank regeneration.
    regen = 6.0 * (1.6 if state.pilot.has("energy") else 1.0)
    for side in ("fore", "aft"):
        if state.shields[side] < state.shield_max and energy_total(state) > 0:
            want = min(regen * dt, state.shield_max - state.shields[side])
            got = drain(state, want * 0.5)
            state.shields[side] = round(min(state.shield_max,
                                            state.shields[side] + got * 2), 1)
    # Banks recharge from the engine when nothing is shooting.
    spare = 2.5 * dt * (1.6 if state.pilot.has("energy") else 1.0)
    for i in range(len(state.banks)):
        if state.banks[i] < 25:
            room = 25 - state.banks[i]
            add = min(room, spare)
            state.banks[i] += add
            spare -= add
            if spare <= 0:
                break
    player = state.flight
    for c in list(state.contacts):
        c.age += dt
        c.cooldown = max(0.0, c.cooldown - dt)
        c.missile_cd = max(0.0, c.missile_cd - dt)
        c.flash = max(0.0, c.flash - dt)
        dist = (c.pos - player.pos).length()
        if c.kind == "missile":
            _missile_step(state, c, dt)
            continue
        if c.kind == "cargo" and dist < SCOOP_RANGE:
            collect(state, c)          # before any collision damage
            continue
        if c.kind == "ship":
            _ai_ship(state, c, dt, dist)
        else:
            c.pos = c.pos + c.orient.forward * (c.type.speed * dt)
        if c.kind != "missile" and dist < 60 + c.size * 0.5                 and c.state not in ("demand", "collect"):
            damage_player(state, 20.0, c.pos)
            if c.kind == "asteroid":
                damage_contact(state, c, 30)
        if c in state.contacts and dist > 45000:
            state.contacts.remove(c)
    # Sun skimming: fuel in exchange for heat.
    sun_dist = (player.pos - state.sun).length()
    if sun_dist < 16000 and state.pilot.has("scoop"):
        gain = 0.6 * dt
        state.pilot.fuel = round(min(7.0, state.pilot.fuel + gain), 2)
        if sun_dist < 9000:
            damage_player(state, 14.0 * dt)
