#include "pico/stdlib.h"
#include "hardware/i2c.h"
#include "hardware/adc.h"
#include "tensorflow/lite/micro/all_ops_resolver.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "model_data.h"

// To do inference on the Raspberry Pi Pico
// TensorFlow Lite configuration
#define TENSOR_ARENA_SIZE 2000
uint8_t tensor_arena[TENSOR_ARENA_SIZE];

// I2C and ADC configuration
#define I2C_PORT i2c0
#define SDA_PIN 0
#define SCL_PIN 1
#define FLEX_ADC_PIN 26
#define I2C_ADDR_BMI270 0x68

// Function prototypes
void init_i2c();
void init_adc();
void read_bmi270(float *accel, float *gyro);
float read_flex_angle();
void run_inference(float *input_data);

void init_i2c() {
    i2c_init(I2C_PORT, 100000); // 100 kHz
    gpio_set_function(SDA_PIN, GPIO_FUNC_I2C);
    gpio_set_function(SCL_PIN, GPIO_FUNC_I2C);
    gpio_pull_up(SDA_PIN);
    gpio_pull_up(SCL_PIN);
}

void init_adc() {
    adc_init();
    adc_gpio_init(FLEX_ADC_PIN); // GPIO 26
    adc_select_input(0); // ADC input 0
}

void read_bmi270(float *accel, float *gyro) {
    uint8_t reg = 0x12; // Example register for acceleration
    uint8_t buffer[12];

    i2c_write_blocking(I2C_PORT, I2C_ADDR_BMI270, &reg, 1, true);
    i2c_read_blocking(I2C_PORT, I2C_ADDR_BMI270, buffer, 12, false);

    accel[0] = (int16_t)((buffer[0] << 8) | buffer[1]) / 16384.0;
    accel[1] = (int16_t)((buffer[2] << 8) | buffer[3]) / 16384.0;
    accel[2] = (int16_t)((buffer[4] << 8) | buffer[5]) / 16384.0;

    gyro[0] = (int16_t)((buffer[6] << 8) | buffer[7]) / 131.0;
    gyro[1] = (int16_t)((buffer[8] << 8) | buffer[9]) / 131.0;
    gyro[2] = (int16_t)((buffer[10] << 8) | buffer[11]) / 131.0;
}

float read_flex_angle() {
    uint16_t adc_value = adc_read();
    float voltage = adc_value * (3.3 / 4095.0);
    float resistance = 10000.0 * (3.3 / voltage - 1.0);
    float angle = 90.0 - (90.0 * resistance / 7000.0);

    if (angle > 90.0) angle = 90.0;
    if (angle < 0.0) angle = 0.0;

    return angle;
}

void run_inference(float *input_data) {
    static tflite::MicroInterpreter *interpreter = nullptr;

    if (!interpreter) {
        const tflite::Model *model = tflite::GetModel(model_tflite);
        static tflite::AllOpsResolver resolver;
        interpreter = new tflite::MicroInterpreter(model, resolver, tensor_arena, TENSOR_ARENA_SIZE);
        interpreter->AllocateTensors();
    }

    TfLiteTensor *input = interpreter->input(0);
    for (int i = 0; i < input->dims->data[0]; ++i) {
        input->data.f[i] = input_data[i];
    }

    interpreter->Invoke();

    TfLiteTensor *output = interpreter->output(0);
    int predicted_index = 0;
    float max_value = output->data.f[0];
    for (int i = 1; i < output->dims->data[0]; ++i) {
        if (output->data.f[i] > max_value) {
            max_value = output->data.f[i];
            predicted_index = i;
        }
    }

    const char *labels[] = {"right", "left", "up", "down"};
    printf("Predicted gesture: %s\n", labels[predicted_index]);
}

int main() {
    stdio_init_all();
    init_i2c();
    init_adc();

    while (true) {
        float input_data[7];
        read_bmi270(input_data, input_data + 3); // IMU data
        input_data[6] = read_flex_angle();      // Flex sensor data
        run_inference(input_data);
        sleep_ms(500);
    }

    return 0;
}