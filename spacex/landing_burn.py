import time
from krpc.client import Client
from krpc.services.spacecenter import Vessel

from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn
from rich.live import Live
from rich.panel import Panel

from common import Telemetry

class LandingSuicideBurn:
    def __init__(self, conn: Client, vessel: Vessel, telemetry: Telemetry):
        self.conn = conn
        self.vessel = vessel
        self.telemetry = telemetry
        self.console = Console()

    def setup_sas_retrograde(self):
        ap = self.vessel.auto_pilot
        ap.sas = True
        ap.sas_mode = ap.sas_mode.retrograde
        self.console.print("[bold green]SAS set to retrograde mode[/bold green]")

    def change_sas_mode(self):
        ap = self.vessel.auto_pilot
        ap.reference_frame = self.vessel.surface_reference_frame
        ap.sas = True
        ap.sas_mode = ap.sas_mode.retrograde
        self.console.print("[bold green]SAS set to surface retrograde mode[/bold green]")
    
    def reset_sas_mode(self):
        ap = self.vessel.auto_pilot
        ap.reference_frame = self.vessel.orbital_reference_frame

    def wait_until_altitude(self, altitude: float, keep_sas_mode: bool = False):
        flight = self.vessel.flight()
        start_altitude = flight.mean_altitude
        distance_to_go = max(start_altitude - altitude, 1)

        with Progress(
            TextColumn("[yellow]Waiting for altitude:[/yellow]"),
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%",
            TextColumn("{task.completed:.2f}/{task.total:.2f} m"),
            console=self.console
        ) as progress:
            task = progress.add_task(f"{altitude}m", total=distance_to_go)
            
            while flight.mean_altitude > altitude:
                current = flight.mean_altitude
                progress.update(task, completed=start_altitude - current)
                time.sleep(1)
                flight = self.vessel.flight()
                
                if keep_sas_mode:
                    self.reset_sas_mode()
            
            # Final update to ensure bar is complete
            progress.update(task, completed=distance_to_go)

        self.console.print(f"[bold cyan]Reached target altitude: {flight.mean_altitude:.2f} m[/bold cyan]")
        
    def start_suicide_burn(self):
        self.change_sas_mode()
        telem = self.telemetry.get_data()
        
        max_altitude = 10_000
        min_altitude = 0
        max_speed = -telem["vertical_speed"]
        current_altitude = 10_000

        self.console.print(f"[blue]Starting suicide burn profile from {current_altitude:.2f} m, speed: {max_speed:.2f} m/s[/blue]")

        with Live(Panel("Initializing...", title="Suicide Burn"), refresh_per_second=10) as live:
            while True:
                telem = self.telemetry.get_data()
                
                target_speed = max_speed * ((telem["terrain_altitude"] - min_altitude) / (max_altitude - min_altitude))

                # Use a quadratic profile for target speed
                if telem["terrain_altitude"] > 750:
                    Kp = 0.02
                elif telem["terrain_altitude"] > 50:
                    Kp = 0.04
                else:
                    Kp = 0.08

                # Calculate error between actual and target speed
                actual_speed = -telem["vertical_speed"]
                speed_error = actual_speed - target_speed
                throttle = max(0.0, min(1.0, Kp * speed_error))
                self.vessel.control.throttle = throttle

                status_line = (
                    f'Altitude: {telem["terrain_altitude"]:5.0f} m\n'
                    f'Target speed: {target_speed:7.2f} m/s\n'
                    f'Actual speed: {actual_speed:.2f} m/s\n'
                    f'Throttle: {throttle:.2f}'
                )

                # Update live display
                live.update(Panel(status_line, title="Suicide Burn"))

                time.sleep(0.01)
                
                if telem["terrain_altitude"] < 150 and self.vessel.auto_pilot.sas_mode != self.vessel.auto_pilot.sas_mode.stability_assist:
                    self.vessel.auto_pilot.sas_mode = self.vessel.auto_pilot.sas_mode.stability_assist
                    self.console.print("[bold green]SAS set to stability assist.[/bold green]")
               
                if telem["terrain_altitude"] <= 10:
                    break

            self.vessel.control.throttle = 0

        self.console.print("[green]Reached ground: Target speed 0.00 m/s[/green]")

    def run(self):
        self.setup_sas_retrograde()
        self.wait_until_altitude(12_500, keep_sas_mode=True)
        self.start_suicide_burn()
        self.console.print("[bold magenta]Suicide burn complete.[/bold magenta]")
