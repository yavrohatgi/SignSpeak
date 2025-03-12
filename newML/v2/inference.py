import numpy as np
import tensorflow.lite as tflite # This is for laptops/desktops
# import tflite_runtime.interpreter as tflite # This is for BeagleBoneBlack

label_mapping = {}                                                           # Dictionary to store label mappings
with open("gesture_labels.txt", "r") as f:                                   # Open text file
    for line in f:                                                           # Read each line
        label, index = line.strip().split()                                  # Split gesture name and index
        label_mapping[int(index)] = label                                    # Store as {index: gesture_name}

interpreter = tflite.Interpreter(model_path="SIGNSPEAK_MLP.tflite")          # Load TensorFlow Lite model
interpreter.allocate_tensors()                                               # Allocate memory for tensors

input_details = interpreter.get_input_details()                              # Get input details
output_details = interpreter.get_output_details()                            # Get output details

np.random.seed(0)                                                            # Set seed for reproducibility
x0 = np.random.rand(1, 300).astype(np.float32)                               # Generate a random input

# Run inference
interpreter.set_tensor(input_details[0]['index'], x0)                        # Load input
interpreter.invoke()                                                         # Run model
predictions = interpreter.get_tensor(output_details[0]['index'])             # Get output

predicted_class = np.argmax(predictions)                                     # Get majority class
predicted_gesture = label_mapping[predicted_class]                           # Convert to original gesture
print("Predicted Gesture:", predicted_gesture)                               # Print predicted gesture            