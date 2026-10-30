# CINDERSPIRE

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

## Run it

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

## Controls

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

## Board combat

- Your **hero** has 80 HP and **mana** that grows from 3 to 8.
- You and the enemy each have **five board slots**.
- Minions have **Attack / Health** and attack **once per turn**. A minion
  played this turn cannot attack unless it has **Charge**.
- **Taunt** minions must be attacked first; **Divine Shield** absorbs the first
  hit; **Poisonous** destroys anything it damages.
- **Battlecry** triggers when a minion is played, **Deathrattle** when it dies.
- You draw 5 cards at the start and 2 per turn. Enemy heroes play from their own
  deck and attack with their board.
- Reduce the enemy hero to 0. If your hero falls, the run ends.

## Five classes

Every class has **20 cards** (16 minions + 4 spells) and its own starter deck.
No card is shared between classes.

| Class | Identity | Starter deck |
| --- | --- | --- |
| **The Warden** | Taunt, big bodies, Charge | Ashguard, Cleaver ×2, Shieldbearer, Brute, Veteran, Ironclad, Berserker, Cleave, Rally |
| **The Ashblade** | Poison, Charge, card draw | Dagger, Cutthroat ×2, Poisoner, Shiv Dancer, Blademaster, Rogue, Shadowblade, Backstab, Fan of Knives |
| **The Emberwright** | Burn spells, machines, mana | Sparkbot, Furnace ×2, Boiler, Turret, Arcanist, Mage, Steambot, Fireball, Overclock |
| **The Pilgrim** | Healing, Divine Shield, Taunt | Acolyte, Cleric, Shieldbearer, Monk, Templar, Guardian, Healer, Zealot, Prayer, Blessing |
| **The Silver Hand** | Divine Shield, Recruits, buffs | Squire, Minibots, Recruiter, Lightwarden, Knight, Argent, Sergeant, Blessing, Reinforce, Consecration |

## What's in the spire

- **100 class cards + 10 tokens** (Shivs, Recruits, Soldiers, ...).
- **19 enemy heroes** with their own decks, including four keepers:
  the Ash Warden, the Hollow Choir, the Cinder King and the First Flame.
- **28 relics**, **13 potions**, **13 events**, **17 achievements**.
- Three acts of seven floors, plus the secret **Ember Heart** (four floors)
  unlocked after your first win.
- **Ascension**, **daily runs**, seed entry and a codex of 177 entries.
- Atomic saves with backups, schema migration and a crash log.

## How a run works

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

## Agent skills

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

## Project layout

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
