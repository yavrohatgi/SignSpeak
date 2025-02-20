#include <stdio.h>
#include <math.h>
#include "pico/stdlib.h"
#include "hardware/i2c.h"
#include "hardware/pio.h"
#include "hardware/interp.h"
#include "hardware/timer.h"
#include "hardware/adc.h"
#include <string.h>

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
#define READING_INTERVAL_SECONDS 1

// holds readings for a single finger for the duration of one sign
struct single_finger_gesture_sample{
        float acc_x[NUM_READINGS];
        float acc_y[NUM_READINGS];
        float acc_z[NUM_READINGS];
        float gyr_x[NUM_READINGS];
        float gyr_y[NUM_READINGS];
        float gyr_z[NUM_READINGS];
        float flex_angle[NUM_READINGS];
        char label[LABEL_LENGTH]; 
};

// holds readings for all fingers for the duration of one sign
struct multi_finger_imu_reading{
        single_finger_gesture_sample* finger_0;
        single_finger_gesture_sample* finger_1;
        single_finger_gesture_sample* finger_2;
        single_finger_gesture_sample* finger_3;
        single_finger_gesture_sample* finger_4;
        char label[LABEL_LENGTH];
};

// calculates the p-norm of a given vector
float calculate_p_norm(int p, float vector[], size_t vector_length){
        /*
        Calculates p-norm of a given vector. 

        Parameters: 
        uint8_t: p, used for calculation. Default value of 2 - Euclidean norm. 
        float*: vector, pointer to vector to get norm from
        size_t: vector_length, length of given vector

        Returns: 
        float: norm, the calculated p-norm for the given array. 
        */ 
        // TODO: make sure empty arguments are handled, eventually
        // calculate norm if p is nonzero, otherwise return the norm
        if(p != 0){
                float total_sum = 0;
                for(int i = 0; i < vector_length; i++){
                        total_sum += pow(vector[i], p);
                }
                float calculated_norm = pow(total_sum, 1/p);
                return calculated_norm;
        } else {
                // alternative option could be l0 norm, which is number of nonzero entries
                return 0;
        }
}

// normalizes a given vector
void normalize_vector(float norm, float vector[], size_t vector_length){
        /*
        Normalizes a given vector. Changes original vector rather than creating a new one, for storage saving.

        Parameters: 
        float: norm, pre-calculated, used to normalize
        float*: vector, pointer to vector to normalize
        size_t: vector_length, length of vector

        Returns: 
        None
        */
        for(int i = 0; i < vector_length; i++){
                vector[i] = vector[i]/norm; // store normalized value in ith value of normalized_vector
        }
}

// maps values from one range to another
float map(float x, float in_min, float in_max, float out_min, float out_max){
        /*
        Maps a value from one range to another

        Parameters:
        float: x, value in original range
        float: in_min, min value of original range
        float: in_max, max value of original range
        float: out_min, min value of desired range
        float: out_max, max value of desired range

        Returns:
        float: mapping of x in output range
        */
        return (float) (out_min + (x - in_min)*(out_max - out_min)/(in_max - in_min));
}

// reads values from flex sensor and converts to an angle
float read_flex_sensor(uint8_t pin){
        /*
        Reads a value from flex sensor connected to specified pin. 

        Parameters:
        uint8_t: pin, number of pin to read from

        Returns:
        float: angle calculated using ADC reading from pin
        */
        // EITHER 12 OR 16, PLAY WITH THIS ONCE THE THINGS ARE CONNECTED
        int num_bits = 12;
        const float conversionFactor = pico_output_voltage_volts / (1 << num_bits);
        float adc_voltage = (float) adc_read() * conversionFactor;
        float adc_resistance = dividing_resistance_ohms * (pico_output_voltage_volts / adc_voltage - 1.0);
        return map(adc_resistance, flex_min_resistance_ohms, flex_max_resistance_ohms, minAngle_degrees, maxAngle_degrees);
}

uint8_t multiplexerAddress = 0x70;

// Helper function for changing TCA output channel
void tcaselect(uint8_t channel) {
        if (channel > 7) return;
        Wire.beginTransmission(multiplexerAddress);
        Wire.write(1 << channel);
        Wire.endTransmission();
}

// Create a new sensor object
BMI270 imu0;
BMI270 imu1;
BMI270 imu2;
BMI270 imu3;
BMI270 imu4;

// I2C address selection
uint8_t i2cAddress = BMI2_I2C_PRIM_ADDR; // 0x68
// uint8_t i2cAddress = BMI2_I2C_SEC_ADDR; // 0x69

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
                while (imu4.beginI2C(i2cAddress) != BMI2_OK) {
                    Serial.print("Error: BMI270 not connected, check wiring and I2C address of IMU ");
                    Serial.println(connected_imus[i]);
                    delay(1000);
                }
                break;
        }
    }
    Serial.println("All BMI270 sensors connected!");
}

// stores the IMU reading in the provided BMI270 object
void store_IMU_reading(BMI270* curr_imu, uint8_t imu_index, single_finger_gesture_sample* finger_reading, uint8_t reading_index){
        tcaselect(imu_index);

        if (curr_imu->getSensorData() == BMI2_OK) {
                // Serial.print("Successful reading from IMU");
                // Serial.println(imu_index);
                finger_reading->acc_x[reading_index] = curr_imu->data.accelX;
                finger_reading->acc_y[reading_index] = curr_imu->data.accelY;
                finger_reading->acc_z[reading_index] = curr_imu->data.accelZ;
                finger_reading->gyr_x[reading_index] = curr_imu->data.gyroX;
                finger_reading->gyr_y[reading_index] = curr_imu->data.gyroY;
                finger_reading->gyr_z[reading_index] = curr_imu->data.gyroZ;
        } else {
                Serial.print("Error reading from IMU");
                Serial.println(imu_index);
        }
}


void setup() {
        // this will be used to setup everything. 
        setup_multiplexer_IMUs();
}

void loop(){
        uint8_t connected_imus[5] = {0, 1, 2, 3, 7};
  
        // TODO: for the machine learning, we want to concatenate all arrays into one big
        // array for training. every array in the single_finger_gesture_sample structure 
        // will be combined into one large array for each finger each large finger array 
        // will then be concatenated with the other large finger arrays this will be one
        // column of the csv, with the other column being the label for the gesture


        // TODO: put the following lines into one method to collect data on one gesture. 
        // we can set it up to print the gesture to record, then pause, then collect data,
        // and store the selected gesture's label in the multi_finger_imu_reading structure
        // method can also be used during inference, as we simply do not attach a label but 
        // we store the reading in a struct this will make it easier to pass to the machine
        // learning model


        // method to collect complete sample for one gesture
        // START METHOD HERE
        single_finger_gesture_sample finger0;
        single_finger_gesture_sample finger1;
        single_finger_gesture_sample finger2;
        single_finger_gesture_sample finger3;
        single_finger_gesture_sample finger4;

        // TODO: see if we can create an array of single_finger_gesture_sample structures, 
        // then loop through that array to fill them out. would be easier logic to follow. 
        for(int reading = 0; reading < NUM_READINGS; reading++){
                for(int j = 0; j < 5; j++){
                        BMI270* curr_imu;
                        single_finger_gesture_sample* curr_finger;
                        switch (connected_imus[j]) {
                                case 0: curr_imu = &imu0; curr_finger = &finger0; break;
                                case 1: curr_imu = &imu1; curr_finger = &finger1; break;
                                case 2: curr_imu = &imu2; curr_finger = &finger2; break;
                                case 3: curr_imu = &imu3; curr_finger = &finger3; break;
                                case 7: curr_imu = &imu4; curr_finger = &finger4; break;
                                default: return; // Invalid IMU selection
                        }
                        store_IMU_reading(curr_imu, connected_imus[j], curr_finger, reading);
                }
                
                delay(1000*READING_INTERVAL_SECONDS/NUM_READINGS); // delay between readings
        }

        multi_finger_imu_reading hand_data;
        hand_data.finger_0 = &finger0;
        hand_data.finger_1 = &finger1;
        hand_data.finger_2 = &finger2;
        hand_data.finger_3 = &finger3;
        hand_data.finger_4 = &finger4;
        // hand_data.label = "gesture";
        strcpy(hand_data.label, "gesture");  // Correct way to copy a string
        // END METHOD HERE

        delay(1000); // delay before next set of readings

        
        // code to print data stored, reading by reading, finger by finger
        for(int i = 0; i < NUM_READINGS; i++){
                for(int j = 0; j < 5; j++){
                        BMI270* curr_imu;
                        single_finger_gesture_sample* curr_finger;
                        switch (connected_imus[j]) {
                                case 0: curr_imu = &imu0; curr_finger = &finger0; break;
                                case 1: curr_imu = &imu1; curr_finger = &finger1; break;
                                case 2: curr_imu = &imu2; curr_finger = &finger2; break;
                                case 3: curr_imu = &imu3; curr_finger = &finger3; break;
                                case 7: curr_imu = &imu4; curr_finger = &finger4; break;
                                default: return; // Invalid IMU selection
                        }
                        Serial.print("Finger ");
                        Serial.print(j);
                        Serial.print(": ");
                        Serial.print("Acc X: ");
                        Serial.print(curr_finger->acc_x[i]);
                        Serial.print(" Acc Y: ");
                        Serial.print(curr_finger->acc_y[i]);
                        Serial.print(" Acc Z: ");
                        Serial.print(curr_finger->acc_z[i]);
                        Serial.print(" Gyr X: ");
                        Serial.print(curr_finger->gyr_x[i]);
                        Serial.print(" Gyr Y: ");
                        Serial.print(curr_finger->gyr_y[i]);
                        Serial.print(" Gyr Z: ");
                        Serial.println(curr_finger->gyr_z[i]);
                }               
                Serial.print("Cycle #");
                Serial.print(i);
                Serial.println(" complete");
        }
        
}