import numpy as np
import joblib
import tflite_runtime.interpreter as tflite

# Load the TensorFlow Lite model
interpreter = tflite.Interpreter(model_path="SIGNSPEAK_MLP_compatible.tflite")
interpreter.allocate_tensors()  # Allocate memory for tensors

# Get input and output tensor details
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Load label encoder
label_encoder = joblib.load("label_encoder.pkl")

# Sample input data (Replace with actual input from your sensor)
x0 = np.random.rand(1, 300).astype(np.float32)  # Ensure input is float32

# Run inference
interpreter.set_tensor(input_details[0]['index'], x0)  # Load input
interpreter.invoke()  # Run model
predictions = interpreter.get_tensor(output_details[0]['index'])  # Get results

# Decode prediction
predicted_class = np.argmax(predictions)  # Get class index
predicted_label = label_encoder.inverse_transform([predicted_class])  # Get label

# Print result
print("Predicted Gesture:", predicted_label[0])