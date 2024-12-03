from machine import Pin, I2C, ADC
import time
from micropython_bmi270 import bmi270

# Initialize I2C and IMU
i2c = I2C(0, sda=Pin(4), scl=Pin(5))
bmi = bmi270.BMI270(i2c)

# Flex sensor constants
flex_resistance_unbent_ohms = 25000
resistor_divider_ohms = 10000
pico_vout_volts = 3.3

# Read flex sensor angle
def read_flex_angle(pin_num):
    adc_pin = ADC(Pin(pin_num))
    adc_reading = adc_pin.read_u16()
    flex_v = pico_vout_volts * float(adc_reading) / 4095.0
    flex_r = abs(resistor_divider_ohms * (pico_vout_volts / flex_v - 1.0))
    angle = 90 - float(90 * flex_r / 7000)
    return max(0, min(90, angle))  # Clamp angle

# Read data from IMU and flex sensors
def read_data():
    data_vector = []
    for _ in range(4):  # Collect data for 4 intervals
        accx, accy, accz = bmi.acceleration
        gyrox, gyroy, gyroz = bmi.gyro
        flex_angle = read_flex_angle(26)
        data_vector.extend([accx, accy, accz, gyrox, gyroy, gyroz, flex_angle])
        time.sleep(0.25)  # Wait for the next interval
    return data_vector

# Send data serially
while True:
    data = read_data()
    print(",".join(f"{x:.2f}" for x in data))  # Send as comma-separated values
    time.sleep(0.1)  # Small delay to control output frequency