#include <stdio.h>
#include <math.h>
#include "pico/stdlib.h"
#include "hardware/i2c.h"
#include "hardware/adc.h"
#include <string.h>
#include <Wire.h>
#include "SparkFun_BMI270_Arduino_Library.h"

// Constants
#define NUM_FEATURES 30  // (6 IMU readings * 5 fingers)
#define NUM_SAMPLES 10   // 10 time samples (0.1s, 0.2s, ..., 1s)
#define GESTURE_COUNT 5  // 5 gestures
#define SAMPLE_COUNT 25  // 25 samples per gesture

// Gesture labels
const char* gestures[] = {"food", "hello", "yes", "please", "bathroom"};

// Sensor objects
BMI270 imu0, imu1, imu2, imu3, imu4;
uint8_t multiplexerAddress = 0x70;
uint8_t i2cAddress = BMI2_I2C_PRIM_ADDR;  // 0x68
uint8_t connected_imus[5] = {0, 1, 2, 3, 7}; // 5 IMUs

// Store IMU data globally
float feature_vector[NUM_FEATURES * NUM_SAMPLES];  // 300 values (30 features × 10 samples)

// Helper function: Switch I2C multiplexer
void tcaselect(uint8_t channel) {
    if (channel > 7) return;
    Wire.beginTransmission(multiplexerAddress);
    Wire.write(1 << channel);
    Wire.endTransmission();
}

// Setup IMUs
void setup_multiplexer_IMUs() {
    Serial.begin(115200);
    while (!Serial);
    Wire.begin();
    delay(500);  

    for (int i = 0; i < 5; i++) {
        tcaselect(connected_imus[i]);
        BMI270* imu_ptr = nullptr;

        switch (connected_imus[i]) {
            case 0: imu_ptr = &imu0; break;
            case 1: imu_ptr = &imu1; break;
            case 2: imu_ptr = &imu2; break;
            case 3: imu_ptr = &imu3; break;
            case 7: imu_ptr = &imu4; break;
        }

        if (imu_ptr) {
            while (imu_ptr->beginI2C(i2cAddress) != BMI2_OK) {
                Serial.print("Error: BMI270 not connected at IMU ");
                Serial.println(connected_imus[i]);
                delay(1000);
            }
        }
    }
    Serial.println("All BMI270 sensors connected!");
}

// Read and store IMU data
void store_IMU_reading(BMI270* curr_imu, uint8_t imu_index, float* buffer, int offset) {
    tcaselect(imu_index);

    if (curr_imu->getSensorData() == BMI2_OK) {
        buffer[offset]   = curr_imu->data.accelX;
        buffer[offset+1] = curr_imu->data.accelY;
        buffer[offset+2] = curr_imu->data.accelZ;
        buffer[offset+3] = curr_imu->data.gyroX;
        buffer[offset+4] = curr_imu->data.gyroY;
        buffer[offset+5] = curr_imu->data.gyroZ;
    } else {
        Serial.print("❌ IMU Read Failed: ");
        Serial.println(imu_index);
    }
}

void setup() {
    setup_multiplexer_IMUs();
}

void capture_sample(float* feature_vector) {
    for (int t = 0; t < NUM_SAMPLES; t++) {  
        for (int j = 0; j < 5; j++) {  
            BMI270* curr_imu;
            switch (connected_imus[j]) {
                case 0: curr_imu = &imu0; break;
                case 1: curr_imu = &imu1; break;
                case 2: curr_imu = &imu2; break;
                case 3: curr_imu = &imu3; break;
                case 7: curr_imu = &imu4; break;
                default: continue;
            }

            // Corrected offset calculation (dont use uint -> stops at 255 and we need 300 values)
            int offset = (t * 5 * 6) + (j * 6);  // 5 IMUs * 6 values per IMU
            store_IMU_reading(curr_imu, connected_imus[j], feature_vector, offset);
        }
    }
}

// Main loop: Collect samples for all gestures
void loop() {
    Serial.println("Start collecting training data...");

    for (int g = 0; g < GESTURE_COUNT; g++) {
        Serial.print("\nStarting gesture: ");
        Serial.println(gestures[g]);

        for (int s = 0; s < SAMPLE_COUNT; s++) {
            Serial.print("Doing ");
            Serial.print(gestures[g]);
            Serial.print(" sample #");
            Serial.println(s + 1);

            // Countdown
            Serial.println("In 3...");
            delay(1000);
            Serial.println("In 2...");
            delay(1000);
            Serial.println("In 1...");
            delay(1000);
            Serial.println("Now!");
            delay(200); // slight delay so user starts correctly

            // 🚀 **DO NOT RESET BUFFER**
            // memset(feature_vector, 0, sizeof(feature_vector)); <-- ❌ REMOVE THIS

            // Collect samples
            capture_sample(feature_vector);

            // Print collected data (exactly 300 values)
            Serial.print("Gesture: ");
            Serial.print(gestures[g]);
            Serial.print(" Sample: ");
            Serial.println(s+1);

            for (int i = 0; i < NUM_FEATURES * NUM_SAMPLES; i++) {
                Serial.print(feature_vector[i], 4);
                Serial.print((i < (NUM_FEATURES * NUM_SAMPLES) - 1) ? " " : "\n");
            }

            // Ensure 300 values per sample
            Serial.print("\nTotal values recorded: ");
            Serial.println(NUM_FEATURES * NUM_SAMPLES);
        }
        Serial.println("Gesture done.");
    }

    Serial.println("Training data collection complete.");
    while (1); // Stop loop
}