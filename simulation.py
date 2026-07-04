"""
Discrete-event simulation engine for the UAM system.

Time is unitless; events are processed in chronological order.
Events scheduled at the same tick execute in insertion order via _counter.
"""
import heapq
from models import Vertiport, Aircraft, Passenger


class Simulation:
    def __init__(self):
        self.now = 0
        self._queue = []
        # Same-time events preserve insertion order in the heap
        self._counter = 0
        self.vertiports: dict[str, Vertiport] = {}
        self.aircrafts: dict[str, Aircraft] = {}
        self.passengers: dict[str, Passenger] = {}

    def register_vertiport(self, vertiport: Vertiport):
        self.vertiports[vertiport.id] = vertiport

    def register_aircraft(self, aircraft: Aircraft):
        self.aircrafts[aircraft.id] = aircraft
        
        # Save the aircraft at vertiport matching its location
        for key, value in self.vertiports.items():
            if key == aircraft.location:
                value.aircrafts.append(aircraft)

    def register_passenger(self, passenger: Passenger):
        self.passengers[passenger.id] = passenger

    def schedule(self, time, event):
        heapq.heappush(self._queue, (time, self._counter, event))
        self._counter += 1

    def log(self, message):
        print(f"[t={self.now}] {message}")

    def run(self):
        while self._queue:
            time, _, event = heapq.heappop(self._queue)
            self.now = time
            event.execute(self)
