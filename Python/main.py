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

i2c = I2C(0, sda=Pin(0), scl=Pin(1))  # Correct I2C pins for RP2040
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

def read_data(timetoread_ms):
        """
        Reads data, creates a specified length vector for each component

        Parameters:
        int: timetoread_ms --> duration of time, in ms, to read IMU data over

        Returns:
        list: data_vector --> 2d list of all data
        """
        accx_list, accy_list, accz_list, gyrox_list, gyroy_list, gyroz_list, flex_list = [], [], [], [], [], [], []
        # reading data over specified time period
        for i in range(timetoread_ms):
                # get data from IMU
                accx, accy, accz = bmi.acceleration
                print(f"acceleration:\tx:{accx:.2f}m/s2\t y:{accy:.2f}m/s2\t z{accz:.2f}m/s2")
                gyrox, gyroy, gyroz = bmi.gyro
                print("gyroscope:\tx:{:.2f}°/s\t y:{:.2f}°/s\t z{:.2f}°/s".format(gyrox, gyroy, gyroz))
                # add to respective list
                accx_list.append(accx)
                accy_list.append(accy)
                accz_list.append(accz)
                gyrox_list.append(gyrox)
                gyroy_list.append(gyroy)
                gyroz_list.append(gyroz)
                flexangle = read_flex_angle(26) 
                print("flex angle:\t", flexangle)
                flex_list.append(flexangle)
                time.sleep(0.25)

        return [flex_list, accx_list, accy_list, accz_list, gyrox_list, gyroy_list, gyroz_list]
        # return [normalize_vector(accx_list), normalize_vector(accy_list), normalize_vector(accz_list), normalize_vector(gyrox_list), normalize_vector(gyroy_list), normalize_vector(gyroz_list), normalize_vector(flex_list)]
    

def log_data(data_vector, label):
        """
        Logs data to a CSV file with the specified label.

        Parameters:
        list: data_vector
        str: label

        Returns:
        None
        """
        filename = "data.csv"
        with open(filename, "a") as file:  # Use "a" to append to the file
                if file.tell() == 0:  # If the file is empty, write the header
                        file.write("flex,acc-x,acc-y,acc-z,gyro-x,gyro-y,gyro-z,label\n")
                print("file created")
                for row in zip(*data_vector):  # Combines lists into rows
                        file.write(",".join(map(str, row)) + f",{label}\n")
                        print(f"row written: {row}, label: {label}")
        print("file written")

def main():
        gestures = ['left', 'right', 'up', 'down']  # Possible gestures
        numLoops = 100 # Number of readings per gesture

        for gesture in gestures:
                print(f"Prepare to perform the gesture: {gesture}")
                time.sleep(3)  # Allow user to prepare
                print(f"Recording data for: {gesture}")
                data_vector = read_data(numLoops)  # Collect data
                log_data(data_vector, label=gesture)  # Save data with gesture label
        print("Data collection complete.")

main()