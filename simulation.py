"""
Discrete-event simulation engine for the UAM system.

Time is unitless; events are processed in chronological order.
Events scheduled at the same tick execute in insertion order via _counter.
"""
import heapq
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from events import RequestRide
from models import Vertiport, Aircraft, Passenger, FlightSector, LogCategory


@dataclass
class LogEntry:
    # Structured record of one simulation event, kept alongside the console print
    tick: int
    category: LogCategory
    message: str
    actor: str | None = None       # aircraft id, when the event is aircraft-driven
    sector: str | None = None
    passenger: str | None = None
    meta: dict = field(default_factory=dict)


class Simulation:
    def __init__(self):
        self.now = 0
        self._queue = []
        # Same-time events preserve insertion order in the heap
        self._counter = 0
        self.vertiports: dict[str, Vertiport] = {}
        self.aircrafts: dict[str, Aircraft] = {}
        self.passengers: dict[str, Passenger] = {}
        self.sectors: dict[str, FlightSector] = {}
        self.log_entries: list[LogEntry] = []

    def register_vertiport(self, vertiport: Vertiport):
        self.vertiports[vertiport.id] = vertiport

    def register_aircraft(self, aircraft: Aircraft):
        self.aircrafts[aircraft.id] = aircraft

        # Save the aircraft at vertiport matching its location
        for value in self.vertiports:
            if value == aircraft.location:
                self.vertiports[value].aircrafts.append(aircraft)

    def register_passenger(self, passenger: Passenger):
        self.passengers[passenger.id] = passenger

    def schedule_ride_request(self, sector: FlightSector):
        # Registry entry is created up front in "requested" state; RequestRide
        # fills in the aircraft/distance/timing fields as the ride progresses.
        self.sectors[sector.id] = sector
        self.schedule(sector.ride_request_time, RequestRide(sector.passenger, sector.origin, sector.destination, sector))


    def schedule(self, time, event):
        heapq.heappush(self._queue, (time, self._counter, event))
        self._counter += 1

    def log(self, category, message, *, actor=None, sector=None, passenger=None, meta=None):
        category = LogCategory(category)
        entry = LogEntry(self.now, category, message, actor, sector, passenger, meta or {})
        self.log_entries.append(entry)
        print(f"[t={self.now}][{category.value}] {message}")

    def logs_by(self, category=None, actor=None, sector=None):
        return [
            e for e in self.log_entries
            if (category is None or e.category == category)
            and (actor is None or e.actor == actor)
            and (sector is None or e.sector == sector)
        ]

    def save_logs(self, path: str | None = None) -> str:
        if path is None:
            os.makedirs("logs", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = f"logs/run_{timestamp}.jsonl"
        with open(path, "w", encoding="utf-8") as f:
            for entry in self.log_entries:
                record = asdict(entry)
                record["category"] = LogCategory(entry.category).value
                f.write(json.dumps(record) + "\n")
        return path

    def run(self):
        while self._queue:
            time, _, event = heapq.heappop(self._queue)
            self.now = time
            event.execute(self)
