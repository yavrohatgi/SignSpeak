import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
import joblib

# Load data
data = pd.read_csv('gesture_data.csv')
X = data[['acc_x_t0.25', 'acc_y_t0.25', 'acc_z_t0.25', 
          'gyro_x_t0.25', 'gyro_y_t0.25', 'gyro_z_t0.25', 'flex_t0.25',
          'acc_x_t0.5', 'acc_y_t0.5', 'acc_z_t0.5', 
          'gyro_x_t0.5', 'gyro_y_t0.5', 'gyro_z_t0.5', 'flex_t0.5',
          'acc_x_t0.75', 'acc_y_t0.75', 'acc_z_t0.75', 
          'gyro_x_t0.75', 'gyro_y_t0.75', 'gyro_z_t0.75', 'flex_t0.75',
          'acc_x_t1.0', 'acc_y_t1.0', 'acc_z_t1.0', 
          'gyro_x_t1.0', 'gyro_y_t1.0', 'gyro_z_t1.0', 'flex_t1.0']]
y = data['label']

# Encode labels and preprocess
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.1, random_state=42)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train the Neural Network
nn_model = MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=500, random_state=42)
nn_model.fit(X_train_scaled, y_train)

# Save the model, scaler, and label encoder
joblib.dump(nn_model, 'nn_model.pkl')
joblib.dump(scaler, 'scaler.pkl')
joblib.dump(label_encoder, 'label_encoder.pkl')

print("Model, scaler, and label encoder saved successfully.")