# Changelog

## 0.1.0

First playable version.

### Galaxy
- Ten galaxies of 256 systems each (2560 total), generated from three 16-bit
  seed words with the classic twist and digram name table.
- Jittered-grid chart layout with a repair pass, so no system is unreachable.
- Galaxy one is seeded so system 7 is Lave with its classic profile.
- `--dump-galaxy N` prints any galaxy; `tools/find_seed.py` searches seeds.

### Flight
- Real 3D with pitch and roll only; position, velocity and a 3x3 orientation
  matrix that is re-orthonormalised as it turns.
- Character rasteriser (`sketch.py`): starfield, ships, asteroids, sun, planet,
  station, depth buffer, silhouettes scaled by distance, three art modes.
- Forward radar with bearing, distance and contact height.
- Speed control, mass lock, hyperspace with a three second countdown.

### Combat
- Fourteen ship types plus asteroids and cargo canisters, with AI roles for
  pirates, police, traders, hunters and Thargoids.
- Laser with cone hit detection and range falloff, missile lock and homing
  missiles, E.C.M., energy bomb, escape capsule.
- Shields fore/aft, four energy banks, hull damage, bounties, legal status.

### Trading and stations
- Seventeen commodities with economy-driven prices, bid/ask spread and market
  impact that prevents same-station arbitrage.
- Coriolis station with a rotating slot; docking checks roll, lateral offset,
  speed and approach side, with a crash penalty.
- Station services: buy, sell, equipment, refuel, repair, clear record,
  galactic hyperdrive, best-hop trade advice.
- Sun skimming with fuel scoops.

### UI
- Curses cockpit and menus, 78x24 minimum, responsive up to 100x32 and beyond.
- Title, chart, flight, docked, buy, sell, equipment, status, inventory, help
  and pause screens, all reachable by keyboard.
- `--art`, `--classic`, `--no-colour`, `--start-docked`, `--seed`, `--galaxy`.

### Under the hood
- Save games in `$XDG_DATA_HOME/coriolis`, atomic writes, versioned format.
- 129 unit tests covering generation, maths, docking, combat, market, saves and
  every screen rendered headlessly.
- `tools/render.py` (headless screenshots), `tools/screenshot.py` (pty capture),
  `tools/build_zipapp.sh` (single-file build).
