import krpc
import math
import time
from krpc.services.spacecenter import Vessel, Node, Orbit

from rich.console import Console

console = Console()

class DeOrbitBurn:
    def __init__(self, conn: krpc.Client, vessel: Vessel):
        self.conn = conn
        self.vessel = vessel
        self.orbit = vessel.orbit
        self.body = self.orbit.body

    def closest_pass_to_latlon(
        self,
        lat_deg: float,
        lon_deg: float,
        coarse: int = 720,
        tol: float = 1.0
    ) -> dict:
        """
        Return the UT, dt (sec from now), and distance (m)
        of the closest approach of 'orbit' to (lat_deg, lon_deg).
        """
        now = self.conn.space_center.ut

        times = [now + i * self.orbit.period / coarse for i in range(coarse + 1)]
        target_vector = self.body.surface_position(lat_deg, lon_deg, self.body.reference_frame)

        min_distance = None
        closest_time = None
        closest_pos = None

        for t in times:
            pos = self.orbit.position_at(t, self.body.reference_frame)
            distance = math.sqrt(
                (pos[0] - target_vector[0]) ** 2 +
                (pos[1] - target_vector[1]) ** 2 +
                (pos[2] - target_vector[2]) ** 2
            )
            if min_distance is None or distance < min_distance:
                min_distance = distance
                closest_time = t
                closest_pos = pos

        dt = self.orbit.period / coarse
        while dt > tol:
            search_times = [closest_time + i * dt for i in range(-2, 3)]
            for t in search_times:
                pos = self.orbit.position_at(t, self.body.reference_frame)
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

        closest_time -= self.orbit.period / 12

        result = {
            "ut": closest_time,
            "dt": closest_time - now,
            "distance": min_distance,
        }

        console.print(f"Closest approach at UT={result['ut']:.2f} & DT={result['dt']:.2f}", style="bold green")
        console.print(f"Distance: {result['distance']:.2f} m", style="bold green")

        return result

    def create_node(self, ut: float, burn: float = 0.0) -> Node:
        """
        Create a maneuver node at the specified UT with a prograde or retrograde burn.
        """
        for existing_node in self.vessel.control.nodes:
            existing_node.remove()
        node = self.vessel.control.add_node(ut, prograde=-burn)
        console.print(f"Creating orbit burn maneuver node. Delta V: {burn:.2f}", style="bold blue")
        return node

    def execute_node(self, node: Node) -> None:
        """
        Execute the maneuver node.
        """
        ap = self.vessel.auto_pilot
        ap.sas = True
        ap.sas_mode = ap.sas_mode.maneuver

        console.print("Executing maneuver node...", style="bold yellow")

        estimated_burn_time = node.delta_v / 20

        while node.time_to >= estimated_burn_time / 2:
            time.sleep(1)

        while node.remaining_delta_v > 10:
            self.vessel.control.throttle = 1.0
            time.sleep(0.1)

        ap.sas_mode = ap.sas_mode.retrograde

        time.sleep(0.05)
        self.vessel.control.throttle = 0.0

        node.remove()
        console.print("Maneuver node executed successfully.", style="bold green")

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

        result = self.closest_pass_to_latlon(
            lat_deg=lat_deg,
            lon_deg=lon_deg,
            coarse=720,
        )

        self.conn.space_center.warp_to(result["ut"])

        distance = self.distance_to_target(lat_deg, lon_deg)
        console.print(f"Current distance to target: {distance:.2f} m", style="bold yellow")

        burn_delta_v = distance / 1500

        node = self.create_node(
            ut=self.conn.space_center.ut + 60,
            burn=burn_delta_v
        )

        self.execute_node(node)

def main() -> None:
    conn = krpc.connect(name='Closest Pass to Lat/Lon Example')
    vessel = conn.space_center.active_vessel

    burner = DeOrbitBurn(conn, vessel)
    burner.run()

if __name__ == '__main__':
    main()
