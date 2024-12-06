from machine import Pin, I2C, ADC
import time
from micropython_bmi270 import bmi270
import uio  # For file I/O in MicroPython

# Initialize I2C and IMU
i2c = I2C(0, sda=Pin(4), scl=Pin(5))
bmi = bmi270.BMI270(i2c)

# Flex sensor constants
flex_resistance_unbent_ohms = 25000
resistor_divider_ohms = 10000
pico_vout_volts = 3.3

# Define gestures
gestures = ["up", "right", "down", "left"]
instances_per_gesture = 25  # Number of instances per gesture

def read_flex_angle(pin_num):
    adc_pin = ADC(Pin(pin_num))
    adc_reading = adc_pin.read_u16()
    flex_v = pico_vout_volts * float(adc_reading) / 4095.0
    flex_r = abs(resistor_divider_ohms * (pico_vout_volts / flex_v - 1.0))
    angle = 90 - float(90 * flex_r / 7000)
    return max(0, min(90, angle))

def collect_gesture_data(gesture_label, instance_num):
    """Collect 10 samples for a single gesture instance within 1 second."""
    data_vector = []
    for t in range(1, 11):  # 10 intervals (0.1s to 1.0s)
        # Indicate progress for each sample
        print(f"Gesture '{gesture_label}' instance {instance_num + 1}/25: 0/{t} taken...")

        accx, accy, accz = bmi.acceleration
        gyrox, gyroy, gyroz = bmi.gyro
        flex_angle = read_flex_angle(26)

        # Collect all features for the time interval
        sample_row = [accx, accy, accz, gyrox, gyroy, gyroz, flex_angle]
        data_vector.extend(sample_row)  # Append features for this time interval
        time.sleep(0.1)  # Wait 0.1 seconds before the next sample

    return data_vector  # Return 70 values (7 features × 10 intervals)

# Open the CSV file for writing
filename = "pcb_data.csv"
with uio.open(filename, "w") as file:
    # Write the specified CSV header
    header = []
    for t in range(1, 11):  # For each time interval
        header.extend([f"acc_x_t{t}", f"acc_y_t{t}", f"acc_z_t{t}", 
                       f"gyro_x_t{t}", f"gyro_y_t{t}", f"gyro_z_t{t}", f"flex_t{t}"])
    header.append("gesture")  # Add gesture label to the header
    file.write(",".join(header) + "\n")

    print("Pico ready to collect data for gestures.")

    # Loop through each gesture and collect data
    for gesture in gestures:
        print(f"Starting data collection for gesture '{gesture}'.")

        # Collect 25 instances of the gesture
        for instance_num in range(instances_per_gesture):
            # Countdown for the gesture instance
            for i in range(3, 0, -1):
                print(f"Get ready! Performing the gesture '{gesture}' (Instance {instance_num + 1}/25) in {i} seconds...")
                time.sleep(1)

            # Collect data for the gesture instance
            print(f"Recording data for gesture '{gesture}' (Instance {instance_num + 1}/25)...")
            gesture_data = collect_gesture_data(gesture, instance_num)

            # Write collected data to CSV file
            gesture_data.append(gesture)  # Add gesture label at the end
            file.write(",".join(map(str, gesture_data)) + "\n")
            file.flush()  # Ensure data is saved
            print(f"Data for gesture '{gesture}' (Instance {instance_num + 1}/25) written to file.")

        print(f"Data collection complete for gesture '{gesture}'.\n")

    print(f"Data collection for all gestures complete. File saved as '{filename}'.")