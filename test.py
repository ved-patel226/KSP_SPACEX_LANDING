import time
from krpc.client import Client
from krpc.services.spacecenter import Vessel

from termcolor import colored

from common import Telemetry

def start_suicide_burn():
    """
    Computes and prints the target speed at each altitude from 10,000m to 0m
    using a quadratic equation. The max speed is the current speed at 10,000m,
    and the target speed at 0m is 0.
    """
    
    max_altitude = 10_000
    min_altitude = 0
    max_speed = 1_000  # Current speed at 10,000m

    # Quadratic: v = a * h^2 + b * h + c
    # At h=10_000, v=max_speed
    # At h=0, v=0
    # v = max_speed * (h / max_altitude) ** 1.5

    current_altitude = 10_000

    print(colored(f"Starting suicide burn profile from {current_altitude:.2f} m, speed: {max_speed:.2f} m/s", "blue"))

    while True:
        telem = self.tele
        
        target_speed = max_speed * ((h - min_altitude) / (max_altitude - min_altitude)) ** 1.5
        print(colored(f"At {h:5d} m -> Target speed: {target_speed:7.2f} m/s | Actual speed:", "white"))
    
    print(colored("Reached ground: Target speed 0.00 m/s", "green"))

def main() -> None:
    start_suicide_burn()

if __name__ == '__main__':
    main()