#pragma once

#include "device_config.h"

void provisioningBegin(DeviceConfig &config);

void provisioningLoop(DeviceConfig &config);

bool provisioningInPairingWindow();
