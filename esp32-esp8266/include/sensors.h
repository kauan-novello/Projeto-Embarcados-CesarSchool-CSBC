#pragma once

struct SensorReadings {
  float powerW;
  float panelTempC;
  float ambientTempC;
  float ambientHumidityPct;
  float irradiancePct;
  float pressureHpa;
  float particulatePct;
  bool valid;
};

void sensorsSetup();
SensorReadings readSensors();
