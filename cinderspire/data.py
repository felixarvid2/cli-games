"""Static content for CINDERSPIRE: cards, enemies, relics, events."""

# ---------------------------------------------------------------- cards ----

CARDS = {}


def card(cid, name, ctype, cost, rarity, text, **kw):
    d = {
        "id": cid, "name": name, "type": ctype, "cost": cost, "rarity": rarity,
        "text": text, "dmg": 0, "block": 0, "magic": 0, "hits": 1,
        "hp_loss": 0, "exhaust": False, "target": "enemy", "up": {},
    }
    d.update(kw)
    return d


def _add(d):
    CARDS[d["id"]] = d


# --- basic -----------------------------------------------------------------
_add(card("strike", "Strike", "attack", 1, "basic",
          "Deal {d} damage.", dmg=6, up={"dmg": 3},
          play=lambda cb: cb.atk(cb.target, cb.C["dmg"])))
_add(card("defend", "Defend", "skill", 1, "basic",
          "Gain {b} Block.", block=5, target="none", up={"block": 3},
          play=lambda cb: cb.block(cb.C["block"])))
_add(card("bash", "Bash", "attack", 2, "basic",
          "Deal {d} damage.\nApply {m} Vulnerable.",
          dmg=8, magic=2, up={"dmg": 2, "magic": 1},
          play=lambda cb: (cb.atk(cb.target, cb.C["dmg"]),
                           cb.status(cb.target, "vuln", cb.C["magic"]))))

# --- common ----------------------------------------------------------------
_add(card("cleave", "Cleave", "attack", 1, "common",
          "Deal {d} damage to ALL enemies.", dmg=8, target="all",
          up={"dmg": 3},
          play=lambda cb: cb.atk_all(cb.C["dmg"])))
_add(card("twin_strike", "Twin Strike", "attack", 1, "common",
          "Deal {d} damage twice.", dmg=5, hits=2, up={"dmg": 2},
          play=lambda cb: cb.atk(cb.target, cb.C["dmg"], times=2)))
_add(card("quick_slash", "Quick Slash", "attack", 1, "common",
          "Deal {d} damage.\nDraw {m} card.", dmg=8, magic=1,
          up={"dmg": 3},
          play=lambda cb: (cb.atk(cb.target, cb.C["dmg"]),
                           cb.draw(cb.C["magic"]))))
_add(card("iron_wave", "Iron Wave", "attack", 1, "common",
          "Deal {d} damage.\nGain {b} Block.", dmg=5, block=5,
          up={"dmg": 2, "block": 2},
          play=lambda cb: (cb.atk(cb.target, cb.C["dmg"]),
                           cb.block(cb.C["block"]))))
_add(card("clothesline", "Clothesline", "attack", 2, "common",
          "Deal {d} damage.\nApply {m} Weak.", dmg=12, magic=2,
          up={"dmg": 2, "magic": 1},
          play=lambda cb: (cb.atk(cb.target, cb.C["dmg"]),
                           cb.status(cb.target, "weak", cb.C["magic"]))))
_add(card("anger", "Anger", "attack", 1, "common",
          "Deal {d} damage.\nAdd a copy of this\ncard to your discard.",
          dmg=6, up={"dmg": 2},
          play=lambda cb: (cb.atk(cb.target, cb.C["dmg"]),
                           cb.dup_to_discard())))
_add(card("body_slam", "Body Slam", "attack", 1, "common",
          "Deal damage equal to\nyour Block.", up={"cost": -1},
          play=lambda cb: cb.atk(cb.target, cb.player.block)))
_add(card("sword_boomerang", "Sword Boomerang", "attack", 1, "common",
          "Deal {d} damage to a\nrandom enemy {h} times.",
          dmg=3, hits=3, target="random", up={"dmg": 1},
          play=lambda cb: cb.atk_random(cb.C["dmg"], times=3)))
_add(card("thunderclap", "Thunderclap", "attack", 1, "common",
          "Deal {d} damage and\napply 1 Vulnerable to\nALL enemies.",
          dmg=4, target="all", up={"dmg": 3},
          play=lambda cb: (cb.atk_all(cb.C["dmg"]),
                           cb.status_all("vuln", 1))))
_add(card("poison_stab", "Poison Stab", "attack", 1, "common",
          "Deal {d} damage.\nApply {m} Poison.", dmg=5, magic=2,
          up={"magic": 2},
          play=lambda cb: (cb.atk(cb.target, cb.C["dmg"]),
                           cb.status(cb.target, "poison", cb.C["magic"]))))
_add(card("pommel_strike", "Pommel Strike", "attack", 1, "common",
          "Deal {d} damage.\nDraw {m} card.", dmg=9, magic=1,
          up={"dmg": 1, "magic": 1},
          play=lambda cb: (cb.atk(cb.target, cb.C["dmg"]),
                           cb.draw(cb.C["magic"]))))

# --- uncommon --------------------------------------------------------------
_add(card("shrug_it_off", "Shrug It Off", "skill", 1, "uncommon",
          "Gain {b} Block.\nDraw {m} card.", block=8, magic=1,
          target="none", up={"block": 3},
          play=lambda cb: (cb.block(cb.C["block"]),
                           cb.draw(cb.C["magic"]))))
_add(card("true_grit", "True Grit", "skill", 1, "uncommon",
          "Gain {b} Block.\nExhaust a random card.", block=7, magic=1,
          target="none", up={"block": 2},
          play=lambda cb: (cb.block(cb.C["block"]), cb.exhaust_random())))
_add(card("battle_trance", "Battle Trance", "skill", 1, "uncommon",
          "Draw {m} cards.", magic=3, target="none", up={"cost": -1},
          play=lambda cb: cb.draw(cb.C["magic"])))
_add(card("armaments", "Armaments", "skill", 1, "uncommon",
          "Gain {b} Block.\nUpgrade a random card\nin your hand.",
          block=5, magic=1, target="none", up={"magic": 1},
          play=lambda cb: (cb.block(cb.C["block"]), cb.upgrade_hand())))
_add(card("seeing_red", "Seeing Red", "skill", 1, "uncommon",
          "Gain {m} Energy.\nExhaust.", magic=2, target="none",
          exhaust=True, up={"cost": -1},
          play=lambda cb: cb.gain_energy(cb.C["magic"])))
_add(card("bloodletting", "Bloodletting", "skill", 0, "uncommon",
          "Lose 3 HP.\nGain {m} Energy.", magic=2, target="none",
          up={"magic": 1},
          play=lambda cb: (cb.lose_hp(3), cb.gain_energy(cb.C["magic"]))))
_add(card("flex", "Flex", "skill", 0, "uncommon",
          "Gain {m} Strength\nthis turn.", magic=2, target="none",
          up={"magic": 2},
          play=lambda cb: cb.status(cb.player, "str_tmp", cb.C["magic"])))
_add(card("uppercut", "Uppercut", "attack", 2, "uncommon",
          "Deal {d} damage.\nApply {m} Weak and\n{m} Vulnerable.",
          dmg=13, magic=1, up={"dmg": 2, "magic": 1},
          play=lambda cb: (cb.atk(cb.target, cb.C["dmg"]),
                           cb.status(cb.target, "weak", cb.C["magic"]),
                           cb.status(cb.target, "vuln", cb.C["magic"]))))
_add(card("entrench", "Entrench", "skill", 2, "uncommon",
          "Double your Block.", target="none", up={"cost": -1},
          play=lambda cb: cb.block(cb.player.block)))

# --- powers ----------------------------------------------------------------
_add(card("inflame", "Inflame", "power", 1, "uncommon",
          "Gain {m} Strength.", magic=2, target="none",
          up={"magic": 1},
          play=lambda cb: cb.status(cb.player, "str", cb.C["magic"])))
_add(card("metallicize", "Metallicize", "power", 1, "uncommon",
          "At the end of your\nturn, gain {m} Block.",
          magic=3, target="none", up={"magic": 1},
          play=lambda cb: cb.status(cb.player, "metallicize", cb.C["magic"])))
_add(card("juggernaut", "Juggernaut", "power", 2, "rare",
          "Whenever you gain\nBlock, deal {m} damage\nto a random enemy.",
          magic=5, target="none", up={"magic": 2},
          play=lambda cb: cb.status(cb.player, "juggernaut", cb.C["magic"])))
_add(card("regeneration", "Regeneration", "power", 1, "uncommon",
          "At the end of your turn,\nheal {m} HP.", magic=5,
          target="none", up={"magic": 2},
          play=lambda cb: cb.status(cb.player, "regen", cb.C["magic"])))
_add(card("thorns", "Thorns", "power", 1, "uncommon",
          "Gain {m} Thorns.", magic=3, target="none", up={"magic": 2},
          play=lambda cb: cb.status(cb.player, "thorns", cb.C["magic"])))
_add(card("demon_form", "Demon Form", "power", 3, "rare",
          "At the start of your\nturn, gain {m} Strength.",
          magic=2, target="none", up={"magic": 1},
          play=lambda cb: cb.status(cb.player, "demon", cb.C["magic"])))

# --- rare ------------------------------------------------------------------
_add(card("bludgeon", "Bludgeon", "attack", 3, "rare",
          "Deal {d} damage.", dmg=32, up={"dmg": 10},
          play=lambda cb: cb.atk(cb.target, cb.C["dmg"])))
_add(card("reaper", "Reaper", "attack", 2, "rare",
          "Deal {d} damage to ALL\nenemies. Heal for\nunblocked damage.",
          dmg=4, target="all", exhaust=True, up={"dmg": 1},
          play=lambda cb: cb.leech_all(cb.C["dmg"])))
_add(card("impervious", "Impervious", "skill", 2, "rare",
          "Gain {b} Block.\nExhaust.", block=30, target="none",
          exhaust=True, up={"block": 10},
          play=lambda cb: cb.block(cb.C["block"])))
_add(card("limit_break", "Limit Break", "skill", 1, "rare",
          "Double your Strength.\nExhaust.", target="none",
          exhaust=True, up={"cost": -1},
          play=lambda cb: cb.double_strength()))
_add(card("whirlwind", "Whirlwind", "attack", -1, "rare",
          "Deal {d} damage to ALL\nenemies X times.", dmg=5,
          target="all", up={"dmg": 3},
          play=lambda cb: cb.whirlwind()))
_add(card("offering", "Offering", "skill", 0, "rare",
          "Lose {l} HP.\nGain 2 Energy.\nDraw 3 cards.",
          hp_loss=6, target="none", exhaust=True, up={"hp_loss": -3},
          play=lambda cb: (cb.lose_hp(cb.C["hp_loss"]), cb.gain_energy(2), cb.draw(3))))

POOL = {r: [c["id"] for c in CARDS.values() if c["rarity"] == r]
        for r in ("common", "uncommon", "rare")}

STARTER_DECK = (["strike"] * 5) + (["defend"] * 4) + ["bash"]

# --------------------------------------------------------------- enemies ---

ENEMIES = {}


def enemy(eid, name, hp, art, color, moves, ai="random"):
    ENEMIES[eid] = dict(id=eid, name=name, hp=hp, art=art, color=color,
                        moves=moves, ai=ai)


def move(name, kind, dmg=0, hits=1, block=0, status=None, weight=1,
         once=False, heal=0, gold=0, cards=None):
    return dict(name=name, kind=kind, dmg=dmg, hits=hits, block=block,
                status=status, weight=weight, once=once, heal=heal, gold=gold,
                cards=cards)


enemy("louse", "Louse", (13, 17), [
    r"  /\_/\  ",
    r" ( o.o ) ",
    r"  > ^ <  ",
    r" /|   |\ ",
], "green", [move("Bite", "attack", 6, weight=3),
             move("Grow", "buff", status=("str", 3), weight=1)])

enemy("jaw_worm", "Jaw Worm", (40, 45), [
    r" __     __ ",
    r"(  \___/  )",
    r" \  o o  / ",
    r" /|     |\ ",
], "orange", [move("Chomp", "attack", 11, weight=3),
              move("Thrash", "attack", 7, block=5, weight=2),
              move("Bellow", "buff", block=6, status=("str", 3), weight=1)])

enemy("cultist", "Cultist", (44, 50), [
    r"    ___    ",
    r"   /_o_\   ",
    r"   | o |   ",
    r"  /|   |\  ",
], "purple", [move("Ritual", "buff", status=("str", 3), once=True, weight=99),
              move("Dark Strike", "attack", 6, weight=1)], ai="ritual")

enemy("slime", "Acid Slime", (27, 32), [
    r"   .---.   ",
    r"  / o o \  ",
    r"  |  ^   | ",
    r"   \___/   ",
], "teal", [move("Tackle", "attack", 9, weight=3),
            move("Lick", "debuff", status=("weak", 2), weight=1)])

enemy("chosen", "Chosen", (58, 64), [
    r"   .---.   ",
    r"  ( o o )  ",
    r"   \___/   ",
    r"  /|   |\  ",
], "purple", [move("Poke", "attack", 5, hits=2, weight=3),
              move("Hex", "debuff", status=("vuln", 1), weight=2),
              move("Zap", "attack", 12, weight=1)])

enemy("parasite", "Shelled Parasite", (64, 70), [
    r" ,-------.  ",
    r"(  o   o  ) ",
    r" \       /  ",
    r" /|     |\  ",
], "green", [move("Fell", "attack", 15, weight=2),
             move("Double Strike", "attack", 7, hits=2, weight=2),
             move("Shell", "block", block=14, weight=1)])

enemy("sentry", "Sentry", (38, 44), [
    r"   [===]    ",
    r"  /|   |\   ",
    r"   |   |    ",
    r"  _|   |_   ",
], "blue", [move("Beam", "attack", 9, weight=3),
            move("Charge", "buff", block=10, status=("str", 2), weight=1)])

enemy("nob", "Gremlin Nob", (50, 56), [
    r"    ,---.   ",
    r"   ( >.< )  ",
    r"   /|   |\  ",
    r"  / |   | \ ",
], "red", [move("Skull Bash", "attack", 6, status=("vuln", 2), weight=2),
           move("Rush", "attack", 13, weight=3),
           move("Bellow", "buff", status=("str", 2), weight=1)])

enemy("book", "Book of Stabbing", (92, 100), [
    r"  _______  ",
    r" |  ___  | ",
    r" | |___| | ",
    r" |_______| ",
], "red", [move("Multi-Stab", "attack", 6, hits=3, weight=3),
           move("Heavy Stab", "attack", 15, weight=2)])

enemy("hound", "Cinder Hound", (52, 58), [
    r"   /\  /\   ",
    r"  ( oo oo )  ",
    r"   \  ^  /   ",
    r"   /|   |\   ",
], "orange", [move("Bite", "attack", 13, weight=3),
              move("Pounce", "attack", 8, hits=2, weight=2),
              move("Howl", "buff", status=("str", 2), weight=1)])

enemy("revenant", "Ash Revenant", (62, 68), [
    r"   .---.    ",
    r"  | o o |   ",
    r"   \ - /    ",
    r"  /|   |\   ",
], "teal", [move("Strike", "attack", 14, weight=3),
            move("Curse", "debuff", status=("weak", 2), weight=2),
            move("Reform", "block", block=12, heal=5, weight=1)])

enemy("warden", "The Ash Warden", (135, 145), [
    r"   ,-----.   ",
    r"  | o   o |  ",
    r"  |   ^   |  ",
    r"   \_____/   ",
], "gold", [move("Cleave", "attack", 12, weight=3),
            move("Bulwark", "buff", block=16, status=("str", 2), weight=1),
            move("Crush", "attack", 19, weight=2),
            move("Quake", "debuff", status=("vuln", 2), weight=1)], ai="boss")

enemy("choir", "The Hollow Choir", (170, 180), [
    r"   ~  ~  ~   ",
    r"  (o) (o)   ",
    r"   \  |  /   ",
    r"    \_|_/    ",
], "purple", [move("Hymn", "debuff", status=("vuln", 2), weight=2),
              move("Dissonance", "attack", 8, hits=3, weight=3),
              move("Crescendo", "attack", 22, weight=2),
              move("Silence", "buff", block=14, status=("str", 2), weight=1)],
     ai="boss")

enemy("king", "The Cinder King", (230, 245), [
    r"   \  |  /  ",
    r"  .--===--. ",
    r" (  o   o  )",
    r"  \  ___  / ",
], "red", [move("Ember Slash", "attack", 18, weight=2),
           move("Rain of Cinders", "attack", 8, hits=2, weight=2),
           move("Crown of Ash", "buff", block=15, status=("str", 3), weight=1),
           move("Wither", "debuff", status=("vuln", 2), weight=1)], ai="boss")

# Three acts, seven floors each, one keeper at the top of every act.
ENCOUNTERS = {
    0: [["louse", "louse"], ["jaw_worm"], ["cultist"], ["louse", "louse", "louse"],
        ["slime", "louse"], ["jaw_worm", "jaw_worm"], ["cultist", "louse"]],
    1: [["chosen"], ["parasite", "louse"], ["cultist", "cultist"],
        ["sentry", "sentry"], ["fungal", "louse"], ["wraith"],
        ["acolyte", "louse"], ["jaw_worm", "slime"], ["fungal", "fungal"]],
    2: [["wraith", "acolyte"], ["revenant"], ["hound", "hound"],
        ["parasite", "parasite"], ["chosen", "chosen"],
        ["acolyte", "acolyte", "acolyte"], ["revenant", "louse"],
        ["sentry", "wraith"], ["hound", "revenant"]],
}
ELITES = {
    0: [["nob"]],
    1: [["book"], ["collector"]],
    2: [["collector"], ["nob", "louse"], ["book", "louse"]],
}
BOSSES = [["warden"], ["choir"], ["king"]]

# ---------------------------------------------------------------- relics ---

RELICS = {
    "burning_blood": dict(name="Burning Blood", color="red",
                          desc="Heal 6 HP after each combat.", tag="BB"),
    "vajra": dict(name="Vajra", color="orange",
                  desc="Your minions have +1 Attack.", tag="VJ"),
    "anchor": dict(name="Anchor", color="blue",
                   desc="Start combat with a 0/3 Taunt guard.", tag="AN"),
    "lantern": dict(name="Lantern", color="gold",
                    desc="Gain 1 extra Energy on turn 1.", tag="LN"),
    "bag_of_prep": dict(name="Bag of Preparation", color="green",
                        desc="Draw 2 extra cards on turn 1.", tag="BP"),
    "bronze_scales": dict(name="Bronze Scales", color="teal",
                          desc="Enemy minions take 1 when they hit you.", tag="BS"),
    "blood_vial": dict(name="Blood Vial", color="red",
                       desc="Heal 2 HP at the start of each combat.", tag="BV"),
    "smooth_stone": dict(name="Oddly Smooth Stone", color="cyan",
                         desc="Your minions have +1 Health.", tag="SS"),
    "orichalcum": dict(name="Orichalcum", color="gold",
                       desc="If you end your turn with no minions, summon a 1/1.", tag="OR"),
    "gremlin_horn": dict(name="Gremlin Horn", color="green",
                         desc="Gain 1 Mana when an enemy minion dies.", tag="GH"),
    "pen_nib": dict(name="Pen Nib", color="purple",
                    desc="Every 5th attack deals double damage.", tag="PN"),
    "teapot": dict(name="Ancient Teapot", color="teal",
                   desc="Heal 4 additional HP at rest sites.", tag="TP"),
}

# ---------------------------------------------------------------- events ---

EVENTS = [
    dict(
        title="The Whispering Idol",
        text=["A stone idol hums in the dark. Its mouth is",
              "cracked open, and something glints inside."],
        choices=[
            dict(label="Reach inside", efe="Lose 8 HP. Gain a relic.", hp=-8,
                 relic=True),
            dict(label="Smash it", efe="Gain 75 gold.", gold=75),
            dict(label="Leave it alone", efe="Nothing happens."),
        ]),
    dict(
        title="Abandoned Camp",
        text=["A cold firepit. Someone left in a hurry -",
              "their pack still leans against a rock."],
        choices=[
            dict(label="Search the pack", efe="Gain 45 gold.", gold=45),
            dict(label="Sleep by the embers", efe="Heal 30% of max HP.",
                 heal_pct=0.30),
            dict(label="Move on", efe="Nothing happens."),
        ]),
    dict(
        title="The Forge",
        text=["An old forge still breathes heat. The coals",
              "are perfect for tempering steel - or flesh."],
        choices=[
            dict(label="Temper a card", efe="Upgrade a card.", pick="upgrade"),
            dict(label="Take an ember", efe="Gain 8 max HP.", maxhp=8),
            dict(label="Warm your hands", efe="Heal 12 HP.", heal=12),
        ]),
    dict(
        title="Gambler's Ghost",
        text=["A translucent figure shuffles cards without",
              "looking at them. \"Double or nothing?\""],
        choices=[
            dict(label="Wager 40 gold", efe="50/50: win 80 gold or lose 40.",
                 gamble=40),
            dict(label="Refuse", efe="Nothing happens."),
        ]),
    dict(
        title="Fountain of Ash",
        text=["Grey water moves against the wind. Drinking it",
              "would mend you - but ash never really leaves."],
        choices=[
            dict(label="Drink deeply", efe="Heal to full. Lose 4 max HP.",
                 full_heal=True, maxhp=-4),
            dict(label="Wash your wounds", efe="Heal 15 HP.", heal=15),
            dict(label="Walk away", efe="Nothing happens."),
        ]),
    dict(
        title="Collapsed Library",
        text=["Shelves lean like drunks. Most scrolls are dust,",
              "but one still glows faintly with old power."],
        choices=[
            dict(label="Take the scroll", efe="Gain a random rare card. Lose 10 HP.",
                 random_card="rare", hp=-10),
            dict(label="Salvage the shelves", efe="Gain 60 gold.", gold=60),
            dict(label="Leave", efe="Nothing happens."),
        ]),
    dict(
        title="The Altar of Cinders",
        text=["A black altar. Names are carved into it, and",
              "there is room for one more - if you give one up."],
        choices=[
            dict(label="Sacrifice a card", efe="Remove a card from your deck. Lose 5 HP.",
                 pick="remove", hp=-5),
            dict(label="Pray", efe="Heal 10 HP.", heal=10),
            dict(label="Leave", efe="Nothing happens."),
        ]),
]

# --------------------------------------------------------------- potions ---

POTIONS = {
    "fire": dict(tag="FI", name="Fire Potion", color="red", target=True,
                 desc="Deal 6 damage."),
    "block": dict(tag="BL", name="Block Potion", color="blue",
                  desc="Restore 8 health."),
    "strength": dict(tag="ST", name="Strength Potion", color="orange",
                     desc="Give your minions +1/+1."),
    "swift": dict(tag="SW", name="Swift Potion", color="green",
                  desc="Draw 2 cards."),
    "energy": dict(tag="EN", name="Energy Potion", color="gold",
                   desc="Gain 2 Mana."),
    "fear": dict(tag="FE", name="Fear Potion", color="purple", target=True,
                 desc="Apply 3 Vulnerable."),
    "regen": dict(tag="RE", name="Regen Potion", color="green",
                  desc="Restore 10 health."),
    "poison": dict(tag="PO", name="Poison Potion", color="teal", target=True,
                   desc="Apply 6 Poison."),
}

# ------------------------------------------------------- extra card pool ---

_add(card("dropkick", "Dropkick", "attack", 1, "uncommon",
          "Deal {d} damage.\nIf the enemy is\nVulnerable: +1 Energy,\ndraw 1.",
          dmg=5, up={"dmg": 3},
          play=lambda cb: cb.dropkick()))
_add(card("hemokinesis", "Hemokinesis", "attack", 1, "uncommon",
          "Lose 2 HP.\nDeal {d} damage.", dmg=15, up={"dmg": 5},
          play=lambda cb: (cb.lose_hp(2),
                           cb.atk(cb.target, cb.C["dmg"]))))
_add(card("intimidate", "Intimidate", "skill", 0, "uncommon",
          "Apply {m} Weak to\nALL enemies.\nExhaust.", magic=1,
          target="all", exhaust=True, up={"magic": 1},
          play=lambda cb: cb.status_all("weak", cb.C["magic"])))
_add(card("shockwave", "Shockwave", "skill", 2, "uncommon",
          "Apply {m} Weak and\n{m} Vulnerable to\nALL enemies.\nExhaust.",
          magic=3, target="all", exhaust=True, up={"magic": 2},
          play=lambda cb: (cb.status_all("weak", cb.C["magic"]),
                           cb.status_all("vuln", cb.C["magic"]))))
_add(card("blur", "Blur", "skill", 1, "uncommon",
          "Gain {b} Block.\nBlock is not removed\nat the start of your\nnext turn.",
          block=5, target="none", up={"block": 3},
          play=lambda cb: (cb.block(cb.C["block"]),
                           cb.status(cb.player, "blur", 1))))
_add(card("berserk", "Berserk", "power", 0, "rare",
          "Gain 2 Vulnerable.\nGain 1 Energy at the\nstart of each turn.",
          target="none",
          play=lambda cb: (cb.status(cb.player, "vuln", 2),
                           cb.status(cb.player, "berserk", 1))))
_add(card("fiend_fire", "Fiend Fire", "attack", 2, "rare",
          "Exhaust your hand.\nDeal {d} damage per\ncard Exhausted.",
          dmg=7, exhaust=True, up={"dmg": 3},
          play=lambda cb: cb.fiend_fire()))
_add(card("feed", "Feed", "attack", 1, "rare",
          "Deal {d} damage.\nIf this kills, gain\n3 max HP.",
          dmg=10, up={"dmg": 4},
          play=lambda cb: cb.feed()))

# ------------------------------------------------------ extra encounters ---

enemy("fungal", "Fungal Beast", (46, 52), [
    r"   .---.    ",
    r"  ( o o )   ",
    r"   \ ^ /    ",
    r"  /|   |\   ",
], "green", [move("Bite", "attack", 8, weight=3),
            move("Spore", "debuff", status=("weak", 2), weight=2),
            move("Grow", "buff", status=("str", 2), weight=1)])

enemy("wraith", "Wraith", (42, 48), [
    r"   ~ ~ ~    ",
    r"  ( o o )   ",
    r"   \   /    ",
    r"   /   \    ",
], "teal", [move("Grasp", "attack", 12, weight=3),
            move("Wail", "debuff", status=("weak", 2), weight=2),
            move("Fade", "block", block=10, weight=1)])

enemy("acolyte", "Acolyte", (38, 44), [
    r"    /\_/\   ",
    r"   | o o |  ",
    r"    \ - /   ",
    r"   /|   |\  ",
], "purple", [move("Litany", "buff", status=("str", 2), once=True, weight=99),
              move("Dark Strike", "attack", 7, weight=1)], ai="ritual")

enemy("collector", "The Collector", (104, 112), [
    r"   _____    ",
    r"  |  o  |   ",
    r"  |_____|   ",
    r"  /|   |\   ",
], "gold", [move("Collect", "attack", 10, hits=2, weight=2),
            move("Torch", "attack", 17, weight=2),
            move("Ward", "block", block=15, weight=1)])

RELICS.update({
    "meat": dict(name="Meat on the Bone", color="red",
                 desc="Heal 12 HP after combat if below half HP.", tag="MB"),
})

RELICS.update({
    "ember_heart": dict(name="Ember Heart", color="red", boss=True, tag="EH",
                        desc="Heal 8 HP after every combat."),
    "molten_core": dict(name="Molten Core", color="orange", boss=True, tag="MC",
                        desc="Your minions have +2 Attack."),
    "bastion": dict(name="Bastion Plate", color="blue", boss=True, tag="BA",
                    desc="Start combat with a 0/3 Taunt guard."),
    "hourglass": dict(name="Black Hourglass", color="purple", boss=True, tag="HG",
                      desc="Draw 1 extra card each turn."),
    "twin_fangs": dict(name="Twin Fangs", color="teal", boss=True, tag="TF",
                       desc="Your minions have +1 Attack."),
    "bloodstone": dict(name="Bloodstone", color="red", boss=True, tag="BD",
                       desc="Gain 10 max HP. Heal 4 HP after combat."),
})

EVENTS.extend([
    dict(
        title="The Mirror",
        text=["A mirror stands in the ash, and your reflection",
              "is holding a card you have never seen."],
        choices=[
            dict(label="Touch the glass", efe="Duplicate a card in your deck.",
                 pick="duplicate"),
            dict(label="Look away", efe="Heal 8 HP.", heal=8),
            dict(label="Break it", efe="Gain 40 gold.", gold=40),
        ]),
    dict(
        title="The Old Soldier",
        text=["A soldier in rusted plate offers you a charm.",
              "\"Take it. I have no more fights in me.\""],
        choices=[
            dict(label="Take the charm", efe="Lose 6 max HP. Gain a relic.",
                 maxhp=-6, relic=True),
            dict(label="Share your rations", efe="Lose 30 gold. Gain 10 max HP.",
                 gold=-30, maxhp=10),
            dict(label="Salute and leave", efe="Nothing happens."),
        ]),
])

# rebuild the reward pools so the new cards are included
POOL = {r: [c["id"] for c in CARDS.values() if c["rarity"] == r]
        for r in ("common", "uncommon", "rare")}

# ------------------------------------------------------- content expansion --

_add(card("headbutt", "Headbutt", "attack", 1, "uncommon",
          "Deal {d} damage.\nPut a card from your\ndiscard on top of\nyour draw pile.",
          dmg=9, up={"dmg": 3},
          play=lambda cb: (cb.atk(cb.target, cb.C["dmg"]), cb.headbutt())))
_add(card("rage", "Rage", "skill", 0, "uncommon",
          "Whenever you play an\nAttack this turn, gain\n{m} Block.",
          magic=3, target="none", up={"magic": 2},
          play=lambda cb: cb.status(cb.player, "rage", cb.C["magic"])))
_add(card("searing_blow", "Searing Blow", "attack", 2, "uncommon",
          "Deal {d} damage.\nCan be upgraded\nmany times.",
          dmg=12, multi_up=True, up={"dmg": 4},
          play=lambda cb: cb.atk(cb.target, cb.C["dmg"])))
_add(card("flame_barrier", "Flame Barrier", "skill", 2, "uncommon",
          "Gain {b} Block.\nGain {m} Thorns this\nturn.",
          block=12, magic=4, target="none", up={"block": 4, "magic": 2},
          play=lambda cb: (cb.block(cb.C["block"]),
                           cb.status(cb.player, "thorns_tmp", cb.C["magic"]),
                           cb.status(cb.player, "thorns", cb.C["magic"]))))
_add(card("second_wind", "Second Wind", "skill", 1, "uncommon",
          "Exhaust all non-Attack\ncards in your hand.\nGain {b} Block for\neach one.",
          block=5, magic=5, target="none", up={"block": 2},
          play=lambda cb: cb.second_wind()))
_add(card("immolate", "Immolate", "attack", 2, "rare",
          "Deal {d} damage to\nALL enemies.\nExhaust.", dmg=18,
          target="all", exhaust=True, up={"dmg": 6},
          play=lambda cb: cb.atk_all(cb.C["dmg"])))
_add(card("reckless_charge", "Reckless Charge", "attack", 0, "common",
          "Deal {d} damage.\nLose 3 HP.", dmg=9, up={"dmg": 3},
          play=lambda cb: (cb.lose_hp(3), cb.atk(cb.target, cb.C["dmg"]))))
_add(card("ember_shot", "Ember Shot", "attack", 0, "common",
          "Deal {d} damage.\nDraw 1 card.\nExhaust.", dmg=5, magic=1,
          exhaust=True, up={"dmg": 3},
          play=lambda cb: (cb.atk(cb.target, cb.C["dmg"]), cb.draw(1))))

enemy("mugger", "Mugger", (44, 50), [
    r"   ,---.    ",
    r"  | o o |   ",
    r"  |  ^  |   ",
    r"  /|   |\\   ",
], "gold", [move("Stab", "attack", 10, weight=3),
            move("Steal", "attack", 6, gold=8, weight=2),
            move("Smoke Bomb", "block", block=10, weight=1)])

enemy("spore_mother", "Spore Mother", (70, 78), [
    r"   ,---.    ",
    r"  ( o o )   ",
    r"   \\ ^ /    ",
    r"  /|   |\\   ",
], "green", [move("Bite", "attack", 13, weight=3),
             move("Spores", "debuff", status=("poison", 3), weight=2),
             move("Bloom", "buff", block=10, status=("str", 2), weight=1)])

enemy("wizard", "Gremlin Wizard", (28, 34), [
    r"   /\\_/\\   ",
    r"  ( o o )   ",
    r"   \\ - /    ",
    r"  /|   |\\   ",
], "blue", [move("Zap", "attack", 9, weight=3),
            move("Charge", "buff", status=("str", 3), once=True, weight=1),
            move("Confuse", "debuff", status=("weak", 2), weight=2)], ai="ritual")

ENCOUNTERS[0].append(["mugger"])
ELITES[0].append(["mugger"])
ENCOUNTERS[1].append(["wizard", "louse"])
ENCOUNTERS[2].append(["wizard", "acolyte"])
ELITES[1].append(["spore_mother"])

POTIONS.update({
    "steel": dict(tag="ES", name="Essence of Steel", color="blue",
                  desc="Give a minion Divine Shield."),
    "memories": dict(tag="LM", name="Liquid Memories", color="purple",
                     desc="Draw 2 cards."),
    "juice": dict(tag="FJ", name="Fruit Juice", color="red",
                  desc="Gain 5 max HP."),
})

RELICS.update({
    "strawberry": dict(name="Strawberry", color="red", tag="SB",
                       desc="Gain 7 max HP when picked up."),
    "letter_opener": dict(name="Letter Opener", color="teal", tag="LO",
                          desc="Every 3 spells, deal 2 damage to the enemy hero."),
    "sundial": dict(name="Sundial", color="gold", tag="SD",
                    desc="Every 3rd turn, gain 1 Energy."),
    "throne": dict(name="Throne of Ash", color="red", boss=True, tag="TA",
                   desc="+1 Energy each turn. Lose 6 max HP."),
    "choir_bell": dict(name="Choir Bell", color="purple", boss=True, tag="CB",
                       desc="Draw 1 extra card at the start of combat."),
})

EVENTS.extend([
    dict(
        title="The Gambling Den",
        text=["A lantern-lit table in the rubble. The dealer has",
              "no face, but the cards are real enough."],
        choices=[
            dict(label="Bet 40 gold", efe="50/50: win 80 or lose 40.",
                 gamble=40),
            dict(label="Buy a card", efe="Pay 60 gold for an uncommon card.",
                 gold=-60, random_card="uncommon"),
            dict(label="Walk away", efe="Nothing happens."),
        ]),
    dict(
        title="The Widow",
        text=["She sits among the ashes of her house, holding a",
              "charm. \"Take it. Just sit with me a while.\""],
        choices=[
            dict(label="Sit with her", efe="Lose 5 max HP. Gain a relic.",
                 maxhp=-5, relic=True),
            dict(label="Give her gold", efe="Lose 40 gold. Heal 25 HP.",
                 gold=-40, heal=25),
            dict(label="Leave quietly", efe="Nothing happens."),
        ]),
])

POOL = {r: [c["id"] for c in CARDS.values() if c["rarity"] == r]
        for r in ("common", "uncommon", "rare")}

# ------------------------------------------------------------ achievements --

ACHIEVEMENTS = {
    "first_blood": dict(name="First Blood", desc="Win your first combat."),
    "act1": dict(name="Through the Gate", desc="Clear Act I."),
    "act2": dict(name="Hollow Victory", desc="Clear Act II."),
    "victory": dict(name="Cinderfall", desc="Defeat the Cinder King."),
    "asc1": dict(name="Harder Ashes", desc="Win on Ascension 1 or higher."),
    "slayer": dict(name="Ash Sweeper", desc="Defeat 50 enemies (lifetime)."),
    "big_hit": dict(name="Overkill", desc="Deal 12 damage with a single hit."),
    "collector": dict(name="Relic Hunter", desc="Hold 8 relics at once."),
    "rich": dict(name="Deep Pockets", desc="Carry 500 gold."),
    "potion_user": dict(name="Alchemist", desc="Drink 10 potions (lifetime)."),
    "lean": dict(name="Lean Machine", desc="Win with a deck of 15 cards or fewer."),
    "daily": dict(name="Daily Ritual", desc="Finish a daily run."),
    "loremaster": dict(name="Loremaster", desc="Discover 80% of the codex."),
}

TIPS = {
    "combat": "Block is wiped at the start of your turn - spend it before you end.",
    "intent": "The line above an enemy is exactly what it will do next.",
    "reward": "You can skip a card. Small decks draw their best cards more often.",
    "shop": "Card removal is often the strongest thing you can buy.",
    "rest": "Upgrading a key card usually beats adding a weak one.",
    "potion": "Potions are free actions. Save them for elites and keepers.",
    "map": "Elites are dangerous, but they always drop a potion and a relic.",
    "boon": "Ember boons are permanent. Build around the one you take.",
    "ascend": "Ascension gives enemies more HP and Strength for less gold.",
}

# ------------------------------------------------------------ act IV: heart --

_add(card("burn", "Burn", "status", -2, "status",
          "Unplayable.\nAt the end of your turn,\ntake 2 damage.",
          target="none", play=lambda cb: None))
_add(card("brand", "Brand", "attack", 1, "uncommon",
          "Deal {d} damage.\nAdd a Burn to your\ndiscard.", dmg=12,
          up={"dmg": 4},
          play=lambda cb: (cb.atk(cb.target, cb.C["dmg"]),
                           cb.add_status_card("burn"))))
_add(card("cauterize", "Cauterize", "skill", 1, "uncommon",
          "Exhaust all Burns in\nyour hand. Heal {m} HP\nfor each.",
          magic=5, target="none", up={"magic": 2},
          play=lambda cb: cb.cauterize()))
_add(card("firestorm", "Firestorm", "attack", 2, "rare",
          "Deal {d} damage to\nALL enemies twice.", dmg=7,
          target="all", up={"dmg": 2},
          play=lambda cb: cb.atk_all(cb.C["dmg"], times=2)))
_add(card("last_light", "Last Light", "attack", 3, "rare",
          "Deal {d} damage.", dmg=30, up={"dmg": 10},
          play=lambda cb: cb.atk(cb.target, cb.C["dmg"])))
_add(card("ashen_guard", "Ashen Guard", "skill", 2, "rare",
          "Gain {b} Block.\nExhaust.", block=22, target="none",
          exhaust=True, up={"block": 8},
          play=lambda cb: cb.block(cb.C["block"])))
_add(card("pyre", "Pyre", "skill", 0, "rare",
          "Exhaust your hand.\nDraw that many cards\nplus {m}.", magic=1,
          target="none", exhaust=True, up={"magic": 1},
          play=lambda cb: cb.pyre()))
_add(card("smolder", "Smolder", "attack", 0, "common",
          "Deal {d} damage.\nApply 2 Poison.\nExhaust.", dmg=5,
          exhaust=True, up={"dmg": 3},
          play=lambda cb: (cb.atk(cb.target, cb.C["dmg"]),
                           cb.status(cb.target, "poison", 2))))
_add(card("ember_ward", "Ember Ward", "skill", 1, "common",
          "Gain {b} Block.\nGain {m} Thorns this\nturn.", block=10, magic=2,
          target="none", up={"block": 3, "magic": 1},
          play=lambda cb: (cb.block(cb.C["block"]),
                           cb.status(cb.player, "thorns_tmp", cb.C["magic"]),
                           cb.status(cb.player, "thorns", cb.C["magic"]))))

enemy("servant", "Flame Servant", (40, 46), [
    r"   (  )     ",
    r"  ( oo )    ",
    r"   \\  /     ",
    r"  /|  |\\    ",
], "orange", [move("Ember Bolt", "attack", 8, weight=3),
              move("Fan the Flames", "debuff", status=("weak", 1),
                   cards=("burn", 2), weight=2),
              move("Stoke", "buff", status=("str", 2), weight=1)])

enemy("colossus", "Molten Colossus", (112, 122), [
    r"  ,-------.  ",
    r" |  o   o  | ",
    r" |    ^    | ",
    r"  \\_______/  ",
], "orange", [move("Slam", "attack", 16, weight=3),
              move("Molten Armor", "buff", block=14, status=("str", 2),
                   weight=1),
              move("Eruption", "attack", 8, hits=3, weight=2)])

enemy("first_flame", "The First Flame", (300, 320), [
    r"    \\ | /    ",
    r"   .-( )-.   ",
    r"  (  o o  )  ",
    r"   \\_____/   ",
], "gold", [move("Pyre", "attack", 20, weight=2),
            move("Cinder Storm", "attack", 9, hits=3, weight=3),
            move("Immolate", "debuff", status=("vuln", 2),
                 cards=("burn", 2), weight=2),
            move("Rebirth", "buff", block=20, status=("str", 3), weight=1)],
     ai="boss")

ENCOUNTERS[3] = [["servant", "hound"], ["wraith", "servant"],
                 ["revenant", "wraith"], ["servant", "servant", "louse"],
                 ["hound", "servant"]]
ELITES[3] = [["colossus"]]
BOSSES.append(["first_flame"])

RELICS.update({
    "crown_flame": dict(name="Crown of the First Flame", color="orange",
                        boss=True, tag="CF",
                        desc="+1 Energy each turn. Lose 8 max HP."),
    "ashen_wings": dict(name="Ashen Wings", color="cyan", boss=True,
                        tag="AW", desc="Start combat with a 1/2 Whelp."),
    "whetstone": dict(name="Whetstone", color="text", tag="WH",
                      desc="Attacks deal 1 extra damage."),
    "heartstone": dict(name="Heartstone", color="red", tag="HS",
                       desc="Gain 6 max HP. Heal 3 HP after combat."),
})

POTIONS.update({
    "firestorm": dict(tag="FS", name="Firestorm Potion", color="orange",
                      desc="Deal 3 damage to all enemy minions."),
    "ember_blood": dict(tag="EB", name="Ember Blood", color="red",
                        desc="Restore 25 health."),
})

EVENTS.extend([
    dict(
        title="The Burning Library",
        text=["Shelves of scorched books. One still turns its own pages,",
              "writing something new in the margin."],
        choices=[
            dict(label="Read the page", efe="Gain a random rare card. Lose 8 HP.",
                 random_card="rare", hp=-8),
            dict(label="Take the ember lamp", efe="Gain 55 gold.", gold=55),
            dict(label="Leave it burning", efe="Nothing happens."),
        ]),
    dict(
        title="The Silent Bell",
        text=["A bell hangs in the ash, perfectly still. It has no",
              "clapper, and yet it is clearly waiting for you."],
        choices=[
            dict(label="Ring it", efe="Lose 6 max HP. Gain 120 gold.",
                 maxhp=-6, gold=120),
            dict(label="Listen", efe="Heal 18 HP.", heal=18),
            dict(label="Leave it", efe="Nothing happens."),
        ]),
])

ACHIEVEMENTS.update({
    "heart": dict(name="Heart of Ember", desc="Descend into the Ember Heart."),
    "first_flame": dict(name="Snuffed Out", desc="Defeat the First Flame."),
    "fourth": dict(name="Ashes to Ashes", desc="Clear all four acts."),
})

POOL = {r: [c["id"] for c in CARDS.values() if c["rarity"] == r]
        for r in ("common", "uncommon", "rare")}

# ----------------------------------------------------------------- classes --

CLASSES = {
    "warden": dict(
        name="The Warden", color="red", starter="bash",
        blurb="Strength, heavy blows and blood price.",
        detail="Big attacks, self-damage and raw Strength."),
    "ashblade": dict(
        name="The Ashblade", color="green", starter="poison_stab",
        blurb="Poison, shivs and card draw.",
        detail="Stack Poison, throw Shivs, draw through your deck."),
    "emberwright": dict(
        name="The Emberwright", color="blue", starter="beam_cell",
        blurb="Energy, Burn and machines.",
        detail="Gain Energy, add Burns to your own deck, power up."),
    "pilgrim": dict(
        name="The Pilgrim", color="gold", starter="smite",
        blurb="Block, healing and thorns.",
        detail="Heal, stack Block and punish attackers."),
}

STARTERS = {
    "warden": ["strike"] * 5 + ["defend"] * 4 + ["bash"],
    "ashblade": ["strike"] * 5 + ["defend"] * 4 + ["poison_stab"],
    "emberwright": ["strike"] * 5 + ["defend"] * 4 + ["beam_cell"],
    "pilgrim": ["strike"] * 5 + ["defend"] * 4 + ["smite"],
}

# Which existing cards belong to which class.
CLASS_OF = {
    "strike": "shared", "defend": "shared",
    "bash": "warden", "cleave": "warden", "twin_strike": "warden",
    "iron_wave": "warden", "clothesline": "warden", "anger": "warden",
    "body_slam": "warden", "sword_boomerang": "warden",
    "thunderclap": "warden", "uppercut": "warden", "inflame": "warden",
    "demon_form": "warden", "juggernaut": "warden", "bludgeon": "warden",
    "reaper": "warden", "impervious": "warden", "limit_break": "warden",
    "whirlwind": "warden", "hemokinesis": "warden", "intimidate": "warden",
    "shockwave": "warden", "flex": "warden", "rage": "warden",
    "searing_blow": "warden", "immolate": "warden",
    "reckless_charge": "warden", "second_wind": "warden",
    "fiend_fire": "warden", "feed": "warden",
    "quick_slash": "ashblade", "poison_stab": "ashblade",
    "pommel_strike": "ashblade", "battle_trance": "ashblade",
    "smolder": "ashblade", "brand": "ashblade", "headbutt": "ashblade",
    "dropkick": "ashblade",
    "metallicize": "emberwright", "seeing_red": "emberwright",
    "bloodletting": "emberwright", "blur": "emberwright",
    "berserk": "emberwright", "offering": "emberwright",
    "ember_shot": "emberwright", "ember_ward": "emberwright",
    "pyre": "emberwright", "last_light": "emberwright",
    "firestorm": "emberwright",
    "shrug_it_off": "pilgrim", "true_grit": "pilgrim",
    "armaments": "pilgrim", "regeneration": "pilgrim", "thorns": "pilgrim",
    "flame_barrier": "pilgrim", "cauterize": "pilgrim",
    "ashen_guard": "pilgrim", "entrench": "pilgrim",
}

for _cid, _cls in CLASS_OF.items():
    CARDS[_cid]["cls"] = _cls
for _cid, _card in CARDS.items():
    _card.setdefault("cls", "shared")

# --- Ashblade --------------------------------------------------------------
_add(card("shiv", "Shiv", "attack", 0, "token",
          "Deal {d} damage.\nExhaust.", dmg=3, exhaust=True, cls="ashblade",
          up={"dmg": 0},
          play=lambda cb: cb.atk(cb.target, cb.C["dmg"])))
_add(card("blade_dance", "Blade Dance", "skill", 1, "common",
          "Add {m} Shivs to\nyour hand.", magic=3, target="none",
          cls="ashblade", up={"magic": 1},
          play=lambda cb: cb.add_shivs(cb.C["magic"])))
_add(card("cloak_dagger", "Cloak and Dagger", "skill", 1, "common",
          "Gain {b} Block.\nAdd {m} Shivs to\nyour hand.", block=6, magic=2,
          target="none", cls="ashblade", up={"block": 3, "magic": 1},
          play=lambda cb: (cb.block(cb.C["block"]),
                           cb.add_shivs(cb.C["magic"]))))
_add(card("deadly_poison", "Deadly Poison", "skill", 1, "common",
          "Apply {m} Poison.", magic=5, target="enemy", cls="ashblade",
          up={"magic": 2},
          play=lambda cb: cb.status(cb.target, "poison", cb.C["magic"])))
_add(card("catalyst", "Catalyst", "skill", 1, "rare",
          "Double the target's\nPoison. Exhaust.", target="enemy",
          exhaust=True, cls="ashblade", up={"cost": -1},
          play=lambda cb: cb.catalyst()))
_add(card("bane", "Bane", "attack", 1, "uncommon",
          "Deal {d} damage.\nDeal {m} more if the\ntarget is Poisoned.",
          dmg=6, magic=6, cls="ashblade", up={"dmg": 3, "magic": 3},
          play=lambda cb: cb.bonus_if_poisoned(cb.C["dmg"], cb.C["magic"])))
_add(card("envenom", "Envenom", "power", 1, "rare",
          "Attacks apply {m}\nPoison.", magic=1, target="none",
          cls="ashblade", up={"magic": 1},
          play=lambda cb: cb.status(cb.player, "envenom", cb.C["magic"])))
_add(card("footwork", "Footwork", "power", 1, "uncommon",
          "Gain {m} Dexterity.", magic=2, target="none", cls="ashblade",
          up={"magic": 1},
          play=lambda cb: cb.status(cb.player, "dex", cb.C["magic"])))
_add(card("backflip", "Backflip", "skill", 1, "common",
          "Gain {b} Block.\nDraw 2 cards.", block=5, target="none",
          cls="ashblade", up={"block": 3},
          play=lambda cb: (cb.block(cb.C["block"]), cb.draw(2))))
_add(card("sneaky_strike", "Sneaky Strike", "attack", 2, "uncommon",
          "Deal {d} damage.\nDeal {m} more if the\ntarget is Poisoned.",
          dmg=12, magic=5, cls="ashblade", up={"dmg": 4, "magic": 2},
          play=lambda cb: cb.bonus_if_poisoned(cb.C["dmg"], cb.C["magic"])))

# --- Emberwright -----------------------------------------------------------
_add(card("overclock", "Overclock", "skill", 0, "common",
          "Draw {m} cards.\nAdd a Burn to your\ndiscard.", magic=2,
          target="none", cls="emberwright", up={"magic": 1},
          play=lambda cb: (cb.draw(cb.C["magic"]),
                           cb.add_status_card("burn"))))
_add(card("turbo", "Turbo", "skill", 0, "uncommon",
          "Gain {m} Energy.\nAdd a Burn to your\ndiscard.", magic=2,
          target="none", cls="emberwright", up={"magic": 1},
          play=lambda cb: (cb.gain_energy(cb.C["magic"]),
                           cb.add_status_card("burn"))))
_add(card("combust", "Combust", "power", 1, "uncommon",
          "At the end of your\nturn, lose 1 HP and\ndeal {m} damage to\nALL enemies.",
          magic=5, target="none", cls="emberwright", up={"magic": 2},
          play=lambda cb: cb.status(cb.player, "combust", cb.C["magic"])))
_add(card("beam_cell", "Beam Cell", "attack", 1, "common",
          "Deal {d} damage.\nApply 1 Vulnerable.", dmg=7, magic=1,
          cls="emberwright", up={"dmg": 3},
          play=lambda cb: (cb.atk(cb.target, cb.C["dmg"]),
                           cb.status(cb.target, "vuln", 1))))
_add(card("glacier", "Glacier", "skill", 2, "uncommon",
          "Gain {b} Block.", block=16, target="none", cls="emberwright",
          up={"block": 6},
          play=lambda cb: cb.block(cb.C["block"])))
_add(card("hologram", "Hologram", "skill", 1, "uncommon",
          "Gain {b} Block.\nReturn a random card\nfrom your discard to\nyour hand.",
          block=5, target="none", cls="emberwright", up={"block": 3},
          play=lambda cb: (cb.block(cb.C["block"]), cb.hologram())))
_add(card("machine_learning", "Machine Learning", "power", 1, "rare",
          "Draw 1 extra card\nat the start of each\nturn.", target="none",
          cls="emberwright", up={"cost": 0},
          play=lambda cb: cb.status(cb.player, "machine", 1)))
_add(card("fusion", "Fusion", "power", 2, "rare",
          "Gain 1 Energy at the\nstart of each turn.\nDraw 1 fewer card.",
          target="none", cls="emberwright", up={"cost": -1},
          play=lambda cb: cb.status(cb.player, "fusion", 1)))

# --- Pilgrim ---------------------------------------------------------------
_add(card("prayer", "Prayer", "skill", 1, "common",
          "Heal {m} HP.\nExhaust.", magic=6, target="none",
          exhaust=True, cls="pilgrim", up={"magic": 3},
          play=lambda cb: cb.heal(cb.C["magic"])))
_add(card("sanctuary", "Sanctuary", "skill", 2, "uncommon",
          "Gain {b} Block.\nHeal {m} HP.", block=14, magic=3,
          target="none", cls="pilgrim", up={"block": 5, "magic": 2},
          play=lambda cb: (cb.block(cb.C["block"]), cb.heal(cb.C["magic"]))))
_add(card("zeal", "Zeal", "attack", 1, "common",
          "Deal 4 damage plus\n1 for every 3 Block\nyou have.", dmg=4,
          magic=3, cls="pilgrim", up={"dmg": 3, "magic": 0},
          play=lambda cb: cb.zeal()))
_add(card("smite", "Smite", "attack", 1, "common",
          "Deal {d} damage.\nHeal 2 HP.", dmg=10, cls="pilgrim",
          up={"dmg": 4},
          play=lambda cb: (cb.atk(cb.target, cb.C["dmg"]), cb.heal(2))))
_add(card("aegis", "Aegis", "skill", 2, "uncommon",
          "Gain {b} Block.\nExhaust.", block=20, target="none",
          exhaust=True, cls="pilgrim", up={"block": 8},
          play=lambda cb: cb.block(cb.C["block"])))
_add(card("divine_shield", "Divine Shield", "power", 1, "uncommon",
          "At the start of your\nturn, gain {m} Block.",
          magic=3, target="none", cls="pilgrim", up={"magic": 1},
          play=lambda cb: cb.status(cb.player, "divine", cb.C["magic"])))
_add(card("martyr", "Martyr", "attack", 2, "uncommon",
          "Deal 6 damage plus 1\nfor every 4 HP you\nare missing.", dmg=6,
          magic=4, cls="pilgrim", up={"dmg": 4},
          play=lambda cb: cb.martyr()))
_add(card("penance", "Penance", "skill", 0, "uncommon",
          "Lose 3 HP. Gain {m}\nEnergy. Draw 1 card.", magic=2,
          target="none", cls="pilgrim", up={"magic": 1},
          play=lambda cb: (cb.lose_hp(3), cb.gain_energy(cb.C["magic"]),
                           cb.draw(1))))
_add(card("consecrate", "Consecrate", "attack", 1, "uncommon",
          "Deal {d} damage to\nALL enemies.\nHeal 2 HP.", dmg=8,
          target="all", cls="pilgrim", up={"dmg": 3},
          play=lambda cb: (cb.atk_all(cb.C["dmg"]), cb.heal(2))))

ACHIEVEMENTS["polymath"] = dict(
    name="Polymath", desc="Win a run with all five classes.")

POOL = {r: [c["id"] for c in CARDS.values() if c["rarity"] == r]
        for r in ("common", "uncommon", "rare")}

# --- pool rounding ---------------------------------------------------------
_add(card("vigil", "Vigil", "skill", 1, "common",
          "Gain {b} Block.\nHeal 1 HP.", block=7, target="none",
          cls="pilgrim", up={"block": 3},
          play=lambda cb: (cb.block(cb.C["block"]), cb.heal(1))))
_add(card("censer", "Censer", "attack", 1, "common",
          "Deal {d} damage.\nHeal 1 HP.", dmg=9, cls="pilgrim",
          up={"dmg": 3},
          play=lambda cb: (cb.atk(cb.target, cb.C["dmg"]), cb.heal(1))))
_add(card("sanctum", "Sanctum", "skill", 2, "rare",
          "Gain {b} Block.\nHeal {m} HP.\nExhaust.", block=24, magic=5,
          target="none", exhaust=True, cls="pilgrim",
          up={"block": 8, "magic": 3},
          play=lambda cb: (cb.block(cb.C["block"]), cb.heal(cb.C["magic"]))))
_add(card("steam_vent", "Steam Vent", "skill", 1, "common",
          "Gain {b} Block.\nDeal {m} damage to\nALL enemies.", block=6,
          magic=4, target="none", cls="emberwright",
          up={"block": 3, "magic": 2},
          play=lambda cb: (cb.block(cb.C["block"]),
                           cb.atk_all(cb.C["magic"]))))

POOL = {r: [c["id"] for c in CARDS.values() if c["rarity"] == r]
        for r in ("common", "uncommon", "rare")}

# ------------------------------------------------------- class basics ------

# Each class gets its own basics with a small signature rider.
_add(card("w_strike", "Strike", "attack", 1, "basic", "Deal {d} damage.",
          dmg=7, cls="warden", up={"dmg": 3},
          play=lambda cb: cb.atk(cb.target, cb.C["dmg"])))
_add(card("w_defend", "Defend", "skill", 1, "basic", "Gain {b} Block.",
          block=5, cls="warden", target="none", up={"block": 3},
          play=lambda cb: cb.block(cb.C["block"])))
_add(card("a_strike", "Quick Cut", "attack", 1, "basic",
          "Deal {d} damage.\nDeal {m} more if the\ntarget is Poisoned.",
          dmg=5, magic=2, cls="ashblade", up={"dmg": 2, "magic": 1},
          play=lambda cb: cb.bonus_if_poisoned(cb.C["dmg"], cb.C["magic"])))
_add(card("a_defend", "Dodge", "skill", 1, "basic",
          "Gain {b} Block.\nDraw 1 card.", block=3, cls="ashblade",
          target="none", up={"block": 2},
          play=lambda cb: (cb.block(cb.C["block"]), cb.draw(1))))
_add(card("e_strike", "Spark", "attack", 1, "basic",
          "Deal {d} damage.\nDeal {m} more if you\nhold a Burn.",
          dmg=6, magic=4, cls="emberwright", up={"dmg": 2},
          play=lambda cb: cb.bonus_if_burn(cb.C["dmg"], cb.C["magic"])))
_add(card("e_defend", "Guard", "skill", 1, "basic", "Gain {b} Block.",
          block=6, cls="emberwright", target="none", up={"block": 3},
          play=lambda cb: cb.block(cb.C["block"])))
_add(card("p_strike", "Censure", "attack", 1, "basic",
          "Deal {d} damage.\nHeal {m} HP.", dmg=5, magic=1,
          cls="pilgrim", up={"dmg": 2},
          play=lambda cb: (cb.atk(cb.target, cb.C["dmg"]),
                           cb.heal(cb.C["magic"]))))
_add(card("p_defend", "Ward", "skill", 1, "basic", "Gain {b} Block.",
          block=6, cls="pilgrim", target="none", up={"block": 3},
          play=lambda cb: cb.block(cb.C["block"])))
_add(card("pal_strike", "Hammer", "attack", 1, "basic",
          "Deal {d} damage.\nGain {b} Block.", dmg=5, block=1,
          cls="paladin", up={"dmg": 2},
          play=lambda cb: (cb.atk(cb.target, cb.C["dmg"]),
                           cb.block(cb.C["block"]))))
_add(card("pal_defend", "Shield of Light", "skill", 1, "basic",
          "Gain {b} Block.\nGain {m} more if you\nhave Divine Shield.",
          block=5, magic=2, cls="paladin", target="none",
          up={"block": 3},
          play=lambda cb: cb.block(cb.C["block"] + (
              cb.C["magic"] if cb.player.st.get("shield") else 0))))

STARTERS = {
    "warden": ["w_strike"] * 5 + ["w_defend"] * 3 + ["w_brace", "bash"],
    "ashblade": (["a_strike"] * 5 + ["a_defend"] * 2
                 + ["a_poison_dart", "a_shiv_throw", "poison_stab"]),
    "emberwright": (["e_strike"] * 4 + ["e_defend"] * 3
                    + ["e_arc", "e_coil", "beam_cell"]),
    "pilgrim": (["p_strike"] * 4 + ["p_defend"] * 3
                + ["p_bless", "p_shield_bash", "smite"]),
    "paladin": (["pal_strike"] * 4 + ["pal_defend"] * 3
                + ["pal_blessing_of_might", "pal_aegis_blessing",
                   "pal_reinforce"]),
}

# ------------------------------------------------------- effect cards ------

def ecard(cls, cid, name, ctype, cost, rarity, eff, dmg=0, block=0, magic=0,
          up=None, text=None, play=None, **kw):
    d = card(cid, name, ctype, cost, rarity, text or "", cls=cls, **kw)
    d.update(dmg=dmg, block=block, magic=magic)
    d["effects"] = list(eff)
    if text is None:
        d["auto_text"] = True
    if up is None:
        up = {}
        if dmg:
            up["dmg"] = 3
        if block:
            up["block"] = 3
        if magic:
            up["magic"] = 1
    d["up"] = up
    if play is not None:
        d["play"] = play
    else:
        d["play"] = lambda cb: cb.run_effects(cb.C["effects"])
    _add(d)
    return d

# ------------------------------------------------------------ Warden ------

N = []
N.append(ecard("warden", "w_iron_bash", "Iron Bash", "attack", 2, "common",
               [("dmg", "dmg"), ("vuln", "magic")], dmg=14, magic=1,
               up={"dmg": 4, "magic": 1}))
N.append(ecard("warden", "w_heavy_swing", "Heavy Swing", "attack", 2, "common",
               [("dmg", "dmg"), ("lose_hp", "hp_loss")], dmg=15, hp_loss=2,
               up={"dmg": 5}))
N.append(ecard("warden", "w_cleave_arc", "Cleave Arc", "attack", 1, "common",
               [("all", "dmg")], dmg=7, target="all", up={"dmg": 3}))
N.append(ecard("warden", "w_shield_charge", "Shield Charge", "attack", 1,
               "common", [("dmg", "dmg"), ("block", "block")], dmg=8,
               block=4, up={"dmg": 2, "block": 2}))
N.append(ecard("warden", "w_rend", "Rend", "attack", 1, "common",
               [("dmg", "dmg"), ("vuln", "magic")], dmg=8, magic=1,
               up={"dmg": 2, "magic": 1}))
N.append(ecard("warden", "w_pummel", "Pummel", "attack", 1, "common",
               [("dmg", "dmg", "hits")], dmg=4, hits=3, up={"dmg": 1}))
N.append(ecard("warden", "w_brace", "Brace", "skill", 1, "common",
               [("block", "block"), ("str", "magic")], block=5, magic=1,
               target="none", up={"block": 3}))
N.append(ecard("warden", "w_stance", "Defensive Stance", "skill", 1, "common",
               [("block", "block")], block=11, target="none",
               up={"block": 4}))
N.append(ecard("warden", "w_blood_price", "Blood Price", "skill", 0,
               "common", [("lose_hp", "hp_loss"), ("energy", "magic")],
               hp_loss=4, magic=2, target="none", up={"hp_loss": -1}))
N.append(ecard("warden", "w_warcry", "Warcry", "skill", 1, "common",
               [("str", "magic")], magic=2, target="none", up={"magic": 1}))
N.append(ecard("warden", "w_battle_focus", "Battle Focus", "skill", 1,
               "common", [("draw", "magic"), ("lose_hp", "hp_loss")],
               magic=2, hp_loss=3, target="none", up={"magic": 1}))
N.append(ecard("warden", "w_sweep", "Sweeping Blow", "attack", 1, "common",
               [("all", "dmg")], dmg=6, target="all", up={"dmg": 2}))
N.append(ecard("warden", "w_iron_will", "Iron Will", "skill", 2, "uncommon",
               [("block", "block"), ("str", "magic")], block=14, magic=2,
               target="none", up={"block": 5}))
N.append(ecard("warden", "w_bloodbath", "Bloodbath", "attack", 2, "uncommon",
               [("all", "dmg"), ("heal", "magic")], dmg=9, magic=3,
               target="all", up={"dmg": 3, "magic": 2}))
N.append(ecard("warden", "w_execute", "Execute", "attack", 2, "uncommon",
               [("dmg", "dmg")], dmg=20, exhaust=True, up={"dmg": 6}))
N.append(ecard("warden", "w_last_stand", "Last Stand", "skill", 2, "uncommon",
               [("block", "block"), ("str", "magic")], block=12, magic=2,
               target="none", up={"block": 4, "magic": 1}))
N.append(ecard("warden", "w_roar", "Berserker's Roar", "skill", 1, "uncommon",
               [("str", "magic"), ("self_vuln", "magic2")], magic=3,
               magic2=2, target="none", up={"magic": 1}))
N.append(ecard("warden", "w_trample", "Trample", "attack", 3, "uncommon",
               [("dmg", "dmg")], dmg=24, up={"dmg": 8}))
N.append(ecard("warden", "w_quake", "Earthshaker", "attack", 2, "uncommon",
               [("all", "dmg"), ("vuln_all", "magic")], dmg=8, magic=1,
               target="all", up={"dmg": 3, "magic": 1}))
N.append(ecard("warden", "w_undying", "Undying", "skill", 2, "uncommon",
               [("heal", "magic"), ("block", "block")], magic=10, block=8,
               target="none", exhaust=True, up={"magic": 4, "block": 3}))
N.append(ecard("warden", "w_warlord", "Warlord", "power", 2, "uncommon",
               [("str", "magic"), ("dex", "magic2")], magic=2, magic2=2,
               target="none", up={"magic": 1}))
N.append(ecard("warden", "w_iron_hide", "Iron Hide", "power", 1, "uncommon",
               [("metallicize", "magic")], magic=4, target="none",
               up={"magic": 1}))
N.append(ecard("warden", "w_thorn_plate", "Thorned Plate", "power", 1,
               "uncommon", [("thorns", "magic")], magic=4, target="none",
               up={"magic": 2}))
N.append(ecard("warden", "w_titans_grip", "Titan's Grip", "skill", 2, "rare",
               [("double_str",)], target="none", exhaust=True,
               up={"cost": -1}))
N.append(ecard("warden", "w_annihilate", "Annihilate", "attack", 3, "rare",
               [("dmg", "dmg")], dmg=34, up={"dmg": 10}))
N.append(ecard("warden", "w_blood_tide", "Blood Tide", "attack", 2, "rare",
               [("all", "dmg"), ("heal", "magic")], dmg=12, magic=5,
               target="all", up={"dmg": 4, "magic": 3}))
N.append(ecard("warden", "w_immortal", "Immortal", "power", 2, "rare",
               [("regen", "magic")], magic=6, target="none",
               up={"magic": 2}))
N.append(ecard("warden", "w_unbroken", "Unbroken", "power", 2, "rare",
               [("metallicize", "magic")], magic=8, target="none",
               up={"magic": 2}))
N.append(ecard("warden", "w_ruin", "Ruin", "attack", 2, "rare",
               [("dmg", "dmg"), ("vuln", "magic")], dmg=22, magic=2,
               up={"dmg": 6, "magic": 1}))

# ----------------------------------------------------------- Ashblade ------

N = []
N.append(ecard("ashblade", "a_slice", "Slice", "attack", 1, "common",
               [("dmg", "dmg"), ("draw_if_poisoned", "magic")], dmg=6,
               magic=1, up={"dmg": 3}))
N.append(ecard("ashblade", "a_sucker_punch", "Sucker Punch", "attack", 1,
               "common", [("dmg", "dmg"), ("weak", "magic")], dmg=6, magic=1,
               up={"dmg": 2, "magic": 1}))
N.append(ecard("ashblade", "a_poison_dart", "Poison Dart", "attack", 1,
               "common", [("dmg", "dmg"), ("poison", "magic")], dmg=4,
               magic=2, up={"dmg": 1, "magic": 1}))
N.append(ecard("ashblade", "a_nightshade", "Nightshade", "skill", 0, "common",
               [("poison", "magic")], magic=2, exhaust=True, up={"magic": 2}))
N.append(ecard("ashblade", "a_shiv_throw", "Shiv Throw", "attack", 1,
               "common", [("dmg", "dmg"), ("add_shiv", "magic")], dmg=4,
               magic=1, up={"dmg": 2, "magic": 1}))
N.append(ecard("ashblade", "a_dagger_spray", "Dagger Spray", "attack", 1,
               "common", [("all", "dmg")], dmg=5, target="all",
               up={"dmg": 2}))
N.append(ecard("ashblade", "a_prepare", "Prepare", "skill", 1, "common",
               [("draw", "magic")], magic=2, target="none", up={"magic": 1}))
N.append(ecard("ashblade", "a_dodge_roll", "Dodge Roll", "skill", 1, "common",
               [("block", "block"), ("draw", "magic")], block=7, magic=1,
               target="none", up={"block": 3}))
N.append(ecard("ashblade", "a_smoke_bomb", "Smoke Bomb", "skill", 1, "common",
               [("block", "block")], block=9, target="none", up={"block": 3}))
N.append(ecard("ashblade", "a_backstab", "Backstab", "attack", 0, "common",
               [("dmg", "dmg")], dmg=9, exhaust=True, up={"dmg": 3}))
N.append(ecard("ashblade", "a_venom_strike", "Venom Strike", "attack", 1,
               "common", [("dmg", "dmg"), ("poison", "magic")], dmg=6,
               magic=2, up={"dmg": 2, "magic": 1}))
N.append(ecard("ashblade", "a_blur_step", "Blur Step", "skill", 1, "common",
               [("block", "block"), ("dex", "magic")], block=6, magic=1,
               target="none", up={"block": 2}))
N.append(ecard("ashblade", "a_caltrops", "Caltrops", "skill", 1, "common",
               [("thorns_tmp", "magic")], magic=3, target="none",
               up={"magic": 2}))
N.append(ecard("ashblade", "a_pierce", "Pierce", "attack", 1, "common",
               [("dmg", "dmg"), ("vuln", "magic")], dmg=8, magic=1,
               up={"dmg": 2, "magic": 1}))
N.append(ecard("ashblade", "a_shadow_step", "Shadow Step", "skill", 1,
               "common", [("block", "block")], block=8, target="none",
               up={"block": 4}))
N.append(ecard("ashblade", "a_quick_hands", "Quick Hands", "skill", 0,
               "common", [("draw", "magic"), ("energy", "magic")], magic=1,
               target="none", exhaust=True, up={"magic": 1}))
N.append(ecard("ashblade", "a_twin_fang", "Twin Fang", "attack", 1, "common",
               [("dmg", "dmg", "hits")], dmg=4, hits=2, up={"dmg": 1}))
N.append(ecard("ashblade", "a_corpse_burst", "Corpse Burst", "attack", 2,
               "uncommon", [("dmg", "dmg"), ("poison", "magic")], dmg=10,
               magic=3, up={"dmg": 3, "magic": 2}))
N.append(ecard("ashblade", "a_toxic_cloud", "Toxic Cloud", "skill", 2,
               "uncommon", [("poison_all", "magic")], magic=4, target="all",
               up={"magic": 2}))
N.append(ecard("ashblade", "a_blade_flurry", "Blade Flurry", "attack", 1,
               "uncommon", [("dmg", "dmg", "hits")], dmg=4, hits=3,
               up={"dmg": 1}))
N.append(ecard("ashblade", "a_assassinate", "Assassinate", "attack", 2,
               "uncommon", [("dmg", "dmg")], dmg=18, up={"dmg": 6}))
N.append(ecard("ashblade", "a_poisoned_blade", "Poisoned Blade", "attack", 1,
               "uncommon", [("dmg", "dmg"), ("poison", "magic")], dmg=9,
               magic=3, up={"dmg": 3, "magic": 2}))
N.append(ecard("ashblade", "a_evasion", "Evasion", "skill", 1, "uncommon",
               [("block", "block"), ("draw", "magic")], block=10, magic=1,
               target="none", up={"block": 4}))
N.append(ecard("ashblade", "a_terror", "Terror", "skill", 1, "uncommon",
               [("vuln_all", "magic")], magic=2, target="all", exhaust=True,
               up={"magic": 1}))
N.append(ecard("ashblade", "a_deadly_gambit", "Deadly Gambit", "skill", 0,
               "uncommon", [("lose_hp", "hp_loss"), ("draw", "magic"),
                            ("energy", "magic2")], hp_loss=5, magic=3,
               magic2=1, target="none", up={"magic": 1}))
N.append(ecard("ashblade", "a_shadow_dance", "Shadow Dance", "skill", 1,
               "uncommon", [("add_shiv", "magic")], magic=3, target="none",
               up={"magic": 1}))
N.append(ecard("ashblade", "a_venom_fang", "Venom Fang", "attack", 2,
               "uncommon", [("dmg", "dmg"), ("poison", "magic")], dmg=11,
               magic=3, up={"dmg": 4, "magic": 2}))
N.append(ecard("ashblade", "a_smoke_screen", "Smoke Screen", "skill", 2,
               "uncommon", [("block", "block"), ("draw", "magic")], block=14,
               magic=1, target="none", up={"block": 5}))
N.append(ecard("ashblade", "a_night_terror", "Night Terror", "attack", 2,
               "uncommon", [("dmg", "dmg"), ("weak", "magic")], dmg=14,
               magic=2, up={"dmg": 4, "magic": 1}))
N.append(ecard("ashblade", "a_creeping_venom", "Creeping Venom", "skill", 1,
               "uncommon", [("poison_all", "magic")], magic=3, target="all",
               up={"magic": 1}))
N.append(ecard("ashblade", "a_blade_barrage", "Blade Barrage", "attack", 2,
               "uncommon", [("dmg", "dmg", "hits")], dmg=5, hits=4,
               up={"dmg": 1}))
N.append(ecard("ashblade", "a_corpse_explosion", "Corpse Explosion", "skill",
               2, "rare", [("poison_all", "magic")], magic=6, target="all",
               up={"magic": 2}))
N.append(ecard("ashblade", "a_grand_finale", "Grand Finale", "attack", 0,
               "rare", [("dmg", "dmg")], dmg=26, exhaust=True,
               up={"dmg": 10}))
N.append(ecard("ashblade", "a_abyss", "Abyss", "attack", 3, "rare",
               [("all", "dmg"), ("poison_all", "magic")], dmg=14, magic=3,
               target="all", up={"dmg": 4, "magic": 1}))
N.append(ecard("ashblade", "a_venom_ring", "Venom Ring", "power", 2, "rare",
               [("envenom", "magic")], magic=2, target="none",
               up={"cost": -1}))
N.append(ecard("ashblade", "a_shadow_master", "Shadow Master", "power", 2,
               "rare", [("dex", "magic")], magic=3, target="none",
               up={"magic": 1}))
N.append(ecard("ashblade", "a_death_mark", "Death Mark", "skill", 1, "rare",
               [("vuln_all", "magic")], magic=3, target="all", exhaust=True,
               up={"cost": -1}))
N.append(ecard("ashblade", "a_acid_rain", "Acid Rain", "attack", 2, "rare",
               [("all", "dmg"), ("poison_all", "magic")], dmg=10, magic=2,
               target="all", up={"dmg": 3, "magic": 1}))
N.append(ecard("ashblade", "a_nightfall", "Nightfall", "attack", 2, "rare",
               [("all", "dmg"), ("weak_all", "magic")], dmg=8, magic=2,
               target="all", up={"dmg": 3, "magic": 1}))
N.append(ecard("ashblade", "a_perfect_poison", "Perfect Poison", "skill", 1,
               "rare", [("poison", "magic")], magic=8, exhaust=True,
               up={"magic": 3}))

# -------------------------------------------------------- Emberwright ------

N = []
N.append(ecard("emberwright", "e_arc", "Arc", "attack", 1, "common",
               [("dmg", "dmg")], dmg=8, up={"dmg": 3}))
N.append(ecard("emberwright", "e_static", "Static", "attack", 0, "common",
               [("dmg", "dmg"), ("draw", "magic")], dmg=4, magic=1,
               exhaust=True, up={"dmg": 2}))
N.append(ecard("emberwright", "e_burnish", "Burnish", "attack", 1, "common",
               [("dmg", "dmg"), ("add_burn", "magic")], dmg=6, magic=1,
               up={"dmg": 2}))
N.append(ecard("emberwright", "e_steam_jet", "Steam Jet", "attack", 1,
               "common", [("dmg", "dmg"), ("block", "block")], dmg=7,
               block=3, up={"dmg": 2, "block": 2}))
N.append(ecard("emberwright", "e_coil", "Coil", "skill", 1, "common",
               [("block", "block")], block=8, target="none", up={"block": 3}))
N.append(ecard("emberwright", "e_circuit", "Circuit", "skill", 1, "common",
               [("draw", "magic"), ("lose_hp", "hp_loss")], magic=2,
               hp_loss=2, target="none", up={"magic": 1}))
N.append(ecard("emberwright", "e_battery", "Battery", "skill", 0, "common",
               [("energy", "magic")], magic=1, target="none", exhaust=True,
               up={"cost": 0}))
N.append(ecard("emberwright", "e_shield_gen", "Shield Generator", "skill", 1,
               "common", [("block", "block")], block=10, target="none",
               up={"block": 4}))
N.append(ecard("emberwright", "e_vent", "Vent", "skill", 1, "common",
               [("block", "block"), ("all", "magic")], block=6, magic=3,
               target="none", up={"block": 2, "magic": 1}))
N.append(ecard("emberwright", "e_charge", "Charge", "skill", 1, "common",
               [("energy", "magic"), ("draw", "magic2")], magic=1, magic2=1,
               target="none", exhaust=True, up={"cost": -1}))
N.append(ecard("emberwright", "e_hammer", "Hammer", "attack", 2, "common",
               [("dmg", "dmg")], dmg=14, up={"dmg": 5}))
N.append(ecard("emberwright", "e_insulate", "Insulate", "skill", 1, "common",
               [("block", "block"), ("metallicize", "magic")], block=7,
               magic=1, target="none", up={"block": 2}))
N.append(ecard("emberwright", "e_spanner", "Spanner", "attack", 1, "common",
               [("dmg", "dmg")], dmg=9, up={"dmg": 3}))
N.append(ecard("emberwright", "e_fuse", "Fuse", "skill", 1, "common",
               [("add_burn", "magic"), ("draw", "magic2")], magic=1, magic2=2,
               target="none", up={"magic2": 1}))
N.append(ecard("emberwright", "e_piston", "Piston", "attack", 1, "common",
               [("dmg", "dmg", "hits")], dmg=5, hits=2, up={"dmg": 2}))
N.append(ecard("emberwright", "e_boiler", "Boiler", "skill", 2, "common",
               [("block", "block"), ("str", "magic")], block=12, magic=1,
               target="none", up={"block": 4}))
N.append(ecard("emberwright", "e_overheat", "Overheat", "attack", 1,
               "uncommon", [("dmg", "dmg"), ("add_burn", "magic")], dmg=12,
               magic=1, up={"dmg": 4}))
N.append(ecard("emberwright", "e_turbine", "Turbine", "power", 1, "uncommon",
               [("metallicize", "magic")], magic=3, target="none",
               up={"magic": 1}))
N.append(ecard("emberwright", "e_reactor", "Reactor", "skill", 1, "uncommon",
               [("energy", "magic"), ("add_burn", "magic2")], magic=2,
               magic2=1, target="none", up={"magic": 1}))
N.append(ecard("emberwright", "e_magnet", "Magnet", "skill", 1, "uncommon",
               [("draw", "magic"), ("lose_hp", "hp_loss")], magic=3,
               hp_loss=3, target="none", up={"magic": 1}))
N.append(ecard("emberwright", "e_bulkhead", "Bulkhead", "skill", 2,
               "uncommon", [("block", "block")], block=18, target="none",
               up={"block": 6}))
N.append(ecard("emberwright", "e_arc_welder", "Arc Welder", "attack", 2,
               "uncommon", [("dmg", "dmg"), ("vuln", "magic")], dmg=16,
               magic=1, up={"dmg": 5, "magic": 1}))
N.append(ecard("emberwright", "e_coolant", "Coolant", "skill", 1, "uncommon",
               [("block", "block"), ("draw", "magic")], block=9, magic=1,
               target="none", up={"block": 4}))
N.append(ecard("emberwright", "e_steam_burst", "Steam Burst", "attack", 1,
               "uncommon", [("all", "dmg"), ("add_burn", "magic")], dmg=6,
               magic=1, target="all", up={"dmg": 2}))
N.append(ecard("emberwright", "e_gearworks", "Gearworks", "power", 1,
               "uncommon", [("str", "magic")], magic=2, target="none",
               up={"magic": 1}))
N.append(ecard("emberwright", "e_gyro", "Gyro", "power", 1, "uncommon",
               [("dex", "magic")], magic=2, target="none", up={"magic": 1}))
N.append(ecard("emberwright", "e_hammerfall", "Hammerfall", "attack", 2,
               "uncommon", [("dmg", "dmg")], dmg=18, up={"dmg": 6}))
N.append(ecard("emberwright", "e_inscription", "Inscription", "skill", 1,
               "uncommon", [("upgrade_hand",), ("draw", "magic")], magic=1,
               target="none", up={"magic": 1}))
N.append(ecard("emberwright", "e_bellows", "Bellows", "skill", 1, "uncommon",
               [("str", "magic"), ("self_vuln", "magic2")], magic=2,
               magic2=1, target="none", up={"magic": 1}))
N.append(ecard("emberwright", "e_core_tap", "Core Tap", "skill", 0,
               "uncommon", [("energy", "magic"), ("draw", "magic2"),
                            ("lose_hp", "hp_loss")], magic=1, magic2=1,
               hp_loss=3, target="none", up={"hp_loss": -1}))
N.append(ecard("emberwright", "e_singularity", "Singularity", "attack", 3,
               "rare", [("all", "dmg")], dmg=18, target="all",
               up={"dmg": 6}))
N.append(ecard("emberwright", "e_meltdown", "Meltdown", "attack", 2, "rare",
               [("dmg", "dmg"), ("add_burn", "magic")], dmg=24, magic=2,
               up={"dmg": 8}))
N.append(ecard("emberwright", "e_eternal", "Eternal", "power", 2, "rare",
               [("regen", "magic")], magic=8, target="none",
               up={"magic": 3}))
N.append(ecard("emberwright", "e_annihilator", "Annihilator", "attack", 2,
               "rare", [("dmg", "dmg"), ("vuln", "magic")], dmg=20, magic=2,
               up={"dmg": 6, "magic": 1}))
N.append(ecard("emberwright", "e_reactor_core", "Reactor Core", "power", 2,
               "rare", [("metallicize", "magic")], magic=10, target="none",
               up={"magic": 3}))
N.append(ecard("emberwright", "e_supernova", "Supernova", "attack", 2, "rare",
               [("all", "dmg"), ("vuln_all", "magic")], dmg=10, magic=2,
               target="all", up={"dmg": 3, "magic": 1}))
N.append(ecard("emberwright", "e_overdrive", "Overdrive", "skill", 1, "rare",
               [("energy", "magic"), ("draw", "magic2"),
                ("add_burn", "magic3")], magic=2, magic2=2, magic3=2,
               target="none", up={"magic": 1}))
N.append(ecard("emberwright", "e_forge", "Forge", "power", 1, "rare",
               [("str", "magic")], magic=3, target="none", up={"magic": 1}))

# ------------------------------------------------------------- Pilgrim -----

N = []
N.append(ecard("pilgrim", "p_bless", "Bless", "skill", 1, "common",
               [("heal", "magic")], magic=5, target="none", up={"magic": 2}))
N.append(ecard("pilgrim", "p_guardian", "Guardian", "skill", 1, "common",
               [("block", "block")], block=9, target="none", up={"block": 3}))
N.append(ecard("pilgrim", "p_lay_on_hands", "Lay on Hands", "skill", 1,
               "common", [("heal", "magic"), ("block", "block")], magic=4,
               block=4, target="none", up={"magic": 2, "block": 2}))
N.append(ecard("pilgrim", "p_chastise", "Chastise", "attack", 1, "common",
               [("dmg", "dmg"), ("weak", "magic")], dmg=9, magic=1,
               up={"dmg": 2, "magic": 1}))
N.append(ecard("pilgrim", "p_rosary", "Rosary", "skill", 1, "common",
               [("block", "block"), ("heal", "magic")], block=6, magic=2,
               target="none", up={"block": 2, "magic": 1}))
N.append(ecard("pilgrim", "p_hymn", "Hymn", "skill", 1, "common",
               [("heal", "magic"), ("draw", "magic2")], magic=3, magic2=1,
               target="none", up={"magic": 2}))
N.append(ecard("pilgrim", "p_shield_bash", "Shield Bash", "attack", 1,
               "common", [("dmg", "dmg"), ("block", "block")], dmg=7,
               block=3, up={"dmg": 2, "block": 2}))
N.append(ecard("pilgrim", "p_devotion", "Devotion", "skill", 1, "common",
               [("dex", "magic"), ("block", "block")], magic=1, block=5,
               target="none", up={"block": 3}))
N.append(ecard("pilgrim", "p_purify", "Purify", "skill", 1, "common",
               [("heal", "magic")], magic=6, target="none", exhaust=True,
               up={"magic": 3}))
N.append(ecard("pilgrim", "p_zealot", "Zealot", "attack", 1, "common",
               [("dmg", "dmg"), ("str", "magic")], dmg=10, magic=1,
               up={"dmg": 3}))
N.append(ecard("pilgrim", "p_sanctify", "Sanctify", "skill", 1, "common",
               [("block", "block"), ("heal", "magic")], block=7, magic=2,
               target="none", up={"block": 3}))
N.append(ecard("pilgrim", "p_mace", "Mace", "attack", 2, "common",
               [("dmg", "dmg"), ("heal", "magic")], dmg=15, magic=2,
               up={"dmg": 5}))
N.append(ecard("pilgrim", "p_shield_wall", "Shield Wall", "skill", 2,
               "common", [("block", "block")], block=14, target="none",
               up={"block": 5}))
N.append(ecard("pilgrim", "p_light", "Light", "skill", 0, "common",
               [("heal", "magic"), ("draw", "magic2")], magic=3, magic2=1,
               target="none", exhaust=True, up={"magic": 2}))
N.append(ecard("pilgrim", "p_penitent", "Penitent", "attack", 1, "common",
               [("dmg", "dmg"), ("lose_hp", "hp_loss")], dmg=6, hp_loss=2,
               up={"dmg": 2}))
N.append(ecard("pilgrim", "p_benediction", "Benediction", "power", 1,
               "uncommon", [("regen", "magic")], magic=4, target="none",
               up={"magic": 2}))
N.append(ecard("pilgrim", "p_holy_light", "Holy Light", "skill", 2,
               "uncommon", [("heal", "magic"), ("block", "block")], magic=10,
               block=8, target="none", up={"magic": 3, "block": 3}))
N.append(ecard("pilgrim", "p_retribution", "Retribution", "attack", 2,
               "uncommon", [("dmg", "dmg"), ("thorns_tmp", "magic")], dmg=12,
               magic=3, up={"dmg": 4}))
N.append(ecard("pilgrim", "p_choir", "Choir", "skill", 1, "uncommon",
               [("heal", "magic"), ("draw", "magic2")], magic=5, magic2=1,
               target="none", up={"magic": 2}))
N.append(ecard("pilgrim", "p_absolution", "Absolution", "skill", 2,
               "uncommon", [("heal", "magic")], magic=12, target="none",
               exhaust=True, up={"magic": 4}))
N.append(ecard("pilgrim", "p_zealotry", "Zealotry", "attack", 1, "uncommon",
               [("dmg", "dmg"), ("heal", "magic")], dmg=10, magic=1,
               up={"dmg": 4}))
N.append(ecard("pilgrim", "p_cathedral", "Cathedral", "power", 1, "uncommon",
               [("divine", "magic")], magic=4, target="none",
               up={"magic": 1}))
N.append(ecard("pilgrim", "p_judgement", "Judgement", "attack", 2,
               "uncommon", [("dmg", "dmg"), ("heal", "magic")], dmg=18,
               magic=3, up={"dmg": 6}))
N.append(ecard("pilgrim", "p_grace", "Grace", "skill", 1, "uncommon",
               [("block", "block"), ("heal", "magic")], block=8, magic=3,
               target="none", up={"block": 3, "magic": 2}))
N.append(ecard("pilgrim", "p_crusade", "Crusade", "attack", 2, "uncommon",
               [("all", "dmg"), ("heal", "magic")], dmg=9, magic=2,
               target="all", up={"dmg": 3}))
N.append(ecard("pilgrim", "p_penitence", "Penitence", "skill", 0,
               "uncommon", [("lose_hp", "hp_loss"), ("energy", "magic"),
                            ("draw", "magic2")], hp_loss=4, magic=2, magic2=1,
               target="none", up={"magic": 1}))
N.append(ecard("pilgrim", "p_shield_of_faith", "Shield of Faith", "power", 1,
               "uncommon", [("thorns", "magic")], magic=4, target="none",
               up={"magic": 2}))
N.append(ecard("pilgrim", "p_renewal", "Renewal", "power", 1, "uncommon",
               [("regen", "magic")], magic=5, target="none",
               up={"magic": 2}))
N.append(ecard("pilgrim", "p_litany", "Litany", "skill", 1, "uncommon",
               [("block", "block"), ("draw", "magic")], block=10, magic=1,
               target="none", up={"block": 4}))
N.append(ecard("pilgrim", "p_miracle", "Miracle", "skill", 2, "rare",
               [("heal", "magic")], magic=20, target="none", exhaust=True,
               up={"magic": 8}))
N.append(ecard("pilgrim", "p_ascension", "Ascension", "power", 2, "rare",
               [("str", "magic"), ("dex", "magic2")], magic=3, magic2=3,
               target="none", up={"magic": 1}))
N.append(ecard("pilgrim", "p_divine_judgement", "Divine Judgement", "attack",
               3, "rare", [("dmg", "dmg"), ("heal", "magic")], dmg=30,
               magic=5, up={"dmg": 8, "magic": 2}))
N.append(ecard("pilgrim", "p_eternal_light", "Eternal Light", "power", 2,
               "rare", [("regen", "magic")], magic=8, target="none",
               up={"magic": 3}))
N.append(ecard("pilgrim", "p_bastion", "Bastion", "power", 2, "rare",
               [("metallicize", "magic")], magic=10, target="none",
               up={"magic": 3}))
N.append(ecard("pilgrim", "p_sacrifice", "Sacrifice", "skill", 0, "rare",
               [("lose_hp", "hp_loss"), ("energy", "magic"),
                ("draw", "magic2")], hp_loss=6, magic=2, magic2=2,
               target="none", up={"hp_loss": -2}))
N.append(ecard("pilgrim", "p_radiance", "Radiance", "attack", 2, "rare",
               [("all", "dmg"), ("heal", "magic")], dmg=14, magic=3,
               target="all", up={"dmg": 4, "magic": 2}))
N.append(ecard("pilgrim", "p_covenant", "Covenant", "skill", 1, "rare",
               [("block", "block")], block=20, target="none", exhaust=True,
               up={"block": 8}))

# ------------------------------------------------- finalise the pools ------
ecard("ashblade", "a_shadow_blast", "Shadow Blast", "attack", 2, "uncommon",
      [("all", "dmg"), ("poison_all", "magic")], dmg=10, magic=2,
      target="all", up={"dmg": 3, "magic": 1})
CARDS["burn"]["cls"] = "emberwright"
CARDS.pop("strike", None)
CARDS.pop("defend", None)
CLASS_OF.pop("strike", None)
CLASS_OF.pop("defend", None)
STARTER_DECK = STARTERS["warden"]

POOL = {r: [c["id"] for c in CARDS.values() if c["rarity"] == r]
        for r in ("common", "uncommon", "rare")}

# ------------------------------------------------------- The Silver Hand ---
# Hearthstone-paladin energy: Divine Shield, Silver Hand Recruits, blessings.

CLASSES["paladin"] = dict(
    name="The Silver Hand", color="gold", starter="pal_reinforce",
    blurb="Divine shields, recruits and blessings.",
    detail="Absorb hits with Divine Shield and swarm with Recruits.")

STARTERS["paladin"] = (["pal_strike"] * 4 + ["pal_defend"] * 3
                       + ["pal_faith", "pal_aegis_blessing",
                          "pal_reinforce"])

_add(card("recruit", "Silver Hand Recruit", "attack", 0, "token",
          "Deal {d} damage.\nExhaust.", dmg=4, exhaust=True, cls="paladin",
          up={"dmg": 0},
          play=lambda cb: cb.atk(cb.target, cb.C["dmg"])))

N = []
# commons
N.append(ecard("paladin", "pal_blessing_of_might", "Blessing of Might",
               "skill", 1, "common", [("str", "magic")], magic=2,
               target="none", up={"magic": 1}))
N.append(ecard("paladin", "pal_hammer_of_wrath", "Hammer of Wrath", "attack",
               1, "common", [("dmg", "dmg")], dmg=9, up={"dmg": 3}))
N.append(ecard("paladin", "pal_light_justice", "Light's Justice", "attack", 1,
               "common", [("dmg", "dmg"), ("heal", "magic")], dmg=8, magic=1,
               up={"dmg": 2}))
N.append(ecard("paladin", "pal_reinforce", "Reinforce", "skill", 1, "common",
               [("add_recruit", "magic")], magic=2, target="none",
               up={"magic": 1}))
N.append(ecard("paladin", "pal_blessed_ground", "Blessed Ground", "skill", 1,
               "common", [("block", "block"), ("heal", "magic")], block=6,
               magic=2, target="none", up={"block": 2, "magic": 1}))
N.append(ecard("paladin", "pal_sacred_shield", "Sacred Shield", "skill", 1,
               "common", [("block", "block")], block=10, target="none",
               up={"block": 4}))
N.append(ecard("paladin", "pal_faith", "Faith", "skill", 0, "common",
               [("heal", "magic")], magic=2, target="none", exhaust=True,
               up={"magic": 1}))
N.append(ecard("paladin", "pal_verdict", "Verdict", "attack", 2, "common",
               [("dmg", "dmg"), ("block", "block")], dmg=12, block=2,
               up={"dmg": 4}))
N.append(ecard("paladin", "pal_seal_of_light", "Seal of Light", "attack", 1,
               "common", [("dmg", "dmg"), ("heal", "magic")], dmg=7, magic=3,
               up={"dmg": 2, "magic": 1}))
N.append(ecard("paladin", "pal_dawn", "Dawn", "attack", 2, "common",
               [("all", "dmg")], dmg=7, target="all", up={"dmg": 2}))
N.append(ecard("paladin", "pal_fervor", "Fervor", "attack", 1, "common",
               [("dmg", "dmg"), ("str", "magic")], dmg=8, magic=1,
               up={"dmg": 2}))
N.append(ecard("paladin", "pal_rally", "Rally", "skill", 1, "common",
               [("add_recruit", "magic"), ("draw", "magic2")], magic=1,
               magic2=1, target="none", up={"magic": 1}))
N.append(ecard("paladin", "pal_shield_slam", "Shield Slam", "attack", 1,
               "common", [("dmg", "dmg"), ("block", "block")], dmg=8,
               block=4, up={"dmg": 2, "block": 2}))
N.append(ecard("paladin", "pal_blessing_wisdom", "Blessing of Wisdom",
               "skill", 1, "common", [("draw", "magic")], magic=2,
               target="none", up={"magic": 1}))
N.append(ecard("paladin", "pal_muster", "Muster", "skill", 2, "common",
               [("add_recruit", "magic")], magic=3, target="none",
               up={"magic": 1}))
N.append(ecard("paladin", "pal_hallowed_ground", "Hallowed Ground", "attack",
               2, "common", [("all", "dmg")], dmg=9, target="all",
               up={"dmg": 3}))
N.append(ecard("paladin", "pal_radiant_light", "Radiant Light", "skill", 1,
               "common", [("heal", "magic")], magic=6, target="none",
               up={"magic": 3}))
N.append(ecard("paladin", "pal_touch_of_light", "Touch of Light", "skill", 1,
               "common", [("heal", "magic"), ("block", "block")], magic=4,
               block=4, target="none", up={"magic": 2, "block": 2}))
N.append(ecard("paladin", "pal_holy_strike", "Holy Strike", "attack", 1,
               "common", [("dmg", "dmg"), ("block", "block")], dmg=9,
               block=1, up={"dmg": 3}))
N.append(ecard("paladin", "pal_aegis_blessing", "Aegis Blessing", "skill", 1,
               "common", [("shield", "magic")], magic=1, target="none",
               up={"cost": 0}))
# uncommons
N.append(ecard("paladin", "pal_divine_favor", "Divine Favor", "skill", 1,
               "uncommon", [("draw", "magic")], magic=3, target="none",
               exhaust=True, up={"magic": 1}))
N.append(ecard("paladin", "pal_avenging_wrath", "Avenging Wrath", "attack", 3,
               "uncommon", [("random", "dmg", "hits")], dmg=3, hits=4,
               target="all", up={"dmg": 1}))
N.append(ecard("paladin", "pal_sword_of_justice", "Sword of Justice", "attack",
               2, "uncommon", [("dmg", "dmg"), ("str", "magic")], dmg=12,
               magic=1, up={"dmg": 4}))
N.append(ecard("paladin", "pal_blessing_of_kings", "Blessing of Kings",
               "skill", 2, "uncommon", [("str", "magic"), ("dex", "magic2")],
               magic=3, magic2=3, target="none", up={"magic": 1}))
N.append(ecard("paladin", "pal_holy_shield", "Holy Shield", "skill", 2,
               "uncommon", [("shield", "magic"), ("block", "block")],
               magic=1, block=8, target="none", up={"block": 4}))
N.append(ecard("paladin", "pal_guardian_of_kings", "Guardian of Kings",
               "skill", 3, "uncommon", [("heal", "magic"),
                                        ("block", "block")], magic=8,
               block=8, target="none", up={"magic": 4, "block": 3}))
N.append(ecard("paladin", "pal_recruiter", "Recruiter", "skill", 1,
               "uncommon", [("add_recruit", "magic"), ("str", "magic2")],
               magic=2, magic2=1, target="none", up={"magic": 1}))
N.append(ecard("paladin", "pal_aura_of_light", "Aura of Light", "power", 2,
               "uncommon", [("aura", "magic")], magic=1, target="none",
               up={"magic": 1}))
N.append(ecard("paladin", "pal_devotion_aura", "Devotion Aura", "power", 1,
               "uncommon", [("divine", "magic")], magic=3, target="none",
               up={"magic": 1}))
N.append(ecard("paladin", "pal_retribution_aura", "Retribution Aura", "power",
               1, "uncommon", [("thorns", "magic")], magic=4, target="none",
               up={"magic": 2}))
N.append(ecard("paladin", "pal_seal_of_power", "Seal of Power", "skill", 1,
               "uncommon", [("str", "magic"), ("draw", "magic2")], magic=2,
               magic2=1, target="none", up={"magic": 1}))
N.append(ecard("paladin", "pal_holy_wrath", "Holy Wrath", "attack", 2,
               "uncommon", [("dmg", "dmg")], dmg=18, up={"dmg": 6}))
N.append(ecard("paladin", "pal_tirion_judgment", "Tirion's Judgment",
               "attack", 3, "uncommon", [("dmg", "dmg"), ("heal", "magic")],
               dmg=22, magic=5, up={"dmg": 7, "magic": 3}))
N.append(ecard("paladin", "pal_blessed_champion", "Blessed Champion", "attack",
               2, "uncommon", [("dmg", "dmg"), ("block", "block")], dmg=8,
               block=8, up={"dmg": 3, "block": 3}))
N.append(ecard("paladin", "pal_equality", "Equality", "skill", 2, "uncommon",
               [("strip_block",), ("vuln_all", "magic")], magic=2,
               target="all", up={"magic": 1}))
N.append(ecard("paladin", "pal_shield_righteous", "Shield of the Righteous",
               "attack", 2, "uncommon", [("dmg", "dmg"), ("shield", "magic")],
               dmg=10, magic=1, up={"dmg": 4}))
N.append(ecard("paladin", "pal_hammer_justice", "Hammer of Justice", "attack",
               2, "uncommon", [("dmg", "dmg"), ("weak", "magic")], dmg=10,
               magic=1, up={"dmg": 4}))
N.append(ecard("paladin", "pal_blessing_sanctuary", "Blessing of Sanctuary",
               "skill", 1, "uncommon", [("shield", "magic")], magic=1,
               target="none", exhaust=True, up={"cost": 0}))
N.append(ecard("paladin", "pal_avenger", "Avenger", "attack", 1, "uncommon",
               [("dmg", "dmg"), ("add_recruit", "magic")], dmg=6, magic=1,
               up={"dmg": 3}))
N.append(ecard("paladin", "pal_holy_shock", "Holy Shock", "attack", 1,
               "uncommon", [("dmg", "dmg"), ("heal", "magic")], dmg=7,
               magic=3, up={"dmg": 3}))
N.append(ecard("paladin", "pal_lights_hammer", "Light's Hammer", "attack", 2,
               "uncommon", [("all", "dmg"), ("heal", "magic")], dmg=7,
               magic=2, target="all", up={"dmg": 3}))
N.append(ecard("paladin", "pal_protector", "Protector", "power", 1,
               "uncommon", [("divine", "magic")], magic=4, target="none",
               up={"magic": 1}))
# rares
N.append(ecard("paladin", "pal_divine_shield", "Divine Shield", "skill", 2,
               "rare", [("shield", "magic")], magic=2, target="none",
               up={"cost": -1}))
N.append(ecard("paladin", "pal_tyrs_fall", "Tyr's Fall", "attack", 3, "rare",
               [("dmg", "dmg")], dmg=28, up={"dmg": 9}))
N.append(ecard("paladin", "pal_silver_hand_army", "Silver Hand Army", "skill",
               3, "rare", [("add_recruit", "magic")], magic=5, target="none",
               exhaust=True, up={"magic": 2}))
N.append(ecard("paladin", "pal_lightbringer", "Lightbringer", "power", 2,
               "rare", [("lightbringer", "magic")], magic=1, target="none",
               up={"cost": -1}))
N.append(ecard("paladin", "pal_aura_mastery", "Aura Mastery", "power", 2,
               "rare", [("aura", "magic")], magic=2, target="none",
               up={"magic": 1}))
N.append(ecard("paladin", "pal_divine_intervention", "Divine Intervention",
               "skill", 2, "rare", [("heal", "magic")], magic=15,
               target="none", exhaust=True, up={"magic": 5}))
N.append(ecard("paladin", "pal_judgment_day", "Judgment Day", "attack", 3,
               "rare", [("all", "dmg"), ("vuln_all", "magic")], dmg=15,
               magic=2, target="all", up={"dmg": 4, "magic": 1}))
N.append(ecard("paladin", "pal_highlord", "Highlord", "power", 2, "rare",
               [("str", "magic"), ("dex", "magic2")], magic=3, magic2=2,
               target="none", up={"magic": 1}))
N.append(ecard("paladin", "pal_sanctified_armor", "Sanctified Armor", "power",
               1, "rare", [("divine", "magic")], magic=5, target="none",
               up={"magic": 2}))
N.append(ecard("paladin", "pal_hammer_righteous", "Hammer of the Righteous",
               "attack", 3, "rare", [("dmg", "dmg"), ("shield", "magic")],
               dmg=18, magic=1, up={"dmg": 6}))
N.append(ecard("paladin", "pal_redemption", "Redemption", "skill", 2, "rare",
               [("heal", "magic"), ("shield", "magic2")], magic=10,
               magic2=1, target="none", up={"magic": 4}))
N.append(ecard("paladin", "pal_eternal_dawn", "Eternal Dawn", "power", 2,
               "rare", [("regen", "magic")], magic=8, target="none",
               up={"magic": 3}))
N.append(ecard("paladin", "pal_avenging_angel", "Avenging Angel", "attack", 2,
               "rare", [("dmg", "dmg"), ("add_recruit", "magic")], dmg=12,
               magic=2, up={"dmg": 4}))
N.append(ecard("paladin", "pal_blessing_ancient_kings",
               "Blessing of Ancient Kings", "skill", 3, "rare",
               [("str", "magic"), ("dex", "magic2")], magic=4, magic2=4,
               target="none", up={"magic": 1}))
N.append(ecard("paladin", "pal_the_light", "The Light", "power", 3, "rare",
               [("regen", "magic"), ("divine", "magic2")], magic=5, magic2=3,
               target="none", up={"magic": 2}))
N.append(ecard("paladin", "pal_final_judgment", "Final Judgment", "attack", 3,
               "rare", [("dmg", "dmg"), ("heal", "magic")], dmg=26, magic=8,
               up={"dmg": 8, "magic": 3}))

POOL = {r: [c["id"] for c in CARDS.values() if c["rarity"] == r]
        for r in ("common", "uncommon", "rare")}
