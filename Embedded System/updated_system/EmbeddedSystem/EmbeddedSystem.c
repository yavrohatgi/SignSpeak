#include <stdio.h>
#include <math.h>
#include "pico/stdlib.h"
#include "hardware/i2c.h"
#include "hardware/pio.h"
#include "hardware/interp.h"
#include "hardware/timer.h"
#include "model_data.cc"
#include "blink.pio.h"
#include "bmi270.h"
#include "bmi2_ois.h"
#include "hardware/adc.h"


// I2C defines
// This example will use I2C0 on GPIO4 (SDA) and GPIO5 (SCL) running at 3.2KHz.
// Pins can be changed, see the GPIO function select table in the datasheet for information on GPIO assignments
#define I2C_PORT i2c0
#define I2C_SDA 4
#define I2C_SCL 5

// variables used for caluculations of flex sensor readings
#define maxAngle_degrees  90.0
#define minAngle_degrees  0.0
#define dividing_resistance_ohms  10000.0
#define pico_output_voltage_volts  3.3
#define flex_max_resistance_ohms  100000.0
#define flex_min_resistance_ohms  25000.0

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

/*
reads data from IMU, stores into array given to method
*/
void read_imu(double data_array[], size_t data_array_size){
    
}

/*
infers a sign from the given data array 
TODO
*/
void predict_sign(void){

}

int main()
{
    stdio_init_all();

    // I2C Initialization. Using it at 3.2 Khz.
    i2c_init(I2C_PORT, 3.2*1000);
    
    gpio_set_function(I2C_SDA, GPIO_FUNC_I2C);
    gpio_set_function(I2C_SCL, GPIO_FUNC_I2C);
    gpio_pull_up(I2C_SDA);
    gpio_pull_up(I2C_SCL);
    // For more examples of I2C use see https://github.com/raspberrypi/pico-examples/tree/master/i2c

    // ADC Initialization. Connected to ADC0
    adc_init();
    adc_select_input(0);    // on ADC0 (pin 26)

}
