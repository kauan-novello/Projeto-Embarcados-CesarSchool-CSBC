#pragma once

#include "device_config.h"

void provisioningBegin(DeviceConfig &config);

void provisioningOpenPortal(DeviceConfig &config);

bool provisioningInPairingWindow();
