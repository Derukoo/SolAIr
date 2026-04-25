#include <Arduino.h>
#include "sensors.h"
#include "mqtt_client.h"

#ifndef DEVICE_ID
  #define DEVICE_ID "unknown"
#endif
#define XSTR(x) #x
#define STR(x)  XSTR(x)

void setup() {
    Serial.begin(115200);
    while (!Serial) {}

    Serial.printf("=== SolAIr Sensor Monitor [%s] ===\n", STR(DEVICE_ID));

    sensors_init();
    network_init();

    Serial.println("Temp(C) | Humidity(%) | Lux | Voltage(V) | Current(A)");
    Serial.println("--------|-------------|-----|------------|----------");
}

void loop() {
    mqtt_loop();

    SensorData d = sensors_read();

    // Serial output (same format as before)
    if (!d.dht_ok) {
       Serial.print("[ERROR] DHT11 read failed");
    } else {
       Serial.printf("%.1f C\t| %.1f %%\t\t| ", d.temperature, d.humidity);
    }

    if (!d.lux_ok) {
       Serial.print("[ERROR] BH1750\t| ");
    } else {
       Serial.printf("%.1f lx\t| ", d.lux);
    }

    Serial.printf("%.2f V\t| %.3f A\n", d.voltage, d.current);

    // Publish over MQTT
    mqtt_publish(d);

    delay(2000);
}
