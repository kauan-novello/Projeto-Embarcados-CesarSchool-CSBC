import logging
import os
import sys
from collections.abc import Sequence

import httpx
import paho.mqtt.client as mqtt

from weather_station.config import ConfigError, load_settings
from weather_station.open_meteo import fetch_closed_hours
from weather_station.station import run


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    try:
        settings = load_settings(os.environ)
    except ConfigError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(settings.mqtt_username, settings.mqtt_password)
    client.connect_async(settings.mqtt_host, settings.mqtt_port)
    client.loop_start()
    logging.info(
        "virtual ESP %s publishing to %s:%d", settings.device_id, settings.mqtt_host, settings.mqtt_port
    )
    with httpx.Client() as http:
        try:
            run(
                settings,
                client,
                lambda now: fetch_closed_hours(http, settings.latitude, settings.longitude, now),
            )
        except KeyboardInterrupt:
            return 0
        finally:
            client.loop_stop()
            client.disconnect()
    return 0


if __name__ == "__main__":
    sys.exit(main())
