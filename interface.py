# [Same imports and global variables — unchanged]
import tkinter as tk
from tkinter import ttk, messagebox
import traci
import threading
from tensorflow.keras.models import load_model
import sumolib
import xml.etree.ElementTree as ET
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Global variables
vehicles_data = {}
congested_edges = set()
rerouted_vehicles = {}
rerouted_vehicle_ids = set()
edges = []
graph = nx.DiGraph()
vehicle_routes = {}
selected_destination = None
congestion_history = []
rerouted_history = []
latest_rerouted_vehicle = None

# SUMO Network Parsing
net = sumolib.net.readNet("osm.net.xml")
canvas_width = 900
canvas_height = 600
min_x, min_y, max_x, max_y = net.getBoundary()


# --- AI Model Integration Placeholder ---
# This code integrates an AI model for congestion prediction (not used in current logic)

def load_ai_model():
   
    try:
        model = load_model("lstm_traffic_model.h5")
        print("AI model loaded successfully (integration placeholder).")
    except Exception as e:
        print(f"AI model not found or failed to load (this does not affect simulation): {e}")


def scale(x, y):
    sx = (x - min_x) / (max_x - min_x) * canvas_width
    sy = canvas_height - (y - min_y) / (max_y - min_y) * canvas_height
    return sx, sy

def parse_netxml(filename="osm.net.xml"):
    global edges, graph, selected_destination
    tree = ET.parse(filename)
    root = tree.getroot()
    edges = [e.get("id") for e in root.findall(".//edge") if e.get("id") and not e.get("function")]
    if edges:
        selected_destination = edges[-1]
    for edge in net.getEdges():
        if edge.getFromNode() and edge.getToNode():
            graph.add_edge(edge.getFromNode().getID(), edge.getToNode().getID(), weight=edge.getLength())

def parse_route_files():
    global vehicle_routes
    route_files = [
        "osm.bicycle.trips.xml", "osm.bus.trips.xml", "osm.motorcycle.trips.xml",
        "osm.passenger.trips.xml", "osm.pedestrian.rou.xml", "osm.truck.trips.xml"
    ]
    for route_file in route_files:
        tree = ET.parse(route_file)
        root = tree.getroot()
        for trip in root.findall(".//trip"):
            veh_id = trip.get("id")
            from_edge = trip.get("from")
            to_edge = trip.get("to")
            vehicle_routes[veh_id] = (from_edge, to_edge)

def start_sumo():
    sumo_cmd = ["sumo-gui", "-c", "osm.sumocfg", "--start"]
    traci.start(sumo_cmd)
    monitor_traffic()

def stop_sumo():
    try:
        traci.close()
        messagebox.showinfo("SUMO Stopped", "SUMO simulation has been stopped.")
    except traci.exceptions.FatalTraCIError:
        messagebox.showerror("Error", "SUMO is not running.")

def monitor_traffic():
    try:
        traci.simulationStep()
        detect_congestion()
        update_vehicle_data()
        update_ui()
        update_combined_graph()
        update_rerouting_pie_chart()
        root.after(500, monitor_traffic)
    except traci.exceptions.FatalTraCIError:
        messagebox.showerror("Error", "TraCI not connected! Restart SUMO.")
    except Exception as e:
        messagebox.showerror("Error", f"Simulation error: {e}")

def detect_congestion():
    global congested_edges
    congested_edges.clear()
    for edge in edges:
        count = traci.edge.getLastStepVehicleNumber(edge)
        speed = traci.edge.getLastStepMeanSpeed(edge)
        wait = sum(traci.vehicle.getWaitingTime(v) for v in traci.edge.getLastStepVehicleIDs(edge)) / max(count, 1)
        if (count > 5 and speed < 5.0) or wait > 10:
            congested_edges.add(edge)

def update_vehicle_data():
    global vehicles_data
    new_data = {}
    for vehicle_id in traci.vehicle.getIDList():
        speed = traci.vehicle.getSpeed(vehicle_id)
        edge = traci.vehicle.getRoadID(vehicle_id)
        new_data[vehicle_id] = (speed, edge)
        if edge in congested_edges:
            reroute_vehicle(vehicle_id)
    vehicles_data.clear()
    vehicles_data.update(new_data)

def find_shortest_path(source_edge, dest_edge):
    try:
        if source_edge not in edges or dest_edge not in edges:
            return None
        source_node = net.getEdge(source_edge).getFromNode().getID()
        dest_node = net.getEdge(dest_edge).getFromNode().getID()
        if source_node in graph and dest_node in graph:
            node_path = nx.shortest_path(graph, source=source_node, target=dest_node, weight="weight")
            edge_path = []
            for i in range(len(node_path) - 1):
                for edge in net.getEdges():
                    if edge.getFromNode().getID() == node_path[i] and edge.getToNode().getID() == node_path[i + 1]:
                        edge_path.append(edge.getID())
            if source_edge not in edge_path:
                edge_path.insert(0, source_edge)
            return edge_path
    except Exception:
        return None

def reroute_vehicle(vehicle_id):
    global latest_rerouted_vehicle
    current_edge = traci.vehicle.getRoadID(vehicle_id)
    if vehicle_id in rerouted_vehicles:
        return
    if current_edge in congested_edges and selected_destination:
        new_path = find_shortest_path(current_edge, selected_destination)
        if new_path:
            traci.vehicle.changeTarget(vehicle_id, new_path[-1])
            old_route = traci.vehicle.getRoute(vehicle_id)
            rerouted_vehicles[vehicle_id] = {"old": old_route, "new": new_path}
            rerouted_vehicle_ids.add(vehicle_id)
            latest_rerouted_vehicle = vehicle_id

def update_ui():
    update_vehicle_table()
    update_congestion_table()
    update_rerouted_table()

def update_vehicle_table():
    vehicle_table.delete(*vehicle_table.get_children())
    for vehicle_id, (speed, edge) in vehicles_data.copy().items():
        vehicle_table.insert("", "end", values=(vehicle_id, edge, f"{speed:.2f} m/s"))

def update_congestion_table():
    congestion_table.delete(*congestion_table.get_children())
    for edge in congested_edges:
        congestion_table.insert("", "end", values=(edge, "⚠️ Congested"))

def update_rerouted_table():
    rerouted_table.delete(*rerouted_table.get_children())
    for vehicle_id, paths in rerouted_vehicles.items():
        old_route = " → ".join(paths["old"])
        new_route = " → ".join(paths["new"])
        rerouted_table.insert("", "end", values=(vehicle_id, old_route, new_route))

def open_combined_graph():
    global graph_window, fig, ax, canvas
    graph_window = tk.Toplevel(root)
    graph_window.title("Congestion and Rerouted Vehicles Over Time")
    graph_window.geometry("900x500")
    fig, ax = plt.subplots(figsize=(8.5, 4))
    canvas = FigureCanvasTkAgg(fig, master=graph_window)
    canvas.get_tk_widget().pack()
    ax.set_title("Network Stats Over Time")
    ax.set_xlabel("Timestep")
    ax.set_ylabel("Count")
    ax.grid(True)
    ax.legend(["Congested Edges", "Rerouted Vehicles"])

def update_combined_graph():
    if 'ax' in globals():
        congestion_history.append(len(congested_edges))
        rerouted_history.append(len(rerouted_vehicle_ids))  # cumulative count
        ax.clear()
        ax.plot(congestion_history, color='red', label="Congested Edges", linewidth=2)
        ax.plot(rerouted_history, color='blue', label="Rerouted Vehicles", linewidth=2)
        ax.set_title("Network Stats Over Time")
        ax.set_xlabel("Timestep")
        ax.set_ylabel("Count")
        ax.legend()
        ax.grid(True)
        canvas.draw()

def open_rerouting_pie_chart_window():
    global pie_window, pie_fig, pie_ax, pie_canvas
    pie_window = tk.Toplevel(root)
    pie_window.title("Rerouting Statistics")
    pie_window.geometry("500x400")
    pie_fig, pie_ax = plt.subplots(figsize=(5, 4))
    pie_canvas = FigureCanvasTkAgg(pie_fig, master=pie_window)
    pie_canvas.get_tk_widget().pack()

def update_rerouting_pie_chart():
    if 'pie_ax' in globals():
        total = len(vehicles_data)
        rerouted = len(rerouted_vehicles)
        non_rerouted = max(total - rerouted, 0)
        pie_ax.clear()
        pie_ax.pie([rerouted, non_rerouted], labels=["Rerouted", "Not Rerouted"],
                   colors=["#FF6347", "#90EE90"], autopct="%1.1f%%", startangle=90)
        pie_ax.set_title("Rerouting Distribution")
        pie_canvas.draw()

def open_network_canvas():
    global network_window, network_canvas
    network_window = tk.Toplevel(root)
    network_window.title("SUMO Network Visualization")
    network_window.geometry(f"{canvas_width}x{canvas_height}")
    network_canvas = tk.Canvas(network_window, bg="white", width=canvas_width, height=canvas_height)
    network_canvas.pack(fill="both", expand=True)
    real_time_network_canvas_update()

def real_time_network_canvas_update():
    if network_canvas:
        network_canvas.delete("all")
        for edge in net.getEdges():
            shape = edge.getShape()
            if len(shape) >= 2:
                edge_id = edge.getID()
                try:
                    speed = traci.edge.getLastStepMeanSpeed(edge_id)
                    count = traci.edge.getLastStepVehicleNumber(edge_id)
                    wait = sum(traci.vehicle.getWaitingTime(v) for v in traci.edge.getLastStepVehicleIDs(edge_id)) / max(count, 1)
                    color = "gray"
                    if (count > 5 and speed < 5) or wait > 10:
                        color = "red"
                    elif count > 2:
                        color = "yellow"
                    else:
                        color = "green"
                except:
                    color = "gray"
                for i in range(len(shape) - 1):
                    x1, y1 = scale(*shape[i])
                    x2, y2 = scale(*shape[i + 1])
                    network_canvas.create_line(x1, y1, x2, y2, fill=color, width=2)

        if latest_rerouted_vehicle and latest_rerouted_vehicle in rerouted_vehicles:
            paths = rerouted_vehicles[latest_rerouted_vehicle]
            for route_type, clr in [("old", "black"), ("new", "blue")]:
                for edge_id in paths[route_type]:
                    try:
                        edge = net.getEdge(edge_id)
                        shape = edge.getShape()
                        for i in range(len(shape) - 1):
                            x1, y1 = scale(*shape[i])
                            x2, y2 = scale(*shape[i + 1])
                            network_canvas.create_line(x1, y1, x2, y2, fill=clr, width=3)
                    except:
                        continue
            try:
                x, y = traci.vehicle.getPosition(latest_rerouted_vehicle)
                sx, sy = scale(x, y)
                network_canvas.create_oval(sx - 5, sy - 5, sx + 5, sy + 5, fill="orange")
                network_canvas.create_text(sx + 10, sy, text=latest_rerouted_vehicle, anchor="w",
                                           font=("Helvetica", 10, "bold"), fill="darkblue")
            except:
                pass
        network_canvas.after(1000, real_time_network_canvas_update)

# ------------ MAIN UI ----------------
parse_netxml()
parse_route_files()

root = tk.Tk()
root.title("Traffic Congestion & V2I Interface")
root.geometry("1100x900")
root.configure(bg="#f0f0f5")

style = ttk.Style()
style.configure("Treeview.Heading", font=("Helvetica", 11, "bold"))
style.configure("Treeview", font=("Helvetica", 10))

tk.Label(root, text="V2I-based Real-Time Traffic Monitoring", font=("Helvetica", 18, "bold"),
         bg="#f0f0f5", fg="#003366").pack(pady=20)

btn_frame = tk.Frame(root, bg="#f0f0f5")
btn_frame.pack(pady=10)

tk.Button(btn_frame, text="▶ Start Simulation", command=start_sumo, bg="#28a745", fg="white",
          font=("Helvetica", 11, "bold")).grid(row=0, column=0, padx=10)
tk.Button(btn_frame, text="■ Stop Simulation", command=stop_sumo, bg="#dc3545", fg="white",
          font=("Helvetica", 11, "bold")).grid(row=0, column=1, padx=10)
tk.Button(btn_frame, text="📊 Show Graphs", command=open_combined_graph, bg="#6f42c1", fg="white",
          font=("Helvetica", 11, "bold")).grid(row=0, column=2, padx=10)
tk.Button(btn_frame, text="🌐 Open Network", command=open_network_canvas, bg="#007bff", fg="white",
          font=("Helvetica", 11, "bold")).grid(row=0, column=3, padx=10)
tk.Button(btn_frame, text="📈 Show Rerouting Stats", command=open_rerouting_pie_chart_window, bg="#ff8800",
          fg="white", font=("Helvetica", 11, "bold")).grid(row=0, column=4, padx=10)

tk.Label(root, text="Live Vehicle Data", font=("Helvetica", 14, "bold"), bg="#f0f0f5").pack(pady=(20, 5))
vehicle_table = ttk.Treeview(root, columns=("Vehicle ID", "Current Edge", "Speed"), show="headings", height=5)
vehicle_table.heading("Vehicle ID", text="Vehicle ID")
vehicle_table.heading("Current Edge", text="Current Edge")
vehicle_table.heading("Speed", text="Speed (m/s)")
vehicle_table.pack(fill="both", padx=20)

tk.Label(root, text="Congested Edges", font=("Helvetica", 14, "bold"), bg="#f0f0f5").pack(pady=(20, 5))
congestion_table = ttk.Treeview(root, columns=("Edge", "Status"), show="headings", height=4)
congestion_table.heading("Edge", text="Edge")
congestion_table.heading("Status", text="Status")
congestion_table.pack(fill="both", padx=20)

tk.Label(root, text="Rerouted Vehicles", font=("Helvetica", 14, "bold"), bg="#f0f0f5").pack(pady=(20, 5))
rerouted_table = ttk.Treeview(root, columns=("Vehicle ID", "Old Route", "New Route"), show="headings", height=5)
rerouted_table.heading("Vehicle ID", text="Vehicle ID")
rerouted_table.heading("Old Route", text="Old Route")
rerouted_table.heading("New Route", text="New Route")
rerouted_table.pack(fill="both", padx=20)

root.mainloop()