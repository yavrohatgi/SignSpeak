import wave
import struct
import mmap
import Adafruit_BBIO.PWM as PWM
import time
import board
import adafruit_tca9548a
from micropython_bmi270 import bmi270

# imports for OLED
import adafruit_ssd1306
import busio

# imports for pushbutton
import os
import select
import threading

import numpy as np
#import tensorflow.lite as tflite # This is for laptops/desktops
import tflite_runtime.interpreter as tflite # This is for BeagleBoneBlack
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="tensorflow")

def display_text(oled, text): #-----------------------
    # Clear the display
    oled.fill(0)

    # Display some text using the default font
    oled.text(text, 0, 0, 1)
    oled.show()

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

# Initialize the TCA9548A multiplexer
i2cOLED = busio.I2C(board.SCL, board.SDA)
tca = adafruit_tca9548a.TCA9548A(i2cOLED)

# Access channel 7
i2c_channel_7 = tca[7]

# Initialize the OLED display (adjust width/height to your display)
WIDTH = 128
HEIGHT = 64
oled = adafruit_ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c_channel_7)

# Clear the display
oled.fill(0)
oled.show()

display_text(oled, "Initializing...")

# testing to make sure we recognize all connected IMUs on the proper channels
for channel in range(7):
    if tca[channel].try_lock():
        print("Channel {}:".format(channel), end="")
        addresses = tca[channel].scan()
        # print([hex(address) for address in addresses if address != 0x70])
        print([hex(address) for address in addresses])

        if len(addresses) > 1:
            used_channels.append(channel)
        tca[channel].unlock()

# --- Pre-initialize sensors once ---
sensors = {}
for channel in used_channels:
    if tca[channel].try_lock():
        wrapped_i2c = I2CWrapper(tca[channel], address_bmi270)
        sensors[channel] = bmi270.BMI270(wrapped_i2c)
        tca[channel].unlock()


def collect_reading(used_channels, sensors): #-----------------------
    gesture_data_list = []
    gesture_length_seconds = 1
    gesture_datapoints = 10
    num_fingers = 5
    datapoints_per_reading = 6  # acc x, y, z, gyr x, y, z
    max_readings = num_fingers * datapoints_per_reading * gesture_datapoints
    curr_reading = 0

    print("Start gesture:")
    
    # --- Collect readings from each sensor ---
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


def load_wav_as_array(filename): #-----------------------
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



def play_audio(output_word): #-----------------------
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
    label_mapping = {}
    with open("gesture_labels.txt", "r") as f:
        for line in f:
            label, index = line.strip().split()
            label_mapping[int(index)] = label

    interpreter = tflite.Interpreter(model_path="SIGNSPEAK_MLP_FINAL.tflite")
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    #print(f"\n--- Inference Attempt {attempt + 1} ---")


    # --- print start time ---
    j=3
    while j>0:
        print(f"Starting in {j} seconds...")
        display_text(oled, f"Starting in {j} seconds...")
        time.sleep(1)
        j -= 1
    display_text(oled, "Perform Gesture")
    start_total = time.perf_counter()

    # --- Time: Data Collection ---
    start_collect = time.perf_counter()
    reading1 = collect_reading(used_channels, sensors)
    end_collect = time.perf_counter()
    print(f"[⏱] Data collection time: {end_collect - start_collect:.3f} seconds")

    x0 = np.array(reading1, dtype=np.float32).reshape(1, -1)

    # --- Time: Model Inference ---
    start_infer = time.perf_counter()
    interpreter.set_tensor(input_details[0]['index'], x0)
    interpreter.invoke()
    predictions = interpreter.get_tensor(output_details[0]['index'])
    end_infer = time.perf_counter()
    print(f"[⏱] Inference time: {end_infer - start_infer:.3f} seconds")

    predicted_class = np.argmax(predictions)
    predicted_gesture = label_mapping.get(predicted_class, "Unknown")
    print("Predicted Gesture:", predicted_gesture)

    # --- Time: Audio Playback ---
    display_text(oled, f"gesture: {predicted_gesture}")
    start_audio = time.perf_counter()
    play_audio(f"{predicted_gesture}.wav")
    end_audio = time.perf_counter()
    print(f"[⏱] Audio playback time: {end_audio - start_audio:.3f} seconds")

    # --- Time: Total ---
    end_total = time.perf_counter()
    print(f"[⏱] Total time: {end_total - start_total:.3f} seconds")

BUTTON_GPIO_NUM = "60"
GPIO_PATH = f"/sys/class/gpio/gpio{BUTTON_GPIO_NUM}/value"
inference_running = False

def setup_gpio_button():
    try:
        if not os.path.exists(f"/sys/class/gpio/gpio{BUTTON_GPIO_NUM}"):
            with open("/sys/class/gpio/export", "w") as f:
                f.write(BUTTON_GPIO_NUM)
        with open(f"/sys/class/gpio/gpio{BUTTON_GPIO_NUM}/direction", "w") as f:
            f.write("in")
        with open(f"/sys/class/gpio/gpio{BUTTON_GPIO_NUM}/edge", "w") as f:
            f.write("falling")
    except Exception as e:
        print("GPIO setup failed:", e)

def run_main_loop():
    global inference_running
    if inference_running:
        print("⚠️ Inference already running — ignoring button press.")
        return

    inference_running = True
    try:
        main()
    except Exception as e:
        print("❌ Error during inference:", e)
    finally:
        inference_running = False
        print("Press the button to start inference...")
        display_text(oled, "Press button to start...")

def watch_button():
    print("Press the button to start inference...")
    display_text(oled, "Press button to start...")

    with open(GPIO_PATH, "r") as gpio_fd:
        poller = select.poll()
        poller.register(gpio_fd, select.POLLPRI)

        gpio_fd.seek(0)
        gpio_fd.read()
        #print("Cleared initial buffer, entering loop")

        while True:
            events = poller.poll(300)

            if not events:
                continue

            gpio_fd.seek(0)
            val = gpio_fd.read().strip()

            if val == "0":
                print("Button pressed — running inference...")
                display_text(oled, "Starting inference")
                t = threading.Thread(target=run_main_loop)
                t.daemon = True
                t.start()

                # Wait until released
                while True:
                    time.sleep(0.05)
                    gpio_fd.seek(0)
                    release_val = gpio_fd.read().strip()
                    if release_val == "1":
                        break

                gpio_fd.seek(0)
                gpio_fd.read()

if __name__ == "__main__":
    setup_gpio_button()
    watch_button()