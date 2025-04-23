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

# Detect channels with BMI270
used_channels = []
for channel in range(8):
    if tca[channel].try_lock():
        print(f"Channel {channel}:", end="")
        addresses = tca[channel].scan()
        print([hex(addr) for addr in addresses])
        if address_bmi270 in addresses:
            used_channels.append(channel)
        tca[channel].unlock()

# Initialize sensors only on valid channels
sensors = {}
for channel in used_channels:
    if tca[channel].try_lock():
        addresses = tca[channel].scan()
        if address_bmi270 in addresses:
            print(f"Initializing BMI270 on channel {channel}")
            wrapped_i2c = I2CWrapper(tca[channel], address_bmi270)
            sensors[channel] = bmi270.BMI270(wrapped_i2c)
        tca[channel].unlock()

def collect_reading(used_channels, sensors):
    for j in range(3, 0, -1):
        print(f"Starting in {j} seconds...")
        time.sleep(1)
    print("Now: Perform Gesture")

    start_total = time.perf_counter()
    gesture_data_list = []

    gesture_length_seconds = 1
    gesture_datapoints = 10
    datapoints_per_reading = 6
    max_readings = len(used_channels) * datapoints_per_reading * gesture_datapoints
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

    duration = time.perf_counter() - start_total
    print(f"[⏱] Data collection time: {duration:.3f} seconds")
    return gesture_data_list

# Define gestures
gestures = ["food", "hello", "yes", "no", "thankyou"]
for gesture in gestures:
    sample = 0
    batch = []
    while sample < 25:
        print(f"\nGesture: {gesture} | Sample {sample+1}/25")
        reading = collect_reading(used_channels, sensors)
        if len(reading) == 300:  # 5 IMUs × 6 × 10 = 300
            batch.append(reading + [gesture])
            sample += 1
            if len(batch) == 5:
                with open('data1.csv', mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerows(batch)
                print("✅ 5 samples written to CSV")
                batch = []
        else:
            print("⚠️ Incomplete reading. IMU issue? Redo gesture.")

    # Write remaining samples if <5
    if batch:
        with open('data1.csv', mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(batch)
        print("Final leftover samples written")