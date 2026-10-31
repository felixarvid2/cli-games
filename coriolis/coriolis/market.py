"""Per-system commodity market.

Prices come from the system's economy: goods the system produces are cheap,
goods it needs are dear. There is a bid/ask spread, and your own trading moves
the price against you in both directions - so no station can be farmed by
buying and selling the same crate back.

All pricing goes through `quote_buy` / `quote_sell`, which are pure functions
of the numbers involved (no pilot, no mutation). The UI, the route advice and
the transaction itself all use the same quote, so what is quoted is exactly
what is charged.
"""

import zlib
from dataclasses import dataclass

from .data import GOODS

BASE_STOCK = 40
SPREAD = 0.05      # dealer's cut, each way
IMPACT = 0.008     # price movement per unit you trade this visit
MONEY = 0.1        # the smallest unit of currency the game deals in


@dataclass
class Listing:
    good: object
    price: float          # equilibrium price per tonne, before events
    stock: int
    initial: int
    bought: int = 0
    sold: int = 0

    def buy_price(self, extra=0):
        """Price of the next tonne, allowing for units already traded."""
        return round(max(0.1, self.price * (1 + SPREAD)
                         * (1 + IMPACT * (self.bought + extra))), 2)

    def sell_price(self, extra=0):
        return round(max(0.05, self.price * (1 - SPREAD)
                         * (1 - IMPACT * (self.sold + extra))), 2)


@dataclass(frozen=True)
class Quote:
    """The exact result of a prospective trade."""

    key: str
    qty: int             # tonnes that can actually be traded
    total: float         # exact credits, rounded to one decimal
    unit: float          # average price per tonne
    limited_by: str = ""  # '', 'stock', 'credits', 'cargo', 'holdings'

    def ok(self):
        return self.qty > 0

    def why(self, good_name="cargo"):
        return {"stock": "No stock",
                "credits": "Not enough credits",
                "cargo": "Cargo hold full",
                "holdings": f"You have no {good_name}"}.get(self.limited_by, "Nothing to trade")


class Market:
    def __init__(self, system):
        self.system = system
        self.listings = {g.key: self._listing(g) for g in GOODS}
        self.events = []            # economic events; see set_events()

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

    # -- events -----------------------------------------------------------
    def set_events(self, events):
        """Apply local economic events to prices and local stock."""
        self.events = list(events)
        for listing in self.listings.values():
            factor = 1.0
            stock_factor = 1.0
            for ev in self.events:
                if listing.good.key in ev.goods:
                    factor *= ev.factor
                    stock_factor *= getattr(ev, "stock", 1.0)
            listing.price = round(self._base_price(listing.good) * factor, 2)
            if stock_factor != 1.0:
                listing.stock = max(0, int(round(listing.initial * stock_factor)))

    def decay(self, seconds):
        """Trade impact fades with time, so a market recovers if left alone."""
        if seconds <= 0:
            return
        fade = max(0.0, 1.0 - seconds / 1800.0)   # half an hour to forget
        for listing in self.listings.values():
            listing.bought = int(listing.bought * fade)
            listing.sold = int(listing.sold * fade)

    # -- persistence -------------------------------------------------------
    def to_dict(self):
        return {"listings": {key: {"stock": l.stock, "bought": l.bought,
                                    "sold": l.sold, "price": l.price}
                              for key, l in self.listings.items()},
                "events": [e.to_dict() for e in self.events]}

    @classmethod
    def from_dict(cls, system, data):
        market = cls(system)
        if not data:
            return market
        for key, row in (data.get("listings") or {}).items():
            listing = market.listings.get(key)
            if listing is None:
                continue
            listing.stock = int(row.get("stock", listing.stock))
            listing.bought = int(row.get("bought", 0))
            listing.sold = int(row.get("sold", 0))
            listing.price = float(row.get("price", listing.price))
        from .economy import Event
        market.events = [Event.from_dict(e) for e in (data.get("events") or [])]
        return market

    def _base_price(self, good):
        """Price with no events applied (recomputed, not accumulated)."""
        industrial = self.system.industrial
        score = good.industrial * industrial + (1.0 - good.industrial) * (1.0 - industrial)
        price = good.base * (1.5 - 0.9 * score)
        local = zlib.crc32((good.key + self.system.name).encode()) / 0xFFFFFFFF
        return round(price * (0.94 + local * 0.12), 2)

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

    # -- quotes (pure) ----------------------------------------------------
    def quote_buy(self, key, qty, credits, room):
        """What buying `qty` tonnes would cost. No state changes."""
        listing = self.listings[key]
        want = max(0, int(qty))
        if listing.stock <= 0:
            return Quote(key, 0, 0.0, 0.0, "stock")
        if room <= 0:
            return Quote(key, 0, 0.0, 0.0, "cargo")
        limit = min(want, listing.stock, int(room))
        total, taken, reason = 0.0, 0, ""
        while taken < limit:
            price = listing.buy_price(taken)
            if round(total + price, 1) > credits + 1e-9:
                reason = "credits"
                break
            total += price
            taken += 1
        if taken == 0:
            return Quote(key, 0, 0.0, 0.0, reason or "credits")
        total = round(total, 1)
        return Quote(key, taken, total, round(total / taken, 2), reason)

    def quote_sell(self, key, qty, held, reserved=0):
        """What selling `qty` tonnes would pay. No state changes."""
        listing = self.listings[key]
        free = max(0, int(held) - max(0, int(reserved)))
        if free <= 0:
            return Quote(key, 0, 0.0, 0.0, "holdings")
        want = min(max(0, int(qty)), free)
        if want <= 0:
            return Quote(key, 0, 0.0, 0.0, "holdings")
        total = sum(listing.sell_price(i) for i in range(want))
        total = round(total, 1)
        return Quote(key, want, total, round(total / want, 2))

    def quote_buy_max(self, key, credits, room):
        """Everything the wallet, the hold and the shelf allow."""
        listing = self.listings[key]
        return self.quote_buy(key, listing.stock, credits, room)

    # -- transactions -----------------------------------------------------
    def buy(self, pilot, key, qty=1):
        quote = self.quote_buy(key, qty, pilot.credits, pilot.cargo_free())
        if not quote.ok():
            return False, quote.why(self.listings[key].good.name)
        listing = self.listings[key]
        listing.stock -= quote.qty
        listing.bought += quote.qty
        pilot.credits = round(pilot.credits - quote.total, 1)
        pilot.add_cargo(key, quote.qty)
        pilot.add_cost(key, quote.total)
        return True, (f"Bought {quote.qty}t {listing.good.name} "
                      f"for {quote.total:.1f} CR")

    def sell(self, pilot, key, qty=1):
        held = pilot.cargo.get(key, 0)
        reserved = pilot.reserved.get(key, 0) if hasattr(pilot, "reserved") else 0
        if held > 0 and held <= reserved:
            return False, (f"{reserved}t {self.listings[key].good.name} is "
                           "reserved for a mission")
        quote = self.quote_sell(key, qty, held, reserved)
        if not quote.ok():
            name = self.listings[key].good.name
            if held > reserved and reserved:
                return False, f"{reserved}t {name} is reserved for a mission"
            return False, quote.why(name)
        listing = self.listings[key]
        listing.stock += quote.qty
        listing.sold += quote.qty
        pilot.credits = round(pilot.credits + quote.total, 1)
        basis = pilot.remove_cargo(key, quote.qty)
        profit = round(quote.total - basis, 1)
        if hasattr(pilot, "trade_profit"):
            pilot.trade_profit = round(pilot.trade_profit + profit, 1)
        return True, (f"Sold {quote.qty}t {listing.good.name} for "
                      f"{quote.total:.1f} CR ({profit:+.1f})")


def affordable(market, key, credits, room):
    """(tonnes, exact cost) that a wallet and a hold can actually cover."""
    quote = market.quote_buy(key, market.stock(key), credits, room)
    return quote.qty, quote.total


def best_routes(system, systems, pilot=None, max_ly=7.0, limit=5):
    """The hops worth making from here.

    With a pilot, routes are ranked by the profit one trip would actually make,
    using the same quotes as the trade screen (so what is promised is what is
    charged), and the fuel burned to get there is subtracted from the estimate.
    Returns (net, system, good, margin_per_tonne, tonnes, fuel_cost, danger).
    """
    from .data import FUEL_PRICE
    from .galaxy import distance

    here = Market.for_system(system)
    out = []
    for other in systems:
        if other.index == system.index:
            continue
        leg = distance(system, other)
        if leg > max_ly:
            continue
        there = Market.for_system(other)
        for good in GOODS:
            if here.stock(good.key) <= 0:
                continue
            room = 20 if pilot is None else pilot.cargo_free()
            credits = 5000.0 if pilot is None else pilot.credits
            buy = here.quote_buy(good.key, room, credits, room)
            if not buy.ok():
                continue
            sell = there.quote_sell(good.key, buy.qty, buy.qty)
            if not sell.ok():
                continue
            fuel = round(leg * FUEL_PRICE, 1)
            net = round(sell.total - buy.total - fuel, 1)
            if net <= 0:
                continue
            out.append((net, other, good, round(net / buy.qty, 2), buy.qty,
                        fuel, round(other.danger, 2)))
    out.sort(key=lambda row: (-row[0], row[4]))
    return out[:limit]
