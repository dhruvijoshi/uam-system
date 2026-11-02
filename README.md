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
RequestRide → BoardPassenger → DepartAircraft → ArriveAircraft → DisembarkPassenger → ChargeAircraft → FinishCharging
```

Travel time between vertiports is the Euclidean distance between their latitude/longitude coordinates, rounded to the nearest tick (minimum 1). Battery cost is calculated per flight from that same distance. After the passenger disembarks, the aircraft charges at 5% per tick and is unavailable until `FinishCharging` returns it to `idle`.

When a ride is requested, the distance and battery required are computed first, then the dispatcher (see [dispatch.py](dispatch.py)) ranks the aircraft at the origin with the simulation's dispatch policy and asks each one's `AircraftAgent` (see [agent.py](agent.py)) in that order. The first to accept gets the ride. The agent only decides; `RequestRide` applies the result to the sector and the simulation. An agent accepts only if the aircraft is at the origin vertiport, is `idle`, and has more battery than the trip requires plus a 20% reserve. If an aircraft at the origin is still flying or charging and none can take the ride yet, the request is retried each tick until one is idle.

Dispatch policies are sort keys over the aircraft at the origin: `best_fit` (default, lowest sufficient battery first, keeping fully charged aircraft free for longer trips) and `highest_battery`. Pass one to `build_sim(dispatch_policy=...)`.

Each ride request is also tracked as a `FlightSector` — a journey record that starts in a `requested` state and is filled in as the ride progresses (aircraft assigned, distance/battery calculated, departure and arrival ticks stamped), rather than that information being computed once and thrown away. A request is marked `rejected` instead of silently disappearing, with the reason stored on the sector (`reject_reason`) and in the log: `no_aircraft` when none is at the origin, `low_battery` when every aircraft there is too low to fly the trip.

After a run, [metrics.py](metrics.py) summarises it: acceptance rate, rejections by reason, and average battery at departure.

See [docs/current_architecture_diagram.png](docs/current_architecture_diagram.png) for the system architecture and [docs/Phase_1_Kaneki_journey_flow.png](docs/Phase_1_Kaneki_journey_flow.png) for a single passenger's journey through the event chain.

---

## Project structure

```
.
├── main.py            # Loads a city file and drives the simulation entry point
├── models.py          # Core domain dataclasses (Passenger, Aircraft, Vertiport, FlightSector)
├── events.py          # Event classes that implement the ride lifecycle
├── agent.py           # AircraftAgent: decides whether an aircraft accepts a ride
├── dispatch.py        # Battery-aware dispatch: ranks aircraft at a vertiport and picks one
├── simulation.py      # Discrete-event engine (priority queue + registry + logging)
├── metrics.py         # Run summary: acceptance rate, rejection reasons, departure battery
├── data/
│   └── cities/
│       └── re.json    # Sample city: vertiports, aircraft, passengers, and ride requests
├── logs/              # Structured run logs (.jsonl), written after each run
└── docs/              # Architecture diagrams
```

---

## Running the simulation

Requires Python 3.10+ 

```bash
python main.py
```

Each run prints a log and saves it to `logs/run_<timestamp>.jsonl`.

Example simulation log:
```
[t=0][assigned] Rinkaku assigned to Kaneki (id: p0001) from Anteiku (id: v0001) to Zeum Hall (id: v0002)
[t=1][boarded] Kaneki (id: p0001) boarded Rinkaku at Anteiku (id: v0001)
[t=2][departed] Rinkaku departed Anteiku -> Zeum Hall (ETA 41t)
[t=5][rejected] Ride requested (r0005) by Yoshimura (p0005) from Anteiku to Tsukiyama Estate was cancelled (no_aircraft).
[t=43][arrived] Rinkaku arrived at Zeum Hall, battery 79%
[t=44][disembarked] Kaneki disembarked at Zeum Hall
[t=45][charging] Rinkaku is currently being charged
[t=50][charged] Rinkaku charged to 100%, status idle
...
```

---

## Key concepts

| Entity | Responsibility |
|---|---|
| **Vertiport** | Represents a landing location and maintains the aircraft currently stationed there. |
| **Aircraft** | Represents an eVTOL vehicle with a home base, current location, battery level, on-board passenger, and operational state (`idle`, `flying`, `charging`). |
| **AircraftAgent** | Decision logic for one aircraft: observes the aircraft and the requested sector, and returns accept, reject (with a reason), or wait. |
| **Dispatch policy** | A sort key that orders the aircraft at a vertiport; the first one whose agent accepts flies the ride. |
| **Passenger** | Represents a traveler. Tracks current location and status; does not carry a fixed destination — a passenger can take many trips, each defined by its own sector. |
| **FlightSector** | The journey record for one ride request: passenger, origin, destination, assigned aircraft, distance, battery required, and timestamps. Created when the request is scheduled and filled in as the ride runs its course. |
| **Event** | Represents a discrete action within the simulation. Each event updates the world and schedules the next event(s). |

---

## World data

The world is defined in a JSON file under `data/cities/` (currently [re.json](data/cities/re.json)) and loaded by `main.py` at startup — nothing about the vertiport layout, fleet, passenger roster, or ride requests is hard-coded. Each file has four sections:

```json
{
  "vertiports":  [{ "id": "v0001", "name": "Anteiku", "latitude": 10, "longitude": 20 }],
  "passengers":  [{ "id": "p0001", "name": "Kaneki", "location": "v0001" }],
  "aircrafts":   [{ "id": "Rinkaku", "home": "v0001", "location": "v0001", "battery": "100" }],
  "sectors":     [{ "id": "r0001", "passenger": "p0001", "origin": "v0001", "destination": "v0002", "ride_request_time": "0" }]
}
```

Vertiport, passenger, and aircraft ids are referenced throughout by string id, so a new city is a drop-in replacement as long as it follows this schema — swap the file path in `main.py` to run a different city.

`sectors` is the ride-request list: each entry names a passenger, an origin and destination vertiport, and the tick it should be requested at. A passenger only has a fixed *location* in the roster, not a destination — where they go is defined per-trip by a sector, so the same passenger can appear in several sectors with different destinations and request times over the course of a run. Requesting a ride as live input (rather than a pre-scheduled sector) remains a possible future addition.

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

### Phase 3 — Ride Requests as Journey Records

- `FlightSector` entity, created per ride request and separate from the passenger
- Passengers decoupled from a fixed destination — trips are defined by sectors, not the roster
- Ride requests scheduled at their own tick instead of uniformly at `t=0`
- Battery cost calculated from actual distance flown, not a flat rate
- Rejected requests (no aircraft available) recorded instead of silently dropped

### Phase 4 — Aircraft Agent

- `AircraftAgent` decides whether an aircraft accepts a requested ride (location, status, battery)
- Distance and battery requirement computed at request time so the agent can use them
- Rejection by the agent recorded on the sector and in the log
- Non-instant charging (5% per tick) with a `charging` state

### Phase 5 — Battery-Aware Dispatch

- `dispatch.py` picks among all aircraft at the origin instead of the last one parked, so a charging aircraft no longer blocks an idle one
- 20% battery reserve required after the flight
- Pluggable dispatch policy (`best_fit`, `highest_battery`)
- Rejection reasons (`no_aircraft`, `low_battery`) on the sector and in the log
- Rides wait and retry while an aircraft at the origin is still flying or charging
- Run summary in `metrics.py`

### Planned

- Resource-based aircraft scheduling
- Passenger waiting queues
- Aircraft utilization statistics
- Routing constraints
- No-fly zones
- Weather effects
- Multiple city support

---

## Motivation

This project is less about building an air taxi simulator and more about exploring how complex transportation systems can be modeled through software.

As the project grows, the goal is to evolve it into a flexible experimentation platform for studying dispatch policies, operational constraints, and autonomous transportation workflows.