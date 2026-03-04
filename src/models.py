from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Literal
from datetime import datetime, timezone


HomeId = str
DeviceId = str

Kind = Literal["sensor", "actuator", "hybrid"]  # hybrid = sensor+actuator
Channel = Literal["telemetry", "state", "cmd"]

DeviceType = Literal[
    "door_window",
    "environment",
    "alarm_controller",
    "alarm_switch",
    "mobile_light",
    "sprinkler",
    "gas_meter",
    "electricity_meter",
    "water_meter",
]


def utc_iso() -> str:
    """Return current UTC time in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def topic(home_id: HomeId, device_id: DeviceId, channel: Channel) -> str:
    """Standard topic schema for this project."""
    return f"home/{home_id}/{device_id}/{channel}"


def wildcard_telemetry(home_id: HomeId) -> str:
    """Subscribe to telemetry of all devices inside a home."""
    return f"home/{home_id}/+/telemetry"


def wildcard_state(home_id: HomeId) -> str:
    """Subscribe to states of all devices inside a home."""
    return f"home/{home_id}/+/state"


@dataclass
class DeviceInfo:
    """Registry entry."""
    device_id: DeviceId
    device_type: str
    kind: Kind


@dataclass
class Command:
    """Command dispatched by the Manager to an actuator (or hybrid device)."""
    target_id: DeviceId
    action: str
    params: Dict[str, Any]


def make_envelope(
    home_id: HomeId,
    device_id: DeviceId,
    device_type: str,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """Create a consistent message payload for telemetry/state."""
    return {
        "ts": utc_iso(),
        "home_id": home_id,
        "device_id": device_id,
        "device_type": device_type,
        "data": payload,
    }
