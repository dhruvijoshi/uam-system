"""
Discrete-event simulation engine for the UAM system.

Time is unitless; events are processed in chronological order.
Events scheduled at the same tick execute in insertion order via _counter.
"""
import heapq
from events import RequestRide
from models import Vertiport, Aircraft, Passenger, FlightSector


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

    def log(self, message):
        print(f"[t={self.now}] {message}")

    def run(self):
        while self._queue:
            time, _, event = heapq.heappop(self._queue)
            self.now = time
            event.execute(self)
