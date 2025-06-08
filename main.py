import krpc
from common import Telemetry, print_telemetry
from spacex import LandingSuicideBurn, DeOrbitBurn, HorizontalSpeedBurn


from rich.console import Console
console = Console()

conn = krpc.connect()
vessel = conn.space_center.active_vessel


telemetry = Telemetry(vessel)

DeOrbitBurn(conn, vessel, console).run()
HorizontalSpeedBurn(conn, vessel, telemetry, console).run()
LandingSuicideBurn(conn, vessel, telemetry, console).run()
