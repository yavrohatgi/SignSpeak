import serial
import joblib
import re

# Load the trained model and preprocessing tools
nn_model = joblib.load('nn_model.pkl')  # Replace with your model path
scaler = joblib.load('scaler.pkl')     # Replace with your scaler path
label_encoder = joblib.load('label_encoder.pkl')  # Replace with your label encoder path

# Configure the serial port
serial_port = '/dev/tty.usbmodem101'  # Replace with your port
baud_rate = 115200
ser = serial.Serial(serial_port, baud_rate, timeout=1)

# Regular expression to match the desired format
pattern = re.compile(r'\[(.*?)\]')  # Matches everything inside square brackets

# Initialize sign counter
sign_count = 0
total_signs = 5

print("Listening for data...")
try:
    while sign_count < total_signs:
        line = ser.readline().decode('utf-8').strip()  # Read and decode a line
        if line:
            print(f"Received raw data: {line}")  # Print raw data
            match = pattern.search(line)  # Extract content inside brackets
            if match:
                try:
                    # Convert matched data to a list of floats
                    data = list(map(float, match.group(1).split(',')))
                    if len(data) == 28:  # Ensure the correct number of features
                        scaled_data = scaler.transform([data])  # Preprocess the data
                        predicted_label = nn_model.predict(scaled_data)  # Predict the label
                        predicted_gesture = label_encoder.inverse_transform(predicted_label)[0]
                        print(f"Predicted Gesture: {predicted_gesture}")  # Print the prediction
                        sign_count += 1  # Increment sign counter
                except ValueError:
                    pass  # Skip if conversion fails
finally:
    ser.close()
    print("Program finished.")