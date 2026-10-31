import unittest

import support  # noqa: F401
from coriolis import combat, core, sketch
from coriolis.flight import Vec3
from coriolis.station import RADIUS


class CanvasTest(unittest.TestCase):
    def test_put_and_clip(self):
        cv = sketch.Canvas(5, 3)
        cv.put(0, 0, "a")
        cv.put(-1, 0, "b")
        cv.put(99, 0, "c")
        cv.put(4, 2, "d")
        self.assertEqual(cv.rows(), ["a    ", "     ", "    d"])

    def test_depth_buffer_keeps_the_nearest(self):
        cv = sketch.Canvas(3, 1)
        cv.put(1, 0, "f", depth=10)
        cv.put(1, 0, "n", depth=50)
        self.assertEqual(cv.rows()[0], " f ")
        cv.put(1, 0, "c", depth=5)
        self.assertEqual(cv.rows()[0], " c ")

    def test_text_always_wins(self):
        cv = sketch.Canvas(4, 1)
        cv.put(0, 0, "x", depth=1)
        cv.text(0, 0, "hi")
        self.assertEqual(cv.rows()[0], "hi  ")


class SpriteTest(unittest.TestCase):
    def test_sprite_size_shrinks_with_distance(self):
        near = sketch.sprite_size(60, 500, 74, 20)
        far = sketch.sprite_size(60, 5000, 74, 20)
        self.assertGreater(near, far)
        self.assertGreaterEqual(far, 1)
        self.assertLessEqual(near, 20)

    def test_sprite_size_is_clamped(self):
        self.assertEqual(sketch.sprite_size(60, 1, 74, 9), 9)
        self.assertEqual(sketch.sprite_size(60, 1e9, 74, 9), 1)

    def test_starfield_is_deterministic(self):
        self.assertEqual(len(sketch.STARS), 260)
        self.assertEqual(sketch.STARS[0], sketch.STARS[0])
        for star in sketch.STARS[:20]:
            self.assertAlmostEqual(star.length(), 1.0, places=6)


class SceneTest(unittest.TestCase):
    def setUp(self):
        self.state = core.GameState(seed=3)
        self.state.launch()

    def test_scene_has_the_requested_size(self):
        cv, _ = sketch.draw_scene(self.state, 60, 12)
        self.assertEqual(len(cv.rows()), 12)
        self.assertTrue(all(len(row) == 60 for row in cv.rows()))

    def test_scene_renders_in_every_art_mode(self):
        for mode in ("solid", "wire", "hybrid"):
            cv, _ = sketch.draw_scene(self.state, 40, 10, mode=mode)
            self.assertEqual(len(cv.rows()), 10)

    def test_target_is_reported_when_it_is_in_front(self):
        c = combat.make("ship", "cobra", Vec3(0, 0, 0))
        self.state.flight.pos = Vec3(0, 0, -900)
        self.state.contacts = [c]
        _, info = sketch.draw_scene(self.state, 60, 12)
        self.assertIsNotNone(info)
        self.assertEqual(info[0].name, "Cobra Mk III")
        self.assertAlmostEqual(info[1], 900, delta=1)

    def test_no_target_behind_the_ship(self):
        c = combat.make("ship", "cobra", Vec3(0, 0, 0))
        self.state.flight.pos = Vec3(0, 0, 900)
        self.state.contacts = [c]
        _, info = sketch.draw_scene(self.state, 60, 12)
        self.assertIsNone(info)

    def test_close_station_draws_inside_the_canvas(self):
        self.state.flight.pos = Vec3(0, 0, -300)
        cv, _ = sketch.draw_scene(self.state, 60, 14)
        self.assertEqual(len(cv.rows()), 14)
        self.assertTrue(any("|" in row or "/" in row for row in cv.rows()))

    def test_station_octagon_fits_clipped_canvas(self):
        cv = sketch.Canvas(20, 8)
        sketch.octagon(cv, 10, 4, 60, 30, "cyan")
        self.assertEqual(len(cv.rows()), 8)
        self.assertTrue(all(len(r) == 20 for r in cv.rows()))


class RadarTest(unittest.TestCase):
    def setUp(self):
        self.state = core.GameState(seed=3)
        self.state.launch()
        self.state.flight.pos = Vec3(0.0, 0.0, 0.0)
        self.state.contacts = []

    def test_contacts_stay_inside_the_grid(self):
        self.state.contacts = [
            combat.make("ship", "cobra", Vec3(0, 0, 1000)),
            combat.make("ship", "python", Vec3(-400, 200, 6000)),
            combat.make("ship", "mamba", Vec3(9000, 0, 300)),
        ]
        for row, col, ch, colour in sketch.radar_contacts(self.state, 15, 5):
            self.assertTrue(0 <= row < 5)
            self.assertTrue(0 <= col < 15)
            self.assertEqual(len(ch), 1)
            self.assertTrue(colour)

    def test_forward_contact_is_above_the_centre(self):
        self.state.contacts = [combat.make("ship", "cobra", Vec3(0, 0, 15000))]
        cells = sketch.radar_contacts(self.state, 15, 5)
        self.assertEqual(cells[0][0], 0)

    def test_contact_behind_shows_as_x(self):
        self.state.contacts = [combat.make("ship", "cobra", Vec3(0, 0, -15000))]
        cells = sketch.radar_contacts(self.state, 15, 5)
        self.assertEqual(cells[0][2], "x")

    def test_height_changes_the_glyph(self):
        self.state.contacts = [combat.make("ship", "cobra", Vec3(0, 6000, 4000))]
        cells = sketch.radar_contacts(self.state, 15, 5)
        self.assertEqual(cells[0][2], "^")
        self.state.contacts = [combat.make("ship", "cobra", Vec3(0, -6000, 4000))]
        self.assertEqual(sketch.radar_contacts(self.state, 15, 5)[0][2], "v")

    def test_far_contacts_are_ignored(self):
        self.state.contacts = [combat.make("ship", "cobra", Vec3(0, 0, 90000))]
        self.assertEqual(sketch.radar_contacts(self.state, 15, 5), [])


if __name__ == "__main__":
    unittest.main()
