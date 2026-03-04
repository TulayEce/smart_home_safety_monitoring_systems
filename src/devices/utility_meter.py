from __future__ import annotations

import argparse
import json
import random
import time

import paho.mqtt.client as mqtt

from src.models import make_envelope, topic


def main() -> None:
    """
    Utility Meter emulator (electricity/gas/water).
    Each meter has a consumption sensor + a supply switch ON/OFF.
    Emulate both (hybrid device): publishes telemetry and reacts to cmd to toggle supply.
    """
    ap = argparse.ArgumentParser()
    ap.add_argument("--home-id", default="home_1")
    ap.add_argument("--meter", choices=["electricity", "gas", "water"], required=True)
    ap.add_argument("--device-id", required=True)  # e.g., gas_meter
    ap.add_argument("--period", type=float, default=2.0)
    args = ap.parse_args()

    if args.meter == "electricity":
        device_type = "electricity_meter"
        unit = "kWh"
    elif args.meter == "gas":
        device_type = "gas_meter"
        unit = "kg"
    else:
        device_type = "water_meter"
        unit = "L"

    home_id = args.home_id
    device_id = args.device_id

    supply_on = True
    total = 0.0
    prev_total = 0.0

    client = mqtt.Client(client_id=f"{device_id}_meter", clean_session=True)

    def on_message(_c, _u, msg: mqtt.MQTTMessage) -> None:
        nonlocal supply_on
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except Exception:
            return
        if payload.get("action") != "set":
            return
        params = payload.get("params", {})
        if "supply_on" in params:
            supply_on = bool(params["supply_on"])

            # publish state immediately
            st = make_envelope(
                home_id=home_id,
                device_id=device_id,
                device_type=device_type,
                payload={"supply_on": supply_on},
            )
            client.publish(topic(home_id, device_id, "state"), json.dumps(st), qos=0, retain=False)

    client.on_message = on_message
    client.connect("127.0.0.1", 1883, keepalive=60)
    client.subscribe(topic(home_id, device_id, "cmd"), qos=0)
    client.loop_start()

    while True:
        prev_total = total

        # When supply is OFF, consumption does not increase
        if supply_on:
            inc = random.uniform(0.02, 0.2)  # tiny increments for demo
            total += inc

        delta = total - prev_total

        payload = make_envelope(
            home_id=home_id,
            device_id=device_id,
            device_type=device_type,
            payload={
                "total": round(total, 4),
                "delta": round(delta, 4),
                "unit": unit,
                "supply_on": supply_on,
            },
        )
        client.publish(topic(home_id, device_id, "telemetry"), json.dumps(payload), qos=0, retain=False)
        time.sleep(args.period)


if __name__ == "__main__":
    main()
