import unittest

import support  # noqa: F401
from coriolis import galaxy
from coriolis.data import CARGO_BASE, GOODS, START_CREDITS
from coriolis.market import Market, best_routes


class FakePilot:
    """The little bit of Pilot the market needs."""

    def __init__(self, credits=START_CREDITS, capacity=CARGO_BASE):
        self.credits = credits
        self.cargo = {}
        self.cargo_cap = capacity

    def cargo_used(self):
        return sum(self.cargo.values())

    def cargo_free(self):
        return max(0, self.cargo_cap - self.cargo_used())

    def add_cargo(self, key, qty):
        self.cargo[key] = self.cargo.get(key, 0) + qty

    def remove_cargo(self, key, qty):
        left = self.cargo.get(key, 0) - qty
        if left > 0:
            self.cargo[key] = left
        else:
            self.cargo.pop(key, None)


class MarketTest(unittest.TestCase):
    def setUp(self):
        self.lave = galaxy.start_system(1)
        self.market = Market.for_system(self.lave)

    def test_every_good_has_a_positive_price(self):
        for good in GOODS:
            self.assertGreater(self.market.price(good.key), 0)

    def test_prices_are_deterministic(self):
        again = Market.for_system(self.lave)
        self.assertEqual(self.market.rows("buy"), again.rows("buy"))

    def test_buy_and_sell_prices_are_on_the_right_side_of_the_spread(self):
        for key in self.market.listings:
            listing = self.market.listings[key]
            self.assertLess(listing.sell_price(), listing.buy_price())

    def test_round_trip_at_one_station_loses_money(self):
        pilot = FakePilot()
        start = pilot.credits
        ok, _ = self.market.buy(pilot, "food", 10)
        self.assertTrue(ok)
        ok, _ = self.market.sell(pilot, "food", 10)
        self.assertTrue(ok)
        self.assertLess(pilot.credits, start)

    def test_repeated_impact_makes_bulk_trading_worse(self):
        pilot = FakePilot(credits=10000)
        first = self.market.listings["food"].buy_price()
        self.market.buy(pilot, "food", 20)
        self.assertGreater(self.market.listings["food"].buy_price(), first)

    def test_cannot_buy_more_than_stock_or_cargo_space(self):
        pilot = FakePilot(credits=10000, capacity=5)
        stock = self.market.stock("food")
        ok, _ = self.market.buy(pilot, "food", 99)
        self.assertTrue(ok)
        self.assertEqual(pilot.cargo["food"], min(5, stock))

    def test_cannot_spend_credits_you_do_not_have(self):
        pilot = FakePilot(credits=1.0)
        stocked = [k for k, l in self.market.listings.items() if l.stock > 0]
        ok, msg = self.market.buy(pilot, stocked[0], 1)
        self.assertFalse(ok)
        self.assertIn("credit", msg.lower())
        self.assertEqual(pilot.cargo, {})

    def test_cannot_sell_what_you_do_not_hold(self):
        pilot = FakePilot()
        ok, _ = self.market.sell(pilot, "gold", 1)
        self.assertFalse(ok)

    def test_empty_stock_cannot_be_bought(self):
        pilot = FakePilot(credits=10000)
        empty = [k for k, l in self.market.listings.items() if l.stock == 0]
        self.assertTrue(empty, "Lave should not stock everything")
        ok, msg = self.market.buy(pilot, empty[0], 1)
        self.assertFalse(ok)
        self.assertEqual(msg, "No stock")

    def test_lawful_systems_do_not_trade_illegal_goods(self):
        lawful = [s for s in galaxy.galaxy(1) if s.government >= 4][0]
        market = Market.for_system(lawful)
        for key in ("slaves", "narcotics", "alien"):
            self.assertEqual(market.stock(key), 0, f"{key} at {lawful.name}")

    def test_computers_are_cheaper_in_industrial_space(self):
        industrial = min(galaxy.galaxy(1), key=lambda s: s.economy)
        agrarian = max(galaxy.galaxy(1), key=lambda s: s.economy)
        self.assertEqual(industrial.economy, 0)
        self.assertEqual(agrarian.economy, 7)
        self.assertLess(Market.for_system(industrial).price("computers"),
                        Market.for_system(agrarian).price("computers"))

    def test_there_is_a_profitable_route_out_of_lave(self):
        routes = best_routes(self.lave, galaxy.galaxy(1))
        self.assertTrue(routes)
        self.assertGreater(routes[0][0], 0)

    def test_routes_respect_the_wallet_and_the_hold(self):
        pilot = FakePilot(credits=100.0)
        routes = best_routes(self.lave, galaxy.galaxy(1), pilot)
        self.assertTrue(routes)
        for score, system, good, margin, tonnes in routes:
            self.assertLessEqual(tonnes, pilot.cargo_free())
            self.assertLessEqual(tonnes * margin, pilot.credits + 1e-6)
        self.assertEqual(routes[0][0], max(r[0] for r in routes))

    def test_rows_are_in_goods_order(self):
        self.assertEqual([r[0] for r in self.market.rows()], [g.key for g in GOODS])


if __name__ == "__main__":
    unittest.main()
