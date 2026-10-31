"""Per-system commodity market.

Prices come from the system's economy: goods the system produces are cheap,
goods it needs are dear. There is a bid/ask spread, and your own trading
moves the price against you in both directions - so no station can be
farmed by buying and selling the same crate back.
"""

import zlib
from dataclasses import dataclass, field

from .data import GOODS, GOOD_BY_KEY

BASE_STOCK = 40
SPREAD = 0.05      # dealer's cut, each way
IMPACT = 0.02      # price movement per unit you trade this visit


@dataclass
class Listing:
    good: object
    price: float          # equilibrium price per tonne
    stock: int
    initial: int
    bought: int = 0
    sold: int = 0

    def buy_price(self):
        return round(max(0.1, self.price * (1 + SPREAD) * (1 + IMPACT * self.bought)), 2)

    def sell_price(self):
        return round(max(0.05, self.price * (1 - SPREAD) * (1 - IMPACT * self.sold)), 2)


class Market:
    def __init__(self, system):
        self.system = system
        self.listings = {g.key: self._listing(g) for g in GOODS}

    @classmethod
    def for_system(cls, system):
        return cls(system)

    # -- generation -------------------------------------------------------
    def _listing(self, good):
        industrial = self.system.industrial
        # 1.0 means the local economy specialises in this good.
        score = good.industrial * industrial + (1.0 - good.industrial) * (1.0 - industrial)
        price = good.base * (1.5 - 0.9 * score)
        local = zlib.crc32((good.key + self.system.name).encode()) / 0xFFFFFFFF
        price *= 0.94 + local * 0.12
        stock = 0
        if self.system.tech >= good.tech:
            stock = int(round(BASE_STOCK * score * (0.45 + self.system.productivity / 90.0)))
            stock = int(stock * (0.7 + local * 0.6))
        if good.illegal and self.system.government >= 4:
            stock = 0            # lawful states do not deal in these openly
        return Listing(good, round(price, 2), stock, max(stock, 1))

    # -- queries ----------------------------------------------------------
    def price(self, key):
        """Equilibrium value, used for valuation and comparisons."""
        return self.listings[key].price

    def stock(self, key):
        return self.listings[key].stock

    def rows(self, mode="buy"):
        """(key, name, price, stock) in the order the shop shows them."""
        out = []
        for listing in self.listings.values():
            price = listing.buy_price() if mode == "buy" else listing.sell_price()
            out.append((listing.good.key, listing.good.name, price, listing.stock))
        return out

    # -- trading ----------------------------------------------------------
    def buy(self, pilot, key, qty=1):
        listing = self.listings[key]
        if listing.stock <= 0:
            return False, "No stock"
        room = pilot.cargo_free()
        if room <= 0:
            return False, "Cargo hold full"
        qty = min(max(1, int(qty)), listing.stock, room)
        cost, taken = 0.0, 0
        for _ in range(qty):
            price = listing.buy_price()
            if round(cost + price, 1) > pilot.credits + 1e-9:
                break
            cost += price
            listing.bought += 1
            taken += 1
        if taken == 0:
            return False, "Not enough credits"
        listing.stock -= taken
        pilot.credits = round(pilot.credits - cost, 1)
        pilot.add_cargo(key, taken)
        return True, f"Bought {taken}t {listing.good.name} for {cost:.1f} CR"

    def sell(self, pilot, key, qty=1):
        listing = self.listings[key]
        have = pilot.cargo.get(key, 0)
        if have <= 0:
            return False, "You have none"
        qty = min(max(1, int(qty)), have)
        earned = 0.0
        for _ in range(qty):
            earned += listing.sell_price()
            listing.sold += 1
        listing.stock += qty
        pilot.credits = round(pilot.credits + earned, 1)
        pilot.remove_cargo(key, qty)
        return True, f"Sold {qty}t {listing.good.name} for {earned:.1f} CR"


def best_routes(system, systems, max_ly=7.0, limit=5):
    """Most profitable single-hop trades from a system, for the chart panel."""
    from .galaxy import distance

    here = Market.for_system(system)
    out = []
    for other in systems:
        if other.index == system.index:
            continue
        d = distance(system, other)
        if d > max_ly:
            continue
        there = Market.for_system(other)
        best = None
        for good in GOODS:
            if here.stock(good.key) <= 0:
                continue
            margin = there.listings[good.key].sell_price() - here.listings[good.key].buy_price()
            if best is None or margin > best[0]:
                best = (margin, good, here.listings[good.key].buy_price(),
                        there.listings[good.key].sell_price())
        if best and best[0] > 0:
            out.append((best[0], other, best[1]))
    out.sort(key=lambda row: -row[0])
    return out[:limit]
