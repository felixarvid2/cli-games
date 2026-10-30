"""Board-mode content for CINDERSPIRE: minions, spells, enemy decks.

Cards are data. Battlecries, deathrattles and spells are lists of ops that
the board engine interprets:

    ("dmg_hero", n)        damage the enemy hero
    ("dmg_random", n)      damage a random enemy minion (hero if none)
    ("aoe", n)             damage all enemy minions
    ("heal", n)            heal your hero
    ("heal_all", n)        heal all your minions
    ("draw", n)
    ("summon", cid, n)
    ("buff_self", atk, hp)
    ("buff_board", atk, hp)
    ("mana", n)
    ("dmg_target", n)      spells only: selected target
    ("destroy_target")     spells only
    ("buff_target", a, h)  spells only (friendly minion)
    ("give_kw", kw)        spells only (friendly minion)
"""

BOARD_CARDS = {}


def mn(cid, name, cls, cost, atk, hp, kw=(), text="", bc=None, dr=None,
       token=False):
    BOARD_CARDS[cid] = dict(
        id=cid, name=name, cls=cls, cost=cost, atk=atk, hp=hp,
        kw=set(kw), text=text, bc=bc, dr=dr, kind="minion", token=token)


def sp(cid, name, cls, cost, text, effects):
    BOARD_CARDS[cid] = dict(id=cid, name=name, cls=cls, cost=cost, atk=0, hp=0,
                            kw=set(), text=text, bc=None, dr=None,
                            kind="spell", effects=list(effects), token=False)


# ------------------------------------------------------------------ tokens --
mn("recruit", "Recruit", "paladin", 1, 1, 1, token=True)
mn("shiv", "Shiv", "ashblade", 1, 1, 1, ("charge",), token=True)
mn("soldier", "Soldier", "warden", 2, 2, 2, token=True)
mn("squire_t", "Squire", "paladin", 1, 1, 2, ("divine_shield",), token=True)
mn("spark_t", "Spark", "emberwright", 1, 1, 1, token=True)
mn("guard_t", "Guard", "pilgrim", 2, 0, 3, ("taunt",), token=True)
mn("wolf", "Wolf", "neutral", 2, 2, 1, ("charge",), token=True)
mn("whelp", "Whelp", "neutral", 1, 1, 2, token=True)
mn("golem_t", "Golem", "neutral", 3, 3, 3, token=True)
mn("spirit", "Spirit", "neutral", 2, 2, 1, token=True)

# ------------------------------------------------------------------ Warden --
mn("w_ashguard", "Ashguard", "warden", 1, 1, 3, ("taunt",))
mn("w_cleaver", "Cleaver", "warden", 1, 3, 1)
mn("w_shieldbearer", "Shieldbearer", "warden", 2, 2, 4, ("taunt",))
mn("w_brute", "Brute", "warden", 2, 4, 3)
mn("w_veteran", "Veteran", "warden", 2, 3, 2, bc=[("buff_board", 1, 0)])
mn("w_ironclad", "Ironclad", "warden", 3, 3, 6, ("taunt",))
mn("w_berserker", "Berserker", "warden", 3, 5, 3)
mn("w_shieldmaiden", "Shieldmaiden", "warden", 3, 3, 5, ("divine_shield",))
mn("w_executioner", "Executioner", "warden", 3, 6, 2, bc=[("dmg_hero", 2)])
mn("w_warlord", "Warlord", "warden", 4, 6, 5)
mn("w_wall", "The Wall", "warden", 4, 2, 8, ("taunt",))
mn("w_champion", "Champion", "warden", 4, 5, 4, bc=[("buff_board", 1, 1)])
mn("w_juggernaut", "Juggernaut", "warden", 5, 8, 6)
mn("w_colossus", "Colossus", "warden", 6, 9, 9)
mn("w_taskmaster", "Taskmaster", "warden", 1, 2, 1, bc=[("buff_self", 1, 1)])
mn("w_bloodrager", "Bloodrager", "warden", 3, 4, 3, ("charge",))
sp("w_cleave", "Cleave", "warden", 2, "Deal 2 damage to all enemy minions.",
   [("aoe", 2)])
sp("w_execute", "Execute", "warden", 3, "Deal 5 damage to a minion.",
   [("dmg_target", 5)])
sp("w_rally", "Rally", "warden", 3, "Summon two 2/2 Soldiers.",
   [("summon", "soldier", 2)])
sp("w_warcry", "Warcry", "warden", 1, "Give your minions +1/+1.",
   [("buff_board", 1, 1)])

# ---------------------------------------------------------------- Ashblade --
mn("a_dagger", "Dagger", "ashblade", 1, 2, 1, ("charge",))
mn("a_cutthroat", "Cutthroat", "ashblade", 1, 2, 1)
mn("a_poisoner", "Poisoner", "ashblade", 2, 1, 3, ("poisonous",))
mn("a_shivdancer", "Shiv Dancer", "ashblade", 2, 2, 1,
   bc=[("summon", "shiv", 1)])
mn("a_blademaster", "Blademaster", "ashblade", 3, 4, 3)
mn("a_assassin", "Assassin", "ashblade", 4, 5, 2, ("poisonous",))
mn("a_venomtail", "Venomtail", "ashblade", 3, 2, 4, ("poisonous",))
mn("a_nightblade", "Nightblade", "ashblade", 4, 6, 4)
mn("a_rogue", "Rogue", "ashblade", 2, 3, 2, bc=[("draw", 1)])
mn("a_shadowblade", "Shadowblade", "ashblade", 3, 3, 3, ("charge",))
mn("a_cutpurse", "Cutpurse", "ashblade", 2, 2, 3, bc=[("mana", 1)])
mn("a_shivmaster", "Shivmaster", "ashblade", 3, 3, 3,
   bc=[("summon", "shiv", 2)])
mn("a_venom", "Venom", "ashblade", 4, 4, 4, ("poisonous",))
mn("a_daggermaster", "Daggermaster", "ashblade", 5, 6, 5)
mn("a_trickster", "Trickster", "ashblade", 2, 1, 3, bc=[("draw", 1)])
mn("a_nightmare", "Nightmare", "ashblade", 6, 7, 6)
sp("a_backstab", "Backstab", "ashblade", 1, "Deal 2 damage to a minion.",
   [("dmg_target", 2)])
sp("a_fan", "Fan of Knives", "ashblade", 2,
   "Deal 1 damage to all enemy minions. Draw a card.",
   [("aoe", 1), ("draw", 1)])
sp("a_assassinate", "Assassinate", "ashblade", 4,
   "Destroy a minion.", [("destroy_target",)])
sp("a_poisoncloud", "Poison Cloud", "ashblade", 3,
   "Deal 2 damage to all enemy minions.", [("aoe", 2)])

# ------------------------------------------------------------- Emberwright --
mn("e_sparkbot", "Sparkbot", "emberwright", 1, 1, 2, bc=[("dmg_hero", 1)])
mn("e_furnace", "Furnace", "emberwright", 2, 2, 3)
mn("e_steambot", "Steambot", "emberwright", 3, 3, 4)
mn("e_boiler", "Boiler", "emberwright", 2, 1, 4, ("taunt",))
mn("e_arcanist", "Arcanist", "emberwright", 3, 3, 3, bc=[("draw", 1)])
mn("e_golem", "Golem", "emberwright", 4, 5, 4)
mn("e_turret", "Turret", "emberwright", 2, 2, 2, bc=[("dmg_random", 1)])
mn("e_colossus", "Colossus", "emberwright", 6, 7, 7)
mn("e_cinder", "Cinder", "emberwright", 1, 1, 1, bc=[("dmg_random", 2)])
mn("e_mage", "Mage", "emberwright", 3, 2, 4, bc=[("aoe", 1)])
mn("e_sentinel", "Sentinel", "emberwright", 4, 3, 6, ("taunt",))
mn("e_forge", "Forge", "emberwright", 5, 6, 6)
mn("e_pyromancer", "Pyromancer", "emberwright", 2, 2, 2, bc=[("dmg_hero", 2)])
mn("e_dynamo", "Dynamo", "emberwright", 3, 2, 3, bc=[("mana", 2)])
mn("e_overload", "Overload", "emberwright", 4, 5, 5)
mn("e_ward", "Ward", "emberwright", 1, 0, 3, ("taunt",))
sp("e_fireball", "Fireball", "emberwright", 4, "Deal 6 damage.",
   [("dmg_target", 6)])
sp("e_flamewave", "Flame Wave", "emberwright", 3,
   "Deal 2 damage to all enemy minions.", [("aoe", 2)])
sp("e_overclock", "Overclock", "emberwright", 1, "Draw 2 cards.",
   [("draw", 2)])
sp("e_burn", "Burn", "emberwright", 2, "Deal 4 damage to the enemy hero.",
   [("dmg_hero", 4)])

# ----------------------------------------------------------------- Pilgrim --
mn("p_acolyte", "Acolyte", "pilgrim", 1, 1, 2, bc=[("heal", 2)])
mn("p_cleric", "Cleric", "pilgrim", 2, 1, 4, bc=[("heal", 3)])
mn("p_shieldbearer", "Shieldbearer", "pilgrim", 2, 2, 3, ("divine_shield",))
mn("p_templar", "Templar", "pilgrim", 3, 3, 4)
mn("p_monk", "Monk", "pilgrim", 2, 2, 2, ("divine_shield",))
mn("p_guardian", "Guardian", "pilgrim", 3, 2, 6, ("taunt",))
mn("p_healer", "Healer", "pilgrim", 3, 2, 3, bc=[("heal_all", 2)])
mn("p_zealot", "Zealot", "pilgrim", 3, 4, 2)
mn("p_lightbringer", "Lightbringer", "pilgrim", 4, 4, 5, ("divine_shield",))
mn("p_sanctuary", "Sanctuary", "pilgrim", 4, 3, 7, ("taunt",))
mn("p_priest", "Priest", "pilgrim", 2, 1, 3, bc=[("heal", 4)])
mn("p_crusader", "Crusader", "pilgrim", 3, 4, 3, ("divine_shield",))
mn("p_ascendant", "Ascendant", "pilgrim", 5, 5, 6)
mn("p_martyr", "Martyr", "pilgrim", 1, 2, 1, dr=[("heal", 3)])
mn("p_beacon", "Beacon", "pilgrim", 2, 1, 2, bc=[("buff_board", 0, 1)])
mn("p_dawn", "Dawn", "pilgrim", 5, 4, 8, ("taunt",))
sp("p_prayer", "Prayer", "pilgrim", 1, "Restore 4 health.", [("heal", 4)])
sp("p_sanctuary_s", "Sanctuary", "pilgrim", 3, "Restore 8 health.",
   [("heal", 8)])
sp("p_blessing", "Blessing", "pilgrim", 2,
   "Give a friendly minion +1/+2.", [("buff_target", 1, 2)])
sp("p_divinelight", "Divine Light", "pilgrim", 4,
   "Restore 4 health to your minions. Draw a card.",
   [("heal_all", 4), ("draw", 1)])

# ------------------------------------------------------------- Silver Hand --
mn("sh_squire", "Squire", "paladin", 1, 1, 2, ("divine_shield",))
mn("sh_minibot", "Shielded Minibot", "paladin", 2, 2, 2,
   ("divine_shield",))
mn("sh_recruiter", "Recruiter", "paladin", 2, 2, 2,
   bc=[("summon", "recruit", 1)])
mn("sh_knight", "Knight", "paladin", 3, 3, 4, ("divine_shield",))
mn("sh_guardian", "Guardian of Kings", "paladin", 4, 4, 5,
   bc=[("heal", 4)])
mn("sh_shknight", "Silver Hand Knight", "paladin", 4, 4, 4,
   bc=[("summon", "squire_t", 1)])
mn("sh_lightwarden", "Lightwarden", "paladin", 2, 2, 3, ("taunt",))
mn("sh_argent", "Argent", "paladin", 3, 3, 3, ("divine_shield",))
mn("sh_crusader", "Crusader", "paladin", 4, 4, 4, ("taunt",))
mn("sh_highlord", "Highlord", "paladin", 5, 6, 6, ("divine_shield",))
mn("sh_sergeant", "Sergeant", "paladin", 1, 2, 1)
mn("sh_blessing", "Blessing", "paladin", 2, 1, 3, bc=[("buff_board", 1, 0)])
mn("sh_warden", "Warden", "paladin", 3, 2, 6, ("taunt",))
mn("sh_champion", "Champion", "paladin", 5, 5, 5,
   bc=[("summon", "recruit", 2)])
mn("sh_light", "The Light", "paladin", 6, 7, 7)
mn("sh_captain", "Recruit Captain", "paladin", 3, 3, 3,
   bc=[("summon", "recruit", 1)])
sp("sh_reinforce", "Reinforce", "paladin", 2,
   "Summon two 1/1 Recruits.", [("summon", "recruit", 2)])
sp("sh_consecration", "Consecration", "paladin", 4,
   "Deal 2 damage to all enemy minions.", [("aoe", 2)])
sp("sh_kings", "Blessing of Kings", "paladin", 3,
   "Give a friendly minion +2/+2.", [("buff_target", 2, 2)])
sp("sh_favor", "Divine Favor", "paladin", 1, "Draw 2 cards.",
   [("draw", 2)])

# --------------------------------------------------------- neutral enemies --
mn("n_louse", "Louse", "neutral", 1, 1, 1)
mn("n_bandit", "Bandit", "neutral", 2, 2, 2)
mn("n_cultist", "Cultist", "neutral", 2, 1, 2, bc=[("dmg_hero", 1)])
mn("n_brute", "Brute", "neutral", 3, 3, 3)
mn("n_shade", "Shade", "neutral", 2, 2, 1, ("charge",))
mn("n_sentinel", "Sentinel", "neutral", 3, 0, 4, ("taunt",))
mn("n_horror", "Horror", "neutral", 4, 4, 4)
mn("n_king", "King's Guard", "neutral", 6, 6, 6)
mn("n_wisp", "Wisp", "neutral", 0, 1, 1)
mn("n_spider", "Spider", "neutral", 1, 1, 1, ("poisonous",))
mn("n_shield", "Shielded Guard", "neutral", 3, 2, 5, ("divine_shield",))

# Starter decks (10 cards each, duplicates allowed).
STARTER_DECKS = {
    "warden": ["w_ashguard", "w_cleaver", "w_cleaver", "w_shieldbearer",
               "w_brute", "w_veteran", "w_ironclad", "w_berserker",
               "w_cleave", "w_rally"],
    "ashblade": ["a_dagger", "a_cutthroat", "a_cutthroat", "a_poisoner",
                 "a_shivdancer", "a_blademaster", "a_rogue", "a_shadowblade",
                 "a_backstab", "a_fan"],
    "emberwright": ["e_sparkbot", "e_furnace", "e_furnace", "e_boiler",
                    "e_turret", "e_arcanist", "e_mage", "e_steambot",
                    "e_fireball", "e_overclock"],
    "pilgrim": ["p_acolyte", "p_cleric", "p_shieldbearer", "p_monk",
                "p_templar", "p_guardian", "p_healer", "p_zealot",
                "p_prayer", "p_blessing"],
    "paladin": ["sh_squire", "sh_minibot", "sh_recruiter", "sh_lightwarden",
                   "sh_knight", "sh_argent", "sh_sergeant", "sh_blessing",
                   "sh_reinforce", "sh_consecration"],
}

# Reward pool: class cards, no tokens.
POOL = {}
for _cid, _c in BOARD_CARDS.items():
    if not _c["token"]:
        POOL.setdefault(_c["cls"], []).append(_cid)

# Enemy heroes: name, HP, and a deck of 12 ids.
ENEMY_HEROES = [
    dict(name="Louse Swarm", hp=26, deck=["n_louse"] * 6 + ["n_wisp"] * 4
         + ["n_spider"] * 2, act=0),
    dict(name="Jaw Worm", hp=32, deck=["n_louse"] * 4 + ["n_bandit"] * 4
         + ["n_brute"] * 2 + ["n_sentinel"] * 2, act=0),
    dict(name="Cultist", hp=32, deck=["n_cultist"] * 4 + ["n_wisp"] * 4
         + ["n_bandit"] * 2 + ["n_shade"] * 2, act=0),
    dict(name="Acid Slime", hp=28, deck=["n_wisp"] * 6 + ["n_spider"] * 4
         + ["n_bandit"] * 2, act=0),
    dict(name="Chosen", hp=44, deck=["n_cultist"] * 4 + ["n_brute"] * 4
         + ["n_horror"] * 2 + ["n_shield"] * 2, act=1),
    dict(name="Shelled Parasite", hp=48, deck=["n_bandit"] * 4
         + ["n_sentinel"] * 3 + ["n_brute"] * 3 + ["n_horror"] * 2, act=1),
    dict(name="Sentry", hp=42, deck=["n_sentinel"] * 4 + ["n_shield"] * 4
         + ["n_brute"] * 2 + ["n_horror"] * 2, act=1),
    dict(name="Wraith", hp=40, deck=["n_shade"] * 5 + ["n_cultist"] * 4
         + ["n_spider"] * 3, act=1),
    dict(name="Ash Revenant", hp=54, deck=["n_brute"] * 4 + ["n_horror"] * 4
         + ["n_shade"] * 2 + ["n_king"] * 2, act=2),
    dict(name="Acolyte", hp=50, deck=["n_cultist"] * 5 + ["n_shield"] * 3
         + ["n_horror"] * 2 + ["n_king"] * 2, act=2),
    dict(name="Cinder Hound", hp=52, deck=["n_shade"] * 4 + ["n_brute"] * 4
         + ["n_horror"] * 2 + ["n_king"] * 2, act=2),
    dict(name="Gremlin Nob", hp=54, deck=["n_brute"] * 5 + ["n_bandit"] * 3
         + ["n_shield"] * 2 + ["n_king"] * 2, act=-1, elite=True),
    dict(name="Mugger", hp=50, deck=["n_shade"] * 4 + ["n_bandit"] * 4
         + ["n_horror"] * 2 + ["n_spider"] * 2, act=-1, elite=True),
    dict(name="Book of Stabbing", hp=62, deck=["n_shield"] * 4
         + ["n_horror"] * 4 + ["n_king"] * 2 + ["n_brute"] * 2,
         act=-1, elite=True),
    dict(name="Molten Colossus", hp=72, deck=["n_shield"] * 3
         + ["n_horror"] * 4 + ["n_king"] * 3 + ["n_brute"] * 2,
         act=-1, elite=True),
    dict(name="The Ash Warden", hp=64, deck=["n_shield"] * 4
         + ["n_brute"] * 4 + ["n_horror"] * 3 + ["n_king"] * 1, act=-1,
         boss=True),
    dict(name="The Hollow Choir", hp=74, deck=["n_cultist"] * 4
         + ["n_horror"] * 4 + ["n_shade"] * 2 + ["n_king"] * 2, act=-1,
         boss=True),
    dict(name="The Cinder King", hp=86, deck=["n_king"] * 4
         + ["n_horror"] * 4 + ["n_shield"] * 2 + ["n_brute"] * 2, act=-1,
         boss=True),
    dict(name="The First Flame", hp=110, deck=["n_king"] * 5
         + ["n_horror"] * 4 + ["n_shield"] * 3, act=-1, boss=True),
]
