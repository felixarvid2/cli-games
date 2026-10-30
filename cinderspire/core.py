"""Game rules for CINDERSPIRE: map, run state, combat engine."""

import json
import os
import random

from .data import (ACHIEVEMENTS, BOSSES, CARDS, CLASSES, ELITES, ENCOUNTERS,
                   ENEMIES, EVENTS, POOL, POTIONS, RELICS, STARTERS)
from .board_data import BOARD_CARDS, STARTER_DECKS, POOL as BPOOL

DATA_DIR = os.path.join(
    os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share")),
    "cinderspire")
SAVE_PATH = os.path.join(DATA_DIR, "save.json")
RUN_PATH = os.path.join(DATA_DIR, "run.json")
LEGACY_SAVE = os.path.expanduser("~/.cinderspire.json")
LEGACY_RUN = os.path.expanduser("~/.cinderspire_run.json")
SAVE_VERSION = 4
RUN_VERSION = 2
FLOORS = 7
ACT_FLOORS = [7, 7, 7, 4]
ACTS = 4
TOTAL_FLOORS = sum(ACT_FLOORS)
ACT_NAMES = ["THE ASHFALL GATE", "THE GILDED HOLLOW", "THE CINDER THRONE",
             "THE EMBER HEART"]
DEBUG = os.environ.get("CINDERSPIRE_DEBUG") == "1"


# ------------------------------------------------------------- card helpers

def inst(cid, up=0):
    return {"id": cid, "up": up}


def cdata(c):
    """Merged card definition for an instance (applies upgrades)."""
    base = CARDS[c["id"]]
    d = dict(base)
    if c.get("up"):
        times = 1
        if base.get("multi_up"):
            times = c.get("ups", 1)
        for k, v in base.get("up", {}).items():
            cur = d.get(k, 0)
            if isinstance(v, (int, float)) and isinstance(cur, (int, float)):
                d[k] = cur + v * times
            else:
                d[k] = v
        d["name"] = base["name"] + "+" * (times if base.get("multi_up") else 1)
        d["upgraded"] = True
    return d


def can_upgrade(c):
    return c.get("up", 0) < 2


AUTO_LINES = {
    "dmg": "Deal {0} damage.",
    "all": "Deal {0} damage to ALL enemies.",
    "random": "Deal {0} damage to a random enemy.",
    "block": "Gain {0} Block.",
    "draw": "Draw {0} card(s).",
    "energy": "Gain {0} Energy.",
    "heal": "Heal {0} HP.",
    "lose_hp": "Lose {0} HP.",
    "vuln": "Apply {0} Vulnerable.",
    "weak": "Apply {0} Weak.",
    "poison": "Apply {0} Poison.",
    "str": "Gain {0} Strength.",
    "dex": "Gain {0} Dexterity.",
    "thorns_tmp": "Gain {0} Thorns this turn.",
    "add_shiv": "Add {0} Shivs to your hand.",
    "add_burn": "Add {0} Burn to your discard.",
    "vuln_all": "Apply {0} Vulnerable to ALL.",
    "weak_all": "Apply {0} Weak to ALL.",
    "poison_all": "Apply {0} Poison to ALL.",
    "metallicize": "Gain {0} Metallicize.",
    "thorns": "Gain {0} Thorns.",
    "regen": "Gain {0} Regeneration.",
    "exhaust_hand": "Exhaust your hand.",
    "double_poison": "Double the target's Poison.",
    "headbutt": "Put a discard card on top of your draw pile.",
    "hologram": "Return a random discard card to your hand.",
    "upgrade_hand": "Upgrade a random card in your hand.",
    "double_str": "Double your Strength.",
    "leech": "Deal {0} damage to ALL. Heal for unblocked damage.",
    "self_vuln": "Gain {0} Vulnerable.",
    "envenom": "Attacks apply {0} Poison.",
    "divine": "At the start of your turn, gain {0} Block.",
    "shield": "Gain {0} Divine Shield.",
    "add_recruit": "Add {0} Silver Hand Recruits to your hand.",
    "aura": "Attacks deal {0} extra damage.",
    "strip_block": "Remove all enemy Block.",
    "lightbringer": "At the start of your turn, add 1 Silver Hand Recruit.",
    "draw_if_poisoned": "Draw {0} card(s) if the target is Poisoned.",
}


def auto_text(cd):
    lines = []
    for item in cd.get("effects", []):
        op = item[0]
        args = item[1:]
        tmpl = AUTO_LINES.get(op)
        if not tmpl:
            continue
        if not args:
            lines.append(tmpl)
            continue
        a0 = cd.get(args[0], 0) if isinstance(args[0], str) else args[0]
        times = 1
        if len(args) > 1:
            times = cd.get(args[1], 1) if isinstance(args[1], str) else args[1]
        s = tmpl.format(a0)
        if times and times > 1 and op in ("dmg", "all", "random", "leech"):
            s = s.rstrip(".")
            s = s.replace("damage", f"damage {times} times", 1)
        lines.append(s)
    return "\n".join(lines)


def ctext(cd):
    if cd.get("auto_text"):
        return auto_text(cd)
    vals = {"d": cd.get("dmg", 0), "b": cd.get("block", 0),
            "m": cd.get("magic", 0), "h": cd.get("hits", 1),
            "l": cd.get("hp_loss", 0)}
    try:
        return cd["text"].format(**vals)
    except (KeyError, IndexError):
        return cd["text"]


def card_cost(cd):
    return cd["cost"]


# ------------------------------------------------------------------ statuses

def st(f, key):
    return f.st.get(key, 0)


def add_st(f, key, n):
    f.st[key] = max(0, f.st.get(key, 0) + n)


class Fighter:
    def __init__(self, name, hp, max_hp=None, color="text"):
        self.name = name
        self.hp = hp
        self.max_hp = max_hp if max_hp is not None else hp
        self.block = 0
        self.st = {}
        self.alive = True
        self.defn = None
        self.next_move = None
        self.history = []
        self.used = {}
        self.color = color


# -------------------------------------------------------------------- combat

class Combat:
    def __init__(self, run, ids, kind="normal", rng=None):
        self.run = run
        self.rng = rng or random.Random()
        self.kind = kind
        self.floor = run.floor
        self.logs = []
        self.player = Fighter("You", run.hp, run.max_hp, "white")
        self.enemies = []
        act_mult = 1.0 if kind == "boss" else 1.0 + 0.08 * getattr(run, "act", 0)
        mult = (1.0 + (0.02 * self.floor if kind == "normal" else 0.0)) * \
            act_mult * (1.0 + 0.11 * getattr(run, "ascension", 0))
        counts = {}
        for eid in ids:
            d = ENEMIES[eid]
            hp = max(1, int(self.rng.randint(*d["hp"]) * mult))
            f = Fighter(d["name"], hp, hp, d["color"])
            f.defn = d
            if getattr(run, "ascension", 0):
                add_st(f, "str", run.ascension)
            self.enemies.append(f)
            counts[d["name"]] = counts.get(d["name"], 0) + 1
        if any(v > 1 for v in counts.values()):
            seen = {}
            for f in self.enemies:
                if counts[f.name] > 1:
                    i = seen.get(f.name, 0)
                    seen[f.name] = i + 1
                    f.name = f"{f.name} {chr(65 + i)}"
        self.draw_pile = [dict(c) for c in run.deck]
        self.rng.shuffle(self.draw_pile)
        self.hand = []
        self.discard = []
        self.exhausted = []
        self.powers = []
        self.energy = 0
        self.max_energy = 3
        self.turn = 0
        self.phase = "player"       # player | enemy | won | lost
        self.pending = []
        self.C = None
        self.target = None
        self.attacks_played = 0
        self.skills_played = 0
        self.damage_dealt = 0
        self.best_hit = 0
        self.dmg_mult = 1
        self.popups = {}            # id(fighter) -> [text, color, ttl]
        self.shake = {}             # id(fighter) -> ttl
        self.flash = {}             # id(fighter) -> ttl
        self.start()

    # -- helpers -----------------------------------------------------------
    def log(self, msg, color="text"):
        self.logs.append((msg, color))
        if len(self.logs) > 60:
            self.logs.pop(0)

    def relic(self, rid):
        return rid in self.run.relics

    def popup(self, f, text, color="red"):
        self.popups[id(f)] = [text, color, 0.8]

    def alive_enemies(self):
        return [e for e in self.enemies if e.alive]

    def sync_player(self):
        self.run.hp = max(0, self.player.hp)

    def draw(self, n):
        for _ in range(n):
            if len(self.hand) >= 10:
                return
            if not self.draw_pile:
                if not self.discard:
                    if not getattr(self, "_deck_out_logged", False):
                        self._deck_out_logged = True
                        self.log("Your deck is empty - no card drawn.", "dim")
                    return
                self.draw_pile = self.discard
                self.discard = []
                self.rng.shuffle(self.draw_pile)
                self.log("Reshuffled discard into draw pile.", "dim")
            self.hand.append(self.draw_pile.pop())

    # -- damage ------------------------------------------------------------
    def deal(self, target, dmg, attacker=None, thorns=True):
        if not target.alive or dmg <= 0:
            return 0
        if (target is self.player and st(self.player, "shield") > 0):
            add_st(self.player, "shield", -1)
            self.popup(self.player, "SHIELD", "gold")
            self.log("Divine Shield absorbs the hit.", "gold")
            return 0
        blocked = min(target.block, dmg)
        target.block -= blocked
        loss = dmg - blocked
        if loss:
            target.hp -= loss
            self.popup(target, f"-{loss}", "red")
            # feedback tiers: small hits barely move, big hits punch
            if loss >= 16:
                self.shake[id(target)] = 0.35
                self.flash[id(target)] = 0.16
            elif loss >= 8:
                self.shake[id(target)] = 0.22
                self.flash[id(target)] = 0.09
            else:
                self.shake[id(target)] = 0.10
            if target is self.player:
                self.log(f"You take {loss} damage.", "red")
            else:
                self.damage_dealt += loss
                self.best_hit = max(self.best_hit, dmg)
        else:
            self.popup(target, "blocked", "blue")
        if blocked and target is self.player:
            self.log(f"You block {blocked} damage.", "blue")
        if target.hp <= 0:
            target.hp = 0
            target.alive = False
            if target is self.player:
                self.sync_player()
                self.phase = "lost"
                self.log("You collapse into the ash.", "red")
            else:
                self.log(f"{target.name} is destroyed.", "green")
                self.popup(target, "\u2620", "red")
                self.on_kill(target)
        if (thorns and target is self.player and attacker is not None
                and attacker.alive and st(self.player, "thorns") > 0
                and loss > 0):
            th = st(self.player, "thorns")
            attacker.hp -= th
            self.popup(attacker, f"-{th}", "green")
            self.log(f"Thorns sting {attacker.name} for {th}.", "green")
            if attacker.hp <= 0:
                attacker.hp = 0
                attacker.alive = False
                self.log(f"{attacker.name} is destroyed.", "green")
                self.on_kill(attacker)
        return loss

    def on_kill(self, f):
        if self.relic("gremlin_horn"):
            self.gain_energy(1)
            self.draw(1)
            self.log("Gremlin Horn: +1 Energy, draw 1.", "gold")
        if not self.alive_enemies() and self.phase != "lost":
            self.phase = "won"

    def atk(self, target, base, times=1, str_mult=1):
        for _ in range(times):
            if target is None or not target.alive:
                return
            dmg = base + st(self.player, "str") * str_mult \
                + st(self.player, "aura")
            if self.relic("twin_fangs"):
                dmg += 2
            if self.relic("whetstone"):
                dmg += 1
            if st(target, "vuln") > 0:
                dmg = int(dmg * 1.5)
            if st(self.player, "weak") > 0:
                dmg = int(dmg * 0.75)
            dmg *= self.dmg_mult
            self.deal(target, max(0, dmg))
            if not self.player.alive or self.phase == "won":
                return

    def atk_all(self, base, times=1):
        for _ in range(times):
            for e in self.alive_enemies():
                self.atk(e, base)
                if self.phase == "won":
                    return

    def atk_random(self, base, times=1):
        for _ in range(times):
            alive = self.alive_enemies()
            if not alive:
                return
            self.atk(self.rng.choice(alive), base)

    def leech_all(self, base):
        healed = 0
        for e in list(self.alive_enemies()):
            before = e.hp
            self.atk(e, base)
            healed += max(0, before - e.hp)
        if healed:
            self.heal(healed)
            self.log(f"Reaper drains {healed} HP.", "green")

    def block(self, n):
        if n <= 0:
            return
        self.player.block += n + st(self.player, "dex")
        if st(self.player, "juggernaut") > 0:
            alive = self.alive_enemies()
            if alive:
                e = self.rng.choice(alive)
                dmg = st(self.player, "juggernaut")
                self.deal(e, dmg)
                self.log(f"Juggernaut slams {e.name} for {dmg}.", "orange")

    def heal(self, n):
        p = self.player
        p.hp = min(p.max_hp, p.hp + n)
        self.sync_player()

    def lose_hp(self, n):
        p = self.player
        p.hp -= n
        self.popup(p, f"-{n}", "red")
        if p.hp <= 0:
            p.hp = 0
            p.alive = False
            self.phase = "lost"
            self.log("Your blood runs out.", "red")
        self.sync_player()

    def status(self, target, key, n):
        if target is None or not target.alive:
            return
        add_st(target, key, n)
        label = {"vuln": "Vulnerable", "weak": "Weak", "frail": "Frail",
                 "poison": "Poison", "str": "Strength", "dex": "Dexterity",
                 "str_tmp": "Strength", "metallicize": "Metallicize",
                 "demon": "Demon Form", "regen": "Regeneration",
                 "thorns": "Thorns", "juggernaut": "Juggernaut",
                 "blur": "Blur", "berserk": "Berserk"}.get(key, key)
        who = "You" if target is self.player else target.name
        verb = "gain" if target is self.player else "gains"
        self.log(f"{who} {verb} {n} {label}.", "purple")

    def status_all(self, key, n):
        for e in self.alive_enemies():
            self.status(e, key, n)

    def gain_energy(self, n):
        self.energy += n

    def exhaust_random(self):
        if self.hand:
            c = self.rng.choice(self.hand)
            self.take_obj(self.hand, c)
            self.exhausted.append(c)
            self.log(f"Exhausted {cdata(c)['name']}.", "dim")

    def upgrade_hand(self):
        pool = [c for c in self.hand if not c.get("up")]
        n = self.C.get("magic", 1) if self.C else 1
        upgraded = 0
        for c in self.rng.sample(pool, min(n, len(pool))):
            c["up"] = 1
            upgraded += 1
            self.log(f"{cdata(c)['name']} was upgraded.", "gold")
        if not upgraded:
            self.log("Nothing to upgrade.", "dim")

    def dup_to_discard(self):
        if self.C:
            self.discard.append({"id": self.C["id"], "up": 1 if self.C.get("upgraded") else 0})
            self.log(f"A copy of {self.C['name']} joins your discard.", "purple")

    def double_strength(self):
        s = st(self.player, "str")
        add_st(self.player, "str", s)
        self.log(f"Strength doubled to {st(self.player, 'str')}.", "orange")

    def dropkick(self):
        if self.target is not None and st(self.target, "vuln") > 0:
            self.gain_energy(1)
            self.draw(1)
            self.log("Dropkick: +1 Energy, draw 1.", "gold")
        self.atk(self.target, self.C["dmg"])

    def fiend_fire(self):
        n = len(self.hand)
        self.exhausted.extend(self.hand)
        self.hand = []
        self.log(f"Fiend Fire consumes {n} cards.", "orange")
        for _ in range(n):
            if self.target is None or not self.target.alive:
                return
            self.atk(self.target, self.C["dmg"])

    def feed(self):
        t = self.target
        self.atk(t, self.C["dmg"])
        if t is not None and not t.alive:
            self.player.max_hp += 3
            self.player.hp += 3
            self.run.max_hp += 3
            self.sync_player()
            self.log("Feed: max HP increased by 3.", "green")

    def add_status_card(self, cid, n=1):
        for _ in range(n):
            self.discard.append({"id": cid, "up": 0})
        self.log(f"{cdata({'id': cid})['name']} x{n} added to your discard.",
                 "orange")

    def cauterize(self):
        n = 0
        for c in list(self.hand):
            if CARDS[c["id"]].get("rarity") == "status":
                self.take_obj(self.hand, c)
                self.exhausted.append(c)
                n += 1
        if n:
            self.heal(self.C["magic"] * n)
            self.log(f"Cauterize burns away {n} cards.", "green")
        else:
            self.log("No Burns to cauterize.", "dim")

    def pyre(self):
        n = len(self.hand)
        self.exhausted.extend(self.hand)
        self.hand = []
        self.draw(n + self.C["magic"])
        self.log(f"Pyre consumes {n} cards.", "orange")

    def run_effects(self, eff):
        def v(x):
            return self.C.get(x, 0) if isinstance(x, str) else x

        for item in eff:
            op = item[0]
            a = item[1:]
            if op == "dmg":
                self.atk(self.target, v(a[0]), times=v(a[1]) if len(a) > 1 else 1)
            elif op == "all":
                self.atk_all(v(a[0]), times=v(a[1]) if len(a) > 1 else 1)
            elif op == "random":
                self.atk_random(v(a[0]), times=v(a[1]) if len(a) > 1 else 1)
            elif op == "block":
                self.block(v(a[0]))
            elif op == "draw":
                self.draw(v(a[0]))
            elif op == "energy":
                self.gain_energy(v(a[0]))
            elif op == "heal":
                self.heal(v(a[0]))
            elif op == "lose_hp":
                self.lose_hp(v(a[0]))
            elif op == "vuln":
                self.status(self.target, "vuln", v(a[0]))
            elif op == "weak":
                self.status(self.target, "weak", v(a[0]))
            elif op == "poison":
                self.status(self.target, "poison", v(a[0]))
            elif op == "str":
                self.status(self.player, "str", v(a[0]))
            elif op == "dex":
                self.status(self.player, "dex", v(a[0]))
            elif op == "thorns_tmp":
                self.status(self.player, "thorns_tmp", v(a[0]))
                self.status(self.player, "thorns", v(a[0]))
            elif op == "thorns":
                self.status(self.player, "thorns", v(a[0]))
            elif op == "metallicize":
                self.status(self.player, "metallicize", v(a[0]))
            elif op == "regen":
                self.status(self.player, "regen", v(a[0]))
            elif op == "add_shiv":
                self.add_shivs(v(a[0]))
            elif op == "add_burn":
                self.add_status_card("burn", v(a[0]))
            elif op == "vuln_all":
                self.status_all("vuln", v(a[0]))
            elif op == "weak_all":
                self.status_all("weak", v(a[0]))
            elif op == "poison_all":
                self.status_all("poison", v(a[0]))
            elif op == "self_vuln":
                self.status(self.player, "vuln", v(a[0]))
            elif op == "exhaust_hand":
                self.exhausted.extend(self.hand)
                self.hand = []
            elif op == "double_poison":
                self.catalyst()
            elif op == "headbutt":
                self.headbutt()
            elif op == "hologram":
                self.hologram()
            elif op == "upgrade_hand":
                self.upgrade_hand()
            elif op == "double_str":
                self.double_strength()
            elif op == "leech":
                self.leech_all(v(a[0]))
            elif op == "envenom":
                self.status(self.player, "envenom", v(a[0]))
            elif op == "divine":
                self.status(self.player, "divine", v(a[0]))
            elif op == "shield":
                self.status(self.player, "shield", v(a[0]))
            elif op == "aura":
                self.status(self.player, "aura", v(a[0]))
            elif op == "lightbringer":
                self.status(self.player, "lightbringer", v(a[0]))
            elif op == "add_recruit":
                self.add_recruits(v(a[0]))
            elif op == "draw_if_poisoned":
                self.draw_if_poisoned(v(a[0]))
            elif op == "strip_block":
                for e in self.alive_enemies():
                    e.block = 0
                self.log("Every guard is lowered.", "gold")

    def add_recruits(self, n):
        added = 0
        for _ in range(n):
            if len(self.hand) >= 10:
                break
            self.hand.append({"id": "recruit", "up": 0})
            added += 1
        if added:
            self.log(f"{added} Silver Hand Recruits rally to you.", "gold")

    def add_shivs(self, n):
        added = 0
        for _ in range(n):
            if len(self.hand) >= 10:
                break
            self.hand.append({"id": "shiv", "up": 0})
            added += 1
        if added:
            self.log(f"{added} Shivs appear in your hand.", "green")

    def bonus_if_burn(self, base, bonus):
        if any(c["id"] == "burn" for c in self.hand):
            self.atk(self.target, base + bonus)
            self.log("The Burn feeds the strike.", "orange")
        else:
            self.atk(self.target, base)

    def draw_if_poisoned(self, n):
        if self.target is not None and st(self.target, "poison") > 0:
            self.draw(n)
            self.log("The poison opens a gap.", "green")

    def catalyst(self):
        t = self.target
        if t is not None and t.alive:
            p = st(t, "poison")
            add_st(t, "poison", p)
            self.log(f"Catalyst doubles {t.name}'s Poison to {st(t, 'poison')}.",
                     "green")

    def bonus_if_poisoned(self, base, bonus):
        t = self.target
        if t is not None and st(t, "poison") > 0:
            self.atk(t, base + bonus)
            self.log("The poison does its work.", "green")
        else:
            self.atk(t, base)

    def hologram(self):
        if self.discard and len(self.hand) < 10:
            c = self.rng.choice(self.discard)
            self.take_obj(self.discard, c)
            self.hand.append(c)
            self.log(f"{cdata(c)['name']} returns from the discard.", "blue")

    def zeal(self):
        self.atk(self.target, self.C["dmg"] + self.player.block // 3)

    def martyr(self):
        missing = self.player.max_hp - self.player.hp
        self.atk(self.target, self.C["dmg"] + missing // 4)

    def headbutt(self):
        if not self.discard:
            return
        c = self.rng.choice(self.discard)
        self.take_obj(self.discard, c)
        self.draw_pile.append(c)
        self.log(f"{cdata(c)['name']} goes on top of your draw pile.", "blue")

    def second_wind(self):
        n = 0
        for c in list(self.hand):
            if cdata(c)["type"] != "attack":
                self.take_obj(self.hand, c)
                self.exhausted.append(c)
                n += 1
        if n:
            self.block(self.C["block"] * n)
            self.log(f"Second Wind exhausts {n} cards.", "blue")

    def whirlwind(self):
        x = self.energy
        self.energy = 0
        for _ in range(x):
            self.atk_all(self.C["dmg"])
            if self.phase == "won":
                return

    # -- turn flow ---------------------------------------------------------
    def start(self):
        self.log("A battle begins.", "dim")
        if self.relic("blood_vial"):
            self.heal(2)
        if self.relic("vajra"):
            add_st(self.player, "str", 1)
        if self.relic("smooth_stone"):
            add_st(self.player, "dex", 1)
        if self.relic("anchor"):
            self.player.block += 10
        if self.relic("bronze_scales"):
            add_st(self.player, "thorns", 3)
        if self.relic("molten_core"):
            add_st(self.player, "str", 2)
        if self.relic("bastion"):
            add_st(self.player, "dex", 1)
            self.player.block += 8
        if self.relic("choir_bell"):
            self.player.block += 4
        if self.relic("ashen_wings"):
            add_st(self.player, "dex", 2)
        for e in self.enemies:
            self.choose_move(e)
        self.start_player_turn(first=True)

    def start_player_turn(self, first=False):
        self.turn += 1
        self._deck_out_logged = False
        p = self.player
        if st(p, "blur") > 0:
            add_st(p, "blur", -1)
            self.log("Blur keeps your Block.", "blue")
        else:
            p.block = 0
        if st(p, "poison") > 0:
            n = st(p, "poison")
            p.hp -= n
            add_st(p, "poison", -1)
            self.popup(p, f"-{n}", "green")
            self.log(f"Poison deals {n} damage.", "green")
            if p.hp <= 0:
                p.hp = 0
                p.alive = False
                self.phase = "lost"
                self.sync_player()
                return
            self.sync_player()
        if st(p, "demon") > 0:
            add_st(p, "str", st(p, "demon"))
            self.log(f"Demon Form: +{st(p, 'demon')} Strength.", "purple")
        if st(p, "metallicize") > 0:
            self.block(st(p, "metallicize"))
        if st(p, "divine") > 0:
            self.block(st(p, "divine"))
        self.energy = 3 + st(p, "berserk") + st(p, "fusion")
        if self.relic("throne"):
            self.energy += 1
        if self.relic("crown_flame"):
            self.energy += 1
        if self.relic("sundial") and self.turn % 3 == 0:
            self.energy += 1
            self.log("Sundial: +1 Energy.", "gold")
        if first and self.relic("lantern"):
            self.energy += 1
        n = 5 + (2 if first and self.relic("bag_of_prep") else 0)
        if self.relic("hourglass"):
            n += 1
        if first and self.relic("choir_bell"):
            n += 1
        n += st(p, "machine") - st(p, "fusion")
        n = max(0, n)
        self.draw(n)
        if st(p, "lightbringer") > 0:
            self.add_recruits(st(p, "lightbringer"))
        self.phase = "player"
        self.log(f"-- Turn {self.turn} --", "dim")

    def end_turn(self):
        if self.phase != "player":
            return
        p = self.player
        if st(p, "metallicize") > 0:
            self.block(st(p, "metallicize"))
        if st(p, "divine") > 0:
            self.block(st(p, "divine"))
        if self.relic("orichalcum") and p.block == 0:
            self.block(6)
            self.log("Orichalcum grants 6 Block.", "gold")
        if st(p, "combust") > 0:
            self.lose_hp(1)
            if self.phase == "lost":
                return
            self.atk_all(st(p, "combust"))
            if self.phase == "won":
                return
        if st(p, "regen") > 0:
            n = st(p, "regen")
            self.heal(n)
            add_st(p, "regen", -1)
            self.log(f"Regeneration heals {n} HP.", "green")
        if st(p, "str_tmp") > 0:
            add_st(p, "str", -st(p, "str_tmp"))
            p.st["str_tmp"] = 0
        if st(p, "thorns_tmp") > 0:
            add_st(p, "thorns", -st(p, "thorns_tmp"))
            p.st["thorns_tmp"] = 0
        if st(p, "rage") > 0:
            p.st["rage"] = 0
        for k in ("vuln", "weak", "frail"):
            if st(p, k) > 0:
                add_st(p, k, -1)
        for c in list(self.hand):
            if c["id"] == "burn":
                self.take_obj(self.hand, c)
                self.exhausted.append(c)
                self.log("Burn sears you for 2.", "orange")
                self.lose_hp(2)
                if self.phase == "lost":
                    return
        self.discard.extend(self.hand)
        self.hand = []
        self.phase = "enemy"
        self.pending = [e for e in self.enemies if e.alive]
        for e in list(self.pending):
            if st(e, "poison") > 0:
                n = st(e, "poison")
                e.hp -= n
                add_st(e, "poison", -1)
                self.popup(e, f"-{n}", "green")
                self.log(f"Poison deals {n} damage to {e.name}.", "green")
                if e.hp <= 0:
                    e.hp = 0
                    e.alive = False
                    self.log(f"{e.name} dissolves.", "green")
                    self.on_kill(e)
        self.pending = [e for e in self.pending if e.alive]
        self.log("Your turn ends.", "dim")
        if DEBUG:
            self.validate()

    def step_enemy(self):
        """Resolve one enemy action. Returns True when the enemy phase is done."""
        if self.phase != "enemy":
            return True
        while self.pending:
            e = self.pending.pop(0)
            if e.alive:
                self.enemy_act(e)
                if self.phase == "lost":
                    return True
                if e.alive:
                    self.choose_move(e)
                return False
        for e in self.enemies:
            for k in ("vuln", "weak"):
                if st(e, k) > 0:
                    add_st(e, k, -1)
        if self.phase == "enemy":
            if self.alive_enemies():
                self.start_player_turn()
            else:
                self.phase = "won"
        return True

    def choose_move(self, e):
        moves = e.defn["moves"]
        if e.defn["ai"] == "ritual" and "ritual" not in e.used:
            e.used["ritual"] = True
            e.next_move = moves[0]
            return
        cand = [m for m in moves if not (m["once"] and m["name"] + "#once" in e.used)]
        if len(e.history) >= 2 and e.history[-1] == e.history[-2]:
            alt = [m for m in cand if m["name"] != e.history[-1]]
            if alt:
                cand = alt
        total = sum(m["weight"] for m in cand)
        r = self.rng.uniform(0, total)
        for m in cand:
            r -= m["weight"]
            if r <= 0:
                if m["once"]:
                    e.used[m["name"] + "#once"] = True
                e.next_move = m
                e.history.append(m["name"])
                return
        e.next_move = cand[-1]
        e.history.append(cand[-1]["name"])

    def enemy_act(self, e):
        m = e.next_move
        if m is None:
            return
        if e.defn["ai"] == "boss" and e.hp < e.max_hp * 0.5 and not e.used.get("enrage"):
            e.used["enrage"] = True
            add_st(e, "str", 3)
            e.block += 12
            self.log("The Cinder King's crown flares white-hot!", "gold")
            return
        self.log(f"{e.name} uses {m['name']}.", "dim")
        if m["dmg"]:
            self.enemy_attack(e, m["dmg"], m["hits"])
        if m["block"]:
            e.block += m["block"]
        if m["heal"]:
            e.hp = min(e.max_hp, e.hp + m["heal"])
        if m.get("cards"):
            cid, n = m["cards"]
            self.add_status_card(cid, n)
        if m.get("gold"):
            stolen = min(self.run.gold, m["gold"])
            if stolen:
                self.run.gold -= stolen
                self.log(f"{e.name} steals {stolen} gold!", "gold")
        if m["status"]:
            key, n = m["status"]
            if m["kind"] == "debuff":
                self.status(self.player, key, n)
            else:
                add_st(e, key, n)
                self.log(f"{e.name} gains {n} {key}.", "purple")

    def enemy_attack(self, e, base, hits=1):
        for _ in range(hits):
            if not self.player.alive:
                return
            dmg = base + st(e, "str")
            if st(self.player, "vuln") > 0:
                dmg = int(dmg * 1.5)
            if st(e, "weak") > 0:
                dmg = int(dmg * 0.75)
            dmg = max(0, dmg)
            self.deal(self.player, dmg, attacker=e)
            if self.phase == "lost" or not e.alive:
                return

    @staticmethod
    def take_obj(lst, obj):
        """Remove by identity, never by equality: duplicate cards compare equal."""
        for i, x in enumerate(lst):
            if x is obj:
                return lst.pop(i)
        return None

    def zone_integrity(self):
        """Every card object lives in exactly one zone (hand/draw/discard/exhaust/powers)."""
        seen = set()
        for zone in (self.draw_pile, self.hand, self.discard,
                     self.exhausted, self.powers):
            for c in zone:
                if id(c) in seen:
                    return False
                seen.add(id(c))
        return True

    def validate(self):
        """Defense in depth: cheap invariants checked after every action in debug runs."""
        problems = []
        if self.energy < 0:
            problems.append(f"negative energy {self.energy}")
        for f in [self.player] + self.enemies:
            if not (0 <= f.hp <= f.max_hp):
                problems.append(f"{f.name} hp {f.hp}/{f.max_hp}")
            if f.alive != (f.hp > 0):
                problems.append(f"{f.name} alive flag out of sync")
            if f.block < 0:
                problems.append(f"{f.name} negative block")
        if not self.zone_integrity():
            problems.append("a card is in two zones")
        if problems:
            raise AssertionError("; ".join(problems))

    def use_potion(self, i, target_idx=None):
        if not (0 <= i < len(self.run.potions)):
            return False
        if self.phase != "player":
            return False
        pid = self.run.potions[i]
        alive = self.alive_enemies()
        tgt = None
        if target_idx is not None and 0 <= target_idx < len(self.enemies):
            tgt = self.enemies[target_idx]
        if tgt is None or not tgt.alive:
            tgt = alive[0] if alive else None
        self.run.potions.pop(i)
        self.log(f"You drink a {POTIONS[pid]['name']}.", "white")
        if pid == "fire" and tgt:
            self.deal(tgt, 20)
        elif pid == "block":
            self.block(12)
        elif pid == "strength":
            add_st(self.player, "str", 2)
        elif pid == "swift":
            self.draw(3)
        elif pid == "energy":
            self.gain_energy(2)
        elif pid == "fear" and tgt:
            self.status(tgt, "vuln", 3)
        elif pid == "regen":
            self.heal(12)
        elif pid == "poison" and tgt:
            self.status(tgt, "poison", 6)
        elif pid == "steel":
            self.status(self.player, "metallicize", 4)
        elif pid == "memories":
            if self.discard and len(self.hand) < 10:
                c = self.rng.choice(self.discard)
                self.take_obj(self.discard, c)
                self.hand.append(c)
                self.log(f"{cdata(c)['name']} returns to your hand.", "purple")
        elif pid == "firestorm":
            self.atk_all(15)
        elif pid == "ember_blood":
            self.heal(25)
        elif pid == "juice":
            self.player.max_hp += 5
            self.player.hp += 5
            self.run.max_hp += 5
            self.sync_player()
        return True

    # -- playing cards -----------------------------------------------------
    def can_play(self, i):
        if not (0 <= i < len(self.hand)):
            return False
        cd = cdata(self.hand[i])
        if cd["type"] == "status" or cd["cost"] < -1:
            return False
        if cd["cost"] < 0:
            return self.energy > 0
        return cd["cost"] <= self.energy

    def play_card(self, i, target_idx=None):
        if self.phase != "player" or not (0 <= i < len(self.hand)):
            return False
        c = self.hand[i]
        cd = cdata(c)
        if cd["type"] == "status":
            return False
        if cd["cost"] < 0:
            if self.energy <= 0:
                return False
        elif cd["cost"] > self.energy:
            return False
        targets = self.alive_enemies()
        if not targets and cd["type"] == "attack":
            return False
        if cd["target"] == "enemy":
            if target_idx is not None and 0 <= target_idx < len(self.enemies) and self.enemies[target_idx].alive:
                tgt = self.enemies[target_idx]
            else:
                tgt = targets[0] if targets else None
        elif cd["target"] == "all":
            tgt = None
        else:
            tgt = None
        self.hand.pop(i)
        x_cost = cd["cost"] < 0
        if x_cost:
            pass
        else:
            self.energy -= cd["cost"]
        self.C = cd
        self.target = tgt
        self.dmg_mult = 1
        if cd["type"] == "attack":
            self.attacks_played += 1
            if self.attacks_played % 3 == 0:
                if self.relic("kunai"):
                    add_st(self.player, "dex", 1)
                    self.log("Kunai: +1 Dexterity.", "green")
                if self.relic("shuriken"):
                    add_st(self.player, "str", 1)
                    self.log("Shuriken: +1 Strength.", "orange")
            if self.relic("pen_nib") and self.attacks_played % 10 == 0:
                self.dmg_mult = 2
                self.log("Pen Nib: double damage!", "gold")
        self.log(f"You play {cd['name']}.", "white")
        try:
            cd["play"](self)
            if cd["type"] == "attack" and st(self.player, "rage") > 0:
                self.block(st(self.player, "rage"))
            if cd["type"] == "attack" and st(self.player, "envenom") > 0:
                n = st(self.player, "envenom")
                if cd["target"] == "all":
                    self.status_all("poison", n)
                elif self.target is not None and self.target.alive:
                    self.status(self.target, "poison", n)
            if cd["type"] == "skill":
                self.skills_played += 1
                if self.relic("letter_opener") and self.skills_played % 3 == 0:
                    self.atk_all(5)
                    self.log("Letter Opener: 5 damage to ALL.", "gold")
        finally:
            if x_cost:
                self.energy = 0
            self.dmg_mult = 1
            if cd["type"] == "power":
                self.powers.append(c)
            elif cd["exhaust"]:
                self.exhausted.append(c)
            else:
                self.discard.append(c)
            self.C = None
            self.target = None
        if self.player.alive and not self.alive_enemies():
            self.phase = "won"
        if DEBUG:
            self.validate()
        return True


# ----------------------------------------------------------------------- map

NODE_TYPES = {
    "monster": dict(label="M", name="Monster", color="red"),
    "elite": dict(label="E", name="Elite", color="orange"),
    "event": dict(label="?", name="Event", color="purple"),
    "rest": dict(label="R", name="Rest", color="green"),
    "shop": dict(label="$", name="Shop", color="gold"),
    "treasure": dict(label="T", name="Treasure", color="cyan"),
    "boss": dict(label="B", name="Boss", color="red"),
}


def gen_map(rng, floors=FLOORS):
    rows = []

    def pick_lanes(prev, k):
        for _ in range(80):
            lanes = sorted(rng.sample([0, 1, 2, 3], k))
            if all(any(abs(l - p) <= 1 for p in prev) for l in lanes) and \
               all(any(abs(l - p) <= 1 for l in lanes) for p in prev):
                return lanes
        return list(prev)

    prev = [1, 2]
    for r in range(floors):
        if r == 0:
            lanes = [1, 2]
        else:
            k = rng.choice([2, 2, 3, 3, 4])
            lanes = pick_lanes(prev, min(k, 4))
        rows.append(dict(lanes=lanes, types={}))
        prev = lanes

    edges = {}
    for r in range(floors - 1):
        for p in rows[r]["lanes"]:
            kids = [c for c in rows[r + 1]["lanes"] if abs(c - p) <= 1]
            if not kids:
                c = min(rows[r + 1]["lanes"], key=lambda x: abs(x - p))
                kids = [c]
            edges[(r, p)] = kids
    for c in rows[-1]["lanes"]:
        parents = [p for p in rows[-2]["lanes"] if abs(c - p) <= 1]
        if not parents:
            p = min(rows[-2]["lanes"], key=lambda x: abs(x - c))
            edges[(floors - 2, p)] = sorted(set(edges[(floors - 2, p)] + [c]))

    # node types
    all_types = []
    for r, row in enumerate(rows):
        for lane in row["lanes"]:
            if r == 0:
                t = "monster"
            elif r == floors - 1:
                t = rng.choice(["rest", "shop"])
            elif r == floors - 2:
                t = rng.choice(["rest", "rest", "shop", "elite"])
            elif floors <= 5:
                t = rng.choices(
                    ["monster", "event", "elite", "rest", "shop", "treasure"],
                    weights=[65, 15, 18, 0, 0, 2])[0]
            else:
                t = rng.choices(
                    ["monster", "event", "elite", "rest", "shop", "treasure"],
                    weights=[48, 22, 12, 9, 6, 3])[0]
            row["types"][lane] = t
            all_types.append((r, lane, t))

    def force(missing, kinds, count):
        for _ in range(60):
            if sum(1 for (_, _, t) in all_types if t in kinds) >= count:
                return
            r, lane, t = rng.choice([x for x in all_types
                                     if x[0] not in (0, floors - 1)
                                     and x[2] in ("monster", "event", "treasure")] or all_types[1:-1])
            rows[r]["types"][lane] = kinds[0]
            all_types.remove((r, lane, t))
            all_types.append((r, lane, kinds[0]))

    force("rest", ("rest",), max(1, floors // 3))
    force("shop", ("shop",), 1 if floors >= 5 else 0)
    force("elite", ("elite",), 1 if floors >= 4 else 0)

    boss_x = 1.5
    return dict(rows=rows, edges=edges, boss_lane=1.5,
                boss_type="boss", rng_seed=None)


# ----------------------------------------------------------------------- run

class Run:
    def __init__(self, seed=None, cls="warden"):
        self.rng = random.Random(seed)
        self.max_hp = 80
        self.hp = 80
        self.gold = 99
        self.cls = cls if cls in CLASSES else "warden"
        self.deck = [inst(c) for c in STARTER_DECKS[self.cls]]
        self.relics = ["burning_blood"]
        self.floor = 0
        self.total_floor = 0
        self.floors = ACT_FLOORS[0]
        self.map = gen_map(self.rng, self.floors)
        self.node = None
        self.avail = list(self.map["rows"][0]["lanes"])
        self.removals = 0
        self.stats = dict(kills=0, battles=0, cards_gained=0)
        self.reward = None
        self.shop = None
        self.act = 0
        self.potions = []
        self.ascension = 0
        self.daily = False
        self.seed = seed

    # -- deck --------------------------------------------------------------
    def add_card(self, cid, up=0):
        self.deck.append(inst(cid, up))
        self.stats["cards_gained"] += 1

    def remove_card(self, idx):
        if 0 <= idx < len(self.deck):
            c = self.deck.pop(idx)
            return c
        return None

    def upgrade_card(self, idx):
        if 0 <= idx < len(self.deck):
            c = self.deck[idx]
            n = c.get("up", 0)
            if n >= 2:
                return False
            c["up"] = n + 1
            return True
        return False

    def add_relic(self, rid):
        if rid not in self.relics:
            self.relics.append(rid)
            if rid == "bloodstone":
                self.max_hp += 10
                self.hp = min(self.max_hp, self.hp + 10)
            if rid == "strawberry":
                self.max_hp += 7
                self.hp = min(self.max_hp, self.hp + 7)
            if rid == "throne":
                self.max_hp = max(1, self.max_hp - 6)
                self.hp = min(self.hp, self.max_hp)
            if rid == "crown_flame":
                self.max_hp = max(1, self.max_hp - 8)
                self.hp = min(self.hp, self.max_hp)
            if rid == "heartstone":
                self.max_hp += 6
                self.hp = min(self.max_hp, self.hp + 6)
            return True
        return False

    # -- map ---------------------------------------------------------------
    def choose(self, lane):
        r = self.floor
        self.node = (r, lane)
        t = self.map["rows"][r]["types"][lane]
        if r < self.floors - 1:
            self.avail = self.map["edges"][(r, lane)]
        else:
            self.avail = ["boss"]
        return t

    def advance(self):
        self.floor += 1
        self.total_floor += 1
        if self.floor >= self.floors:
            return "boss"
        return None

    def next_act(self):
        self.act = min(self.act + 1, ACTS - 1)
        self.floor = 0
        self.floors = ACT_FLOORS[self.act]
        self.map = gen_map(self.rng, self.floors)
        self.node = None
        self.avail = list(self.map["rows"][0]["lanes"])
        self.reward = None
        self.shop = None

    def encounter_for(self, kind):
        act = min(self.act, ACTS - 1)
        if kind == "boss":
            return BOSSES[act]
        if kind == "elite":
            return self.rng.choice(ELITES[act])
        return self.rng.choice(ENCOUNTERS[act])

    # -- rewards -----------------------------------------------------------
    def roll_cards(self, n=3):
        owned = {c["id"] for c in self.deck}
        class_pool = BPOOL.get(self.cls, [])
        picks = [c for c in class_pool if c not in owned] or class_pool
        return self.rng.sample(picks, min(n, len(picks)))

    def make_reward(self, kind):
        gold = self.rng.randint(10, 18) + self.floor * 2 + self.act * 6
        if kind == "elite":
            gold += 25
        if kind == "boss":
            gold += 60
        gold = max(5, int(gold * (1.0 - 0.07 * self.ascension)))
        relic = None
        if kind in ("elite", "boss"):
            relic = self.random_relic()
        if kind == "boss" and relic is None:
            gold += 50
        return dict(gold=gold, cards=self.roll_cards(3), relic=relic, kind=kind)

    def random_relic(self, boss=False):
        owned = set(self.relics)
        pool = [r for r, d in RELICS.items()
                if r not in owned and bool(d.get("boss")) == boss]
        if not pool:
            return None
        return self.rng.choice(pool)

    def roll_boss_relics(self, n=3):
        owned = set(self.relics)
        pool = [r for r, d in RELICS.items() if d.get("boss") and r not in owned]
        self.rng.shuffle(pool)
        out = pool[:n]
        if len(out) < n:
            extra = [r for r, d in RELICS.items()
                     if not d.get("boss") and r not in owned]
            self.rng.shuffle(extra)
            out += extra[:n - len(out)]
        return out

    def grant_reward(self, reward):
        self.gold += reward["gold"]
        if reward.get("relic") and self.add_relic(reward["relic"]):
            pass

    def post_combat(self):
        if "burning_blood" in self.relics:
            self.hp = min(self.max_hp, self.hp + 6)
        if "meat" in self.relics and self.hp < self.max_hp * 0.5:
            self.hp = min(self.max_hp, self.hp + 12)
        if "ember_heart" in self.relics:
            self.hp = min(self.max_hp, self.hp + 8)
        if "bloodstone" in self.relics:
            self.hp = min(self.max_hp, self.hp + 4)
        if "heartstone" in self.relics:
            self.hp = min(self.max_hp, self.hp + 3)

    def add_potion(self, pid=None):
        if len(self.potions) >= 3:
            return None
        pid = pid or self.rng.choice(list(POTIONS))
        self.potions.append(pid)
        return pid

    # -- shop --------------------------------------------------------------
    def open_shop(self):
        scale = 1.0 + 0.10 * self.act
        cards = []
        for cid in self.roll_cards(4):
            d = BOARD_CARDS[cid]
            base = 26 + d["cost"] * 15
            cards.append(dict(cid=cid,
                              price=int(base * scale * self.rng.uniform(0.9, 1.1))))
        relic = self.random_relic()
        rprice = int((145 + self.rng.randint(0, 45)) * scale)
        removal = int((70 + 30 * self.removals) * scale)
        potions = []
        for _ in range(2):
            pid = self.rng.choice(list(POTIONS))
            potions.append(dict(pid=pid,
                                price=50 + self.rng.randint(0, 20) + 6 * self.act))
        self.shop = dict(cards=cards, relic=relic, relic_price=rprice,
                         removal=removal, potions=potions, sold=set())
        return self.shop

    def buy_card(self, i):
        s = self.shop
        item = s["cards"][i]
        if i in s["sold"] or self.gold < item["price"]:
            return False
        self.gold -= item["price"]
        s["sold"].add(i)
        self.add_card(item["cid"])
        return True

    def buy_relic(self):
        s = self.shop
        if s["relic"] is None or "relic" in s["sold"] or self.gold < s["relic_price"]:
            return False
        self.gold -= s["relic_price"]
        s["sold"].add("relic")
        self.add_relic(s["relic"])
        return True

    def pay_removal(self):
        s = self.shop
        if "removal" in s["sold"] or self.gold < s["removal"]:
            return False
        self.gold -= s["removal"]
        s["sold"].add("removal")
        self.removals += 1
        return True

    # -- events ------------------------------------------------------------
    def roll_event(self):
        return self.rng.choice(EVENTS)

    def resolve_choice(self, ch, picked=None):
        msgs = []
        if ch.get("hp"):
            self.hp = max(0, min(self.max_hp, self.hp + ch["hp"]))
            msgs.append(f"You {'lose' if ch['hp'] < 0 else 'gain'} {abs(ch['hp'])} HP.")
        if ch.get("heal"):
            self.hp = min(self.max_hp, self.hp + ch["heal"])
            msgs.append(f"You heal {ch['heal']} HP.")
        if ch.get("heal_pct"):
            n = int(self.max_hp * ch["heal_pct"])
            self.hp = min(self.max_hp, self.hp + n)
            msgs.append(f"You heal {n} HP.")
        if ch.get("full_heal"):
            self.hp = self.max_hp
            msgs.append("Your wounds close completely.")
        if ch.get("maxhp"):
            delta = ch["maxhp"]
            self.max_hp = max(1, self.max_hp + delta)
            self.hp = min(self.max_hp, max(1, self.hp + max(0, delta)))
            msgs.append(f"Max HP {'increased' if delta > 0 else 'reduced'} by {abs(delta)}.")
        if ch.get("gold"):
            self.gold = max(0, self.gold + ch["gold"])
            if ch["gold"] > 0:
                msgs.append(f"You gain {ch['gold']} gold.")
            else:
                msgs.append(f"You lose {abs(ch['gold'])} gold.")
        if ch.get("gamble"):
            w = ch["gamble"]
            self.gold -= w
            if self.rng.random() < 0.5:
                self.gold += w * 2
                msgs.append(f"Fortune smiles. You win {w * 2} gold.")
            else:
                msgs.append(f"Fortune laughs. You lose {w} gold.")
        if ch.get("relic"):
            rid = self.random_relic()
            if rid:
                self.add_relic(rid)
                msgs.append(f"You found {RELICS[rid]['name']}.")
            else:
                self.gold += 50
                msgs.append("You find only gold (50).")
        if ch.get("random_card"):
            pool = BPOOL.get(self.cls) or []
            cid = self.rng.choice(pool) if pool else None
            if cid:
                self.add_card(cid)
                msgs.append(f"You gained {BOARD_CARDS[cid]['name']}.")
        if ch.get("pick") == "upgrade" and picked is not None:
            cid = self.deck[picked]["id"]
            if self.upgrade_card(picked):
                msgs.append(f"{BOARD_CARDS[cid]['name']} was upgraded (+1/+1).")
        if ch.get("pick") == "duplicate" and picked is not None:
            c = self.deck[picked]
            self.deck.append(dict(c))
            msgs.append(f"{BOARD_CARDS[c['id']]['name']} was duplicated.")
        if ch.get("pick") == "remove" and picked is not None:
            c = self.remove_card(picked)
            if c:
                msgs.append(f"{BOARD_CARDS[c['id']]['name']} was removed from your deck.")
        if not msgs:
            msgs.append("Nothing happens.")
        return " ".join(msgs)

    # -- score -------------------------------------------------------------
    def score(self, won):
        return (self.gold + 25 * self.total_floor + 10 * self.stats["kills"]
                + 2 * self.hp + 150 * self.act + (400 if won else 0))


# ---------------------------------------------------------------- save/load

def _ensure_dir():
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
    except OSError:
        pass


def _read_json(path):
    with open(path) as f:
        return json.load(f)


def _atomic_write(path, payload):
    """Write JSON atomically: temp file + replace, with a .bak of the old file."""
    _ensure_dir()
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(payload, f)
        f.flush()
        try:
            os.fsync(f.fileno())
        except OSError:
            pass
    if os.path.exists(path):
        try:
            with open(path) as src, open(path + ".bak", "w") as dst:
                dst.write(src.read())
        except OSError:
            pass
    os.replace(tmp, path)


def _load_valid(path, legacy, current, migrations, valid):
    """Try primary, then .bak, then a legacy path; validate every candidate."""
    for p in (path, path + ".bak"):
        try:
            return valid(_migrate(_read_json(p), current, migrations))
        except Exception:
            continue
    if legacy:
        try:
            data = valid(_migrate(_read_json(legacy), current, migrations))
            _atomic_write(path, data)
            return data
        except Exception:
            pass
    return None


def _migrate(data, current, migrations, key="version"):
    v = int(data.get(key, 1))
    if v > current:
        raise ValueError(f"save version {v} is newer than {current}")
    while v < current:
        fn = migrations.get(v)
        if fn is not None:
            data = fn(data)
        v += 1
        data[key] = v
    return data


def default_meta():
    return {"best": 0, "wins": 0, "runs": 0, "asc": 1, "settings": {},
            "history": [], "seen": {"cards": [], "relics": [], "potions": [],
                                    "enemies": []},
            "achievements": [], "tips": [], "class_wins": {},
            "lifetime": {"kills": 0, "damage": 0, "potions": 0, "combats": 0},
            "daily": {"date": "", "score": 0, "won": False}}


def _meta_v1_to_v2(d):
    d.setdefault("settings", {})
    d.setdefault("history", [])
    return d


def _meta_v3_to_v4(d):
    d.setdefault("class_wins", {})
    return d


def _meta_v2_to_v3(d):
    base = default_meta()
    for k, v in base.items():
        d.setdefault(k, v)
    for k in ("cards", "relics", "potions", "enemies"):
        d["seen"].setdefault(k, [])
    for k in ("kills", "damage", "potions", "combats"):
        d["lifetime"].setdefault(k, 0)
    return d


META_MIGRATIONS = {1: _meta_v1_to_v2, 2: _meta_v2_to_v3, 3: _meta_v3_to_v4}


def _valid_meta(d):
    if not isinstance(d, dict):
        raise ValueError("meta is not an object")
    base = default_meta()
    for k, v in base.items():
        d.setdefault(k, v)
    for k in ("best", "wins", "runs", "asc"):
        try:
            d[k] = int(d.get(k, 0) or 0)
        except (TypeError, ValueError):
            d[k] = 0
    d["best"] = max(0, d["best"])
    d["wins"] = max(0, d["wins"])
    d["runs"] = max(0, d["runs"])
    d["asc"] = max(1, min(9, d["asc"]))
    if not isinstance(d.get("settings"), dict):
        d["settings"] = {}
    if not isinstance(d.get("history"), list):
        d["history"] = []
    d["history"] = [h for h in d["history"] if isinstance(h, dict)][:5]
    seen = d.get("seen")
    if not isinstance(seen, dict):
        seen = {}
    valid = {"cards": set(BOARD_CARDS), "relics": set(RELICS),
             "potions": set(POTIONS), "enemies": set(ENEMIES)}
    clean = {}
    for kind, pool in valid.items():
        vals = seen.get(kind)
        clean[kind] = [x for x in vals if x in pool] if isinstance(vals, list) else []
    d["seen"] = clean
    ach = d.get("achievements")
    d["achievements"] = [a for a in ach if a in ACHIEVEMENTS] \
        if isinstance(ach, list) else []
    tips = d.get("tips")
    d["tips"] = [t for t in tips if isinstance(t, str)] if isinstance(tips, list) else []
    life = d.get("lifetime")
    if not isinstance(life, dict):
        life = {}
    for k in ("kills", "damage", "potions", "combats"):
        try:
            life[k] = max(0, int(life.get(k, 0) or 0))
        except (TypeError, ValueError):
            life[k] = 0
    d["lifetime"] = life
    cw = d.get("class_wins")
    if not isinstance(cw, dict):
        cw = {}
    d["class_wins"] = {k: max(0, int(cw.get(k, 0) or 0))
                       for k in CLASSES if k in cw}
    daily = d.get("daily")
    if not isinstance(daily, dict):
        daily = {}
    d["daily"] = {"date": str(daily.get("date", "")),
                  "score": int(daily.get("score", 0) or 0),
                  "won": bool(daily.get("won", False))}
    return d


def load_best():
    data = _load_valid(SAVE_PATH, LEGACY_SAVE, SAVE_VERSION,
                       META_MIGRATIONS, _valid_meta)
    if data is None:
        return default_meta()
    return data


def save_best(data):
    try:
        payload = dict(data)
        payload["version"] = SAVE_VERSION
        _atomic_write(SAVE_PATH, _valid_meta(payload))
    except Exception:
        pass


def _run_v1_to_v2(d):
    d.setdefault("potions", [])
    d.setdefault("path", [])
    d.setdefault("ascension", 0)
    return d


RUN_MIGRATIONS = {1: _run_v1_to_v2}


def _valid_run(d):
    """Return a cleaned run dict or raise. Unknown content is dropped, not fatal."""
    if not isinstance(d, dict):
        raise ValueError("run is not an object")
    for k in ("hp", "max_hp", "gold", "deck", "relics", "act", "floor",
              "total_floor", "map", "avail"):
        if k not in d:
            raise ValueError(f"missing {k}")
    if not isinstance(d["map"], dict) or "rows" not in d["map"]:
        raise ValueError("bad map")
    d["cls"] = d.get("cls") if d.get("cls") in CLASSES else "warden"
    d["max_hp"] = max(1, min(500, int(d["max_hp"])))
    d["hp"] = max(0, min(d["max_hp"], int(d["hp"])))
    d["gold"] = max(0, min(99999, int(d["gold"])))
    d["act"] = max(0, min(ACTS - 1, int(d["act"])))
    max_floor = ACT_FLOORS[d["act"]]
    d["floor"] = max(0, min(max_floor, int(d["floor"])))
    d["total_floor"] = max(0, min(TOTAL_FLOORS, int(d["total_floor"])))
    deck = []
    for c in d["deck"]:
        if isinstance(c, dict) and c.get("id") in BOARD_CARDS:
            up = max(0, min(2, int(c.get("up", 0) or 0)))
            deck.append({"id": c["id"], "up": up})
    if not deck:
        deck = [{"id": "w_ashguard", "up": 0}]
    d["deck"] = deck
    d["relics"] = [r for r in d["relics"] if r in RELICS]
    d["potions"] = [p for p in d.get("potions", []) if p in POTIONS][:3]
    d["daily"] = bool(d.get("daily", False))
    rows = []
    for row in d["map"]["rows"]:
        lanes = [int(l) for l in row["lanes"]]
        types = {int(k): v for k, v in row["types"].items()
                 if int(k) in lanes and isinstance(v, str)}
        rows.append(dict(lanes=lanes, types=types))
    edges = {}
    for k, v in d["map"]["edges"].items():
        r, p = (int(x) for x in str(k).split(","))
        edges[f"{r},{p}"] = [int(c) for c in v]
    if not rows:
        raise ValueError("empty map")
    d["map"] = dict(rows=rows, edges=edges)
    if not isinstance(d["avail"], list) or not d["avail"]:
        d["avail"] = list(rows[min(d["floor"], len(rows) - 1)]["lanes"])
    d["avail"] = [int(x) for x in d["avail"]]
    if d.get("node") is not None:
        d["node"] = [int(x) for x in d["node"]]
    return d


def save_run(data):
    try:
        payload = dict(data)
        payload["version"] = RUN_VERSION
        _atomic_write(RUN_PATH, payload)
    except Exception:
        pass


def load_run():
    data = _load_valid(RUN_PATH, LEGACY_RUN, RUN_VERSION,
                       RUN_MIGRATIONS, _valid_run)
    if data is None:
        if os.path.exists(RUN_PATH):
            clear_run()
        return None
    return data


def clear_run():
    for p in (RUN_PATH, RUN_PATH + ".tmp", RUN_PATH + ".bak"):
        try:
            os.remove(p)
        except Exception:
            pass


def run_to_dict(run, path):
    return dict(
        cls=run.cls, hp=run.hp, max_hp=run.max_hp, gold=run.gold, deck=run.deck,
        relics=run.relics, potions=run.potions, act=run.act, floor=run.floor,
        total_floor=run.total_floor, removals=run.removals, stats=run.stats,
        ascension=run.ascension, seed=run.seed, daily=run.daily,
        node=list(run.node) if run.node else None, avail=run.avail,
        path=[list(p) for p in path],
        map=dict(
            rows=[dict(lanes=r["lanes"],
                       types={str(k): v for k, v in r["types"].items()})
                  for r in run.map["rows"]],
            edges={f"{r},{p}": v for (r, p), v in run.map["edges"].items()},
        ))


def run_from_dict(d):
    run = Run(d.get("seed") or 1, d.get("cls", "warden"))
    run.cls = d.get("cls", "warden")
    run.hp = d["hp"]
    run.max_hp = d["max_hp"]
    run.gold = d["gold"]
    run.deck = [dict(c) for c in d["deck"]]
    run.relics = list(d["relics"])
    run.potions = list(d.get("potions", []))
    run.act = d["act"]
    run.floor = d["floor"]
    run.total_floor = d["total_floor"]
    run.removals = d.get("removals", 0)
    run.stats.update(d.get("stats", {}))
    run.ascension = d.get("ascension", 0)
    run.daily = bool(d.get("daily", False))
    run.map = dict(
        rows=[dict(lanes=r["lanes"],
                   types={int(k): v for k, v in r["types"].items()})
              for r in d["map"]["rows"]],
        edges={tuple(int(x) for x in k.split(",")): v
               for k, v in d["map"]["edges"].items()},
    )
    run.node = tuple(d["node"]) if d.get("node") else None
    run.avail = list(d["avail"])
    run.reward = None
    run.shop = None
    return run
