from __future__ import annotations

import json
import time
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import paho.mqtt.client as mqtt

from .models import DeviceInfo, topic, wildcard_state, wildcard_telemetry
from .rules import evaluate_rules
from .state import Config, DeviceRegistry, EventLogger, StateStore


# -----------------------------
# Runtime defaults 
# -----------------------------
HOME_ID = "home_1"
BROKER_HOST = "127.0.0.1"
BROKER_PORT = 1883

LOG_PATH = "outputs/events.log"


app = FastAPI(title="Smart Home Safety Manager (MQTT + Minimal REST)")

cfg = Config()
registry = DeviceRegistry()
store = StateStore()
logger = EventLogger(LOG_PATH)

mqtt_client: Optional[mqtt.Client] = None


# -----------------------------
# REST Schemas (minimal CRUD)
# -----------------------------
class DeviceIn(BaseModel):
    device_id: str
    device_type: str
    kind: str  # sensor|actuator|hybrid


class ConfigIn(BaseModel):
    armed: Optional[bool] = None
    temp_threshold: Optional[float] = None
    pm10_threshold: Optional[float] = None
    gas_spike_ratio: Optional[float] = None
    gas_min_delta: Optional[float] = None

    rule_intrusion_enabled: Optional[bool] = None
    rule_fire_enabled: Optional[bool] = None
    rule_gas_enabled: Optional[bool] = None


# -----------------------------
# MQTT helpers
# -----------------------------
def _publish_cmd(cmd_target: str, action: str, params: Dict[str, Any]) -> None:
    global mqtt_client
    if mqtt_client is None:
        return

    payload = {
        "ts_unix": time.time(),
        "home_id": HOME_ID,
        "target_id": cmd_target,
        "action": action,
        "params": params,
    }
    mqtt_client.publish(topic(HOME_ID, cmd_target, "cmd"), json.dumps(payload), qos=0, retain=False)


def _handle_incoming_message(channel: str, data: Dict[str, Any]) -> None:
    """
    Update last-state + evaluate rules + dispatch commands.
    This is the "Data Collector & Manager" core.
    """
    device_id = data.get("device_id")
    if not device_id:
        return

    if channel == "telemetry":
        store.update_telemetry(device_id, data)
    elif channel == "state":
        store.update_state(device_id, data)

    # Allow Alarm Switch device to arm/disarm by publishing state/telemetry
    if data.get("device_type") == "alarm_switch":
        d = data.get("data", {})
        if isinstance(d, dict) and "armed" in d:
            cfg.armed = bool(d["armed"])

    commands, events = evaluate_rules(store, cfg)

    for e in events:
        logger.log(e)

    for c in commands:
        _publish_cmd(c.target_id, c.action, c.params)


def _on_message(_client, _userdata, msg: mqtt.MQTTMessage) -> None:
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
    except Exception:
        return

    # Topic format: home/<home_id>/<device_id>/<channel>
    parts = msg.topic.split("/")
    if len(parts) < 4:
        return
    channel = parts[-1]
    if channel not in ("telemetry", "state"):
        return

    _handle_incoming_message(channel, payload)


@app.on_event("startup")
def on_startup() -> None:
    """
    Connect to MQTT broker and subscribe to:
      - all telemetry
      - all actuator states
    """
    global mqtt_client
    mqtt_client = mqtt.Client(client_id="manager", clean_session=True)
    mqtt_client.on_message = _on_message
    mqtt_client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)

    mqtt_client.subscribe(wildcard_telemetry(HOME_ID), qos=0)
    mqtt_client.subscribe(wildcard_state(HOME_ID), qos=0)

    mqtt_client.loop_start()

    # Minimal bootstrap registry (helpful for /status)
    registry.add(DeviceInfo("door_1", "door_window", "sensor"))
    registry.add(DeviceInfo("window_1", "door_window", "sensor"))
    registry.add(DeviceInfo("env_1", "environment", "sensor"))

    registry.add(DeviceInfo("alarm_controller", "alarm_controller", "actuator"))
    registry.add(DeviceInfo("alarm_switch", "alarm_switch", "actuator"))
    registry.add(DeviceInfo("mobile_light", "mobile_light", "hybrid"))
    registry.add(DeviceInfo("sprinkler", "sprinkler", "actuator"))

    registry.add(DeviceInfo("gas_meter", "gas_meter", "hybrid"))
    registry.add(DeviceInfo("electricity_meter", "electricity_meter", "hybrid"))
    registry.add(DeviceInfo("water_meter", "water_meter", "hybrid"))

    logger.log({"event": "startup", "ts_unix": time.time(), "msg": "Manager started"})


# -----------------------------
# REST endpoints
# -----------------------------
@app.get("/status")
def get_status() -> Dict[str, Any]:
    """
    Aggregated status view.
    """
    devs = {k: v.__dict__ for k, v in registry.list_all().items()}
    snap = store.snapshot()
    return {
        "home_id": HOME_ID,
        "config": cfg.__dict__,
        "devices": devs,
        "last_telemetry": snap["telemetry"],
        "last_state": snap["state"],
    }


@app.get("/devices")
def list_devices() -> Dict[str, Any]:
    devs = {k: v.__dict__ for k, v in registry.list_all().items()}
    return {"devices": devs}


@app.post("/devices")
def add_device(d: DeviceIn) -> Dict[str, Any]:
    if not d.device_id or not d.device_type:
        raise HTTPException(status_code=400, detail="device_id and device_type are required")
    registry.add(DeviceInfo(d.device_id, d.device_type, d.kind))
    return {"ok": True, "device": registry.get(d.device_id).__dict__}


@app.delete("/devices/{device_id}")
def delete_device(device_id: str) -> Dict[str, Any]:
    registry.remove(device_id)
    return {"ok": True}


@app.get("/config")
def get_config() -> Dict[str, Any]:
    return {"config": cfg.__dict__}


@app.put("/config")
def update_config(c: ConfigIn) -> Dict[str, Any]:
    # Arm/disarm + thresholds + rule toggles.
    if c.armed is not None:
        cfg.armed = c.armed
    if c.temp_threshold is not None:
        cfg.temp_threshold = c.temp_threshold
    if c.pm10_threshold is not None:
        cfg.pm10_threshold = c.pm10_threshold
    if c.gas_spike_ratio is not None:
        cfg.gas_spike_ratio = c.gas_spike_ratio
    if c.gas_min_delta is not None:
        cfg.gas_min_delta = c.gas_min_delta

    if c.rule_intrusion_enabled is not None:
        cfg.rule_intrusion_enabled = c.rule_intrusion_enabled
    if c.rule_fire_enabled is not None:
        cfg.rule_fire_enabled = c.rule_fire_enabled
    if c.rule_gas_enabled is not None:
        cfg.rule_gas_enabled = c.rule_gas_enabled

    logger.log({"event": "config_update", "ts_unix": time.time(), "config": cfg.__dict__})
    return {"ok": True, "config": cfg.__dict__}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.manager:app", host="127.0.0.1", port=8000, reload=False)
