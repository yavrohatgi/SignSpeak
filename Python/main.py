# this will be the stuff to run, will use the correct micropython library for the IMU, hopefully
# this code was developed without testing on Pico
# example code from https://github.com/jposada202020/MicroPython_BMI270/blob/master/examples/bmi270_simpletest.py
# Rev 1.0       21 Nov 2024

import time
from machine import Pin, I2C, ADC, PWM
import random
from micropython_bmi270 import bmi270

# values for flex sensor
flex_resistance_unbent_ohms = 25000
flex_resistance_max_ohms = 100000
resistor_divider_ohms = 10000
pico_vout_volts = 3.3         

i2c = I2C(0, sda=Pin(4), scl=Pin(5))
devices = i2c.scan()
print("I2C devices found:", devices)
bmi = bmi270.BMI270(i2c)

def lp_norm(vector, p = 2):
        """
        Returns the p-norm for a given vector. If no p specified, calculates Euclidean norm (p = 2)

        Parameters:
        list: vector
        int: p

        Returns:
        double: norm
        """
        sum = 0
        for num in vector:
                sum += pow(abs(num), p)
        return pow(sum, 1/p)

def normalize_vector(vector = [], p = 2):
        """
        Normalizes vector

        Parameters:
        list: vector
        int: p

        Returns:
        list: normalized_data
        """
        data_norm = lp_norm(vector, p)
        return [value/data_norm for value in vector] 

def predict_sign(gesture_data):
        """
        Predicts a sign using trained model.
        """
        gesture_words = ''
        return gesture_words

def read_flex_angle(pinNum):
        """
        Reads angle detected by flex sensor on specified pin. 
        
        Parameters:
        int: pinNum
        
        Returns:
        double: calculatedAngle
        """
        adc_pin = ADC(Pin(pinNum, mode = Pin.IN))
        adc_reading = adc_pin.read_u16()
        flexV = pico_vout_volts * float(adc_reading) / 4095.0

        if flexV <= 0:
                return 0

        flexR = abs(resistor_divider_ohms * (pico_vout_volts / flexV - 1.0))
        anglemax = 90
        anglemin = 0
        angle = 90-float(90*flexR/7000) # get the angle from the resistance
        if angle > anglemax:
                angle = anglemax # if more than 90 degrees, set to 90 degrees
        elif angle < anglemin:
                angle = anglemin # if negative angle, set to 0 degrees
        return angle

def read_wav_to_list(filename):
    """Reads 8-bit mono WAV file data into a list."""
    with open(filename, "rb") as f:
        # Skip WAV header (first 44 bytes for standard WAV files)
        f.seek(44)
        # Read the remaining data into a list
        data = f.read()
    return [byte for byte in data]

def play_audio(pinNum, audioFileName):
        """
        Plays specified audio file on speaker connected to specified pin. 
        
        Parameters:
        int: pinNum
        str: audioFileName

        Returns:
        None
        """
        speakerFreq = 8000
        pwm = PWM(Pin(pinNum))
        pwm.freq(speakerFreq)
        data = read_wav_to_list(audioFileName)
        for sample in data:
                pwm.duty_u16(sample << 8)  # Scale 8-bit to 16-bit for PWM
                time.sleep_us(int(1e6 / speakerFreq))  # Wait for the sample duration
        pwm.duty_u16(0)  # Turn off the PWM signal when done

def read_data():
    """
    Reads IMU and flex sensor data at four time intervals: t=0.25, 0.5, 0.75, and 1.0 seconds.

    Returns:
    list: Flattened list of sensor readings for one gesture.
    """
    acc_x_vector = []
    acc_y_vector = []
    acc_z_vector = []
    gyro_x_vector = []
    gyro_y_vector = []
    gyro_z_vector = []
    flex_vector = []
    data_vector = []

    for _ in range(4):  # Read data at specific time intervals
        accx, accy, accz = bmi.acceleration
        gyrox, gyroy, gyroz = bmi.gyro
        flexangle = read_flex_angle(26)

        # Add the sensor data for this timestamp
        acc_x_vector.append(accx)
        acc_y_vector.append(accy)
        acc_z_vector.append(accz)
        gyro_x_vector.append(gyrox)
        gyro_y_vector.append(gyroy)
        gyro_z_vector.append(gyroz)
        flex_vector.append(flexangle)
        time.sleep(0.25)  # Wait for the next interval

    data_vector = acc_x_vector + acc_y_vector + acc_z_vector + gyro_x_vector + gyro_y_vector + gyro_z_vector + flex_vector
    return data_vector

def log_data(row_data, label, filename="gesture_data.csv"):
    """
    Logs a single row of gesture data to a CSV file without duplicating headers.

    Parameters:
    list: row_data -> Flattened list of sensor readings for one gesture
    str: label -> Gesture label
    str: filename -> Name of the CSV file to write data

    Returns:
    None
    """
    # Function to check if the file exists
    def file_exists(filename):
        try:
            with open(filename, "r"):
                return True
        except OSError:
            return False
    
    # Define the header
    header = [['acc_x_t0.25', 'acc_x_t0.5','acc_x_t0.75','acc_x_t1.0',
          'acc_y_t0.25', 'acc_y_t0.5', 'acc_y_t0.75', 'acc_y_t1.0',
          'acc_z_t0.25', 'acc_z_t0.5', 'acc_z_t0.75', 'acc_z_t1.0',
          'gyro_x_t0.25', 'gyro_x_t0.5', 'gyro_x_t0.75', 'gyro_x_t1.0',
          'gyro_y_t0.25', 'gyro_y_t0.5', 'gyro_y_t0.75', 'gyro_y_t1.0',
          'gyro_z_t0.25', 'gyro_z_t0.5', 'gyro_z_t0.75', 'gyro_z_t1.0',
          'flex_t0.25','flex_t0.5','flex_t0.75','flex_t1.0']]

    with open(filename, "a") as file:
        # Write the header if the file does not exist
        if not file_exists(filename):
            file.write(",".join(header) + "\n")

        # Write the row data
        row_data.append(label)  # Add the label to the end
        file.write(",".join(map(str, row_data)) + "\n")

def main():
    gestures = ['left', 'right', 'up', 'down']  # Define the gestures to collect
    samples_per_gesture = 25  # Number of samples per gesture

    for gesture in gestures:
        print(f"Prepare to perform the gesture: {gesture}")
        time.sleep(3)  # Allow user to prepare

        for sample_num in range(samples_per_gesture):
            print(f"Recording sample {sample_num + 1}/{samples_per_gesture} for gesture: {gesture}")
            
            # start 
            print("Prepare to perform the gesture in 3 seconds...")
            time.sleep(3)
            print("Recording gesture now...")

            # Collect and log data
            data_vector = read_data()  # Collect data
            log_data(data_vector, label=gesture)  # Save data with gesture label
            print(data_vector)
            time.sleep(1)  # Wait 1 second between gesture samples

    print("All gesture data collection complete.")

main()