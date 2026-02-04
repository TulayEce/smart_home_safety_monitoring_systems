# Smart Home Safety System

**Course:** Distributed and Internet of Things Software Architectures  
**Student:** Tulay Ece Yildirim (375660)  
**Academic Year:** Fall_2025/2026

---

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [IoT Devices](#iot-devices)
- [Rule Engine](#rule-engine)
- [Installation](#installation)
- [Execution](#execution)
- [REST API](#rest-api)
- [Project Structure](#project-structure)

---

## Overview

This project implements an automated smart home safety system that monitors environmental conditions, detects hazardous situations, and triggers protective responses. The system collects data from distributed IoT sensors, evaluates safety rules in real-time, and commands actuators to respond to detected threats.

**Core Functionality:**
- Real-time monitoring of intrusion, fire, and gas leak conditions
- Autonomous activation of safety measures (alarms, sprinklers, utility shut-offs)
- Event-driven communication between independent IoT devices
- REST API for status queries and configuration management
- Complete audit trail of safety events

**Safety Scenarios:**
1. **Intrusion:** Armed system + door/window open → alarm + lights
2. **Fire:** High temperature + PM10 levels → alarm + sprinkler
3. **Gas Leak:** Abnormal consumption spike → alarm + gas shutoff

---

## System Architecture

**Pattern:** Distributed Event-Driven Architecture

**Justification:**
- Scalability: Add devices without modifying central manager
- Loose coupling: Devices communicate through message broker
- Real-time responsiveness: Event-driven processing for immediate reaction
- Industry alignment: Follows AWS IoT, Azure IoT Hub best practices

**Components:**

1. **IoT Devices** - Distributed sensors and actuators publishing telemetry via MQTT
2. **Manager** - Central service for data collection, rule evaluation, and command dispatch
3. **Observers** - External applications querying system via REST API

**Architecture Diagram:**

```
┌──────────────────────────────┐
│     Observers & Apps         │
│  (Postman, Web UI, cURL)     │
└──────────────┬───────────────┘
               │ HTTP/REST
               ▼
┌──────────────────────────────┐
│  Data Collector & Manager    │
│   - FastAPI (REST API)       │
│   - MQTT Client              │
│   - Rule Engine              │
│   - Device Registry          │
│   - State Store              │
└──────────────┬───────────────┘
               │ MQTT Broker
               ▼
┌─────────┬──────────┬─────────┐
│ Sensors │Actuators │ Hybrid  │
│ (3)     │  (4)     │ Devices │
│         │          │  (3)    │
└─────────┴──────────┴─────────┘
```

**Communication Protocols:**

| Protocol | Usage | Justification |
|----------|-------|---------------|
| **MQTT** | Device ↔ Manager | Lightweight, pub/sub pattern, persistent connections, IoT standard |
| **HTTP/REST** | Observer ↔ Manager | Ubiquitous, stateless, cacheable, easy integration |

**Data Format:** JSON (human-readable, language-agnostic, native FastAPI support)

**MQTT Topic Structure:**
```
home/<home_id>/<device_id>/{telemetry|state|cmd}
```

---

## IoT Devices

**Total Devices:** 10 emulated devices across 3 categories

### Sensors (3 devices)

| Device | Telemetry | Description |
|--------|-----------|-------------|
| door_1 | open: bool | Front door sensor |
| window_1 | open: bool | Window sensor |
| env_1 | temperature: float, pm10: float | Environmental monitor |

### Actuators (4 devices)

| Device | Commands | Description |
|--------|----------|-------------|
| alarm_controller | set(on: bool) | Siren/alarm control |
| alarm_switch | set(armed: bool) | System arm/disarm |
| sprinkler | set(on: bool) | Fire suppression |
| mobile_light | set(on: bool, level: str) | Smart light |

### Hybrid Devices (3 devices)

| Device | Telemetry | Commands | Description |
|--------|-----------|----------|-------------|
| gas_meter | total, delta, supply_on | set(supply_on: bool) | Gas meter with shutoff |
| electricity_meter | total, delta, supply_on | set(supply_on: bool) | Electricity meter |
| water_meter | total, delta, supply_on | set(supply_on: bool) | Water meter |

---

## Rule Engine

The manager evaluates three safety rules based on incoming telemetry. Each rule implements **edge detection** (triggers only on False→True transition) and has a **5-second cooldown** to prevent command spam.

### Rule 1: Intrusion Detection

**Condition:** `armed == True AND door/window open == True`  
**Actions:** Alarm ON, Light ON (HIGH)

### Rule 2: Fire Detection

**Condition:** `temperature ≥ 60°C AND pm10 ≥ 150 μg/m³`  
**Actions:** Alarm ON, Sprinkler ON

### Rule 3: Gas Leak Detection

**Condition:** `gas_delta ≥ 0.1 kg AND (current_delta / prev_delta) ≥ 2.0`  
**Actions:** Alarm ON, Gas supply OFF

**Thresholds:** Configurable via `/config` endpoint (see REST API)

**Event Logging:** All rule activations logged to `outputs/events.log` in JSONL format

---

## Installation

**Prerequisites:**
- Python 3.10+
- MQTT Broker (Mosquitto)

**Install Dependencies:**

```bash
pip install fastapi uvicorn[standard] paho-mqtt pydantic
```

**Install Mosquitto:**

```bash
# Ubuntu/Debian
sudo apt-get install mosquitto mosquitto-clients

# macOS
brew install mosquitto

# Windows: Download from https://mosquitto.org/download/
```

---

## Execution

### Start System

**Terminal 1 - MQTT Broker:**
```bash
mosquitto -v
```

**Terminal 2 - Manager:**
```bash
python -m src.manager
```
API available at: `http://127.0.0.1:8000`

**Terminal 3+ - Devices:**
```bash
# Sensors
python -m src.devices.door_window --device-id door_1
python -m src.devices.env_node --device-id env_1

# Actuators
python -m src.devices.actuators --device alarm_controller --device-id alarm_controller
python -m src.devices.actuators --device alarm_switch --device-id alarm_switch

# Meters
python -m src.devices.utility_meter --meter gas --device-id gas_meter
```

### Run Demo Scenario

The demo script automatically triggers all three safety rules:

```bash
python -m src.devices.demo_scenario
```

**Demo Actions:**
1. Arms system → opens door → triggers intrusion rule
2. Sends high temp/PM10 → triggers fire rule
3. Sends gas spike → triggers gas leak rule

**Verify Results:**
```bash
curl http://127.0.0.1:8000/status
cat outputs/events.log
```

---

## REST API

Base URL: `http://127.0.0.1:8000`

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/status` | GET | Complete system snapshot (config, devices, telemetry, state) |
| `/config` | GET | Retrieve current configuration (thresholds, rules enabled) |
| `/config` | PUT | Update configuration (armed state, thresholds) |
| `/devices` | GET | List all registered devices |
| `/devices` | POST | Register new device |
| `/devices/{id}` | DELETE | Remove device from registry |

### Example: Query Status

```bash
curl http://127.0.0.1:8000/status
```

Response:
```json
{
  "home_id": "home_1",
  "config": {
    "armed": false,
    "temp_threshold": 60.0,
    "pm10_threshold": 150.0,
    ...
  },
  "devices": {...},
  "last_telemetry": {...},
  "last_state": {...}
}
```

### Example: Update Configuration

```bash
curl -X PUT http://127.0.0.1:8000/config \
  -H "Content-Type: application/json" \
  -d '{"armed": true, "temp_threshold": 55.0}'
```

**Interactive Documentation:** Visit `http://127.0.0.1:8000/docs` for Swagger UI

---

## Project Structure

```
smart_home_safety_monitoring_systems/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── .gitignore                   # Git ignore rules
├── outputs/
│   └── events.log              # Runtime event log (JSONL)
├── presentation/
│   └── Smart_Home_Safety_System_Presentation.pptx
└── src/
    ├── __init__.py
    ├── models.py               # Pydantic data models
    ├── state.py                # State management (Config, Registry, Logger)
    ├── rules.py                # Rule evaluation logic
    ├── manager.py              # FastAPI application & MQTT client
    └── devices/
        ├── __init__.py
        ├── door_window.py      # Door/window sensor
        ├── env_node.py         # Environmental sensor
        ├── actuators.py        # Alarm, switch, sprinkler, light
        ├── utility_meter.py    # Gas/electricity/water meters
        └── demo_scenario.py    # Automated demo script
```

**Code Metrics:**
- Total lines: 950+ (excluding comments/blanks)
- Modules: 9 Python files
- Devices: 10 emulated IoT devices

---

## Design Decisions

### Architectural Choices

**Event-Driven vs Request-Response:**
- Selected event-driven for real-time safety requirements
- Devices publish autonomously; manager reacts immediately
- Alternative (polling) would introduce unacceptable latency

**MQTT vs HTTP for Device Communication:**
- MQTT chosen for persistent connections and pub/sub pattern
- Reduces network overhead compared to HTTP polling
- Industry standard for IoT (AWS IoT Core, Azure IoT Hub)

**Monolithic Manager vs Microservices:**
- Single manager appropriate for scope (one home, 10 devices)
- Simplifies deployment and testing
- Scalable to microservices if expanding to multi-home scenarios

### Implementation Choices

**Edge Detection:**
- Rules trigger only on False→True state transitions
- Prevents duplicate activations during persistent conditions
- Example: Temperature stays at 70°C → alarm triggered once, not continuously

**Cooldown Period:**
- 5-second buffer prevents command spam
- Allows actuators time to respond before re-evaluation
- Configurable per-rule if needed

**Alarm Switch via Telemetry:**
- Alarm switch publishes armed state as telemetry (not just state)
- Enables bidirectional control (manual toggle + remote command)
- Demonstrates hybrid device pattern

**Thread-Safe State Management:**
- Manager maintains global state with thread locks
- Ensures consistency across concurrent MQTT callbacks and HTTP requests
- Critical for multi-threaded FastAPI/Uvicorn environment

**Single-Home Design:**
- Current implementation supports one home (`home_1`)
- Extensible to multi-home by parameterizing home_id
- Scoped to assignment requirements (one smart home system)

---

## Testing

**Manual Testing:**
1. Start all components (broker, manager, devices)
2. Arm system: `curl -X PUT http://127.0.0.1:8000/config -d '{"armed": true}'`
3. Open door: Observe intrusion rule trigger
4. Check logs: `cat outputs/events.log`

**Automated Testing:**
- Run demo scenario: `python -m src.devices.demo_scenario`
- Verifies all three rules activate correctly
- Logs should show 3 events (intrusion, fire, gas_spike)

---

## References

- Eclipse Paho MQTT: https://eclipse.dev/paho/index.php?page=clients/python/index.php
- FastAPI Documentation: https://fastapi.tiangolo.com/
- MQTT Protocol Specification: https://mqtt.org/mqtt-specification/
- AWS IoT Best Practices: https://docs.aws.amazon.com/iot/latest/developerguide/

---

**Project Repository:** https://github.com/TulayEce/smart_home_safety_monitoring_systems
