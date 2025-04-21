import board
import adafruit_tca9548a
import time
import numpy as np
import csv
from micropython_bmi270 import bmi270

class I2CWrapper:
    def __init__(self, i2c_obj, address):
        self._i2c = i2c_obj
        self._address = address

    def readfrom_mem(self, addr, reg, length, *_):
        self._i2c.writeto(self._address, bytes([reg]))
        result = bytearray(length)
        self._i2c.readfrom_into(self._address, result)
        return result

    def writeto_mem(self, addr, reg, data, *_):
        self._i2c.writeto(self._address, bytes([reg]) + bytes(data))

# Constants
address_bmi270 = 0x68

# Initialize I2C and multiplexer
i2c = board.I2C()
tca = adafruit_tca9548a.TCA9548A(i2c)

# Detect connected IMUs
used_channels = []
for channel in range(8):
    if tca[channel].try_lock():
        print(f"Channel {channel}:", end="")
        addresses = tca[channel].scan()
        print([hex(address) for address in addresses])
        if len(addresses) > 1:
            used_channels.append(channel)
        tca[channel].unlock()

# Initialize sensors once
sensors = {}
for channel in used_channels:
    if tca[channel].try_lock():
        wrapped_i2c = I2CWrapper(tca[channel], address_bmi270)
        sensors[channel] = bmi270.BMI270(wrapped_i2c)
        tca[channel].unlock()

def collect_reading(used_channels, sensors):
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
    datapoints_per_reading = 6
    max_readings = num_fingers * datapoints_per_reading * gesture_datapoints
    curr_reading = 0

    while curr_reading < max_readings:
        for channel in used_channels:
            if tca[channel].try_lock():
                sensor = sensors[channel]
                for datapt in sensor.acceleration:
                    gesture_data_list.append(datapt)
                for datapt in sensor.gyro:
                    gesture_data_list.append(datapt)
                curr_reading += datapoints_per_reading
                tca[channel].unlock()
        time.sleep(gesture_length_seconds / gesture_datapoints)

    return gesture_data_list

# Collect samples
gestures = ["food", "hello", "yes", "no", "thank you"]
for gesture in gestures:
    sample = 0
    batch = []  # 🔧 hold 5 samples in memory
    while sample < 25:
        print(f"Gesture: {gesture} | Sample {sample+1}/25")
        reading = collect_reading(used_channels, sensors)
        if len(reading) == 300:
            batch.append(reading + [gesture])
            sample += 1
            if len(batch) == 5:  # write to CSV every 5 samples
                with open('final_data.csv', mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerows(batch)
                batch = []  # 🔧 clear batch
        else:
            print("⚠️ One IMU not connected. Redo gesture.")

    if batch:
        with open('final_data.csv', mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(batch)