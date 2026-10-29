#pragma once

struct AmbientReading {
  float tempC;
  float humidityPct;
  float pressureHpa;
};

bool ambientSensorSetup();
bool readAmbientSensor(AmbientReading &out);
