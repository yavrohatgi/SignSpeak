import board
import adafruit_tca9548a
import bmi270
from bmi270.BMI270 import *
import time
import numpy as np
import Adafruit_BBIO
from micropython_bmi270 import bmi270

class I2CWrapper:
    def __init__(self, i2c_obj, address):
        self._i2c = i2c_obj
        self._address = address

    def readfrom_mem(self, addr, reg, length, *_):
        """Reads data from the specified register."""
        self._i2c.writeto(self._address, bytes([reg]))  # Set register
        result = bytearray(length)
        self._i2c.readfrom_into(self._address, result)
        return result

    def writeto_mem(self, addr, reg, data, *_):
        """Writes data to the specified register."""
        self._i2c.writeto(self._address, bytes([reg]) + bytes(data))

# Constants
address_bmi270 = 0x68  # I2C address of the BMI270 sensor
address_multiplexer = 0x68

# Initialize I2C bus
i2c = board.I2C()  # Uses board.SCL and board.SDA

# Create the TCA9548A multiplexer object
tca = adafruit_tca9548a.TCA9548A(i2c)

# list of all channels of multiplexer in use (integers)
used_channels = []

# testing to make sure we recognize all connected IMUs on the proper channels
for channel in range(8):
    if tca[channel].try_lock():
        print("Channel {}:".format(channel), end="")
        addresses = tca[channel].scan()
        # print([hex(address) for address in addresses if address != 0x70])
        print([hex(address) for address in addresses])

        if len(addresses) > 1:
            used_channels.append(channel)
        tca[channel].unlock()


def collect_reading(used_channels):
    """
    returns a list of one gesture's readings over 1s
    """
    time.sleep(2)
    print("Start gesture:")
    print("In 2s")
    time.sleep(1)
    print("In 1s")
    time.sleep(1)
    print("Now:")
    gesture_data_list = []
    gesture_length_seconds = 1
    gesture_datapoints = 10
    num_fingers = 5
    datapoints_per_reading = 6 # acc x, y, z, gyr x, y, z
    max_readings = num_fingers * datapoints_per_reading * gesture_datapoints
    curr_reading = 0
    while curr_reading < max_readings:
        for channel in used_channels:
            if tca[channel].try_lock():
                wrapped_i2c = I2CWrapper(tca[channel], address_bmi270)
                sensor = bmi270.BMI270(wrapped_i2c)
                for datapt in sensor.acceleration:
                    gesture_data_list.append(datapt)
                for datapt in sensor.gyro:
                    gesture_data_list.append(datapt)
                curr_reading += datapoints_per_reading
            tca[channel].unlock()
        time.sleep(gesture_length_seconds/gesture_datapoints)
    return gesture_data_list

import csv 

gestures = ["food", "hello","yes"]
with open('final_data.csv', mode='a', newline='') as file:
    writer = csv.writer(file)
    for gesture in gestures:
        sample = 0
        while sample < 25:
            print(gesture)
            reading = collect_reading(used_channels)
            print(len(reading))
            print(sample)
            if len(reading) == 300:
                writer.writerow(reading + [gesture])  # Append data to CSV
                sample += 1
            else :
                print("one imu not connected")
                print("redo gesture")