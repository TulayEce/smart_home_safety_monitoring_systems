from __future__ import annotations

import argparse
import json
import time

import paho.mqtt.client as mqtt

from src.models import make_envelope, topic


def run_alarm_controller(home_id: str, device_id: str) -> None:
    """
    Alarm Controller (siren) actuator: ON/OFF.
    """
    is_on = False
    client = mqtt.Client(client_id=f"{device_id}_act", clean_session=True)

    def on_message(_c, _u, msg: mqtt.MQTTMessage) -> None:
        nonlocal is_on
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except Exception:
            return
        if payload.get("action") == "set":
            params = payload.get("params", {})
            if "on" in params:
                is_on = bool(params["on"])
                st = make_envelope(home_id, device_id, "alarm_controller", {"on": is_on})
                client.publish(topic(home_id, device_id, "state"), json.dumps(st), qos=0, retain=False)

    client.on_message = on_message
    client.connect("127.0.0.1", 1883, keepalive=60)
    client.subscribe(topic(home_id, device_id, "cmd"), qos=0)
    client.loop_forever()


def run_alarm_switch(home_id: str, device_id: str) -> None:
    """
    Alarm Switch actuator: arms/disarms the system.
    Publish telemetry with {"armed": bool} so Manager can reflect it.
    """
    armed = False
    client = mqtt.Client(client_id=f"{device_id}_act", clean_session=True)

    def on_message(_c, _u, msg: mqtt.MQTTMessage) -> None:
        nonlocal armed
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except Exception:
            return
        if payload.get("action") == "set":
            params = payload.get("params", {})
            if "armed" in params:
                armed = bool(params["armed"])
                t = make_envelope(home_id, device_id, "alarm_switch", {"armed": armed})
                client.publish(topic(home_id, device_id, "telemetry"), json.dumps(t), qos=0, retain=False)

    client.on_message = on_message
    client.connect("127.0.0.1", 1883, keepalive=60)
    client.subscribe(topic(home_id, device_id, "cmd"), qos=0)
    client.loop_forever()


def run_sprinkler(home_id: str, device_id: str) -> None:
    """
    Irrigation Controller used as sprinkler: ON/OFF.
    """
    is_on = False
    client = mqtt.Client(client_id=f"{device_id}_act", clean_session=True)

    def on_message(_c, _u, msg: mqtt.MQTTMessage) -> None:
        nonlocal is_on
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except Exception:
            return
        if payload.get("action") == "set":
            params = payload.get("params", {})
            if "on" in params:
                is_on = bool(params["on"])
                st = make_envelope(home_id, device_id, "sprinkler", {"on": is_on})
                client.publish(topic(home_id, device_id, "state"), json.dumps(st), qos=0, retain=False)

    client.on_message = on_message
    client.connect("127.0.0.1", 1883, keepalive=60)
    client.subscribe(topic(home_id, device_id, "cmd"), qos=0)
    client.loop_forever()


def run_mobile_light(home_id: str, device_id: str) -> None:
    """
    Mobile Light is hybrid (actuator + energy consumption sensor).
    - Actuation: ON/OFF + level
    - Telemetry: energy consumption
    """
    is_on = False
    level = "LOW"
    energy_kwh = 0.0

    client = mqtt.Client(client_id=f"{device_id}_hybrid", clean_session=True)

    def on_message(_c, _u, msg: mqtt.MQTTMessage) -> None:
        nonlocal is_on, level
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except Exception:
            return
        if payload.get("action") == "set":
            params = payload.get("params", {})
            if "on" in params:
                is_on = bool(params["on"])
            if "level" in params:
                level = str(params["level"]).upper()

            st = make_envelope(home_id, device_id, "mobile_light", {"on": is_on, "level": level})
            client.publish(topic(home_id, device_id, "state"), json.dumps(st), qos=0, retain=False)

    client.on_message = on_message
    client.connect("127.0.0.1", 1883, keepalive=60)
    client.subscribe(topic(home_id, device_id, "cmd"), qos=0)
    client.loop_start()

    # Periodic telemetry loop
    while True:
        # very rough energy simulation
        if is_on:
            if level == "HIGH":
                energy_kwh += 0.05
            elif level == "MEDIUM":
                energy_kwh += 0.03
            else:
                energy_kwh += 0.01

        tel = make_envelope(
            home_id, device_id, "mobile_light",
            {"energy_kwh": round(energy_kwh, 4), "on": is_on, "level": level}
        )
        client.publish(topic(home_id, device_id, "telemetry"), json.dumps(tel), qos=0, retain=False)
        time.sleep(2.0)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--home-id", default="home_1")
    ap.add_argument("--device", choices=["alarm_controller", "alarm_switch", "sprinkler", "mobile_light"], required=True)
    ap.add_argument("--device-id", required=True)
    args = ap.parse_args()

    if args.device == "alarm_controller":
        run_alarm_controller(args.home_id, args.device_id)
    elif args.device == "alarm_switch":
        run_alarm_switch(args.home_id, args.device_id)
    elif args.device == "sprinkler":
        run_sprinkler(args.home_id, args.device_id)
    else:
        run_mobile_light(args.home_id, args.device_id)


if __name__ == "__main__":
    main()
