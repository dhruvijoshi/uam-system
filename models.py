"""
Core domain models for the UAM simulation.

Coordinates use an arbitrary 2-D plane; distance is Euclidean and maps
directly to travel time (rounded ticks) in DepartAircraft.
"""
from dataclasses import dataclass, field
from typing import List
import math


@dataclass
class Passenger:
    id: str
    location: str  # vertiport id or aircraft id reference while in transit
    destination: str
    status: str = "waiting"  # waiting → assigned → boarded → arrived


@dataclass
class Aircraft:
    id: str
    home: str      # home vertiport
    location: str  # current vertiport id, or "engaged" while in flight
    status: str = "idle"   # idle → flying → idle (after charge)
    battery: int = 100     # percentage; depletes 10% per trip


@dataclass
class Vertiport:
    id: str
    x: float
    y: float
    # Mutable list of aircrafts present
    aircrafts: List[Aircraft] = field(default_factory=list)

    def distance_to(self, other: "Vertiport") -> float:
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)