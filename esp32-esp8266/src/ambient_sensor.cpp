#include "ambient_sensor.h"
#include "config.h"
#include <Adafruit_BME280.h>
#include <Adafruit_BMP280.h>
#include <Arduino.h>
#include <Wire.h>

static const uint8_t CHIP_ID_REG = 0xD0;
static const uint8_t CHIP_ID_BMP280 = 0x58;
static const uint8_t CHIP_ID_BME280 = 0x60;

enum class AmbientChip { None, BMP280, BME280 };

static AmbientChip chip = AmbientChip::None;
static uint8_t chipAddress = 0;
static Adafruit_BME280 bme;
static Adafruit_BMP280 bmp(&Wire);

static int readChipId(uint8_t address) {
  Wire.beginTransmission(address);
  Wire.write(CHIP_ID_REG);
  if (Wire.endTransmission() != 0) return -1;
  if (Wire.requestFrom(address, (uint8_t)1) != 1) return -1;
  return Wire.read();
}

static const unsigned long RETRY_INTERVAL_MS = 5000;
static unsigned long lastDetectAt = 0;

static bool detectChip() {
  lastDetectAt = millis();

  for (const uint8_t address : {0x76, 0x77}) {
    const int id = readChipId(address);
    if (id < 0) continue;

    Serial.printf("Sensor ambiente em 0x%02X, chip ID 0x%02X: ", address, id);
    if (id == CHIP_ID_BME280 && bme.begin(address, &Wire)) {
      chip = AmbientChip::BME280;
      chipAddress = address;
      Serial.println("BME280 (temp + umidade + pressão).");
      return true;
    }
    if (id == CHIP_ID_BMP280 && bmp.begin(address, CHIP_ID_BMP280)) {
      chip = AmbientChip::BMP280;
      chipAddress = address;
      Serial.println("BMP280 (temp + pressão, sem umidade).");
      return true;
    }
    Serial.println("chip não reconhecido.");
  }

  Serial.println("Sensor ambiente não encontrado (confira VCC 3V3, SDA/SCL e GND).");
  return false;
}

bool ambientSensorSetup() {
  Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
  return detectChip();
}

static uint8_t expectedChipId() {
  return chip == AmbientChip::BME280 ? CHIP_ID_BME280 : CHIP_ID_BMP280;
}

static bool chipStillResponds() {
  if (readChipId(chipAddress) == expectedChipId()) return true;

  Serial.println("Sensor ambiente parou de responder; tentando detectar de novo.");
  chip = AmbientChip::None;
  lastDetectAt = millis();
  return false;
}

bool readAmbientSensor(AmbientReading &out) {
  if (chip != AmbientChip::None && !chipStillResponds()) return false;

  switch (chip) {
    case AmbientChip::BME280:
      out.tempC = bme.readTemperature();
      out.humidityPct = bme.readHumidity();
      out.pressureHpa = bme.readPressure() / 100.0f;
      break;
    case AmbientChip::BMP280:
      out.tempC = bmp.readTemperature();
      out.humidityPct = NAN;
      out.pressureHpa = bmp.readPressure() / 100.0f;
      break;
    case AmbientChip::None:
      if (millis() - lastDetectAt >= RETRY_INTERVAL_MS) detectChip();
      return false;
  }
  return !isnan(out.tempC) && !isnan(out.pressureHpa);
}
