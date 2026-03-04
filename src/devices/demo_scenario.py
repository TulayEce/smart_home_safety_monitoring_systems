from __future__ import annotations

import argparse
import json
import time
import paho.mqtt.client as mqtt

from src.models import make_envelope, topic


def main() -> None:
    """
    Demo scenario for the 3 situations:
    1) Intrusion: armed + door open -> siren + light
    2) Fire: temp & pm10 high -> siren + sprinkler
    3) Gas spike: high delta -> siren + gas supply off
    """
    ap = argparse.ArgumentParser()
    ap.add_argument("--home-id", default="home_1")
    args = ap.parse_args()

    client = mqtt.Client(client_id="demo_scenario", clean_session=True)
    client.connect("127.0.0.1", 1883, keepalive=60)

    # 0) Arm system via REST normally, but we can also publish alarm_switch telemetry:
    arm_msg = make_envelope(args.home_id, "alarm_switch", "alarm_switch", {"armed": True})
    client.publish(topic(args.home_id, "alarm_switch", "telemetry"), json.dumps(arm_msg), qos=0, retain=False)
    time.sleep(1)

    # 1) Intrusion: door opens
    door_msg = make_envelope(args.home_id, "door_1", "door_window", {"open": True})
    client.publish(topic(args.home_id, "door_1", "telemetry"), json.dumps(door_msg), qos=0, retain=False)
    time.sleep(3)

    # 2) Fire: env high temp + pm10
    env_msg = make_envelope(args.home_id, "env_1", "environment", {"temperature": 80.0, "pm10": 300.0})
    client.publish(topic(args.home_id, "env_1", "telemetry"), json.dumps(env_msg), qos=0, retain=False)
    time.sleep(3)

    # 3) Gas spike: send gas meter deltas
    gas1 = make_envelope(args.home_id, "gas_meter", "gas_meter", {"total": 10.0, "delta": 0.2, "unit": "kg", "supply_on": True})
    client.publish(topic(args.home_id, "gas_meter", "telemetry"), json.dumps(gas1), qos=0, retain=False)
    time.sleep(2)

    gas2 = make_envelope(args.home_id, "gas_meter", "gas_meter", {"total": 11.0, "delta": 0.8, "unit": "kg", "supply_on": True})
    client.publish(topic(args.home_id, "gas_meter", "telemetry"), json.dumps(gas2), qos=0, retain=False)

    print("Demo scenario messages published. Check /status and outputs/events.log.")


if __name__ == "__main__":
    main()
