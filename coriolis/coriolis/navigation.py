"""Route planning across the chart.

A leg is one hyperspace jump, and a jump may not be longer than a full tank.
Planning is done on that graph, so a route never asks for fuel the ship cannot
carry; the planner then walks the route with the fuel actually in the tanks and
marks where a refill is needed.
"""

import heapq
from dataclasses import dataclass, field

from . import galaxy
from .data import FUEL_PRICE, MAX_FUEL

MODES = ("short", "safe")


@dataclass
class Route:
    start: int
    target: int
    path: list = field(default_factory=list)      # system indexes, start..target
    legs: list = field(default_factory=list)      # distance per leg
    refuel_at: list = field(default_factory=list)  # indexes where you must refuel
    fuel_now: float = MAX_FUEL
    reason: str = ""

    @property
    def ok(self):
        """A usable route: at least one jump, ending where we asked."""
        return len(self.path) > 1 and self.path[-1] == self.target

    @property
    def jumps(self):
        return len(self.legs)

    @property
    def total(self):
        return round(sum(self.legs), 1)

    @property
    def next_hop(self):
        return self.path[1] if len(self.path) > 1 else None

    @property
    def fuel_cost(self):
        """Credits to buy every litre this route needs."""
        need = 0.0
        fuel = self.fuel_now
        for i, leg in enumerate(self.legs):
            if fuel + 1e-6 < leg:
                need += MAX_FUEL - fuel
                fuel = MAX_FUEL
            fuel = max(0.0, fuel - leg)
        return round(need * FUEL_PRICE, 1)


class _Graph:
    def __init__(self, galaxy_no):
        self.systems = galaxy.galaxy(galaxy_no)
        self.by_index = {s.index: s for s in self.systems}
        self.edges = {}
        for a in self.systems:
            near = []
            for b in self.systems:
                if b.index == a.index:
                    continue
                d = galaxy.distance(a, b)
                if d <= MAX_FUEL:
                    near.append((b.index, d, b.danger))
            self.edges[a.index] = near


_GRAPHS = {}


def graph(galaxy_no):
    if galaxy_no not in _GRAPHS:
        _GRAPHS[galaxy_no] = _Graph(galaxy_no)
    return _GRAPHS[galaxy_no]


def reachable(galaxy_no, start, fuel=MAX_FUEL):
    """Every system reachable from `start` using legs of at most `fuel` LY."""
    g = graph(galaxy_no)
    seen = {start}
    queue = [start]
    while queue:
        here = queue.pop()
        for index, dist, _ in g.edges.get(here, ()):
            if dist <= fuel and index not in seen:
                seen.add(index)
                queue.append(index)
    seen.discard(start)
    return seen


def _cost(mode, dist, danger, danger_weight=2.5):
    if mode == "safe":
        return dist * (1.0 + danger_weight * danger)
    return dist


def plan(galaxy_no, start, target, fuel=MAX_FUEL, mode="short"):
    """Shortest (or safest) route from start to target, one tank per leg."""
    route = Route(start=start, target=target, fuel_now=max(0.0, fuel))
    if start == target:
        route.path = [start]
        route.reason = "Already there"
        return route
    g = graph(galaxy_no)
    if target not in g.by_index:
        route.reason = "No such system"
        return route
    dist, prev = {start: 0.0}, {}
    heap = [(0.0, start)]
    while heap:
        cost, here = heapq.heappop(heap)
        if here == target:
            break
        if cost > dist.get(here, 1e18):
            continue
        for index, leg, danger in g.edges.get(here, ()):
            step = _cost(mode, leg, danger)
            cand = cost + step
            if cand < dist.get(index, 1e18) - 1e-9:
                dist[index] = cand
                prev[index] = here
                heapq.heappush(heap, (cand, index))
    if target not in prev and target != start:
        route.reason = ("No route with 7.0 LY legs - the target sits in a "
                        "cluster you cannot jump to")
        return route
    path = [target]
    while path[-1] != start:
        path.append(prev[path[-1]])
    path.reverse()
    route.path = path
    route.legs = [galaxy.distance(g.by_index[a], g.by_index[b])
                  for a, b in zip(path, path[1:])]
    # Walk the tanks: a leg you cannot afford means a refill before it.
    current = route.fuel_now
    for i, leg in enumerate(route.legs):
        if current + 1e-6 < leg:
            route.refuel_at.append(path[i])
            current = MAX_FUEL
        current = max(0.0, current - leg)
    return route


def steps(galaxy_no, route):
    """(index, distance, refuel_here) for each leg of a route."""
    out = []
    for i, (a, b) in enumerate(zip(route.path, route.path[1:])):
        out.append((b, route.legs[i], route.path[i] in route.refuel_at))
    return out


def search(galaxy_no, query, limit=8):
    """Systems whose name starts with (or contains) the query."""
    q = (query or "").strip().lower()
    if not q:
        return []
    systems = galaxy.galaxy(galaxy_no)
    starts = [s for s in systems if s.name.lower().startswith(q)]
    rest = [s for s in systems if q in s.name.lower()
            and s not in starts]
    starts.sort(key=lambda s: s.name.lower())
    rest.sort(key=lambda s: s.name.lower())
    return (starts + rest)[:limit]
