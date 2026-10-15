import json
import logging

import paho.mqtt.client as mqtt
from pydantic import ValidationError

from app.core.config import settings
from app.db.session import SessionLocal
from app.schemas.reading import ReadingIn
from app.services.device_service import ingest_device_reading, is_valid_device_id

logger = logging.getLogger(__name__)

READINGS_TOPIC_FILTER = "solarsense/+/readings"


def _device_id_from_topic(topic: str) -> str | None:
    parts = topic.split("/")
    if len(parts) != 3 or parts[0] != "solarsense" or parts[2] != "readings":
        return None
    return parts[1] if is_valid_device_id(parts[1]) else None


def _on_connect(
    client: mqtt.Client,
    userdata: object,
    connect_flags: mqtt.ConnectFlags,
    reason_code: mqtt.ReasonCode,
    properties: mqtt.Properties | None,
) -> None:
    logger.info("Connected to MQTT broker (rc=%s), subscribing to %s", reason_code, READINGS_TOPIC_FILTER)
    client.subscribe(READINGS_TOPIC_FILTER)


def _on_message(client: mqtt.Client, userdata: object, message: mqtt.MQTTMessage) -> None:
    device_id = _device_id_from_topic(message.topic)
    if device_id is None:
        logger.warning("Discarding reading on unexpected topic %s", message.topic)
        return

    try:
        payload = ReadingIn.model_validate(json.loads(message.payload))
    except (json.JSONDecodeError, ValidationError):
        logger.warning("Discarding malformed reading on topic %s", message.topic)
        return

    db = SessionLocal()
    try:
        ingest_device_reading(db, device_id=device_id, payload=payload)
    finally:
        db.close()


def build_mqtt_client() -> mqtt.Client:
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(settings.mqtt_username, settings.mqtt_password)
    client.on_connect = _on_connect
    client.on_message = _on_message
    return client


def start_mqtt_ingest() -> mqtt.Client:
    client = build_mqtt_client()
    client.connect_async(settings.mqtt_broker_host, settings.mqtt_broker_port)
    client.loop_start()
    return client


def stop_mqtt_ingest(client: mqtt.Client) -> None:
    client.loop_stop()
    client.disconnect()
