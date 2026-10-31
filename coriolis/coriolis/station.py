"""The Coriolis station: geometry, docking rules and station services."""

import math

from .data import (EQUIPMENT, EQUIPMENT_BY_KEY, FUEL_PRICE, MAX_FUEL,
                   MAX_MISSILES)
from .flight import Vec3

RADIUS = 420.0
SLOT_HALF_WIDTH = 60.0
DOCK_SPEED = 320.0
DOCK_ROLL = math.radians(28.0)
DOCK_LATERAL = 55.0
DOCK_AXIAL = 140.0


class Station:
    """A spinning Coriolis. The docking slot faces the arrival point (-z)."""

    def __init__(self, pos=None, angle=0.0):
        self.pos = pos or Vec3(0.0, 0.0, 0.0)
        self.angle = angle
        self.spin = 0.42
        self.radius = RADIUS
        self.axis = Vec3(0.0, 0.0, -1.0)   # outward normal of the slot face

    def step(self, dt):
        self.angle = (self.angle + self.spin * dt) % (2 * math.pi)

    # -- geometry ---------------------------------------------------------
    def relative(self, pos):
        rel = pos - self.pos
        axial = rel.dot(self.axis)
        lateral_sq = max(0.0, rel.dot(rel) - axial * axial)
        return rel, axial, math.sqrt(lateral_sq)

    def slot_vector(self):
        """The station's 'up' in the slot plane, rotated by the spin."""
        u = Vec3(0.0, 1.0, 0.0)
        c, s = math.cos(self.angle), math.sin(self.angle)
        return Vec3(u.x * c - u.y * s, u.x * s + u.y * c, 0.0)

    def roll_error(self, ship_up):
        slot_up = self.slot_vector()
        flat = Vec3(ship_up.x, ship_up.y, 0.0)
        if flat.length() < 1e-6:
            return math.pi / 2
        return flat.angle_to(slot_up)

    def dock_check(self, flight):
        """Return (status, text) where status is dock/crash/wait."""
        rel, axial, lateral = self.relative(flight.pos)
        dist = rel.length()
        if axial < -self.radius * 0.5:
            return "crash", "You flew into the station's hull"
        if axial < 0:
            return "wait", "You are behind the station - turn around"
        if dist < self.radius * 0.75 and lateral > SLOT_HALF_WIDTH:
            return "crash", "The hull fills your view"
        if lateral > SLOT_HALF_WIDTH:
            return "wait", f"Lateral {lateral:.0f}m off the slot"
        if axial > DOCK_AXIAL:
            return "wait", f"Slot {axial - DOCK_AXIAL:.0f}m ahead"
        if flight.speed > DOCK_SPEED:
            return "wait", f"Too fast ({flight.speed:.0f} m/s)"
        err = self.roll_error(flight.orient.up)
        if err > DOCK_ROLL:
            return "wait", f"Roll {math.degrees(err):.0f} deg off the slot"
        return "dock", "Docking clamps engaged"

    def distance(self, pos):
        return (pos - self.pos).length()


# -- station services ------------------------------------------------------

def fuel_price(missing):
    return round(missing * FUEL_PRICE, 1)


def refuel(pilot):
    missing = MAX_FUEL - pilot.fuel
    if missing <= 0.05:
        return False, "Tanks are full"
    cost = fuel_price(missing)
    if pilot.credits < cost:
        return False, "Not enough credits"
    pilot.credits = round(pilot.credits - cost, 1)
    pilot.fuel = MAX_FUEL
    return True, f"Refuelled to {MAX_FUEL:.1f} LY for {cost:.1f} CR"


def repair(pilot, damage):
    """damage: points of hull/shield damage still on the ship."""
    if damage <= 0:
        return False, "Nothing to repair"
    cost = round(damage * 1.5, 1)
    if pilot.credits < cost:
        return False, f"Repairs cost {cost:.1f} CR"
    pilot.credits = round(pilot.credits - cost, 1)
    return True, f"Repaired for {cost:.1f} CR"


def fine(pilot):
    """Clear an offender/fugitive record."""
    if pilot.legal <= 0:
        return False, "You have a clean record"
    cost = round(120.0 * pilot.legal, 1)
    if pilot.credits < cost:
        return False, f"Fine is {cost:.1f} CR"
    pilot.credits = round(pilot.credits - cost, 1)
    pilot.legal = 0
    return True, f"Record cleared for {cost:.1f} CR"


def available(pilot, item, tech):
    return why_not(pilot, item, tech) == ""


def buy(pilot, key, tech):
    item = EQUIPMENT_BY_KEY[key]
    if not available(pilot, item, tech):
        return False, f"{item.name} is not available here"
    if pilot.credits < item.price:
        return False, f"{item.name} costs {item.price:.0f} CR"
    pilot.credits = round(pilot.credits - item.price, 1)
    if key == "missile":
        pilot.missiles = min(pilot.max_missiles, pilot.missiles + 1)
    elif key in ("beam", "military"):
        pilot.equipment.discard("beam")
        pilot.equipment.discard("military")
        pilot.equipment.add(key)
    else:
        pilot.equipment.add(key)
    return True, f"Bought {item.name} for {item.price:.0f} CR"


def equipment_rows(pilot, tech):
    """(key, name, price, note, why) for the shop screen."""
    rows = []
    for item in EQUIPMENT:
        why = why_not(pilot, item, tech)
        rows.append((item.key, item.name, item.price, item.desc, why))
    return rows


# -- shipyard --------------------------------------------------------------

SHIPYARD_TECH = 4          # only the better yards sell hulls
MISSILE_RESALE = 0.5


def has_shipyard(system):
    return system.tech >= SHIPYARD_TECH


def trade_in_value(pilot):
    from .ships import TRADE_IN, player_ship
    return round(player_ship(pilot.ship).price * TRADE_IN, 1)


def shipyard_rows(pilot):
    """(key, cfg, trade_in, cost, can_buy, why) for every hull on the lot."""
    from .ships import PLAYER_SHIPS, SHIP_ORDER
    rows = []
    trade = trade_in_value(pilot)
    for key in SHIP_ORDER:
        cfg = PLAYER_SHIPS[key]
        own = key == pilot.ship
        cost = round(max(0.0, cfg.price - (0 if own else trade)), 1)
        ok, why = can_buy_ship(pilot, key)
        rows.append((key, cfg, 0 if own else trade, cost, ok, why))
    return rows


def can_buy_ship(pilot, key):
    """Validate a purchase against cargo, equipment, missiles and credits."""
    from .ships import PLAYER_SHIPS, LARGE_BAY_BONUS, TRADE_IN, player_ship
    cfg = PLAYER_SHIPS.get(key)
    if cfg is None:
        return False, "No such ship"
    if key == pilot.ship:
        return False, "You already fly one of these"
    cost = round(max(0.0, cfg.price - player_ship(pilot.ship).price * TRADE_IN), 1)
    if cost > pilot.credits + 1e-9:
        return False, f"Needs {cost:.0f} CR"
    capacity = cfg.cargo + (LARGE_BAY_BONUS if "largebay" in pilot.equipment else 0)
    if pilot.cargo_used() > capacity:
        return False, (f"Hold too small: {pilot.cargo_used()}t aboard, "
                       f"{capacity}t capacity")
    if len(pilot.equipment) > cfg.slots:
        return False, (f"{cfg.slots} equipment slots; you carry "
                       f"{len(pilot.equipment)} items")
    if pilot.missiles > cfg.missiles:
        return False, (f"{cfg.name} carries {cfg.missiles} missiles; "
                       f"sell {pilot.missiles - cfg.missiles} first")
    return True, ""


def buy_ship(pilot, key):
    """Trade the current hull in against a new one."""
    from .ships import PLAYER_SHIPS, TRADE_IN, player_ship
    ok, why = can_buy_ship(pilot, key)
    if not ok:
        return False, why
    cfg = PLAYER_SHIPS[key]
    cost = round(max(0.0, cfg.price - player_ship(pilot.ship).price * TRADE_IN), 1)
    pilot.credits = round(pilot.credits - cost, 1)
    pilot.ship = key
    pilot.missiles = min(pilot.missiles, cfg.missiles)
    if cost <= 0:
        return True, (f"Traded for a {cfg.name}; the old hull covered it "
                      "and no change was given")
    return True, f"Bought a {cfg.name} for {cost:.0f} CR (trade-in included)"


def sell_missile(pilot):
    from .data import EQUIPMENT_BY_KEY
    if pilot.missiles <= 0:
        return False, "No missiles to sell"
    refund = round(EQUIPMENT_BY_KEY["missile"].price * MISSILE_RESALE, 1)
    pilot.missiles -= 1
    pilot.credits = round(pilot.credits + refund, 1)
    return True, f"Sold a missile for {refund:.0f} CR"


def sell_equipment(pilot, key):
    """Cash in a fitted item at half price (never the one you are using)."""
    item = EQUIPMENT_BY_KEY.get(key)
    if item is None or key not in pilot.equipment:
        return False, "Not fitted"
    refund = round(item.price * MISSILE_RESALE, 1)
    pilot.equipment.discard(key)
    if key == "largebay" and pilot.cargo_used() > pilot.cargo_cap:
        pilot.equipment.add(key)
        return False, "Cargo would not fit without the bay"
    pilot.credits = round(pilot.credits + refund, 1)
    return True, f"Sold {item.name} for {refund:.0f} CR"


def why_not(pilot, item, tech):
    """Explain why an item is not on the shelf."""
    if item.tech > tech:
        return f"needs tech {item.tech}"
    if item.key == "missile":
        return "racks are full" if pilot.missiles >= pilot.max_missiles else ""
    if item.key == "largebay":
        return "already fitted" if "largebay" in pilot.equipment else ""
    if item.key in ("beam", "military"):
        order = {"pulse": 0, "beam": 1, "military": 2}
        if order[item.key] <= order[pilot.laser]:
            return "you have this laser or better"
        return ""
    if item.key in pilot.equipment:
        return "already fitted"
    if len(pilot.equipment) >= pilot.slots:
        return f"all {pilot.slots} slots used"
    return ""
