import serial
import joblib
import pandas as pd
import numpy as np
import json
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import classification_report

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn.base")

# Load gesture data
gesture_data = pd.read_csv('gesture_data_augmented.csv')

# Prepare features and labels
X = gesture_data[[
    'acc_x_t0.25', 'acc_x_t0.5', 'acc_x_t0.75', 'acc_x_t1.0',
    'acc_y_t0.25', 'acc_y_t0.5', 'acc_y_t0.75', 'acc_y_t1.0',
    'acc_z_t0.25', 'acc_z_t0.5', 'acc_z_t0.75', 'acc_z_t1.0',
    'gyro_x_t0.25', 'gyro_x_t0.5', 'gyro_x_t0.75', 'gyro_x_t1.0',
    'gyro_y_t0.25', 'gyro_y_t0.5', 'gyro_y_t0.75', 'gyro_y_t1.0',
    'gyro_z_t0.25', 'gyro_z_t0.5', 'gyro_z_t0.75', 'gyro_z_t1.0',
    'flex_t0.25', 'flex_t0.5', 'flex_t0.75', 'flex_t1.0'
]]
y = gesture_data['label']

# Split data (for offline testing and validation)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train a Neural Network
mlp = MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=500, random_state=42)
mlp.fit(X_train_scaled, y_train)

# Evaluate on test set
y_pred = mlp.predict(X_test_scaled)
print("Classification Report:")
print(classification_report(y_test, y_pred))

# Save the model and scaler
joblib.dump(mlp, 'mlp_model.pkl')
joblib.dump(scaler, 'scaler.pkl')

# Load saved model for real-time inference
mlp = joblib.load('mlp_model.pkl')
scaler = joblib.load('scaler.pkl')

# Configure serial port for real-time data
serial_port = '/dev/tty.usbmodem101'  # Replace with your port
baud_rate = 115200
ser = serial.Serial(serial_port, baud_rate, timeout=1)

# Real-time prediction loop
print("Listening for data...")
sign_count = 0
total_signs = 10

try:
    while sign_count < total_signs:
        line = ser.readline().decode('utf-8').strip()  # Read and decode a line
        if line:
            print(f"Received raw data: {line}")  # Print raw data

            # Check if the line contains the "Data collected:" prefix
            if "Data collected:" in line:
                # Extract the dictionary string after the prefix
                raw_data = line.split("Data collected:")[-1].strip()
                try:
                    # Parse the dictionary
                    data_dict = json.loads(raw_data.replace("'", '"'))  # Convert single quotes to double for JSON parsing
                    # Convert dictionary values to a list (ensure correct feature order)
                    feature_order = [
                        'acc_x_t0.25', 'acc_x_t0.5', 'acc_x_t0.75', 'acc_x_t1.0',
                        'acc_y_t0.25', 'acc_y_t0.5', 'acc_y_t0.75', 'acc_y_t1.0',
                        'acc_z_t0.25', 'acc_z_t0.5', 'acc_z_t0.75', 'acc_z_t1.0',
                        'gyro_x_t0.25', 'gyro_x_t0.5', 'gyro_x_t0.75', 'gyro_x_t1.0',
                        'gyro_y_t0.25', 'gyro_y_t0.5', 'gyro_y_t0.75', 'gyro_y_t1.0',
                        'gyro_z_t0.25', 'gyro_z_t0.5', 'gyro_z_t0.75', 'gyro_z_t1.0',
                        'flex_t0.25', 'flex_t0.5', 'flex_t0.75', 'flex_t1.0'
                    ]
                    data = [data_dict[key] for key in feature_order]

                    # Scale the incoming data
                    scaled_data = scaler.transform([data])

                    # Predict using the Neural Network
                    predicted_label = mlp.predict(scaled_data)[0]
                    print(f"Predicted Gesture: {predicted_label}")  # Print prediction

                    sign_count += 1  # Increment sign counter
                except (ValueError, KeyError, json.JSONDecodeError) as e:
                    print(f"Error parsing data: {e}")
finally:
    ser.close()
    print("Program finished.")