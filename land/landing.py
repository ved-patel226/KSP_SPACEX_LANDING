import time
from krpc.client import Client
from krpc.services.spacecenter import Vessel

from termcolor import colored

from common import Telemetry
from tqdm import tqdm

class LandingSuicideBurn:
    def __init__(self, conn: Client, vessel: Vessel, telemetry: Telemetry):
        self.conn = conn
        self.vessel = vessel
        self.telemetry = telemetry

    def setup_sas_retrograde(self):
        ap = self.vessel.auto_pilot

        ap.sas = True
        ap.sas_mode = ap.sas_mode.retrograde

        print(colored("SAS set to retrograde mode", "green", attrs=["bold"]))

    def change_sas_mode(self):
        ap = self.vessel.auto_pilot
        ap.reference_frame = self.vessel.surface_reference_frame
        ap.sas = True
        ap.sas_mode = ap.sas_mode.retrograde

        print(colored("SAS set to surface retrograde mode", "green", attrs=["bold"]))
    
    
    def reset_sas_mode(self):
        ap = self.vessel.auto_pilot
        ap.reference_frame = self.vessel.orbital_reference_frame

    def wait_until_altitude(self, altitude: float, keep_sas_mode: bool = False):
        flight = self.vessel.flight()
        start_altitude = flight.mean_altitude

        with tqdm(
            total=max(start_altitude - altitude, 1),
            desc=colored(f"Waiting for altitude: {altitude}m", "yellow"),
            unit="m",
            ncols=60,
            bar_format="{desc}: {bar} {percentage:3.0f}% | {n:.2f}/{total:.2f} m"
        ) as pbar:
            last_alt = start_altitude
            while flight.mean_altitude > altitude:
                current = flight.mean_altitude
                pbar.update(last_alt - current)
                last_alt = current
                time.sleep(1)
                flight = self.vessel.flight()
                
                if keep_sas_mode:
                    self.reset_sas_mode()
                    
            # Final update to ensure bar is complete
            pbar.update(last_alt - altitude)

        print(colored(
            f"Reached target altitude: {flight.mean_altitude:.2f} m",
            "cyan", attrs=["bold"]
        ))
        
    def start_suicide_burn(self):
        """
        Computes and prints the target speed at each altitude from 10,000m to 0m
        using a quadratic equation. The max speed is the current speed at 10,000m,
        and the target speed at 0m is 0.
        """
        
        self.change_sas_mode()
        telem = self.telemetry.get_data()
        
        max_altitude = 10_000
        min_altitude = 0
        max_speed = -telem["vertical_speed"]  # Current speed at 10,000m

        current_altitude = 10_000

        print(colored(f"Starting suicide burn profile from {current_altitude:.2f} m, speed: {max_speed:.2f} m/s", "blue"))

        while True:
            telem = self.telemetry.get_data()
            
            target_speed = max_speed * ((telem["terrain_altitude"] - min_altitude) / (max_altitude - min_altitude))

            # Use a quadratic profile for target speed to slow down more aggressively near the ground
            if telem["terrain_altitude"] > 750:
                Kp = 0.02
            elif telem["terrain_altitude"] > 50:
                Kp = 0.04
            else:
                Kp = 0.08

            
            # Calculate error between actual and target speed
            actual_speed = -telem["vertical_speed"]
            speed_error = actual_speed - target_speed

            # Simple proportional controller for throttle
            throttle = Kp * speed_error

            # Clamp throttle between 0 and 1
            throttle = max(0.0, min(1.0, throttle))

            self.vessel.control.throttle = throttle

            status_line = (
                f'At {telem["terrain_altitude"]:5.0f} m -> Target speed: {target_speed:7.2f} m/s | '
                f'Actual speed: {-telem["vertical_speed"]:.2f} | Throttle: {throttle:.2f}'
            )

            # Print status line, clear to end of line to avoid overlap
            print('\r' + colored(status_line, "white") + ' ' * 20, end='', flush=True)

            time.sleep(0.01)
            
            if telem["terrain_altitude"] < 250 and self.vessel.auto_pilot.sas_mode != self.vessel.auto_pilot.sas_mode.stability_assist:
                # Print newline before SAS message to avoid overlap
                print()
                self.vessel.auto_pilot.sas_mode = self.vessel.auto_pilot.sas_mode.stability_assist
                print(colored("SAS set to stability assist.", "green", attrs=["bold"]))
           
            if telem["terrain_altitude"] <= 10:
                break

        self.vessel.control.throttle = 0


        # Print newline before final message to avoid overlap
        print()
        print(colored("Reached ground: Target speed 0.00 m/s", "green"))


    def run(self):
        self.setup_sas_retrograde()
        

        self.wait_until_altitude(12_500, keep_sas_mode=True)
        self.start_suicide_burn()

        print(colored("Suicide burn complete.", "magenta", attrs=["bold"]))
