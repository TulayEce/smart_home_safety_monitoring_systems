from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .models import DeviceId, DeviceInfo


@dataclass
class Config:
    """
    Project runtime configuration.
    arm/disarm, thresholds, enable/disable rules
    """
    armed: bool = False

    # Fire rule thresholds
    temp_threshold: float = 60.0
    pm10_threshold: float = 150.0

    # Gas spike rule thresholds (simple ratio-based spike)
    gas_spike_ratio: float = 2.0
    gas_min_delta: float = 0.1

    # Rule toggles
    rule_intrusion_enabled: bool = True
    rule_fire_enabled: bool = True
    rule_gas_enabled: bool = True

    # Cooldown to avoid command spamming in demos
    cooldown_seconds: float = 5.0


class DeviceRegistry:
    """In-memory registry of devices (minimal CRUD)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._devices: Dict[DeviceId, DeviceInfo] = {}

    def add(self, info: DeviceInfo) -> None:
        with self._lock:
            self._devices[info.device_id] = info

    def remove(self, device_id: DeviceId) -> None:
        with self._lock:
            self._devices.pop(device_id, None)

    def get(self, device_id: DeviceId) -> Optional[DeviceInfo]:
        with self._lock:
            return self._devices.get(device_id)

    def list_all(self) -> Dict[DeviceId, DeviceInfo]:
        with self._lock:
            return dict(self._devices)


class StateStore:
    """Stores last telemetry and last actuator states."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.last_telemetry: Dict[DeviceId, Dict[str, Any]] = {}
        self.last_state: Dict[DeviceId, Dict[str, Any]] = {}

        # helper: last gas delta for spike detection
        self._last_gas_delta: Optional[float] = None

        # helper: edge detection for rules
        self.rule_active: Dict[str, bool] = {"intrusion": False, "fire": False, "gas": False}
        self.last_trigger_ts: Dict[str, float] = {"intrusion": 0.0, "fire": 0.0, "gas": 0.0}

   
    def update_telemetry(self, device_id: DeviceId, message: Dict[str, Any]) -> None:
        with self._lock:
            self.last_telemetry[device_id] = message

    def update_state(self, device_id: DeviceId, message: Dict[str, Any]) -> None:
        with self._lock:
            self.last_state[device_id] = message

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "telemetry": dict(self.last_telemetry),
                "state": dict(self.last_state),
                "rule_active": dict(self.rule_active),
            }

   
    def set_last_gas_delta(self, delta: float) -> None:
        with self._lock:
            self._last_gas_delta = delta

    def get_last_gas_delta(self) -> Optional[float]:
        with self._lock:
            return self._last_gas_delta

   
    def can_trigger(self, rule_name: str, now_s: float, cooldown_s: float) -> bool:
        with self._lock:
            return (now_s - self.last_trigger_ts.get(rule_name, 0.0)) >= cooldown_s

    def mark_trigger(self, rule_name: str, now_s: float) -> None:
        with self._lock:
            self.last_trigger_ts[rule_name] = now_s


class EventLogger:
    """Simple JSONL event logger for demo."""

    def __init__(self, log_path: str) -> None:
        self.log_path = log_path
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        self._lock = threading.Lock()

    def log(self, event: Dict[str, Any]) -> None:
        line = json.dumps(event, ensure_ascii=False)
        with self._lock:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
