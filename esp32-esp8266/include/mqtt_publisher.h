#pragma once

#include "device_config.h"
#include "sensors.h"

void mqttSetup(const DeviceConfig &config);
void mqttEnsureConnected();
void mqttLoop();
void mqttPublishReading(const SensorReadings &readings);
