from __future__ import annotations

import argparse
import json
import random
import time
import paho.mqtt.client as mqtt

from src.models import make_envelope, topic


def main() -> None:
    """Door/Window Sensor emulator."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--home-id", default="home_1")
    ap.add_argument("--device-id", required=True)  # e.g., door_1 or window_1
    ap.add_argument("--period", type=float, default=2.0)
    ap.add_argument("--flip-prob", type=float, default=0.2, help="Probability to flip open/closed per tick.")
    args = ap.parse_args()

    home_id = args.home_id
    device_id = args.device_id

    client = mqtt.Client(client_id=f"{device_id}_sensor", clean_session=True)
    client.connect("127.0.0.1", 1883, keepalive=60)

    is_open = False

    while True:
        if random.random() < args.flip_prob:
            is_open = not is_open

        payload = make_envelope(
            home_id=home_id,
            device_id=device_id,
            device_type="door_window",
            payload={"open": is_open},
        )
        client.publish(topic(home_id, device_id, "telemetry"), json.dumps(payload), qos=0, retain=False)
        time.sleep(args.period)


if __name__ == "__main__":
    main()
