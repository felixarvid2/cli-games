"""The optional first flight: a contract that teaches the loop by doing it.

Objectives advance on real events (accepting, jumping, docking, delivering),
never on a timer, and the reward is paid once.
"""

from . import missions
from .data import GOOD_BY_KEY

STEPS = ("accept", "cargo", "jump", "dock", "deliver")
REWARD = 250.0
BADGE = "GRADUATE"

TEXT = {
    "accept": "Accept the delivery contract on the board (ENTER).",
    "cargo": "The cargo is aboard. Launch when you are ready.",
    "jump": "Open the chart (H) and jump to the destination.",
    "dock": "Fly the slot and dock at the destination station.",
    "deliver": "Docking delivers the freight; collect your fee.",
}


def start(pilot):
    pilot.tutorial = {"step": 0, "done": False, "rewarded": False,
                      "mid": "", "skipped": False}
    return pilot.tutorial


def skip(pilot):
    if pilot.tutorial and not pilot.tutorial.get("done"):
        pilot.tutorial["skipped"] = True
        pilot.tutorial["done"] = True
        return True
    return False


def active(pilot):
    t = pilot.tutorial or {}
    return bool(t) and not t.get("done")


def step(pilot):
    t = pilot.tutorial or {}
    index = int(t.get("step", 0))
    return STEPS[index] if index < len(STEPS) else "done"


def text(pilot):
    if not active(pilot):
        return ""
    return TEXT.get(step(pilot), "")


def _tutorial_mission(state):
    """A short hop that is always reachable on the first tank."""
    from .galaxy import neighbours
    pilot = state.pilot
    options = [(d, s) for d, s in neighbours(pilot.galaxy, pilot.system, 6.0)
               if d >= 3.0]
    if not options:
        options = neighbours(pilot.galaxy, pilot.system)
    dist, dest = options[0]
    qty = max(2, min(6, pilot.cargo_cap // 3))
    good = GOOD_BY_KEY["food"]
    return missions.Mission(
        mid=f"tutorial-{state.seed}", kind="freight",
        title=f"Freight: {qty}t {good.name} to {dest.name}",
        brief=("Your first contract: carry this freight to "
               f"{dest.name} station and dock there."),
        origin=f"{pilot.galaxy}:{pilot.system}",
        dest=f"{dest.galaxy}:{dest.index}",
        pay=REWARD, deadline=state.time + 3 * 3600.0,
        cargo_key="food", cargo_qty=qty, difficulty=1, tutorial=True)


def ensure_offer(state):
    """Put the tutorial contract on the board if it is missing."""
    if not active(state.pilot):
        return None
    missions.ensure_board(state)
    key = f"{state.pilot.galaxy}:{state.pilot.system}"
    board = state.boards.setdefault(key, {"offers": [],
                                          "next": state.time + 900.0})
    for row in board["offers"]:
        if row.get("tutorial"):
            return missions.Mission.from_dict(row)
    for mission in state.missions:
        if getattr(mission, "tutorial", False) and mission.state == "active":
            return mission
    mission = _tutorial_mission(state)
    board["offers"].insert(0, mission.to_dict())
    return mission


def notify(state, event, mission=None, dest=None):
    """Advance the tutorial from a real game event."""
    pilot = state.pilot
    if not active(pilot):
        return []
    here = step(pilot)
    notes = []
    if event == "accept":
        if mission is None or not getattr(mission, "tutorial", False):
            return []
        pilot.tutorial["mid"] = mission.mid
        pilot.tutorial["dest"] = mission.dest
        if here != "accept":
            return []
        # The freight is loaded as the contract is signed, so both the accept
        # and the cargo steps are done at once.
        pilot.tutorial["step"] = STEPS.index("jump")
        notes.append("Tutorial: cargo loaded. Launch and open the chart (H).")
    elif event == "jump":
        if here not in ("jump", "cargo"):
            return []
        # The cargo step is satisfied by accepting, so jump may follow cargo.
        if here == "cargo":
            pilot.tutorial["step"] = STEPS.index("jump")
        dest_key = pilot.tutorial.get("dest")
        if dest_key and dest is not None and dest != dest_key:
            return []
        notes.append("Tutorial: in the destination system. Fly in and dock.")
    elif event == "dock":
        dest = pilot.tutorial.get("dest")
        current = f"{pilot.galaxy}:{pilot.system}"
        if here not in ("jump", "dock"):
            return []
        if dest and current != dest:
            return []
        notes.append("Tutorial: docked. Your freight is delivered.")
    elif event == "deliver":
        if mission is None or not getattr(mission, "tutorial", False):
            return []
        if here not in ("dock", "deliver"):
            return []
    else:
        return []
    _advance(state, event, mission)
    return notes


def _advance(state, event, mission=None):
    pilot = state.pilot
    t = pilot.tutorial
    order = {"accept": 0, "cargo": 1, "jump": 2, "dock": 3, "deliver": 4}
    t["step"] = max(int(t.get("step", 0)), order[event] + 1)
    if event == "accept" and mission is not None:
        t["dest"] = mission.dest
    if t["step"] >= len(STEPS):
        finish(state)


def finish(state):
    pilot = state.pilot
    t = pilot.tutorial
    t["done"] = True
    if not t.get("rewarded"):
        pilot.credits = round(pilot.credits + REWARD, 1)
        if BADGE not in pilot.badges:
            pilot.badges.append(BADGE)
        t["rewarded"] = True
    state.say(f"Tutorial complete: +{REWARD:.0f} CR and a pilot's badge")
