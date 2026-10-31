# Changelog

## 0.2.0

A second pass over the whole game: contracts, hulls, navigation, a deeper
economy, and AI that reacts to what the player does.

### Interface and navigation
- Escape is a real back action backed by a screen stack: station submenus
  return to the station, pause resumes the screen it came from, help returns to
  whoever opened it, and repeated menu cycles cannot trap the player.
- Full stop on the old bug where Escape from the buy screen opened pause and a
  second Escape left Resume pointing at pause.

### Trading
- Purchases and sales go through side-effect free quotes used by the interface,
  the route advice and the transaction itself, so the quoted total is exactly
  what is charged.
- Fixed the double counted price impact in bulk trades and the unit-price
  estimate that ignored the price curve.
- Cost basis per commodity, realised profit shown separately from revenue, and
  a consistent 0.1 CR rounding.
- `M` buys the maximum or sells the lot, with the executable quantity and the
  exact total shown before you press it.

### Combat and AI
- Bounded pitch-and-roll steering that can acquire a target behind, above or
  beside the ship, used by NPCs and missiles.
- Pirates intercept, demand cargo and only fire when refused; jettisoning works.
- Police scan for contraband, fine and seize it, hunt fugitives, and patrol
  harder in lawful space. Traders flee, call mayday and shed cargo. Bounty
  hunters only chase pilots with a record.
- Telegraphed NPC missiles that home and damage the player, making ECM useful.
- Asteroids, canisters and interceptors no longer count as murdered crews.

### Missions
- Station mission board with freight, courier, escort, rescue and bounty
  contracts, deadlines on the simulation clock, reserved cargo, a journal, and
  rewards paid exactly once.
- Boards are seeded, persisted per station and never rerolled by docking.

### Ships
- Five playable hulls with real differences in hold, speed, acceleration, turn
  rate, protection, racks and equipment slots; a shipyard that validates the
  purchase and shows the trade-in and final cost; no trade-in exploit.
- Hull and shield limits, the flight model, repairs and the HUD follow the ship.

### Docking
- Docking instrument with distance, lateral offset and side, signed roll error
  and direction, speed against the safe limit, and a clear-to-dock readout.
  Guidance and collision rules share one function.
- The docking computer is armed with `C`, explains why it cannot engage, and
  disarms itself after docking.

### Chart and economy
- System search, local and galaxy views, and multi-hop route planning (shortest
  or safer) that respects one tank per leg and says where to refuel.
- Mission and trade destinations selectable from the chart.
- Local economic events (shortages, construction, disruptions, gluts, festivals,
  medical emergencies) with durations, saved with the game.
- Markets persist between visits; trade impact fades with time rather than
  resetting, so stock cannot be refreshed by leaving and returning.

### Salvage and mining
- Wrecks leave canisters with a commodity, quantity and legal status; scooping
  needs equipment, space and a sane speed, and is resolved before collisions.
- Asteroids have finite ore, a mining laser cuts it loose, and fragments must be
  scooped.

### Progression
- New commanders start docked with a short, skippable tutorial that advances on
  real events and pays its reward once.
- Trading rank from realised profit and exploration rank from unique systems,
  alongside the existing combat rank, with milestones shown and announced.

### Saves
- Format version 2 with automatic migration from version 1; damaged or newer
  saves are explained and never overwritten (the old file is kept as `.bad`).
- Markets, events, missions, boards, tutorial state and the random state are all
  persisted, so a seeded run continues exactly.

### Under the hood
- New headless modules: `missions`, `navigation`, `economy`, `progression`,
  `tutorial`; the simulation now owns its clock, so tests drive the same code
  the terminal does.
- 301 tests, including full keyboard playthroughs and every screen rendered at
  78x24, 80x24 and 100x32 in Unicode, ASCII and monochrome.

## 0.1.0

First playable version: ten galaxies of 256 seeded systems, 3D flight with pitch
and roll only, a rotating Coriolis slot, trading, combat, bounties, ranks and a
station economy.
