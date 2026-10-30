# CINDERSPIRE

**A deckbuilding roguelike for the terminal.**

The spire is burning from the inside. Three acts, three keepers, and a lot of
ash stand between you and the Cinder King. Pick one of five classes, build a
deck, read the enemy intents, and climb - and once you have won, the throne
cracks open and a fourth, harder act waits below.

```
  CINDERSPIRE  · ELITE                                     ACT I  ·  FLOOR 1/7
  HP ████████████████ 80/80     GOLD 320       DECK 10                      BB
────────────────────────────────────────────────────────────────────────────────
  YOU  T1                     ▶ ATK 9                         ATK 9
   o                           ,---.                          /\_/\
  /|\                         ( >.< )                        ( o.o )
  / \                         /|   |\                         > ^ <
  BLK 12 IN 18               / |   | \                       /|   |\
  80/80                     Gremlin Nob                       Louse
  STR3 VULN1           ████│███│███│█ 55/55           ████│███│███│█ 17/17
  THRN3
  A battle begins.
  -- Turn 1 --
────────────────────────────────────────────────────────────────────────────────
  HAND  5       ENERGY ● ● ○                  +5 BLOCK              D5  X0  E0
   ╔════════════╗ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐
   ║ Defend   1 ║ │ Defend   1 │ │ Strike   1 │ │ Strike   1 │ │ Strike   1 │
   ║════════════║ │────────────│ │────────────│ │────────────│ │────────────│
   ║ Gain 5     ║ │ Gain 5     │ │ Deal 6     │ │ Deal 6     │ │ Deal 6     │
   ║ Block.     ║ │ Block.     │ │ damage.    │ │ damage.    │ │ damage.    │
   ║            ║ │            │ │            │ │            │ │            │
   ║            ║ │            │ │            │ │            │ │            │
   ╚════════════╝ └────────────┘ └────────────┘ └────────────┘ └────────────┘
```

## Run it

```bash
python3 play_cinderspire.py     # straight from the checkout
python3 -m cinderspire          # module form
pip install . && cinderspire    # installed command
./tools/build_zipapp.sh         # single-file build -> dist/cinderspire.pyz
```

Prebuilt single-file builds are attached to the repository's Releases.

Options: `--seed N` starts a run with a fixed seed, `--version` prints the
version and `--reset` clears saves.

Requires Python 3.9+ and a terminal with `curses`. No third-party packages.
Minimum size is 78x24; 100x30 or larger looks best.

## Controls

| Key | Action |
| --- | --- |
| `1`-`9` | Play the card in that slot |
| `←` `→` | Select a card |
| `TAB` / `↑` `↓` | Change target |
| `ENTER` / `SPACE` | Play selected card |
| `E` | End turn |
| `Q` | Potions |
| `D` | Deck |
| `R` | Relics |
| `ESC` | Pause menu (also settings, save & quit) |
| `L` / `?` | Combat log / status glossary |
| `V` | Pin or release the selected card's full text |
| `H` `J` `K` `L` | Move with vim keys (selection / target) |
| `S` (title) | Start a run from a seed |
| `R` (end screen) | Start a new run instantly |
| `↑` `↓` `ENTER` | Menus, map, shops |

Number keys are contextual: in menus and the map, `↑`/`↓` + `ENTER` do the
work.

## Five classes

| Class | Identity | Starter |
| --- | --- | --- |
| **The Warden** | Strength, heavy blows, self-damage | Bash |
| **The Ashblade** | Poison, Shivs, draw and Dexterity | Poison Stab |
| **The Emberwright** | Energy, Burns, powers and big Block | Beam Cell |
| **The Pilgrim** | Healing, Block, thorns and zeal | Smite |
| **The Silver Hand** | Divine Shield, Recruits, blessings and auras | Reinforce |

Each class has **60 unique cards** and its own basics - there is no shared card
pool at all. Rewards, shops and the codex change with your choice. Every class
can be won with, and winning with all five unlocks the **Polymath** achievement.

The starting decks are deliberately different from turn one:

| Class | Starter deck (10 cards) |
| --- | --- |
| Warden | 5× Strike (7 dmg), 3× Defend, Brace (Block + Strength), Bash |
| Ashblade | 5× Quick Cut (bonus vs Poisoned), 2× Dodge (Block + draw), Poison Dart, Shiv Throw, Poison Stab |
| Emberwright | 4× Spark (bonus with a Burn), 3× Guard, Arc, Coil, Beam Cell |
| Pilgrim | 4× Censure (damage + heal), 3× Ward, Bless, Shield Bash, Smite |
| Silver Hand | 4× Hammer (damage + Block), 3× Shield of Light, Faith, Aegis Blessing, Reinforce |

## What's in the spire

- **300 cards** - 60 unique cards per class, no shared pool - every one
  upgradeable.
- **24 enemies** with telegraphed intents, plus elites and **four bosses** -
  the Ash Warden, the Hollow Choir, the Cinder King and the secret First Flame
  - each with its own patterns and a phase change below half health.
- **30 relics**: 20 you find on the way, plus 10 **ember boons** offered only
  after a boss (extra energy, flat damage, a bigger hand, ...).
- **13 potions** in a three-slot belt - the panic button you save for the boss.
- **13 events**, and a fresh branching map for each act with rests, shops,
  treasure and elite fights.
- **Ascension**: win once and a harder spire unlocks. Each level gives enemies
  more HP and Strength while paying less gold.
- **Daily run** with a date-derived seed, plus seed entry for sharing.
- **Codex**: 384 entries (300 cards by class, relics, potions, bestiary,
  achievements), revealed as you discover them.
- **17 achievements** with lifetime stats, and one-time onboarding tips.
- **Burn** status cards, Molten Colossus elites and Flame Servants in the
  Ember Heart.

## How a run works

1. Pick a class, then a path up the branching map - seven floors per act.
2. Fight, and take one of three cards (or skip - small decks are sharp).
3. Spend gold at shops, upgrade at campfires, cut cards you never play.
4. Beat the keeper at the top of each act, claim an ember boon, and climb on.
5. Kill the Cinder King at the top of the third act.
6. If you have won at least once, the throne cracks open: descend into the
   Ember Heart for a four-floor gauntlet and the true final boss, or leave with
   the crown and take the victory.

Block is removed at the start of your turn, so save it for the turn an enemy
actually swings. Vulnerable increases damage taken by 50%; Weak cuts damage
dealt by 25%. Enemy intents always show the damage they will deal *after* those
modifiers.

Your best score, win count, ascension and settings are saved to
`~/.local/share/cinderspire/save.json`. Quitting to the title saves the run at
the map in `run.json`, so CONTINUE picks it up next time. Writes are atomic and
versioned, the previous file is kept as `.bak`, and a corrupt save falls back to
the backup instead of crashing. Old saves from `~/.cinderspire.json` are
migrated automatically.

## Project layout

```
play_cinderspire.py     entry point
cinderspire/
  data.py               cards, enemies, relics, potions, events
  core.py               rules: combat engine, map generation, run state, saves
  ui.py                 curses rendering, input, screens, animation
  __main__.py           python -m cinderspire
pyproject.toml          installable package + `cinderspire` command
tools/build_zipapp.sh   builds dist/cinderspire.pyz
CHANGELOG.md            release notes
```

The rules layer is independent of curses: `Combat` and `Run` can be driven
headlessly, which is how the balance simulation works.

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

## Development

```bash
python3 -m py_compile cinderspire/*.py
python3 -m cinderspire          # play
CINDERSPIRE_ANIM=0.2 python3 play_cinderspire.py   # faster enemy turns
```
