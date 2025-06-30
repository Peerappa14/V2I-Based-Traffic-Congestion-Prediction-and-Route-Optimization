<div align="center">
  <h1>🚦 V2I-Based Traffic Congestion Prediction and Route Optimization</h1>
  <img src="docs/imgs/traffic_ai_logo.png" width="200" alt="Project Logo">
  
  [![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
  [![Simulation Tool: SUMO](https://img.shields.io/badge/SUMO-Traffic%20Simulator-blue)](https://www.eclipse.org/sumo/)
  [![TensorFlow](https://img.shields.io/badge/AI-Model%20(TensorFlow)-green)](https://www.tensorflow.org/)
</div>

---

## 📖 Overview

Urban traffic congestion causes serious problems like delays, fuel wastage, and pollution. This project leverages **Vehicle-to-Infrastructure (V2I)** communication and **LSTM-based AI prediction** to provide real-time congestion forecasting and route optimization.

It uses **SUMO** for traffic simulation and dynamically calculates the best paths using live and historical data. The system is visualized through an interactive **web-based GUI** and responds to traffic conditions in real-time.

---

## 🚗 Key Features

- Real-time traffic monitoring using **V2I communication**
- **AI model** (LSTM) to predict congestion patterns with ~90% accuracy
- **Dynamic rerouting** of vehicles using Dijkstra's algorithm
- Traffic simulation with **OpenStreetMap + SUMO**
- Interactive dashboard for monitoring live vehicle data, congestion stats, and rerouting
- Scalable and modular backend using Python + Flask

---

## 🧠 System Architecture

![Architecture](docs/imgs/architecture.png)

1. **Network Generation** – OpenStreetMap + SUMO
2. **V2I Communication** – Vehicle-to-RSU messaging via TraCI
3. **Real-Time Data Storage** – Stored in CSV and used for training
4. **AI Traffic Prediction** – LSTM model for time-series traffic forecasting
5. **Route Optimization** – Dijkstra's algorithm for dynamic rerouting
6. **Web Dashboard** – GUI interface for control and visualization

---

## 🛠️ Tech Stack

| Component         | Technology               |
|------------------|---------------------------|
| Programming Lang | Python 3.9+               |
| Simulation Tool  | SUMO + TraCI              |
| AI Framework     | TensorFlow (LSTM)         |
| Backend API      | Flask                     |
| Data Handling    | Pandas, NumPy             |
| Visualization    | Matplotlib + Tkinter GUI  |
| Routing Logic    | NetworkX (Graph Ops)      |
| Data Storage     | CSV, Real-time XML logs   |

---

## 📂 Project Structure

