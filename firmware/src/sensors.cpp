#include "sensors.h"
#include <Wire.h>

// --- Pin definitions ---
#define DHT_PIN       32
#define DHT_TYPE      DHT11
#define VOLTAGE_PIN   36   // ADC1_CH0 — input only
#define CURRENT_PIN   39   // ADC1_CH3 — input only

// --- Voltage sensor (0-25V module, R1=30k / R2=7.5k divider, ratio 1:5) ---
static constexpr float VOLTAGE_DIVIDER_RATIO = 5.0f;
static constexpr float ADC_REF               = 3.3f;
static constexpr int   ADC_RESOLUTION        = 4095;

// --- ACS712 5A (sensitivity 185 mV/A, midpoint 2.5V at 0A) ---
static constexpr float ACS712_SENSITIVITY = 0.185f;
static constexpr float ACS712_MIDPOINT    = 2.5f;

static constexpr int ADC_SAMPLES = 64;

static DHT    dht(DHT_PIN, DHT_TYPE);
static BH1750 lightMeter;

static float readADC_V(int pin) {
    long sum = 0;
    for (int i = 0; i < ADC_SAMPLES; i++) {
        sum += analogRead(pin);
    }
    return (sum / (float)ADC_SAMPLES / ADC_RESOLUTION) * ADC_REF;
}

void sensors_init() {
    Wire.begin();  // SDA=21, SCL=22
    dht.begin();

    if (!lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE)) {
        Serial.println("[ERROR] BH1750 not found — check wiring on SDA/SCL");
    }
}

SensorData sensors_read() {
    SensorData d;

    d.temperature = dht.readTemperature();
    d.humidity    = dht.readHumidity();
    d.dht_ok      = !(isnan(d.temperature) || isnan(d.humidity));

    d.lux    = lightMeter.readLightLevel();
    d.lux_ok = (d.lux >= 0);

    float rawV = readADC_V(VOLTAGE_PIN);
    d.voltage  = rawV * VOLTAGE_DIVIDER_RATIO;

    float sensorV = readADC_V(CURRENT_PIN);
    d.current     = (sensorV - ACS712_MIDPOINT) / ACS712_SENSITIVITY;

    return d;
}
