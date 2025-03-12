import numpy as np
import pandas as pd
import tensorflow.lite as tflite # This is for laptops/desktops
# import tflite_runtime.interpreter as tflite # This is for BeagleBoneBlack

# Load label mapping manually from a text file
label_mapping = {}                                                           # Dictionary to store label mappings
with open("gesture_labels.txt", "r") as f:                                   # Open text file
    for line in f:                                                           # Read each line
        label, index = line.strip().split()                                  # Split gesture name and index
        label_mapping[int(index)] = label                                    # Store as {index: gesture_name}

# Load test dataset
test_file_path = "test.csv"                                                  # Define test dataset path
test_data = pd.read_csv(test_file_path)                                      # Read test dataset

x_test = test_data.iloc[:, :-1].values.astype(np.float32)                    # Features (first 300 columns)
y_actual = test_data.iloc[:, -1].values                                      # Actual gesture labels

# Load TensorFlow Lite model
interpreter = tflite.Interpreter(model_path="SIGNSPEAK_MLP.tflite")          # Load trained TFLite model
interpreter.allocate_tensors()                                               # Allocate memory for tensors

input_details = interpreter.get_input_details()                              # Get input tensor details
output_details = interpreter.get_output_details()                            # Get output tensor details

correct_predictions = 0                                                      # Initialize correct predictions counter
predictions_list = []                                                        # List to store (predicted, actual) pairs

# Run inference on all test samples
for i in range(len(x_test)):
    sample = x_test[i].reshape(1, 300)                                      # Ensure correct shape (1, 300)

    interpreter.set_tensor(input_details[0]['index'], sample)               # Load input tensor
    interpreter.invoke()                                                    # Run model inference
    predictions = interpreter.get_tensor(output_details[0]['index'])        # Get model output

    predicted_class = np.argmax(predictions)                                     # Get index of highest probability class
    predicted_gesture = label_mapping.get(predicted_class)                       # Convert index to gesture
    actual_gesture = y_actual[i]                                                 # Get actual gesture from dataset

    predictions_list.append((predicted_gesture, actual_gesture))            # Store results
    if predicted_gesture == actual_gesture:                                 # Compare predicted vs actual gesture
        correct_predictions += 1                                            # Increment correct predictions count

accuracy = (correct_predictions / len(x_test)) * 100                        # Compute accuracy percentage

# Display results
df_results = pd.DataFrame(predictions_list, columns=["Predicted Gesture", "Actual Gesture"])
print(df_results)

print(f"\nModel Accuracy on Test Set: {accuracy:.2f}%")                     # Print final accuracy percentage