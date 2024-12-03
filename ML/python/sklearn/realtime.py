import numpy as np
import joblib

# Load the artifacts
nn_model = joblib.load('nn_model.pkl')
scaler = joblib.load('scaler.pkl')
label_encoder = joblib.load('label_encoder.pkl')

# Simulate a single data input (7x4 flattened into 28 features)
sample_data = np.random.rand(28)  # Replace with actual test data
scaled_data = scaler.transform([sample_data])  # Scale the data
prediction = nn_model.predict(scaled_data)
print("Predicted Label:", label_encoder.inverse_transform(prediction))