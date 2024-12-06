from machine import Pin, I2C, ADC, UART
import time
from micropython_bmi270 import bmi270

# Initialize I2C and IMU
i2c = I2C(0, sda=Pin(4), scl=Pin(5))
bmi = bmi270.BMI270(i2c)

# Initialize UART for serial communication
uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1))

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

    # Time intervals for sampling (10 samples in 1 second)
    time_intervals = [round(0.1 * i, 1) for i in range(1, 11)]

    for idx, t in enumerate(time_intervals):
        accx, accy, accz = bmi.acceleration
        gyrox, gyroy, gyroz = bmi.gyro
        flex_angle = read_flex_angle(26)

        # Append data in CSV-compatible format
        data_vector.extend([accx, accy, accz, gyrox, gyroy, gyroz, flex_angle])
        
        # Print progress
        print(f"Sample {idx + 1}/{len(time_intervals)} done.")
        time.sleep(0.1)  # Wait for the next interval

    return data_vector

# Main loop to collect data for 5 signs
print("Pico ready to send data for 5 signs.")
sign_count = 0
total_signs = 20

while sign_count < total_signs:
    # Countdown indicator for user
    for i in range(3, 0, -1):
        print(f"Get ready! Performing the sign in {i} seconds...")
        time.sleep(1)

    # Collect and send data
    print("Recording data now...")
    data = read_data()  # Collect data into the required format
    data_csv = ','.join(map(str, data))  # Convert list to CSV line
    uart.write(data_csv + '\n')  # Send over UART
    print(f"Data sent: {data_csv}")
    print("Data collection complete. Waiting for the next cycle...\n")
    time.sleep(5)
    sign_count += 1  # Increment sign count

print("Data collection for 20 signs complete. Program exiting.")