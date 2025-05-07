import serial
import numpy as np
import joblib

# Load the trained model and preprocessing tools
nn_model = joblib.load('nn_model.pkl')  # Replace with your model path
scaler = joblib.load('scaler.pkl')     # Replace with your scaler path
label_encoder = joblib.load('label_encoder.pkl')  # Replace with your label encoder path

# Set up the serial connection
pico_serial = serial.Serial('/dev/tty.usbmodem101', baudrate=9600, timeout=1)  # Replace with your port

# Read and process one set of data
print("Waiting for one set of data from Pico...")
try:
    line = pico_serial.readline().decode('utf-8').strip()  # Read data from Pico
    if line:
        raw_data = list(map(float, line.split(',')))  # Convert to list of floats
        if len(raw_data) == 28:  # Ensure correct data length
            scaled_data = scaler.transform([raw_data])  # Preprocess the data
            predicted_label = nn_model.predict(scaled_data)
            print(f"Predicted Gesture: {label_encoder.inverse_transform(predicted_label)[0]}")
        else:
            print(f"Incomplete data received: {line}")
except ValueError as e:
    print(f"Error processing data: {e}")
except KeyboardInterrupt:
    print("Stopped by user.")