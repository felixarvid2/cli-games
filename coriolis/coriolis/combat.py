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
    return Contact(kind=kind, type=t, pos=pos, orient=orient or Mat3.identity(),
                   shields=t.shields, energy=t.energy, hostile=hostile,
                   cooldown=0.4)


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
    state.contacts.remove(c)
    bounty = c.type.bounty
    if c.hostile or c.type.role in ("pirate", "alien", "hunter"):
        state.pilot.kills += 1
        if bounty:
            state.pilot.credits = round(state.pilot.credits + bounty, 1)
            state.say(f"{c.name} destroyed. Bounty {bounty:.0f} CR")
        else:
            state.say(f"{c.name} destroyed")
    elif c.type.role in ("police", "military"):
        state.pilot.legal += 30
        state.say("You killed a police ship!")
    else:
        state.pilot.legal += 12
        state.say(f"{c.name} destroyed. That was a clean ship.")


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
    if abs(az_up if -sign > 0 else az_down) + 0.35 < abs(az_up if sign > 0 else az_down):
        sign = -sign
    c._steer_sign = sign
    az = az_up if sign > 0 else az_down
    alpha = math.atan2(math.hypot(d.x, d.y), d.z)
    if abs(az) > 0.10:
        c.orient = (c.orient @ Mat3.rot_z(max(-step, min(step, az)))).renormalise()
    else:
        c.orient = (c.orient
                    @ Mat3.rot_x(-sign * max(-step, min(step, alpha)))).renormalise()


def _ai_ship(state, c, dt, dist):
    player = state.flight
    t = c.type
    if c.hostile:
        if dist > 2200:
            c.state = "pursue"
        elif dist < 380:
            c.state = "evade"
        else:
            c.state = "attack"
        if c.state == "evade":
            away = c.pos + (c.pos - player.pos).norm() * 4000
            _steer(c, away, dt, t.turn)
        else:
            _steer(c, player.pos, dt, t.turn)
        speed = t.speed * (1.0 if c.state != "evade" else 0.85)
        c.pos = c.pos + c.orient.forward * (speed * dt)
        if (c.state == "attack" and dist < LASER_RANGE
                and c.orient.forward.angle_to(player.pos - c.pos) < 0.09
                and c.cooldown <= 0):
            c.cooldown = 0.9
            damage_player(state, t.laser * 0.8, c.pos)
    else:
        # Traders and police fly a lazy circuit around the station.
        goal = state.station.pos + Vec3(math.cos(c.age * 0.2) * 2500,
                                        0.0, math.sin(c.age * 0.2) * 2500)
        _steer(c, goal, dt, t.turn * 0.5)
        c.pos = c.pos + c.orient.forward * (t.speed * 0.4 * dt)


def _missile_step(state, m, dt):
    target = None
    for c in state.contacts:
        if id(c) == m.cargo and c.kind in ("ship", "asteroid"):
            target = c
            break
    if target is None:
        m.energy -= 20 * dt
        m.pos = m.pos + m.orient.forward * (m.type.speed * dt)
        if m.energy <= 0:
            state.contacts.remove(m)
        return
    _steer(m, target.pos, dt, 2.4)
    m.pos = m.pos + m.orient.forward * (m.type.speed * dt)
    if (m.pos - target.pos).length() < 90:
        damage_contact(state, target, 85)
        state.contacts.remove(m)
        state.say("Missile hit")


def step(state, dt):
    """Advance every contact, resolve specials, age the bookkeeping."""
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
        c.flash = max(0.0, c.flash - dt)
        dist = (c.pos - player.pos).length()
        if c.kind == "missile":
            _missile_step(state, c, dt)
        elif c.kind == "ship":
            _ai_ship(state, c, dt, dist)
        else:
            c.pos = c.pos + c.orient.forward * (c.type.speed * dt)
        if c.kind != "missile" and dist < 60 + c.size * 0.5:
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
