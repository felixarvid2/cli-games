"""3D maths and the flight model.

Conventions: local axes are x = right, y = up, z = forward. A Mat3 stores the
three local axes as columns, so `m @ v` turns a local vector into world space
and `m.t() @ v` turns a world vector into ship space (which is also the
camera transform). Ships only pitch and roll, like the original.
"""

import math
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Vec3:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __add__(self, o):
        return Vec3(self.x + o.x, self.y + o.y, self.z + o.z)

    def __sub__(self, o):
        return Vec3(self.x - o.x, self.y - o.y, self.z - o.z)

    def __mul__(self, k):
        return Vec3(self.x * k, self.y * k, self.z * k)

    __rmul__ = __mul__

    def __neg__(self):
        return Vec3(-self.x, -self.y, -self.z)

    def dot(self, o):
        return self.x * o.x + self.y * o.y + self.z * o.z

    def cross(self, o):
        return Vec3(self.y * o.z - self.z * o.y,
                    self.z * o.x - self.x * o.z,
                    self.x * o.y - self.y * o.x)

    def length(self):
        return math.sqrt(self.dot(self))

    def norm(self):
        n = self.length()
        return Vec3() if n < 1e-9 else self * (1.0 / n)

    def angle_to(self, o):
        a = self.norm()
        b = o.norm()
        return math.acos(max(-1.0, min(1.0, a.dot(b))))


class Mat3:
    __slots__ = ("c0", "c1", "c2")

    def __init__(self, c0, c1, c2):
        self.c0, self.c1, self.c2 = c0, c1, c2

    @classmethod
    def identity(cls):
        return cls(Vec3(1, 0, 0), Vec3(0, 1, 0), Vec3(0, 0, 1))

    @classmethod
    def rot_x(cls, a):
        c, s = math.cos(a), math.sin(a)
        return cls(Vec3(1, 0, 0), Vec3(0, c, s), Vec3(0, -s, c))

    @classmethod
    def rot_y(cls, a):
        c, s = math.cos(a), math.sin(a)
        return cls(Vec3(c, 0, -s), Vec3(0, 1, 0), Vec3(s, 0, c))

    @classmethod
    def rot_z(cls, a):
        c, s = math.cos(a), math.sin(a)
        return cls(Vec3(c, s, 0), Vec3(-s, c, 0), Vec3(0, 0, 1))

    def __matmul__(self, o):
        if isinstance(o, Vec3):
            return self.c0 * o.x + self.c1 * o.y + self.c2 * o.z
        return Mat3(self @ o.c0, self @ o.c1, self @ o.c2)

    def t(self):
        return Mat3(Vec3(self.c0.x, self.c1.x, self.c2.x),
                    Vec3(self.c0.y, self.c1.y, self.c2.y),
                    Vec3(self.c0.z, self.c1.z, self.c2.z))

    @property
    def right(self):
        return self.c0

    @property
    def up(self):
        return self.c1

    @property
    def forward(self):
        return self.c2

    def renormalise(self):
        """Gram-Schmidt, to stop float drift after thousands of rotations."""
        f = self.c2.norm()
        r = self.c1.cross(f).norm()
        u = f.cross(r)
        return Mat3(r, u, f)


@dataclass
class FlightModel:
    orient: Mat3 = field(default_factory=Mat3.identity)
    pos: Vec3 = field(default_factory=Vec3)
    speed: float = 0.0
    max_speed: float = 900.0
    accel: float = 700.0
    brake: float = 900.0
    pitch_rate: float = 1.15
    roll_rate: float = 2.0
    assist: float = 6.0

    @property
    def forward(self):
        return self.orient.forward

    def rotate(self, pitch, roll, dt):
        if pitch:
            self.orient = self.orient @ Mat3.rot_x(-pitch * self.pitch_rate * dt)
        if roll:
            self.orient = self.orient @ Mat3.rot_z(-roll * self.roll_rate * dt)
        if pitch or roll:
            self.orient = self.orient.renormalise()

    def thrust(self, throttle, dt):
        if throttle > 0:
            self.speed = min(self.max_speed, self.speed + self.accel * dt)
        elif throttle < 0:
            self.speed = max(0.0, self.speed - self.brake * dt)
        else:
            self.speed = max(0.0, self.speed - self.assist * dt)

    def advance(self, dt):
        self.pos = self.pos + self.forward * (self.speed * dt)

    def step(self, pitch, roll, throttle, dt):
        self.rotate(pitch, roll, dt)
        self.thrust(throttle, dt)
        self.advance(dt)

    def apply_ship(self, cfg):
        """Fit the model to a hull: speed, thrust and turn rates."""
        self.max_speed = float(cfg.max_speed)
        self.accel = float(cfg.accel)
        self.pitch_rate = float(cfg.pitch_rate)
        self.roll_rate = float(cfg.roll_rate)
        self.speed = min(self.speed, self.max_speed)
        return self

    def to_dict(self):
        return {"pos": [self.pos.x, self.pos.y, self.pos.z],
                "speed": self.speed,
                "orient": [[c.x, c.y, c.z] for c in
                           (self.orient.c0, self.orient.c1, self.orient.c2)]}

    @classmethod
    def from_dict(cls, data):
        fm = cls()
        if not data:
            return fm
        p = data.get("pos") or [0, 0, 0]
        fm.pos = Vec3(*p)
        fm.speed = float(data.get("speed", 0.0))
        ori = data.get("orient")
        if ori and len(ori) == 3:
            fm.orient = Mat3(*[Vec3(*v) for v in ori]).renormalise()
        return fm


def camera(orient, pos, world_point):
    """World point -> camera space for a ship at pos with orientation."""
    return orient.t() @ (world_point - pos)


def project(cam, width, height, focal=None):
    """Camera space -> screen cells. Returns (sx, sy, z, scale) or None."""
    if cam.z <= 1e-6:
        return None
    focal = focal or width * 0.92
    sx = width / 2.0 + cam.x / cam.z * focal
    sy = height / 2.0 - cam.y / cam.z * focal
    return sx, sy, cam.z, focal / cam.z


def in_cone(forward, to_target, cone=0.06):
    if to_target.length() < 1e-6:
        return True
    return forward.angle_to(to_target) <= cone
