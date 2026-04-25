#pragma once

#include <Arduino.h>
#include "sensors.h"

void network_init();
bool mqtt_ensure_connected();
void mqtt_publish(const SensorData &data);
void mqtt_loop();
