import math
import os
import time
import krpc
from rich.console import Console

from krpc.services.spacecenter import Orbit, Node, Vessel

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
        
        self.horizontal_speed = vessel.flight(ref_frame).horizontal_speed
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
    


def create_node(vessel: Vessel, console: Console,  ut: float, burn: float = 0.0) -> Node:
    """
    Create a maneuver node at the specified UT with a prograde or retrograde burn.
    """
    for existing_node in vessel.control.nodes:
        existing_node.remove()
    node = vessel.control.add_node(ut, prograde=-burn)
    console.print(f"Creating orbit burn maneuver node. Delta V: {burn:.2f}", style="bold blue")
    return node

def execute_node(node: Node, vessel: Vessel, console: Console) -> None:
    """
    Execute the maneuver node.
    """
    ap = vessel.auto_pilot
    ap.sas = True
    ap.sas_mode = ap.sas_mode.maneuver
    
    vessel.control.rcs = True

    console.print("Executing maneuver node...", style="bold yellow")

    estimated_burn_time = node.delta_v * vessel.mass / vessel.available_thrust
    if vessel.available_thrust == 0:
        estimated_burn_time = float('inf')  # Avoid division by zero

    while node.remaining_delta_v > 10:
        if node.time_to > estimated_burn_time / 2:
            
            vessel.control.throttle = 0.0
            
            time.sleep(1)
            continue
        
        vessel.control.throttle = 1.0
        time.sleep(0.1)

    ap.sas_mode = ap.sas_mode.retrograde

    vessel.control.throttle = 0.0
    time.sleep(1)
    


    node.remove()
    console.print("Maneuver node executed successfully.", style="bold green")


def closest_pass_to_latlon(
    conn: krpc.Client, orbit: Orbit,   console: Console,
    
    lat_deg: float,
    lon_deg: float,
    coarse: int = 720,
    tol: float = 1.0
) -> dict:
    """
    Return the UT, dt (sec from now), and distance (m)
    of the closest approach of 'orbit' to (lat_deg, lon_deg).
    """
    now = conn.space_center.ut

    times = [now + i * orbit.period / coarse for i in range(coarse + 1)]
    target_vector = orbit.body.surface_position(lat_deg, lon_deg, orbit.body.reference_frame)

    min_distance = None
    closest_time = None
    closest_pos = None

    for t in times:
        pos = orbit.position_at(t, orbit.body.reference_frame)
        distance = math.sqrt(
            (pos[0] - target_vector[0]) ** 2 +
            (pos[1] - target_vector[1]) ** 2 +
            (pos[2] - target_vector[2]) ** 2
        )
        if min_distance is None or distance < min_distance:
            min_distance = distance
            closest_time = t
            closest_pos = pos

    dt = orbit.period / coarse
    while dt > tol:
        search_times = [closest_time + i * dt for i in range(-2, 3)]
        for t in search_times:
            pos = orbit.position_at(t, orbit.body.reference_frame)
            distance = math.sqrt(
                (pos[0] - target_vector[0]) ** 2 +
                (pos[1] - target_vector[1]) ** 2 +
                (pos[2] - target_vector[2]) ** 2
            )
            if distance < min_distance:
                min_distance = distance
                closest_time = t
                closest_pos = pos
        dt /= 2

    # closest_time -= orbit.period / 12

    result = {
        "ut": closest_time,
        "dt": closest_time - now,
        "distance": min_distance,
    }

    console.print(f"Closest approach at UT={result['ut']:.2f} & DT={result['dt']:.2f}", style="bold green")
    console.print(f"Distance: {result['distance']:.2f} m", style="bold green")

    return result
