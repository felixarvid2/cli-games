# CORIOLIS

**An Elite-style space trading and combat game for the terminal.**

Ten galaxies, 2560 star systems, a Coriolis station you have to dock with by
hand, pirates who would rather you did not, and a mission board that pays for
the risk. All of it inside an 80x24 character cockpit.

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
Minimum size is 78x24; 100x32 looks better. A new commander starts docked, with
a short tutorial contract on the board.

| Option | Meaning |
| --- | --- |
| `--seed N` | deterministic encounters (same seed, same space) |
| `--galaxy N` | start in galaxy 1-10 |
| `--art solid\|wire\|hybrid` | ship silhouettes, outlines, or outlines up close |
| `--classic` | 1984 key map: arrows do nothing, fly with letters |
| `--no-tutorial` | skip the introduction |
| `--dump-galaxy N` | print all 256 systems of a galaxy and exit |
| `--selftest` | headless simulation, then exit |
| `--no-colour` | monochrome |

## The galaxy and the chart

```
{chart}
```

Every galaxy is a chain of 256 systems generated from three 16-bit seed words:
`tweak(seed)` advances the chain, and each system draws its name from the
original digram table plus its chart position, economy, government, tech level,
population, productivity and radius. The chart is a jittered 16x16 grid, then
nudged so that **no system is stranded** - everything has at least one
neighbour inside one fuel tank. Galaxy one is seeded so system 7 is **Lave**
with its classic profile.

The chart has two views (local neighbourhood or whole galaxy), name search
(`/`), and route planning with `P`: shortest by distance, or safer with `M`,
using the fuel actually in the tanks for the first leg and a full tank for the
rest. It shows the next hop, the number of jumps, the total distance and where
you must refuel, and it explains when a destination cannot be reached. Mission
destinations (`N`) and trade recommendations (`T`) can be selected straight from
the chart. Jumping a route still goes through the normal jump, fuel and combat
rules.

## Missions

```
{missions}
```

Stations offer five kinds of contract: **freight** (cargo loaded and reserved on
acceptance), **courier** (a sealed packet, no hold space), **escort** (a trader
who must survive the trip), **rescue** (recover survivors adrift, then deliver
them) and **bounty** (destroy a named wanted ship in a named system). Each shows
its destination, pay, risk, difficulty, deadline and any cargo or hold
requirement before you sign, and the journal (`4` in flight) tracks progress and
time left. Deadlines run on the simulation clock, which only advances while you
are flying, and rewards are paid exactly once. Abandoning a contract unloads
the freight and pays nothing.

## Trading, events and profit

Prices follow the economy: goods a system produces are cheap there, goods it
needs are dear. There is a 5% dealer spread each way and your own trading moves
the price against you, so **buying and selling the same crate never makes
money**. Markets remember their stock between visits, so leaving and returning
cannot refresh a shelf, and trade impact fades with time instead of resetting.

The hold tracks what each tonne cost, so the market shows **realised profit**
separately from revenue, per row as well as per visit. `M` buys the maximum the
wallet, the hold and the shelf allow, or sells the lot. The station also lists
the best hops from where you are, net of fuel, sized to your wallet, with the
risk at the other end shown separately.

Local **economic events** - shortages, construction booms, disrupted routes,
gluts, festivals, medical emergencies - shift prices and stock for a few hours.
They are generated from the world seed, saved with the game, and never reroll on
docking.

## Ships

```
{shipyard}
```

Five hulls are for sale at tech 4 or better: the Cobra Mk III you start in, the
Adder freighter, the Moray courier, the Fer-de-Lance warship and the Asp
explorer. They differ in price, hold, top speed, acceleration, turn rate, hull,
shields, missile racks and equipment slots, and those differences are what the
flight model and the HUD use. The yard shows your ship beside the candidate with
the trade-in and the final cost, and refuses a purchase that would not fit your
cargo, your equipment, your missiles or your wallet. A trade-in never pays you
money, so swapping hulls back and forth always costs.

## Flying, fighting and docking

- Real 3D: position, velocity along the nose, and an orientation matrix.
  **Pitch and roll only, no yaw**, just like 1984.
- The forward view is rasterised to text: starfield, ships, asteroids, the sun,
  the planet and the station, depth-sorted so nearer things occlude further ones.
- The docking instrument shows distance to the slot, lateral offset and which
  side the slot is on, the signed roll error and which way to roll, speed
  against the safe limit, and `CLEAR TO DOCK` when all four checks pass. The
  docking computer is armed with `C`, only flies when armed and in range, says
  why it cannot engage, and disarms itself after docking.
- Radar: forward is up, bearing across, and the glyph tells you whether a
  contact is above (`^`), below (`v`), level (`o`) or behind you (`x`).
- **Pirates** intercept, demand cargo and only fire when refused - `J`
  jettisons, and they scoop the drop and leave. **Police** scan for contraband,
  fine and seize it, hunt fugitives, and patrol harder in lawful space.
  **Traders** flee, call mayday and shed cargo. **Bounty hunters** only chase
  pilots with a record. NPCs launch telegraphed missiles that home and hurt, so
  `E` (ECM) has a job.
- Wrecks leave salvage, asteroids can be mined with a mining laser (`N`) and
  their fragments scooped; collecting needs fuel scoops, hold space and a sane
  approach speed, and never counts as murder.
- Ranks: combat (Harmless to Elite), **trade** (realised profit, Penniless to
  Magnate) and **exploration** (unique systems, Lost to Cartographer), with the
  next milestone shown on the status screen.

## Station screen

```
{docked}
```

## Controls

| Key | Flight | Station |
| --- | --- | --- |
| `S` `X` / arrows | pitch up / down | menu up / down |
| `,` `.` / arrows | roll left / right | menu up / down |
| `A` `Z` | more / less speed | - |
| `SPACE` | fire laser | - |
| `T` / `M` | lock / fire missile | (in the market) buy max / sell all |
| `E` / `B` | E.C.M. / energy bomb | - |
| `L` | level the roll | - |
| `C` | dock computer on/off | - |
| `J` / `N` / `R` | jettison / mine / recover | - |
| `H` or `1` | chart (then `/` find, `P` route, `V` view, `M` mode) | - |
| `2` / `3` / `4` | status / inventory / journal | - |
| `LEFT` `RIGHT` | - | trade quantity (`[` `]` by ten) |
| `ENTER` | - | select / trade |
| `ESC` | pause menu | back one screen |
| `?` | controls | controls |

Escape is always "back": station submenus return to the station, pause resumes
the screen it came from, help returns to whoever opened it.

## Bigger terminals

```
{flight100}
```

## Saves

The run is saved when you dock and after station transactions, in
`$XDG_DATA_HOME/coriolis/save.json`, written atomically with a unique temporary
file. The format is version 2 and version 1 saves migrate automatically: they
gain the Cobra hull, their cargo and equipment (including a large bay) and a
clean progression slate. A damaged or newer save is never overwritten; the game
says why it cannot use it, and any file it has to replace is kept as
`save.json.bad`. The random state is saved too, so a seeded run continues
exactly where it left off.

## Tests

```bash
python3 -m unittest discover -s tests -t tests
```

301 tests and no third-party runner: galaxy determinism and reachability, the
mathematics of cameras and matrices, docking tolerances and the instrument's
guidance, damage order, market arbitrage and bulk pricing, mission completion,
failure and duplicate rewards, ship purchases, NPC behaviour and steering,
route validity and refuelling, event expiry and market persistence, finite
mining, the tutorial, save migration, and every screen rendered headlessly at
78x24, 80x24 and 100x32 in Unicode, ASCII and monochrome.

`tools/render.py` runs the real `Game` class against a fake screen, so a layout
regression shows up as a test failure instead of a broken terminal.
