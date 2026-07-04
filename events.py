"""
Simulation events for the UAM ride lifecycle.

Each event's execute() method may schedule follow-on events, forming a chain:
  RequestRide → BoardPassenger → DepartAircraft → ArriveAircraft
              → DisembarkPassenger → ChargeAircraft
"""
from dataclasses import dataclass
from models import Passenger, Aircraft, Vertiport


@dataclass
class RequestRide:
    passenger: Passenger
    origin: Vertiport
    destination: str
    status: str = "pending"

    def execute(self, sim):
        aircraft = self.find_aircraft()

        if aircraft is None:
            sim.log(f"No aircrafts available at {self.origin.id}")
            return

        sim.log(f"aircraft {aircraft.id} assigned")
        self.passenger.status = "assigned"
        self.status = "booked"
        aircraft.location = "engaged"
        sim.log(f"{aircraft.id} assigned to {self.passenger.id} from {self.origin.id} to {self.destination}")
        sim.schedule(sim.now, BoardPassenger(self.passenger, aircraft, self.origin.id, self.destination))

    def find_aircraft(self) -> Aircraft | None:
        # Dispatch the most recently registered aircraft
        if self.origin.aircrafts:
            return self.origin.aircrafts.pop()
        return None


@dataclass
class BoardPassenger:
    passenger: Passenger
    aircraft: Aircraft
    origin: str
    destination: str

    def execute(self, sim):
        self.passenger.location = self.aircraft
        sim.log(f"{self.passenger.id} boarded {self.aircraft} at {self.origin}")
        sim.schedule(sim.now + 1, DepartAircraft(self.passenger, self.aircraft, self.origin, self.destination))


@dataclass
class DepartAircraft:
    passenger: Passenger
    aircraft: Aircraft
    origin: str
    destination: str

    def execute(self, sim):
        self.aircraft.status = "flying"
        origin_vp = sim.vertiports[self.origin]
        dest_vp = sim.vertiports[self.destination]
        # Travel time is Euclidean distance rounded to nearest tick, minimum 1
        travel_time = max(1, round(origin_vp.distance_to(dest_vp)))
        sim.log(f"{self.aircraft.id} departed {self.origin} -> {self.destination} (ETA {travel_time}t)")
        sim.schedule(sim.now + travel_time, ArriveAircraft(self.passenger, self.aircraft, self.destination))


@dataclass
class ArriveAircraft:
    passenger: Passenger
    aircraft: Aircraft
    destination: str

    def execute(self, sim):
        self.aircraft.location = self.destination
        self.passenger.location = self.destination
        # Each trip costs 10% battery; clamp to 0 so it never goes negative
        self.aircraft.battery = max(0, self.aircraft.battery - 10)
        sim.vertiports[self.destination].aircrafts.append(self.aircraft)
        sim.log(f"{self.aircraft.id} arrived at {self.destination}, battery {self.aircraft.battery}%")
        sim.schedule(sim.now + 1, DisembarkPassenger(self.passenger, self.aircraft))


@dataclass
class DisembarkPassenger:
    passenger: Passenger
    aircraft: Aircraft

    def execute(self, sim):
        self.aircraft.passenger = None
        self.passenger.status = "arrived"
        sim.log(f"{self.passenger.id} disembarked at {self.passenger.location}")
        sim.schedule(sim.now + 1, ChargeAircraft(self.aircraft))


@dataclass
class ChargeAircraft:
    aircraft: Aircraft

    def execute(self, sim):
        # Instant full recharge
        self.aircraft.battery = 100
        self.aircraft.status = "idle"
        sim.log(f"{self.aircraft.id} charged to 100%, status idle")
