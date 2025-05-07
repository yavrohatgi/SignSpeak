#include <Wire.h>
#include "SparkFun_BMI270_Arduino_Library.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/micro/micro_mutable_op_resolver.h"
#include "tensorflow/lite/schema/schema_generated.h"
#include "SIGNSPEAK_MLP_full_model.h"

#define NUM_FEATURES 30
#define NUM_SAMPLES 10
#define GESTURE_COUNT 5
#define TENSOR_ARENA_SIZE 40 * 1024

const char* gestures[] = {"food", "hello", "yes", "please", "bathroom"};
const uint8_t connected_imus[5] = {0, 1, 2, 3, 7};
BMI270 imus[5];
float feature_vector[NUM_FEATURES * NUM_SAMPLES];
uint8_t tensor_arena[TENSOR_ARENA_SIZE];
const tflite::Model* model = nullptr;
tflite::MicroInterpreter* interpreter = nullptr;
TfLiteTensor* input = nullptr;
TfLiteTensor* output = nullptr;
uint8_t multiplexerAddress = 0x70;

void tcaselect(uint8_t channel) {
    if (channel > 7) return;
    Wire.beginTransmission(multiplexerAddress);
    Wire.write(1 << channel);
    Wire.endTransmission();
}

void setup_IMUs() {
    Wire.begin();
    delay(500);
    for (int i = 0; i < 5; i++) {
        tcaselect(connected_imus[i]);
        if (!imus[i].beginI2C(BMI2_I2C_PRIM_ADDR)) {
            Serial.printf("IMU %d failed to initialize!\n", connected_imus[i]);
        }
    }
}

void store_IMU_reading(int imu_index, float* buffer, int offset) {
    tcaselect(connected_imus[imu_index]);
    if (imus[imu_index].getSensorData() == BMI2_OK) {
        buffer[offset] = imus[imu_index].getAccelX();
        buffer[offset + 1] = imus[imu_index].getAccelY();
        buffer[offset + 2] = imus[imu_index].getAccelZ();
        buffer[offset + 3] = imus[imu_index].getGyroX();
        buffer[offset + 4] = imus[imu_index].getGyroY();
        buffer[offset + 5] = imus[imu_index].getGyroZ();
    } else {
        Serial.printf("IMU %d reading failed!\n", connected_imus[imu_index]);
    }
}

void capture_sample(float* feature_vector) {
    for (int t = 0; t < NUM_SAMPLES; t++) {
        for (int j = 0; j < 5; j++) {
            store_IMU_reading(j, feature_vector, (t * NUM_FEATURES) + (j * 6));
        }
        delay(100);
    }
}

void setup() {
    Serial.begin(115200);
    Wire.begin();
    setup_IMUs();
    Serial.println("Initializing TensorFlow Lite model...");
    model = tflite::GetModel(g_SIGNSPEAK_MLP_full_model);
    if (model->version() != TFLITE_SCHEMA_VERSION) {
        Serial.println("Model schema mismatch!");
        return;
    }
    static tflite::MicroMutableOpResolver<10> resolver;
    resolver.AddFullyConnected();
    resolver.AddRelu();
    resolver.AddSoftmax();
    static tflite::MicroInterpreter static_interpreter(model, resolver, tensor_arena, TENSOR_ARENA_SIZE);
    interpreter = &static_interpreter;
    if (interpreter->AllocateTensors() != kTfLiteOk) {
        Serial.println("Tensor allocation failed!");
        return;
    }
    input = interpreter->input(0);
    output = interpreter->output(0);
    Serial.println("Setup complete, ready to infer!");
}

void loop() {
    Serial.println("Get ready to sign in 3... 2... 1...");
    delay(3000);
    capture_sample(feature_vector);
    if (NUM_FEATURES * NUM_SAMPLES != input->bytes / sizeof(float)) {
        Serial.println("Feature vector size mismatch!");
        return;
    }
    for (int i = 0; i < NUM_FEATURES * NUM_SAMPLES; i++) {
        input->data.f[i] = feature_vector[i];
    }
    if (interpreter->Invoke() != kTfLiteOk) {
        Serial.println("Inference failed!");
        return;
    }
    int gesture_index = 0;
    float highest_confidence = output->data.f[0];
    for (int i = 1; i < GESTURE_COUNT; i++) {
        if (output->data.f[i] > highest_confidence) {
            highest_confidence = output->data.f[i];
            gesture_index = i;
        }
    }
    Serial.printf("The sign you did was: %s\n", gestures[gesture_index]);
    delay(3000);
}