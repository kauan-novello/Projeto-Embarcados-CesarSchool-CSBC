#include "mqtt_publisher.h"
#include "config.h"
#include "logger.h"
#include "provisioning.h"
#include <ArduinoJson.h>
#include <ESPmDNS.h>
#include <PubSubClient.h>
#include <WiFi.h>
#include <time.h>

static const unsigned long RECONNECT_INTERVAL_MS = 5000UL;
static const uint32_t MDNS_QUERY_TIMEOUT_MS = 2000;

static const DeviceConfig *deviceConfig = nullptr;
static char topic[64];
static char clientId[40];
static unsigned long lastAttemptAt = 0;

static WiFiClient wifiClient;
static PubSubClient mqttClient(wifiClient);

static bool isMdnsName(const char *host) {
  const size_t len = strlen(host);
  return len > 6 && strcasecmp(host + len - 6, ".local") == 0;
}

static bool resolveBroker(IPAddress &ip) {
  const char *host = deviceConfig->brokerHost;
  if (ip.fromString(host)) return true;
  if (isMdnsName(host)) {
    const String name = String(host).substring(0, strlen(host) - 6);
    ip = MDNS.queryHost(name, MDNS_QUERY_TIMEOUT_MS);
    return ip != IPAddress();
  }
  return WiFi.hostByName(host, ip) == 1;
}

void mqttSetup(const DeviceConfig &config) {
  deviceConfig = &config;
  snprintf(topic, sizeof(topic), "solarsense/%s/readings", deviceId());
  snprintf(clientId, sizeof(clientId), "solarsense-%s", deviceId());
  MDNS.begin(clientId);
}

void mqttEnsureConnected() {
  if (mqttClient.connected() || WiFi.status() != WL_CONNECTED) return;
  if (lastAttemptAt != 0 && millis() - lastAttemptAt < RECONNECT_INTERVAL_MS) return;
  lastAttemptAt = millis();

  IPAddress brokerIp;
  if (!resolveBroker(brokerIp)) {
    logPrintf("Não achei o servidor %s na rede.\n", deviceConfig->brokerHost);
    return;
  }
  mqttClient.setServer(brokerIp, deviceConfig->brokerPort);

  logPrintf("Conectando ao broker MQTT %s (%s)...\n", deviceConfig->brokerHost, brokerIp.toString().c_str());
  if (mqttClient.connect(clientId, deviceConfig->brokerUser, deviceConfig->brokerPassword)) {
    logPrintf("Broker MQTT conectado.\n");
  } else {
    logPrintf("Conexão com o broker falhou, rc=%d\n", mqttClient.state());
    if (mqttClient.state() == MQTT_CONNECT_BAD_CREDENTIALS || mqttClient.state() == MQTT_CONNECT_UNAUTHORIZED) {
      logPrintf("Usuário ou senha MQTT recusados: segure BOOT para reabrir o portal e corrigir.\n");
    }
  }
}

void mqttLoop() {
  mqttClient.loop();
}

static bool isoTimestampUtc(char *buf, size_t len) {
  const time_t utcEpoch = time(nullptr);
  if (utcEpoch < 1700000000) return false;

  struct tm timeinfo;
  gmtime_r(&utcEpoch, &timeinfo);
  strftime(buf, len, "%Y-%m-%dT%H:%M:%SZ", &timeinfo);
  return true;
}

void mqttPublishReading(const SensorReadings &readings) {
  if (!mqttClient.connected()) return;

  JsonDocument doc;
  char timestampBuf[25];
  if (isoTimestampUtc(timestampBuf, sizeof(timestampBuf))) {
    doc["timestamp"] = timestampBuf;
  }
  if (!isnan(readings.powerW)) doc["power_w"] = readings.powerW;
  if (!isnan(readings.panelTempC)) doc["panel_temp_c"] = readings.panelTempC;
  if (!isnan(readings.ambientTempC)) doc["ambient_temp_c"] = readings.ambientTempC;
  if (!isnan(readings.ambientHumidityPct)) doc["ambient_humidity_pct"] = readings.ambientHumidityPct;
  doc["irradiance"] = readings.irradiancePct;
  if (!isnan(readings.pressureHpa)) doc["pressure_hpa"] = readings.pressureHpa;
  if (!isnan(readings.particulatePct)) doc["particulate_pct"] = readings.particulatePct;
  if (provisioningInPairingWindow()) doc["pairing_mode"] = true;

  char payload[384];
  const size_t payloadLen = serializeJson(doc, payload, sizeof(payload));
  mqttClient.publish(topic, (const uint8_t *)payload, payloadLen, false);

  logPrintf("Publicado em %s: %s\n", topic, payload);
}
