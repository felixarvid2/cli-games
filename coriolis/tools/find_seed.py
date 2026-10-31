#!/usr/bin/env python3
"""Find a galaxy-1 seed whose system at START_INDEX is called LAVE.

Brute forces the 16-bit family [base, base^0x0248, base^0xB753] through the
real generator (same draw order as galaxy.py) and scores the candidates on
the classic Lave profile: agricultural, democratic, mid tech, has neighbours
within one fuel tank.

Usage: python3 tools/find_seed.py [--name Lave] [--index 7]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from coriolis import galaxy as g  # noqa: E402


def profile(seed, count):
    """Replay the generator's draws for the first `count` systems."""
    used = set()
    last = None
    for _ in range(count):
        name = g.system_name(seed, used)
        used.add(name)
        x = g._jitter(seed)
        y = g._jitter(seed)
        economy = g.draw(seed) & 7
        government = (g.draw(seed) >> 5) & 7
        population = round(0.1 + (g.draw(seed) % 70) / 10.0, 1)
        productivity = 1 + g.draw(seed) % 100
        g.draw(seed)  # radius
        wealth = (7 - economy) * 8 + productivity // 2
        tech = max(1, min(15, 1 + int((wealth + population * 10
                                       + (7 - government) * 3) / 18)))
        last = (name, x, y, economy, government, tech, population, productivity)
    return last


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="Lave")
    ap.add_argument("--index", type=int, default=g.START_INDEX)
    args = ap.parse_args()

    hits = []
    for base in range(0x10000):
        seed = [base, (base ^ 0x0248) & 0xFFFF, (base ^ 0xB753) & 0xFFFF]
        name, x, y, econ, gov, tech, pop, prod = profile(seed, args.index + 1)
        if name.lower() != args.name.lower():
            continue
        score = 0
        if econ in (4, 5):
            score += 3
        if 4 <= tech <= 6:
            score += 2
        if gov == 6:
            score += 2
        if 2.0 <= pop <= 3.0:
            score += 2
        hits.append((score, base, econ, gov, tech, pop, prod))

    print(f"{len(hits)} seeds produce {args.name} at index {args.index}")
    if not hits:
        return 1
    # Now grow the best candidates into full galaxies and score the start
    # neighbourhood: the first trade route must actually be profitable.
    scored = []
    for hit in hits:
        score, base, econ, gov, tech, pop, prod = hit
        g.GALAXY1_SEED = (base, base ^ 0x0248, base ^ 0xB753)
        g._CACHE.clear()
        systems = g.galaxy(1)
        nb = g.neighbours(1, args.index)
        industrial = [s for _, s in nb if s.economy <= 3]
        rich = [s for _, s in nb if s.economy <= 1]
        bonus = 0
        bonus += 3 if rich else 0
        bonus += 2 if industrial else 0
        bonus += min(3, len(nb) // 2)
        scored.append((score + bonus, base, econ, gov, tech, pop, prod,
                       len(nb), len(industrial), [s.name for s in rich][:2]))
    g.GALAXY1_SEED = (0xB58A, 0xB7C2, 0x02D9)
    g._CACHE.clear()
    scored.sort(key=lambda h: (-h[0], abs(h[4] - 5), h[1]))
    for row in scored[:8]:
        print(f"  score {row[0]:2d}  base=0x{row[1]:04X}  econ={row[2]} gov={row[3]} "
              f"tech={row[4]} pop={row[5]}  neighbours={row[7]} "
              f"industrial={row[8]} {row[9]}")
    best = scored[0]
    base = best[1]
    words = (base, base ^ 0x0248, base ^ 0xB753)
    print("\nGALAXY1_SEED =", "(0x%04X, 0x%04X, 0x%04X)" % words)
    return 0


if __name__ == "__main__":
    sys.exit(main())
