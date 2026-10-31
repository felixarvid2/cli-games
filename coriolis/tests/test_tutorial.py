"""The introduction, and the trading and exploration ranks."""
import unittest

import support
from coriolis import core, galaxy, missions, progression, tutorial
from coriolis.flight import Mat3, Vec3


def new_game(**kwargs):
    game, scr = support.make_game("\n", ["--seed", "1"])
    return game, scr


def tutorial_offer(state):
    for mission in missions.offers(state):
        if getattr(mission, "tutorial", False):
            return mission
    return None


class TutorialTest(unittest.TestCase):
    def test_new_commander_starts_docked_with_a_contract(self):
        game, _ = new_game()
        self.assertEqual(game.screen, "docked")
        offer = tutorial_offer(game.state)
        self.assertIsNotNone(offer)
        self.assertEqual(tutorial.step(game.state.pilot), "accept")
        self.assertTrue(tutorial.active(game.state.pilot))

    def test_accepting_the_contract_loads_cargo_and_advances(self):
        game, _ = new_game()
        state = game.state
        offer = tutorial_offer(state)
        ok, msg = missions.accept(state, offer)
        self.assertTrue(ok, msg)
        self.assertEqual(state.pilot.reserved.get("food"), offer.cargo_qty)
        self.assertEqual(tutorial.step(state.pilot), "jump")

    def test_a_normal_contract_does_not_advance_the_tutorial(self):
        game, _ = new_game()
        state = game.state
        other = [m for m in missions.offers(state)
                 if not getattr(m, "tutorial", False)]
        if not other:
            self.skipTest("no ordinary contract on this board")
        missions.accept(state, other[0])
        self.assertEqual(tutorial.step(state.pilot), "accept")

    def test_jumping_to_the_destination_advances(self):
        game, _ = new_game()
        state = game.state
        offer = tutorial_offer(state)
        missions.accept(state, offer)
        dest = offer.dest_tuple[1]
        state.pilot.fuel = 7.0
        self.assertTrue(state.can_jump(dest)[0])
        state.begin_jump(dest)
        for _ in range(400):
            if state.jump:
                state.jump["left"] -= 1 / 60
                if state.jump["left"] <= 0:
                    state.complete_jump(state.jump["index"], state.jump["cost"])
        self.assertEqual(tutorial.step(state.pilot), "dock")

    def test_jumping_elsewhere_does_not_advance(self):
        game, _ = new_game()
        state = game.state
        offer = tutorial_offer(state)
        missions.accept(state, offer)
        dest = offer.dest_tuple[1]
        wrong = None
        for _dist, system in galaxy.neighbours(1, state.pilot.system):
            if system.index != dest:
                wrong = system.index
                break
        self.assertIsNotNone(wrong)
        state.pilot.fuel = 7.0
        state.begin_jump(wrong)
        for _ in range(400):
            if state.jump:
                state.jump["left"] -= 1 / 60
                if state.jump["left"] <= 0:
                    state.complete_jump(state.jump["index"], state.jump["cost"])
        self.assertEqual(tutorial.step(state.pilot), "jump")

    def test_docking_and_delivering_finishes_with_one_reward(self):
        game, _ = new_game()
        state = game.state
        offer = tutorial_offer(state)
        missions.accept(state, offer)
        credits = state.pilot.credits
        state.pilot.system = offer.dest_tuple[1]
        state.dock()
        self.assertIn("GRADUATE", state.pilot.badges)
        self.assertGreater(state.pilot.credits, credits)
        paid = state.pilot.credits
        tutorial.finish(state)
        self.assertEqual(state.pilot.credits, paid)
        self.assertEqual(state.pilot.badges.count("GRADUATE"), 1)

    def test_skipping_pays_nothing(self):
        game, _ = new_game()
        state = game.state
        credits = state.pilot.credits
        self.assertTrue(tutorial.skip(state.pilot))
        self.assertFalse(tutorial.active(state.pilot))
        self.assertEqual(state.pilot.credits, credits)
        self.assertNotIn("GRADUATE", state.pilot.badges)

    def test_skip_from_the_station_menu(self):
        game, _ = new_game()
        actions = [a for a, _ in game.docked_items()]
        self.assertIn("skip_tutorial", actions)
        support.pick(game, "skip_tutorial")
        self.assertFalse(tutorial.active(game.state.pilot))

    def test_tutorial_state_survives_a_save(self):
        game, _ = new_game()
        state = game.state
        missions.accept(state, tutorial_offer(state))
        again = core.GameState.from_dict(state.to_dict())
        self.assertEqual(tutorial.step(again.pilot), "jump")

    def test_no_tutorial_flag_skips_it(self):
        game, _ = support.make_game("\n", ["--seed", "1", "--no-tutorial"])
        self.assertFalse(tutorial.active(game.state.pilot))


class PlaythroughTest(unittest.TestCase):
    def test_tutorial_can_be_played_with_the_keyboard(self):
        game, scr = new_game()
        state = game.state
        # Station: open the board and accept the tutorial contract.
        support.pick(game, "missions")
        self.assertEqual(game.screen, "missions")
        game.handle(10)
        self.assertEqual(len(missions.active(state)), 1)
        offer = missions.active(state)[0]
        self.assertTrue(offer.tutorial)
        self.assertEqual(tutorial.step(state.pilot), "jump")
        game.handle(support.KEYS["esc"])
        # Launch and jump from the chart.
        support.pick(game, "launch")
        self.assertEqual(game.screen, "flight")
        game.handle(ord("h"))
        game.chart_sel = offer.dest_tuple[1]
        game.handle(10)
        self.assertEqual(game.screen, "flight")
        for _ in range(400):
            game.step_sim(1 / 60)
        self.assertEqual(state.pilot.system, offer.dest_tuple[1])
        self.assertEqual(tutorial.step(state.pilot), "dock")
        # Fly the slot and dock.
        state.contacts = []
        station = state.station
        up = station.slot_vector()
        forward = Vec3(0, 0, 1)
        ship = state.flight
        ship.pos = Vec3(0, 0, -120)
        ship.speed = 100.0
        ship.orient = Mat3(up.cross(forward), up, forward).renormalise()
        game.step_sim(1 / 60)
        self.assertEqual(game.screen, "docked")
        self.assertFalse(tutorial.active(state.pilot))
        self.assertIn("GRADUATE", state.pilot.badges)


class RankTest(unittest.TestCase):
    def test_trade_rank_follows_realised_profit(self):
        self.assertEqual(progression.trade_rank(0), "Penniless")
        self.assertEqual(progression.trade_rank(300), "Peddler")
        self.assertEqual(progression.trade_rank(5000), "Merchant")
        self.assertEqual(progression.trade_rank(1e9), "Magnate")

    def test_exploration_rank_follows_unique_systems(self):
        self.assertEqual(progression.explore_rank(0), "Lost")
        self.assertEqual(progression.explore_rank(3), "Scout")
        self.assertEqual(progression.explore_rank(500), "Cartographer")

    def test_next_milestones(self):
        title, left = progression.next_trade(0)
        self.assertEqual(title, "Peddler")
        self.assertEqual(left, 250)
        title, left = progression.next_explore(0)
        self.assertEqual(title, "Scout")
        self.assertEqual(left, 3)

    def test_visiting_a_system_twice_counts_once(self):
        pilot = core.Pilot()
        self.assertTrue(pilot.visit(1, 7))
        self.assertFalse(pilot.visit(1, 7))
        self.assertTrue(pilot.visit(1, 8))
        self.assertEqual(len(pilot.visited), 2)

    def test_ranks_are_announced_once(self):
        state = core.GameState(seed=1)
        state.check_ranks()                      # sets the starting ranks
        state.pilot.trade_profit = 300
        notes = state.check_ranks()
        self.assertIn("Trade rank: Peddler", notes)
        self.assertEqual(state.check_ranks(), [])

    def test_exploration_rank_is_announced_when_it_changes(self):
        state = core.GameState(seed=1)
        state.check_ranks()
        for index in (7, 8, 9):
            state.pilot.visit(1, index)
        notes = state.check_ranks()
        self.assertTrue(any("Exploration rank" in note for note in notes))

    def test_docking_records_the_visit(self):
        state = core.GameState(seed=1)
        state.dock()
        self.assertIn("1:7", state.pilot.visited)


if __name__ == "__main__":
    unittest.main()
