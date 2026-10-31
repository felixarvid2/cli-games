import math
import unittest

import support  # noqa: F401
from coriolis.flight import (FlightModel, Mat3, Vec3, camera, in_cone,
                             project)


class VectorTest(unittest.TestCase):
    def test_basic_maths(self):
        a, b = Vec3(1, 2, 3), Vec3(4, 5, 6)
        self.assertEqual(a + b, Vec3(5, 7, 9))
        self.assertEqual(b - a, Vec3(3, 3, 3))
        self.assertEqual(a * 2, Vec3(2, 4, 6))
        self.assertEqual(a.dot(b), 32)
        self.assertEqual(a.cross(b), Vec3(-3, 6, -3))

    def test_norm_and_length(self):
        v = Vec3(3, 0, 4)
        self.assertEqual(v.length(), 5.0)
        self.assertAlmostEqual(v.norm().length(), 1.0)
        self.assertEqual(Vec3().norm(), Vec3())

    def test_angle(self):
        self.assertAlmostEqual(Vec3(0, 0, 1).angle_to(Vec3(0, 0, 1)), 0.0)
        self.assertAlmostEqual(Vec3(0, 0, 1).angle_to(Vec3(1, 0, 0)), math.pi / 2)


class MatrixTest(unittest.TestCase):
    def test_identity_maps_vectors_unchanged(self):
        m = Mat3.identity()
        self.assertEqual(m @ Vec3(1, 2, 3), Vec3(1, 2, 3))
        self.assertEqual(m.forward, Vec3(0, 0, 1))

    def test_rotation_is_orthonormal(self):
        m = Mat3.rot_x(0.7) @ Mat3.rot_z(-0.3)
        self.assertAlmostEqual(m.c0.length(), 1.0)
        self.assertAlmostEqual(m.c0.dot(m.c1), 0.0, places=9)
        self.assertAlmostEqual(m.c1.dot(m.c2), 0.0, places=9)

    def test_transpose_inverts(self):
        m = Mat3.rot_y(0.4) @ Mat3.rot_z(1.1)
        v = Vec3(5, -2, 9)
        back = m.t() @ (m @ v)
        for got, want in zip((back.x, back.y, back.z), (v.x, v.y, v.z)):
            self.assertAlmostEqual(got, want, places=9)

    def test_renormalise_removes_drift(self):
        m = Mat3.identity()
        for _ in range(20000):
            m = m @ Mat3.rot_x(0.01) @ Mat3.rot_z(0.013)
        drift = abs(m.c1.cross(m.c2).length() - 1.0)
        self.assertGreaterEqual(drift, 0.0)
        clean = m.renormalise()
        self.assertAlmostEqual(clean.c0.dot(clean.c1), 0.0, places=9)
        self.assertAlmostEqual(clean.c0.length(), 1.0, places=9)

    def test_matrix_composition_matches_vector_order(self):
        a, b = Mat3.rot_x(0.2), Mat3.rot_z(0.5)
        v = Vec3(1, 0, 0)
        self.assertEqual((a @ b) @ v, a @ (b @ v))


class CameraTest(unittest.TestCase):
    def test_camera_space_and_projection(self):
        cam = camera(Mat3.identity(), Vec3(), Vec3(0, 0, 100))
        self.assertEqual(cam, Vec3(0, 0, 100))
        sx, sy, z, _ = project(cam, 80, 24)
        self.assertAlmostEqual(sx, 40.0)
        self.assertAlmostEqual(sy, 12.0)
        self.assertEqual(z, 100)

    def test_target_off_axis_projects_off_centre(self):
        cam = camera(Mat3.identity(), Vec3(), Vec3(10, 0, 100))
        sx, sy, _, _ = project(cam, 80, 24)
        self.assertGreater(sx, 40)
        self.assertAlmostEqual(sy, 12.0)

    def test_behind_the_camera_is_not_projected(self):
        self.assertIsNone(project(Vec3(0, 0, -10), 80, 24))
        self.assertIsNone(project(Vec3(0, 0, 0), 80, 24))


class FlightModelTest(unittest.TestCase):
    def test_forward_and_movement(self):
        f = FlightModel()
        f.speed = 100
        f.advance(1.0)
        self.assertAlmostEqual(f.pos.z, 100.0)

    def test_pitch_nose_up_roll_changes_up_vector(self):
        f = FlightModel()
        f.rotate(1.0, 0.0, 0.1)
        self.assertGreater(f.forward.y, 0.0)
        f2 = FlightModel()
        f2.rotate(0.0, 1.0, 0.5)
        self.assertNotEqual(f2.orient.up, Vec3(0, 1, 0))

    def test_assist_bleeds_speed_off(self):
        f = FlightModel(speed=500)
        for _ in range(100):
            f.step(0, 0, 0, 1 / 60)
        self.assertLess(f.speed, 500)
        for _ in range(12000):
            f.step(0, 0, 0, 1 / 60)
        self.assertEqual(f.speed, 0.0)

    def test_thrust_never_exceeds_max(self):
        f = FlightModel(speed=900.0)
        f.step(0, 0, 1, 10.0)
        self.assertLessEqual(f.speed, f.max_speed)

    def test_orientation_stays_orthonormal_while_turning(self):
        f = FlightModel()
        for _ in range(5000):
            f.rotate(0.9, -0.7, 1 / 60)
        self.assertAlmostEqual(f.orient.c0.dot(f.orient.c1), 0.0, places=6)
        self.assertAlmostEqual(f.orient.c2.length(), 1.0, places=6)

    def test_save_round_trip(self):
        f = FlightModel(pos=Vec3(1, 2, 3), speed=42)
        f.rotate(1, 1, 0.3)
        again = FlightModel.from_dict(f.to_dict())
        self.assertAlmostEqual(again.pos.z, 3.0)
        self.assertAlmostEqual(again.speed, 42.0)
        self.assertAlmostEqual(again.forward.x, f.forward.x, places=6)


class ConeTest(unittest.TestCase):
    def test_cone(self):
        self.assertTrue(in_cone(Vec3(0, 0, 1), Vec3(0, 0, 5), 0.1))
        self.assertFalse(in_cone(Vec3(0, 0, 1), Vec3(5, 0, 1), 0.1))
        self.assertTrue(in_cone(Vec3(0, 0, 1), Vec3(0, 0, 0)))


if __name__ == "__main__":
    unittest.main()
