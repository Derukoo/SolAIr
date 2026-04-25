#include "mqtt_client.h"
#include <WiFi.h>
#include <PubSubClient.h>

// These macros are injected by load_settings.py from settings.ini.
// Provide fallbacks so the IDE doesn't flag them.
#ifndef WIFI_SSID
  #define WIFI_SSID     "CHANGE_ME"
#endif
#ifndef WIFI_PASSWORD
  #define WIFI_PASSWORD "CHANGE_ME"
#endif
#ifndef MQTT_BROKER_IP
  #define MQTT_BROKER_IP "192.168.1.100"
#endif
#ifndef MQTT_BROKER_PORT
  #define MQTT_BROKER_PORT 1883
#endif
#ifndef MQTT_PREFIX
  #define MQTT_PREFIX "solair/unknown"
#endif
#ifndef DEVICE_ID
  #define DEVICE_ID "unknown"
#endif

// Stringify helper — turns a macro value into a C string literal
#define XSTR(x) #x
#define STR(x)  XSTR(x)

static WiFiClient   espClient;
static PubSubClient mqttClient(espClient);

static void wifi_connect() {
    Serial.printf("[WIFI] Connecting to %s password is %s ", WIFI_SSID, WIFI_PASSWORD);
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    int retries = 0;
    while (WiFi.status() != WL_CONNECTED && retries < 40) {
        delay(500);
        Serial.print('.');
        retries++;
    }
    if (WiFi.status() == WL_CONNECTED) {
        Serial.printf("\n[WIFI] Connected — IP: %s\n", WiFi.localIP().toString().c_str());
    } else {
        Serial.println("\n[WIFI] Connection FAILED — will retry next cycle");
    }
}

void network_init() {
    wifi_connect();
    mqttClient.setServer(MQTT_BROKER_IP, MQTT_BROKER_PORT);
}

bool mqtt_ensure_connected() {
    if (WiFi.status() != WL_CONNECTED) {
        wifi_connect();
        if (WiFi.status() != WL_CONNECTED) return false;
    }

    if (mqttClient.connected()) return true;

    Serial.printf("[MQTT] Connecting to %s:%d as %s ... ",
                  STR(MQTT_BROKER_IP), MQTT_BROKER_PORT, STR(DEVICE_ID));

    if (mqttClient.connect(STR(DEVICE_ID))) {
        Serial.println("OK");
        return true;
    }

    Serial.printf("FAILED (rc=%d)\n", mqttClient.state());
    return false;
}

static bool publish_float(const char *subtopic, float value, int decimals) {
    char topic[128];
    char payload[16];
    snprintf(topic, sizeof(topic), "%s/%s", MQTT_PREFIX, subtopic);
    dtostrf(value, 0, decimals, payload);
    return mqttClient.publish(topic, payload);
}

void mqtt_publish(const SensorData &data) {
    if (!mqtt_ensure_connected()) return;

    // Publish each sensor to its own subtopic:
    //   solair/<device-id>/temperature
    //   solair/<device-id>/humidity
    //   solair/<device-id>/lux
    //   solair/<device-id>/voltage
    //   solair/<device-id>/current
    int ok = 0, total = 0;

    if (data.dht_ok) {
        ok += publish_float("temperature", data.temperature, 1); total++;
        ok += publish_float("humidity",    data.humidity,    1); total++;
    }
    if (data.lux_ok) {
        ok += publish_float("lux", data.lux, 1); total++;
    }
    ok += publish_float("voltage", data.voltage, 2); total++;
    ok += publish_float("current", data.current, 3); total++;

    Serial.printf("[MQTT] Published %d/%d to %s/*\n", ok, total, MQTT_PREFIX);
}

void mqtt_loop() {
    mqttClient.loop();
}
