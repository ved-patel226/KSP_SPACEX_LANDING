import krpc
from krpc.services.spacecenter import Vessel, Node
from rich.console import Console
from rich.progress import Progress, BarColumn, TimeRemainingColumn
import time

from common import Telemetry, closest_pass_to_latlon, create_node, execute_node


# lat_deg = 28.573469
# lon_deg = -80.651070

class HorizontalSpeedBurn:
    def __init__(self, conn: krpc.Client, vessel: Vessel, telemetry: Telemetry, console: Console ):
        self.conn = conn
        self.vessel = vessel
        self.orbit = vessel.orbit
        self.body = self.orbit.body
        self.console = console
        self.telemetry = telemetry
        
    def run(self):
        lat_deg = 28.573469
        lon_deg = -80.651070
        
        initial_pass = closest_pass_to_latlon(
            self.conn, self.vessel.orbit, self.console,  lat_deg, lon_deg
        )
        
        self.vessel.control.rcs = True
        self.console.print("[bold green]RCS enabled[/bold green]")
        
        
        i = 0
        
        while i < 5:
            i += 1
            
            node = create_node(
                self.vessel, self.console, self.conn.space_center.ut, burn=50 * i
            )
            
            new_pass = closest_pass_to_latlon(
                self.conn, node.orbit, self.console, lat_deg, lon_deg
            )
            
            ap = self.vessel.auto_pilot
            ap.sas = True
            
            ap.sas_mode = ap.sas_mode.maneuver
            
            time.sleep(2)
            
            
            self.console.print("[bold green]SAS set to maneuver mode[/bold green]")
            
            
            if initial_pass["distance"] > new_pass["distance"]:
                initial_pass = new_pass
            
                time.sleep(1)            
                
                execute_node(
                    node, self.vessel, self.console
                )
                
                self.vessel.control.rcs = True
                
            else:
                self.console.print(
                    f"[bold red]No improvement found after {i} iterations[/bold red]"
                )
                
                break
            
        self.vessel.control.rcs = False
        
        self.console.print("[bold green]RCS disabled[/bold green]")
        