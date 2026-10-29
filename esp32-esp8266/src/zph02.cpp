#include "zph02.h"
#include "config.h"
#include <Arduino.h>
#include <driver/gpio.h>

static const size_t FRAME_LEN = 9;
static const uint8_t FRAME_START = 0xFF;
static const uint8_t FRAME_TYPE_PARTICLES = 0x18;

static uint8_t frame[FRAME_LEN];
static size_t frameLen = 0;
static float lastPct = NAN;
static unsigned long lastFrameAt = 0;

void zph02Setup() {
  Serial2.begin(ZPH02_BAUD, SERIAL_8N1, PIN_ZPH02_RX, -1);
  gpio_pullup_en((gpio_num_t)PIN_ZPH02_RX);
}

static bool frameIsValid() {
  if (frame[0] != FRAME_START || frame[1] != FRAME_TYPE_PARTICLES) return false;
  uint8_t sum = 0;
  for (size_t i = 1; i < FRAME_LEN - 1; i++) sum += frame[i];
  return (uint8_t)(~sum + 1) == frame[FRAME_LEN - 1];
}

static void consumeByte(uint8_t b) {
  if (frameLen == 0 && b != FRAME_START) return;
  frame[frameLen++] = b;
  if (frameLen < FRAME_LEN) return;

  if (frameIsValid()) {
    lastPct = frame[3] + frame[4] / 100.0f;
    lastFrameAt = millis();
  }
  frameLen = 0;
}

float zph02ReadPct() {
  while (Serial2.available()) consumeByte(Serial2.read());
  if (lastFrameAt == 0 || millis() - lastFrameAt > ZPH02_STALE_MS) return NAN;
  return lastPct;
}
