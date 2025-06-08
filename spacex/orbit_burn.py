import krpc
import math
import time
from krpc.services.spacecenter import Vessel
from rich.console import Console

from common import closest_pass_to_latlon, create_node, execute_node
from rich.progress import Progress, BarColumn, TimeRemainingColumn


class DeOrbitBurn:
    def __init__(self, conn: krpc.Client, vessel: Vessel, console: Console ):
        self.conn = conn
        self.vessel = vessel
        self.orbit = vessel.orbit
        self.body = self.orbit.body
        self.console = console

    def distance_to_target(self, lat_deg: float, lon_deg: float) -> float:
        current_pos = self.orbit.position_at(self.conn.space_center.ut, self.body.reference_frame)
        target_vector = self.body.surface_position(lat_deg, lon_deg, self.body.reference_frame)
        distance = math.sqrt(
            (current_pos[0] - target_vector[0]) ** 2 +
            (current_pos[1] - target_vector[1]) ** 2 +
            (current_pos[2] - target_vector[2]) ** 2
        )
        return distance

    def run(self):
        """
        Run the deorbit burn sequence.
        """
        
        # KSC coords
        lat_deg = 28.573469
        lon_deg = -80.651070

        result = closest_pass_to_latlon(
            self.conn,
            self.orbit,
            self.console,
            lat_deg=lat_deg,
            lon_deg=lon_deg,
            coarse=720,
        )

        self.conn.space_center.warp_to(result["ut"])

        self.console.print(f"Closest pass to ({lat_deg}, {lon_deg}) at UT: {result['ut']:.2f} sec")


        distance = self.distance_to_target(lat_deg, lon_deg)
        self.console.print(f"Current distance to target: {distance:.2f} m", style="bold yellow")

        burn_delta_v = distance / 375

        node = create_node(
            vessel=self.vessel,
            console=self.console,
            ut=self.conn.space_center.ut + 60,
            burn=burn_delta_v
        )

        execute_node(node, self.vessel, self.console)

def main() -> None:
    conn = krpc.connect(name='Closest Pass to Lat/Lon Example')
    vessel = conn.space_center.active_vessel

    burner = DeOrbitBurn(conn, vessel)
    burner.run()

if __name__ == '__main__':
    main()
