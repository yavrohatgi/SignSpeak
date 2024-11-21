# this will be the stuff to run, will use the correct micropython library for the IMU, hopefully
# this code was developed without testing on Pico
# example code from https://github.com/jposada202020/MicroPython_BMI270/blob/master/examples/bmi270_simpletest.py
# Rev 1.0       21 Nov 2024


import time
from machine import Pin, I2C
from micropython_bmi270 import bmi270

i2c = I2C(1, sda=Pin(2), scl=Pin(3))  # Correct I2C pins for RP2040
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

def format_data(acceleration_data, gyroscope_data):
        """
        Normalizes and combines acceleration and gyroscope data into a list. 

        Parameters:
        tuple: acceleration_data
        tuple: gyroscope_data

        Returns:
        list: formatted_data
        """
        acc_data_norm = lp_norm(acceleration_data)
        gyr_data_norm = lp_norm(gyroscope_data)
        # normalizing acceleration and gyroscope data separately
        return [value/acc_data_norm for value in acceleration_data] + [value/gyr_data_norm for value in gyroscope_data]

def predict_sign(gesture_data):
        """
        Predicts a sign using trained model.
        """
        gesture_words = ''
        return gesture_words

def main():
        numLoops = 10000
        for i in range(numLoops):
                accx, accy, accz = bmi.acceleration
                print(f"x:{accx:.2f}m/s2, y:{accy:.2f}m/s2, z{accz:.2f}m/s2")
                gyrox, gyroy, gyroz = bmi.gyro
                print("x:{:.2f}°/s, y:{:.2f}°/s, z{:.2f}°/s".format(gyrox, gyroy, gyroz))

                data = format_data(bmi.acceleration, bmi.gyro) # take current acceleration and gyroscope data and format into vector
                predict_sign(data)
                
                time.sleep(0.5)

main()