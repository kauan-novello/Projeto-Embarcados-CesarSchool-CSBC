#include "sensors.h"
#include "config.h"
#include <Arduino.h>

#ifdef SIMULATE_SENSORS

#include <time.h>

static float simDaylightFactor() {
  time_t now = time(nullptr);
  int hour = 12;
  if (now > 1700000000) {
    struct tm timeinfo;
    localtime_r(&now, &timeinfo);
    hour = timeinfo.tm_hour;
  }
  if (hour < 6 || hour > 18) return 0.0f;
  return sinf(((hour - 6) / 12.0f) * PI);
}

void sensorsSetup() {
  randomSeed(analogRead(PIN_LDR));
}

SensorReadings readSensors() {
  const float daylight = simDaylightFactor();
  const float noise = (float)random(0, 100) / 100.0f;

  SensorReadings readings;
  readings.powerW = daylight * 1800.0f + noise * 60.0f;
  readings.panelTempC = 28.0f + daylight * 22.0f + noise * 3.0f;
  readings.ambientTempC = 24.0f + daylight * 6.0f + noise * 2.0f;
  readings.ambientHumidityPct = 55.0f + noise * 15.0f;
  readings.irradiancePct = daylight * 95.0f + noise * 5.0f;
  readings.pressureHpa = 1012.0f + (noise - 0.5f) * 6.0f;
  readings.particulatePct = 0.5f + noise * 2.0f;
  readings.valid = true;
  return readings;
}

#else

#include "ambient_sensor.h"
#ifdef HAS_ZPH02
#include "zph02.h"
#endif
#ifdef HAS_DHT11
#include <DHT.h>
static DHT dht11(PIN_DHT11, DHT11);
#endif

static float readIrradiancePct() {
  const int raw = analogRead(PIN_LDR);
  long pct = map(raw, LDR_DARK_RAW, LDR_BRIGHT_RAW, 0, 100);
  if (pct < 0) pct = 0;
  if (pct > 100) pct = 100;
  return (float)pct;
}

static void particulateSensorSetup() {
#ifdef HAS_ZPH02
  zph02Setup();
#endif
}

static float readParticulatePct() {
#ifdef HAS_ZPH02
  return zph02ReadPct();
#else
  return NAN;
#endif
}

#ifdef LIVE_SENSORS

void sensorsSetup() {
  analogReadResolution(12);
#ifdef HAS_BME280
  ambientSensorSetup();
#endif
#ifdef HAS_DHT11
  dht11.begin();
#endif
  particulateSensorSetup();
}

SensorReadings readSensors() {
  SensorReadings readings;
  readings.powerW = NAN;
  readings.panelTempC = NAN;
  readings.ambientTempC = NAN;
  readings.ambientHumidityPct = NAN;
  readings.pressureHpa = NAN;
  readings.irradiancePct = readIrradiancePct();
  readings.particulatePct = readParticulatePct();

#ifdef HAS_BME280
  AmbientReading ambient;
  if (readAmbientSensor(ambient)) {
    readings.ambientTempC = ambient.tempC;
    readings.ambientHumidityPct = ambient.humidityPct;
    readings.pressureHpa = ambient.pressureHpa;
  }
#endif

#ifdef HAS_DHT11
  if (isnan(readings.ambientHumidityPct)) readings.ambientHumidityPct = dht11.readHumidity();
#endif

  readings.valid = true;
  return readings;
}

#else

#include <DallasTemperature.h>
#include <OneWire.h>

static OneWire oneWire(PIN_DS18B20);
static DallasTemperature ds18b20(&oneWire);

void sensorsSetup() {
  analogReadResolution(12);
  ambientSensorSetup();
  ds18b20.begin();
  particulateSensorSetup();
}

static float readCurrentRms() {
  const unsigned long start = millis();
  const int midpoint = 2048;
  double sumSquares = 0;
  unsigned long samples = 0;

  while (millis() - start < CURRENT_SAMPLE_WINDOW_MS) {
    const int raw = analogRead(PIN_SCT013);
    const double centered = (double)raw - midpoint;
    sumSquares += centered * centered;
    samples++;
  }

  if (samples == 0) return 0.0f;
  const double rmsRaw = sqrt(sumSquares / (double)samples);
  const double rmsVoltage = (rmsRaw / 4095.0) * 3.3;
  return (float)(rmsVoltage * CURRENT_CALIBRATION_A_PER_V);
}

SensorReadings readSensors() {
  SensorReadings readings;

  AmbientReading ambient;
  if (!readAmbientSensor(ambient)) {
    readings.valid = false;
    return readings;
  }

  ds18b20.requestTemperatures();
  const float panelTemp = ds18b20.getTempCByIndex(0);
  if (panelTemp <= -127.0f) {
    readings.valid = false;
    return readings;
  }

  const float currentRms = readCurrentRms();

  readings.powerW = V_NOMINAL * currentRms;
  readings.panelTempC = panelTemp;
  readings.ambientTempC = ambient.tempC;
  readings.ambientHumidityPct = ambient.humidityPct;
  readings.pressureHpa = ambient.pressureHpa;
  readings.irradiancePct = readIrradiancePct();
  readings.particulatePct = readParticulatePct();
  readings.valid = true;
  return readings;
}

#endif
#endif
