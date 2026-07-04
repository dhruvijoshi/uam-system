"""
Entry point for the simulation.

Wires up a small test world — three vertiports, two aircraft, two passengers —
and runs two concurrent ride requests to exercise the full event chain.
"""
from models import Passenger, Aircraft, Vertiport
from events import RequestRide
from simulation import Simulation


def main():
    sim = Simulation()

    # Vertiports placed on a 2-D plane; coordinates drive Euclidean travel time
    anteiku = Vertiport("Anteiku", 10.0, 20.0)
    zeum_hall = Vertiport("Zeum Hall", 50.0, 30.0)
    cochlea = Vertiport("Cochlea", 9.0, 12.0)
    sim.register_vertiport(anteiku)
    sim.register_vertiport(zeum_hall)
    sim.register_vertiport(cochlea)

    # Aircrafts initialise - id, Home, Current location parameters
    rinkaku = Aircraft("Rinkaku", "Anteiku", "Anteiku")
    bikaku = Aircraft("Bikaku", "Ward 11", "Anteiku")
    sim.register_aircraft(rinkaku)
    sim.register_aircraft(bikaku)

    # Initialise Passengers - id, current location and destination (destination added for initial system simulation)
    kaneki = Passenger("Kaneki", "Anteiku", "Zeum Hall")
    juuzou = Passenger("Juuzou", "Anteiku", "Cochlea")
    sim.register_passenger(kaneki)
    sim.register_passenger(juuzou)

    aircraft = anteiku.aircrafts
    print(f'list of aircrafts: {aircraft}')

    if aircraft:
        # Schedule at t=0 and t=1 so rides are staggered but share the same pool
        ride_1 = RequestRide(juuzou, anteiku, juuzou.destination)
        sim.schedule(0, ride_1)

        ride_2 = RequestRide(kaneki, anteiku, kaneki.destination)
        sim.schedule(1, ride_2)

        sim.run()
    else:
        print("No aircraft available")


if __name__ == "__main__":
    main()