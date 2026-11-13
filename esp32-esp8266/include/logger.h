#pragma once

void logInit();
void logPrintf(const char *format, ...) __attribute__((format(printf, 1, 2)));
