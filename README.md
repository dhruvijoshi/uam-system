# Urban Air Mobility (UAM) Management System

A discrete-event simulation platform for experimenting with Urban Air Mobility (UAM) Operations.

The simulator models — vertiports, electric aircraft, and passengers — built in pure Python with no external dependencies using event-driven architecture. Rather than focusing on aircraft physics, the project explores operational problems such as dispatching, scheduling, passenger movement, and fleet management.

The simulation world is loaded from a JSON city definition, allowing different synthetic or real-world environments to be used without modifying the simulation engine.

---

## Why this project?

Urban Air Mobility is an emerging transportation domain where software systems will be responsible for coordinating thousands of autonomous aircraft, passengers, vertiports, and operational constraints.

This project is my attempt to understand those systems by building one from first principles.

Instead of relying on an existing simulation framework, the initial versions intentionally implement a custom discrete-event engine to better understand event scheduling, state transitions, and simulation architecture before introducing larger frameworks such as SimPy.

---

## How it works

The simulation runs on a priority-queue-based event loop (see [simulation.py](simulation.py)). Time advances in integer ticks. Each event fires at a scheduled tick and may enqueue follow-on events, forming a chain:

```
RequestRide → BoardPassenger → DepartAircraft → ArriveAircraft → DisembarkPassenger → ChargeAircraft
```

Travel time between vertiports is the Euclidean distance between their latitude/longitude coordinates, rounded to the nearest tick (minimum 1). Each flight costs the aircraft 10% battery; the aircraft recharges to 100% immediately after the passenger disembarks.

See [docs/Phase_1_UAM_architecture.png](docs/Phase_1_UAM_architecture.png) for the system architecture and [docs/Phase_1_Kaneki_journey_flow.png](docs/Phase_1_Kaneki_journey_flow.png) for a single passenger's journey through the event chain.

---

## Project structure

```
.
├── main.py            # Loads a city file and drives the simulation entry point
├── models.py          # Core domain dataclasses (Passenger, Aircraft, Vertiport)
├── events.py          # Event classes that implement the ride lifecycle
├── simulation.py      # Discrete-event engine (priority queue + registry)
├── metrics.py         # Placeholder for trip stats and fleet utilisation
├── data/
│   └── cities/
│       └── re.json    # Sample city: vertiports, aircraft, and passengers
└── docs/              # Architecture diagrams
```

---

## Running the simulation

Requires Python 3.10+ 

```bash
python main.py
```

Example simulation log:
```
[t=0] aircraft Rinkaku assigned
[t=0] Rinkaku assigned to Kaneki (id: p0001) from Anteiku (id: v0001) to Zeum Hall (id: v0002)
[t=1] Kaneki (id: p0001) boarded Rinkaku at Anteiku (id: v0001)
[t=2] Rinkaku departed Anteiku -> Zeum Hall (ETA 41t)
[t=43] Rinkaku arrived at Zeum Hall, battery 90%
[t=44] Kaneki disembarked at Zeum Hall
[t=45] Rinkaku charged to 100%, status idle
...
```

---

## Key concepts

| Entity | Responsibility |
|---|---|
| **Vertiport** | Represents a landing location and maintains the aircraft currently stationed there. |
| **Aircraft** | Represents an eVTOL vehicle with a home base, current location, battery level, and operational state. |
| **Passenger** | Represents a traveler moving through the simulation. Tracks current location, destination, and ride status. |
| **Event** | Represents a discrete action within the simulation. Each event updates the world and schedules the next event(s). |

---

## World data

The world is defined in a JSON file under `data/cities/` (currently [re.json](data/cities/re.json)) and loaded by `main.py` at startup — nothing about the vertiport layout, fleet, or passenger list is hard-coded. Each file has three sections:

```json
{
  "vertiports":  [{ "id": "v0001", "name": "Anteiku", "latitude": 10, "longitude": 20 }],
  "passengers":  [{ "id": "p0001", "name": "Kaneki", "location": "v0001", "destination": "v0002" }],
  "aircrafts":   [{ "id": "Rinkaku", "home": "v0001", "location": "v0001", "battery": "100" }]
}
```

Passenger `location`/`destination` and aircraft `home`/`location` all reference vertiport `id`s, so a new city is a drop-in replacement as long as it follows this schema — swap the file path in `main.py` to run a different city. Each passenger's ride request is currently scheduled automatically at `t=0`; requesting a ride as a live input is a possible future addition.

## Roadmap

### Phase 1 — Event-Driven Simulation

- Priority queue simulation engine
- Passenger ride lifecycle
- Aircraft state transitions
- Event scheduling

### Phase 2 — Data-Driven World

- JSON-based city loading
- World initialization
- Entity relationships via IDs
- Simulation independent of city layout

### Phase 3

- Flight entity
- Ride history
- Request vs Flight separation

### Planned

- Resource-based aircraft scheduling
- Passenger waiting queues
- Simulation metrics
- Aircraft utilization statistics
- Battery-aware dispatch
- Non-instant charging
- Routing constraints
- No-fly zones
- Weather effects
- Multiple city support

---

## Motivation

This project is less about building an air taxi simulator and more about exploring how complex transportation systems can be modeled through software.

As the project grows, the goal is to evolve it into a flexible experimentation platform for studying dispatch policies, operational constraints, and autonomous transportation workflows.