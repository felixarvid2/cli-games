import unittest

import support  # noqa: F401  (path + curses stubs)
from coriolis import galaxy as g


class GalaxyTest(unittest.TestCase):
    def test_ten_galaxies_of_256(self):
        self.assertEqual(g.GALAXY_COUNT, 10)
        for number in range(1, 11):
            self.assertEqual(len(g.galaxy(number)), 256)

    def test_generation_is_deterministic(self):
        first = g.galaxy(3)
        g._CACHE.clear()
        second = g.galaxy(3)
        self.assertEqual([s.name for s in first], [s.name for s in second])
        self.assertEqual([(s.x, s.y) for s in first], [(s.x, s.y) for s in second])

    def test_lave_is_the_start_of_galaxy_one(self):
        lave = g.start_system(1)
        self.assertEqual(lave.name, "Lave")
        self.assertEqual(lave.index, g.START_INDEX)
        self.assertEqual((lave.x, lave.y), (0.0, 0.0))
        self.assertEqual(lave.tech, 5)
        self.assertEqual(lave.economy, 5)
        self.assertEqual(lave.population, 2.0)

    def test_names_are_unique_within_a_galaxy(self):
        for number in range(1, 11):
            names = [s.name for s in g.galaxy(number)]
            self.assertEqual(len(set(names)), 256, f"galaxy {number}")
            for name in names:
                self.assertTrue(4 <= len(name) <= 10, name)
                self.assertNotIn(".", name)

    def test_every_system_is_reachable_by_one_jump(self):
        for number in range(1, 11):
            systems = g.galaxy(number)
            for s in systems:
                near = [o for o in systems
                        if o.index != s.index and g.distance(s, o) <= 7.0]
                self.assertTrue(near, f"{s.name} is stranded in galaxy {number}")

    def test_minimum_separation(self):
        systems = g.galaxy(1)
        closest = min(g.distance(a, b) for i, a in enumerate(systems)
                      for b in systems[i + 1:])
        self.assertGreaterEqual(closest, 2.0)

    def test_distance_is_symmetric_and_zero_for_self(self):
        a = g.system(1, 7)
        b = g.system(1, 12)
        self.assertEqual(g.distance(a, b), g.distance(b, a))
        self.assertEqual(g.distance(a, a), 0.0)

    def test_neighbours_are_sorted_within_fuel_range(self):
        nb = g.neighbours(1, g.START_INDEX)
        self.assertTrue(nb)
        self.assertEqual([d for d, _ in nb], sorted(d for d, _ in nb))
        for d, s in nb:
            self.assertLessEqual(d, 7.0)
            self.assertNotEqual(s.index, g.START_INDEX)

    def test_lave_has_an_industrial_neighbour(self):
        # The first trade route has to exist, or the game opens with nothing to do.
        nb = g.neighbours(1, g.START_INDEX)
        self.assertTrue(any(s.economy <= 3 for _, s in nb))

    def test_galaxy_seeds_differ(self):
        seeds = {g.galaxy_seed(n) for n in range(1, 11)}
        self.assertEqual(len(seeds), 10)

    def test_find_by_name(self):
        self.assertEqual(g.find("lave").index, g.START_INDEX)
        self.assertIsNone(g.find("Nowhere"))

    def test_derived_properties_are_sane(self):
        for s in g.galaxy(1):
            self.assertTrue(1 <= s.tech <= 15)
            self.assertTrue(0 <= s.economy <= 7)
            self.assertTrue(0 <= s.government <= 7)
            self.assertTrue(0.1 <= s.population <= 7.0)
            self.assertTrue(1 <= s.productivity <= 100)
            self.assertTrue(2000 <= s.radius <= 6000)
            self.assertTrue(0.0 <= s.danger <= 1.0)


if __name__ == "__main__":
    unittest.main()
