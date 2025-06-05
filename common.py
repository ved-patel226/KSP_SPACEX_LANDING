import math
import os
import time

class Telemetry(object):
    def __init__(self, vessel):
        ref_frame = vessel.orbit.body.reference_frame
        self.apoapsis = vessel.orbit.apoapsis_altitude
        self.periapsis = vessel.orbit.periapsis_altitude
        self.time_to_apo = vessel.orbit.time_to_apoapsis
        self.time_to_peri = vessel.orbit.time_to_periapsis
        self.velocity = vessel.orbit.speed
        self.inclination = math.radians(vessel.orbit.inclination)
        self.altitude = vessel.flight(ref_frame).mean_altitude
        self.terrain_altitude = vessel.flight(ref_frame).surface_altitude
        self.lat = vessel.flight(ref_frame).latitude
        self.lon = vessel.flight(ref_frame).longitude
        self.q = vessel.flight(ref_frame).dynamic_pressure
        self.g = vessel.flight(ref_frame).g_force
        self.vertical_speed = vessel.flight(ref_frame).vertical_speed
        
        self.vessel = vessel
        
    def get_data(self):
        self.update()
        
        return {attr: getattr(self, attr) for attr in dir(self)
            if not attr.startswith('_') and not callable(getattr(self, attr))}
        
    def update(self):
        self.__init__(self.vessel)

def print_telemetry(telemetry):
    os.system('cls' if os.name == 'nt' else 'clear')
    # Retrieve all non-callable, non-private attributes from telemetry
    attributes = [(attr, getattr(telemetry, attr)) for attr in dir(telemetry)
                  if not attr.startswith('_') and not callable(getattr(telemetry, attr))]
    
    # Print header
    print(f"{'Attribute':<20} | {'Value':<20}")
    print("-" * 43)
    
    # Print each attribute in a row
    for attr, value in attributes:
        print(f"{attr:<20} | {str(value):<20}")
    time.sleep(0.5)
    