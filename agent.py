"""
Decision logic for a single aircraft: should it accept a requested ride?

The agent only decides; RequestRide applies the outcome to the simulation.
"""
from enum import Enum
from models import FlightSector, Aircraft

class Decision(str, Enum):
    ACCEPT = "accepted"
    REJECT = "rejected"
    WAIT = "wait"
    


class AircraftAgent:

    def __init__(self, aircraft: Aircraft, sector: FlightSector) -> None:
        self.aircraft = aircraft
        self.sector = sector



    def observe(self) -> None:
        # Snapshot of what the agent is allowed to see, taken just before deciding
        self.battery = self.aircraft.battery
        self.aircraft_status = self.aircraft.status
        self.aircraft_location = self.aircraft.location

        self.battery_required = self.sector.battery_required
        self.distance = self.sector.distance
        self.sector_origin = self.sector.origin.id
        return



    def decide(self) -> Decision:
        # Must be parked at the pickup vertiport
        if self.aircraft_location != self.sector_origin:
            return Decision.REJECT

        # Not flying or charging
        if self.aircraft_status != "idle":
            return Decision.REJECT

        # Strictly more charge than the trip needs
        if self.battery > self.battery_required:
            return Decision.ACCEPT

        return Decision.REJECT


    
    def act(self) -> None:
        # Placeholder: the simulation applies the decision for now
        pass
