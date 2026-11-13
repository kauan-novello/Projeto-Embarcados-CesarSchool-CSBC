#include "logger.h"
#include <Arduino.h>
#include <freertos/FreeRTOS.h>
#include <freertos/semphr.h>
#include <stdarg.h>

static const TickType_t LOG_LOCK_TIMEOUT = pdMS_TO_TICKS(200);

static SemaphoreHandle_t serialMutex = nullptr;

void logInit() {
  serialMutex = xSemaphoreCreateMutex();
}

void logPrintf(const char *format, ...) {
  char line[512];
  va_list args;
  va_start(args, format);
  vsnprintf(line, sizeof(line), format, args);
  va_end(args);

  if (serialMutex == nullptr || xSemaphoreTake(serialMutex, LOG_LOCK_TIMEOUT) != pdTRUE) return;
  Serial.print(line);
  xSemaphoreGive(serialMutex);
}
