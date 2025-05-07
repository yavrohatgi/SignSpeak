import numpy as np
import tensorflow.lite as tflite 

interpreter = tflite.Interpreter(model_path="SIGNSPEAK_MLP_compatible.tflite")
interpreter.allocate_tensors()  # Allocate memory for tensors

# Get input and output tensor details
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Load label mapping (NumPy dictionary)
label_mapping = np.load("label_mapping.npy", allow_pickle=True).item()

# Reverse mapping (class index → label name)
index_to_label = {v: k for k, v in label_mapping.items()}

# Sample input data (Replace with actual input from your sensor)
x0 = np.random.rand(1, 300,1,1).astype(np.float32)  # Ensure input is float32

# Run inference
interpreter.set_tensor(input_details[0]['index'], x0)  # Load input
interpreter.invoke()  # Run model
predictions = interpreter.get_tensor(output_details[0]['index'])  # Get results

# Decode prediction
predicted_class = np.argmax(predictions)  # Get class index
predicted_label = index_to_label[predicted_class]  # Convert index to label name

# Print result
print("Predicted Gesture:", predicted_label)