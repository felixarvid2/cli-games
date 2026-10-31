# CORIOLIS

**An Elite-style space trading and combat game for the terminal.**

Ten galaxies, 2560 star systems, a Coriolis station you have to dock with by
hand, and pirates who would rather you did not. All of it inside an 80x24
character cockpit.

```
{flight}
```

## Run it

```bash
python3 play_coriolis.py        # straight from the checkout
python3 -m coriolis             # module form
pip install . && coriolis       # installed command
./tools/build_zipapp.sh         # single file: dist/coriolis.pyz
```

Requires Python 3.9+ and a terminal with `curses`. No third-party packages.
Minimum size is 78x24; 100x32 looks better.

| Option | Meaning |
| --- | --- |
| `--seed N` | deterministic encounters (same seed, same space) |
| `--galaxy N` | start in galaxy 1-10 |
| `--art solid\|wire\|hybrid` | ship silhouettes, outlines, or outlines up close |
| `--classic` | 1984 key map: arrows do nothing, fly with letters |
| `--start-docked` | skip the launch, start at the station menu |
| `--dump-galaxy N` | print all 256 systems of a galaxy and exit |
| `--selftest` | headless thirty-second simulation, then exit |
| `--no-colour` | monochrome |

## The galaxy

```
{chart}
```

Every galaxy is a chain of 256 systems generated from three 16-bit seed words:
`tweak(seed)` advances the chain, and each system draws its name from the
original digram table plus its chart position, economy, government, tech level,
population, productivity and radius.

The chart is a jittered 16x16 grid, then nudged so that **no system is ever
stranded** - everything has at least one neighbour inside one fuel tank. Galaxy
one is seeded so that system 7 is **Lave**, with its classic profile: rich
agricultural, feudal, tech 5, 2.0 billion people. `tools/find_seed.py` is the
brute-force search that found that seed, and `--dump-galaxy 1` prints the
galaxy exactly as generated.

## Flying and fighting

- Real 3D: your ship has a position, a velocity along its nose, and an
  orientation matrix. **Pitch and roll only, no yaw**, just like 1984.
- The forward view is rasterised to text: starfield, ships, asteroids, the sun,
  the planet and the station, depth-sorted so nearer things occlude further ones.
- Ships render as silhouettes that shrink with distance; past a few kilometres
  they become a single glyph. `--art wire` draws outlines, `hybrid` switches at
  close range.
- Radar: forward is up, bearing across, and the glyph tells you whether a
  contact is above (`^`), below (`v`), level (`o`) or behind you (`x`).
- Laser, missile lock, E.C.M., energy bomb, shields fore and aft, four energy
  banks, and a hull that does not regenerate for free.
- Fourteen ship types with roles: pirates in lawless space, police in
democracies, traders, bounty hunters, Thargoids. Bounties are paid; killing
clean ships makes you an Offender, and killing police makes you a Fugitive.
- Ranks from Harmless to Elite (6400 kills), saved in your profile.

## Trading and docking

```
{docked}
```

Prices follow the economy: goods a system produces are cheap there, goods it
needs are dear. There is a 5% dealer spread each way and your own trading moves
the price against you, so **buying and selling the same crate never makes
money** - you have to actually fly somewhere.

The station screen shows the best hop from where you are, sized to your wallet
and your hold, so the first ten minutes are not a guessing game: from Lave, a
few tonnes of Liquor/Wines to Raer are worth about 26 credits on the first trip.

```
{buy}
```

Docking is the game's skill check. The slot is the `=` bar on the Coriolis, and
it rotates with the station. To get in you need to be within 140 m of the slot
mouth, under 320 m/s, within 55 m laterally, and rolled to within 28 degrees of
the slot. Crash into the hull and it costs you 45 points of ship. The 1500 CR
docking computer flies the approach for you once you can afford it.

Hyperspace needs fuel (0.5 CR per light year, 7 LY tank) and is blocked while
anything is close enough to mass-lock you. Buy fuel scoops and you can skim the
sun for free fuel - at the cost of your hull.

## Controls

| Key | Flight | Station |
| --- | --- | --- |
| `S` `X` / arrows | pitch up / down | menu up / down |
| `,` `.` / arrows | roll left / right | menu up / down |
| `A` `Z` | more / less speed | - |
| `SPACE` | fire laser | - |
| `T` / `M` | lock / fire missile | - |
| `E` / `B` | E.C.M. / energy bomb | - |
| `L` | level the roll | - |
| `H` or `1` | galactic chart | - |
| `2` / `3` | status / inventory | - |
| `LEFT` `RIGHT` | - | trade quantity |
| `ENTER` | - | select |
| `ESC` | pause menu | pause menu |
| `?` | controls | controls |

## Bigger terminals

```
{flight100}
```

## Tests

```bash
python3 -m unittest discover -s tests -t tests
```

127 tests and no third-party runner: galaxy determinism and reachability, the
mathematics of cameras and matrices, docking tolerances, damage order, market
arbitrage, save/load and migrations, a full trade run, and every screen
rendered headlessly at 80x24 and 100x32.

`tools/render.py` runs the real `Game` class against a fake screen, so a layout
regression shows up as a test failure instead of a broken terminal.

## What is faithful, and what is not

Faithful in spirit: seed-driven galaxies, pitch/roll only, the rotating slot,
seven light years of fuel, the market model, the rank ladder, fore/aft shields,
energy banks, mass lock, sun skimming, bounties and legal status.

Deliberately different: the original had no save game, no mouse, and 8 galaxies;
this has saves at stations, a resize-safe responsive layout, ten galaxies (with
`GRAND MASTER` for anyone who loops all ten), and a modern default key map with
`--classic` if you want the old one. The galaxy data comes from the same kind of
algorithm but is not a bit-exact copy of the 1984 star charts.

Not implemented yet: missions, the Constrictor, witchspace ambushes, cargo
contracts, and the cloaking device.
