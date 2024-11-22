# this will be the stuff to run, will use the correct micropython library for the IMU, hopefully
# this code was developed without testing on Pico
# example code from https://github.com/jposada202020/MicroPython_BMI270/blob/master/examples/bmi270_simpletest.py
# Rev 1.0       21 Nov 2024


import time
from machine import Pin, I2C
import random
from micropython_bmi270 import bmi270

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

def read_data(timetoread_ms):
        """
        Reads data, creates a specified length vector for each component

        Parameters:
        int: timetoread_ms --> duration of time, in ms, to read IMU data over

        Returns:
        list: data_vector --> 2d list of all data
        """
        accx_list, accy_list, accz_list, gyrox_list, gyroy_list, gyroz_list = [], [], [], [], [], []
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
                time.sleep(1)
        # return normalized data
        return [normalize_vector(accx_list), normalize_vector(accy_list), normalize_vector(accz_list), normalize_vector(gyrox_list), normalize_vector(gyroy_list), normalize_vector(gyroz_list)]


def main():
        numLoops = 1000
        firstread = read_data(numLoops)
        predicted_sign = predict_sign(firstread)
        print(predicted_sign)
main()