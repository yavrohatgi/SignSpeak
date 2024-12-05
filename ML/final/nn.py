import serial
import joblib
import numpy as np
from sklearn.preprocessing import StandardScaler
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="sklearn.base")

# Load scaler and KNN model
scaler = joblib.load('scaler.pkl')
nn_model = joblib.load('nn_model.pkl')
label_encoder = joblib.load('label_encoder.pkl')

# Feature order based on uploaded data
feature_order = [
    'acc_x_t1', 'acc_y_t1', 'acc_z_t1', 'gyro_x_t1', 'gyro_y_t1', 'gyro_z_t1', 'flex_t1',
    'acc_x_t2', 'acc_y_t2', 'acc_z_t2', 'gyro_x_t2', 'gyro_y_t2', 'gyro_z_t2', 'flex_t2',
    'acc_x_t3', 'acc_y_t3', 'acc_z_t3', 'gyro_x_t3', 'gyro_y_t3', 'gyro_z_t3', 'flex_t3',
    'acc_x_t4', 'acc_y_t4', 'acc_z_t4', 'gyro_x_t4', 'gyro_y_t4', 'gyro_z_t4', 'flex_t4',
    'acc_x_t5', 'acc_y_t5', 'acc_z_t5', 'gyro_x_t5', 'gyro_y_t5', 'gyro_z_t5', 'flex_t5',
    'acc_x_t6', 'acc_y_t6', 'acc_z_t6', 'gyro_x_t6', 'gyro_y_t6', 'gyro_z_t6', 'flex_t6',
    'acc_x_t7', 'acc_y_t7', 'acc_z_t7', 'gyro_x_t7', 'gyro_y_t7', 'gyro_z_t7', 'flex_t7',
    'acc_x_t8', 'acc_y_t8', 'acc_z_t8', 'gyro_x_t8', 'gyro_y_t8', 'gyro_z_t8', 'flex_t8',
    'acc_x_t9', 'acc_y_t9', 'acc_z_t9', 'gyro_x_t9', 'gyro_y_t9', 'gyro_z_t9', 'flex_t9',
    'acc_x_t10', 'acc_y_t10', 'acc_z_t10', 'gyro_x_t10', 'gyro_y_t10', 'gyro_z_t10', 'flex_t10'
]

# Configure serial port for real-time data
serial_port = '/dev/tty.usbmodem101'  # Replace with your port
baud_rate = 115200
ser = serial.Serial(serial_port, baud_rate, timeout=1)

# Real-time prediction loop
print("Listening for data...")
sign_count = 0
total_signs = 5

try:
    while sign_count < total_signs:
        line = ser.readline().decode('utf-8').strip()  # Read and decode a line
        if line:
            print(f"Received raw data: {line}")  # Print raw data

            # Check if the line is valid CSV data
            if line.startswith("Data sent:"):
                # Extract CSV data from the line
                raw_data = line.split("Data sent:")[-1].strip()

                try:
                    # Parse the CSV data into a list of floats
                    data = list(map(float, raw_data.split(',')))

                    # Check if the number of features matches the expected feature order
                    if len(data) != len(feature_order):
                        # print(f"Error: Received data has {len(data)} features, expected {len(feature_order)}.")
                        continue

                    # Scale the incoming data
                    scaled_data = scaler.transform([data])

                    predicted_label = nn_model.predict(scaled_data)[0]

                    # Decode the label to the gesture name
                    predicted_gesture = label_encoder.inverse_transform([predicted_label])[0]
                    print(f"Predicted Gesture: {predicted_gesture}")  # Print prediction

                    sign_count += 1  # Increment sign counter
                except ValueError as e:
                    print(f"Error parsing data: {e}")
finally:
    ser.close()
    print("Program finished.")