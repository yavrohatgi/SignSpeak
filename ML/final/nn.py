import serial
import joblib
import numpy as np
from sklearn.preprocessing import StandardScaler
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="sklearn.base")

# ======== Load the trained model and scaler ========
scaler = joblib.load('scaler.pkl')
nn_model = joblib.load('nn_model.pkl')
label_encoder = joblib.load('label_encoder.pkl')

# =========== Define inputs and outputs ==========
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

# ======= Setup serial port ========
serial_port = '/dev/tty.usbmodem101' # change accordinly 
baud_rate = 115200 # default val
ser = serial.Serial(serial_port, baud_rate, timeout=1)

# ======= Main program loop ========
print("Listening for data...")
sign_count = 0
total_signs = 5 # change accordingly

try:
    while sign_count < total_signs:
        line = ser.readline().decode('utf-8').strip() # read data from serial port
        if line:
            # print(f"Received raw data: {line}") 
            if line.startswith("Data sent:"): # Check if the line contains data
                raw_data = line.split("Data sent:")[-1].strip()

                try:
                    data = list(map(float, raw_data.split(','))) # parse the data into 70 features

                    # Check if the number of features matches the expected feature order
                    if len(data) != len(feature_order):
                        continue # skip 

                    scaled_data = scaler.transform([data]) # scale
                    
                    # predict returns an array of values, we need to get the scalar prediction value so index 0
                    predicted_label = nn_model.predict(scaled_data)[0] # get the prediction
                    predicted_gesture = label_encoder.inverse_transform([predicted_label])[0] # decode the prediction
                    print(f"Predicted Gesture: {predicted_gesture}")

                    sign_count += 1
                except ValueError as e:
                    print(f"Error parsing data: {e}")

finally:
    ser.close() # Close the serial port
    print("Program finished.")