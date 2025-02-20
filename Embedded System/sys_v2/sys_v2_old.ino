#include <stdio.h>
#include <math.h>
#include "pico/stdlib.h"
#include "hardware/i2c.h"
#include "hardware/pio.h"
#include "hardware/interp.h"
#include "hardware/timer.h"
#include "hardware/adc.h"

#include <Wire.h>
#include "SparkFun_BMI270_Arduino_Library.h"

// variables used for caluculations of flex sensor readings
#define maxAngle_degrees  90.0
#define minAngle_degrees  0.0
#define dividing_resistance_ohms  10000.0
#define pico_output_voltage_volts  3.3
#define flex_max_resistance_ohms  100000.0
#define flex_min_resistance_ohms  25000.0

/*
So the average ASL sign length is 0.5-1 second long
So our sampling period should be the same
We should try the highest possible sampling rate to scalculate how many readings fit in one sample
Need to look into the capabilities of Tensorflow Lite
*/
#define NUM_READINGS 10
#define LABEL_LENGTH 20

struct single_finger_imu_reading{
    // TODO: CHANGE THIS TO FLOATS, SAVES STORAGE W/PRECISION TRADEOFF
        double acc_x[NUM_READINGS];
        double acc_y[NUM_READINGS];
        double acc_z[NUM_READINGS];
        double gyr_x[NUM_READINGS];
        double gyr_y[NUM_READINGS];
        double gyr_z[NUM_READINGS];
        double flex_angle[NUM_READINGS];
        char label[LABEL_LENGTH]; 
};


/*
Calculates p-norm of a given vector. 

Parameters: 
uint8_t: p, used for calculation. Default value of 2 - Euclidean norm. 
double*: vector, pointer to vector to get norm from
size_t: vector_length, length of given vector

Returns: 
double: norm, the calculated p-norm for the given array. 
*/ 
double calculate_p_norm(int p, double vector[], size_t vector_length){
        // TODO: make sure empty arguments are handled, eventually
        // calculate norm if p is nonzero, otherwise return the norm
        if(p != 0){
                double total_sum = 0;
                for(int i = 0; i < vector_length; i++){
                        total_sum += pow(vector[i], p);
                }
                double calculated_norm = pow(total_sum, 1/p);
                return calculated_norm;
        } else {
                // alternative option could be l0 norm, which is number of nonzero entries
                return 0;
        }
}

/*
Normalizes a given vector. Changes original vector rather than creating a new one, for storage saving.

Parameters: 
double: norm, pre-calculated, used to normalize
double*: vector, pointer to vector to normalize
size_t: vector_length, length of vector

Returns: 
None
*/
void normalize_vector(double norm, double vector[], size_t vector_length){
        for(int i = 0; i < vector_length; i++){
                vector[i] = vector[i]/norm; // store normalized value in ith value of normalized_vector
        }
}

/*
Maps a value from one range to another

Parameters:
double: x, value in original range
double: in_min, min value of original range
double: in_max, max value of original range
double: out_min, min value of desired range
double: out_max, max value of desired range

Returns:
double: mapping of x in output range
*/
double map(double x, double in_min, double in_max, double out_min, double out_max){
        return (double) (out_min + (x - in_min)*(out_max - out_min)/(in_max - in_min));
}

/*
Reads a value from flex sensor connected to specified pin. 

Parameters:
uint8_t: pin, number of pin to read from

Returns:
double: angle calculated using ADC reading from pin
*/
double read_flex_sensor(uint8_t pin){
        // EITHER 12 OR 16, PLAY WITH THIS ONCE THE THINGS ARE CONNECTED
        int num_bits = 12;
        const float conversionFactor = pico_output_voltage_volts / (1 << num_bits);
        double adc_voltage = (float) adc_read() * conversionFactor;
        double adc_resistance = dividing_resistance_ohms * (pico_output_voltage_volts / adc_voltage - 1.0);
        return map(adc_resistance, flex_min_resistance_ohms, flex_max_resistance_ohms, minAngle_degrees, maxAngle_degrees);
}

// Create a new sensor object
BMI270 imu0;
BMI270 imu1;
BMI270 imu2;
BMI270 imu3;
BMI270 imu7;

// I2C address selection
uint8_t i2cAddress = BMI2_I2C_PRIM_ADDR; // 0x68
// uint8_t i2cAddress = BMI2_I2C_SEC_ADDR; // 0x69
uint8_t multiplexerAddress = 0x70;

// Helper function for changing TCA output channel
void tcaselect(uint8_t channel) {
        if (channel > 7) return;
        Wire.beginTransmission(multiplexerAddress);
        Wire.write(1 << channel);
        Wire.endTransmission();
}

void setup_multiplexer_IMUs() {
    // Start serial
    Serial.begin(115200);
    while (!Serial);

    // Initialize the I2C library
    Wire.begin();

    // Check if sensor is connected and initialize
    uint8_t connected_imus[5] = {0, 1, 2, 3, 7};
    for (int i = 0; i < 5; i++) {
        tcaselect(connected_imus[i]);
        switch (connected_imus[i]) {
            case 0:
                while (imu0.beginI2C(i2cAddress) != BMI2_OK) {
                    Serial.print("Error: BMI270 not connected, check wiring and I2C address of IMU ");
                    Serial.println(connected_imus[i]);
                    delay(1000);
                }
                break;
            case 1:
                while (imu1.beginI2C(i2cAddress) != BMI2_OK) {
                    Serial.print("Error: BMI270 not connected, check wiring and I2C address of IMU ");
                    Serial.println(connected_imus[i]);
                    delay(1000);
                }
                break;
            case 2:
                while (imu2.beginI2C(i2cAddress) != BMI2_OK) {
                    Serial.print("Error: BMI270 not connected, check wiring and I2C address of IMU ");
                    Serial.println(connected_imus[i]);
                    delay(1000);
                }
                break;
            case 3:
                while (imu3.beginI2C(i2cAddress) != BMI2_OK) {
                    Serial.print("Error: BMI270 not connected, check wiring and I2C address of IMU ");
                    Serial.println(connected_imus[i]);
                    delay(1000);
                }
                break;
            case 7:
                while (imu7.beginI2C(i2cAddress) != BMI2_OK) {
                    Serial.print("Error: BMI270 not connected, check wiring and I2C address of IMU ");
                    Serial.println(connected_imus[i]);
                    delay(1000);
                }
                break;
        }
    }
    Serial.println("All BMI270 sensors connected!");
}

void read_IMU(uint8_t selected_imu) {
    tcaselect(selected_imu);
    BMI270* curr_imu;
    switch (selected_imu) {
        case 0: curr_imu = &imu0; break;
        case 1: curr_imu = &imu1; break;
        case 2: curr_imu = &imu2; break;
        case 3: curr_imu = &imu3; break;
        case 7: curr_imu = &imu7; break;
        default: return; // Invalid IMU selection
    }

    if (curr_imu->getSensorData() == BMI2_OK) {
        // Print acceleration data
        Serial.print("IMU ");
        Serial.print(selected_imu);
        Serial.print(": Acceleration in g's");
        Serial.print("\t");
        Serial.print("X: ");
        Serial.print(curr_imu->data.accelX, 3);
        Serial.print("\t");
        Serial.print("Y: ");
        Serial.print(curr_imu->data.accelY, 3);
        Serial.print("\t");
        Serial.print("Z: ");
        Serial.print(curr_imu->data.accelZ, 3);

        Serial.print("\t");

        // Print rotation data
        Serial.print("Rotation in deg/sec");
        Serial.print("\t");
        Serial.print("X: ");
        Serial.print(curr_imu->data.gyroX, 3);
        Serial.print("\t");
        Serial.print("Y: ");
        Serial.print(curr_imu->data.gyroY, 3);
        Serial.print("\t");
        Serial.print("Z: ");
        Serial.println(curr_imu->data.gyroZ, 3);

    } else {
        Serial.print("Error reading from IMU ");
        Serial.println(selected_imu);
    }

}

// stores the IMU reading in the provided BMI270 object
void store_IMU_reading(BMI270* curr_imu){
    if (curr_imu->getSensorData() == BMI2_OK) {
        // Print acceleration data
        Serial.print(curr_imu->data.accelX, 3);
        Serial.print(curr_imu->data.accelY, 3);
        Serial.print(curr_imu->data.accelZ, 3);

        // Print rotation data
        Serial.print(curr_imu->data.gyroX, 3);
        Serial.print(curr_imu->data.gyroY, 3);
        Serial.print(curr_imu->data.gyroZ, 3);

    } else {
        Serial.print("Error reading from IMU");
    }
}


void setup() {
        // this will be used to setup everything. 
        setup_multiplexer_IMUs();
}



void loop(){
        uint8_t connected_imus[5] = {0, 1, 2, 3, 7};
        // this loop works, reading sensor values and printing to terminal
        for(int i = 0; i < 5; i++){
                read_IMU(connected_imus[i]);
                // this will actually store the values in an array 
        }

        // trying to read one full sample
        single_finger_imu_reading* finger1;

        // read a single finger
        for(int reading = 0; reading < NUM_READINGS; reading++){
            BMI270* curr_imu;
            store_IMU_reading(curr_imu);
            finger1->acc_x[reading] = curr_imu->data.accelX;
            finger1->acc_y[reading] = curr_imu->data.accelY;
            finger1->acc_z[reading] = curr_imu->data.accelZ;
            finger1->gyr_x[reading] = curr_imu->data.gyroX;
            finger1->gyr_y[reading] = curr_imu->data.gyroY;
            finger1->gyr_z[reading] = curr_imu->data.gyroZ;

            // this is for all 5 fingers simultaneously
            // for(int imu_ind = 0; imu_ind < 5; imu_ind++){
            //     read_IMU(connected_imus[i]);
            //     finger1->acc_x[reading] = curr_imu->data.accelX;
            // }
        }

        delay(5);
}
