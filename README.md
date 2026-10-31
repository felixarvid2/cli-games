# cli-games

Two games for the terminal, both plain Python with `curses` and no third-party
dependencies. Each game is self-contained: its own README, tests, `pyproject.toml`
and single-file build.

| Game | Directory | Run it | What it is |
| --- | --- | --- | --- |
| **CINDERSPIRE** | `cinderspire/` | `python3 play_cinderspire.py` | A Hearthstone-like deckbuilder roguelike |
| **CORIOLIS** | `coriolis/` | `python3 play_coriolis.py` | An Elite-style space trading and combat game |

```bash
python3 play_cinderspire.py                 # deckbuilder roguelike
python3 play_coriolis.py                    # space trading and combat
python3 -m unittest discover -s coriolis/tests -t coriolis/tests
```

---

## CINDERSPIRE

**A Hearthstone-like deckbuilder roguelike for the terminal.**

A hero, a hand of cards, and a five-slot board. Play minions, buff them, trade
them, and break the enemy hero before it breaks you. Climb three acts and the
secret Ember Heart across five classes.

```
  CINDERSPIRE  · COMBAT                                    ACT I  ·  FLOOR 1/7
  HP ████████████████ 80/80     GOLD 320       DECK 10                      BB
────────────────────────────────────────────────────────────────────────────────
    LOUSE SWARM    HP 26/26    MANA 3/3    HAND 5
   ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐
   │ 2/2        │ │ 0/4  TAUNT │ │    empty   │ │    empty   │ │    empty   │
   │ Bandit     │ │ Sentinel   │ │            │ │            │ │            │
   └────────────┘ └────────────┘ └────────────┘ └────────────┘ └────────────┘
────────────────────────────────────────────────────────────────────────────────
   ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐
   │ 2/4  TAUNT │ │ 5/3        │ │    empty   │ │    empty   │ │    empty   │
   │ Shieldbear…│ │ Berserker  │ │            │ │            │ │            │
   └────────────┘ └────────────┘ └────────────┘ └────────────┘ └────────────┘
   Ashguard (1): 1/3 TAUNT
  MANA ● ● ●  3/3                                  TURN 1   DECK 5   DISCARD 0
   ╔════════════╗ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐
   ║ Ashguard 1 ║ │ Cleaver  1 │ │ Cleave   2 │ │ Cleaver  1 │ │ Berserker3 │
   ║────────────║ │────────────│ │────────────│ │────────────│ │────────────│
   ║ 1 / 3      ║ │ 3 / 1      │ │ SPELL      │ │ 3 / 1      │ │ 5 / 3      │
   ║ TAUNT      ║ │            │ │ Deal 2     │ │            │ │            │
   ║            ║ │            │ │ damage to  │ │            │ │            │
   ╚════════════╝ └────────────┘ └────────────┘ └────────────┘ └────────────┘
  1-9 play  A attack all  TAB rows  E end  Q potion  V text  ESC
```

### Run it

```bash
python3 play_cinderspire.py     # straight from the checkout
python3 -m cinderspire          # module form
pip install . && cinderspire    # installed command
./tools/build_zipapp.sh         # single-file build -> dist/cinderspire.pyz
```

Prebuilt single-file builds are attached to the repository's Releases.
Options: `--seed N`, `--version`, `--reset`.

Requires Python 3.9+ and a terminal with `curses`. No third-party packages.
Minimum size is 78x24; 100x30 or larger looks best.

### Visuals

CINDERSPIRE uses a 256-colour terminal palette, per-class accent colours,
gradient banners, rounded panels, drop shadows, animated embers and sparks,
floating combat numbers, attack arrows, turn banners, confetti and more.
The full catalogue of 100 visual improvements is in [VISUALS.md](VISUALS.md).

### Controls

| Key | Action |
| --- | --- |
| `1`-`9` | Play the card in that slot |
| `←` `→` | Select a card, minion or target |
| `↑` `↓` / `TAB` | Switch row: hand → your board → enemy board |
| `0`-`5` | Pick the enemy hero (0) or a minion as the attack target |
| `ENTER` | Play the selected card, or attack with the selected minion |
| `A` | Attack with every ready minion |
| `E` | End turn |
| `Q` | Potions |
| `V` | Full card text / combat log |
| `D` / `R` / `L` / `?` | Deck / relics / log / keywords |
| `ESC` | Pause menu |
| Mouse | Click a card to select it, click it again to play; click your minion then an enemy to attack; click END TURN; click menu entries, map nodes, reward cards, shop rows and events |
| Drag | Hold a hand card or one of your minions, drag it onto an enemy minion or the enemy hero, and release. The target is highlighted and its stats are shown while you drag |

### Board combat

- Your **hero** has 80 HP and **mana** that grows from 3 to 8.
- You and the enemy each have **five board slots**.
- Minions have **Attack / Health** and attack **once per turn**. A minion
  played this turn cannot attack unless it has **Charge**.
- **Taunt** minions must be attacked first; **Divine Shield** absorbs the first
  hit; **Poisonous** destroys anything it damages.
- **Battlecry** triggers when a minion is played, **Deathrattle** when it dies.
- **Combo** cards get a bonus when they are the second or later card you play
  in the same turn. The hint bar shows `COMBO READY` once the chain is live.
- **Windfury** minions attack twice; **Rush** minions can attack minions the
  turn they arrive but never heroes.
- You draw 5 cards at the start and 2 per turn. Enemy heroes play from their own
  deck and attack with their board.
- Reduce the enemy hero to 0. If your hero falls, the run ends.

#### Synergies and combos

- **War Banner** gives every minion +1 Attack, including ones you summon later;
  stack it with **Reinforcements** and **Quartermaster** for a wide board.
- **Venom Aura** gives your whole board Poisonous, so even 1/1 Recruits trade
  with anything.
- **Pyromaniac** and **Mana Wyrm** reward spell chains: cheap spells clear the
  enemy board and grow your wyrm at the same time.
- **Lightwarden** gains +2 Attack whenever your minions are healed - pair it
  with **Circle of Healing** or **Divine Light**.
- **Inner Fire** turns a high-Health minion (The Wall, Sanctuary, Tirion) into a
  huge attacker.
- **Eviscerate**, **SI:7 Agent**, **Last Stand**, **Reinforcements** and
  **Circle of Healing** all have Combo payoffs. Play a cheap card first.
- **Tirion** leaves a Divine Shielded 3/3 Ashbringer behind, and **Divine
  Shield** plus **Hand of Protection** lets you attack without trading away
  your board.

### Five classes

Every class has **23 cards** and its own starter deck. No card is shared
between classes.

| Class | Identity | Starter deck |
| --- | --- | --- |
| **The Warden** | Taunt, big bodies, Charge | Ashguard, Cleaver ×2, Shieldbearer, Brute, Veteran, Ironclad, Berserker, Cleave, Rally |
| **The Ashblade** | Poison, Charge, card draw | Dagger, Cutthroat ×2, Poisoner, Shiv Dancer, Blademaster, Rogue, Shadowblade, Backstab, Fan of Knives |
| **The Emberwright** | Burn spells, machines, mana | Sparkbot, Furnace ×2, Boiler, Turret, Arcanist, Mage, Steambot, Fireball, Overclock |
| **The Pilgrim** | Healing, Divine Shield, Taunt | Acolyte, Cleric, Shieldbearer, Monk, Templar, Guardian, Healer, Zealot, Prayer, Blessing |
| **The Silver Hand** | Divine Shield, Recruits, buffs | Squire, Minibots, Recruiter, Lightwarden, Knight, Argent, Sergeant, Blessing, Reinforce, Consecration |

### What's in the spire

- **115 class cards + 11 tokens** (Shivs, Recruits, Soldiers, ...).
- **19 enemy heroes** with their own decks, including four keepers:
  the Ash Warden, the Hollow Choir, the Cinder King and the First Flame.
- **28 relics**, **13 potions**, **13 events**, **17 achievements**.
- Three acts of seven floors, plus the secret **Ember Heart** (four floors)
  unlocked after your first win.
- **Ascension**, **daily runs**, seed entry and a codex of 192 entries.
- Atomic saves with backups, schema migration and a crash log.

### How a run works

1. Pick a class and a path up the branching map.
2. Win board fights, take one of three cards (or skip).
3. Spend gold at shops, upgrade cards at campfires (+1/+1), cut dead weight.
4. Beat the keeper at the end of each act, claim an ember boon, climb on.
5. The Cinder King can be left with the crown - or you can descend into the
   Ember Heart for the true final boss.

Your best score, wins, ascension and settings are saved to
`~/.local/share/cinderspire/save.json`. Quitting to the title saves the run at
the map in `run.json`; CONTINUE picks it up next time. Writes are atomic and
versioned, the previous file is kept as `.bak`, and corrupt saves fall back to
the backup.

### Agent skills

These OpenCode skills are installed in `~/.agents/skills` and load automatically
when working on this repo:

| Skill | Used for |
| --- | --- |
| `card-game` | zone model, effect resolution, deckbuilder pitfalls |
| `game-feel` | juice, impact feedback, shake/hit-stop tiers |
| `game-ui-ux` | HUD/menu layout, focus navigation, screen stack |
| `save-systems` | save format, versioning, crash-safe writes |
| `systematic-debugging` | root-cause process for bugs and test failures |
| `verification-before-completion` | evidence before claiming a task is done |

They are agent tooling only - the game itself has no dependencies.

### Project layout

```
play_cinderspire.py     entry point
cinderspire/
  board_data.py         minions, spells, enemy decks
  board.py              board combat engine (heroes, mana, minions, keywords)
  data.py               relics, potions, events, achievements, classes
  core.py               run state, map, rewards, shops, saves
  ui.py                 curses rendering, input, screens, animation
  __main__.py           python -m cinderspire
pyproject.toml          installable package + `cinderspire` command
tools/build_zipapp.sh   builds dist/cinderspire.pyz
CHANGELOG.md            release notes
```

The rules layer is independent of curses: `BoardCombat` and `Run` can be driven
headlessly, which is how the balance and keyword tests work.

## CORIOLIS

Elite (1984) in an 80x24 terminal: ten galaxies of 256 procedurally generated
systems, real 3D flight with pitch and roll only, a Coriolis station you must
dock with by hand, pirates and police, bounties, legal status, and a market that
punishes staying put.

```
 CORIOLIS  · LAVE           FUEL  7.0 LY  CR 100.0            CLEAN
 ──────────────────────────────────────────────────────────────────────────────



                               ---  /______\
                               |+| |        |
                               --- | -+   --|
                                    \______/
                                        |

                             .         .

 ──────────────────────────────────────────────────────────────────────────────
  SPD ░░░░░░░░░░░░    0 m/s    FORE ██████████  AFT ██████████  HULL ████████
  E1 █████ E2 █████ E3 █████ E4 █████   MISSILES ●●●○   ---  ----  PULSE
 ──────────────────────────────────────────────────────────────────────────────
 ┌─ RADAR ───────┐ ALERT Hyperspace to Raer in 3...
 │               │ TARGET Cobra Mk III 7.3 km
 │       +       │ DOCK 6.0 km  Slot 5860m ahead
 │               │ HYPER RAER in 3.0
 └───────────────┘
  S/X pitch  ,/. roll  A/Z speed  SPC fire  T lock  M missile  E ECM  H chart
```

```bash
python3 play_coriolis.py                    # from this checkout
cd coriolis && ./tools/build_zipapp.sh      # dist/coriolis.pyz
```

Controls, the economy, the galaxy generator and the test suite are documented in
[coriolis/README.md](coriolis/README.md).
