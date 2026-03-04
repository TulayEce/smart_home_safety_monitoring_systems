from __future__ import annotations

import time
from typing import Any, Dict, List, Tuple

from .models import Command
from .state import Config, StateStore


def _find_any_open_door_or_window(state: Dict[str, Any]) -> bool:
    """
    Door/Window sensor: open/closed detection
    Assumed telemetry data includes: data.open -> bool
    """
    for msg in state["telemetry"].values():
        dtype = msg.get("device_type")
        if dtype == "door_window":
            data = msg.get("data", {})
            if bool(data.get("open")):
                return True
    return False


def _read_environment(state: Dict[str, Any]) -> Tuple[float | None, float | None]:
    """
    Environmental Monitoring provides temperature and PM10.
    """
    for msg in state["telemetry"].values():
        if msg.get("device_type") == "environment":
            d = msg.get("data", {})
            return d.get("temperature"), d.get("pm10")
    return None, None


def _read_gas_delta(state: Dict[str, Any]) -> float | None:
    """
    Gas Metering includes gas consumption sensor.
    Used a simple 'delta' field sent by the meter emulator.
    """
    for msg in state["telemetry"].values():
        if msg.get("device_type") == "gas_meter":
            d = msg.get("data", {})
            return d.get("delta")
    return None


def evaluate_rules(store: StateStore, cfg: Config) -> Tuple[List[Command], List[Dict[str, Any]]]:
    """
    Evaluate 3 rules described in the proposal:
    - Intrusion (armed + door/window opens) -> siren ON + lights ON
    - Fire (temp & PM10 exceed) -> siren ON + sprinkler ON
    - Gas spike -> siren ON + gas supply OFF
    """
    snap = store.snapshot()
    now_s = time.time()

    commands: List[Command] = []
    events: List[Dict[str, Any]] = []

    # -------------------------
    # Rule 1: Intrusion
    # -------------------------
    intrusion_cond = cfg.rule_intrusion_enabled and cfg.armed and _find_any_open_door_or_window(snap)
    prev_intrusion = snap["rule_active"].get("intrusion", False)

    if intrusion_cond and not prev_intrusion and store.can_trigger("intrusion", now_s, cfg.cooldown_seconds):
        commands += [
            Command(target_id="alarm_controller", action="set", params={"on": True}),
            Command(target_id="mobile_light", action="set", params={"on": True, "level": "HIGH"}),
        ]
        events.append({"rule": "intrusion", "ts_unix": now_s, "actions": [c.__dict__ for c in commands[-2:]]})
        store.mark_trigger("intrusion", now_s)

    # -------------------------
    # Rule 2: Fire
    # -------------------------
    temp, pm10 = _read_environment(snap)
    fire_cond = (
        cfg.rule_fire_enabled
        and temp is not None and pm10 is not None
        and float(temp) >= cfg.temp_threshold
        and float(pm10) >= cfg.pm10_threshold
    )
    prev_fire = snap["rule_active"].get("fire", False)

    if fire_cond and not prev_fire and store.can_trigger("fire", now_s, cfg.cooldown_seconds):
        commands += [
            Command(target_id="alarm_controller", action="set", params={"on": True}),
            Command(target_id="sprinkler", action="set", params={"on": True}),
        ]
        events.append({"rule": "fire", "ts_unix": now_s, "actions": [c.__dict__ for c in commands[-2:]]})
        store.mark_trigger("fire", now_s)

    # -------------------------
    # Rule 3: Gas spike suspicion
    # -------------------------
    gas_delta = _read_gas_delta(snap)
    prev_delta = store.get_last_gas_delta()

    gas_cond = False
    if cfg.rule_gas_enabled and gas_delta is not None and float(gas_delta) >= cfg.gas_min_delta:
        if prev_delta is not None and prev_delta > 0:
            ratio = float(gas_delta) / float(prev_delta)
            gas_cond = ratio >= cfg.gas_spike_ratio

    prev_gas = snap["rule_active"].get("gas", False)

    if gas_cond and not prev_gas and store.can_trigger("gas", now_s, cfg.cooldown_seconds):
        commands += [
            Command(target_id="alarm_controller", action="set", params={"on": True}),
            Command(target_id="gas_meter", action="set", params={"supply_on": False}),
        ]
        events.append({"rule": "gas_spike", "ts_unix": now_s, "actions": [c.__dict__ for c in commands[-2:]]})
        store.mark_trigger("gas", now_s)

    
    # Update edge-detection flags and gas baseline
    snap2 = store.snapshot()
    snap2["rule_active"]["intrusion"] = bool(intrusion_cond)
    snap2["rule_active"]["fire"] = bool(fire_cond)
    snap2["rule_active"]["gas"] = bool(gas_cond)

    # Persist rule active flags into the store:
    # Reuse update_state on a pseudo-device "manager_rules" to keep everything uniform.
    store.update_state("manager_rules", {"rule_active": snap2["rule_active"]})

    if gas_delta is not None:
        store.set_last_gas_delta(float(gas_delta))

    return commands, events
