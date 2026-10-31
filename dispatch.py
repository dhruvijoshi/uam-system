"""
Battery-aware dispatch: pick which aircraft at a vertiport flies a ride.

A policy is a sort key over the aircraft at the origin. Each aircraft's agent is
asked in that order and the first to accept gets the ride.
"""
from agent import AircraftAgent, Decision


def best_fit(aircraft):
    # Lowest battery first, keeping fully charged aircraft free for longer trips
    return aircraft.battery


def highest_battery(aircraft):
    return -aircraft.battery


def select_aircraft(vertiport, sector, policy=best_fit):
    """Return (decision, aircraft, reason): ACCEPT with an aircraft, WAIT while one is
    still busy here, or REJECT with the reason no aircraft could take the ride."""
    if not vertiport.aircrafts:
        return Decision.REJECT, None, "no_aircraft"

    waiting = False
    for aircraft in sorted(vertiport.aircrafts, key=policy):
        agent = AircraftAgent(aircraft, sector)
        agent.observe()
        decision, reason = agent.decide()
        if decision == Decision.ACCEPT:
            return decision, aircraft, None
        waiting = waiting or decision == Decision.WAIT

    if waiting:
        return Decision.WAIT, None, None
    return Decision.REJECT, None, reason  # every aircraft rejected; report the last reason
