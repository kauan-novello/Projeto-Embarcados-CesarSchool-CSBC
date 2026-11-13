#include <Arduino.h>
#include <WiFi.h>
#include "config.h"
#include "device_config.h"
#include "logger.h"
#include "mqtt_publisher.h"
#include "provisioning.h"
#include "sensors.h"
#include "tasks.h"

static DeviceConfig deviceConfig;

void setup() {
  Serial.begin(115200);
  logInit();
  sensorsSetup();
  deviceConfigLoad(deviceConfig);
  provisioningBegin(deviceConfig);
  configTime(NTP_GMT_OFFSET_SEC, NTP_DAYLIGHT_OFFSET_SEC, NTP_SERVER);
  mqttSetup(deviceConfig);
  tasksStart(deviceConfig);
}

void loop() {
  vTaskDelete(nullptr);
}
