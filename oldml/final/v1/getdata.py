import serial
import joblib
import json  # For parsing the dictionary format

# Load the trained model and preprocessing tools
nn_model = joblib.load('nn_model.pkl')  # Replace with your model path
scaler = joblib.load('scaler.pkl')     # Replace with your scaler path
label_encoder = joblib.load('label_encoder.pkl')  # Replace with your label encoder path

# Configure the serial port
serial_port = '/dev/tty.usbmodem101'  # Replace with your port
baud_rate = 115200
ser = serial.Serial(serial_port, baud_rate, timeout=1)

# Initialize sign counter
sign_count = 0
total_signs = 5

print("Listening for data...")
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
                    # Convert the dictionary values to a list (ensure the correct feature order)
                    feature_order = [
                        'acc_x_t0.25', 'acc_x_t0.5', 'acc_x_t0.75', 'acc_x_t1.0',
                        'acc_y_t0.25', 'acc_y_t0.5', 'acc_y_t0.75', 'acc_y_t1.0',
                        'acc_z_t0.25', 'acc_z_t0.5', 'acc_z_t0.75', 'acc_z_t1.0',
                        'gyro_x_t0.25', 'gyro_x_t0.5', 'gyro_x_t0.75', 'gyro_x_t1.0',
                        'gyro_y_t0.25', 'gyro_y_t0.5', 'gyro_y_t0.75', 'gyro_y_t1.0',
                        'gyro_z_t0.25', 'gyro_z_t0.5', 'gyro_z_t0.75', 'gyro_z_t1.0',
                        'flex_t0.25', 'flex_t0.5', 'flex_t0.75', 'flex_t1.0'
                    ]
                    data = [data_dict[key] for key in feature_order]  # Ensure order matches model input
                    if len(data) == 28:  # Ensure correct number of features
                        scaled_data = scaler.transform([data])  # Preprocess the data
                        predicted_label = nn_model.predict(scaled_data)  # Predict the label
                        predicted_gesture = label_encoder.inverse_transform(predicted_label)[0]
                        print(f"Predicted Gesture: {predicted_gesture}")  # Print the prediction
                        sign_count += 1  # Increment sign counter
                except (ValueError, KeyError, json.JSONDecodeError) as e:
                    print(f"Error parsing data: {e}")
finally:
    ser.close()
    print("Program finished.")