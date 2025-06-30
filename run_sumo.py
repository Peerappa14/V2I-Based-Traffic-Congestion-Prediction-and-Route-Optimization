import traci
import xml.etree.ElementTree as ET

# Load RSU positions from `osm.add.xml`
rsu_positions = {}
tree = ET.parse("osm.add.xml")
root = tree.getroot()
for rsu in root.findall("inductionLoop"):
    rsu_id = rsu.get("id")
    lane = rsu.get("lane")
    pos = float(rsu.get("pos"))
    rsu_positions[rsu_id] = (lane, pos)

print(f"Loaded {len(rsu_positions)} RSUs from osm.add.xml.")

# Start SUMO simulation
sumoCmd = ["sumo-gui", "-c", "osm.sumocfg"]
traci.start(sumoCmd)

step = 0
while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()
    active_vehicles = traci.vehicle.getIDList()

    for vehicle_id in active_vehicles:
        speed = traci.vehicle.getSpeed(vehicle_id)
        lane_id = traci.vehicle.getLaneID(vehicle_id)
        lane_pos = traci.vehicle.getLanePosition(vehicle_id)  # ✅ Get vehicle position

        print(f"Step {step}: Vehicle {vehicle_id} | Speed: {speed:.2f} m/s | Lane: {lane_id} | Position: {lane_pos:.2f}")

        # ✅ Check if vehicle is near an RSU (Induction Loop)
        for rsu_id, (rsu_lane, rsu_pos) in rsu_positions.items():
            if lane_id == rsu_lane:  # ✅ Same lane
                distance = abs(lane_pos - rsu_pos)
                if distance < 30:  # ✅ Within 30m range
                    print(f"🚗➡️📡 Vehicle {vehicle_id} detected by RSU {rsu_id} at lane {lane_id}")

                    # ✅ Example: Reduce vehicle speed near RSU
                    new_speed = max(speed * 0.8, 5)  # Reduce by 20%, min 5 m/s
                    traci.vehicle.setSpeed(vehicle_id, new_speed)
                    print(f"🔽 Speed of {vehicle_id} reduced to {new_speed:.2f} m/s")

    step += 1

traci.close()
