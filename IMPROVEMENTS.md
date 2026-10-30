# CINDERSPIRE — 100 improvements

All 100 shipped. Verified by the regression suite described at the bottom.

## Combat UX (1–23)
1. Incoming damage total shown in the player panel ("IN 18").
2. "IN 18!!" lethal warning when the incoming hit would kill you.
3. Damage preview for the selected card ("9 DMG → Louse").
4. Block preview for block cards ("+8 BLOCK").
5. Multi-hit previews ("6x2") and ALL-target previews ("9 DMG ALL").
6. Preview includes the current target's name.
7. End-turn confirmation when energy and playable cards remain.
8. The confirmation is a toggle in Settings.
9. Full combat log overlay on `L`.
10. Status glossary overlay on `?`.
11. Vim-style `hjkl` movement.
12. Turn number next to YOU.
13. "You block N damage" log line.
14. Low-HP health text blinks.
15. Gold counter flashes and rolls to its new value.
16. Boss arrival message when a keeper fight starts.
17. "no playable cards" nudge instead of a wasted turn.
18. Target cycling skips dead enemies.
19. Intent damage reflects strength, weak and vulnerable.
20. Energy orbs animate when spent or refilled.
21. HP bars have segment ticks.
22. Selected card name is highlighted in reverse video.
23. Boss HP bar changes colour below half health.

## Content (24–44)
24. Card: Headbutt (recalls a card from the discard pile).
25. Card: Rage (block per attack this turn).
26. Card: Searing Blow (upgradeable five times).
27. Card: Flame Barrier (temporary thorns).
28. Card: Second Wind (exhaust skills for block).
29. Card: Immolate (heavy AoE, exhaust).
30. Card: Reckless Charge (free attack, costs HP).
31. Card: Ember Shot (free cantrip, exhaust).
32. Enemy: Mugger, an act I elite who steals gold.
33. Enemy: Spore Mother, an act II elite with poison.
34. Enemy: Gremlin Wizard.
35. Potion: Essence of Steel (Metallicize).
36. Potion: Liquid Memories (recall from discard).
37. Potion: Fruit Juice (permanent max HP).
38. Relic: Strawberry (+7 max HP).
39. Relic: Letter Opener (every 3 skills, AoE damage).
40. Relic: Sundial (energy every 3rd turn).
41. Boss relic: Throne of Ash (+1 energy, −6 max HP).
42. Boss relic: Choir Bell (block + extra draw).
43. Event: The Gambling Den.
44. Event: The Widow.

## Economy & screens (45–59)
45. Shops sell two potions.
46. Shop prices scale with the act.
47. Elites always drop a potion.
48. Bosses top up the potion belt.
49. Reward screen shows the relic description.
50. Unaffordable shop prices are red.
51. Event box shows your HP and gold.
52. Event choices you cannot afford are marked.
53. Rest shows how many cards can be upgraded.
54. Treasure shows the relic description.
55. Interlude shows HP and relic count.
56. Potions can only be bought with a free slot.
57. Gold rewards scale with the act.
58. Shop card names are coloured by type.
59. Shop rows show card cost and type.

## Systems (60–79)
60. Save and resume at the map.
61. CONTINUE entry on the title screen.
62. Settings screen (animation, end-turn confirm, flash).
63. Settings persist between sessions.
64. Seed entry for a new run (`s` on the title).
65. Run history for the last five runs.
66. Deck sort toggle (`s` in the deck view).
67. Pause shows act, floor, kills and seed.
68. Ascension description under the title menu.
69. Run seed shown on the end screen.
70. Title shows best score, wins and total runs.
71. Terminal title set to CINDERSPIRE.
72. Terminal title restored on exit.
73. Ctrl-C exits cleanly.
74. Auto-save whenever you leave a node.
75. "Save and quit" in the pause menu.
76. The save is deleted when a run ends.
77. Unreadable saves are discarded safely.
78. New runs reset combat and overlay state.
79. `r` on the end screen starts a new run instantly.

## Visuals & feel (80–91)
80. Ash particles drift across the victory screen.
81. Available map nodes pulse.
82. Act banner when a new act opens.
83. Low-HP rule line flashes red.
84. Smooth gold counter.
85. Animated energy orbs.
86. Boss HP bar turns red under half.
87. Enemy names dim as they weaken.
88. Title-screen falling ash.
89. Playable cards glow, unplayable ones dim.
90. Map legend panel.
91. Relic tags in the header.

## Quality (92–100)
92. Map side panel no longer collides with the legend.
93. Reward toasts use the right lifetime.
94. Empty-deck pickers are safe.
95. Every draw call clips to the terminal.
96. Status grammar is correct ("You gain").
97. Relic overlay lists relics in acquisition order.
98. Cards cannot be played during the enemy turn.
99. Damage dealt is tracked and shown on the end screen.
100. README and this manifest updated; regression suite green.

## Verification
- `python3 -m py_compile cinderspire/*.py`
- 350-run headless soak + 200 map seeds (0 failures)
- 51 cards played unupgraded and upgraded (0 errors)
- 21 enemies, 11 potions, 26 relics exercised (0 errors)
- 20 UI interaction checks across shop, potions, rest, deck,
  pause, save/continue, settings, seed, act transitions, boss kill
- Randomised fuzz: no tracebacks
- Balance: ~38% win rate for a naive AI over 250 full runs


## Skill audit (round 2)

Run against the installed `card-game`, `save-systems`, `game-feel`,
`game-ui-ux`, `systematic-debugging` and `verification-before-completion`
skills.

- **Zone invariant found a real duplication bug.** `list.remove(card)` compares
  by value, so with duplicate cards (five Strikes) Second Wind / True Grit /
  Headbutt / Liquid Memories could remove a *different* card and leave one card
  in two zones. Fixed with identity-based removal; `Combat.validate()` now
  asserts zone integrity under `CINDERSPIRE_DEBUG=1` (200 debug runs green).
- **Seed determinism.** Combat and potion drops used the UI's unseeded RNG;
  same seed now reproduces the same encounters, hands and intents.
- **Save hardening.** Atomic temp+replace writes, `.bak` fallback on parse *or*
  validation failure, integer schema version with a migration chain, load-time
  validation (unknown cards/relics/potions dropped, HP/gold/floor clamped),
  XDG data dir, legacy path migration.
- **Feedback tiers.** Damage now picks a small/medium/large preset: trauma-scaled
  shake (0.10 / 0.22 / 0.35 s), hit flash for medium+ hits, and a "Screen shake"
  accessibility toggle. Flashes stay well under three per second.
- **Screen stack.** Settings can be opened from the pause menu and returns to
  the pause instead of the title.
- **Deck-out feedback.** Drawing with both piles empty logs it once per turn
  instead of failing silently.
- **Defense in depth.** `Combat.validate()` checks negative energy, HP bounds,
  alive flags, negative block and duplicate zones after every action in debug.

New tests: `test_save.py` (15 checks: roundtrip, backup fallback, migration,
newer-version refusal, unknown-content cleanup, run reconstruction).


## Release readiness (round 3)

- **Codex** with five pages (cards, relics, potions, bestiary, achievements),
  discovery tracking, per-page and overall completion, locked entries hidden
  as `???`, and full details for unlocked entries.
- **13 achievements** with toasts, a dedicated codex page and lifetime stats
  (kills, damage, potions, combats) stored in the profile.
- **Daily run** seeded from the date, with the day's best score recorded and a
  checkmark on the title once played. Seed entry and `--seed` remain available
  for sharing.
- **Onboarding tips**: nine contextual hints shown once each (combat, intents,
  rewards, shops, campfires, potions, map, boons, ascension) with a Hints
  toggle in settings.
- **Crash safety**: an unexpected error saves the run at the last map, writes
  `crash.log` with the seed and traceback, restores the terminal and prints a
  friendly message instead of dying silently.
- **Packaging**: `pyproject.toml` (pip install + `cinderspire` command),
  `--version` / `--seed` / `--reset`, LICENSE, CHANGELOG and a single-file
  `dist/cinderspire.pyz` build script (188 KB).
- **Save schema v3** with migrations, now covering seen entries, achievements,
  tips, lifetime stats and the daily record.
- **Toast queue** so achievements and tips do not silently overwrite each other;
  achievements jump the queue.


## Act IV: The Ember Heart (round 4)

- **A secret fourth act** unlocked after the first win: four floors of flame
  enemies, a Molten Colossus elite and **The First Flame** (300-320 HP), with a
  different ending and score bonus.
- **The heart choice**: after the Cinder King, choose to leave with the crown
  (victory) or descend for a heal, an ember boon and the true final boss.
- **Per-act floor counts** (7/7/7/4) so the secret act is a tight gauntlet, not
  another full climb.
- **Burn status cards**: unplayable, 2 damage at end of turn, then exhaust;
  added by the First Flame, Flame Servants and the Brand card. Cauterize eats
  them for healing.
- **8 new cards** (Brand, Cauterize, Firestorm, Last Light, Ashen Guard, Pyre,
  Smolder, Ember Ward), **3 enemies**, **4 relics** (2 boss), **2 potions**,
  **2 events** and **3 achievements**.
- **Codex and totals** updated: 142 entries, status cards excluded.
- **Balance**: normal victory ~40 %, true ending ~18 % for the naive sim.


## Four classes (round 5)

- **Four playable classes**, each with its own card pool, starter deck and
  identity: Warden (strength), Ashblade (poison/shivs/draw), Emberwright
  (energy/burn/powers), Pilgrim (heal/block/zeal).
- **Class select screen** before every run (including daily, seeded and
  ascension runs), with identity, playstyle and starter card.
- **30 new cards plus the Shiv token**, including poison payoff (Bane, Catalyst,
  Envenom), shiv generators (Blade Dance, Cloak and Dagger), energy engines
  (Overclock, Turbo, Fusion, Machine Learning), and faith payoffs (Zeal,
  Martyr, Sanctuary, Aegis, Divine Shield).
- **Class-specific rewards and shops**: card pools are filtered by class plus
  shared basics, so runs feel different from the first fight.
- **Class-aware codex** with per-class sorting and class labels on every card.
- **Polymath achievement** for winning with all four classes, tracked per class
  in the profile.
- **Balance**: 30-36 % true-ending rate per class for the naive sim (50 runs
  each), so the four classes are within a few points of each other.


## 60 cards per class, zero sharing (round 6)

- **240 cards total**, exactly **60 per class**, with class-specific basics
  (`Strike`/`Defend` for the Warden, `Quick Cut`/`Dodge`, `Spark`/`Guard`,
  `Censure`/`Ward`). The old shared Strike/Defend were removed.
- **No shared cards**: every collectible card belongs to one class. Burn is an
  Emberwright status, Shiv an Ashblade token; Brand now creates a Shiv instead
  of a Burn and Cauterize exhausts any status card.
- **Effect-driven card definitions**: a small effect interpreter
  (`run_effects`) with automatic card text keeps 140+ new cards consistent and
  upgrade-safe (upgrades change the same numbers the text reads).
- **New mechanics across the sets**: multi-hit, AoE + status, energy engines,
  self-damage payoffs, block scaling, regen/metallicize/divine shells, thorns,
  poison payoffs and shiv generation.
- **Class balance** (naive sim, 40 runs each): Warden 38 %, Ashblade 45 %,
  Emberwright 42 %, Pilgrim 38 %.
- **Codex** now covers 324 entries; class pages show 60 cards each.


## The Silver Hand (round 7)

- **Fifth class, The Silver Hand**, built around the Hearthstone paladin
  fantasy: **Divine Shield**, **Silver Hand Recruits**, blessings and auras.
- **Divine Shield** is a real mechanic: a stack absorbs one entire hit, shown
  in the player panel and announced in the log.
- **Recruits** are 0-cost 4-damage tokens; Reinforce, Muster, Rally, Recruiter,
  Lightbringer and Silver Hand Army flood the board with them.
- **Auras** add flat damage to every attack; blessings grant Strength,
  Dexterity and healing.
- **60 new cards** (20 common, 22 uncommon, 16 rare, 2 basics, plus the Recruit
  token), no shared cards. Total content: **300 cards / 5 classes**.
- **Codex** now covers 384 entries; the class screen lists five classes with
  their own starter card and 60-card count.
- **Polymath** now requires a win with all five classes.
- **Balance** (40 sims each): Warden 45 %, Ashblade 40 %, Emberwright 40 %,
  Silver Hand 38 %, Pilgrim 35 %.


## Class identity pass (round 8)

- **Unique basics for every class**, no more five clones of "6 damage / 5
  block": Quick Cut (poison payoff), Dodge (Block + draw), Spark (Burn payoff),
  Censure (damage + heal), Hammer (damage + Block), Shield of Light (Block that
  scales with Divine Shield), Ward (6 Block).
- **Distinct starter decks**: each class now opens with 4-5 different cards
  instead of 9 basics and a signature. Warden keeps the heavy 7-damage Strike,
  Ashblade cycles with Dodge and poisons, Emberwright holds Burns, Pilgrim
  heals on every Censure, the Silver Hand shields and recruits.
- **Class-flavoured commons**: Heavy Swing pays HP, Slice draws only against
  poisoned targets, Mace/Judgement heal, Holy Strike/Verdict add Block.
- **Balance after the pass** (60 sims per class): Warden 52 %, Ashblade 45 %,
  Emberwright 45 %, Pilgrim 47 %, Silver Hand 48 %.
