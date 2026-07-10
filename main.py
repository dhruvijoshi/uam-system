"""
Entry point for the simulation.

Wires up a small test world from re.json world file.
"""
from models import Passenger, Aircraft, Vertiport
from events import RequestRide
from simulation import Simulation
import json

def main():
    sim = Simulation()
    
    # Load and initialise world
    with open('./data/cities/re.json','r', encoding='utf-8') as file:
        data = json.load(file)

    for i in data['vertiports']:
        sim.register_vertiport(Vertiport(i['id'], i['name'], i['latitude'], i['longitude']))

    for i in data['passengers']:
        sim.register_passenger(Passenger(i['id'], i['name'], i['location'], i['destination']))

    for i in data['aircrafts']:
        sim.register_aircraft(Aircraft(i['id'], i['home'], i['location'], i['battery']))

    # Initialise rides 
    for i in sim.passengers:
        sim.schedule(0, RequestRide(sim.passengers[i], sim.vertiports[sim.passengers[i].location], sim.vertiports[sim.passengers[i].destination]))
    
    sim.run()

if __name__ == "__main__":
    main()