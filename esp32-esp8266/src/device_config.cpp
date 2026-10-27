#include "device_config.h"
#include "config.h"
#include <Preferences.h>
#include <esp_system.h>

static const char *NVS_NAMESPACE = "solarsense";

static String readString(Preferences &prefs, const char *key, const char *fallback) {
  return prefs.isKey(key) ? prefs.getString(key) : String(fallback);
}

void deviceConfigLoad(DeviceConfig &config) {
  Preferences prefs;
  prefs.begin(NVS_NAMESPACE, false);
  readString(prefs, "broker_host", DEFAULT_MQTT_BROKER_HOST).toCharArray(config.brokerHost, sizeof(config.brokerHost));
  config.brokerPort = prefs.isKey("broker_port") ? prefs.getUShort("broker_port") : DEFAULT_MQTT_BROKER_PORT;
  readString(prefs, "broker_user", "").toCharArray(config.brokerUser, sizeof(config.brokerUser));
  readString(prefs, "broker_pass", "").toCharArray(config.brokerPassword, sizeof(config.brokerPassword));
  config.pairingPending = prefs.isKey("pairing") && prefs.getBool("pairing");
  prefs.end();
}

void deviceConfigSave(const DeviceConfig &config) {
  Preferences prefs;
  prefs.begin(NVS_NAMESPACE, false);
  prefs.putString("broker_host", config.brokerHost);
  prefs.putUShort("broker_port", config.brokerPort);
  prefs.putString("broker_user", config.brokerUser);
  prefs.putString("broker_pass", config.brokerPassword);
  prefs.putBool("pairing", config.pairingPending);
  prefs.end();
}

bool deviceConfigIsComplete(const DeviceConfig &config) {
  return config.brokerHost[0] != '\0' && config.brokerPort != 0 && config.brokerUser[0] != '\0' &&
         config.brokerPassword[0] != '\0';
}

const char *deviceId() {
  static char id[13] = "";
  if (id[0] == '\0') {
    uint8_t mac[6];
    esp_efuse_mac_get_default(mac);
    snprintf(id, sizeof(id), "%02X%02X%02X%02X%02X%02X", mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
  }
  return id;
}
