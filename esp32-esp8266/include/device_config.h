#pragma once

#include <stdint.h>

struct DeviceConfig {
  char brokerHost[64];
  uint16_t brokerPort;
  char brokerUser[32];
  char brokerPassword[64];
  bool pairingPending;
};

void deviceConfigLoad(DeviceConfig &config);
void deviceConfigSave(const DeviceConfig &config);
bool deviceConfigIsComplete(const DeviceConfig &config);

const char *deviceId();
