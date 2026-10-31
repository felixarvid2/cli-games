"""The Coriolis station: geometry, docking rules and station services."""

import math

from .data import (CARGO_LARGE, EQUIPMENT, EQUIPMENT_BY_KEY, FUEL_PRICE,
                   MAX_FUEL, MAX_MISSILES)
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
    if item.tech > tech:
        return False
    if item.key in ("missile",):
        return pilot.missiles < MAX_MISSILES
    if item.key in ("largebay",):
        return pilot.cargo_cap < CARGO_LARGE
    if item.key in ("beam", "military"):
        tier = pilot.laser
        order = {"pulse": 0, "beam": 1, "military": 2}
        return order[item.key] > order[tier]
    return item.key not in pilot.equipment


def buy(pilot, key, tech):
    item = EQUIPMENT_BY_KEY[key]
    if not available(pilot, item, tech):
        return False, f"{item.name} is not available here"
    if pilot.credits < item.price:
        return False, f"{item.name} costs {item.price:.0f} CR"
    pilot.credits = round(pilot.credits - item.price, 1)
    if key == "missile":
        pilot.missiles = min(MAX_MISSILES, pilot.missiles + 1)
    elif key == "largebay":
        pilot.cargo_cap = CARGO_LARGE
    elif key in ("beam", "military"):
        pilot.equipment.discard("beam")
        pilot.equipment.discard("military")
        pilot.equipment.add(key)
    else:
        pilot.equipment.add(key)
    return True, f"Bought {item.name} for {item.price:.0f} CR"


def equipment_rows(pilot, tech):
    """(key, name, price, note) for the shop screen."""
    rows = []
    for item in EQUIPMENT:
        if available(pilot, item, tech):
            rows.append((item.key, item.name, item.price, item.desc))
    return rows
