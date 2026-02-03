from __future__ import annotations

import argparse
import json
import random
import time
import paho.mqtt.client as mqtt

from src.models import make_envelope, topic


def main() -> None:
    """
    Environmental Monitoring emulator.
    """
    ap = argparse.ArgumentParser()
    ap.add_argument("--home-id", default="home_1")
    ap.add_argument("--device-id", default="env_1")
    ap.add_argument("--period", type=float, default=2.0)
    ap.add_argument("--base-temp", type=float, default=22.0)
    ap.add_argument("--base-pm10", type=float, default=20.0)
    args = ap.parse_args()

    client = mqtt.Client(client_id=f"{args.device_id}_env", clean_session=True)
    client.connect("127.0.0.1", 1883, keepalive=60)

    while True:
        # Simple noisy readings
        temperature = args.base_temp + random.uniform(-0.5, 0.5)
        pm10 = args.base_pm10 + random.uniform(-2.0, 2.0)

        payload = make_envelope(
            home_id=args.home_id,
            device_id=args.device_id,
            device_type="environment",
            payload={"temperature": round(temperature, 2), "pm10": round(pm10, 2)},
        )

        client.publish(topic(args.home_id, args.device_id, "telemetry"), json.dumps(payload), qos=0, retain=False)
        time.sleep(args.period)


if __name__ == "__main__":
    main()
