#pragma once

#include <Arduino.h>
#include <DHT.h>
#include <BH1750.h>

struct SensorData {
    float temperature;  // Celsius
    float humidity;     // %
    float lux;
    float voltage;      // V
    float current;      // A
    bool  dht_ok;
    bool  lux_ok;
};

void sensors_init();
SensorData sensors_read();
