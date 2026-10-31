"""
Entry point for the simulation.

Wires up a small test world from re.json world file.
"""
from dispatch import best_fit
from metrics import summarize
from models import Passenger, Aircraft, Vertiport, FlightSector, LogCategory
from simulation import Simulation
import json

def build_sim(world_path='./data/cities/re.json', dispatch_policy=best_fit) -> Simulation:
    sim = Simulation(dispatch_policy)

    # Load and initialise world
    with open(world_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    for i in data['vertiports']:
        sim.register_vertiport(Vertiport(i['id'], i['name'], i['latitude'], i['longitude']))

    for i in data['passengers']:
        sim.register_passenger(Passenger(i['id'], i['name'], i['location']))

    for i in data['aircrafts']:
        sim.register_aircraft(Aircraft(i['id'], i['home'], i['location'], battery=int(i['battery'])))

    # Ride requests: each JSON sector becomes a FlightSector 
    for i in data['sectors']:
        sector = FlightSector(
            i['id'],
            sim.passengers[i['passenger']],
            sim.vertiports[i['origin']],
            sim.vertiports[i['destination']],
            int(i['ride_request_time']),
        )
        sim.schedule_ride_request(sector)

    return sim

def main():
    sim = build_sim()
    sim.run()

    summary = summarize(sim)
    sim.log(LogCategory.SUMMARY, "Simulation summary", meta=summary)

    log_path = sim.save_logs()
    print(f"logs written to {log_path}")
    print(summary)

if __name__ == "__main__":
    main()