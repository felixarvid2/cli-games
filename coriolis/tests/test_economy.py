"""Prices, profits, events and market persistence."""
import unittest

import support
from coriolis import core, economy, market as market_mod


def docked(seed=3, system=None, now=0.0):
    state = core.GameState(seed=seed)
    if system is not None:
        state.pilot.system = system
    state.time = now
    state.dock()
    return state


class EventTest(unittest.TestCase):
    def test_events_are_deterministic(self):
        a = economy.roll(5, 1, 7, 3)
        b = economy.roll(5, 1, 7, 3)
        self.assertEqual([e.to_dict() for e in a], [e.to_dict() for e in b])

    def test_different_buckets_differ(self):
        rolls = [tuple(sorted(e.short for e in economy.roll(5, 1, 7, b)))
                 for b in range(12)]
        self.assertGreater(len(set(rolls)), 1)

    def test_an_event_moves_the_prices_of_its_goods_only(self):
        state = docked(now=0.0)
        plain = market_mod.Market.for_system(state.system)
        events = []
        for bucket in range(1, 40):
            state.time = economy.EVENT_PERIOD * bucket
            state.markets.clear()
            events = state.market_for(state.system).events
            if events:
                break
        self.assertTrue(events, "no event found in 40 windows")
        ev = events[0]
        for key in ev.goods:
            self.assertNotAlmostEqual(state.market.listings[key].price,
                                      plain.listings[key].price, places=2)
        for key in plain.listings:
            if key in ev.goods:
                continue
            self.assertAlmostEqual(state.market.listings[key].price,
                                   plain.listings[key].price, places=2)

    def test_market_does_not_reroll_on_docking(self):
        state = docked(now=economy.EVENT_PERIOD * 2.5)
        first = [(e.kind, e.until) for e in state.market.events]
        state.launch()
        state.dock()
        self.assertEqual([(e.kind, e.until) for e in state.market.events], first)

    def test_events_survive_a_reload(self):
        state = docked(now=economy.EVENT_PERIOD * 2.5)
        first = [(e.kind, e.until) for e in state.market.events]
        again = core.GameState.from_dict(state.to_dict())
        again.dock()
        self.assertEqual([(e.kind, e.until) for e in again.market.events], first)

    def test_events_expire_with_the_clock(self):
        state = docked(now=0.0)
        events = []
        for bucket in range(1, 40):
            state.time = economy.EVENT_PERIOD * bucket
            state.markets.clear()
            events = state.market_for(state.system).events
            if events:
                break
        self.assertTrue(events, "no event in forty windows")
        state.time = events[0].until + 1
        state.markets.clear()
        fresh = state.market
        self.assertEqual([e for e in fresh.events if e.until < state.time], [])
        self.assertFalse(any(e.until <= state.time for e in fresh.events))


class MarketPersistenceTest(unittest.TestCase):
    def test_stock_survives_leaving_and_returning(self):
        state = docked()
        before = state.market.stock("food")
        state.market.buy(state.pilot, "food", 5)
        after = state.market.stock("food")
        self.assertLess(after, before)
        state.launch()
        state.dock()
        self.assertEqual(state.market.stock("food"), after)

    def test_market_survives_a_save_and_load(self):
        state = docked()
        state.market.buy(state.pilot, "food", 4)
        stock = state.market.stock("food")
        again = core.GameState.from_dict(state.to_dict())
        self.assertEqual(again.market.stock("food"), stock)

    def test_trade_impact_fades_with_time(self):
        state = docked()
        state.market.buy(state.pilot, "food", 10)
        listing = state.market.listings["food"]
        hot = listing.buy_price()
        state.tick_markets(4000.0)
        self.assertLess(listing.bought, 10)
        self.assertLess(listing.buy_price(), hot)

    def test_each_system_keeps_its_own_market(self):
        state = docked()
        first = state.market.stock("food")
        state.pilot.system = 12
        state.dock()
        self.assertNotEqual(state.market.stock("food"), first)
        state.pilot.system = 7
        state.dock()
        self.assertEqual(state.market.stock("food"), first)


class ProfitTest(unittest.TestCase):
    def test_realised_profit_is_revenue_minus_cost(self):
        state = docked()
        credits = state.pilot.credits
        buy = state.market.quote_buy("food", 20, credits, state.pilot.cargo_free())
        state.market.buy(state.pilot, "food", buy.qty)
        sale = state.market.quote_sell("food", buy.qty, buy.qty)
        state.market.sell(state.pilot, "food", buy.qty)
        self.assertAlmostEqual(state.pilot.trade_profit,
                               round(sale.total - buy.total, 1), places=1)
        self.assertAlmostEqual(state.pilot.credits,
                               credits + sale.total - buy.total, places=1)

    def test_partial_sales_keep_the_rest_of_the_basis(self):
        state = docked()
        state.market.buy(state.pilot, "food", 6)
        total = state.pilot.costs["food"]
        state.market.sell(state.pilot, "food", 3)
        self.assertAlmostEqual(state.pilot.costs["food"], total / 2, delta=0.6)

    def test_losing_trade_shows_a_loss(self):
        state = docked()
        state.market.buy(state.pilot, "food", 5)
        state.market.sell(state.pilot, "food", 5)
        self.assertLess(state.pilot.trade_profit, 0)

    def test_cost_basis_is_cleared_when_the_hold_is(self):
        state = docked()
        state.market.buy(state.pilot, "food", 5)
        state.market.sell(state.pilot, "food", 5)
        self.assertNotIn("food", state.pilot.costs)

    def test_profit_survives_a_save(self):
        state = docked()
        state.market.buy(state.pilot, "food", 2)
        state.market.sell(state.pilot, "food", 2)
        again = core.GameState.from_dict(state.to_dict())
        self.assertAlmostEqual(again.pilot.trade_profit,
                               state.pilot.trade_profit, places=1)


if __name__ == "__main__":
    unittest.main()
