#include "tasks.h"
#include "config.h"
#include "logger.h"
#include "mqtt_publisher.h"
#include "provisioning.h"
#include "sensors.h"
#include <Arduino.h>
#include <WiFi.h>
#include <freertos/FreeRTOS.h>
#include <freertos/queue.h>
#include <freertos/task.h>

static const uint32_t SENSOR_STACK_BYTES = 4096;
static const uint32_t MQTT_STACK_BYTES = 8192;
static const uint32_t WIFI_STACK_BYTES = 3072;
static const uint32_t BUTTON_STACK_BYTES = 10240;

static const UBaseType_t MQTT_PRIORITY = 3;
static const UBaseType_t SENSOR_PRIORITY = 2;
static const UBaseType_t BUTTON_PRIORITY = 2;
static const UBaseType_t WIFI_PRIORITY = 1;

static const uint32_t MQTT_QUEUE_WAIT_MS = 50;
static const uint32_t WIFI_CHECK_INTERVAL_MS = 5000;
static const uint32_t BUTTON_POLL_MS = 50;
static const uint32_t BUTTON_DEBOUNCE_MS = 50;

static QueueHandle_t readingsQueue = nullptr;
static TaskHandle_t buttonTaskHandle = nullptr;
static DeviceConfig *deviceConfig = nullptr;
static volatile uint32_t lastButtonEdgeMs = 0;

static void IRAM_ATTR onButtonPressed() {
  const uint32_t now = millis();
  if (now - lastButtonEdgeMs < BUTTON_DEBOUNCE_MS) return;
  lastButtonEdgeMs = now;

  BaseType_t higherPriorityWoken = pdFALSE;
  vTaskNotifyGiveFromISR(buttonTaskHandle, &higherPriorityWoken);
  if (higherPriorityWoken) portYIELD_FROM_ISR();
}

static void sensorTask(void *) {
  TickType_t lastWake = xTaskGetTickCount();
  for (;;) {
    const SensorReadings readings = readSensors();
    if (readings.valid) {
      xQueueOverwrite(readingsQueue, &readings);
    } else {
      logPrintf("Leitura de sensor inválida, pulando publicação.\n");
    }
    vTaskDelayUntil(&lastWake, pdMS_TO_TICKS(PUBLISH_INTERVAL_MS));
  }
}

static void mqttTask(void *) {
  SensorReadings readings;
  for (;;) {
    mqttEnsureConnected();
    mqttLoop();
    if (xQueueReceive(readingsQueue, &readings, pdMS_TO_TICKS(MQTT_QUEUE_WAIT_MS)) == pdTRUE) {
      mqttPublishReading(readings);
    }
  }
}

static void wifiTask(void *) {
  for (;;) {
    vTaskDelay(pdMS_TO_TICKS(WIFI_CHECK_INTERVAL_MS));
    if (WiFi.status() != WL_CONNECTED) {
      logPrintf("Wi-Fi desconectado; tentando reconectar.\n");
      WiFi.reconnect();
    }
  }
}

static bool buttonHeldForPortal() {
  const TickType_t pressedAt = xTaskGetTickCount();
  while (xTaskGetTickCount() - pressedAt < pdMS_TO_TICKS(CONFIG_BUTTON_HOLD_MS)) {
    if (digitalRead(PIN_CONFIG_BUTTON) == HIGH) return false;
    vTaskDelay(pdMS_TO_TICKS(BUTTON_POLL_MS));
  }
  return true;
}

static void buttonTask(void *) {
  for (;;) {
    ulTaskNotifyTake(pdTRUE, portMAX_DELAY);
    if (buttonHeldForPortal()) provisioningOpenPortal(*deviceConfig);
  }
}

void tasksStart(DeviceConfig &config) {
  deviceConfig = &config;
  readingsQueue = xQueueCreate(1, sizeof(SensorReadings));
  pinMode(PIN_CONFIG_BUTTON, INPUT_PULLUP);

  xTaskCreatePinnedToCore(sensorTask, "sensors", SENSOR_STACK_BYTES, nullptr, SENSOR_PRIORITY, nullptr, APP_CPU_NUM);
  xTaskCreatePinnedToCore(mqttTask, "mqtt", MQTT_STACK_BYTES, nullptr, MQTT_PRIORITY, nullptr, APP_CPU_NUM);
  xTaskCreatePinnedToCore(wifiTask, "wifi", WIFI_STACK_BYTES, nullptr, WIFI_PRIORITY, nullptr, APP_CPU_NUM);
  xTaskCreatePinnedToCore(buttonTask, "button", BUTTON_STACK_BYTES, nullptr, BUTTON_PRIORITY, &buttonTaskHandle,
                          APP_CPU_NUM);

  attachInterrupt(digitalPinToInterrupt(PIN_CONFIG_BUTTON), onButtonPressed, FALLING);
}
