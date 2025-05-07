import wave
import struct
import Adafruit_BBIO.PWM as PWM
import time
import board
import adafruit_tca9548a
from micropython_bmi270 import bmi270

import adafruit_ssd1306
import busio

import os
import select
import threading
import queue
import numpy as np
import tflite_runtime.interpreter as tflite
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="tensorflow")

# --------------------- Constants ---------------------

address_bmi270 = 0x68  # I2C address of BMI270 sensor
max_queue_size = 20
gesture_queue = queue.Queue(max_queue_size)

pause_event = threading.Event()
pause_event.set()  # Start in running state

BUTTON_GPIO_NUM = "60"
GPIO_PATH = f"/sys/class/gpio/gpio{BUTTON_GPIO_NUM}/value"


# --------------------- Classes ---------------------

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

# --------------------- Utility Functions ---------------------

def display_text(oled, text): 
    oled.fill(0)
    oled.text(text, 0, 0, 1)
    oled.show()

def collect_reading(used_channels, sensors): 
    gesture_data_list = []
    gesture_length_seconds = 1
    gesture_datapoints = 10
    datapoints_per_reading = 6
    max_readings = len(used_channels) * datapoints_per_reading * gesture_datapoints
    curr_reading = 0
    print("Collecting new gesture...")
    for i in range(2):
        display_text(oled, f"Perform gesture in {2-i}s")
    # display_text(oled, "Collecting Gesture")
    start_collect = time.perf_counter()
    while curr_reading < max_readings:
        for channel in used_channels:
            if tca[channel].try_lock():
                sensor = sensors[channel]
                gesture_data_list.extend(sensor.acceleration)
                gesture_data_list.extend(sensor.gyro)
                curr_reading += datapoints_per_reading
                tca[channel].unlock()
        time.sleep(gesture_length_seconds / gesture_datapoints)
    end_collect = time.perf_counter()
    # print(f"[⏱] Data collection time: {end_collect - start_collect:.3f} seconds")
    return gesture_data_list

def load_wav_as_array(filename): 
    try:
        wav = wave.open(filename, "rb")
    except FileNotFoundError:
        print(f"Audio file {filename} not found.")
        return None, None

    sample_width = wav.getsampwidth()
    sample_rate = wav.getframerate()
    n_frames = wav.getnframes()

    if wav.getnchannels() != 1:
        print("Error: Only mono WAV files are supported.")
        return None, None

    samples = []
    for _ in range(n_frames):
        frame_data = wav.readframes(1)
        if sample_width == 2:
            sample = struct.unpack("<h", frame_data)[0]
        elif sample_width == 1:
            sample = struct.unpack("B", frame_data)[0] - 128
        else:
            print("Unsupported sample width.")
            return None, None
        samples.append(sample)

    wav.close()
    return samples, sample_rate

def play_audio(output_word): 
    PWM_PIN = "P9_14"
    PWM_FREQUENCY = 44000

    wav_samples, sample_rate = load_wav_as_array(output_word)
    if wav_samples is None:
        return

    min_val = min(wav_samples)
    max_val = max(wav_samples)
    wav_samples = [(sample - min_val) / (max_val - min_val) * 100 for sample in wav_samples]

    PWM.start(PWM_PIN, 50, PWM_FREQUENCY)
    frame_duration = 1.0 / sample_rate
    start_time = time.time()

    try:
        for i, duty_cycle in enumerate(wav_samples):
            PWM.set_duty_cycle(PWM_PIN, duty_cycle)
            while time.time() < start_time + (i * frame_duration):
                pass
    finally:
        PWM.stop(PWM_PIN)
        PWM.cleanup()

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

# --------------------- Thread Functions ---------------------

def gesture_collector():
    while True:
    # for i in range(10):
        pause_event.wait()   # <-- Add this
        # print("Collecting new gesture...")
        # display_text(oled, "Collecting Gesture")
        reading = collect_reading(used_channels, sensors)
        gesture_queue.put(reading)
        # print("Gesture queued.")
        # display_text(oled, "Gesture queued")
        time.sleep(0.1)  # Small delay before next collection cycle


def inference_worker():
    label_mapping = {}
    with open("gesture_labels.txt", "r") as f:
        for line in f:
            label, index = line.strip().rsplit(" ", 1)
            label_mapping[int(index)] = label

    interpreter = tflite.Interpreter(model_path="SIGNSPEAK_MLP_FINAL.tflite")
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    while True:
    # for i in range(10):
        pause_event.wait()   # <-- Add this
        reading = gesture_queue.get()
        if reading is None:
            break

        # display_text(oled, "Running inference...")
        print("Running inference...")
        x0 = np.array(reading, dtype=np.float32).reshape(1, -1)
        start_infer = time.perf_counter()
        interpreter.set_tensor(input_details[0]['index'], x0)
        interpreter.invoke()
        predictions = interpreter.get_tensor(output_details[0]['index'])
        end_infer = time.perf_counter()
        # print(f"[⏱] Inference time: {end_infer - start_infer:.3f} seconds")
        predicted_class = np.argmax(predictions)
        predicted_gesture = label_mapping.get(predicted_class, "Unknown")
        print(f"Predicted Gesture: {predicted_gesture}")
        # display_text(oled, f"{predicted_gesture}")

        start_audio = time.perf_counter()
        play_audio(f"{predicted_gesture}.wav")
        end_audio = time.perf_counter()
        # print(f"[⏱] Audio playback time: {end_audio - start_audio:.3f} seconds")


def button_monitor():
    setup_gpio_button()
    print("Press button to toggle pause/resume")
    display_text(oled, "Btn: Pause/Resume")

    with open(GPIO_PATH, "r") as gpio_fd:
        poller = select.poll()
        poller.register(gpio_fd, select.POLLPRI)

        gpio_fd.seek(0)
        gpio_fd.read()  # Clear initial interrupt

        while True:
            events = poller.poll(300)  # Wait for button press
            if not events:
                continue

            gpio_fd.seek(0)
            val = gpio_fd.read().strip()
            if val == "0":  # Button press detected
                if pause_event.is_set():
                    print("System Paused")
                    display_text(oled, "System Paused")
                    pause_event.clear()
                else:
                    print("System Running")
                    display_text(oled, "System Running")
                    pause_event.set()

                # Wait for button release
                while True:
                    time.sleep(0.05)
                    gpio_fd.seek(0)
                    if gpio_fd.read().strip() == "1":
                        break

                gpio_fd.seek(0)
                gpio_fd.read()  # Clear interrupt after release
                

# --------------------- Initialization ---------------------

print("Initializing I2C and OLED...")
i2c = board.I2C()
tca = adafruit_tca9548a.TCA9548A(i2c)

i2cOLED = busio.I2C(board.SCL, board.SDA)
tca = adafruit_tca9548a.TCA9548A(i2cOLED)

oled = adafruit_ssd1306.SSD1306_I2C(128, 64, tca[7])
oled.fill(0)
oled.show()
display_text(oled, "Initializing...")

used_channels = []
for channel in range(7):
    if tca[channel].try_lock():
        addresses = tca[channel].scan()
        if len(addresses) > 1:
            used_channels.append(channel)
        tca[channel].unlock()

sensors = {}
for channel in used_channels:
    if tca[channel].try_lock():
        wrapped_i2c = I2CWrapper(tca[channel], address_bmi270)
        sensors[channel] = bmi270.BMI270(wrapped_i2c)
        tca[channel].unlock()

# --------------------- Start Threads ---------------------

def start_system():
    display_text(oled, "System Running")

    threading.Thread(target=gesture_collector, daemon=True).start()
    threading.Thread(target=inference_worker, daemon=True).start()
    threading.Thread(target=button_monitor, daemon=True).start()

    # Run for 30 seconds total
    RUN_DURATION = 60 * 60 * 4  # seconds
    start_time = time.time()

    while True:
        if time.time() - start_time > RUN_DURATION:
            print(f"{RUN_DURATION} seconds elapsed. Exiting...")
            display_text(oled, "Exiting...")
            break
        time.sleep(1)  # Keep main thread alive in intervals

if __name__ == "__main__":
    start_system()