# Changelog

## 2.4.0

- 100 visual improvements across every screen, catalogued in `VISUALS.md`:
  a wider 256-colour palette, class accents/emblems, gradient wordmark,
  segmented HP bars, relic chips, floor pips, rounded panels, drop shadows,
  zebra lists, icon-driven cards and keycap-style help.
- Combat feedback: floating damage/heal numbers, Divine Shield popups, hit
  flashes, screen shake, dotted attack arrows, lethal and combo badges,
  pulsing selection borders and animated turn banners.
- Map: node icons, visited ticks, travelled trail, boss crown, legend and a
  rounded side panel with relics and potions.
- Screens: shop awning/stamps/quotes, reward card fan/sparkles/coin stacks,
  animated campfire, event emblems and choice chips, codex progress, history
  zebra rows, pause/settings icons, confetti victory and ember defeat screens.
- New `cinderspire/visuals.py` holds palette, glyph, motif and easing data.
- Fixed normal fights being labelled `BOSS` in the header.
- Rewrote the help screen and class descriptions for board combat.

## 2.3.0

- Drag and drop: hold a card in hand or one of your minions, drag it onto an
  enemy minion or the enemy hero, and release to play/attack. The enemy under
  the cursor is highlighted and its name, stats and keywords are shown while
  dragging.
- Fixed the shop crashing when buying a potion (`Run.buy_potion` was missing).
- Fixed shop sold-state collisions between card slots and potion slots, so
  buying card 1 no longer marks potion 1 as sold.

## 2.2.0

- 15 new cards, three per class, built around combos and board synergies:
  War Banner, Last Stand, Reinforcements, SI:7 Agent, Eviscerate, Venom Aura,
  Pyromaniac, Mana Wyrm, Arcane Missiles, Lightwarden, Inner Fire, Circle of
  Healing, Quartermaster, Hand of Protection and Tirion.
- **Combo**: the second and later card you play in a turn triggers bonus
  effects. The hint bar shows `COMBO READY` while the chain is live.
- New keywords and triggers: Windfury (two attacks), Rush (minions only),
  Poisonous auras, spell-cast triggers, healing triggers and Lifesteal.
- Press `V` on a hand card for a full-text card view.
- Fixed targeted spells (Fireball, Eviscerate, ...) crashing when aimed at the
  enemy hero.

## 2.1.0

- Mouse support: click cards, minions, the enemy hero, END TURN, menus, map
  nodes, rewards, shop rows, rest options and events. Keyboard still works.

## 2.0.1

- Fixed a crash when an event upgraded, duplicated or removed a card.
- Explicit attack targeting: `0`-`5` picks the enemy hero or a minion, the
  current target is shown in the hint, and Taunt blocks with a clear message.

## 2.0.0

- Complete combat redesign: Hearthstone-like board with heroes, growing mana,
  five minion slots per side, and Taunt / Charge / Divine Shield / Poisonous /
  Battlecry / Deathrattle.
- 100 new class cards (20 per class, 16 minions + 4 spells) and 10 tokens.
- Enemy heroes with their own decks replace intent-based single enemies.
- New board UI: row cursor, attack-all, minion stats, full card text.
- Rewards, shops, deck, codex, relics and potions rebuilt around board play.

## 1.5.1

- Card text is no longer cut off: cards show five lines and the selected
  card's full text is shown above the hand (V toggles between card text and
  the combat log). During the enemy turn the log is shown automatically.

## 1.5.0

- Unique basics and starter decks for all five classes; no shared "6/5" clones.
- Class-flavoured common cards (poison draws, healing strikes, block riders).
- Balance pass: every class now wins 45-52 % in simulation.

## 1.4.0

- Fifth class: The Silver Hand (Divine Shield, Recruits, blessings, auras).
- 60 new paladin cards; 300 cards total across five classes.
- Codex now covers 384 entries; Polymath requires all five classes.

## 1.3.0

- 240 cards: 60 unique cards per class and no shared card pool.
- Class-specific basics; Brand/Cauterize no longer cross class lines.
- Effect-driven card engine with automatic card text.
- Codex now covers 324 entries.

## 1.2.0

- Four classes with separate card pools and starter decks: Warden, Ashblade,
  Emberwright, Pilgrim.
- Class selection before every run; class-filtered rewards and shops.
- 30 new cards, the Shiv token, and the Polymath achievement.
- Codex now covers 173 entries.

## 1.1.0

- Secret fourth act: The Ember Heart, with The First Flame, per-act floor
  counts and a true ending.
- Burn status cards, 8 new cards, 3 enemies, 4 relics, 2 potions, 2 events.
- Codex now covers 142 entries; 16 achievements.

## 1.0.0

First release.

- Three acts, seven floors each, three keepers: Ash Warden, Hollow Choir,
  Cinder King.
- 51 cards, 21 enemies, 26 relics (8 ember boons), 11 potions, 11 events.
- Ember-boon interludes, ascension levels, daily runs and seed entry.
- Codex with discovery tracking and achievements.
- Save/resume at the map with atomic writes, backups and schema migration.
- Potion belt, deck sorting, combat log, status glossary, colour-blind-friendly
  text labels and screen-shake/flash accessibility toggles.
- Single-file distribution: `tools/build_zipapp.sh` produces
  `dist/cinderspire.pyz`.
