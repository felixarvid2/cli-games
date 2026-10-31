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
        self.costs = {}
        self.reserved = {}
        self.trade_profit = 0.0
        self.cargo_cap = capacity

    def cargo_used(self):
        return sum(self.cargo.values())

    def cargo_free(self):
        return max(0, self.cargo_cap - self.cargo_used())

    def add_cargo(self, key, qty):
        self.cargo[key] = self.cargo.get(key, 0) + qty

    def remove_cargo(self, key, qty):
        have = self.cargo.get(key, 0)
        qty = min(qty, have)
        basis = self.cost_basis(key, qty)
        left = have - qty
        if left > 0:
            self.cargo[key] = left
        else:
            self.cargo.pop(key, None)
            self.costs.pop(key, None)
        return basis

    def add_cost(self, key, amount):
        self.costs[key] = round(self.costs.get(key, 0.0) + amount, 2)

    def cost_basis(self, key, qty):
        have = self.cargo.get(key, 0)
        total = self.costs.get(key, 0.0)
        if have <= 0 or total <= 0 or qty <= 0:
            return 0.0
        basis = round(total * min(qty, have) / have, 2)
        left = round(total - basis, 2)
        if left > 0:
            self.costs[key] = left
        else:
            self.costs.pop(key, None)
        return basis


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
        for net, system, good, margin, tonnes, fuel, danger in routes:
            self.assertGreater(tonnes, 0)
            self.assertLessEqual(tonnes, pilot.cargo_free())
            self.assertGreater(net, 0)
            self.assertGreaterEqual(fuel, 0)
            self.assertTrue(0.0 <= danger <= 1.0)
        self.assertEqual(routes[0][0], max(r[0] for r in routes))

    def test_quote_matches_what_is_charged(self):
        pilot = FakePilot(credits=500.0, capacity=40)
        quote = self.market.quote_buy("food", 20, pilot.credits, pilot.cargo_free())
        before = pilot.credits
        ok, _ = self.market.buy(pilot, "food", 20)
        self.assertTrue(ok)
        self.assertAlmostEqual(before - pilot.credits, quote.total, places=1)
        self.assertEqual(pilot.cargo["food"], quote.qty)
        self.assertAlmostEqual(self.market.listings["food"].bought, quote.qty)

    def test_bulk_price_impact_is_counted_once(self):
        pilot = FakePilot(credits=5000.0, capacity=80)
        quote = self.market.quote_buy("food", 20, pilot.credits, pilot.cargo_free())
        self.market.buy(pilot, "food", 20)
        self.assertAlmostEqual(self.market.listings["food"].bought, quote.qty)
        # A second batch must start where the first stopped, not twice as far.
        second = self.market.quote_buy("food", 20, pilot.credits, pilot.cargo_free())
        self.assertGreater(second.unit, quote.unit)
        self.assertLess(second.unit, quote.unit * 1.25)

    def test_quote_respects_stock_credits_and_hold(self):
        self.assertEqual(self.market.quote_buy("narcotics", 5, 1000.0, 20).qty, 0)
        self.assertEqual(self.market.quote_buy("food", 5, 0.0, 20).qty, 0)
        self.assertEqual(self.market.quote_buy("food", 5, 1000.0, 0).qty, 0)
        stock = self.market.stock("food")
        self.assertLessEqual(self.market.quote_buy("food", 999, 10000.0, 999).qty, stock)

    def test_buy_maximum_fills_the_hold_and_the_wallet(self):
        pilot = FakePilot(credits=40.0, capacity=20)
        quote = self.market.quote_buy_max("food", pilot.credits, pilot.cargo_free())
        self.assertTrue(quote.ok())
        ok, _ = self.market.buy(pilot, "food", quote.qty)
        self.assertTrue(ok)
        self.assertLessEqual(pilot.credits, 40.0)
        self.assertGreaterEqual(pilot.credits, 0.0)
        self.assertEqual(pilot.cargo["food"], quote.qty)

    def test_sell_quote_matches_the_payment_and_skips_reserved_cargo(self):
        pilot = FakePilot(credits=100.0)
        pilot.add_cargo("food", 6)
        pilot.reserved["food"] = 4
        quote = self.market.quote_sell("food", 99, pilot.cargo["food"],
                                       pilot.reserved["food"])
        self.assertEqual(quote.qty, 2)
        before = pilot.credits
        ok, _ = self.market.sell(pilot, "food", 99)
        self.assertTrue(ok)
        self.assertAlmostEqual(pilot.credits - before, quote.total, places=1)
        self.assertEqual(pilot.cargo["food"], 4)

    def test_money_is_rounded_to_one_decimal(self):
        pilot = FakePilot(credits=100.0)
        self.market.buy(pilot, "food", 3)
        self.assertEqual(round(pilot.credits, 1), pilot.credits)
        self.market.sell(pilot, "food", 3)
        self.assertEqual(round(pilot.credits, 1), pilot.credits)

    def test_rows_are_in_goods_order(self):
        self.assertEqual([r[0] for r in self.market.rows()], [g.key for g in GOODS])


if __name__ == "__main__":
    unittest.main()
