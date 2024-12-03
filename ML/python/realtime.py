import time
from machine import Pin, I2C, ADC
from micropython_bmi270 import bmi270
from tflite_runtime.interpreter import Interpreter

# Initialize I2C and IMU
i2c = I2C(0, sda=Pin(4), scl=Pin(5))  # Correct I2C pins for RP2040
devices = i2c.scan()
print("I2C devices found:", devices)
bmi = bmi270.BMI270(i2c)

# Flex sensor parameters
flex_resistance_unbent_ohms = 25000
flex_resistance_max_ohms = 100000
resistor_divider_ohms = 10000
pico_vout_volts = 3.3         

# Load TensorFlow Lite model
model_path = "model.tflite"
interpreter = Interpreter(model_path=model_path)
interpreter.allocate_tensors()

# Get model input and output details
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

def read_flex_angle(pin_num):
    """
    Reads angle detected by flex sensor on specified pin.
    """
    adc_pin = ADC(Pin(pin_num))
    adc_reading = adc_pin.read_u16()
    flex_voltage = pico_vout_volts * float(adc_reading) / 65535.0
    flex_resistance = resistor_divider_ohms * (pico_vout_volts / flex_voltage - 1.0)
    angle = max(0, min(90, 90 - float(90 * flex_resistance / flex_resistance_max_ohms)))
    return angle

def read_imu_data():
    """
    Reads accelerometer and gyroscope data.
    """
    accx, accy, accz = bmi.acceleration
    gyrox, gyroy, gyroz = bmi.gyro
    return [accx, accy, accz, gyrox, gyroy, gyroz]

def collect_data():
    """
    Collects a single gesture's data over 1 second.
    Returns a flattened list of sensor readings.
    """
    data_vector = []
    for _ in range(4):  # Four readings at intervals of 0.25s
        imu_data = read_imu_data()
        flex_angle = read_flex_angle(26)  # Replace 26 with your flex sensor pin number
        data_vector.extend(imu_data + [flex_angle])
        time.sleep(0.25)
    return [float(x) for x in data_vector]  # Convert to floats if needed

def run_inference(data):
    """
    Runs inference on collected data and returns the predicted class index.
    """
    # Set input tensor
    interpreter.set_tensor(input_details[0]['index'], data)
    interpreter.invoke()

    # Get the output tensor
    output = interpreter.get_tensor(output_details[0]['index'])

    # Find the index of the maximum probability
    predicted_index = max(range(len(output[0])), key=lambda i: output[0][i])
    return predicted_index

def main():
    gesture_labels = ['left', 'right', 'up', 'down']  # Adjust based on your model training
    samples_per_gesture = 5  # Number of predictions to make
    print("Starting real-time gesture detection...")

    for sample_num in range(samples_per_gesture):
        print("Prepare to perform the gesture in 3 seconds...")
        time.sleep(3)
        print("Recording gesture now...")
        
        # Collect and predict
        data = collect_data()  # Collect sensor data
        predicted_class_index = run_inference(data)  # Get prediction
        predicted_label = gesture_labels[predicted_class_index]
        print(f"Predicted Gesture: {predicted_label}")
        
        # Short gap before the next prediction
        print("Prediction complete. Preparing for the next gesture...\n")
        time.sleep(2)

main()