import krpc
from common import Telemetry, print_telemetry
from land import LandingSuicideBurn


conn = krpc.connect()
vessel = conn.space_center.active_vessel


telemetry = Telemetry(vessel)

LandingSuicideBurn(conn, vessel, telemetry).run()
    
    