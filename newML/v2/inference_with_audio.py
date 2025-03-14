import wave
import struct
import mmap
import Adafruit_BBIO.PWM as PWM
import time
import board
import adafruit_tca9548a
import bmi270
from bmi270.BMI270 import *
import Adafruit_BBIO
from micropython_bmi270 import bmi270

import numpy as np
#import tensorflow.lite as tflite # This is for laptops/desktops
import tflite_runtime.interpreter as tflite # This is for BeagleBoneBlack
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="tensorflow")


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
    print(gesture_data_list)
    print(len(gesture_data_list))
    return gesture_data_list

def load_wav_as_array(filename):
    """Load a WAV file and return an array of samples."""
    wav = wave.open(filename, "rb")
    sample_width = wav.getsampwidth()
    sample_rate = wav.getframerate()
    n_frames = wav.getnframes()

    print(f"Loaded WAV: {sample_rate} Hz, {n_frames} frames, {sample_width * 8}-bit depth")

    if wav.getnchannels() != 1:
        print("Error: Only mono WAV files are supported.")
        return None, None

    samples = []
    for _ in range(n_frames):
        frame_data = wav.readframes(1)
        if sample_width == 2:  # 16-bit PCM
            sample = struct.unpack("<h", frame_data)[0]  # Little-endian signed short
        elif sample_width == 1:  # 8-bit PCM (unsigned)
            sample = struct.unpack("B", frame_data)[0] - 128  # Convert to signed
        else:
            print("Unsupported sample width.")
            return None, None
        samples.append(sample)

    wav.close()
    return samples, sample_rate



def play_audio(output_word):
    # Choose PWM pin
    PWM_PIN = "P9_14"  # PWM output pin
    PWM_FREQUENCY = 44000  # 44 kHz carrier frequency to match audio playback rate

    # Load WAV file
    WAV_FILE = output_word  # Your preprocessed WAV file

    # Load the WAV file
    wav_samples, sample_rate = load_wav_as_array(WAV_FILE)
    if wav_samples is None:
        exit(1)

    # Normalize sample values to PWM range (0 to 100%)
    min_val = min(wav_samples)
    max_val = max(wav_samples)
    wav_samples = [(sample - min_val) / (max_val - min_val) * 100 for sample in wav_samples]

    # Start PWM
    PWM.start(PWM_PIN, 50, PWM_FREQUENCY)

    # Improved playback loop with higher precision timing
    frame_duration = 1.0 / sample_rate  # Time per sample
    start_time = time.time()

    try:
        for i, duty_cycle in enumerate(wav_samples):
            PWM.set_duty_cycle(PWM_PIN, duty_cycle)
            expected_time = start_time + (i * frame_duration)
            
            # Busy wait for precise timing instead of sleep()
            while time.time() < expected_time:
                pass  # Wait exactly until the next frame
    except KeyboardInterrupt:
        print("Playback interrupted.")
    finally:
        PWM.stop(PWM_PIN)
        PWM.cleanup()
        print("Playback finished.")


def main():

    label_mapping = {}                                                           # Dictionary to store label mappings
    with open("gesture_labels.txt", "r") as f:                                   # Open text file
        for line in f:                                                           # Read each line
            label, index = line.strip().split()                                  # Split gesture name and index
            label_mapping[int(index)] = label                                    # Store as {index: gesture_name}

    interpreter = tflite.Interpreter(model_path="SIGNSPEAK_MLP_FINAL.tflite")          # Load TensorFlow Lite model
    interpreter.allocate_tensors()                                               # Allocate memory for tensors

    input_details = interpreter.get_input_details()                              # Get input details
    output_details = interpreter.get_output_details()                            # Get output details

    # to use, just put in the list of the channels used on multiplexer (0, 1, 2, 3, 7)
    # it returns a 300 point list of data points
    reading1 = collect_reading(used_channels)                                    # Collect data
    x0 = np.array(reading1, dtype=np.float32).reshape(1, -1) 

    # Run inference
    interpreter.set_tensor(input_details[0]['index'], x0)                  # Load input
    interpreter.invoke()                                                         # Run model
    predictions = interpreter.get_tensor(output_details[0]['index'])             # Get output

    predicted_class = np.argmax(predictions)                                     # Get majority class
    predicted_gesture = label_mapping[predicted_class]                           # Convert to original gesture
    predicted_gesture = label_mapping.get(predicted_class, "Unknown") 
    print("Predicted Gesture:", predicted_gesture)                               # Print predicted gesture            

    play_audio(f"{predicted_gesture}.wav")                                       # Play the audio

main()