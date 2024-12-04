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

def read_flex_angle(pin_num):
    adc_pin = ADC(Pin(pin_num))
    adc_reading = adc_pin.read_u16()
    flex_v = pico_vout_volts * float(adc_reading) / 4095.0
    flex_r = abs(resistor_divider_ohms * (pico_vout_volts / flex_v - 1.0))
    angle = 90 - float(90 * flex_r / 7000)
    return max(0, min(90, angle))

def read_data():
    data_vector = []
    for _ in range(4):  # Collect data for 4 intervals
        accx, accy, accz = bmi.acceleration
        gyrox, gyroy, gyroz = bmi.gyro
        flex_angle = read_flex_angle(26)
        data_vector.extend([accx, accy, accz, gyrox, gyroy, gyroz, flex_angle])
        time.sleep(0.25)  # Wait for the next interval
    return data_vector

# Main loop to collect data for 5 signs
print("Pico ready to send data for 5 signs.")
sign_count = 0
total_signs = 5

while sign_count < total_signs:
    # Countdown indicator for user
    for i in range(5, 0, -1):
        print(f"Get ready! Performing the sign in {i} seconds...")
        time.sleep(1)
    
    # Collect and print data
    print("Recording data now...")
    data = read_data()  # Function to collect the data (assumed defined elsewhere)
    print(f"Data collected: {data}")
    print("Data collection complete. Waiting for the next cycle...\n")
    
    # Increment sign count
    sign_count += 1

print("Data collection for 5 signs complete. Program exiting.")