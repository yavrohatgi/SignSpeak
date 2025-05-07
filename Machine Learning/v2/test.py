import numpy as np
import tensorflow.lite as tflite # This is for laptops/desktops
# import tflite_runtime.interpreter as tflite # This is for BeagleBoneBlack

# Load label mapping manually from a text file
label_mapping = {}                                                           # Dictionary to store label mappings
with open("gesture_labels.txt", "r") as f:                                   # Open text file
    for line in f:                                                           # Read each line
        parts = line.strip().split()                                         # Split gesture name and index
        label = parts[0]                                                     # Gesture name
        index = int(parts[1])                                                # Gesture index
        label_mapping[index] = label                                         # Store mapping {index: gesture}

# Load test dataset manually (No pandas)
x_test = []                                                                  # List to store feature values
y_actual = []                                                                # List to store actual labels

with open("test.csv", "r") as f:                                             # Open test CSV file
    lines = f.readlines()                                                    # Read all lines
    for line in lines[1:]:                                                   # Skip the header
        parts = line.strip().split(",")                                      # Split by comma
        features = []                                                        # Temporary list for features
        for v in parts[:-1]:                                                 # Loop through first 300 values
            features.append(float(v))                                        # Convert to float and store
        x_test.append(features)                                              # Store features in x_test
        y_actual.append(parts[-1])                                           # Store actual gesture label

x_test = np.array(x_test, dtype=np.float32)                                  # Convert features to NumPy array

# Load TensorFlow Lite model
interpreter = tflite.Interpreter(model_path="SIGNSPEAK_MLP.tflite")          # Load trained TFLite model
interpreter.allocate_tensors()                                               # Allocate memory for tensors

input_details = interpreter.get_input_details()                              # Get input tensor details
output_details = interpreter.get_output_details()                            # Get output tensor details

correct_predictions = 0                                                      # Initialize correct predictions counter
predictions_list = []                                                        # List to store (predicted, actual) pairs

# Run inference on all test samples
for i in range(len(x_test)):
    sample = x_test[i]                                                       # Get one sample
    sample = sample.reshape(1, 300)                                          # Ensure correct shape (1, 300)

    interpreter.set_tensor(input_details[0]['index'], sample)                # Load input tensor
    interpreter.invoke()                                                      # Run model inference
    predictions = interpreter.get_tensor(output_details[0]['index'])         # Get model output

    predicted_class = np.argmax(predictions)                                 # Get index of highest probability class
    if predicted_class in label_mapping:                                     # Check if label exists
        predicted_gesture = label_mapping[predicted_class]                   # Convert index to gesture
    else:
        predicted_gesture = "UNKNOWN"                                        # Fallback if index not found

    actual_gesture = y_actual[i]                                             # Get actual gesture from dataset

    predictions_list.append((predicted_gesture, actual_gesture))             # Store results
    if predicted_gesture == actual_gesture:                                  # Compare predicted vs actual gesture
        correct_predictions += 1                                             # Increment correct predictions count

accuracy = (correct_predictions / len(x_test)) * 100                         # Compute accuracy percentage

# Display results in a readable format
print("\nPredicted Gesture | Actual Gesture")
print("-" * 30)
for pred, actual in predictions_list:
    print(f"{pred:<16}  | {actual}")

print(f"\nModel Accuracy on Test Set: {accuracy:.2f}%")                      # Print final accuracy percentage
