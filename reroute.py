import traci
import random

def check_congestion(edge_id, threshold=5):
    """Check if an edge is congested based on the number of vehicles."""
    vehicle_count = sum(1 for v in traci.vehicle.getIDList() if traci.vehicle.getRoadID(v) == edge_id)
    return vehicle_count > threshold

def find_alternate_route(source, destination):
    """Find an alternative shortest path if congestion is detected."""
    edges = traci.edge.getIDList()
    alternate_paths = [edge for edge in edges if edge != source and edge != destination]
    return random.choice(alternate_paths) if alternate_paths else destination

def reroute_vehicle(vehicle_id, source, destination):
    """Reroute the vehicle based on congestion detection."""
    if check_congestion(source):
        new_route = find_alternate_route(source, destination)
        traci.vehicle.changeTarget(vehicle_id, new_route)
        return new_route
    return destination
