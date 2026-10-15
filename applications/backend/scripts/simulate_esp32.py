import argparse
import json
import math
import os
import random
import time
from datetime import UTC, datetime

from paho.mqtt import publish


def make_reading(hour: int) -> dict:
    daylight = math.sin(((hour - 6) / 12) * math.pi) if 6 <= hour <= 18 else 0
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "power_w": round(daylight * 1800 + random.uniform(0, 60), 1),
        "panel_temp_c": round(28 + daylight * 22 + random.uniform(0, 3), 1),
        "ambient_temp_c": round(24 + daylight * 6 + random.uniform(0, 2), 1),
        "ambient_humidity_pct": round(55 + random.uniform(0, 15), 1),
        "irradiance": round(daylight * 95 + random.uniform(0, 5), 1),
        "pressure_hpa": round(1012 + random.uniform(-3, 3), 1),
        "particulate_pct": round(0.5 + random.uniform(0, 2), 2),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish fake readings, simulating the ESP32 firmware")
    parser.add_argument("device_id", help="MAC do dispositivo em 12 hex maiúsculos, ex.: A1B2C3D48823")
    parser.add_argument("--pairing", action="store_true", help="Publica em modo pareamento")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=1883)
    parser.add_argument("--username", default=os.environ.get("MQTT_USERNAME"))
    parser.add_argument("--password", default=os.environ.get("MQTT_PASSWORD"))
    parser.add_argument("--interval", type=float, default=5.0, help="Segundos entre publicações")
    parser.add_argument("--count", type=int, default=0, help="Quantidade de leituras (0 = infinito)")
    parser.add_argument("--overheat", action="store_true", help="Força panel_temp_c=70 pra testar o alerta")
    args = parser.parse_args()
    if not args.username or not args.password:
        parser.error("broker credentials required: --username/--password or MQTT_USERNAME/MQTT_PASSWORD")
    auth = {"username": args.username, "password": args.password}

    topic = f"solarsense/{args.device_id}/readings"
    published = 0

    while args.count == 0 or published < args.count:
        reading = make_reading(datetime.now().hour)
        if args.overheat:
            reading["panel_temp_c"] = 70.0
        if args.pairing:
            reading["pairing_mode"] = True
        publish.single(topic, payload=json.dumps(reading), hostname=args.host, port=args.port, auth=auth)
        print(f"published to {topic}: {reading}")
        published += 1
        if args.count == 0 or published < args.count:
            time.sleep(args.interval)


if __name__ == "__main__":
    main()
