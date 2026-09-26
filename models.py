"""
Core domain models for the UAM simulation.

Coordinates use an arbitrary 2-D plane; distance is Euclidean and maps
directly to travel time (rounded ticks) in DepartAircraft.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List
import math


class LogCategory(str, Enum):
    REJECTED = "rejected"
    ASSIGNED = "assigned"
    BOARDED = "boarded"
    DEPARTED = "departed"
    ARRIVED = "arrived"
    DISEMBARKED = "disembarked"
    CHARGED = "charged"


@dataclass
class Passenger:
    id: str
    name: str
    location: str  # vertiport id or aircraft id reference while in transit
    status: str = "waiting"  # waiting → assigned → boarded → arrived


@dataclass
class Aircraft:
    id: str
    home: str      # home vertiport
    location: str  # current vertiport id, or "engaged" while in flight
    status: str = "idle"   # idle → flying → idle (after charge)
    battery: int = 100     # percentage; depletes based on distance travelled


@dataclass
class Vertiport:
    id: str
    name: str
    latitude: float
    longitude: float
    # Mutable list of aircrafts present
    aircrafts: List[Aircraft] = field(default_factory=list)

    def distance_to(self, other: "Vertiport") -> float:
        return math.sqrt((self.latitude - other.latitude) ** 2 + (self.longitude - other.longitude) ** 2)


@dataclass
class FlightSector:
    # Journey record for one ride request
    id: str
    passenger: Passenger
    origin: Vertiport
    destination: Vertiport
    ride_request_time: int
    aircraft: Aircraft | None = None
    distance: float = 0          # Euclidean distance, set on departure
    battery_required: float = 0  # distance / 2, set on departure
    departure_time: int = 0
    arrival_time: int = 0
    estimated_time_of_arrival: int = 0     # Same as distance
    status: str = "requested"        # requested → accepted | rejected; accepted → enroute → arrived