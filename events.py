"""
Simulation events for the UAM ride lifecycle.

Each event's execute() method may schedule follow-on events, forming a chain:
  RequestRide → BoardPassenger → DepartAircraft → ArriveAircraft
              → DisembarkPassenger → ChargeAircraft
"""
import math
from dataclasses import dataclass
from models import Passenger, Aircraft, Vertiport, FlightSector


@dataclass
class RequestRide:
    passenger: Passenger
    origin: Vertiport
    destination: Vertiport
    sector: FlightSector
    status: str = "pending"

    def execute(self, sim):
        aircraft = self.find_aircraft()

        if aircraft is None:
            self.sector.status = "rejected"
            sim.log(f"Ride requested ({self.sector.id}) by {self.passenger.name} ({self.passenger.id}) from {self.origin.name} to {self.destination.name} was cancelled due to no aircraft available.")
            return

        self.passenger.status = "assigned"
        self.status = "booked"
        self.sector.aircraft = aircraft
        self.sector.status = "accepted"
        sim.log(f"{aircraft.id} assigned to {self.passenger.name} (id: {self.passenger.id}) from {self.origin.name} (id: {self.origin.id}) to {self.destination.name} (id: {self.destination.id})")
        sim.schedule(sim.now+1, BoardPassenger(self.passenger, aircraft, self.origin, self.destination, self.sector))

    def find_aircraft(self) -> Aircraft | None:
        # Dispatch the most recently registered aircraft
        if self.origin.aircrafts:
            return self.origin.aircrafts.pop()
        return None


@dataclass
class BoardPassenger:
    passenger: Passenger
    aircraft: Aircraft
    origin: Vertiport
    destination: Vertiport
    sector: FlightSector

    def execute(self, sim):
        self.passenger.location = self.aircraft
        sim.log(f"{self.passenger.name} (id: {self.passenger.id}) boarded {self.aircraft.id} at {self.origin.name} (id: {self.origin.id})")
        sim.schedule(sim.now+1, DepartAircraft(self.passenger, self.aircraft, self.origin, self.destination, self.sector))


@dataclass
class DepartAircraft:
    passenger: Passenger
    aircraft: Aircraft
    origin: Vertiport
    destination: Vertiport
    sector: FlightSector

    def execute(self, sim):
        self.aircraft.status = "flying"
        origin_vp = sim.vertiports[self.origin.id]
        dest_vp = sim.vertiports[self.destination.id]
        self.aircraft.location = "engaged"
        # Travel time is Euclidean distance rounded to nearest tick, minimum 1
        distance = origin_vp.distance_to(dest_vp)
        travel_time = max(1, round(distance))

        self.sector.distance = distance
        self.sector.battery_required = math.ceil(distance) / 2
        self.sector.estimated_time_of_arrival = distance
        self.sector.departure_time = sim.now
        self.sector.status = "enroute"

        sim.log(f"{self.aircraft.id} departed {self.origin.name} -> {self.destination.name} (ETA {travel_time}t)")
        sim.schedule(sim.now + travel_time, ArriveAircraft(self.passenger, self.aircraft, self.destination, self.sector))


@dataclass
class ArriveAircraft:
    passenger: Passenger
    aircraft: Aircraft
    destination: Vertiport
    sector: FlightSector

    def execute(self, sim):
        self.aircraft.location = self.destination.id
        self.passenger.location = self.destination.id
        # Battery cost is the sector's calculated requirement, not a flat rate;
        self.aircraft.battery = max(0, round(self.aircraft.battery - self.sector.battery_required))
        sim.vertiports[self.destination.id].aircrafts.append(self.aircraft)

        self.sector.arrival_time = sim.now
        self.sector.status = "arrived"

        sim.log(f"{self.aircraft.id} arrived at {self.destination.name}, battery {self.aircraft.battery}%")
        sim.schedule(sim.now + 1, DisembarkPassenger(self.passenger, self.aircraft))


@dataclass
class DisembarkPassenger:
    passenger: Passenger
    aircraft: Aircraft

    def execute(self, sim):
        self.aircraft.passenger = None
        self.passenger.status = "arrived"
        sim.log(f"{self.passenger.name} disembarked at {sim.vertiports[self.passenger.location].name}")
        sim.schedule(sim.now + 1, ChargeAircraft(self.aircraft))


@dataclass
class ChargeAircraft:
    aircraft: Aircraft

    def execute(self, sim):
        # Instant full recharge
        self.aircraft.battery = 100
        self.aircraft.status = "idle"
        sim.log(f"{self.aircraft.id} charged to 100%, status idle")
