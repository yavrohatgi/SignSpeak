import wave
import struct
import mmap
import Adafruit_BBIO.PWM as PWM
import time

import numpy as np
import tensorflow.lite as tflite # This is for laptops/desktops
# import tflite_runtime.interpreter as tflite # This is for BeagleBoneBlack
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="tensorflow")

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

    interpreter = tflite.Interpreter(model_path="SIGNSPEAK_MLP.tflite")          # Load TensorFlow Lite model
    interpreter.allocate_tensors()                                               # Allocate memory for tensors

    input_details = interpreter.get_input_details()                              # Get input details
    output_details = interpreter.get_output_details()                            # Get output details

    np.random.seed(0)                                                            # Set seed for reproducibility
    x0 = np.random.rand(1, 300).astype(np.float32)                               # Generate a random input

    # Run inference
    interpreter.set_tensor(input_details[0]['index'], x0)                        # Load input
    interpreter.invoke()                                                         # Run model
    predictions = interpreter.get_tensor(output_details[0]['index'])             # Get output

    predicted_class = np.argmax(predictions)                                     # Get majority class
    predicted_gesture = label_mapping[predicted_class]                           # Convert to original gesture
    print("Predicted Gesture:", predicted_gesture)                               # Print predicted gesture            


    play_audio(f"{predicted_gesture}.wav")                                       # Play the audio


