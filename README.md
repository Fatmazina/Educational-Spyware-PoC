# 🛡️ Educational Spyware: Installer Telemetry (Academic PoC)

> **⚠️ ETHICAL DISCLAIMER:** This project was developed strictly for **educational and academic purposes** to study endpoint security, data exfiltration mechanics, and defensive monitoring. It is a Proof of Concept (PoC) and is not intended for malicious use or deployment on unauthorized systems.

## 📖 Overview
This project is an academic simulation of spyware telemetry. Unlike a full Command and Control (C2) framework, this agent is designed for **passive data collection**. It triggers only upon execution (e.g., when a user opens the installer), gathers specific system metrics, and securely transmits them to a centralized Flask dashboard for analysis.

## 🛠️ Tech Stack
- **Client Agent:** Python 3, `requests`, `psutil` (or your actual libraries)
- **Server Backend:** Python, Flask
- **Frontend Dashboard:** HTML5, CSS3, JavaScript, Bootstrap
- **Environment:** Kali Linux / Virtualized Testing Environments

## 🚀 Features
- **Passive Execution:** Collects data immediately upon client execution without requiring persistent background C2 communication.
- **Centralized Dashboard:** Real-time web interface to view incoming telemetry data.
- **Modular Design:** Client and server are decoupled, making it easy to study network traffic and HTTP POST behaviors.
- *(Add 1-2 specific things it spies on, e.g., "Captures system info, screenshots, or keystroke logs locally before transmission")*

## 🏗️ Architecture
1. **Client (`client/`)**: The "installer" payload. Runs once, gathers predefined data, and sends an HTTP POST request to the server.
2. **Server (`server/` & `dashboard.py`)**: Listens for incoming POST requests, logs the data, and serves the visualization dashboard.

## 🎓 Learning Outcomes
Through this project, I gained hands-on experience with:
- Understanding the lifecycle and execution flow of spyware/telemetry agents.
- Building secure(ish) HTTP data exfiltration simulations.
- Developing a Flask-based backend to ingest and display endpoint data.
- The importance of `.gitignore` and operational security (OpSec) in handling sensitive captured data.