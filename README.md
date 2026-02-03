# Smart Home Safety System

**Course:** Distributed and Internet of Things Software Architectures  
**Student:** Tulay Ece Yildirim (375660)  
**Academic Year:** 2025/2026

---

## 📋 Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
  - [Architecture Pattern](#architecture-pattern)
  - [Components](#components)
  - [Communication Protocols](#communication-protocols)
  - [Data Format](#data-format)
- [IoT Devices](#iot-devices)
- [Rule Engine](#rule-engine)
- [Installation](#installation)
- [Execution Instructions](#execution-instructions)
- [Demo Scenario](#demo-scenario)
- [REST API Reference](#rest-api-reference)
- [Project Structure](#project-structure)
- [Design Decisions & Justifications](#design-decisions--justifications)

---

## 🏠 Overview

This project implements an **automated smart home safety system** that monitors environmental conditions, detects hazardous situations, and triggers automatic protective responses. The system continuously collects data from distributed IoT sensors (door/window sensors, environmental monitors, utility meters), evaluates safety rules in real-time, and commands actuators (alarms, lights, sprinklers, utility shut-offs) to respond to detected threats.

### Key Features

- **Real-time threat detection:** Intrusion, fire, and gas leak detection through rule-based monitoring
- **Automatic response:** Autonomous activation of safety measures (alarms, sprinklers, utility shut-offs)
- **Distributed architecture:** Event-driven communication between independent IoT devices and central manager
- **REST API:** Query system status, configure thresholds, and manage devices
- **Event logging:** Complete audit trail of all safety rule activations

### Safety Scenarios

1. **Intrusion Detection:** When the system is armed and a door/window opens, the alarm sounds and lights turn on
2. **Fire Detection:** When temperature and PM10 levels exceed thresholds, the alarm sounds and sprinkler activates
3. **Gas Leak Detection:** When gas consumption spikes abnormally, the alarm sounds and gas supply shuts off

---

## 🏗️ System Architecture

### Architecture Pattern

The system implements a **Distributed Event-Driven Architecture** pattern, chosen for the following reasons:

- **Scalability:** New devices can be added without modifying the central manager
- **Loose coupling:** Devices operate independently and communicate through standard message protocols
- **Real-time responsiveness:** Event-driven processing enables immediate reaction to hazardous conditions
- **IoT best practices:** Aligns with industry standards for smart home and IoT system design

### Components

The system consists of three main architectural components:

#### 1. **IoT Devices (Emulated)**

Distributed sensor and actuator nodes that publish telemetry and respond to commands. Each device runs as an independent process and communicates via MQTT.

**Device Categories:**
- **Sensors:** Door/window sensors, environmental monitoring (temperature, PM10)
- **Actuators:** Alarm controller, alarm switch, sprinkler
- **Hybrid Devices:** Mobile light (actuator + energy sensor), utility meters (actuator + consumption sensor)

#### 2. **Data Collector & Manager (Backend Service)**

Central service responsible for:
- **Data Collection:** Subscribes to all device telemetry and state updates via MQTT
- **State Management:** Maintains latest readings from all devices
- **Rule Evaluation:** Continuously evaluates safety rules based on incoming data
- **Command Dispatch:** Publishes commands to actuators when rules trigger
- **REST API:** Exposes endpoints for status queries and configuration
- **Event Logging:** Records all rule activations with timestamps

#### 3. **Apps & Observers (Clients)**

External applications that interact with the manager through the REST API:
- Query system status and device states
- Configure safety thresholds
- Enable/disable rules
- Arm/disarm the system

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         OBSERVERS/APPS                          │
│                  (Postman, Web UI, Scripts)                     │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/REST
                             │ (Status queries, Configuration)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   DATA COLLECTOR & MANAGER                      │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐   │
│  │   FastAPI    │  │ Rule Engine  │  │  Device Registry   │   │
│  │  REST API    │  │ - Intrusion  │  │  & State Store     │   │
│  │              │  │ - Fire       │  │                    │   │
│  │              │  │ - Gas Leak   │  │                    │   │
│  └──────────────┘  └──────────────┘  └────────────────────┘   │
│                                                                 │
│                     MQTT Client (Paho)                          │
│              Subscribe: telemetry, state                        │
│              Publish: commands                                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ MQTT Broker (Mosquitto)
                             │ Topic: home/home_1/+/{telemetry,state,cmd}
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   SENSORS     │    │  ACTUATORS    │    │ HYBRID DEVICES│
├───────────────┤    ├───────────────┤    ├───────────────┤
│ • Door/Window │    │ • Alarm Ctrl  │    │ • Mobile Light│
│ • Environment │    │ • Alarm Switch│    │ • Gas Meter   │
│               │    │ • Sprinkler   │    │ • Elec. Meter │
│               │    │               │    │ • Water Meter │
└───────────────┘    └───────────────┘    └───────────────┘
  Publish:              Subscribe:          Publish:
  telemetry             cmd                 telemetry + state
                        Publish:            Subscribe:
                        state               cmd
```

### Communication Protocols

#### MQTT (Message Queue Telemetry Transport)

**Used for:** Device ↔ Manager communication

**Justification:**
- Lightweight and efficient for resource-constrained IoT devices
- Publish/Subscribe pattern enables loose coupling
- Quality of Service (QoS) levels for reliability
- Industry standard for IoT communication

**Topic Schema:**
```
home/<home_id>/<device_id>/<channel>
```
Where:
- `home_id`: Home identifier (e.g., "home_1")
- `device_id`: Unique device identifier (e.g., "door_1", "gas_meter")
- `channel`: Message type (`telemetry`, `state`, or `cmd`)

**Examples:**
- `home/home_1/door_1/telemetry` - Door sensor publishes open/closed state
- `home/home_1/alarm_controller/cmd` - Manager publishes command to alarm
- `home/home_1/mobile_light/state` - Light publishes actuator state

#### HTTP/REST (Representational State Transfer)

**Used for:** Observer/App ↔ Manager communication

**Justification:**
- Familiar and widely supported protocol
- Request/response pattern suitable for queries and configuration
- Stateless and cacheable
- Easy integration with web applications and tools like Postman

### Data Format

**JSON (JavaScript Object Notation)** is used for all message payloads in both MQTT and REST.

**Justification:**
- Human-readable and easy to debug
- Language-agnostic and widely supported
- Flexible schema for different device types
- Native support in FastAPI and paho-mqtt

**Message Envelope Structure:**
```json
{
  "ts": "2026-02-03T20:15:30.123456+00:00",
  "home_id": "home_1",
  "device_id": "door_1",
  "device_type": "door_window",
  "data": {
    "open": true
  }
}
```

**Command Structure:**
```json
{
  "ts_unix": 1738613730.123,
  "home_id": "home_1",
  "target_id": "alarm_controller",
  "action": "set",
  "params": {
    "on": true
  }
}
```

---

## 🔌 IoT Devices

### Sensor Devices

| Device | Type | Telemetry Fields | Description |
|--------|------|------------------|-------------|
| **door_1** | door_window | `open: bool` | Front door sensor - detects open/closed state |
| **window_1** | door_window | `open: bool` | Window sensor - detects open/closed state |
| **env_1** | environment | `temperature: float`<br>`pm10: float` | Environmental monitor - temperature (°C) and PM10 (μg/m³) |

### Actuator Devices

| Device | Type | Commands | State Fields | Description |
|--------|------|----------|--------------|-------------|
| **alarm_controller** | alarm_controller | `set(on: bool)` | `on: bool` | Siren/alarm control |
| **alarm_switch** | alarm_switch | `set(armed: bool)` | `armed: bool` | Arms/disarms security system |
| **sprinkler** | sprinkler | `set(on: bool)` | `on: bool` | Fire suppression sprinkler |

### Hybrid Devices (Sensor + Actuator)

| Device | Type | Telemetry Fields | Commands | State Fields | Description |
|--------|------|------------------|----------|--------------|-------------|
| **mobile_light** | mobile_light | `energy_kwh: float`<br>`on: bool`<br>`level: str` | `set(on: bool, level: str)` | `on: bool`<br>`level: str` | Smart light with energy monitoring |
| **gas_meter** | gas_meter | `total: float`<br>`delta: float`<br>`unit: str`<br>`supply_on: bool` | `set(supply_on: bool)` | `supply_on: bool` | Gas meter with shut-off valve |
| **electricity_meter** | electricity_meter | `total: float`<br>`delta: float`<br>`unit: str`<br>`supply_on: bool` | `set(supply_on: bool)` | `supply_on: bool` | Electricity meter with breaker |
| **water_meter** | water_meter | `total: float`<br>`delta: float`<br>`unit: str`<br>`supply_on: bool` | `set(supply_on: bool)` | `supply_on: bool` | Water meter with shut-off valve |

---

## ⚙️ Rule Engine

The system evaluates three safety rules continuously based on incoming telemetry:

### Rule 1: Intrusion Detection

**Condition:**
- System is armed (`armed == True`)
- Any door or window is open (`open == True`)

**Actions:**
1. Turn alarm ON
2. Turn mobile light ON at HIGH brightness

**Edge Detection:** Rule triggers only on state transition (False → True)  
**Cooldown:** 5 seconds (configurable)

### Rule 2: Fire Detection

**Condition:**
- Temperature ≥ threshold (default: 60.0°C)
- PM10 ≥ threshold (default: 150.0 μg/m³)

**Actions:**
1. Turn alarm ON
2. Turn sprinkler ON

**Edge Detection:** Rule triggers only on state transition (False → True)  
**Cooldown:** 5 seconds (configurable)

### Rule 3: Gas Leak Detection

**Condition:**
- Gas consumption delta ≥ minimum threshold (default: 0.1 kg)
- Current delta / previous delta ≥ spike ratio (default: 2.0)

**Actions:**
1. Turn alarm ON
2. Shut off gas supply (`supply_on = False`)

**Edge Detection:** Rule triggers only on state transition (False → True)  
**Cooldown:** 5 seconds (configurable)  
**Note:** Requires at least two gas readings to establish baseline

---

## 📦 Installation

### Prerequisites

- **Python 3.10+** (tested with Python 3.10)
- **MQTT Broker** (Mosquitto recommended)
- **pip** package manager

### Install Dependencies

```bash
pip install fastapi uvicorn[standard] paho-mqtt pydantic
```

Or create a `requirements.txt`:
```txt
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
paho-mqtt>=1.6.1
pydantic>=2.0.0
```

Install with:
```bash
pip install -r requirements.txt
```

### Install MQTT Broker (Mosquitto)

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install mosquitto mosquitto-clients
```

**macOS (Homebrew):**
```bash
brew install mosquitto
```

**Windows:**
Download from [https://mosquitto.org/download/](https://mosquitto.org/download/)

---

## 🚀 Execution Instructions

### Step 1: Start MQTT Broker

```bash
mosquitto -v
```

The broker will start on `127.0.0.1:1883` by default.

### Step 2: Start Data Collector & Manager

```bash
python -m src.manager
```

Or with uvicorn directly:
```bash
uvicorn src.manager:app --host 127.0.0.1 --port 8000
```

The REST API will be available at `http://127.0.0.1:8000`

**Verify startup:** Visit `http://127.0.0.1:8000/docs` for interactive API documentation

### Step 3: Start IoT Devices

Open separate terminal windows for each device:

#### Sensors

```bash
# Door sensor
python -m src.door_window --device-id door_1

# Window sensor
python -m src.door_window --device-id window_1

# Environmental monitor
python -m src.env_node --device-id env_1
```

#### Actuators

```bash
# Alarm controller
python -m src.actuators --device alarm_controller --device-id alarm_controller

# Alarm switch
python -m src.actuators --device alarm_switch --device-id alarm_switch

# Sprinkler
python -m src.actuators --device sprinkler --device-id sprinkler

# Mobile light
python -m src.actuators --device mobile_light --device-id mobile_light
```

#### Utility Meters

```bash
# Gas meter
python -m src.utility_meter --meter gas --device-id gas_meter

# Electricity meter
python -m src.utility_meter --meter electricity --device-id electricity_meter

# Water meter
python -m src.utility_meter --meter water --device-id water_meter
```

### Step 4: Monitor System Status

Query the REST API to view current state:

```bash
# Get complete system status
curl http://127.0.0.1:8000/status

# Get current configuration
curl http://127.0.0.1:8000/config

# Get device list
curl http://127.0.0.1:8000/devices
```

Or use the interactive API docs: `http://127.0.0.1:8000/docs`

---

## 🎬 Demo Scenario

### Automated Demo Script

The project includes a demo script that automatically triggers all three safety rules:

```bash
python -m src.demo_scenario
```

**What it does:**
1. Arms the system (via alarm_switch)
2. Opens door_1 to trigger **intrusion detection** → alarm + lights activate
3. Sends high temperature/PM10 to trigger **fire detection** → alarm + sprinkler activate
4. Sends gas consumption spike to trigger **gas leak detection** → alarm + gas shut-off

**Check results:**
- View triggered events: `cat outputs/events.log`
- Query system status: `curl http://127.0.0.1:8000/status`

### Manual Testing with REST API

#### Arm the System

```bash
curl -X PUT http://127.0.0.1:8000/config \
  -H "Content-Type: application/json" \
  -d '{"armed": true}'
```

#### Update Fire Thresholds

```bash
curl -X PUT http://127.0.0.1:8000/config \
  -H "Content-Type: application/json" \
  -d '{"temp_threshold": 50.0, "pm10_threshold": 100.0}'
```

#### Disable a Rule

```bash
curl -X PUT http://127.0.0.1:8000/config \
  -H "Content-Type: application/json" \
  -d '{"rule_intrusion_enabled": false}'
```

### Manual Testing with MQTT

You can also publish test messages directly via MQTT:

```bash
# Trigger intrusion (after arming)
mosquitto_pub -h 127.0.0.1 -t "home/home_1/door_1/telemetry" \
  -m '{"ts":"2026-02-03T20:00:00Z","home_id":"home_1","device_id":"door_1","device_type":"door_window","data":{"open":true}}'

# Trigger fire
mosquitto_pub -h 127.0.0.1 -t "home/home_1/env_1/telemetry" \
  -m '{"ts":"2026-02-03T20:00:00Z","home_id":"home_1","device_id":"env_1","device_type":"environment","data":{"temperature":80.0,"pm10":300.0}}'
```

---

## 📡 REST API Reference

### Get System Status

**Request:**
```http
GET /status
```

**Response:**
```json
{
  "home_id": "home_1",
  "config": {
    "armed": false,
    "temp_threshold": 60.0,
    "pm10_threshold": 150.0,
    "gas_spike_ratio": 2.0,
    "gas_min_delta": 0.1,
    "rule_intrusion_enabled": true,
    "rule_fire_enabled": true,
    "rule_gas_enabled": true,
    "cooldown_seconds": 5.0
  },
  "devices": { ... },
  "last_telemetry": { ... },
  "last_state": { ... }
}
```

### Get Configuration

**Request:**
```http
GET /config
```

**Response:**
```json
{
  "config": {
    "armed": false,
    "temp_threshold": 60.0,
    ...
  }
}
```

### Update Configuration

**Request:**
```http
PUT /config
Content-Type: application/json

{
  "armed": true,
  "temp_threshold": 50.0,
  "rule_fire_enabled": false
}
```

**Response:**
```json
{
  "ok": true,
  "config": { ... }
}
```

### List Devices

**Request:**
```http
GET /devices
```

**Response:**
```json
{
  "devices": {
    "door_1": {
      "device_id": "door_1",
      "device_type": "door_window",
      "kind": "sensor"
    },
    ...
  }
}
```

### Add Device

**Request:**
```http
POST /devices
Content-Type: application/json

{
  "device_id": "new_sensor",
  "device_type": "door_window",
  "kind": "sensor"
}
```

**Response:**
```json
{
  "ok": true,
  "device": { ... }
}
```

### Delete Device

**Request:**
```http
DELETE /devices/{device_id}
```

**Response:**
```json
{
  "ok": true
}
```

---

## 📁 Project Structure

```
smart-home-safety/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── outputs/                  # Auto-created by manager
│   └── events.log           # Event log (JSONL format)
├── src/                     # Source code package
│   ├── __init__.py          # Package marker
│   ├── models.py            # Data models and message utilities
│   ├── state.py             # Configuration, registry, state store
│   ├── rules.py             # Safety rule evaluation engine
│   ├── manager.py           # Data Collector & Manager (FastAPI + MQTT)
│   ├── door_window.py       # Door/window sensor emulator
│   ├── env_node.py          # Environmental sensor emulator
│   ├── utility_meter.py     # Utility meter emulator (gas/electricity/water)
│   ├── actuators.py         # Actuator emulators (alarm, switch, sprinkler, light)
│   └── demo_scenario.py     # Automated demo script
└── presentation/            # Project presentation materials
    └── slides.pdf           # Presentation slides
```

---

## 🎯 Design Decisions & Justifications

### 1. Architecture Pattern: Distributed Event-Driven

**Decision:** Adopt publish/subscribe event-driven architecture over client-server or layered architecture.

**Justification:**
- **Scalability:** Adding new devices requires no changes to existing components - they simply publish to new topics
- **Loose Coupling:** Devices are independent and unaware of each other, communicating only through the message broker
- **Real-time Processing:** Events are processed immediately as they occur, critical for safety applications
- **Fault Tolerance:** If one device fails, others continue operating normally
- **IoT Best Practice:** Aligns with industry standards (AWS IoT, Azure IoT Hub, Google Cloud IoT)

### 2. Protocol Selection: MQTT for Device Communication

**Decision:** Use MQTT instead of HTTP, CoAP, or custom protocols for device-to-manager communication.

**Justification:**
- **Lightweight:** Minimal overhead suitable for resource-constrained embedded devices
- **Bi-directional:** Supports both device→manager telemetry and manager→device commands
- **QoS Levels:** Provides configurable delivery guarantees (at most once, at least once, exactly once)
- **Persistent Connections:** Reduces connection overhead compared to HTTP polling
- **Industry Standard:** Widely adopted in IoT (Eclipse Paho, HiveMQ, Mosquitto)

### 3. Protocol Selection: REST for Application Interface

**Decision:** Use HTTP/REST instead of MQTT or WebSocket for application/observer interface.

**Justification:**
- **Ubiquitous Support:** Every programming language and platform supports HTTP
- **Stateless:** No connection management required, simplifies client implementation
- **Cacheable:** Responses can be cached to reduce load
- **Tooling:** Extensive ecosystem (Postman, curl, OpenAPI/Swagger)
- **Appropriate Pattern:** Request/response matches query and configuration use cases

### 4. Data Format: JSON

**Decision:** Use JSON instead of Protocol Buffers, MessagePack, or XML.

**Justification:**
- **Human Readable:** Easy to debug and inspect during development
- **Language Agnostic:** Native support in Python, JavaScript, and most modern languages
- **Flexible Schema:** Accommodates different device types without schema migration
- **Standard Support:** FastAPI serializes to JSON automatically, paho-mqtt handles JSON payloads efficiently

### 5. Edge Detection + Cooldown for Rules

**Decision:** Implement edge detection (trigger only on False→True transitions) with cooldown periods.

**Justification:**
- **Prevents Spam:** Avoids flooding the system with duplicate commands when conditions persist
- **State Management:** Tracks whether condition is active to detect transitions
- **Realistic Behavior:** Matches how physical safety systems operate (alarm doesn't continuously re-trigger)
- **Configurable:** Cooldown period can be adjusted based on application requirements

### 6. Special Alarm Switch Design

**Decision:** Alarm switch publishes telemetry (not state) to update manager's armed configuration.

**Justification:**
- **Bidirectional Control:** Allows both REST API and physical device to arm/disarm system
- **Centralized State:** Manager maintains single source of truth for armed status
- **User Experience:** Supports scenarios where user arms system via physical switch rather than app

### 7. Hybrid Device Pattern

**Decision:** Model utility meters and mobile light as hybrid sensor+actuator devices.

**Justification:**
- **Realistic Modeling:** Real-world smart meters report consumption AND control supply
- **State Correlation:** Actuator state (supply_on) directly affects sensor readings (consumption)
- **Efficient Communication:** Single device instance handles both telemetry and commands

### 8. Thread-Safe State Management

**Decision:** Use threading locks for StateStore and DeviceRegistry.

**Justification:**
- **Concurrency Safety:** MQTT callbacks and FastAPI endpoints run in separate threads
- **Data Integrity:** Prevents race conditions when multiple threads access shared state
- **Simple Model:** Locks are straightforward to reason about for this scale of application

### 9. Single Home Design

**Decision:** Hardcode `home_id = "home_1"` rather than supporting multiple homes.

**Justification:**
- **Project Scope:** Assignment focuses on device interaction and rule evaluation, not multi-tenancy
- **Simplicity:** Reduces complexity in demo and testing
- **Future Extension:** Architecture supports multi-home by parameterizing home_id

### 10. No Authentication/Authorization

**Decision:** Omit authentication and authorization mechanisms.

**Justification:**
- **Local Development:** System runs on localhost for demonstration purposes
- **Assignment Scope:** Security is not a primary evaluation criterion
- **Production Note:** Real deployment would add MQTT authentication (username/password or certificates) and REST API authentication (OAuth2, API keys)

---

## 🔍 Testing & Validation

### Functional Testing

All three safety rules have been tested and verified:

✅ **Intrusion Detection:** System correctly triggers alarm and lights when armed and door opens  
✅ **Fire Detection:** System correctly triggers alarm and sprinkler when temperature and PM10 exceed thresholds  
✅ **Gas Leak Detection:** System correctly triggers alarm and gas shut-off when consumption spikes  

### Edge Cases Verified

✅ Edge detection prevents duplicate triggers when conditions persist  
✅ Cooldown mechanism prevents command spam  
✅ Rule enable/disable flags work correctly  
✅ Gas spike requires baseline (minimum 2 readings)  
✅ Utility meters stop consumption when supply is off  

### System Integration

✅ All 10 devices communicate successfully with manager via MQTT  
✅ REST API endpoints return correct data  
✅ Event logging captures all rule activations  
✅ Configuration updates apply immediately  

---

## 📊 Monitoring & Observability

### Event Log

All rule activations are logged to `outputs/events.log` in JSONL format:

```json
{"rule": "intrusion", "ts_unix": 1738613730.123, "actions": [...]}
{"rule": "fire", "ts_unix": 1738613733.456, "actions": [...]}
{"rule": "gas_spike", "ts_unix": 1738613738.789, "actions": [...]}
```

### Real-time Status

Query `/status` endpoint to view:
- Current configuration (armed state, thresholds, rule toggles)
- All registered devices
- Latest telemetry from each sensor
- Latest state from each actuator

### MQTT Monitoring

Monitor MQTT traffic using mosquitto_sub:

```bash
# Monitor all telemetry
mosquitto_sub -h 127.0.0.1 -t "home/home_1/+/telemetry" -v

# Monitor all commands
mosquitto_sub -h 127.0.0.1 -t "home/home_1/+/cmd" -v

# Monitor all state updates
mosquitto_sub -h 127.0.0.1 -t "home/home_1/+/state" -v
```

---

## 🚧 Known Limitations & Future Enhancements

### Current Limitations

- **Single Home:** System supports only one home (home_1)
- **No Persistence:** State is lost on manager restart (in-memory only)
- **No Authentication:** MQTT and REST API are unsecured
- **No GUI:** Interaction requires REST API or MQTT clients
- **Local Only:** No remote access or cloud integration

### Potential Enhancements

- **Multi-Home Support:** Allow multiple homes with isolated device namespaces
- **Persistent Storage:** Add database (PostgreSQL, MongoDB) for state and event history
- **Web Dashboard:** Real-time visualization of device states and events
- **Mobile App:** Native iOS/Android app for system control
- **Cloud Integration:** Connect to AWS IoT Core or Azure IoT Hub
- **Machine Learning:** Anomaly detection for unusual consumption patterns
- **Voice Control:** Integration with Amazon Alexa or Google Home
- **Historical Analytics:** Trend analysis and reporting on consumption and events

---

## 📄 License

This project is developed as coursework for the Distributed and Internet of Things Software Architectures course at the University of Modena and Reggio Emilia.

---

## 👤 Author

**Tulay Ece Yildirim**  
Student ID: 375660  
Email: 375660@studenti.unimore.it

---

## 🙏 Acknowledgments

- Course instructors and teaching assistants
- Eclipse Paho MQTT project
- FastAPI framework developers
- Open source community

---

**Last Updated:** February 3, 2026
