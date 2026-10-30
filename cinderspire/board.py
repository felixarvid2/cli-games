"""Hearthstone-like board combat for CINDERSPIRE.

Heroes, mana, a five-slot board per side, minions with Attack/Health and
Taunt / Charge / Divine Shield / Poisonous / Battlecry / Deathrattle.
"""

import random

from .board_data import BOARD_CARDS, ENEMY_HEROES

MAX_BOARD = 5
MAX_HAND = 8
MAX_MANA = 8


class Hero:
    def __init__(self, name, hp, max_hp=None):
        self.name = name
        self.hp = hp
        self.max_hp = max_hp or hp
        self.mana = 0
        self.max_mana = 0
        self.armor = 0


class Minion:
    def __init__(self, cid, owner, up=0, atk_bonus=0, hp_bonus=0):
        d = BOARD_CARDS[cid]
        self.cid = cid
        self.name = d["name"]
        self.owner = owner
        self.base_atk = d["atk"] + up
        self.atk = self.base_atk + atk_bonus
        self.max_hp = d["hp"] + up + hp_bonus
        self.hp = self.max_hp
        self.kw = set(d["kw"])
        self.bc = d.get("bc")
        self.dr = d.get("dr")
        self.combo = d.get("combo")
        self.divine = "divine_shield" in self.kw
        self.taunt = "taunt" in self.kw
        self.poisonous = "poisonous" in self.kw
        self.ready = "charge" in self.kw
        self.alive = True
        self.attacks = 0
        self.summoned = 0

    @property
    def max_attacks(self):
        return 2 if "windfury" in self.kw else 1

    def label(self):
        kws = []
        if self.taunt:
            kws.append("TAUNT")
        if self.divine:
            kws.append("DS")
        if self.poisonous:
            kws.append("POISON")
        if "charge" in self.kw:
            kws.append("CHARGE")
        if "rush" in self.kw:
            kws.append("RUSH")
        if "windfury" in self.kw:
            kws.append("WIND")
        return kws


class BoardCombat:
    def __init__(self, run, hero_def, kind="normal", rng=None):
        self.run = run
        self.rng = rng or random.Random()
        self.kind = kind
        self.hero_def = hero_def
        self.player = Hero("You", run.hp, run.max_hp)
        self.enemy = Hero(hero_def["name"], hero_def["hp"], hero_def["hp"])
        self.pboard = []
        self.eboard = []
        self.deck = [dict(c) for c in run.deck]
        self.rng.shuffle(self.deck)
        self.edeck = [{"id": c} for c in hero_def["deck"]]
        self.rng.shuffle(self.edeck)
        self.ehand = []
        self.hand = []
        self.discard = []
        self.energy = 0
        self.turn = 0
        self.phase = "player"
        self.logs = []
        self.popups = {}
        self.shake = {}
        self.flash = {}
        self.anim_next = 0.0
        self.eactions = 0
        self.best_hit = 0
        self.damage_dealt = 0
        self.kills = 0
        self.attacks_played = 0
        self.spells_played = 0
        self.relics = set(run.relics)
        self.turn_ended_with_board = False
        self.flags = dict(
            atk_aura=(2 if "molten_core" in self.relics else
                      1 if ("vajra" in self.relics or "twin_fangs" in self.relics
                            or "whetstone" in self.relics) else 0),
            hp_aura=1 if "smooth_stone" in self.relics else 0,
            extra_draw=1 if "hourglass" in self.relics else 0,
            thorns=1 if "bronze_scales" in self.relics else 0,
            mana_bonus=1 if ("throne" in self.relics
                             or "crown_flame" in self.relics) else 0,
            pen=0,
            spells=0,
            killed=0,
            banner=False,
            venom_aura=False,
        )
        self.played_this_turn = 0
        self.start()

    # -- helpers -----------------------------------------------------------
    def log(self, msg, color="text"):
        self.logs.append((msg, color))
        if len(self.logs) > 80:
            self.logs.pop(0)

    def popup(self, target, text, color="red"):
        self.popups[id(target)] = [text, color, 0.8]

    def enemy_alive(self):
        return [m for m in self.eboard if m.alive]

    def player_alive(self):
        return [m for m in self.pboard if m.alive]

    def draw(self, n, side="player"):
        for _ in range(n):
            if side == "player":
                if len(self.hand) >= MAX_HAND:
                    return
                if not self.deck:
                    if not self.discard:
                        return
                    self.deck = self.discard
                    self.discard = []
                    self.rng.shuffle(self.deck)
                self.hand.append(self.deck.pop())
            else:
                if len(self.ehand) >= MAX_HAND:
                    return
                if not self.edeck:
                    return
                self.ehand.append(self.edeck.pop())

    def summon(self, side, cid, n=1, up=0):
        board = self.pboard if side == "player" else self.eboard
        for _ in range(n):
            if len([m for m in board if m.alive]) >= MAX_BOARD:
                self.log("The board is full.", "dim")
                return
            m = Minion(cid, side, up,
                       atk_bonus=self.flags["atk_aura"] if side == "player" else 0,
                       hp_bonus=self.flags["hp_aura"] if side == "player" else 0)
            m.summoned = self.turn
            if "charge" in m.kw or "rush" in m.kw:
                m.ready = True
            if side == "player":
                if self.flags.get("banner"):
                    m.atk += 1
                if self.flags.get("venom_aura"):
                    m.poisonous = True
                    m.kw.add("poisonous")
            board.append(m)
            self.flash[id(m)] = 0.25
            self.log(f"{side.title()} summons {m.name}.", "green")
            if m.bc:
                self.run_ops(side, m, m.bc)
            return m
        return None

    # -- ops ---------------------------------------------------------------
    def run_ops(self, side, src, ops, target=None):
        enemy = "enemy" if side == "player" else "player"
        eboard = self.eboard if enemy == "enemy" else self.pboard
        ehero = self.enemy if enemy == "enemy" else self.player
        for item in ops:
            op = item[0]
            a = item[1:]
            if op == "dmg_hero":
                self.hurt_hero(enemy, a[0], src)
            elif op == "dmg_random":
                alive = [m for m in eboard if m.alive]
                if alive:
                    self.hurt_minion(self.rng.choice(alive), a[0], src)
                else:
                    self.hurt_hero(enemy, a[0], src)
            elif op == "aoe":
                for m in list(eboard):
                    if m.alive:
                        self.hurt_minion(m, a[0], src)
            elif op == "heal":
                hero = self.player if side == "player" else self.enemy
                before = hero.hp
                hero.hp = min(hero.max_hp, hero.hp + a[0])
                if hero.hp > before:
                    self.popup(hero, f"+{hero.hp - before}", "green")
                self.log(f"{hero.name} heals {a[0]}.", "green")
            elif op == "heal_all":
                board = self.pboard if side == "player" else self.eboard
                for m in board:
                    if m.alive:
                        before = m.hp
                        m.hp = min(m.max_hp, m.hp + a[0])
                        if m.hp > before:
                            self.popup(m, f"+{m.hp - before}", "green")
                self.log(f"Friendly minions heal {a[0]}.", "green")
                for m in board:
                    if m.alive and m.cid == "p_lightwarden":
                        m.atk += 2
                        self.log("Lightwarden grows stronger.", "gold")
            elif op == "draw":
                self.draw(a[0], side)
                self.log(f"{side.title()} draws {a[0]}.", "dim")
            elif op == "summon":
                self.summon(side, a[0], a[1] if len(a) > 1 else 1)
            elif op == "mana":
                hero = self.player if side == "player" else self.enemy
                hero.mana += a[0]
            elif op == "buff_self":
                src.atk += a[0]
                src.max_hp += a[1]
                src.hp += a[1]
            elif op == "buff_board":
                board = self.pboard if side == "player" else self.eboard
                for m in board:
                    if m.alive:
                        m.atk += a[0]
                        m.max_hp += a[1]
                        m.hp += a[1]
                self.log("Friendly minions are buffed.", "gold")
            elif op == "dmg_target" and target is not None:
                side_t = target[0]
                idx = target[1] if len(target) > 1 else 0
                if side_t == "hero":
                    self.hurt_hero("enemy", a[0], src)
                elif side_t == "e" and 0 <= idx < len(self.eboard) \
                        and self.eboard[idx].alive:
                    self.hurt_minion(self.eboard[idx], a[0], src)
                elif side_t == "p" and 0 <= idx < len(self.pboard) \
                        and self.pboard[idx].alive:
                    self.hurt_minion(self.pboard[idx], a[0], src)
            elif op == "destroy_target" and target is not None:
                side_t = target[0]
                idx = target[1] if len(target) > 1 else 0
                if side_t == "e" and 0 <= idx < len(self.eboard) \
                        and self.eboard[idx].alive:
                    self.kill(self.eboard[idx])
            elif op == "buff_target":
                board = self.pboard if side == "player" else self.eboard
                alive = [m for m in board if m.alive]
                if alive:
                    m = max(alive, key=lambda x: x.atk)
                    m.atk += a[0]
                    m.max_hp += a[1]
                    m.hp += a[1]
            elif op == "banner":
                self.flags["banner"] = True
            elif op == "venom_aura":
                self.flags["venom_aura"] = True
                board = self.pboard if side == "player" else self.eboard
                for m in board:
                    if m.alive:
                        m.poisonous = True
                        m.kw.add("poisonous")
            elif op == "taunt_board":
                board = self.pboard if side == "player" else self.eboard
                for m in board:
                    if m.alive:
                        m.taunt = True
            elif op == "buff_recruits":
                board = self.pboard if side == "player" else self.eboard
                for m in board:
                    if m.alive and m.cid == "recruit":
                        m.atk += a[0]
                        m.max_hp += a[1]
                        m.hp += a[1]
            elif op == "set_atk_hp":
                board = self.pboard if side == "player" else self.eboard
                alive = [m for m in board if m.alive]
                if alive:
                    m = max(alive, key=lambda x: x.hp)
                    m.atk = max(1, m.hp)
            elif op == "random_split":
                for _ in range(a[0]):
                    alive = self.enemy_alive() if side == "player" else self.player_alive()
                    if alive:
                        self.hurt_minion(self.rng.choice(alive), 1, src)
                    else:
                        self.hurt_hero("enemy" if side == "player" else "player",
                                       1, src)
            elif op == "give_kw":
                board = self.pboard if side == "player" else self.eboard
                alive = [m for m in board if m.alive]
                if alive:
                    m = max(alive, key=lambda x: x.atk)
                    if a[0] == "divine_shield":
                        m.divine = True
                        m.kw.add("divine_shield")
            self.check_over()

    # -- damage ------------------------------------------------------------
    def hurt_minion(self, m, n, src=None):
        if not m.alive or n <= 0:
            return
        if m.divine:
            m.divine = False
            m.kw.discard("divine_shield")
            self.popup(m, "SHIELD", "gold")
            self.log(f"{m.name}'s Divine Shield absorbs the hit.", "gold")
            return
        m.hp -= n
        self.shake[id(m)] = 0.32
        self.flash[id(m)] = 0.16
        if m.owner == "enemy":
            self.damage_dealt += n
        if src is not None and "lifesteal" in getattr(src, "kw", ()):
            hero = self.player if getattr(src, "owner", "") == "player" else self.enemy
            before = hero.hp
            hero.hp = min(hero.max_hp, hero.hp + n)
            if hero.hp > before:
                self.popup(hero, f"+{hero.hp - before}", "green")
        self.popup(m, f"-{n}", "red")
        if src is not None and getattr(src, "poisonous", False):
            m.hp = 0
        if m.hp <= 0:
            self.kill(m)

    def hurt_hero(self, side, n, src=None):
        hero = self.enemy if side == "enemy" else self.player
        if n <= 0:
            return
        hero.hp -= n
        self.shake[id(hero)] = 0.40
        self.flash[id(hero)] = 0.22
        if side == "enemy":
            self.damage_dealt += n
        if src is not None and "lifesteal" in getattr(src, "kw", ()):
            own = self.player if getattr(src, "owner", "") == "player" else self.enemy
            before = own.hp
            own.hp = min(own.max_hp, own.hp + n)
            if own.hp > before:
                self.popup(own, f"+{own.hp - before}", "green")
        self.popup(hero, f"-{n}", "red")
        self.log(f"{hero.name} takes {n} damage.", "red")
        if side == "player":
            self.run.hp = max(0, hero.hp)
        if src is not None:
            self.best_hit = max(self.best_hit, n)
        self.check_over()

    def kill(self, m):
        if not m.alive:
            return
        m.alive = False
        m.hp = 0
        self.kills += 1
        self.log(f"{m.name} dies.", "dim")
        if m.dr:
            self.run_ops(m.owner, m, m.dr)
        if m.owner == "enemy" and "gremlin_horn" in self.relics:
            hero = self.player
            hero.mana += 1
            self.log("Gremlin Horn: +1 Mana.", "gold")

    def compact(self):
        self.pboard = [m for m in self.pboard if m.alive]
        self.eboard = [m for m in self.eboard if m.alive]

    def check_over(self):
        if self.phase in ("won", "lost"):
            return
        if self.enemy.hp <= 0:
            self.phase = "won"
            self.log("The enemy hero falls.", "gold")
        elif self.player.hp <= 0:
            self.phase = "lost"
            self.run.hp = 0
            self.log("You fall.", "red")

    # -- turn flow ---------------------------------------------------------
    def start(self):
        self.turn = 1
        self.player.max_mana = 3
        self.player.mana = 3 + self.flags["mana_bonus"]
        if "lantern" in self.relics:
            self.player.mana += 1
        self.draw(5)
        if "bag_of_prep" in self.relics:
            self.draw(2)
        if "choir_bell" in self.relics:
            self.draw(1)
        if "blood_vial" in self.relics:
            self.player.hp = min(self.player.max_hp, self.player.hp + 2)
        if "anchor" in self.relics:
            self.summon("player", "guard_t")
        if "bastion" in self.relics:
            self.summon("player", "guard_t")
        if "ashen_wings" in self.relics:
            self.summon("player", "whelp")
        self.enemy.max_mana = 3
        self.enemy.mana = 3
        self.draw(5, "enemy")
        self.log("A battle begins.", "dim")
        self.log(f"-- Turn {self.turn} --", "dim")
        self.phase = "player"

    def start_player_turn(self):
        self.turn += 1
        self.played_this_turn = 0
        self.player.max_mana = min(MAX_MANA, 2 + self.turn)
        self.player.mana = self.player.max_mana + self.flags["mana_bonus"]
        if "sundial" in self.relics and self.turn % 3 == 0:
            self.player.mana += 1
        for m in self.pboard:
            if m.alive:
                m.ready = True
                m.attacks = 0
        self.draw(2 + self.flags["extra_draw"])
        if "orichalcum" in self.relics and not self.player_alive():
            self.summon("player", "recruit")
        self.phase = "player"
        self.log(f"-- Turn {self.turn} --", "dim")

    def end_turn(self):
        if self.phase != "player":
            return
        for m in self.pboard:
            if m.alive:
                m.ready = False
        self.enemy.max_mana = min(MAX_MANA, 2 + self.turn)
        self.enemy.mana = self.enemy.max_mana
        self.draw(1, "enemy")
        self.phase = "enemy"
        self.eactions = 0
        self.log("Your turn ends.", "dim")

    def step_enemy(self):
        """One enemy action: play a card, attack, or pass the turn."""
        if self.phase != "enemy":
            return True
        self.eactions += 1
        if self.eactions > 40:
            self.finish_enemy_turn()
            self.compact()
            return True
        # 1) play a card
        playable = []
        for i, c in enumerate(self.ehand):
            d = BOARD_CARDS[c["id"]]
            if d["cost"] <= self.enemy.mana:
                if d["kind"] == "spell" or len(self.enemy_alive()) < MAX_BOARD:
                    playable.append(i)
        if playable and self.ehand:
            i = max(playable, key=lambda k: BOARD_CARDS[self.ehand[k]["id"]]["cost"])
            self.enemy_play(i)
            return False
        # 2) attack
        ready = [m for m in self.eboard if m.alive and m.ready]
        if ready:
            m = ready[0]
            taunts = [x for x in self.pboard if x.alive and x.taunt]
            if taunts:
                self.enemy_attack(m, self.rng.choice(taunts))
            elif self.player_alive() and self.rng.random() < 0.18:
                self.enemy_attack(m, self.rng.choice(self.player_alive()))
            else:
                self.enemy_attack(m, None)
            self.compact()
            return False
        self.finish_enemy_turn()
        self.compact()
        return True

    def finish_enemy_turn(self):
        for m in self.eboard:
            if m.alive:
                m.ready = True
        if self.phase == "enemy":
            self.start_player_turn()

    def enemy_play(self, i):
        c = self.ehand.pop(i)
        d = BOARD_CARDS[c["id"]]
        self.enemy.mana -= d["cost"]
        if d["kind"] == "minion":
            self.summon("enemy", c["id"])
        else:
            self.run_ops("enemy", None, d["effects"])

    def enemy_attack(self, m, target):
        m.ready = False
        if target is None:
            self.hurt_hero("player", m.atk, m)
            if self.flags["thorns"] > 0:
                self.hurt_minion(m, self.flags["thorns"], None)
            return
        self.exchange(m, target)

    # -- player actions ----------------------------------------------------
    def can_play(self, i):
        if not (0 <= i < len(self.hand)):
            return False
        d = BOARD_CARDS[self.hand[i]["id"]]
        if d["cost"] > self.player.mana:
            return False
        if d["kind"] == "minion" and len(self.player_alive()) >= MAX_BOARD:
            return False
        return True

    def play_card(self, i, target=None):
        if self.phase != "player" or not self.can_play(i):
            return False
        c = self.hand.pop(i)
        d = BOARD_CARDS[c["id"]]
        combo = self.played_this_turn > 0
        self.player.mana -= d["cost"]
        if d["kind"] == "minion":
            up = c.get("up", 0)
            m = self.summon("player", c["id"], 1, up)
            if combo and d.get("combo") and m is not None:
                self.log(f"Combo! {d['name']}.", "gold")
                self.run_ops("player", m, d["combo"], target)
        else:
            self.spells_played += 1
            self.run_ops("player", None, d["effects"], target)
            if combo and d.get("combo"):
                self.log(f"Combo! {d['name']}.", "gold")
                self.run_ops("player", None, d["combo"], target)
            self.spell_triggers()
            if "letter_opener" in self.relics and self.spells_played % 3 == 0:
                self.hurt_hero("enemy", 2)
            self.discard.append(c)
        self.played_this_turn += 1
        self.check_over()
        self.compact()
        return True

    def spell_triggers(self):
        for m in self.player_alive():
            if m.cid == "e_pyromaniac":
                for e in list(self.eboard):
                    if e.alive:
                        self.hurt_minion(e, 1, m)
                self.log("Pyromaniac scorches the enemy board.", "gold")
            elif m.cid == "e_manawyrm":
                m.atk += 1
                self.log("Mana Wyrm grows stronger.", "gold")

    def use_potion(self, pid, target=None):
        if pid in ("fire", "poison", "steel"):
            pass
        if pid == "fire":
            self.run_ops("player", None, [("dmg_target", 6)], target or ("hero",))
        elif pid == "poison":
            self.run_ops("player", None, [("dmg_target", 4)], target or ("hero",))
        elif pid == "block":
            self.run_ops("player", None, [("heal", 8)])
        elif pid == "strength":
            self.run_ops("player", None, [("buff_board", 1, 1)])
        elif pid in ("swift", "memories"):
            self.run_ops("player", None, [("draw", 2)])
        elif pid == "energy":
            self.run_ops("player", None, [("mana", 2)])
        elif pid == "fear":
            self.run_ops("player", None, [("aoe", 2)])
        elif pid == "regen":
            self.run_ops("player", None, [("heal", 10)])
        elif pid == "steel":
            self.run_ops("player", None, [("give_kw", "divine_shield")])
        elif pid == "juice":
            self.player.max_hp += 5
            self.player.hp += 5
            self.run.max_hp += 5
        elif pid == "firestorm":
            self.run_ops("player", None, [("aoe", 3)])
        elif pid == "ember_blood":
            self.run_ops("player", None, [("heal", 20)])
        self.check_over()
        self.compact()
        return True

    def attack(self, i, target):
        """target: ("hero",) or ("e", idx)."""
        if self.phase != "player":
            return False
        alive = self.player_alive()
        if not (0 <= i < len(alive)):
            return False
        a = alive[i]
        if not a.ready:
            return False
        if target[0] == "hero":
            if "rush" in a.kw:
                self.log("Rush minions cannot attack heroes.", "dim")
                return False
            if any(m.alive and m.taunt for m in self.eboard):
                self.log("A Taunt minion blocks the way.", "dim")
                return False
            a.attacks += 1
            a.ready = a.attacks < a.max_attacks
            self.attacks_played += 1
            self.hurt_hero("enemy", self.attack_damage(a), a)
            self.compact()
            return True
        idx = target[1]
        if not (0 <= idx < len(self.eboard)) or not self.eboard[idx].alive:
            return False
        t = self.eboard[idx]
        if any(m.alive and m.taunt for m in self.eboard) and not t.taunt:
            self.log("You must attack a Taunt minion.", "dim")
            return False
        a.attacks += 1
        a.ready = a.attacks < a.max_attacks
        self.attacks_played += 1
        self.exchange(a, t)
        self.compact()
        return True

    def attack_damage(self, m):
        dmg = m.atk
        if "pen_nib" in self.relics:
            self.flags["pen"] += 1
            if self.flags["pen"] % 5 == 0:
                dmg *= 2
                self.log("Pen Nib: double damage!", "gold")
        return dmg

    def exchange(self, a, t):
        if t is None:
            self.hurt_hero("enemy", self.attack_damage(a), a)
            return
        dmg = self.attack_damage(a)
        back = t.atk
        self.hurt_minion(t, dmg, a)
        self.hurt_minion(a, back, t)
        self.log(f"{a.name} attacks {t.name}.", "dim")


def enemy_for(run, kind, rng):
    """Pick an enemy hero for the current act/kind."""
    if kind == "boss":
        pool = [e for e in ENEMY_HEROES if e.get("boss")]
        idx = min(run.act, len(pool) - 1)
        return pool[idx]
    if kind == "elite":
        pool = [e for e in ENEMY_HEROES if e.get("elite")]
        return rng.choice(pool)
    act = min(run.act, 2)
    pool = [e for e in ENEMY_HEROES if e.get("act") == act and not e.get("elite")]
    if not pool:
        pool = [e for e in ENEMY_HEROES if not e.get("boss")]
    return rng.choice(pool)
