import traci
import xml.etree.ElementTree as ET
import math

# Start SUMO silently
sumoCmd = ["sumo", "-c", "osm.sumocfg", "--start", "--quit-on-end"]
traci.start(sumoCmd)

def distance(p1, p2):
    return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

# Get all candidate intersections
intersections = {}
edge_coverage = {}

for junction_id in traci.junction.getIDList():
    x, y = traci.junction.getPosition(junction_id)
    edges = set(traci.junction.getIncomingEdges(junction_id) + traci.junction.getOutgoingEdges(junction_id))
    if len(edges) > 2:
        intersections[junction_id] = {"position": (x, y), "edges": edges}
        edge_coverage[junction_id] = edges

# Build complete edge set
all_edges = set()
for edges in edge_coverage.values():
    all_edges.update(edges)

covered_edges = set()
used_positions = []
selected_intersections = set()

MIN_RSU_DISTANCE = 100  # Increase to reduce clustering
print("Placing optimized RSUs...")

# Greedy placement: place RSU only if it covers significant *new* edges
while covered_edges != all_edges:
    best_junction = None
    best_new_coverage = 0

    for junction_id, edges in edge_coverage.items():
        if junction_id in selected_intersections:
            continue

        # Skip junctions near already-used ones
        too_close = any(distance(intersections[junction_id]["position"], pos) < MIN_RSU_DISTANCE for pos in used_positions)
        if too_close:
            continue

        new_coverage = len(edges - covered_edges)
        if new_coverage > best_new_coverage:
            best_new_coverage = new_coverage
            best_junction = junction_id

    if best_junction is None:
        break

    selected_intersections.add(best_junction)
    covered_edges.update(edge_coverage[best_junction])
    used_positions.append(intersections[best_junction]["position"])

print(f"✅ Reduced RSUs to {len(selected_intersections)}")

# Write RSUs to XML
root = ET.Element("additional")
rsu_count = 0

for junction_id in selected_intersections:
    x, y = intersections[junction_id]["position"]
    edges = intersections[junction_id]["edges"]

    selected_lane = None
    min_distance = float("inf")
    selected_pos = 0

    for edge_id in edges:
        lane_id = f"{edge_id}_0"
        if lane_id in traci.lane.getIDList():
            lane_length = traci.lane.getLength(lane_id)
            if lane_length > 5:
                lane_x, lane_y = traci.lane.getShape(lane_id)[0]
                dist = ((x - lane_x)**2 + (y - lane_y)**2) ** 0.5
                valid_pos = max(1, min(dist, lane_length - 1))
                if valid_pos < min_distance:
                    min_distance = valid_pos
                    selected_lane = lane_id
                    selected_pos = valid_pos

    if selected_lane:
        rsu_id = f"rsu_{rsu_count}"
        ET.SubElement(root, "inductionLoop",
                      id=rsu_id,
                      lane=selected_lane,
                      pos=str(selected_pos),
                      freq="1",
                      file="detector_output.xml")
        rsu_count += 1

tree = ET.ElementTree(root)
tree.write("osm.add.xml")

print(f"✅ Final RSU XML created with {rsu_count} RSUs")

traci.close()
