import pandas as pd                                                           # For handling dataset operations
import tensorflow as tf                                                       # For building and training the model

from sklearn.model_selection import train_test_split                          # For splitting dataset
from sklearn.preprocessing import LabelEncoder                                # For encoding gesture labels
from tensorflow.keras import layers                                           # For defining neural network layers
from tensorflow.keras.optimizers import Adam                                  # For optimizing training

# Load Dataset
print("\n---- Dataset Info ----")
gesture_data = pd.read_csv("data_final.csv")                                        # Read dataset from CSV file

x = gesture_data.iloc[:, :-1].values                                          # Features (first 300 columns)
y = gesture_data.iloc[:, -1].values                                           # Labels (gesture names)

# Encode labels
label_encoder = LabelEncoder()                                                # Initialize label encoder
y = label_encoder.fit_transform(y)                                            # Convert labels to numeric values

print(f"Dataset Shape: {gesture_data.shape}")                                 # Print dataset shape
print(f"Feature Shape: {x.shape}")                                            # Print feature shape
print(f"Label Shape: {y.shape}")                                              # Print label shape
print("Label Mapping:", dict(zip(label_encoder.classes_,                      # Print label mapping dictionary
                                 range(len(label_encoder.classes_)))))

# Train-validation-test split (80% train, 10% val, 10% test)
random_state = 42                                                              # Set random state for reproducibility
x_train, x_temp, y_train, y_temp = train_test_split(x, y, test_size=0.2)       # Split data into 80% train, 20% temp
x_val, x_test, y_val, y_test = train_test_split(x_temp, y_temp, test_size=0.5) # Split temp into 50% val, 50% test

# Define Model
model = tf.keras.Sequential([
    layers.Input(shape=(300,)),                                                 # Input layer with 300 features                        
    layers.Dense(256, activation='relu'),                                       # Dense layer with 256 units and ReLU activation                      
    layers.Dropout(0.4),                                                        # Dropout layer with 40% dropout rate                       
    layers.Dense(128, activation='relu'),                                       # Dense layer with 128 units and ReLU activation
    layers.Dropout(0.4),                                                        # Dropout layer with 40% dropout rate
    layers.Dense(64, activation='relu'),                                        # Dense layer with 64 units and ReLU activation
    layers.Dropout(0.4),                                                        # Dropout layer with 40% dropout rate               
    layers.Dense(len(label_encoder.classes_), activation='softmax')             # Output layer with softmax activation (num_classes units)
])


model.compile(optimizer=Adam(learning_rate=0.001),                            # Use Adam optimizer with low LR
              loss='sparse_categorical_crossentropy',                         # Use sparse categorical loss for multi-class
              metrics=['accuracy'])                                           # Track accuracy during training
model.summary()                                                               # Print model architecture

# Train Model
history = model.fit(x_train, y_train,                                         # Train using training set
                    epochs=100,                                               # Train for 100 epochs
                    batch_size=16,                                            # Use batch size of 16 for better training
                    validation_data=(x_val, y_val))                           # Validate using validation set

# Evaluate Model
test_loss, test_acc = model.evaluate(x_test, y_test)                          # Evaluate on test set
print(f"Test Accuracy: {test_acc:.4f}")                                       # Print test accuracy

# Save Model in HDF5 Format
saved_model_path = "SIGNSPEAK_MLP.h5"                                         # Define model save path
model.save(saved_model_path)                                                  # Save trained model in .h5 format
print(f"Model saved as {saved_model_path}")                                   # Print confirmation

# Convert to TensorFlow Lite (Keeping Your Settings)
converter = tf.lite.TFLiteConverter.from_keras_model(model)                   # Convert model to TensorFlow Lite
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS]        # Set TFLite supported operations
converter._experimental_lower_tensor_list_ops = False                         # Keep compatibility settings
tflite_model = converter.convert()                                            # Convert model to TFLite format

# Save TFLite Model
tflite_model_path = "SIGNSPEAK_MLP_FINAL.tflite"                                    # Define TFLite model save path
with open(tflite_model_path, "wb") as f:                                      # Open file to write
    f.write(tflite_model)                                                     # Save converted TFLite model
print(f"TFLite model saved: {tflite_model_path}")                             # Print confirmation