"""
Decision logic for a single aircraft: should it accept a requested ride?

The agent only decides; RequestRide applies the outcome to the simulation.
"""
from enum import Enum
from models import FlightSector, Aircraft

RESERVE = 20  # battery % that must remain after the flight

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



    def decide(self) -> tuple[Decision, str | None]:
        # Returns the decision and, on reject, the reason
        # Must be parked at the pickup vertiport
        if self.aircraft_location != self.sector_origin:
            return Decision.REJECT, "not_at_origin"

        # Flying or charging: it will be idle again, so the ride can wait for it
        if self.aircraft_status != "idle":
            return Decision.WAIT, None

        # Strictly more charge than the trip needs, plus the reserve
        if self.battery > self.battery_required + RESERVE:
            return Decision.ACCEPT, None

        return Decision.REJECT, "low_battery"


    
    def act(self) -> None:
        # Placeholder: the simulation applies the decision for now
        pass
