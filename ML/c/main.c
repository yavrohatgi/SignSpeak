#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/adc.h"
#include "hardware/i2c.h"
#include "tensorflow/lite/micro/all_ops_resolver.h"
#include "tensorflow/lite/micro/micro_error_reporter.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/schema/schema_generated.h"
#include "tensorflow/lite/version.h"

// Include the model data
extern const unsigned char g_model[];
extern const unsigned int g_model_len;

// I2C and ADC configurations
#define I2C_PORT i2c0
#define SCL_PIN 5
#define SDA_PIN 4
#define FLEX_PIN 26

// TensorFlow Lite Micro configurations
#define TENSOR_ARENA_SIZE 1024 * 16
uint8_t tensor_arena[TENSOR_ARENA_SIZE];

void setup_hardware() {
    // Initialize I2C
    i2c_init(I2C_PORT, 100 * 1000);
    gpio_set_function(SDA_PIN, GPIO_FUNC_I2C);
    gpio_set_function(SCL_PIN, GPIO_FUNC_I2C);
    gpio_pull_up(SDA_PIN);
    gpio_pull_up(SCL_PIN);

    // Initialize ADC
    adc_init();
    adc_gpio_init(FLEX_PIN);
    adc_select_input(0); // FLEX_PIN must be connected to ADC channel 0
}

float read_flex_angle() {
    uint16_t adc_value = adc_read();
    float voltage = (adc_value / 4095.0) * 3.3; // Convert ADC value to voltage
    float resistance = 10000.0 * (3.3 / voltage - 1.0); // Calculate resistance
    float angle = 90.0 - (90.0 * resistance / 100000.0); // Map resistance to angle
    if (angle < 0) angle = 0;
    if (angle > 90) angle = 90;
    return angle;
}

void read_imu_data(float *acc, float *gyro) {
    uint8_t reg = 0x12;  // Example register for BMI270 data
    uint8_t buffer[12];

    i2c_write_blocking(I2C_PORT, 0x68, &reg, 1, true);  // BMI270 I2C address
    i2c_read_blocking(I2C_PORT, 0x68, buffer, 12, false);

    // Convert raw IMU data to readable values
    acc[0] = (int16_t)(buffer[0] << 8 | buffer[1]) / 16384.0;
    acc[1] = (int16_t)(buffer[2] << 8 | buffer[3]) / 16384.0;
    acc[2] = (int16_t)(buffer[4] << 8 | buffer[5]) / 16384.0;

    gyro[0] = (int16_t)(buffer[6] << 8 | buffer[7]) / 131.0;
    gyro[1] = (int16_t)(buffer[8] << 8 | buffer[9]) / 131.0;
    gyro[2] = (int16_t)(buffer[10] << 8 | buffer[11]) / 131.0;
}

void run_inference(float *data, int *predicted_index) {
    // Set up TensorFlow Lite Micro
    static tflite::MicroErrorReporter error_reporter;
    static tflite::AllOpsResolver resolver;
    static tflite::MicroInterpreter interpreter(
        tflite::GetModel(g_model), resolver, tensor_arena, TENSOR_ARENA_SIZE, &error_reporter);

    // Allocate tensors
    interpreter.AllocateTensors();

    // Fill input tensor with data
    TfLiteTensor *input = interpreter.input(0);
    for (int i = 0; i < 28; i++) {
        input->data.f[i] = data[i];
    }

    // Run inference
    interpreter.Invoke();

    // Read output tensor and find the class with the highest probability
    TfLiteTensor *output = interpreter.output(0);
    *predicted_index = 0;
    float max_value = output->data.f[0];
    for (int i = 1; i < 4; i++) {
        if (output->data.f[i] > max_value) {
            max_value = output->data.f[i];
            *predicted_index = i;
        }
    }
}

int main() {
    stdio_init_all();
    setup_hardware();

    float acc[3], gyro[3];
    float data[28];
    int predicted_index;
    const char *gesture_labels[] = {"left", "right", "up", "down"};

    printf("Starting real-time gesture detection...\n");

    while (1) {
        printf("Collecting data...\n");
        for (int i = 0; i < 4; i++) {  // Collect data at 4 time intervals
            read_imu_data(acc, gyro);
            float flex_angle = read_flex_angle();

            int offset = i * 7;
            data[offset] = acc[0];
            data[offset + 1] = acc[1];
            data[offset + 2] = acc[2];
            data[offset + 3] = gyro[0];
            data[offset + 4] = gyro[1];
            data[offset + 5] = gyro[2];
            data[offset + 6] = flex_angle;

            sleep_ms(250);  // Wait 0.25 seconds
        }

        printf("Running inference...\n");
        run_inference(data, &predicted_index);
        printf("Predicted Gesture: %s\n", gesture_labels[predicted_index]);
        sleep_ms(2000);  // Wait 2 seconds before the next prediction
    }

    return 0;
}