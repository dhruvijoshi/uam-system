# Urban Air Mobility (UAM) Management System

A discrete-event simulation of an Urban Air Mobility network — vertiports, electric aircraft, and passengers — built in pure Python with no external dependencies.

---

## How it works

The simulation runs on a priority-queue-based event loop (see [simulation.py](simulation.py)). Time advances in integer ticks. Each event fires at a scheduled tick and may enqueue follow-on events, forming a chain:

```
RequestRide → BoardPassenger → DepartAircraft → ArriveAircraft → DisembarkPassenger → ChargeAircraft
```

Travel time between vertiports is the Euclidean distance between their 2-D coordinates, rounded to the nearest tick (minimum 1). Each flight costs the aircraft 10% battery; the aircraft recharges to 100% immediately after the passenger disembarks.

---

## Project structure

```
.
├── main.py          # Scenario setup and simulation entry point
├── models.py        # Core domain dataclasses (Passenger, Aircraft, Vertiport)
├── events.py        # Event classes that implement the ride lifecycle
├── simulation.py    # Discrete-event engine (priority queue + registry)
└── metrics.py       # Placeholder for trip stats and fleet utilisation

```

---

## Running the simulation

Requires Python 3.10+.

```bash
python main.py
```

Example output:
```
list of aircrafts: [Aircraft(...), Aircraft(...)]
[t=0] aircraft Bikaku assigned
[t=0] Bikaku assigned to Juuzou from Anteiku to Cochlea
[t=0] Juuzou boarded Aircraft(...) at Anteiku
[t=1] aircraft Rinkaku assigned
...
[t=9] Rinkaku charged to 100%, status idle
```

---

## Key concepts

| Concept | Description |
|---|---|
| **Vertiport** | Named landing pad with (x, y) coordinates and a list of parked aircraft |
| **Aircraft** | Has a home base, current location, status (`idle`/`flying`), and battery % |
| **Passenger** | Travels from a location to a destination; status tracks ride progress |
| **Event** | Immutable dataclass with an `execute(sim)` method; schedules its own successors |

---

## World data

The scenario in `main.py` is hard-coded. In future, a richer world definition will be implemented for a data-driven Simulation.
