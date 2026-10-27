#include <Arduino.h>
#include <WiFi.h>
#include "config.h"
#include "device_config.h"
#include "mqtt_publisher.h"
#include "provisioning.h"
#include "sensors.h"

static DeviceConfig deviceConfig;
static unsigned long lastPublishAt = 0;

void setup() {
  Serial.begin(115200);
  sensorsSetup();
  deviceConfigLoad(deviceConfig);
  provisioningBegin(deviceConfig);
  configTime(NTP_GMT_OFFSET_SEC, NTP_DAYLIGHT_OFFSET_SEC, NTP_SERVER);
  mqttSetup(deviceConfig);
}

void loop() {
  provisioningLoop(deviceConfig);
  mqttEnsureConnected();
  mqttLoop();

  if (millis() - lastPublishAt >= PUBLISH_INTERVAL_MS) {
    lastPublishAt = millis();
    const SensorReadings readings = readSensors();
    if (readings.valid) {
      mqttPublishReading(readings);
    } else {
      Serial.println("Leitura de sensor inválida, pulando publicação.");
    }
  }
}
