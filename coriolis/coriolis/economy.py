"""Local economic events: shortages, building booms and disrupted trade.

Events are generated per system from the world seed and a time bucket, then
stored with the save. A visit never rerolls a market, so docking cannot be used
to shop around for a better event.
"""

import random
import zlib
from dataclasses import asdict, dataclass

EVENT_PERIOD = 4 * 3600.0      # a new window every four hours of flight time
EVENT_CHANCE = 0.5


@dataclass
class Event:
    kind: str
    goods: tuple
    factor: float           # price multiplier
    until: float            # absolute simulation time
    short: str              # tag shown in the market table
    text: str
    stock: float = 1.0      # local stock multiplier

    def active(self, now):
        return now < self.until

    def to_dict(self):
        data = asdict(self)
        data["goods"] = list(self.goods)
        return data

    @classmethod
    def from_dict(cls, data):
        data = dict(data)
        data["goods"] = tuple(data.get("goods") or ())
        return cls(**data)


CATALOGUE = (
    ("shortage", ("food", "liquor"), 1.55, 0.55, "SHORT",
     "Food shortage: staples are scarce"),
    ("construction", ("computers", "machinery", "alloys"), 1.45, 0.7, "BUILD",
     "Construction boom: machinery in demand"),
    ("disruption", ("minerals", "gold", "platinum"), 1.6, 0.6, "DISRUPT",
     "Trade routes disrupted: raw materials dear"),
    ("glut", ("furs", "textiles"), 0.7, 1.5, "GLUT",
     "Bumper harvest: local prices have collapsed"),
    ("festival", ("liquor", "luxuries"), 1.5, 0.8, "FEST",
     "Festival season: luxuries sell high"),
    ("medical", ("narcotics", "radioactives"), 1.35, 0.9, "MEDIC",
     "Medical emergency: supplies running out"),
)


@dataclass
class EventRecord:
    bucket: int
    events: list = None

    def to_dict(self):
        return {"bucket": self.bucket,
                "events": [e.to_dict() for e in (self.events or [])]}

    @classmethod
    def from_dict(cls, data):
        return cls(int(data.get("bucket", -1)),
                   [Event.from_dict(e) for e in (data.get("events") or [])])


def roll(seed, galaxy_no, index, bucket):
    """The events for one system in one time bucket. Deterministic."""
    salt = zlib.crc32(f"{seed}:{galaxy_no}:{index}:{bucket}".encode())
    rng = random.Random(salt)
    start = bucket * EVENT_PERIOD
    if rng.random() > EVENT_CHANCE:
        return []
    kind, goods, factor, stock, short, text = rng.choice(CATALOGUE)
    duration = rng.uniform(1.5, 3.5) * 3600.0
    jitter = rng.uniform(0.94, 1.06)
    return [Event(kind=kind, goods=goods, factor=round(factor * jitter, 3),
                  until=start + duration, short=short, text=text,
                  stock=stock)]


def merge(seed, galaxy_no, index, now, stored):
    """Current events, generating the current bucket once.

    `stored` is the persisted EventRecord for the system (or None). Returns
    (events, record) where the record is what should be saved back.
    """
    bucket = int(now // EVENT_PERIOD)
    record = stored or EventRecord(bucket, [])
    if record.bucket != bucket:
        record = EventRecord(bucket, roll(seed, galaxy_no, index, bucket))
    alive = [e for e in record.events if e.active(now)]
    record.events = alive
    return alive, record
