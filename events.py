"""
Simulation events for the UAM ride lifecycle.

Each event's execute() method may schedule follow-on events, forming a chain:
  RequestRide → BoardPassenger → DepartAircraft → ArriveAircraft
              → DisembarkPassenger → ChargeAircraft → FinishCharging

At RequestRide the aircraft's agent decides whether to accept; on reject
the chain stops there.
"""
import math
from dataclasses import dataclass
from models import Passenger, Aircraft, Vertiport, FlightSector, LogCategory
from agent import AircraftAgent, Decision

@dataclass
class RequestRide:
    passenger: Passenger
    origin: Vertiport
    destination: Vertiport
    sector: FlightSector
    status: str = "pending"

    def execute(self, sim):

        distance = self.origin.distance_to(self.destination)
        self.sector.distance = distance
        self.sector.battery_required = math.ceil(distance) / 2
        self.sector.estimated_time_of_arrival = int(distance)

        aircraft = self.find_aircraft()

        if aircraft is None:
            # ride rejected due to no aircrafts at vertiport
            self.sector.status = "rejected"
            sim.log(
                LogCategory.REJECTED,
                f"Ride requested ({self.sector.id}) by {self.passenger.name} ({self.passenger.id}) from {self.origin.name} to {self.destination.name} was cancelled due to no aircraft available.",
                sector=self.sector.id, passenger=self.passenger.id,
                meta={"origin": self.origin.id, "destination": self.destination.id},
            )
            return
        
        # The aircraft's agent decides whether to take the ride
        agent = AircraftAgent(aircraft, self.sector)
        agent.observe()
        decision = agent.decide()

        if decision == Decision.ACCEPT:
            self.passenger.status = "assigned"
            self.status = "booked"
            self.sector.status = "accepted"
            self.sector.aircraft = aircraft
            self.origin.aircrafts.remove(aircraft)

            sim.log(
                LogCategory.ASSIGNED,
                f"{aircraft.id} assigned to {self.passenger.name} (id: {self.passenger.id}) from {self.origin.name} (id: {self.origin.id}) to {self.destination.name} (id: {self.destination.id})",
                actor=aircraft.id, sector=self.sector.id, passenger=self.passenger.id,
            )
            sim.schedule(sim.now+1, BoardPassenger(self.passenger, aircraft, self.origin, self.destination, self.sector))
        
        else:
            # Agent declined
            self.sector.status = "rejected"
            sim.log(
                        LogCategory.REJECTED,
                        f"{aircraft.id} rejected the ride",
                        actor=aircraft.id, sector=self.sector.id,
                    )

    def find_aircraft(self) -> Aircraft | None:
        if self.origin.aircrafts:
            return self.origin.aircrafts[-1]
        return None


@dataclass
class BoardPassenger:
    passenger: Passenger
    aircraft: Aircraft
    origin: Vertiport
    destination: Vertiport
    sector: FlightSector

    def execute(self, sim):
        self.passenger.location = self.aircraft.id
        self.aircraft.passenger = self.passenger
        sim.log(
            LogCategory.BOARDED,
            f"{self.passenger.name} (id: {self.passenger.id}) boarded {self.aircraft.id} at {self.origin.name} (id: {self.origin.id})",
            actor=self.aircraft.id, sector=self.sector.id, passenger=self.passenger.id,
        )
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
        self.aircraft.location = "engaged"
        travel_time = max(1, round(self.sector.distance))

        self.sector.departure_time = sim.now
        self.sector.status = "enroute"

        sim.log(
            LogCategory.DEPARTED,
            f"{self.aircraft.id} departed {self.origin.name} -> {self.destination.name} (ETA {travel_time}t)",
            actor=self.aircraft.id, sector=self.sector.id,
            meta={"distance": self.sector.distance, "battery_required": self.sector.battery_required, "eta": travel_time},
        )
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

        sim.log(
            LogCategory.ARRIVED,
            f"{self.aircraft.id} arrived at {self.destination.name}, battery {self.aircraft.battery}%",
            actor=self.aircraft.id, sector=self.sector.id,
            meta={"battery": self.aircraft.battery},
        )
        sim.schedule(sim.now + 1, DisembarkPassenger(self.passenger, self.aircraft, self.sector))


@dataclass
class DisembarkPassenger:
    passenger: Passenger
    aircraft: Aircraft
    sector: FlightSector

    def execute(self, sim):
        self.aircraft.passenger = None
        self.passenger.status = "arrived"
        sim.log(
            LogCategory.DISEMBARKED,
            f"{self.passenger.name} disembarked at {sim.vertiports[self.passenger.location].name}",
            actor=self.aircraft.id, passenger=self.passenger.id, sector=self.sector.id,
        )
        sim.schedule(sim.now + 1, ChargeAircraft(self.aircraft))


@dataclass
class ChargeAircraft:
    aircraft: Aircraft

    def execute(self, sim):
        # Charges 5% per tick
        charge_required = 100 - self.aircraft.battery
        self.aircraft.status = "charging"
        time = math.ceil(charge_required / 5)
        
        sim.log(LogCategory.CHARGING, f"{self.aircraft.id} is currently being charged", actor=self.aircraft.id)
        sim.schedule(sim.now + time, FinishCharging(self.aircraft))

@dataclass
class FinishCharging:
    aircraft: Aircraft

    def execute(self, sim):
        # Aircraft becomes available again
        self.aircraft.battery = 100
        self.aircraft.status = "idle"
        sim.log(LogCategory.CHARGED, f"{self.aircraft.id} charged to 100%, status idle", actor=self.aircraft.id)
