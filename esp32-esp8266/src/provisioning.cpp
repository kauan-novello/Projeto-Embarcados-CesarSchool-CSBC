#include "provisioning.h"
#include "config.h"
#include "logger.h"
#include <WiFi.h>
#include <WiFiManager.h>

static WiFiManager wifiManager;
static char apName[24];
static char portBuf[6];
static DeviceConfig *activeConfig = nullptr;
static unsigned long pairingWindowEndsAt = 0;

static WiFiManagerParameter brokerHostParam("broker_host", "Servidor (IP ou nome .local)", "", 63);
static WiFiManagerParameter brokerPortParam("broker_port", "Porta MQTT", "", 5);
static WiFiManagerParameter brokerUserParam("broker_user", "Usuário MQTT", "", 31);
static WiFiManagerParameter brokerPasswordParam("broker_pass", "Senha MQTT (vazio mantém a atual)", "", 63,
                                                "type=\"password\"");

static void onParamsSaved() {
  String host(brokerHostParam.getValue());
  host.trim();
  host.toCharArray(activeConfig->brokerHost, sizeof(activeConfig->brokerHost));
  activeConfig->brokerPort = (uint16_t)atoi(brokerPortParam.getValue());
  String user(brokerUserParam.getValue());
  user.trim();
  user.toCharArray(activeConfig->brokerUser, sizeof(activeConfig->brokerUser));
  if (strlen(brokerPasswordParam.getValue()) > 0) {
    strlcpy(activeConfig->brokerPassword, brokerPasswordParam.getValue(), sizeof(activeConfig->brokerPassword));
  }
  activeConfig->pairingPending = true;
  deviceConfigSave(*activeConfig);
  logPrintf("Configuração salva: servidor %s:%u\n", activeConfig->brokerHost, activeConfig->brokerPort);
}

static void fillParams(const DeviceConfig &config) {
  snprintf(portBuf, sizeof(portBuf), "%u", config.brokerPort);
  brokerHostParam.setValue(config.brokerHost, 63);
  brokerPortParam.setValue(portBuf, 5);
  brokerUserParam.setValue(config.brokerUser, 31);
}

static void setupPortal(DeviceConfig &config) {
  activeConfig = &config;
  snprintf(apName, sizeof(apName), "%s%s", CONFIG_AP_PREFIX, deviceId() + 8);
  fillParams(config);

  wifiManager.setTitle("SolarSense");
  wifiManager.addParameter(&brokerHostParam);
  wifiManager.addParameter(&brokerPortParam);
  wifiManager.addParameter(&brokerUserParam);
  wifiManager.addParameter(&brokerPasswordParam);
  wifiManager.setSaveParamsCallback(onParamsSaved);
  wifiManager.setConnectTimeout(WIFI_CONNECT_TIMEOUT_S);
  wifiManager.setConfigPortalTimeout(CONFIG_PORTAL_TIMEOUT_S);
}

static void rebootUnlessReady(bool connected) {
  if (!connected || !deviceConfigIsComplete(*activeConfig)) {
    logPrintf("Configuração incompleta ou Wi-Fi indisponível; reiniciando para tentar de novo.\n");
    delay(1000);
    ESP.restart();
  }
}

void provisioningBegin(DeviceConfig &config) {
  WiFi.mode(WIFI_STA);
  setupPortal(config);

  bool connected;
  if (deviceConfigIsComplete(config)) {
    logPrintf("Dispositivo %s: conectando ao Wi-Fi salvo (sem Wi-Fi, abre o portal %s, senha %s)...\n",
                  deviceId(), apName, CONFIG_AP_PASSWORD);
    connected = wifiManager.autoConnect(apName, CONFIG_AP_PASSWORD);
  } else {
    logPrintf("Sem configuração: portal aberto na rede %s (senha %s)\n", apName, CONFIG_AP_PASSWORD);
    connected = wifiManager.startConfigPortal(apName, CONFIG_AP_PASSWORD);
  }
  rebootUnlessReady(connected);

  WiFi.setAutoReconnect(true);
  logPrintf("Wi-Fi conectado, IP: %s\n", WiFi.localIP().toString().c_str());

  if (config.pairingPending) {
    pairingWindowEndsAt = millis() + PAIRING_WINDOW_MS;
    config.pairingPending = false;
    deviceConfigSave(config);
    logPrintf("Modo pareamento por %lu min: vincule %s pelo app.\n", PAIRING_WINDOW_MS / 60000UL, apName);
  }
}

bool provisioningInPairingWindow() {
  return pairingWindowEndsAt != 0 && (long)(pairingWindowEndsAt - millis()) > 0;
}

void provisioningOpenPortal(DeviceConfig &config) {
  logPrintf("Botão BOOT segurado: portal aberto na rede %s (senha %s)\n", apName, CONFIG_AP_PASSWORD);
  fillParams(config);
  wifiManager.startConfigPortal(apName, CONFIG_AP_PASSWORD);
  ESP.restart();
}
